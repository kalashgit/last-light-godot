"""F01 source-first refrigerator calibration. NOT canonical production approval.

blender -b --factory-startup -t 2 --python tools/factory/furniture/refrigerator_calibration.py -- --output build/f01_calibration/refrigerator
"""
import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

# Some Blender-in-Codex builds expose a partial embedded Python stdlib.
# Resolve its matching system extension directory for glTF's ctypes dependency.
system_extensions = Path(f"/usr/lib/python{sys.version_info.major}.{sys.version_info.minor}/lib-dynload")
if system_extensions.is_dir() and str(system_extensions) not in sys.path:
    sys.path.insert(0, str(system_extensions))
runtime_sites = Path(f"/opt/codex/runtimes/codex-primary-runtime/dependencies/python/lib/python{sys.version_info.major}.{sys.version_info.minor}/site-packages")
if runtime_sites.is_dir() and str(runtime_sites) not in sys.path:
    sys.path.append(str(runtime_sites))

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0,str(Path(__file__).resolve().parent))
sys.path.insert(0, str(ROOT / "tools/blender_factory"))
import render_v3_recovery as hero
from f01_materials import enamel


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def component(name, xyz, dims, material, bevel=0.006, parent=None):
    ob = hero.cube(name, xyz, dims, material, bevel=bevel)
    if parent:
        ob.parent = parent
        ob.matrix_parent_inverse = parent.matrix_world.inverted()
    return ob


