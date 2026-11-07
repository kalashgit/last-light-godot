"""LAST LIGHT Animation Factory V1: actual articulated Blender meshes, not post-hoc image morphs.
Run: blender -b --factory-startup -t 2 --python tools/animation_factory/render.py -- --output build/animation_factory/raw
Existing V3 mesh/shader family is reused. No downloaded reference pixels or external assets.
"""
import hashlib
import json
import math
import sys
from pathlib import Path
import bpy
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "blender_factory"))
import render_v3_recovery as hero

def component_axis(o, axis):
    # Curve pipes are defined in world coordinates inside their local spline, unlike meshes.
    if o.type == "CURVE" and len(o.data.splines):
        pts = [tuple(pt.co[:3]) for sp in o.data.splines for pt in sp.points]
        if pts:
            return sum(p[axis] for p in pts) / len(pts)
    return o.matrix_world.translation[axis]

def parent_preserving_world(ob, parent):
    old = ob.matrix_world.copy()
    ob.parent = parent
    ob.matrix_world = old

def hinge(name, position, objects):
    if not objects:
        raise RuntimeError("No geometry bound to animation hinge " + name)
    empty = bpy.data.objects.new(name, None)
    bpy.context.collection.objects.link(empty)
    empty.location = position
    bpy.context.view_layer.update()
    for ob in objects:
        parent_preserving_world(ob, empty)
    return empty

def rig_parts(action):
    all_parts = list(bpy.context.scene.objects)
    rig = action["rig"]
    if rig == "fridge_hinge":
        z = 1.405 if action["part"] == "upper" else .617
        names = ("Individual pressed convex door", "Door aged left/right seam",
                 "Door rubber seal", "Bent chromed pull")
        moving = [o for o in all_parts if any(o.name.startswith(s) for s in names)
                  and abs(component_axis(o, 2) - z) < .36]
        if len(moving) < 4:
            raise RuntimeError("Refrigerator door semantic binding incomplete: " + str(len(moving)))
        return [(hinge("hinge_fridge_"+action["part"], (-.355,-.368,z), moving),1.0)]
    if rig == "paired_cabinet_hinges":
        names = ("Individual framed door perimeter", "Carved inner recess",
                 "Slightly convex hand-finished inner panel", "Panel vertical worn grain",
                 "Bent cast door hardware")
        objects = [o for o in all_parts if any(o.name.startswith(s) for s in names)]
        left = [o for o in objects if component_axis(o,0) < -.05]
        right = [o for o in objects if component_axis(o,0) > .05]
        if len(left) < 4 or len(right) < 4:
            raise RuntimeError("Cabinet paired door rig incomplete: " + str((len(left),len(right))))
        a=hinge("cabinet_left",(-.50,-.315,.735),left)
        b=hinge("cabinet_right",(.50,-.315,.735),right)
        # The doors swing OUT from the front of the cabinet in opposite directions.
        return [(a,-1.0),(b,1.0)]
    raise ValueError("Unknown rig: "+rig)

def validate_hollow_storage(family):
    """Mechanical guard: storage is truly void, not a painted solid box.

    Validate two air-pocket witness points per family against world bounding
    boxes, in addition to requiring separately named sides/rear/shelves.
    This is a *geometry* check, not proof of final visual quality or loot logic.
    """
    expectations = {
        "refrigerator": dict(
            required=("Fridge insulated outer side shell",
                      "Fridge insulated rear shell", "Fridge removable interior shelf",
                      "Fridge freezer separator"),
            forbidden=("Curved ivory enamel carcass", "Inset black rubber gasket"),
            probes=((0,-.06,.56),(0,-.06,1.22))),
        "cabinet": dict(
            required=("Cabinet load-bearing hollow side",
                      "Cabinet real thin back panel", "Cabinet removable interior shelf"),
            forbidden=("Dark walnut solid carcass", "Recessed inset back panel"),
            probes= ((-.235,-.06,.765),(.235,-.06,.765)))
    }
    if family not in expectations:
        return
    rules=expectations[family]
    meshes=[o for o in bpy.context.scene.objects if o.type=="MESH"]
    names=[o.name for o in meshes]
    for key in rules["required"]:
        if not any(n.startswith(key) for n in names):
            raise RuntimeError("Storage interior missing required geometry: "+key)
    for key in rules["forbidden"]:
        if any(n.startswith(key) for n in names):
            raise RuntimeError("Solid/opaque interior obstruction remains: "+key)
    bpy.context.view_layer.update()
    # This test intentionally uses interior point occupancy. A solid carcass
    # would enclose the probe; shelves/skins must *not*.
    for p in rules["probes"]:
        v=Vector(p)
        for ob in meshes:
            points=[ob.matrix_world@Vector(co) for co in ob.bound_box]
            lo=tuple(min(point[a] for point in points) for a in range(3))
            hi=tuple(max(point[a] for point in points) for a in range(3))
            if all(lo[a]+.001 < v[a] < hi[a]-.001 for a in range(3)):
                raise RuntimeError("Blocked "+family+" air cavity at "+
                    str(p)+" by "+ob.name)
    print("LL_HOLLOW_GEOMETRY_PASS",family,len(meshes),flush=True)


