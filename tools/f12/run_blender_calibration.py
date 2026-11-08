"""F12 actual Blender calibrated render pilot.

NONCANONICAL for cow and vehicle; refrigerator has A00 verified semantic ID
but source recipe variant is a calibration reconstruction, not Golden approval.
Requires source checkout from geometry-first branch and F07 calibration branch.
Blender: blender -b -t 2 --python tools/f12/run_blender_calibration.py -- OUT geometry_src f07_src
"""
import bpy
import hashlib
import json
import math
import sys
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

out = Path(sys.argv[sys.argv.index("--") + 1]).resolve()
source_root = Path(sys.argv[sys.argv.index("--") + 2]).resolve()
animal_root = Path(sys.argv[sys.argv.index("--") + 3]).resolve()
out.mkdir(parents=True, exist_ok=True)
for p in ["tools/blender_factory", "tools/vehicle_factory"]:
    sys.path.insert(0, str(source_root / p))
import render_v3_recovery as hero
from fleet_render import build_vehicle

RES = 384
# One world-ground metre projects to (40,20) px for 80x40 logical tile.
# As renderer rotates models, camera and screen-space key light are fixed.
ORTHO = RES * math.sqrt(2.0) / 80.0
records = []

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def configure(scene):
    scene.render.resolution_x = RES
    scene.render.resolution_y = RES
    scene.render.resolution_percentage = 100
    scene.render.engine = "BLENDER_EEVEE"
    scene.eevee.taa_render_samples = 8
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.film_transparent = True
    scene.camera.data.ortho_scale = ORTHO
    scene.view_settings.view_transform = "Standard"

def xy(scene, v):
    p = world_to_camera_view(scene, scene.camera, Vector(v))
    return [round(p.x * RES, 5), round((1-p.y) * RES, 5)]

def camera_report(scene):
    origin = xy(scene, (0,0,0))
    east = xy(scene, (1,0,0))
    north = xy(scene, (0,1,0))
    bx = [round(east[i]-origin[i],5) for i in range(2)]
    by = [round(north[i]-origin[i],5) for i in range(2)]
    max_error = max(abs(abs(v[0])-40) for v in (bx,by))
    max_error = max(max_error,*(abs(abs(v[1])-20) for v in (bx,by)))
    if max_error > .05:
        raise AssertionError("Camera projection failed: "+str((bx,by,max_error)))
    return dict(grid_basis_x_px=bx,grid_basis_y_px=by,
                max_axis_error_px=round(max_error,5),
                calibration_evidence="MEASURED_FROM_ACTUAL_BLENDER_WORLD_TO_CAMERA_VIEW",
                image_size_px=[RES,RES],ortho_scale=ORTHO,
                elevation_deg=30,reference_godot="scripts/house.gd TX=40 TY=20")

def group_roots():
    root = bpy.data.objects.new("F12_FRAME_ROOT", None)
    bpy.context.scene.collection.objects.link(root)
    for ob in list(bpy.context.scene.objects):
        if ob is root:
            continue
        if ob.type in {"MESH", "CURVE", "FONT", "ARMATURE"} and ob.parent is None:
            transform = ob.matrix_world.copy()
            ob.parent = root
            ob.matrix_world = transform
    return root

def setup():
    scene = hero.setup()
    configure(scene)
    return scene

def save_source(scene, slug):
    dest = out / slug
    dest.mkdir(parents=True, exist_ok=True)
    src = dest / (slug + ".blend")
    bpy.ops.wm.save_as_mainfile(filepath=str(src),compress=False)
    return src

def render(scene, slug, heading, frame, state, root):
    root.rotation_euler.z = math.tau*heading / (16 if slug=="vehicle" else 8) if slug in ("vehicle","cow") else 0
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    dest = out / slug / ("%s_%02d_%02d.png" % (state, heading, frame))
    scene.render.filepath = str(dest)
    bpy.ops.render.render(write_still=True)
    rec=dict(slug=slug,heading=heading,source_frame=frame,state=state,
             png=str(dest.relative_to(out)),sha256=sha(dest),
             origin_px=xy(scene,(0,0,0)))
    records.append(rec)
    print("F12_REAL_RENDER",slug,state,heading,frame,flush=True)

def cube():
    scene=setup()
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0,0,.5))
    obj=bpy.context.object
    obj.name="F12_MEASURED_CUBE_NONCANONICAL"
    obj.data.materials.append(hero.mat("Calibration cyan-grey",(.28,.54,.58)))
    root=group_roots()
    calib=camera_report(scene)
    src=save_source(scene,"cube")
    render(scene,"cube",0,1,"static",root)
    return {"source_sha":sha(src),"camera_measurement":calib,"status":"CALIBRATION_ONLY"}

def vehicle():
    scene=setup()
    build_vehicle(dict(model="compact_hatchback",paint_hex="#647265",condition_level=1))
    root=group_roots()
    src=save_source(scene,"vehicle")
    for heading in range(16):
        render(scene,"vehicle",heading,1,"static",root)
    return {"source_sha":sha(src),"headings":16,"status":"NONCANONICAL_F10_CALIBRATION"}

