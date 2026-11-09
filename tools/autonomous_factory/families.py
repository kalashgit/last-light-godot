"""Fail-closed, all-family production admission and deterministic queue reporting."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = Path(__file__).with_name("family_registry.json")


def validate(records):
    if records.get("schema_version") != 1:
        raise ValueError("unsupported registry schema")
    families = records["families"]
    actual = [x["id"] for x in families]
    expected = [f"F{i:02d}" for i in range(1, 13)]
    if actual != expected or len(actual) != len(set(actual)):
        raise ValueError("registry must contain every F01-F12 family exactly once, ordered")
    for row in families:
        if row["canonical_promotion"] is not False:
            raise ValueError(f"{row['id']} attempts production promotion")
        if row["readiness"] == "CALIBRATION_RUNNABLE":
            if row["adapter"] != "f01_refrigerator_v10" or row["id"] != "F01":
                raise ValueError("unverified adapter marked executable")
            if not (ROOT / "tools/factory/furniture/refrigerator_calibration.py").is_file():
                raise ValueError("F01 source missing")
        elif row["adapter"] is not None:
            raise ValueError(f"unverified adapter attached to {row['id']}")
    return families


def plan(registry, requested):
    rows = validate(registry)
    chosen = rows if requested == "ALL" else [r for r in rows if r["id"] == requested]
    if not chosen:
        raise ValueError("unknown family")
    return {"schema_version": 1, "requested": requested,
            "ready": [r["id"] for r in chosen if r["readiness"] == "CALIBRATION_RUNNABLE"],
            "blocked": [{"id": r["id"], "reason": r["readiness"], "source_branch": r["source_branch"]}
                        for r in chosen if r["readiness"] != "CALIBRATION_RUNNABLE"],
            "golden_approved": [], "merges_authorized": False,
            "source_registry_sha256": hashlib.sha256(REGISTRY.read_bytes()).hexdigest()}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--family", default="ALL", choices=["ALL", *[f"F{i:02d}" for i in range(1, 13)]])
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    result = plan(json.loads(REGISTRY.read_text()), args.family)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(f"M02_FAMILY_PLAN ready={len(result['ready'])} blocked={len(result['blocked'])}")


if __name__ == "__main__":
    main()
