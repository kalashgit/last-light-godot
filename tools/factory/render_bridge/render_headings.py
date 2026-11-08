"""F12 candidate directional render runner for EXISTING .blend assets.

Example:
 blender -b --factory-startup --python tools/factory/render_bridge/render_headings.py -- \
   --blend /absolute/model.blend --object VehicleRoot --output /tmp/f12-vehicle \
   --headings 16 --width 256 --height 256

Noncanonical QA output only. No A00 ID or approval is inferred.
"""
import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def setup_camera(scene, width, height):
    elevation=math.asin(0.5)
    camera_data=bpy.data.cameras.new("F12_CAMERA_CANDIDATE")
    camera=bpy.data.objects.new("F12_CAMERA_CANDIDATE",camera_data)
    scene.collection.objects.link(camera)
    camera.location=(8,8,8*math.sqrt(2)*math.tan(elevation))
    camera.rotation_euler=(-camera.location).to_track_quat("-Z","Y").to_euler()
    camera_data.type="ORTHO"
    # Preserve exactly 40px per horizontal projected metre, independent of canvas width.
    camera_data.ortho_scale=height/(40*math.sqrt(2))
    scene.camera=camera
    return camera

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--blend",type=Path,required=True)
    parser.add_argument("--object",required=True,help="Exact existing object name to rotate as root")
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--headings",type=int,choices=[4,8,16],default=16)
    parser.add_argument("--width",type=int,default=256)
    parser.add_argument("--height",type=int,default=256)
    parser.add_argument("--samples",type=int,default=16)
    args=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    opts=parser.parse_args(args)
    if opts.width<64 or opts.height<64 or opts.width>4096 or opts.height>4096:
        raise ValueError("invalid render size")
    if opts.samples<1 or opts.samples>4096:
        raise ValueError("invalid samples")
    blend=opts.blend.resolve(strict=True)
    out=opts.output.resolve()
    if out.exists():
        raise FileExistsError("refusing to overwrite output directory: "+str(out))
    bpy.ops.wm.open_mainfile(filepath=str(blend))
    scene=bpy.context.scene
    root=bpy.data.objects.get(opts.object)
    if root is None:
        raise ValueError("missing exact root object: "+opts.object)
    if root.type=="CAMERA":
        raise ValueError("camera cannot be asset root")
    if root.hide_render:
        raise ValueError('root is hidden from rendering')
    if root.location.length > 0.0001:
        raise ValueError('root origin must be at world origin for locked F12 camera')
    def belongs_to_root(obj):
        while obj is not None:
            if obj == root:
                return True
            obj = obj.parent
        return False
    descendants = [obj for obj in bpy.data.objects if belongs_to_root(obj)]
    geometry = [obj for obj in descendants if obj.type == 'MESH' and not obj.hide_render]
    if not geometry:
        raise ValueError('root has no renderable mesh descendants')
    # Existing scene lights and materials are preserved; camera is replaced.
    setup_camera(scene,opts.width,opts.height)
    scene.render.engine="CYCLES"
    scene.cycles.samples=opts.samples
    scene.cycles.use_denoising=False
    scene.render.resolution_x=opts.width
    scene.render.resolution_y=opts.height
    scene.render.resolution_percentage=100
    scene.render.film_transparent=True
    scene.render.image_settings.file_format="PNG"
    scene.render.image_settings.color_mode="RGBA"
    scene.view_settings.view_transform="Standard"
    scene.render.image_settings.color_depth="8"
    # Rotating the existing root keeps camera and lighting fixed in world space.
    # The root's origin must already be at the intended ground/pivot anchor.
    initial=root.rotation_mode
    original=root.rotation_euler.copy() if initial=="XYZ" else None
    if initial!="XYZ":
        raise ValueError("asset root must use XYZ Euler rotation for this candidate runner")
    out.mkdir(parents=True,exist_ok=False)
    frames=[]
    for heading in range(opts.headings):
        root.rotation_euler=original.copy()
        root.rotation_euler.z+=2*math.pi*heading/opts.headings
        bpy.context.view_layer.update()
        # Fail before rendering a clipped direction: bounding-box corners are
        # measured in the same orthographic camera used for the PNG output.
        projected = []
        for mesh in geometry:
            for corner in mesh.bound_box:
                world = mesh.matrix_world @ Vector(corner)
                projected.append(world_to_camera_view(scene, scene.camera, world))
        if not projected or any(p.z <= 0 or p.x < 0.02 or p.x > 0.98 or p.y < 0.02 or p.y > 0.98 for p in projected):
            raise ValueError('heading %d geometry exceeds camera safe frame' % heading)
        filename="heading_%02d.png"%heading
        path=out/filename
        scene.render.filepath=str(path)
        bpy.ops.render.render(write_still=True)
        frames.append({"key":"heading_%02d"%heading,"file":filename,
                       "width":opts.width,"height":opts.height,
                       "duration_ms":100,"direction":heading,"frame_index":0,
                       "clip":"static","source_sha256":digest(path)})
    root.rotation_euler=original
    manifest={"schema_version":1,"status":"CANDIDATE_NOT_A00_APPROVED",
              "source_blend_sha256":digest(blend),"root_object":opts.object,
              "headings":opts.headings,"camera":"F12_80x40_candidate",
              "pivot_policy":"EXISTING_ROOT_ORIGIN_NOT_VERIFIED",
              "frames":frames}
    (out/"manifest.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n")
    print("F12_DIRECTIONAL_CANDIDATE_RENDER_COMPLETE",len(frames),flush=True)

if __name__=="__main__":
    main()