def render_action(action, out):
    if action["condition"] != 1:
        raise ValueError("Only condition=1 visually test-rendered; do not fake other wear levels")
    scene = hero.setup()
    scene.cycles.samples=12
    scene.render.resolution_x = 512
    scene.render.resolution_y = 512
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = True
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.image_settings.file_format = "PNG"
    mats = hero.materials(action["family"])
    hero.BUILD[action["family"]](mats)
    bpy.context.view_layer.update()
    validate_hollow_storage(action["family"])
    hinges = rig_parts(action)
    bpy.context.view_layer.update()
    fixed_camera = tuple(round(x,6) for x in scene.camera.location)
    anchor_uv = world_to_camera_view(scene,scene.camera,Vector((0,0,0)))
    anchor = [round(anchor_uv.x * 512,3),round((1-anchor_uv.y)*512,3)]
    folder = out / action["id"]
    folder.mkdir(parents=True, exist_ok=True)
    files=[]
    for f in range(action["frames"]):
        t = f / (action["frames"]-1)
        if action["easing"] == "smoothstep":
            t = t*t*(3-2*t)
        angle = action["start_deg"]+(action["end_deg"]-action["start_deg"])*t
        for h,sign in hinges:
            # Single fridge swing is negative; paired cabinet swing is symmetric.
            h.rotation_euler.z=math.radians(angle * sign)
        bpy.context.view_layer.update()
        name=f"frame_{f:02d}.png"
        scene.render.filepath=str((folder/name).resolve())
        bpy.ops.render.render(write_still=True)
        files.append(name)
        print("LL_ANIM_FRAME",action["id"],f,round(angle,3),flush=True)
    return dict(id=action["id"],family=action["family"],fps=action["fps"],frames=files,
                event_frame=action["event_frame"],reverse_for_close=action["reverse_for_close"],
                condition=action["condition"],pivot_source_canvas=anchor,
                source_canvas_px=[512,512],render_camera_fixed=fixed_camera,
                state="rendered_candidate_visual_approval_pending")

def main():
    args=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    out=Path(args[args.index("--output")+1]) if "--output" in args else Path("build/animation_factory/raw")
    only=args[args.index("--actions")+1].split(",") if "--actions" in args else None
    data_path=Path(__file__).with_name("recipes.json")
    data=json.loads(data_path.read_text())
    actions=[a for a in data["actions"] if only is None or a["id"] in only]
    if not actions:
        raise ValueError("No actions selected")
    if any(a["family"] not in hero.BUILD or a["frames"] < 2 for a in actions):
        raise ValueError("Invalid family or frame count")
    out.mkdir(parents=True,exist_ok=True)
    result=[render_action(a,out) for a in actions]
    manifest=dict(schema_version=1,tile_px=[80,40],projection="fixed isometric",
                  source_recipe_sha256=hashlib.sha256(data_path.read_bytes()).hexdigest(),
                  source="Original V3 Blender geometry + articulated hinge rig",
                  status="rendered_candidate_not_godot_verified",entries=result)
    (out/"manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")
    print("LL_ANIM_RENDER_DONE",len(result),sum(len(e["frames"]) for e in result),flush=True)

if __name__ == "__main__": main()
