"""Original LAST LIGHT Blender-to-2D pilot. No reference-game assets or downloads.
Usage: blender -b --factory-startup -t 2 --python tools/blender_factory/render_pilot.py -- --output build/blender_factory/raw
"""
import bpy
import math
import json
import sys
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

ITEMS = ("refrigerator", "cabinet", "sofa", "crate")
RES = 1024
TILE_PX = (80, 40)
FINAL_DOWNSAMPLE = 2
# A one-metre floor-square needs an 80x40 projected diamond after halving the render.
ORTHO_SCALE = (RES / FINAL_DOWNSAMPLE) * math.sqrt(2) / TILE_PX[0]


def material(name, rgb, metallic=0.0, roughness=0.72):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*rgb, 1.0)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*rgb, 1.0)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    return mat


def block(name, xyz, dimensions, mat, bevel=0.018):
    bpy.ops.mesh.primitive_cube_add(size=1, location=xyz)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mat)
    if bevel > 0:
        mod = obj.modifiers.new("subtle worn hard edges", "BEVEL")
        mod.width = min(bevel, min(dimensions) * 0.16)
        mod.segments = 1
        mod2 = obj.modifiers.new("weighted edge normals", "WEIGHTED_NORMAL")
    return obj


def make_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    world = bpy.context.scene.world
    world.color = (0.18, 0.2, 0.21)
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    bg.inputs["Color"].default_value = (0.55, 0.62, 0.68, 1.0)
    bg.inputs["Strength"].default_value = 0.65

    cam_data = bpy.data.cameras.new("Locked 2:1 dimetric camera")
    cam = bpy.data.objects.new("Locked 2:1 dimetric camera", cam_data)
    bpy.context.collection.objects.link(cam)
    elevation = math.radians(30.0)  # sin(elevation)=0.5: projected axes have 1:2 slopes
    horizontal = 10.0
    cam.location = (horizontal/math.sqrt(2), -horizontal/math.sqrt(2),
                    horizontal * math.tan(elevation))
    target = Vector((0, 0, 0))
    cam.rotation_euler = (target - cam.location).to_track_quat("-Z", "Y").to_euler()
    # Camera points at a constant fixed world point; all assets retain a real floor-contact pivot.
    cam_data.type = "ORTHO"
    cam_data.ortho_scale = ORTHO_SCALE
    bpy.context.scene.camera = cam

    lamp_data = bpy.data.lights.new("Upper-left soft daylight", "AREA")
    lamp = bpy.data.objects.new("Upper-left soft daylight", lamp_data)
    bpy.context.collection.objects.link(lamp)
    lamp.location = (-3.5, -4.0, 7.0)
    lamp_data.energy = 650.0
    lamp_data.shape = "DISK"
    lamp_data.size = 4.0

    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 24
    scene.cycles.use_denoising = True
    scene.render.resolution_x = RES
    scene.render.resolution_y = RES
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = True
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.image_settings.color_depth = "8"
    scene.render.film_transparent = True
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "Medium High Contrast"
    scene.render.image_settings.compression = 15
    return scene


def refrigerator(m):
    metal, steel, black, handle = m["cream"], m["steel"], m["dark"], m["black"]
    block("Refrigerator chassis", (0,0,0.88), (.76,.72,1.76), metal)
    block("Freezer upper door", (0,-.365,1.39), (.73,.045,.69), metal, .01)
    block("Lower refrigerator door", (0,-.365,.62), (.73,.045,.83), metal, .01)
    block("Door seal", (0,-.393,1.02), (.7,.012,.025), black, .003)
    block("Upper handle", (.255,-.405,1.31), (.018,.025,.33), handle, .006)
    block("Lower handle", (.255,-.405,.62), (.018,.025,.34), handle, .006)
    for x in (-.25,.25):
        block("rubber foot", (x,-.23,.035),(.12,.13,.07),black,.004)
    return (.76,.79,1.76)


def cabinet(m):
    wood, dark, steel = m["wood"],m["wood_dark"],m["steel"]
    block("Cabinet body", (0,0,.72), (1.03,.53,1.44), wood)
    block("Left door front", (-.26,-.275,.73),(.48,.042,1.27),wood,.008)
    block("Right door front", (.26,-.275,.73),(.48,.042,1.27),wood,.008)
    block("Door seam", (0,-.304,.74),(.013,.011,1.2),dark,.003)
    for x in (-.085,.085):
        block("Cabinet handle", (x,-.314,.80),(.018,.027,.14),steel,.006)
    block("Raised feet trim", (0,0,.06),(.98,.52,.11),dark,.005)
    return (1.03,.57,1.44)


