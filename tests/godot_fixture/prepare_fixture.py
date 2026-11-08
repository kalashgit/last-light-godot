#!/usr/bin/env python3
"""Prepare real F12 Blender PNGs as verified RGBA atlases for isolated Godot.

Does not grant A00, Golden, rights, game, or device approval.
Usage: python tests/godot_fixture/prepare_fixture.py RAW_ARTIFACT_DIR
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys
from PIL import Image

CASES = {"cube": 1, "vehicle": 16, "cow": 16, "fridge": 7}
GRID = {"cube": 1, "vehicle": 4, "cow": 4, "fridge": 4}
SIZE = (384, 384)


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def require(value, message):
    if not value:
        raise RuntimeError(message)


def prepare(artifact_root, dest):
    reports = list(artifact_root.rglob("render_report.json"))
    require(len(reports) == 1, f"expected exactly one render report, found {len(reports)}")
    root = reports[0].parent.resolve()
    report = json.loads(reports[0].read_text())
    frames = report.get("frames", [])
    require(len(frames) == sum(CASES.values()), f"expected 40 frames, got {len(frames)}")
    require(set(report.get("results", {})) == set(CASES), "source results incomplete")
    dest.mkdir(parents=True, exist_ok=True)
    result = {"schema_version": 1, "approval_status": "CALIBRATION_ONLY",
              "source_run_id": 42533683097, "logical_tile_px": [80, 40],
              "renderer_input_sha256": sha256(reports[0]),
              "cases": {}}
    for subject, count in CASES.items():
        group = [x for x in frames if x.get("slug") == subject]
        require(len(group) == count, f"{subject} frame count mismatch")
        require(all(x.get("sha256") for x in group), f"{subject} has missing SHA")
        if subject == "vehicle":
            require({r["heading"] for r in group} == set(range(16)), "vehicle missing 16 headings")
        if subject == "cow":
            require({(r["heading"], r["source_frame"]) for r in group}
                    == {(h, pose) for h in range(8) for pose in (1, 4)}, "cow 8x2 mismatch")
        if subject == "fridge":
            require({r["source_frame"] for r in group} == set(range(1, 8)), "fridge door sequence invalid")
            require(report["results"]["fridge"].get("max_hinge_screen_distance_px", 1000) < 35,
                    "fridge failed repaired hinge guard")
        # Exact deterministic atlas assignment by heading then source frame.
        group.sort(key=lambda x: (x["heading"], x["source_frame"]))
        cols = GRID[subject]
        rows = (count + cols - 1) // cols
        atlas = Image.new("RGBA", (cols * SIZE[0], rows * SIZE[1]), (0, 0, 0, 0))
        regions = []
        for index, frame in enumerate(group):
            rel = frame["png"]
            require(isinstance(rel, str) and not Path(rel).is_absolute()
                    and ".." not in Path(rel).parts, "unsafe source frame path")
            frame_path = (root / rel).resolve()
            require(frame_path.is_relative_to(root) and frame_path.is_file(),
                    f"missing real frame {rel}")
            require(sha256(frame_path) == frame["sha256"], f"frame SHA mismatch {rel}")
            with Image.open(frame_path) as image:
                require(image.mode == "RGBA" and image.size == SIZE, f"invalid RGBA {rel}")
                require(image.getchannel("A").getbbox() is not None, f"blank alpha {rel}")
                x, y = index % cols * SIZE[0], index // cols * SIZE[1]
                atlas.alpha_composite(image, (x, y))
            regions.append({"heading": frame["heading"], "source_frame": frame["source_frame"],
                            "rect": [x, y, SIZE[0], SIZE[1]],
                            "ground_pivot_px": frame["origin_px"],
                            "original_sha256": frame["sha256"],
                            "duration_ms": 100})
        atlas_file = dest / f"{subject}_atlas.png"
        atlas.save(atlas_file)
        result["cases"][subject] = {"atlas": atlas_file.name, "atlas_sha256": sha256(atlas_file),
                                    "size": list(atlas.size), "frames": regions,
                                    "source_model_sha256": report["results"][subject]["source_sha"]}
    manifest = dest / "fixture_manifest.json"
    manifest.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"status": "PASS_REAL_SOURCE_TO_ATLAS",
                      "case_count": len(result["cases"]), "frame_count": len(frames),
                      "manifest_sha256": sha256(manifest)}, sort_keys=True))
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("artifact_root", type=Path)
    parser.add_argument("--output", type=Path,
                        default=Path("tests/godot_fixture/generated"))
    a = parser.parse_args()
    prepare(a.artifact_root, a.output)
