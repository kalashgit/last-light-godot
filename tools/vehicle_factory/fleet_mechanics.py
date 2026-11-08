"""Noncanonical F10 mechanical hinge calibration for hatchback and sedan.

Builds Blender-editable panel overlays and real pivot-keyframed clips. This is
NOT a finished cutout body: no door/engine cavity or engine collision logic is
present, so it must not be used as final interactive or Golden vehicle art.
"""
import argparse
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"tools"/"blender_factory"))
sys.path.insert(0,str(Path(__file__).resolve().parent))
import render_v3_recovery as base
from fleet_catalog import PROFILES,PALETTE
from fleet_render import build_vehicle,make_materials,cube,faces,pipe

CLIPS={
    "front_left_door_open":dict(axis="Z",angle_deg=64,frames=4,ms_per_frame=100),
    "hood_open":dict(axis="Y",angle_deg=-48,frames=4,ms_per_frame=100),
    "trunk_open":dict(axis="Y",angle_deg=58,frames=4,ms_per_frame=100),
}


def hinge_panel(name,pivot_xyz,center_xyz,size_xyz,material):
    hinge=bpy.data.objects.new("LL F10 PIVOT "+name,None)
    bpy.context.collection.objects.link(hinge)
    hinge.location=pivot_xyz
    shell=cube("mechanical overlay "+name,center_xyz,size_xyz,material,.018)
    world=shell.matrix_world.copy()
    shell.parent=hinge
    shell.matrix_world=world
    shell["calibration_only"]="NO_BODY_CAVITY_OR_COLLISION_APPROVAL"
    return hinge,shell


def join_to_hinge(hinge,part):
    world=part.matrix_world.copy()
    part.parent=hinge
    part.matrix_world=world
    return part


def build_mechanical_scene(model):
    if model not in ("compact_hatchback","city_sedan"):
        raise ValueError("only calibrated passenger bodies supported")
    profile=PROFILES[model]
    L,W,H=profile["dimensions_m"]
    base.setup()
    bpy.context.scene.cycles.use_denoising=False
    bpy.context.view_layer.cycles.use_denoising=False
    job=dict(model=model,paint_hex=PALETTE["olive_green"],condition_level=1)
    build_vehicle(job)
    m=make_materials(job["paint_hex"],job["condition_level"])
    hinges={}
    hinges["front_left_door_open"]=hinge_panel(
        "front_left_door",(L*.275,-W*.461,.83),
        (L*.112,-W*.469,.656),(L*.321,.029,.435),m["body"])
    # Glass rises with the door instead of remaining a detached static decal.
    door_glass=faces("LL F10 left front door glass overlay",[
        (L*.105,-W*.337,H-.105),(L*.270,-W*.335,H-.13),
        (L*.270,-W*.458,.935),(-L*.016,-W*.454,.935)],m["glass"])
    join_to_hinge(hinges["front_left_door_open"][0],door_glass)
    hinges["hood_open"]=hinge_panel(
        "hood",(L*.305,0,.88),
        (L*.398,0,.879),(L*.173,W*.75,.026),m["body"])
    if model=="compact_hatchback":
        roof_back=-L*.383
        sill_back=-L*.460
        pivot=bpy.data.objects.new("LL F10 PIVOT rear_hatch",None)
        bpy.context.collection.objects.link(pivot)
        pivot.location=(roof_back,0,H-.065)
        glass=faces("LL F10 hatch glass moving panel",[
            (roof_back,-W*.337,H-.068),(roof_back,W*.337,H-.068),
            (sill_back,W*.445,.893),(sill_back,-W*.445,.893)],m["black_glass"])
        join_to_hinge(pivot,glass)
        for name,coords in (
            ("hatch left upright",[(roof_back,-W*.337,H-.068),(sill_back,-W*.445,.893)]),
            ("hatch right upright",[(roof_back,W*.337,H-.068),(sill_back,W*.445,.893)]),
            ("hatch lower frame",[(sill_back,-W*.445,.893),(sill_back,W*.445,.893)])):
            frame=pipe(name,coords,.034,m["body"])
            join_to_hinge(pivot,frame)
        lower=cube("hatch lower lid",(-L*.470,0,.741),
                   (L*.031,W*.82,.255),m["body"],.018)
        join_to_hinge(pivot,lower)
        hinges["trunk_open"]=(pivot,lower)
    else:
        hinges["trunk_open"]=hinge_panel(
            "trunk",(-L*.369,0,.88),(-L*.426,0,.875),
            (L*.105,W*.72,.029),m["body"])
    for hinge,shell in hinges.values():
        assert shell.parent==hinge
    return hinges


def animate_clip(hinges,clip):
    cfg=CLIPS[clip]
    scene=bpy.context.scene
    axis=2 if cfg["axis"]=="Z" else 1
    hinge=hinges[clip][0]
    # Reset every hinge before authoring a separately reusable action.
    for pivot,_ in hinges.values():
        pivot.rotation_euler=(0,0,0)
        pivot.animation_data_clear()
    for frame in range(1,cfg["frames"]+1):
        t=(frame-1)/(cfg["frames"]-1)
        hinge.rotation_euler[axis]=math.radians(cfg["angle_deg"])*t
        hinge.keyframe_insert(data_path="rotation_euler",frame=frame,index=axis)
    scene.frame_start=1
    scene.frame_end=cfg["frames"]
    scene.render.film_transparent=True
    return cfg


def run(model,out_dir,render):
    out_dir.mkdir(parents=True,exist_ok=True)
    hinges=build_mechanical_scene(model)
    results=[]
    for clip,cfg in CLIPS.items():
        settings=animate_clip(hinges,clip)
        scene=bpy.context.scene
        scene.frame_set(settings["frames"])
        bpy.context.view_layer.update()
        hinge=hinges[clip][0]
        angle=math.degrees(hinge.rotation_euler[2 if settings["axis"]=="Z" else 1])
        assert abs(angle)>40,(clip,angle)
        clip_dir=out_dir/clip
        clip_dir.mkdir(exist_ok=True)
        bpy.ops.wm.save_as_mainfile(filepath=str((clip_dir/"hinge_calibration.blend").resolve()))
        if render:
            scene.render.resolution_x=384
            scene.render.resolution_y=384
            scene.cycles.samples=8
            for frame in range(1,settings["frames"]+1):
                scene.frame_set(frame)
                scene.render.filepath=str((clip_dir/f"frame_{frame-1:02}.png").resolve())
                bpy.ops.render.render(write_still=True)
        results.append(dict(clip=clip,frames=settings["frames"],
            ms_per_frame=settings["ms_per_frame"],final_angle_deg=round(angle,3),
            blend=str((clip_dir/"hinge_calibration.blend").relative_to(out_dir)),
            rendered_frames=settings["frames"] if render else 0))
        print("F10_MECHANICAL_CLIP_CALIBRATED",model,clip,round(angle,3),flush=True)
    manifest=dict(schema_version=1,model=model,canonical_master_id=None,
        status="PANEL_OVERLAY_CALIBRATION_NOT_GOLDEN_NOT_GODOT_INTEGRATED",
        limits=["No cutout doors or physically empty cabin", "No engine or cargo cavities",
                "No swept collision validation", "Clip events are W05/W07 proposals"],
        clips=results)
    (out_dir/"manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")
    return manifest


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--model",choices=("compact_hatchback","city_sedan"),required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--render",action="store_true")
    args=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    a=p.parse_args(args)
    run(a.model,a.out,a.render)
