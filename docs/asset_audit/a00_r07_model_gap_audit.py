#!/usr/bin/env python3
"""R07: recover unreviewed model-image evidence without admitting new assets.

This pass reuses the immutable B001–B008 PZwiki source census. An image in
"Item models" or "Vehicle models" is evidence of a visible representation,
not proof of a distinct underlying 3D geometry file or LAST LIGHT requirement.
"""
import argparse
import base64
import collections
import gzip
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
GEOMETRY_SNAPSHOT = ROOT / "a00_r07_existing_geometry_360.json"


def source_files():
    paths = []
    for name in ("b001_300", "b002_300", "b003_500", "b004_1000"):
        paths.extend(ROOT.glob(f"a00_20261108_{name}.jsonl"))
    for name in ("b005_3000", "b006_3000", "b007_8000", "b008_4925"):
        paths.extend(sorted(ROOT.glob(f"a00_20261108_{name}_part_*.jsonl")))
    return paths


def iter_rows(paths):
    for path in paths:
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    yield json.loads(line)


def normalized_stem(title):
    title = title.removeprefix("File:")
    stem = title.rsplit(".", 1)[0]
    return re.sub(r"[^a-z0-9]", "", stem.casefold())


def strip_model_suffix(title):
    stem = title.removeprefix("File:").rsplit(".", 1)[0]
    return re.sub(r"(?i)\s+model$", "", stem).strip()


def provisional_family(source, vehicle):
    if vehicle:
        return "F10"
    cats = " ".join(source["source_categories"]).casefold()
    title = source["source_title"].removeprefix("File:").casefold()
    if title.startswith(("mattress", "fridge", "refrigerator", "microwave", "washingmachine", "bedframe", "wardrobe", "cabinet", "bookshelf", "sofa", "toaster")):
        return "F01"
    if any(word in cats for word in ("jacket models", "hat models", "suit models", "bag models", "jewelry models", "shoe models", "shirt models", "pants models", "clothing models", "underwear models")):
        return "F05"
    if title.startswith(("baseballcap", "socks", "scarf", "shirt", "trousers", "underwear", "sweatband", "headband", "hardhat")):
        return "F05"
    return "F09"


def import_existing_geometry(ref):
    """Store only verified manifest identities, not licensed external artwork."""
    path = "preview/geometry-first-all-360/batch_report.json"
    result = subprocess.run(["git", "show", f"{ref}:{path}"], check=True, capture_output=True)
    report = json.loads(result.stdout)
    ids = sorted({r["asset_id"] for r in report["items"]})
    assert report["generated_3d_source_count"] == len(ids) == 360
    snapshot = {
        "source_repo_path": path,
        "source_git_ref": ref,
        "source_sha256": hashlib.sha256(result.stdout).hexdigest(),
        "geometry_ids": ids,
        "status": report["status"],
        "visual_qa_approved": False,
    }
    GEOMETRY_SNAPSHOT.write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")


def geometry_lexical_links():
    snapshot = json.loads(GEOMETRY_SNAPSHOT.read_text(encoding="utf-8"))
    ids = snapshot["geometry_ids"]
    assert len(ids) == len(set(ids)) == 360
    by_stem = collections.defaultdict(list)
    for asset_id in ids:
        tokens = asset_id.split("_")
        if len(tokens) >= 3 and tokens[0] == "ll":
            by_stem[normalized_stem("_".join(tokens[2:]))].append(asset_id)
    return by_stem, snapshot


