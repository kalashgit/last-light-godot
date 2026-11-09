#!/usr/bin/env python3
"""SYNTHETIC stand-in for W01's tests/godot_fixture/generated output.

Used ONLY when the real F12 Blender artifact is unavailable (it lives in an
authenticated GitHub Actions run). Writes the exact fixture_manifest.json and
v2_<subject>_package.json shapes produced by prepare_fixture.py, with simple
flat-shaded frames. It proves Worker 04's consumer code paths, NOT F12 output,
art quality or any approval. Every file is labelled SYNTHETIC.
"""
import hashlib
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw

SIZE = 384
CASES = {"fridge": (7, 4, "F01"), "vehicle": (16, 4, "F10")}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main(dest):
    dest = Path(dest)
    dest.mkdir(parents=True, exist_ok=True)
    result = {"schema_version": 1, "approval_status": "CALIBRATION_ONLY", "logical_tile_px": [80, 40],
              "synthetic": "SYNTHETIC_FORMAT_CONFORMANCE_NOT_F12_OUTPUT", "cases": {}}
    for subject, (count, cols, _family) in CASES.items():
        rows = (count + cols - 1) // cols
        atlas = Image.new("RGBA", (cols * SIZE, rows * SIZE), (0, 0, 0, 0))
        regions = []
        for i in range(count):
            x, y = i % cols * SIZE, i // cols * SIZE
            d = ImageDraw.Draw(atlas)
            if subject == "fridge":
                d.polygon([(x + 162, y + 300), (x + 222, y + 330), (x + 222, y + 190), (x + 162, y + 160)], fill=(200, 205, 200, 255))
                d.polygon([(x + 222, y + 330), (x + 262, y + 310), (x + 262, y + 170), (x + 222, y + 190)], fill=(150, 156, 150, 255))
                d.line([(x + 222, y + 250), (x + 222 + i * 6, y + 250 - i * 3)], fill=(60, 60, 60, 255), width=3)
            else:
                d.polygon([(x + 120, y + 250), (x + 200, y + 290), (x + 270, y + 255), (x + 190, y + 215)], fill=(120, 60 + i * 8, 70, 255))
                d.polygon([(x + 160, y + 245), (x + 205, y + 268), (x + 240, y + 250), (x + 195, y + 228)], fill=(50, 60, 70, 255))
            regions.append({"heading": i if subject == "vehicle" else 0, "source_frame": 1 if subject == "vehicle" else i + 1,
                            "rect": [x, y, SIZE, SIZE], "ground_pivot_px": [192, 270], "original_sha256": "0" * 64,
                            "duration_ms": 100})
        atlas_file = dest / f"{subject}_atlas.png"
        atlas.save(atlas_file)
        result["cases"][subject] = {"atlas": atlas_file.name, "atlas_sha256": sha(atlas_file), "size": list(atlas.size),
                                    "frames": regions, "source_model_sha256": hashlib.sha256(f"synthetic-{subject}".encode()).hexdigest()}
    manifest = dest / "fixture_manifest.json"
    manifest.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    for subject, (_c, _cols, family) in CASES.items():
        info = result["cases"][subject]
        pkg = {"schema_version": 2, "package_id": f"LL-{family}-SYNTHETIC-{subject.upper()}-W04-CONFORMANCE", "family": family,
               "stage": "CALIBRATION",
               "source": {"sha256": info["source_model_sha256"], "archive_uri": "synthetic://not-a-source-model",
                          "builder_commit": "0" * 40},
               "renderer": {"commit": "0" * 40, "profile": "SYNTHETIC_FORMAT_CONFORMANCE_NOT_F12",
                            "directions": 16 if subject == "vehicle" else 1, "logical_tile_px": [80, 40]},
               "material_recipe_ids": [],
               "artifacts": [{"kind": "atlas", "uri": "./" + info["atlas"], "sha256": info["atlas_sha256"]},
                             {"kind": "metadata", "uri": "./fixture_manifest.json", "sha256": sha(manifest)}],
               "approval_note": "SYNTHETIC; never a game asset", "mass_production_authorized": False}
        (dest / f"v2_{subject}_package.json").write_text(json.dumps(pkg, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"status": "SYNTHETIC_FIXTURE_WRITTEN", "dir": str(dest)}))


if __name__ == "__main__":
    main(sys.argv[1])
