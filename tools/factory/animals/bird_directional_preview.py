"""Noncanonical eight-heading 2.5D bird art review sheet, not F12 production."""
import bpy
import math
import os
import sys
from mathutils import Vector

out=os.path.abspath(sys.argv[sys.argv.index('--')+1])
motion='--motion' in sys.argv
os.makedirs(out,exist_ok=True)
scene=bpy.context.scene
scene.frame_set(1)
scene.render.engine='BLENDER_EEVEE'
scene.eevee.taa_render_samples=16 if motion else 32
scene.render.resolution_x=192 if motion else 256
scene.render.resolution_y=192 if motion else 256
scene.render.resolution_percentage=100
scene.render.film_transparent=True
scene.render.image_settings.file_format='PNG'
center=Vector((3.02,0,.56))
for ob in scene.objects:
    if ob.type=='MESH':
        ob.hide_render=not ob.name.startswith(('Chicken_CAL','ChickenShank','Beak','ScallopedComb',
                                             'TailFeather','ChickenEye','ChickenToe','WingFeather',
                                             'ChickenThighFeather','ChickenInstep'))
for heading in range(8):
    theta=2*math.pi*heading/8
    pos=center+Vector((6*math.cos(theta),6*math.sin(theta),4.8))
    bpy.ops.object.camera_add(location=pos)
    cam=bpy.context.object
    cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler()
    cam.data.type='ORTHO'
    cam.data.ortho_scale=1.82
    scene.camera=cam
    for frame in ((1,5,9,13) if motion else (1,)):
        scene.frame_set(frame)
        filename=(f'bird_heading_{heading:02d}_f{frame:02d}.png' if motion
                  else f'bird_heading_{heading:02d}.png')
        scene.render.filepath=os.path.join(out,filename)
        bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(cam,do_unlink=True)
print('F07_DIRECTIONAL_PREVIEW',out,'motion=',motion,
      'rendered_count=',32 if motion else 8)
