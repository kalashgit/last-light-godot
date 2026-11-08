"""Install QA-verified Blender terrain sprite candidates in the Godot project.

This is a reproducible copy/manifest bridge. It never changes the main scene
or promotes a sprite to Founder Golden approval.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path

from PIL import Image

import qa


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def install(sources, target, expected):
    if target.is_absolute():
        raise ValueError("Target must be a Godot res://-relative repository path")
    assets = qa.verify(sources, expected)
    original = json.loads((sources / "manifest.json").read_text())
    first_source_meta = json.loads((sources / assets[0] / "asset.json").read_text())
    planned = []
    for key in assets:
        folder = sources / key
        meta = json.loads((folder / "asset.json").read_text())
        source = folder / "world.png"
        with Image.open(source) as im:
            if im.size != (80, 40) or im.mode != "RGBA":
                raise ValueError("Non-native terrain sprite " + key)
        planned.append((source, target / "sprites" / (key + ".png"), {
            "asset_id": key,
            "kind": meta["kind"],
            "material_a": meta["material_a"],
            "material_b": meta["material_b"],
            "corner_mask": meta["corner_mask"],
            "texture": "res://" + str((target / "sprites" / (key + ".png")).as_posix()),
            "texture_sha256": sha(source),
            "anchor_px": [40, 20],
            "tile_px": [80, 40],
        }))
    for src, dest, item in planned:
        if dest.exists() and sha(dest) != item["texture_sha256"]:
            raise FileExistsError("Refusing to overwrite different sprite: " + str(dest))
    manifest = {
        "schema": 1, "family": "terrain_tile", "status": "TECHNICAL_CANDIDATE",
        "tile_px": [80, 40], "anchor_px": [40, 20],
        "preview_scene_only": True,
        "founder_golden_approved": False, "iphone_verified": False,
        "full_recipe_count": original["full_recipe_count"],
        "installed_count": len(planned), "aliases": original["aliases"],
        "source_recipe_sha256": first_source_meta["source_recipe_sha256"],
        "build_source_sha256": first_source_meta["build_source_sha256"],
        "pixel_finish_source_sha256": first_source_meta["pixel_finish_source_sha256"],
        "tiles": [entry for _, _, entry in planned],
    }
    payload = json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    dest_manifest = target / "manifest.json"
    if dest_manifest.exists() and dest_manifest.read_text() != payload:
        raise FileExistsError("Refusing to overwrite a different terrain manifest")
    (target / "sprites").mkdir(parents=True, exist_ok=True)
    for src, dest, _ in planned:
        if not dest.exists():
            shutil.copyfile(src, dest)
    if not dest_manifest.exists():
        dest_manifest.write_text(payload)
    print("LL_TERRAIN_GODOT_CANDIDATES_INSTALLED", len(planned), target)
    return manifest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sources", type=Path, required=True)
    parser.add_argument("--target", type=Path,
                        default=Path("assets/last_light/terrain/v1"))
    parser.add_argument("--expected", type=int, default=12)
    args = parser.parse_args()
    install(args.sources, args.target, args.expected)


if __name__ == "__main__":
    main()
