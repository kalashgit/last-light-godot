"""F02 cross-family review report; never self-certifies F11/F12 approval.

Reads the actual LAST LIGHT 2D house projection, compares F02 tile geometry,
checks planned F11 PBR channels, and records blocking integration conditions.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from geometry import make_plan
from textures import PALETTE

REQUIRED_CHANNELS = ("basecolor", "roughness", "metallic", "normal")


def evaluate(house_source: Path) -> dict:
    code = house_source.read_text(encoding="utf-8")
    def measure(name: str) -> float:
        m = re.search(r"^const\s+" + re.escape(name) + r"\s*:=\s*([0-9.]+)", code, re.MULTILINE)
        if not m:
            raise ValueError(f"Missing gameplay projection constant {name}")
        return float(m.group(1))

    tx, ty = measure("TX"), measure("TY")
    f02 = make_plan("small_house").manifest()["render_contract"]["tile_px"]
    projection_matches = tx * 2 == f02[0] and ty * 2 == f02[1] and tx == 2 * ty

    # F02 currently authors albedo only. Scalar roughness and metalness in
    # Blender node values are not equivalent to baked portable PBR channels.
    material_issues = []
    for name, (_, rough, metal) in PALETTE.items():
        if not (0 <= rough <= 1 and 0 <= metal <= 1):
            material_issues.append(f"{name}: scalar outside [0,1]")
        material_issues.append(f"{name}: missing portable roughness/metallic/normal maps")

    return {
        "status": "NONCANONICAL_CALIBRATION_ONLY",
        "source_gameplay": str(house_source),
        "world_tile_px": f02,
        "gameplay_iso": {"TX": tx, "TY": ty},
        "projection_tile_dimensions_match": projection_matches,
        "f12_approval": "PENDING_CAMERA_FACING_ANCHOR_LIGHTING_AND_PIXEL_QA",
        "f11_approval": "PENDING_PORTABLE_PBR_CHANNELS_AND_F11_REVIEW",
        "f11_material_issues": material_issues,
        "actual_f02_sprite_import_in_game": False,
        "iphone_verified": False,
        "canonical_id_authorized": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--house", type=Path, default=Path("scripts/house.gd"))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = evaluate(args.house)
    output = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output)
    else:
        print(output)
    if not report["projection_tile_dimensions_match"]:
        raise SystemExit("F02_F12_TILE_GEOMETRY_MISMATCH")


if __name__ == "__main__":
    main()