def sofa(m):
    cloth, seams, legs = m["fabric"],m["fabric_dark"],m["wood_dark"]
    block("Sofa base", (0,0,.31),(1.95,.85,.35),cloth,.05)
    block("Sofa back", (0,.34,.72),(1.94,.22,.70),cloth,.055)
    for x in (-.81,.81):
        block("Side upholstered arm", (x,-.03,.54),(.32,.91,.46),cloth,.045)
    for x in (-.47,.47):
        block("Seat cushion", (x,-.155,.53),(.86,.61,.16),cloth,.03)
        block("Back pillow", (x,.205,.76),(.86,.16,.48),cloth,.03)
    for x in (-.79,.79):
        for y in (-.29,.29):
            block("Short exposed foot", (x,y,.065),(.09,.09,.13),legs,.006)
    return (1.95,.95,1.08)


def crate(m):
    wood, dark, steel = m["wood"],m["wood_dark"],m["steel"]
    block("Crate dark interior", (0,0,.29),(.62,.55,.55),dark,.004)
    for z in (.115,.285,.45):
        for y in (-.286,.286):
            block("Front-back weathered planks", (0,y,z),(.67,.037,.14),wood,.008)
        for x in (-.332,.332):
            block("Side weathered planks", (x,0,z),(.035,.59,.14),wood,.008)
    for x in (-.303,.303):
        for y in (-.268,.268):
            block("Braced timber post", (x,y,.30),(.064,.065,.60),wood,.008)
    return (.67,.61,.60)


BUILDERS = {"refrigerator":refrigerator,"cabinet":cabinet,"sofa":sofa,"crate":crate}


def main():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    out = Path("build/blender_factory/raw")
    if "--output" in args:
        out = Path(args[args.index("--output")+1])
    out.mkdir(parents=True,exist_ok=True)
    manifest = {"schema":1, "tile_px":list(TILE_PX),
                "projection":"fixed 2:1 dimetric, orthographic 30-degree elevation",
                "source":"Original generated parametric Blender geometry (not imported reference art)",
                "render_resolution":RES, "downsample":FINAL_DOWNSAMPLE, "entries":[]}
    for name in ITEMS:
        scene = make_scene()
        m = {
            "cream":material(name+"_cream",(.59,.63,.60),.13,.49),
            "steel":material(name+"_steel",(.48,.54,.53),.65,.32),
            "black":material(name+"_black",(.09,.12,.12),.06,.83),
            "dark":material(name+"_dark",(.15,.20,.19),.10,.8),
            "wood":material(name+"_wood",(.34,.23,.15),.0,.81),
            "wood_dark":material(name+"_wood_dark",(.18,.12,.09),.0,.85),
            "fabric":material(name+"_fabric",(.34,.38,.35),.0,.94),
            "fabric_dark":material(name+"_fabric_dark",(.21,.27,.24),.0,.96),
        }
        dims = BUILDERS[name](m)
        bpy.context.view_layer.update()
        # The floor-contact point is the item's *origin* at z=0.
        uv = world_to_camera_view(scene,scene.camera,Vector((0.0,0.0,0.0)))
        contact = [round(float(uv.x)*RES,3),round((1.0-float(uv.y))*RES,3)]
        scene.render.filepath = str((out/(name+".png")).resolve())
        bpy.ops.render.render(write_still=True)
        manifest["entries"].append({
            "id":"ll_pilot_"+name, "name":name,
            "raw_file":name+".png", "dimensions_m":list(dims),
            "footprint_m":list(dims[:2]),
            "contact_px_raw":contact,
            "usage":"world_furniture" if name!="crate" else "world_prop",
            "originality":"constructed entirely from Blender primitives"
        })
        print("LAST LIGHT PILOT: rendered",name,"at",contact,flush=True)
    (out/"manifest.json").write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
    print("LAST LIGHT PILOT: finished",len(manifest["entries"]),"original models",flush=True)


if __name__ == "__main__":
    main()
