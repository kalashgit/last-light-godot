#!/usr/bin/env python3
"""Generate a read-only reference catalog from A00 census and R02 review shards."""
import glob
import hashlib
import json
import base64
import gzip
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent


def rows(paths):
    for path in paths:
        with open(path, encoding="utf-8") as stream:
            for line in stream:
                if line.strip():
                    yield json.loads(line)


def files():
    paths = []
    for name in ("b001_300", "b002_300", "b003_500", "b004_1000"):
        paths.extend(ROOT.glob(f"a00_20261108_{name}.jsonl"))
    for name in ("b005_3000", "b006_3000", "b007_8000", "b008_4925"):
        paths.extend(sorted(ROOT.glob(f"a00_20261108_{name}_part_*.jsonl")))
    return paths


def signature(page_id, title):
    return hashlib.sha256(f"{page_id}|{title}".encode("utf-8")).hexdigest()[:16]


def main():
    first_pass = list(rows(files()))
    second_pass = {r["id"]: r for r in rows(sorted(ROOT.glob("a00_r02_review_*.jsonl")))}
    assert len(first_pass) == 21025
    assert len({r["source_page_id"] for r in first_pass}) == 21025
    assert len(second_pass) == 6072

    compact = []
    for r in first_pass:
        i = r["source_page_id"]
        s = second_pass.get(i)
        title = r["source_title"].removeprefix("File:")
        entry = {
            "id": i,
            "name": title,
            "url": r["source_url"],
            "category": r["primary_class"],
            "proposal": s["decision"] if s else r["primary_class"],
            "family": s["family"] if s else r.get("suggested_queue"),
            "key": s["key"] if s else (r.get("proposed_parent_stem") or ""),
            "parent": s["parent_id"] if s and s["parent_id"] is not None else r.get("parent_source_page_id"),
            "canonical": (s.get("master") if s else None) or r.get("master_id"),
            "models": s["model_ids"] if s else [],
            "categories": [x.removeprefix("Category:") for x in r.get("source_categories", []) if "copyright" not in x.casefold()],
            "reason": r.get("reason") or "",
            "rights": r.get("rights", "source_research_only"),
            "r02": bool(s),
            "confidence": s["confidence"] if s else None,
            "sig": signature(i, title),
        }
        compact.append(entry)
    digest = hashlib.sha256("\n".join(f'{r["id"]}:{r["sig"]}' for r in compact).encode()).hexdigest()
    payload = {"schema": "A00_VISUAL_CATALOG_V1", "archive_count": len(compact), "r02_count": len(second_pass), "snapshot": digest, "records": compact}
    encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    # Browser-native gzip extraction reduces the 21k-entry transfer ~85%; this
    # also works from a local folder without fetch(file://...) access.
    compressed = gzip.compress(encoded, compresslevel=9, mtime=0)
    embedded = base64.b64encode(compressed).decode("ascii")
    (OUT / "catalog_embed.js").write_text(f'window.__A00_CATALOG_GZIP = "{embedded}";\n', encoding="ascii")
    (OUT / "catalog_manifest.json").write_text(json.dumps({"schema": payload["schema"], "archive_count": len(compact), "r02_count": len(second_pass), "snapshot": digest, "catalog_sha256": hashlib.sha256(encoded).hexdigest(), "compressed_sha256": hashlib.sha256(compressed).hexdigest(), "compressed_bytes": len(compressed)}, indent=2) + "\n", encoding="utf-8")
    print(f"Catalog: {len(compact)} sources, {len(second_pass)} R02 records, snapshot {digest[:14]}")


if __name__ == "__main__":
    main()
