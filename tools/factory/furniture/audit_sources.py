"""Read-only F01 source/identity audit; never promotes records to Golden."""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SNAPSHOT = ROOT / "docs/production/f01/a00_verified_snapshot_20261108.json"
REPORT = ROOT / "preview/geometry-first-all-360/batch_report.json"


def audit(snapshot, report):
    source = {row["asset_id"]: row for row in report["items"]}
    seen = set()
    results = []
    for row in snapshot["records"]:
        identity = row["canonical_master_id"]
        assert identity not in seen, f"Duplicate canonical identity: {identity}"
        seen.add(identity)
        assert row["queue"] == "F01"
        assert row["semantic_verification"] == "Canonical Verified"
        assert row["source_revision"] and row["notion_asset_url"]
        matches = [source[c] for c in row["existing_source_candidates"] if c in source]
        results.append({
            "canonical_master_id": identity,
            "source_revision": row["source_revision"],
            "source_candidates": [{
                "source_id": m["asset_id"],
                "bounds_m": m["actual_bounds_m"],
                "geometry_status": m["geometry_status"],
                "recipe_hash": m["recipe_hash"],
                "glb_sha256": m["glb_sha256"]
            } for m in matches],
            "missing_source_candidates": [c for c in row["existing_source_candidates"] if c not in source],
            "production_ready": False,
            "blockers": ["RIGHTS_REVIEW_PENDING", "FOUNDER_VISUAL_APPROVAL_PENDING", "BLENDER_REFINEMENT_UNTESTED"]
        })
    return {"scope": "PARTIAL_VERIFIED_ROWS_ONLY", "audited_records": len(results), "records": results}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot", type=Path, default=SNAPSHOT)
    parser.add_argument("--report", type=Path, default=REPORT)
    args = parser.parse_args()
    print(json.dumps(audit(json.loads(args.snapshot.read_text()), json.loads(args.report.read_text())), indent=2))


if __name__ == "__main__":
    main()
