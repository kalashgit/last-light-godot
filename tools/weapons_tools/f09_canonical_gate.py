"""Fail-closed F09 source-to-canonical reconciliation. No Blender dependency."""
import argparse
import json
from pathlib import Path

SOURCE_KEYS = ("asset_id", "archetype")
REQUIRED_EVIDENCE = ("content_id", "semantic_verification", "production_queue", "source_asset_id", "registry_url")

def audit(recipes, registry):
    assets = recipes.get("assets", [])
    errors = []
    seen = set()
    mappings = []
    for asset in assets:
        source = asset.get("asset_id")
        if not source or source in seen:
            errors.append(f"duplicate_or_missing_source:{source}")
            continue
        seen.add(source)
        matches = [r for r in registry if r.get("source_asset_id") == source]
        if len(matches) != 1:
            errors.append(f"canonical_mapping_count:{source}:{len(matches)}")
            continue
        record = matches[0]
        if any(not record.get(k) for k in REQUIRED_EVIDENCE):
            errors.append(f"missing_evidence:{source}")
            continue
        if record["semantic_verification"] != "Canonical Verified" or record["production_queue"] != "F09":
            errors.append(f"unverified_or_wrong_queue:{source}")
            continue
        if record.get("founder_visual_approved") is not True:
            errors.append(f"founder_gate_pending:{source}")
            continue
        mappings.append({"source_asset_id": source, "content_id": record["content_id"]})
    ids = [m["content_id"] for m in mappings]
    if len(ids) != len(set(ids)):
        errors.append("duplicate_canonical_content_id")
    return {"status": "READY_FOR_REVIEW" if not errors and len(mappings) == len(assets) else "BLOCKED_CANONICAL_IDS",
            "source_count": len(assets), "mapped_count": len(mappings), "mappings": mappings, "errors": errors}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--recipes", default="tools/weapons_tools/recipes.json")
    parser.add_argument("--registry", required=True, help="Explicit reviewed A00 JSON snapshot; never generated from recipe names")
    parser.add_argument("--output", default="-")
    args = parser.parse_args()
    result = audit(json.loads(Path(args.recipes).read_text()), json.loads(Path(args.registry).read_text()))
    output = json.dumps(result, indent=2, sort_keys=True)
    if args.output == "-":
        print(output)
    else:
        Path(args.output).write_text(output + "\n")
    raise SystemExit(0 if result["status"] == "READY_FOR_REVIEW" else 2)

if __name__ == "__main__":
    main()
