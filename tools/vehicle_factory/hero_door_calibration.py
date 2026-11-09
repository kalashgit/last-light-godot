"""Four-frame mechanically isolated F10 driver-door experiment.

The connected body surface opens about one stable vertical hinge. This is an
art/animation calibration, not a production collision or interaction rig.
"""
import argparse
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "blender_factory"))
import render_v3_recovery as base
from hero_hatchback import build


def run(output, samples=8):
    output.mkdir(parents=True, exist_ok=True)
    frames=[]
    for index, angle in enumerate((0, 22, 44, 66)):
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
        build(driver_door_deg=angle)
        hinge=bpy.data.objects.get("F10 HERO driver door vertical hinge PROTOTYPE")
        assert hinge is not None and len(hinge.children)>=11
        assert abs(math.degrees(hinge.rotation_euler.z)-angle)<.001
        door=bpy.data.objects["F10 HERO connected left front door exterior"]
        assert door.parent == hinge and len(door.data.polygons)>10
        assert bpy.data.objects["F10 HERO inset front door pane"].parent == hinge
        assert bpy.data.objects["F10 HERO driver door movable upper belt"].parent == hinge
        # At rest a sampled door polygon must occupy exactly its authored
        # body-surface coordinate; a double pivot translation would fail here.
        if index==0:
            vid=door.data.polygons[0].vertices[0]
            actual=door.matrix_world @ door.data.vertices[vid].co
            assert (actual-door.data.vertices[vid].co).length<1e-5
        bpy.context.view_layer.update()
        if index==0:
            bpy.ops.wm.save_as_mainfile(filepath=str((output/"hero_front_door_calibration.blend").resolve()))
        uv=world_to_camera_view(scene,scene.camera,Vector((0,0,0)))
        filename=f"door_{index:02}.png"
        scene.render.filepath=str((output/filename).resolve())
        bpy.ops.render.render(write_still=True)
        frames.append({"index":index,"angle_deg":angle,"duration_ms":100,
                       "png":filename,"pivot_xyz_m":[.965,-.717,.94],
                       "fixed_world_pivot_px":[round(uv.x*768,4),round((1-uv.y)*768,4)]})
        print("F10_DOOR_FRAME",index,angle,flush=True)
    (output/"manifest.json").write_text(json.dumps({
        "schema_version":1,"asset_id":"NONCANONICAL_F10_HERO_HATCHBACK_V2",
        "status":"EXPERIMENTAL_DRIVER_DOOR_NOT_APPROVED",
        "canonical_master_id":None,"heading_deg":0,"samples":samples,
        "clip":"driver_front_door_open","timing_ms":400,"frames":frames,
        "limitations":["no approved inner upholstery","no collision clearance proof",
                       "no Godot gameplay contract","no founder visual approval"]},indent=2)+"\n")
    print("F10_DOOR_CALIBRATION_DONE",len(frames))


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--samples",type=int,default=8)
    args=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    a=p.parse_args(args)
    run(a.output,a.samples)
