#!/usr/bin/env python3
"""Validate founder classification-review exports before making them agent-readable.

Default mode is read-only; an explicit --out writes a validated JSONL snapshot.
Never changes Notion master IDs or production approval flags.
"""
import argparse
import base64
import datetime as dt
import gzip
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CHOICES = {
    "PHYSICAL_MASTER_CANDIDATE", "NEEDS_VISUAL_EVIDENCE", "TILE_OR_ATLAS_COMPONENT",
    "APPEARANCE_VARIANT", "NON_PHYSICAL_RESEARCH", "RESEARCH_COMPOSITE",
    "STATE_OF_PARENT", "MODEL_VIEW_OF_PARENT", "ANIMATION_REFERENCE",
    "UI_ICON_ONLY", "MATERIAL_TEXTURE", "DUPLICATE_ALIAS", "OUT_OF_SCOPE",
    "COMPOSITION_REFERENCE", "CANONICAL_MASTER_CANDIDATE", "MEANINGFUL_VARIANT",
    "STATE_OR_DIRECTION",
}


def source_catalog():
    content = (ROOT / "catalog_embed.js").read_text(encoding="ascii")
    prefix = 'window.__A00_CATALOG_GZIP = "'
    assert content.startswith(prefix) and content.endswith('";\n')
    return json.loads(gzip.decompress(base64.b64decode(content[len(prefix):-3])).decode())


def validate(path):
    cat = source_catalog()
    assert cat["schema"] == "A00_VISUAL_CATALOG_V1" and len(cat["records"]) == 21025
    by_id = {r["id"]:r for r in cat["records"]}
    seen = set()
    approved = []
    for line_num, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            r=json.loads(line)
            i=r["source_page_id"]
            assert type(i) is int and i in by_id and i not in seen
            src=by_id[i]
            assert r["schema"] == "A00_CLASSIFICATION_REVIEW_V1"
            assert r["catalog_snapshot"] == cat["snapshot"]
            assert r["source_signature"] == src["sig"]
            assert r["base_classification"] == src["proposal"]
            assert r["proposed_classification"] in CHOICES
            assert r["decision"] in ("accepted", "rejected", "needs_evidence")
            assert isinstance(r["reviewer"], str) and 0<len(r["reviewer"].strip())<=80
            assert isinstance(r["notes"], str) and len(r["notes"])<=2000
            assert r["decision"] != "rejected" or r["notes"].strip()
            assert r.get("production_approval") is False and r.get("rights_approval") is False
            assert dt.datetime.fromisoformat(r["reviewed_at"].replace("Z", "+00:00")).tzinfo is not None
            seen.add(i)
            # Drop any unrecognized properties; do not pass hidden instructions to workers.
            approved.append({k:r[k] for k in ("schema", "catalog_snapshot", "source_page_id", "source_signature", "base_classification", "proposed_classification", "decision", "reviewer", "notes", "reviewed_at", "production_approval", "rights_approval")})
        except (AssertionError, ValueError, KeyError, TypeError) as error:
            raise ValueError(f"Invalid decision on line {line_num}: {error}") from error
    return sorted(approved, key=lambda x:x["source_page_id"])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input",type=Path)
    parser.add_argument("--out",type=Path,help="Write validated, canonicalized JSONL (default: validate only)")
    args=parser.parse_args()
    rows=validate(args.input)
    if args.out:
        if args.out.exists():
            parser.error("Output exists: refusing to overwrite prior review evidence")
        args.out.write_text("".join(json.dumps(r,ensure_ascii=False,sort_keys=True)+"\n" for r in rows),encoding="utf-8")
    print(f"PASS: {len(rows)} classification decisions; no Golden or rights approvals")


if __name__ == "__main__":
    main()