def fridge():
    scene=setup()
    hero.fridge_v3(hero.materials("refrigerator"))
    # The existing source has hollow cavities and separate top/bottom doors,
    # but its art source lacks animated parent grouping. Do not fake a whole
    # cabinet rotation: group only top door panel, trim/seals and handle.
    top_z=1.405
    hinge_x=-.341
    hinge_y=-.378
    door_names=("Individual pressed convex door","Door aged left/right seam",
                "Door rubber seal","Bent chromed pull")
    hinge=bpy.data.objects.new("F12_TOP_FREEZER_DOOR_HINGE",None)
    scene.collection.objects.link(hinge)
    hinge.location=(hinge_x,hinge_y,top_z)
    moved=0
    for ob in list(scene.objects):
        if ob.type not in {"MESH","CURVE"} or not ob.name.startswith(door_names):
            continue
        if abs(ob.matrix_world.translation.z-top_z)>.26:
            continue
        world=ob.matrix_world.copy()
        ob.parent=hinge
        ob.matrix_world=world
        moved+=1
    if moved<4:
        raise AssertionError("Top door has too few isolated parts: "+str(moved))
    root=group_roots()
    src=save_source(scene,"fridge")
    for i in range(7):
        hinge.rotation_euler.z=math.radians(-85)*i/6
        render(scene,"fridge",0,i+1,"freezer_open",root)
    return {"source_sha":sha(src),"moving_door_parts":moved,
            "frames":7,"status":"A00_ID_VERIFIED_SOURCE_RECONSTRUCTION_UNAPPROVED"}

def cow():
    # Reuse F07's actual original procedural rig-building code instead of
    # inventing a new cow. Stop before F07-specific camera/render loop; all
    # frames are rendered here through one F12 shared camera.
    script=animal_root/"tools/factory/animals/calibrate.py"
    text=script.read_text()
    pre,separator,_=text.partition("\nworld = bpy.context.scene.world")
    if not separator or "cow_arm=rig" not in pre:
        raise RuntimeError("F07 source boundary changed; refusing to guess")
    scene=setup()
    ns={"__name__":"f07_source_geometry","__file__":str(script)}
    exec(compile(pre,str(script),"exec"),ns)
    # Hide/delete unrelated bird rig and meshes; retain cow source.
    for ob in list(scene.objects):
        if ob.type in {"MESH","ARMATURE"} and ob not in ns["cow_parts"]:
            bpy.data.objects.remove(ob,do_unlink=True)
    # F07's source builder resets the Blender scene and removes the camera.
    # Recreate exactly the shared locked F12 orthographic camera and key light.
    camdata=bpy.data.cameras.new("F12_RESTORED_2_TO_1")
    cam=bpy.data.objects.new("F12_RESTORED_2_TO_1",camdata)
    scene.collection.objects.link(cam)
    cam.location=(8/math.sqrt(2),-8/math.sqrt(2),8*math.tan(math.radians(30)))
    cam.rotation_euler=(-cam.location).to_track_quat("-Z","Y").to_euler()
    camdata.type="ORTHO"
    scene.camera=cam
    light=bpy.data.lights.new("F12_KEY","AREA")
    source_light=bpy.data.objects.new("F12_KEY",light)
    scene.collection.objects.link(source_light)
    source_light.location=(-3.6,-4.5,7.5)
    light.energy=850
    light.size=3
    configure(scene)
    camera_report(scene)
    # F07 mesh still shares its original cow armature and walk action.
    arm=ns["cow_arm"]
    action=bpy.data.actions.get("CowRig_CAL_walk")
    if action is None:
        raise RuntimeError("No F07 walk action; cow animation blocked")
    arm.animation_data.action=action
    root=group_roots()
    src=save_source(scene,"cow")
    for heading in range(8):
        for frame in (1,4):
            render(scene,"cow",heading,frame,"walk_sample",root)
    return {"source_sha":sha(src),"headings":8,"pose_samples":2,
            "f07_source_sha":sha(script),"status":"NONCANONICAL_F07_COW_RIG_CALIBRATION"}

status={}
for name,fn in (("cube",cube),("vehicle",vehicle),("cow",cow),("fridge",fridge)):
    try:
        status[name]=fn()
    except Exception as exc:
        status[name]={"status":"FAIL","error":str(exc)}
        (out/"render_report.json").write_text(json.dumps(dict(
            schema=1,source_root=str(source_root),results=status,frames=records
        ),indent=2)+"\n")
        raise
(out/"render_report.json").write_text(json.dumps(dict(
    schema=1,source_root=str(source_root),results=status,frames=records,
    stage="ACTUAL_BLENDER_TECHNICAL_CALIBRATION_NOT_GOLDEN_OR_GAME_READY",
    frame_count=len(records)
),indent=2)+"\n")
print("F12_CALIBRATION_ALL_RENDERED",len(records),flush=True)
