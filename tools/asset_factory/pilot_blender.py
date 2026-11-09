"""Deterministic F01 calibration candidates; never Golden-approved assets.

blender -b -t 2 --python tools/asset_factory/pilot_blender.py -- --output /tmp/ll-pilot
"""
import argparse
import json
import sys
from pathlib import Path

import bpy
from mathutils import Vector


def cube(name, location, scale, material):
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    mod = obj.modifiers.new("Soft edges", "BEVEL")
    mod.width = 0.035
    mod.segments = 2
    obj.data.materials.append(material)


def material(name, color):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Roughness"].default_value = 0.75
    return m


def candidate(kind):
    wood = material("Warm wood", (0.31, 0.18, 0.095))
    steel = material("Cool steel", (0.38, 0.45, 0.48))
    pale = material("Enamel", (0.71, 0.75, 0.70))
    if kind == "stool":
        cube("seat", (0, 0, 0.78), (0.82, 0.82, 0.13), wood)
        for x in (-0.30, 0.30):
            for y in (-0.30, 0.30):
                cube("leg", (x, y, 0.37), (0.085, 0.085, 0.73), wood)
    elif kind == "cabinet":
        cube("carcass", (0, 0, 0.65), (1.2, 0.55, 1.3), wood)
        cube("door left", (-0.294, -0.289, 0.64), (0.565, 0.035, 1.22), pale)
        cube("door right", (0.294, -0.289, 0.64), (0.565, 0.035, 1.22), pale)
        for x in (-0.065, 0.065):
            cube("handle", (x, -0.332, 0.72), (0.025, 0.025, 0.17), steel)
    elif kind == "table":
        cube("tabletop", (0, 0, 0.88), (1.45, 0.95, 0.12), wood)
        for x in (-0.58, 0.58):
            for y in (-0.34, 0.34):
                cube("leg", (x, y, 0.42), (0.10, 0.10, 0.83), steel)
    else:
        raise ValueError(kind)


def main():
    args = argparse.ArgumentParser()
    args.add_argument("--output", required=True)
    args.add_argument("--asset", choices=("stool", "cabinet", "table"), default="stool")
    parsed = args.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    out = Path(parsed.output).resolve()
    out.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    candidate(parsed.asset)
    light_data = bpy.data.lights.new("Upper-left softbox", "AREA")
    light = bpy.data.objects.new("Upper-left softbox", light_data)
    bpy.context.collection.objects.link(light)
    light.location = (-3, -4, 7)
    light_data.energy = 650
    light_data.shape = "DISK"
    light_data.size = 4
    camera_data = bpy.data.cameras.new("Orthographic 2.5D")
    camera = bpy.data.objects.new("Orthographic 2.5D", camera_data)
    bpy.context.collection.objects.link(camera)
    camera.location = (3.8, -5.4, 4.7)
    target = Vector((0, 0, 0.65))
    camera.rotation_euler = (target - camera.location).to_track_quat("-Z", "Y").to_euler()
    camera_data.type = "ORTHO"
    camera_data.ortho_scale = 2.9
    bpy.context.scene.camera = camera
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE_NEXT" if bpy.app.version >= (4, 2, 0) else "BLENDER_EEVEE"
    scene.render.resolution_x = 192
    scene.render.resolution_y = 192
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = True
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.filepath = str(out / f"{parsed.asset}.png")
    bpy.ops.wm.save_as_mainfile(filepath=str(out / f"{parsed.asset}.blend"))
    bpy.ops.render.render(write_still=True)
    report = {"asset_id": f"F01_PILOT_{parsed.asset.upper()}", "stage": "CALIBRATION_ONLY", "approval": "UNAPPROVED", "source": "original procedural generator", "blender_version": bpy.app.version_string, "render": f"{parsed.asset}.png", "blend": f"{parsed.asset}.blend"}
    (out / f"{parsed.asset}.json").write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
