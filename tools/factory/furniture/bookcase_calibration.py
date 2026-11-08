"""Original noncanonical F01 bookcase geometry/material calibration.

blender -b --factory-startup -t 2 --python tools/factory/furniture/bookcase_calibration.py -- --output build/f01_calibration/bookcase
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

import bpy

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/"tools/factory/furniture"))
from refrigerator_calibration import component,sha256
sys.path.insert(0,str(ROOT/"tools/blender_factory"))
import render_v3_recovery as hero
from f01_materials import wood_grain


def main():
    args=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    p=argparse.ArgumentParser()
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--samples",type=int,default=48)
    opt=p.parse_args(args)
    out=opt.output.resolve();out.mkdir(parents=True,exist_ok=True)
    scene=hero.setup()
    scene.cycles.use_denoising=False
    for layer in scene.view_layers: layer.cycles.use_denoising=False
    m=hero.materials("f01_bookcase")
    w,d,h=.935,.312,1.584
    side=.032
    # Actual open-front shelving construction, empty shelf bays and rear backboard.
    component("case.back_wood_panel",(0,d/2-.009,h/2),(w-.045,.018,h-.05),m["wood_dark"],.004)
    for x in (-w/2+side/2,w/2-side/2):
        component("case.oak_side",(x,0,h/2),(side,d,h),m["wood"],.006)
        # Thin front solid-oak face frame, grain runs vertically.
        component("case.front_stile",(x,-d/2-.006,h/2),(.045,.016,h-.04),m["wood_light"],.004)
        # Subtle full-height shadow groove behind the solid front stile.
        component("joinery.stile_shadow_gap",(x+(.018 if x<0 else -.018),-d/2-.016,h/2),
                  (.004,.003,h-.08),m["wood_dark"],.001)
    for z in (.028,h-.027):
        component("case.top_bottom_panel",(0,0,z),(w-.065,d,.054),m["wood"],.008)
    for index,z in enumerate((.355,.735,1.115)):
        component(f"shelf.{index}.plank",(0,-.005,z),(w-.067,d-.026,.035),m["wood"],.005)
        component(f"shelf.{index}.front_edge",(0,-d/2-.010,z),(.865,.020,.038),m["wood_light"],.002)
        component(f"joinery.shelf_under_shadow.{index}",(0,-d/2-.023,z-.024),
                  (.79,.004,.004),m["wood_dark"],.001)
        # Two real shelf support pins on each side, not flat image detail.
        for x in (-w/2+.047,w/2-.047):
            component(f"hardware.shelf_support.{index}",(x,-.106,z-.025),(.016,.032,.008),m["steel"],.001)
    component("case.lower_plinth",(0,-d/2-.013,.045),(.84,.031,.073),m["wood_dark"],.005)
    for x in (-.40,.40):
        # Recessed peg-hole strips signal adjustable shelf construction at scale.
        for z in (.45,.54,.83,.92,1.22,1.30):
            component("joinery.peg_socket",(x,-d/2+.035,z),(.007,.005,.009),m["wood_dark"],.001)
    for x in (-.36,.36):
        component("case.rear_mount_bracket",(x,d/2+.004,1.40),(.065,.016,.08),m["steel"],.003)
    # Grain lines run longitudinally: X-varying side panels create Z-oriented grain.
    vertical=wood_grain("F01 oak quarter-sawn vertical V5",(.43,.28,.15),(.34,.20,.10),"X")
    horizontal=wood_grain("F01 oak shelf crossgrain V5",(.51,.33,.18),(.41,.25,.12),"Y")
    dark_wood=wood_grain("F01 dark hardwood endgrain V5",(.29,.17,.088),(.21,.11,.05),"Y")
    for ob in bpy.context.scene.objects:
        if ob.type!="MESH" or not ob.data.materials:continue
        if ob.name.startswith(("case.oak_side","case.front_stile","case.back_wood_panel")):
            ob.data.materials[0]=vertical
        elif ob.name.startswith(("shelf.","case.top_bottom_panel")):
            ob.data.materials[0]=horizontal
        elif ob.name.startswith("case.lower_plinth"):
            ob.data.materials[0]=dark_wood
    ground=bpy.data.objects.new("world_ground",None);bpy.context.collection.objects.link(ground)
    ground.location=(0,d/2,0)
    scene.render.resolution_x=512;scene.render.resolution_y=512
    scene.cycles.samples=opt.samples
    scene.render.film_transparent=True
    scene.render.image_settings.file_format="PNG"
    scene.render.image_settings.color_mode="RGBA"
    blend=out/"bookcase_calibration.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    scene.render.filepath=str(out/"bookcase_empty_world.png")
    bpy.ops.render.render(write_still=True)
    meshes=[o for o in scene.objects if o.type=="MESH"]
    bpy.ops.object.select_all(action="DESELECT")
    for o in meshes:o.select_set(True)
    bpy.context.view_layer.objects.active=meshes[0]
    glb=out/"bookcase_calibration.glb"
    bpy.ops.export_scene.gltf(filepath=str(glb),export_format="GLB",use_selection=True,export_apply=True)
    assert len([o for o in meshes if o.name.startswith("shelf.")])==6
    assert len([o for o in meshes if o.name.startswith("case.oak_side")])==2
    assert not any("filler" in o.name for o in meshes)
    assert glb.stat().st_size>5000
    files=[blend,glb,out/"bookcase_empty_world.png"]
    report={"stage":"NONCANONICAL_CALIBRATION_NOT_APPROVED","canonical_candidate":"ll_furniture_bookcase",
        "a00_revision":"A00-20261108-B004-r1","original_360_sources_preserved":True,
        "source_bounds_reference_m":[w,d,h],"shelf_count":3,"open_bays":4,
        "material_status":"PROCEDURAL_PILOT_NOT_F11_APPROVED","geometry_status":"BLENDER_REPLAY_PASS_NEEDS_INDEPENDENT_QA",
        "mesh_count":len(meshes),"sha256":{f.name:sha256(f) for f in files}}
    (out/"calibration_report.json").write_text(json.dumps(report,indent=2)+"\n")
    print("F01_BOOKCASE_CALIBRATION_PASS",len(meshes),flush=True)


if __name__=="__main__":main()
