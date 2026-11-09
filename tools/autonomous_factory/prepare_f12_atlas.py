"""Adapter from measured F12 CAL-01 candidate frames to pinned F12 atlas CLI.

Only bridges documented metadata; the atlas layout/compositor code stays pinned
to the original F12 specialist commit, never copied into the F01 source.
"""
import argparse
import json
from pathlib import Path

from tools.autonomous_factory.qa_shared import check_f12_report


def adapt(report):
    check_f12_report(report)
    frames = []
    for frame in report["frames"]:
        angle = frame["degrees"]
        frames.append({
            "key": f"f01_refrigerator_cal01_idle_{angle:03d}",
            "file": frame["file"],
            "width": 256,
            "height": 256,
            "duration_ms": 100,
            "direction": (angle // 90) * 4,
            "clip": "idle_calibration",
            "source_sha256": frame["sha256"],
        })
    return {
        "schema_version": 1,
        "status": "F12_CAL01_ATLAS_INPUT_UNAPPROVED",
        "tile_logical_pixels": [80, 40],
        "ground_anchor_px": [128, 128],
        "founder_approved": False,
        "frames": frames,
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("candidate_dir", type=Path)
    args = p.parse_args()
    root = args.candidate_dir
    candidate = json.loads((root / "f12_candidate.json").read_text())
    output = adapt(candidate)
    (root / "atlas_input.json").write_text(json.dumps(output, indent=2) + "\n")
    print("M02_F12_ATLAS_INPUT_PASS", len(output["frames"]))


if __name__ == "__main__":
    main()
