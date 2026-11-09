"""Blender-native bonnet and rear-hatch hinge clips for F10 experimental vehicle.

Each export contains an independently animated pivot, editable mesh children,
and four sprite review poses. These are source candidates, not gameplay assets.
"""
import argparse
import json
import math
import sys
from pathlib import Path

import bpy

sys.path.insert(0,str(Path(__file__).resolve().parent))
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"blender_factory"))
import render_v3_recovery as base
from hero_hatchback import build,BONNET_HINGE,HATCH_HINGE

CLIPS={
    "bonnet":{"hinge":BONNET_HINGE,"open_deg":56,"sign":-1,"heading":45,
              "arg":"bonnet_deg"},
    "rear_hatch":{"hinge":HATCH_HINGE,"open_deg":70,"sign":1,"heading":225,
                  "arg":"rear_hatch_deg"},
}


def curves(action):
    if hasattr(action,"fcurves"):
        return list(action.fcurves)
    return [c for layer in action.layers for strip in layer.strips
            for bag in strip.channelbags for c in bag.fcurves]


def animate(scene,hinge,clip,parameters):
    scene.frame_start=1
    scene.frame_end=5
    scene.render.fps=10
    scene.render.fps_base=1
    for frame,degree in enumerate((0,parameters["open_deg"]*.33,
                                   parameters["open_deg"]*.67,
                                   parameters["open_deg"],parameters["open_deg"]),1):
        hinge.rotation_euler.y=math.radians(parameters["sign"]*degree)
        hinge.keyframe_insert(data_path="rotation_euler",index=1,frame=frame,
                              group=f"F10_{clip}_transverse_hinge")
    action=hinge.animation_data.action
    assert action is not None
    action.name=f"F10_{clip}_open_400ms_NONCANONICAL"
    track=curves(action)
    assert any(len(c.keyframe_points)==5 for c in track)
    for curve in track:
        for key in curve.keyframe_points:
            key.interpolation="LINEAR"
    scene.frame_set(1)
    bpy.context.view_layer.update()
    return action.name


def run(out,samples=8):
    out.mkdir(parents=True,exist_ok=True)
    for clip,params in CLIPS.items():
        dest=out/clip
        dest.mkdir(parents=True,exist_ok=True)
        scene=base.setup()
        scene.cycles.samples=samples
        scene.cycles.use_denoising=False
        bpy.context.view_layer.cycles.use_denoising=False
        scene.camera.data.ortho_scale=7.80
        scene.render.resolution_x=768
        scene.render.resolution_y=768
        scene.render.resolution_percentage=100
        scene.render.film_transparent=True
        scene.render.image_settings.color_mode="RGBA"
        build(**{params["arg"]:0})
        turntable=bpy.data.objects.new(f"F10 {clip} review turntable",None)
        bpy.context.collection.objects.link(turntable)
        for ob in list(scene.objects):
            if ob.parent is None and (ob.type in ("MESH","CURVE") or ob.name==params["hinge"]):
                world=ob.matrix_world.copy()
                ob.parent=turntable
                ob.matrix_world=world
        turntable.rotation_euler.z=math.radians(params["heading"])
        hinge=bpy.data.objects[params["hinge"]]
        assert len(hinge.children)>=2, f"{clip} has no movable panel geometry"
        action=animate(scene,hinge,clip,params)
        bpy.ops.wm.save_as_mainfile(filepath=str((dest/f"{clip}.blend").resolve()))
        glb=dest/f"{clip}.glb"
        bpy.ops.export_scene.gltf(filepath=str(glb.resolve()),export_format="GLB",
                                  export_animations=True)
        assert glb.exists() and glb.stat().st_size>1000
        frames=[]
        for idx,frame in enumerate((1,2,3,4)):
            scene.frame_set(frame)
            bpy.context.view_layer.update()
            png=f"{clip}_{idx:02}.png"
            scene.render.filepath=str((dest/png).resolve())
            bpy.ops.render.render(write_still=True)
            frames.append({"frame":frame,"png":png,"hinge_deg":round(
                params["sign"]*(0,params["open_deg"]*.33,
                                params["open_deg"]*.67,params["open_deg"])[idx],3)})
        manifest={"schema_version":1,"status":"NONCANONICAL_F10_PANEL_CLIP",
                  "clip":clip,"hinge":params["hinge"],"action":action,
                  "axis_blender":"Y","duration_s":.4,
                  "heading_deg":params["heading"],"frames":frames,
                  "glb":glb.name,"blend":f"{clip}.blend"}
        (dest/"manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")
        print("F10_PANEL_CLIP_DONE",clip,len(frames),glb.stat().st_size,flush=True)


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--samples",type=int,default=8)
    args=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    params=parser.parse_args(args)
    run(params.output,params.samples)
