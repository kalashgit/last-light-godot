#!/usr/bin/env python3
"""Build a standalone Godot 4.3 inspection project ZIP without editing project.godot.

This exports only original procedural DEBUG art and includes no Golden-approved
asset content. Device behavior must be tested manually on iPhone/Xogot.
"""
from pathlib import Path
import argparse
import shutil
import zipfile

ROOT = Path(__file__).resolve().parents[2]
REQUIRED = [
    "scenes/all_archetypes_neighborhood_v1.tscn",
    "scripts/all_archetypes_neighborhood_v1.gd",
    "data/generated/all_archetypes_neighborhood_v1.json",
    "tests/neighborhood/smoke_scene.gd",
]

PREVIEW_PROJECT = """config_version=5

[application]
config/name="LAST LIGHT — All Buildings QA Preview"
run/main_scene="res://scenes/all_archetypes_neighborhood_v1.tscn"
config/features=PackedStringArray("4.3", "GL Compatibility")

[display]
window/size/viewport_width=720
window/size/viewport_height=1152
window/stretch/mode="canvas_items"
window/handheld/orientation=1

[rendering]
renderer/rendering_method="gl_compatibility"
renderer/rendering_method.mobile="gl_compatibility"
textures/default_filters/use_nearest_mipmap_filter=false
"""

PREVIEW_README = """# LAST LIGHT — 63 Building Technical Neighborhood

Godot 4.3 standalone inspection project; does NOT modify the real game.
Run the default scene after importing this folder in Godot/Xogot.

Contains 60 original catalog archetype PLACEHOLDERS plus 3 existing-house
layout variants. Districts: House Quarter, Market, Civic, Works, Parks, Special.
Left thumbstick moves, right ENTER interacts, six top tabs jump to districts.
Desktop: arrow keys, E/Space, R for roof visibility, 1–6 district inspection.

All building art is debug geometry, NOT Golden-approved F02 assets.
Many building interiors, zombies, loot and damage are metadata only.
Real iPhone gameplay/performance is NOT verified.
This archive is a temporary review tool, not the official game.
"""

def build(output_dir: Path):
    project = output_dir / "LAST_LIGHT_63_BUILDINGS_GODOT_4_3_PREVIEW"
    project.mkdir(parents=True, exist_ok=True)
    for rel in REQUIRED:
        src = ROOT / rel
        if not src.is_file():
            raise RuntimeError(f"missing source {src}")
        destination = project / rel
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, destination)
    (project / "project.godot").write_text(PREVIEW_PROJECT, encoding="utf8")
    (project / "README.md").write_text(PREVIEW_README, encoding="utf8")
    target = output_dir / "LAST_LIGHT_63_BUILDINGS_GODOT_4_3_PREVIEW.zip"
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for file in sorted(project.rglob("*")):
            if not file.is_file():
                continue
            rel = file.relative_to(output_dir)
            info = zipfile.ZipInfo(rel.as_posix(), (1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            zf.writestr(info, file.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    print(f"NEIGHBORHOOD_PORTABLE_GODOT_PREVIEW_BUILT path={target} bytes={target.stat().st_size}")
    return project, target

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=ROOT / "build" / "neighborhood_preview")
    args = parser.parse_args()
    build(args.output_dir)
