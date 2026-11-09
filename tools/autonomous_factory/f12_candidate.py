"""Render a noncanonical F01 source under the pinned F12 CAL-01 camera contract.

The 80x40 projection is measured in Blender, not inferred from PNG filenames.
This is a calibration candidate, not an approved sprite or production atlas.
The camera and fixed world light reproduce F12's pinned CAL-01 parameters.
"""
import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Matrix, Vector

F12_SOURCE_SHA = "eba8e2c6d78bbc41b2de413d176d805b6c288337"
TARGET_BASIS = ((-40, 20), (40, 20))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def project(scene, coords):
    uv = world_to_camera_view(scene, scene.camera, Vector(coords))
    return (
        uv.x * scene.render.resolution_x,
        (1 - uv.y) * scene.render.resolution_y,
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    args = parser.parse_args(argv)
    bpy.ops.wm.open_mainfile(filepath=str(args.source.resolve()))
    scene = bpy.context.scene
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)

    # The source F01 asset is retained; only a candidate viewing rig is added.
    for ob in scene.objects:
        if ob.type == "LIGHT":
            ob.hide_render = True
    camera_data = bpy.data.cameras.new("M02_F12_CAL01_ortho")
    camera = bpy.data.objects.new("M02_F12_CAL01_ortho", camera_data)
    scene.collection.objects.link(camera)
    camera_data.type = "ORTHO"
    camera_data.ortho_scale = 256 / (40 * math.sqrt(2))
    scene.camera = camera

    lamp_data = bpy.data.lights.new("M02_F12_CAL01_fixed_upper_left", "AREA")
    lamp_data.energy = 450
    lamp_data.shape = "DISK"
    lamp_data.size = 4
    lamp = bpy.data.objects.new(lamp_data.name, lamp_data)
    scene.collection.objects.link(lamp)
    lamp.location = (-3, 2, 7)
    scene.world.color = (0.17, 0.17, 0.17)

    scene.render.engine = "CYCLES"
    scene.cycles.samples = 8
    scene.cycles.use_denoising = False
    scene.render.resolution_x = 256
    scene.render.resolution_y = 256
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = True
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "Medium High Contrast"
    scene.frame_set(1)

    elev = math.asin(20 / 40)
    initial_position = Vector((8, 8, 8 * math.sqrt(2) * math.tan(elev)))
    frames = []
    measured_basis = None
    residual = None
    for degrees in (0, 90, 180, 270):
        rotation = Matrix.Rotation(math.radians(degrees), 4, "Z")
        camera.location = rotation @ initial_position
        camera.rotation_euler = (-camera.location).to_track_quat("-Z", "Y").to_euler()
        bpy.context.view_layer.update()
        if degrees == 0:
            origin = project(scene, (0, 0, 0))
            px = project(scene, (1, 0, 0))
            py = project(scene, (0, 1, 0))
            measured_basis = [
                [round(px[i] - origin[i], 6) for i in (0, 1)],
                [round(py[i] - origin[i], 6) for i in (0, 1)],
            ]
            residual = max(abs(measured_basis[j][i] - TARGET_BASIS[j][i])
                           for j in (0, 1) for i in (0, 1))
            if residual > .001:
                raise AssertionError(f"F12 CAL-01 world basis mismatch: {measured_basis}")
        path = out / f"f12_cal01_{degrees:03d}.png"
        scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
        frames.append({"degrees": degrees, "file": path.name, "sha256": digest(path)})
    report = {
        "schema_version": 1,
        "status": "F12_CAL01_WORLD_SCALE_TECHNICAL_CANDIDATE_NOT_GOLDEN",
        "f12_pinned_source_sha": F12_SOURCE_SHA,
        "source_f01_blend_sha256": digest(args.source),
        "tile_logical_pixels": [80, 40],
        "target_basis_px": TARGET_BASIS,
        "measured_basis_px": measured_basis,
        "max_absolute_residual_px": round(residual, 6),
        "ortho_scale": camera_data.ortho_scale,
        "camera_elevation_radians": elev,
        "canvas_px": [256, 256],
        "light": "fixed_world_upper_left",
        "founder_approved": False,
        "canonical_promoted": False,
        "frames": frames,
    }
    (out / "f12_candidate.json").write_text(json.dumps(report, indent=2) + "\n")
    print("M02_F12_CAL01_F01_CAMERA_PARITY_PASS", measured_basis, flush=True)


if __name__ == "__main__":
    main()