def audit():
    sources = list(iter_rows(source_files()))
    reviewed_ids = {r["id"] for r in iter_rows(sorted(ROOT.glob("a00_r02_review_*.jsonl")))}
    assert len(sources) == len({r["source_page_id"] for r in sources}) == 21025
    assert len(reviewed_ids) == 6072

    icon_ids = collections.defaultdict(list)
    geometry, geometry_snapshot = geometry_lexical_links()
    for r in sources:
        if "Category:Item icons" in r["source_categories"]:
            icon_ids[normalized_stem(r["source_title"])].append(r["source_page_id"])

    model_categories = ("Category:Item models", "Category:Vehicle models")
    all_model_images = [r for r in sources if any(c in r["source_categories"] for c in model_categories)]
    unreviewed = [r for r in all_model_images if r["source_page_id"] not in reviewed_ids]
    ledger = []
    for r in unreviewed:
        vehicle = "Category:Vehicle models" in r["source_categories"]
        root = strip_model_suffix(r["source_title"])
        exact_icons = sorted(icon_ids.get(normalized_stem(root), [])) if not vehicle else []
        existing_geometry_ids = sorted(geometry.get(normalized_stem(root), []))
        bucket = (
            "VEHICLE_MODEL_IMAGE_REQUIRES_ARCHETYPE_REVIEW" if vehicle else
            "ITEM_MODEL_IMAGE_WITH_ICON_LINK" if exact_icons else
            "ITEM_MODEL_IMAGE_WITHOUT_EXACT_ICON_LINK"
        )
        ledger.append({
            "source_page_id": r["source_page_id"],
            "source_title": r["source_title"],
            "source_url": r["source_url"],
            "previous_classification": r["primary_class"],
            "category": "VEHICLE_MODEL_IMAGE" if vehicle else "ITEM_MODEL_IMAGE",
            "evidence_class": bucket,
            "provisional_model_stem": root,
            "provisional_queue": provisional_family(r, vehicle),
            "exact_normalized_icon_source_ids": exact_icons,
            "existing_360_exact_lexical_ids": existing_geometry_ids,
            "recommendation": "VISUALLY_REVIEW_EXISTING_MODEL_EVIDENCE_BEFORE_CREATING_OR_MERGING_MASTER",
            "rights": "source_research_only",
            "canonical_master_admitted": False,
            "new_geometry_proven": False,
        })

    counts = collections.Counter(r["evidence_class"] for r in ledger)
    assert len(unreviewed) == len(ledger)
    assert len(all_model_images) == 3599, "Source snapshot changed; inspect before accepting new totals"
    assert len(ledger) == 3539, "R02 membership changed; inspect before accepting new totals"
    summary = {
        "schema": "A00_R07_MODEL_IMAGE_GAP_AUDIT_V1",
        "method": "Existing 21,025-record B001–B008 metadata only; no new source crawl or binary game model extraction",
        "total_source_file_pages": len(sources),
        "r02_semantically_triaged": len(reviewed_ids),
        "source_file_pages_not_in_r02": len(sources) - len(reviewed_ids),
        "item_model_images_total": sum("Category:Item models" in r["source_categories"] for r in sources),
        "vehicle_model_images_total": sum("Category:Vehicle models" in r["source_categories"] for r in sources),
        "unique_model_image_source_page_ids": len(all_model_images),
        "model_image_pages_already_in_r02": len(all_model_images) - len(unreviewed),
        "new_model_evidence_review_queue": len(ledger),
        "evidence_buckets": dict(sorted(counts.items())),
        "distinct_provisional_model_stems": len({normalized_stem(x["provisional_model_stem"]) for x in ledger}),
        "provisional_family_queue_counts": dict(sorted(collections.Counter(x["provisional_queue"] for x in ledger).items())),
        "existing_geometry_manifest_total": len(geometry_snapshot["geometry_ids"]),
        "existing_geometry_source_ref": geometry_snapshot["source_git_ref"],
        "model_images_with_strict_360_name_link": sum(bool(x["existing_360_exact_lexical_ids"]) for x in ledger),
        "can_validate_4807_unique_3d_models": False,
        "cannot_infer_from_wiki_images": [
            "Count of unique game model binaries",
            "Count of distinct LAST LIGHT Blender meshes needed",
            "Final gameplay necessity or art rights",
            "Whether unnamed game model files lack wiki imagery",
        ],
        "production_status": "EVIDENCE_ONLY_NOT_CANONICAL_NOT_GOLDEN",
    }
    return ledger, summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--import-geometry-manifest-from-ref", help="One-time snapshot of 360 geometry IDs from an already fetched Git ref")
    args = parser.parse_args()
    if args.import_geometry_manifest_from_ref:
        import_existing_geometry(args.import_geometry_manifest_from_ref)
    ledger, summary = audit()
    output = "".join(json.dumps(x, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n" for x in ledger).encode()
    compressed = gzip.compress(output, mtime=0, compresslevel=9)
    (ROOT / "a00_r07_model_evidence_queue.jsonl.gz.base64").write_text(base64.b64encode(compressed).decode() + "\n", encoding="ascii")
    summary.update({"ledger_sha256": hashlib.sha256(output).hexdigest(), "ledger_rows": len(ledger)})
    (ROOT / "a00_r07_model_gap_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(f"PASS: {summary['new_model_evidence_review_queue']} previously unreviewed model images; {dict(summary['evidence_buckets'])}")


if __name__ == "__main__":
    main()
