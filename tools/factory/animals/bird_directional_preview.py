"""Noncanonical eight-heading 2.5D bird art review sheet, not F12 production."""
import bpy
import math
import os
import sys
from mathutils import Vector

out=os.path.abspath(sys.argv[sys.argv.index('--')+1])
os.makedirs(out,exist_ok=True)
scene=bpy.context.scene
scene.frame_set(1)
scene.render.engine='BLENDER_EEVEE'
scene.eevee.taa_render_samples=32
scene.render.resolution_x=256
scene.render.resolution_y=256
scene.render.resolution_percentage=100
scene.render.film_transparent=True
scene.render.image_settings.file_format='PNG'
center=Vector((3.02,0,.56))
for ob in scene.objects:
    if ob.type=='MESH':
        ob.hide_render=not ob.name.startswith(('Chicken_CAL','ChickenShank','Beak','ScallopedComb',
                                             'TailFeather','ChickenEye','ChickenToe','WingFeather'))
for heading in range(8):
    theta=2*math.pi*heading/8
    pos=center+Vector((6*math.cos(theta),6*math.sin(theta),4.8))
    bpy.ops.object.camera_add(location=pos)
    cam=bpy.context.object
    cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler()
    cam.data.type='ORTHO'
    cam.data.ortho_scale=1.82
    scene.camera=cam
    scene.render.filepath=os.path.join(out,f'bird_heading_{heading:02d}.png')
    bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(cam,do_unlink=True)
print('F07_DIRECTIONAL_PREVIEW',out)
