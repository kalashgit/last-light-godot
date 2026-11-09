"""Additional diagnostic F12 views from the EXISTING locked F01 .blend rig.

Four orientations are inspection-only, NOT accepted 80x40 world sprites.
"""
import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Matrix, Vector


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args(sys.argv[sys.argv.index("--") + 1:])
    bpy.ops.wm.open_mainfile(filepath=str(args.source.resolve()))
    scene = bpy.context.scene
    camera = scene.camera
    if camera is None or camera.data.type != "ORTHO":
        raise RuntimeError("F12 source has no locked orthographic camera")
    args.output.mkdir(parents=True, exist_ok=True)
    # Camera/light orbital movement preserves frame-relative upper-left lighting.
    lights = [o for o in scene.objects if o.type == "LIGHT"]
    original = {o.name: o.matrix_world.copy() for o in [camera, *lights]}
    scene.render.film_transparent = True
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.resolution_percentage = 100
    # Frozen diagnostic world-geometry state; full animation remains in source.
    scene.frame_set(1)
    frames = []
    for degrees in (0, 90, 180, 270):
        rotation = Matrix.Rotation(math.radians(degrees), 4, "Z")
        for obj in [camera, *lights]:
            obj.matrix_world = rotation @ original[obj.name]
        path = args.output / f"view_{degrees:03d}.png"
        scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
        frames.append({"degrees": degrees, "file": path.name,
                       "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    (args.output / "views.json").write_text(json.dumps({
        "source": args.source.name, "status": "F12_DIAGNOSTIC_NOT_WORLD_SCALE_APPROVED",
        "camera": "original locked orthographic rig, orbited 90 degrees per view",
        "world_px_per_m_validated": False, "founder_approved": False,
        "frames": frames}, indent=2) + "\n")


if __name__ == "__main__":
    main()
