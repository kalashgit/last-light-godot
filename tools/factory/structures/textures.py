"""Deterministic original material swatches for F02 calibration only.

These lightweight PBR base-colour maps use no external images. F11 must approve
shared production material IDs, roughness and any final normal-map process.
"""
from __future__ import annotations

from pathlib import Path
import hashlib
import json
import random

PALETTE = {
    "plaster": ((189, 178, 155), 0.86, 0.0),
    "brick": ((148, 96, 78), 0.91, 0.0),
    "concrete": ((135, 138, 130), 0.94, 0.0),
    "timber": ((126, 94, 63), 0.82, 0.0),
    "ceramic": ((163, 158, 139), 0.43, 0.0),
    "trim": ((88, 91, 81), 0.55, 0.0),
    "glass": ((129, 174, 187), 0.10, 0.0),
    "door_wood": ((101, 76, 57), 0.61, 0.0),
    "steel": ((87, 96, 100), 0.42, 0.72),
    "metal_roof": ((100, 111, 112), 0.65, 0.62),
    "shingle": ((70, 75, 76), 0.95, 0.0),
    "membrane": ((75, 79, 77), 0.96, 0.0),
}


def make_maps(directory: Path, resolution: int = 128) -> dict:
    from PIL import Image
    directory.mkdir(parents=True, exist_ok=True)
    output = {}
    for material, (base, rough, metal) in PALETTE.items():
        rng = random.Random(f"F02_original_V1:{material}")
        image = Image.new("RGB", (resolution, resolution))
        px = image.load()
        for y in range(resolution):
            for x in range(resolution):
                grain = rng.randrange(-5, 6)
                if material in ("timber", "door_wood"):
                    grain += int(5 * __import__("math").sin(x*.24 + 1.8*__import__("math").sin(y*.04)))
                if material == "brick":
                    row = y // 22
                    mortar = y % 22 <= 1 or (x + (row % 2)*24) % 48 <= 2
                    grain += -32 if mortar else 0
                if material in ("shingle", "metal_roof"):
                    grain += -14 if y % 24 <= 1 else 0
                if material == "ceramic":
                    grain += -20 if x % 40 <= 1 or y % 40 <= 1 else 0
                if material == "steel":
                    grain += (2 if x % 11 == 0 else 0)
                px[x, y] = tuple(max(0, min(255, c+grain)) for c in base)
        target = directory / f"{material}_basecolor.png"
        image.save(target)
        output[material] = {"basecolor_file": target.name,
                            "sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
                            "roughness": rough, "metallic": metal,
                            "status": "ORIGINAL_CALIBRATION_UNAPPROVED_F11"}
    return output


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--output-dir", type=Path, required=True)
    a = p.parse_args()
    manifest = make_maps(a.output_dir)
    print(json.dumps(manifest, indent=2))
