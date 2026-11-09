"""F12 noncanonical 80x40 isometric calibration fixture.

Run: blender -b --factory-startup --python tools/factory/render_bridge/calibrate.py -- --output /tmp/f12-cal
No game assets or A00 identities are created by this script.
"""
import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def project(scene, xyz):
    uv = world_to_camera_view(scene, scene.camera, Vector(xyz))
    return [uv.x * scene.render.resolution_x, (1 - uv.y) * scene.render.resolution_y]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    opts = parser.parse_args(args)
    out = opts.output.resolve()
    out.mkdir(parents=True, exist_ok=True)

    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 16
    scene.cycles.use_denoising = False
    scene.render.resolution_x = 256
    scene.render.resolution_y = 256
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = True
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "Medium High Contrast"

    camera_data = bpy.data.cameras.new("F12_orthographic_v0_candidate")
    camera = bpy.data.objects.new("F12_orthographic_v0_candidate", camera_data)
    scene.collection.objects.link(camera)
    # Elevation is derived from vertical/horizontal diamond slope 20/40:
    # sin(elevation) = 1/2. It is not independently assumed from art reference.
    elevation = math.asin(20 / 40)
    camera.location = (8, 8, 8 * math.sqrt(2) * math.tan(elevation))
    target = Vector((0, 0, 0))
    camera.rotation_euler = (target - camera.location).to_track_quat("-Z", "Y").to_euler()
    camera_data.type = "ORTHO"
    camera_data.ortho_scale = 256 / (40 * math.sqrt(2))
    scene.camera = camera

    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0.5))
    cube = bpy.context.object
    cube.name = "CALIBRATION_ONLY_one_metre_cube"
    mat = bpy.data.materials.new("CALIBRATION_ONLY_slate")
    mat.diffuse_color = (0.27, 0.38, 0.48, 1)
    cube.data.materials.append(mat)

    # Fixed world light, not attached to rotating assets.
    lamp = bpy.data.lights.new("F12_upper_left_key_candidate", "AREA")
    lamp.energy = 450
    lamp.shape = "DISK"
    lamp.size = 4
    light = bpy.data.objects.new(lamp.name, lamp)
    scene.collection.objects.link(light)
    light.location = (-3, 2, 7)
    scene.world.color = (0.17, 0.17, 0.17)

    origin = project(scene, (0, 0, 0))
    px = project(scene, (1, 0, 0))
    py = project(scene, (0, 1, 0))
    bx = [round(px[i] - origin[i], 6) for i in (0, 1)]
    by = [round(py[i] - origin[i], 6) for i in (0, 1)]
    # The handedness of the world coordinate axes is captured as measured.
    # Blender +X maps to Godot +Y and Blender +Y maps to Godot +X.
    # Godot's iso(x,y)=(40(x-y),20(x+y)) then gives these basis vectors.
    target_basis = [[-40, 20], [40, 20]]
    report_axes = {"blender_x": "godot_y", "blender_y": "godot_x"}
    residual = max(abs(bx[i] - target_basis[0][i]) for i in (0, 1))
    residual = max(residual, *(abs(by[i] - target_basis[1][i]) for i in (0, 1)))
    report = {
        "schema_version": 1,
        "fixture": "CAL-01",
        "canonical_status": "CALIBRATION_ONLY_NONCANONICAL",
        "camera_status": "CANDIDATE_PENDING_GODOT_W01_W08",
        "tile_logical_pixels": [80, 40],
        "target_basis_px": target_basis,
        "world_axis_mapping": report_axes,
        "measured_origin_px": origin,
        "measured_basis_px": [bx, by],
        "max_absolute_residual_px": round(residual, 6),
        "camera_matrix_world": [[round(v, 9) for v in row] for row in camera.matrix_world],
        "ortho_scale": camera_data.ortho_scale,
        "elevation_radians": elevation,
        "blender_version": bpy.app.version_string,
    }
    if residual > 0.001:
        raise AssertionError("Projection does not match 80x40: " + json.dumps(report))

    blend = out / "CAL-01_calibration_only.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    image = out / "CAL-01_cube_rgba.png"
    scene.render.filepath = str(image)
    bpy.ops.render.render(write_still=True)
    report["source_blend_sha256"] = sha(blend)
    report["render_png_sha256"] = sha(image)
    (out / "CAL-01_report.json").write_text(json.dumps(report, indent=2) + "\n")
    print("F12_CAL_01_PASS", json.dumps(report), flush=True)


if __name__ == "__main__":
    main()
