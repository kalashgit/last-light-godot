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


def author_blender_door_action(scene,hinge):
    """Actual Blender animation datablock, independent of rendered PNG poses."""
    scene.frame_start=1
    scene.frame_end=5
    scene.render.fps=10
    scene.render.fps_base=1
    for frame,angle in ((1,0),(2,22),(3,44),(4,66),(5,66)):
        hinge.rotation_euler.z=math.radians(angle)
        hinge.keyframe_insert(data_path="rotation_euler",index=2,frame=frame,
                              group="F10_driver_door_vertical_hinge")
    action=hinge.animation_data.action
    assert action is not None
    action.name="F10_driver_front_door_open_400ms_NONCANONICAL"
    for curve in action.fcurves:
        for point in curve.keyframe_points:
            point.interpolation="LINEAR"
    scene.frame_set(1)
    bpy.context.view_layer.update()
    assert len(action.fcurves)>=1
    assert any(len(c.keyframe_points)==5 for c in action.fcurves)
    return action.name


def run(output, samples=8, heading_deg=0):
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
        turntable=bpy.data.objects.new("F10 HERO clip turntable",None)
        bpy.context.collection.objects.link(turntable)
        for obj in list(scene.objects):
            if obj.parent is None and (obj.type in ("MESH","CURVE") or
                                       obj.name=="F10 HERO driver door vertical hinge PROTOTYPE"):
                world=obj.matrix_world.copy()
                obj.parent=turntable
                obj.matrix_world=world
        turntable.rotation_euler.z=math.radians(heading_deg)
        hinge=bpy.data.objects.get("F10 HERO driver door vertical hinge PROTOTYPE")
        assert hinge is not None and len(hinge.children)>=17
        assert abs(math.degrees(hinge.rotation_euler.z)-angle)<.001
        door=bpy.data.objects["F10 HERO connected left front door exterior"]
        assert door.parent == hinge and len(door.data.polygons)>10
        assert bpy.data.objects["F10 HERO inset front door pane"].parent == hinge
        assert bpy.data.objects["F10 HERO driver door movable upper belt"].parent == hinge
        for name in ("driver door inner padded card","driver door inner upper rail",
                     "driver door inner armrest","driver door interior latch",
                     "driver door front edge thickness","driver door rear edge thickness"):
            assert bpy.data.objects["F10 HERO "+name].parent == hinge
        for name in ("textured driver seat cushion","raked driver seat back",
                     "driver headrest","dashboard lower assembly","cabin recessed footwell"):
            assert bpy.data.objects["F10 HERO "+name].parent != hinge
        assert bpy.data.objects.get("F10 HERO driver aperture recessed dark inner backing") is None
        # At rest a sampled door polygon must occupy exactly its authored
        # body-surface coordinate; a double pivot translation would fail here.
        if index==0:
            vid=door.data.polygons[0].vertices[0]
            actual=door.matrix_world @ door.data.vertices[vid].co
            assert (actual-door.data.vertices[vid].co).length<1e-5
        bpy.context.view_layer.update()
        if index==0:
            action_name=author_blender_door_action(scene,hinge)
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
        "canonical_master_id":None,"heading_deg":heading_deg,"samples":samples,
        "clip":"driver_front_door_open","timing_ms":400,"frames":frames,
        "blender_action":"F10_driver_front_door_open_400ms_NONCANONICAL",
        "blender_keyframes":[1,2,3,4,5],"blender_fps":10,
        "cabin_opening":"separated_body_surface_with_recessed_floor_and_fixed_seat",
        "moving_door_parts":"exterior_skin_window_frame_inner_card_armrest_latch_edges",
        "limitations":["no validated door/fender collision clearance",
                       "no Godot gameplay contract","no founder visual approval"]},indent=2)+"\n")
    print("F10_DOOR_CALIBRATION_DONE",len(frames))


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--samples",type=int,default=8)
    p.add_argument("--heading-deg",type=float,default=0)
    args=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    a=p.parse_args(args)
    run(a.output,a.samples,a.heading_deg)
