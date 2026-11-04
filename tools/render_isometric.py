"""Blender 4.3 offline renderer; see docs/visual-pipeline.md. No runtime 3D."""
import argparse
import bpy
import hashlib
import json
import math
import sys
from pathlib import Path
from mathutils import Vector

def configure_scene():
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = 16
    scene.cycles.use_denoising = False
    scene.render.resolution_x = scene.render.resolution_y = 256
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGBA'
    scene.render.film_transparent = True
    scene.view_settings.view_transform = 'Standard'
    scene.view_settings.look = 'Medium High Contrast'
    scene.world.color = (.22, .24, .26)
    # Elevation 30 degrees makes the ground diamond exactly 2:1.
    # 56.5685 px/world-unit => 40 horizontal,20 vertical per ground axis.
    bpy.ops.object.camera_add()
    cam = bpy.context.object
    cam.data.type = 'ORTHO'
    cam.data.ortho_scale = 256 / math.sqrt(3200)
    target = Vector((0, 0, (64 / math.sqrt(3200)) / math.cos(math.pi / 6)))
    cam.location = target + Vector((8, -8, math.sqrt(128) * math.tan(math.pi / 6)))
    cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
    scene.camera = cam
    bpy.ops.object.light_add(type='AREA', location=(-3, -4, 7))
    bpy.context.object.data.energy = 450
    bpy.context.object.data.shape = 'DISK'
    bpy.context.object.data.size = 4
    bpy.context.object.rotation_euler = (Vector((0, 0, 0)) - bpy.context.object.location).to_track_quat('-Z', 'Y').to_euler()
    return scene, cam

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--input', type=Path)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--width-tiles', type=float, default=1.0)
    p.add_argument('--directions', type=int, choices=(1, 4, 8), default=1)
    p.add_argument('--source', required=True)
    p.add_argument('--license', required=True)
    p.add_argument('--smoke-cube', action='store_true')
    a = p.parse_args(sys.argv[sys.argv.index('--') + 1:])
    if a.width_tiles <= 0:
        p.error('width-tiles must be positive')
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    if a.smoke_cube:
        bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, .5))
    elif a.input:
        ext = a.input.suffix.lower()
        if ext == '.fbx':
            bpy.ops.import_scene.fbx(filepath=str(a.input.resolve()))
        elif ext in ('.gltf', '.glb'):
            bpy.ops.import_scene.gltf(filepath=str(a.input.resolve()))
        elif ext == '.obj':
            bpy.ops.wm.obj_import(filepath=str(a.input.resolve()))
        else:
            p.error('supported source formats: FBX, GLB, GLTF, OBJ')
    else:
        p.error('provide --input or --smoke-cube')
    meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    if not meshes:
        raise RuntimeError('No meshes imported')
    # Apply shared normalization at an empty parent, preserving mesh relationships.
    points = [o.matrix_world @ Vector(c) for o in meshes for c in o.bound_box]
    lo = Vector(tuple(min(v[i] for v in points) for i in range(3)))
    hi = Vector(tuple(max(v[i] for v in points) for i in range(3)))
    scale = a.width_tiles / max(hi.x - lo.x, hi.y - lo.y, .0001)
    root = bpy.data.objects.new('SpritePivot', None)
    bpy.context.collection.objects.link(root)
    for obj in list(bpy.context.scene.objects):
        if obj != root and obj.parent is None:
            obj.parent = root
    root.scale = (scale,) * 3
    root.location = (-.5 * (lo.x + hi.x) * scale, -.5 * (lo.y + hi.y) * scale, -lo.z * scale)
    # Nest pivot so all directions rotate around grounded center.
    pivot = bpy.data.objects.new('DirectionPivot', None)
    bpy.context.collection.objects.link(pivot)
    root.parent = pivot
    scene, cam = configure_scene()
    a.output.mkdir(parents=True, exist_ok=True)
    frames = []
    for i in range(a.directions):
        pivot.rotation_euler.z = i * math.tau / a.directions
        filename = f'direction_{i:02}.png'
        scene.render.filepath = str((a.output / filename).resolve())
        bpy.ops.render.render(write_still=True)
        frames.append({'file': filename, 'angle_degrees': i * 360 / a.directions, 'anchor_px': [128, 192]})
    manifest = {'schema': 1, 'tile_px': [80, 40], 'canvas_px': [256, 256], 'frames': frames,
                'source': a.source, 'license': a.license, 'width_tiles': a.width_tiles,
                'input_sha256': hashlib.sha256(a.input.read_bytes()).hexdigest() if a.input else None,
                'blender_version': bpy.app.version_string, 'shadows': 'runtime ground ellipse; no baked floor',
                'status': 'candidate; inspect clipping, grounding, palette and license before integration'}
    (a.output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')

if __name__ == "__main__":
    main()