def main():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--samples", type=int, default=12)
    opt = parser.parse_args(args)
    output = opt.output.resolve()
    output.mkdir(parents=True, exist_ok=True)

    scene = hero.setup()  # existing locked F12-predecessor 30-degree camera/light rig
    m = hero.materials("f01_fridge")
    m["paint"]=enamel("F01 original aged enamel V5")
    shelf_glass = hero.mat("F01 glass shelving pale green edge",(.70,.82,.78),rough=.16,wear=.015)
    glass_bsdf = shelf_glass.node_tree.nodes.get("Principled BSDF")
    if glass_bsdf:
        glass_bsdf.inputs["Transmission Weight"].default_value=.55
        glass_bsdf.inputs["IOR"].default_value=1.46
    w, d, h = 0.77, 0.71, 1.77
    t = 0.047
    # True cavity: the shell is five separate panels, not a sealed solid cube.
    component("body.left_insulated_wall", (-w/2+t/2, 0, h/2), (t,d,h), m["paint"])
    component("body.right_insulated_wall", (w/2-t/2, 0, h/2), (t,d,h), m["paint"])
    component("body.back_insulated_wall", (0,d/2-t/2,h/2), (w-2*t,t,h), m["paint"])
    component("body.roof", (0,0,h-t/2), (w-2*t,d,t), m["paint"])
    component("body.floor", (0,0,t/2+.035), (w-2*t,d,.07), m["paint"])
    # Liner, door seal, real shelf slabs and edge lips.
    component("liner.back", (0,d/2-t-.009,h/2), (w-2*t-.025,.018,h-.14), m["plastic"])
    for n, z in enumerate((.40,.70,1.00,1.34)):
        component(f"shelf.{n}.glass", (0,.015,z), (w-2*t-.035,d-.15,.018),shelf_glass,.003)
        component(f"shelf.{n}.front_lip", (0,-d/2+.08,z), (w-2*t-.035,.013,.032),m["chrome"],.002)
    for side in (-1,1):
        component("opening.gasket.vertical",(side*(w/2-t-.008),-d/2-.005,h/2),(.014,.013,h-.12),m["rubber"],.001)
    for z in (.065,h-.05):
        component("opening.gasket.horizontal",(0,-d/2-.005,z),(w-2*t,.013,.014),m["rubber"],.001)
    hinge_xyz = (-w/2+.015,-d/2-.019,h/2)
    hinge = bpy.data.objects.new("hinge_local.main_door",None)
    bpy.context.collection.objects.link(hinge)
    hinge.location = hinge_xyz
    hinge.empty_display_size = .08
    # Door meshes use world coordinates and parent_inverse to retain rest placement.
    component("door.enamel_panel",(0,-d/2-.056,h/2),(w-.014,.065,h-.075),m["paint"],.023,hinge)
    # Interior liner faces the cavity (+Y); it must not be painted on the exterior.
    component("door.inner_liner",(0,-d/2-.017,h/2),(w-.071,.015,h-.13),m["plastic"],.008,hinge)
    # Real shallow storage pockets, parented to the door, seen when fully open.
    for n,z in enumerate((.36,.73,1.11)):
        component(f"door.storage_bin.{n}.front_rail",(0,-d/2+.008,z),(.53,.026,.045),m["plastic"],.006,hinge)
        component(f"door.storage_bin.{n}.shelf",(0,-d/2+.024,z-.063),(.53,.10,.018),m["plastic"],.003,hinge)
    component("door.pull.vertical",(.295,-d/2-.11,h/2),(.025,.035,.38),m["chrome"],.009,hinge)
    for z in (.17,h-.16):
        component("door.hinge_pin",(hinge_xyz[0],hinge_xyz[1],z),(.03,.03,.063),m["steel"],.006)
    for z in (.03,.07,.11):
        component("compressor.vent_louver",(0,-d/2-.029,z),(.40,.012,.008),m["black"],.002)
    # Low-profile pressed sheet-metal junctions and feet add physical detail.
    for x in (-.29,.29):
        component("body.adjustable_floor_foot",(x,.22,.022),(.08,.08,.044),m["rubber"],.009)
    for z in (.14,1.61):
        component("body.side_seam",(w/2+.001,.17,z),(.005,.26,.007),m["steel"],.001)

    ground = bpy.data.objects.new("world_ground",None)
    bpy.context.collection.objects.link(ground)
    ground.location=(0,0,0)
    ground.empty_display_size=.1
    # Unlocked proposal, not a W05/W07 gameplay state contract.
    for frame in range(1,8):
        hinge.rotation_euler.z = -math.radians(105) * (frame-1)/6
        hinge.keyframe_insert(data_path="rotation_euler",frame=frame)
    scene.frame_start=1
    scene.frame_end=7
    scene.render.film_transparent=True
    scene.render.resolution_x=512
    scene.render.resolution_y=512
    scene.cycles.samples=opt.samples
    scene.cycles.use_denoising=False
    for layer in scene.view_layers:
        layer.cycles.use_denoising=False
    scene.render.image_settings.file_format="PNG"
    scene.render.image_settings.color_mode="RGBA"

    source = output / "refrigerator_refined_calibration.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(source))
    for f in range(1,8):
        scene.frame_set(f)
        scene.render.filepath=str(output / f"hinge_open_{f-1:02d}.png")
        bpy.ops.render.render(write_still=True)
    scene.frame_set(1)
    objs=[o for o in scene.objects if o.type=="MESH"]
    bpy.ops.object.select_all(action="DESELECT")
    for obj in objs:
        obj.select_set(True)
    bpy.context.view_layer.objects.active=objs[0]
    glb=output/"refrigerator_refined_calibration.glb"
    bpy.ops.export_scene.gltf(filepath=str(glb),export_format="GLB",use_selection=True,export_apply=True)
    scene.frame_set(7)
    # Deterministic checks of actual Blender hierarchy and full travel.
    doors=[o for o in scene.objects if o.name.startswith("door.") and o.type=="MESH" and o.parent==hinge]
    assert len(doors)==9 and all(o.parent==hinge for o in doors)
    assert abs(math.degrees(hinge.rotation_euler.z)+105)<.01
    assert sum(o.name.startswith("shelf.") for o in scene.objects)==8
    assert all((output/f"hinge_open_{i:02d}.png").stat().st_size>1000 for i in range(7))
    files=[source,glb]+[output/f"hinge_open_{i:02d}.png" for i in range(7)]
    report={"type":"NONCANONICAL_CALIBRATION_NOT_APPROVED","family":"F01","source_not_overwritten":True,
      "canonical_candidate":"ll_furniture_refrigerator","reference_revision":"A00-20261108-B001-r1",
      "camera":"existing render_v3_recovery.setup, 30-degree elevation", "frame_timing_proposed_ms":75,
      "hinge_range_deg":[0,-105],"frames":7,"mesh_count":len(objs),"door_meshes":len(doors),
      "real_cavity":True,"material_finish":"CALIBRATION_NOT_F11_VALIDATED",
      "checks":{"door_parenting":True,"shelf_pairs":True,"animation_end_angle":True,"render_files":True},
      "sha256":{p.name:sha256(p) for p in files}}
    (output/"calibration_report.json").write_text(json.dumps(report,indent=2)+"\n")
    print("F01_REFRIGERATOR_CALIBRATION_PASS", json.dumps(report["checks"]),flush=True)


if __name__=="__main__":
    main()
