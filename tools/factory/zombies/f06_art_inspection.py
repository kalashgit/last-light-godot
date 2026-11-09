"""Render a non-gameplay high-resolution F06 facial art review image.

blender -b --factory-startup --python tools/factory/zombies/f06_art_inspection.py -- \
  /absolute/path/editable_noncanonical.blend /absolute/path/face_review.png

This inspection changes only the opened Blender session; no .blend save occurs.
It intentionally does not change F12 sprite camera or game exports.
"""
import sys
from pathlib import Path
import bpy
from mathutils import Vector

args=sys.argv[sys.argv.index('--')+1:]
source,target=Path(args[0]).resolve(),Path(args[1]).resolve()
bpy.ops.wm.open_mainfile(filepath=str(source))
scene=bpy.context.scene
rig=bpy.data.objects['F05_TEST_RIG']
rig.animation_data.action=bpy.data.actions['F06_V2_CAL_idle']
scene.frame_set(1)
turntable=bpy.data.objects.get('F06_DIRECTION_TURNTABLE')
if turntable:turntable.rotation_euler.z=0
camera=scene.camera
camera.data.type='ORTHO'
camera.data.ortho_scale=.76
camera.location=(.70,-1.05,1.96)
look_at=Vector((0,0,1.65))
camera.rotation_euler=(look_at-camera.location).to_track_quat('-Z','Y').to_euler()
scene.render.resolution_x=512
scene.render.resolution_y=512
scene.render.resolution_percentage=100
scene.render.film_transparent=False
scene.world.color=(.15,.15,.15)
for light in (o for o in bpy.data.objects if o.type=='LIGHT'):
    light.location=(-2.2,-2.4,4.1)
    light.data.energy=550
    light.data.size=2.0
scene.render.image_settings.file_format='PNG'
scene.render.image_settings.color_mode='RGBA'
scene.render.filepath=str(target)
target.parent.mkdir(parents=True,exist_ok=True)
bpy.ops.render.render(write_still=True)
print('F06_ART_INSPECTION_RENDERED',target)
