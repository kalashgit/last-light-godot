"""F01 source-first refrigerator calibration. NOT canonical production approval.

blender -b --factory-startup -t 2 --python tools/factory/furniture/refrigerator_calibration.py -- --output build/f01_calibration/refrigerator
"""
import argparse
import hashlib
import json
import math
import struct
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
    # render_v3_recovery's weighted-normal helper requires this in Blender 4.0;
    # otherwise it emits warnings and its modifier is not evaluated correctly.
    ob.data.use_auto_smooth = True
    if parent:
        ob.parent = parent
        ob.matrix_parent_inverse = parent.matrix_world.inverted()
    return ob


def hardware_pin(name, xyz, radius, length, material, parent=None, rotation=None):
    ob = hero.cyl(name, xyz, radius, length, material, vertices=20, rotation=rotation)
    ob.data.use_auto_smooth = True
    if parent:
        ob.parent = parent
        ob.matrix_parent_inverse = parent.matrix_world.inverted()
    return ob


def main():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--samples", type=int, default=24)
    opt = parser.parse_args(args)
    output = opt.output.resolve()
    output.mkdir(parents=True, exist_ok=True)

    scene = hero.setup()  # existing locked F12-predecessor 30-degree camera/light rig
    m = hero.materials("f01_fridge")
    m["paint"]=enamel("F01 original aged mint enamel V9",base=(.49,.55,.53),
                      texture_folder=output/"textures")
    m["plastic"]=hero.mat("F01 original warm ivory cavity liner",(.73,.73,.65),rough=.65,wear=.025)
    m["glass_edge"]=hero.mat("F01 glass edge cool jade",(.46,.68,.61),rough=.30,wear=.01)
    m["drawer"]=hero.mat("F01 milky translucent drawer plastic",(.62,.71,.65),rough=.33,wear=.025)
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
    for side in (-1,1):
        component(f"liner.side_wall.{side}",(side*(w/2-t-.012),0,h/2),(.016,d-.09,h-.16),m["plastic"],.004)
        component(f"opening.frame.stile.{side}",(side*(w/2-.025),-d/2-.012,h/2),(.028,.018,h-.05),m["plastic"],.005)
    for tag,z in (("head",h-.025),("threshold",.025)):
        component(f"opening.frame.{tag}",(0,-d/2-.012,z),(w-.047,.018,.035),m["plastic"],.004)
    for n, z in enumerate((.40,.70,1.00,1.34)):
        component(f"shelf.{n}.glass", (0,.015,z), (w-2*t-.035,d-.15,.018),shelf_glass,.003)
        component(f"shelf.{n}.front_lip", (0,-d/2+.08,z), (w-2*t-.035,.013,.032),m["glass_edge"],.002)
        for side in (-1,1):
            component(f"shelf.{n}.wall_bracket.{side}",
                      (side*(w/2-t-.029),.03,z-.023),(.035,.40,.019),m["plastic"],.005)
    # Real separated lower bin: a shallow open-topped vessel, not a painted cube.
    # Geometry is parented to its own sliding origin to allow future independent
    # state animation; the door-open clip intentionally does not move this drawer.
    slide = bpy.data.objects.new("slide_local.crisper_drawer",None)
    bpy.context.collection.objects.link(slide)
    slide.location=(0,-.04,.245)
    slide.empty_display_size=.055
    slide["motion_axis_local"]="-Y"
    slide["proposed_travel_m"]=.19
    for side in (-1,1):
        component(f"crisper.fixed_slide_rail.{side}",
                  (side*(w/2-t-.042),-.02,.215),(.028,.48,.021),m["chrome"],.003)
    component("crisper.tray.floor",(0,-.034,.178),(.555,.446,.018),m["drawer"],.006,slide)
    component("crisper.tray.front",(0,-.263,.270),(.555,.017,.184),m["drawer"],.008,slide)
    component("crisper.tray.back",(0,.188,.270),(.555,.015,.184),m["drawer"],.005,slide)
    for side in (-1,1):
        component(f"crisper.tray.side.{side}",(side*.272,-.037,.270),(.015,.435,.184),m["drawer"],.005,slide)
    component("crisper.tray.grip",(0,-.286,.323),(.207,.023,.023),m["plastic"],.011,slide)
    component("crisper.tray.top_edge",(0,-.260,.362),(.54,.023,.014),m["plastic"],.005,slide)
    # A separate molded freezer/chiller hood and accessible dial visually define
    # the upper cold compartment without filling the hollow main refrigerator.
    component("chiller.upper_hood",(0,.204,1.603),(.60,.19,.092),m["plastic"],.015)
    component("chiller.lower_shadow_lip",(0,.085,1.549),(.57,.016,.014),m["glass_edge"],.003)
    hardware_pin("control.thermostat_dial",(.210,-.005,1.551),.027,.022,m["black"],rotation=(math.pi/2,0,0))
    hardware_pin("control.thermostat_center",(.210,-.022,1.551),.009,.025,m["plastic"],rotation=(math.pi/2,0,0))
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
    for side in (-1,1):
        component(f"door.inner_gasket.vertical.{side}",
                  (side*(w/2-.035),-d/2-.005,h/2),(.014,.013,h-.13),m["rubber"],.002,hinge)
    for z in (.10,h-.10):
        component(f"door.inner_gasket.horizontal.{z:.2f}",
                  (0,-d/2-.005,z),(w-.086,.013,.015),m["rubber"],.002,hinge)
    # Real shallow storage pockets, parented to the door, seen when fully open.
    for n,z in enumerate((.36,.73,1.11)):
        component(f"door.storage_bin.{n}.front_rail",(0,-d/2+.008,z),(.53,.026,.045),m["plastic"],.006,hinge)
        component(f"door.storage_bin.{n}.shelf",(0,-d/2+.024,z-.063),(.53,.10,.018),m["plastic"],.003,hinge)
    component("door.pull.vertical",(.295,-d/2-.11,h/2),(.025,.035,.38),m["chrome"],.009,hinge)
    for z in (h/2-.18,h/2+.18):
        component(f"door.pull.standoff.{z:.3f}",(.295,-d/2-.088,z),(.035,.055,.032),m["steel"],.011,hinge)
    # A pressed metal face seam remains visible at native sprite scale.
    component("door.lower_pressed_seam",(0,-d/2-.09,.220),(w-.11,.007,.004),m["steel"],.002,hinge)
    for z in (.17,h-.16):
        component("door.hinge_pin",(hinge_xyz[0],hinge_xyz[1],z),(.03,.03,.063),m["steel"],.006)
    for z in (.03,.07,.11):
        component("compressor.vent_louver",(0,-d/2-.029,z),(.40,.012,.008),m["black"],.002)
    component("compressor.dark_recess",(0,-d/2-.027,.078),(.43,.006,.115),m["black"],.002)
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
    # Include hinge transform and world-ground anchor; otherwise Blender can
    # export a visually valid GLB with ZERO animation clips or reusable pivots.
    for obj in objs+[hinge,slide,ground]:
        obj.select_set(True)
    bpy.context.view_layer.objects.active=objs[0]
    glb=output/"refrigerator_refined_calibration.glb"
    bpy.ops.export_scene.gltf(filepath=str(glb),export_format="GLB",use_selection=True,
                              export_apply=True,export_animations=True,
                              export_nla_strips=False,export_force_sampling=True)
    binary=glb.read_bytes()
    json_length=struct.unpack_from("<I",binary,12)[0]
    gltf_doc=json.loads(binary[20:20+json_length])
    clips=gltf_doc.get("animations",[])
    assert clips,"GLB export lost hinge animation"
    assert any("hinge_local" in node.get("name","") for node in gltf_doc.get("nodes",[])),"GLB lost hinge pivot"
    scene.frame_set(7)
    # Deterministic checks of actual Blender hierarchy and full travel.
    doors=[o for o in scene.objects if o.name.startswith("door.") and o.type=="MESH" and o.parent==hinge]
    tray=[o for o in scene.objects if o.name.startswith("crisper.tray.") and o.type=="MESH" and o.parent==slide]
    assert len(doors)>=9 and all(o.parent==hinge for o in doors)
    assert len(tray)==7 and all(o.parent==slide for o in tray)
    assert slide["proposed_travel_m"]==.19
    assert abs(math.degrees(hinge.rotation_euler.z)+105)<.01
    assert sum(o.name.endswith(".glass") and o.name.startswith("shelf.") for o in scene.objects)==4
    assert sum(".wall_bracket." in o.name and o.name.startswith("shelf.") for o in scene.objects)==8
    # Actual ray intersection is the strongest cheap regression test of a hollow
    # appliance: closed door blocks the cavity; open door reveals the rear liner.
    test_ray_start=(0,-1.40,1.20)
    test_ray_direction=(0,1,0)
    scene.frame_set(1)
    hit_closed=scene.ray_cast(bpy.context.evaluated_depsgraph_get(),test_ray_start,test_ray_direction)
    scene.frame_set(7)
    hit_open=scene.ray_cast(bpy.context.evaluated_depsgraph_get(),test_ray_start,test_ray_direction)
    assert hit_closed[0] and hit_closed[-2].name=="door.enamel_panel",hit_closed
    assert hit_open[0] and hit_open[-2].name=="liner.back",hit_open
    assert all((output/f"hinge_open_{i:02d}.png").stat().st_size>1000 for i in range(7))
    texture_files=sorted((output/"textures").glob("*.png"))
    assert len(texture_files)==2
    color_image=bpy.data.images.get("F01 original enamel basecolor")
    assert color_image is not None
    assert max(color_image.pixels[0],color_image.pixels[1],color_image.pixels[2])>.30, "Empty/black enamel texture"
    assert len(gltf_doc.get("textures",[]))>=2,"Portable PBR images were lost in GLB export"
    files=[source,glb]+texture_files+[output/f"hinge_open_{i:02d}.png" for i in range(7)]
    report={"type":"NONCANONICAL_CALIBRATION_NOT_APPROVED","family":"F01","source_not_overwritten":True,
      "canonical_candidate":"ll_furniture_refrigerator","reference_revision":"A00-20261108-B001-r1",
      "camera":"existing render_v3_recovery.setup, 30-degree elevation", "frame_timing_proposed_ms":75,
      "hinge_range_deg":[0,-105],"frames":7,"mesh_count":len(objs),"door_meshes":len(doors),
      "crisper_tray_meshes":len(tray),"crisper_slide_travel_proposed_m":.19,
      "real_cavity":True,"material_finish":"IMAGE_BACKED_ENAMEL_CALIBRATION_NOT_F11_VALIDATED",
      "portable_texture_count":len(gltf_doc.get("textures",[])),
      "original_texture_images":[str(p.relative_to(output)) for p in texture_files],
      "checks":{"door_parenting":True,"crisper_separate_sliding_rig":True,
                "shelf_pairs":True,"animation_end_angle":True,"render_files":True,
                "closed_door_raycast":hit_closed[-2].name,
                "open_cavity_raycast":hit_open[-2].name},
      "glb_animation_clips":len(clips),"glb_hinge_pivot_exported":True,
      "sha256":{p.name:sha256(p) for p in files}}
    (output/"calibration_report.json").write_text(json.dumps(report,indent=2)+"\n")
    print("F01_REFRIGERATOR_CALIBRATION_PASS", json.dumps(report["checks"]),flush=True)


if __name__=="__main__":
    main()
