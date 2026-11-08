"""Render noncanonical V4 IK study frames from its saved Blender scene."""
import bpy
import math
import os
import sys
from mathutils import Vector

root=os.path.abspath(sys.argv[sys.argv.index('--')+1])
travel='--travel' in sys.argv
os.makedirs(os.path.join(root,'preview_frames'),exist_ok=True)
scene=bpy.context.scene
scene.render.engine='BLENDER_EEVEE'
scene.eevee.taa_render_samples=24
scene.render.resolution_x=256
scene.render.resolution_y=256
scene.render.resolution_percentage=100
scene.render.film_transparent=True
scene.render.image_settings.file_format='PNG'
if not any(x.type=='LIGHT' for x in scene.objects):
    bpy.ops.object.light_add(type='AREA',location=(-3,-4,7))
    bpy.context.object.data.energy=850

for species,center,scale in [('cow',Vector((.1+.17*(travel),0,1.0)),4.35),('chicken',Vector((3+.17*(travel),0,.5)),1.7)]:
    bpy.ops.object.camera_add(location=(center.x,center.y-6,center.z+4.25))
    cam=bpy.context.object
    cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler()
    cam.data.type='ORTHO'
    cam.data.ortho_scale=scale
    scene.camera=cam
    for ob in scene.objects:
        if ob.type!='MESH':
            continue
        is_cow=(ob.name.startswith(('Cow_CAL','SplitClovenHoof','Eye','Cattle','Horn')))
        is_bird=(ob.name.startswith(('Chicken_CAL','Beak','ScallopedComb','TailFeather','ChickenEye','ChickenToe','WingFeather')))
        ob.hide_render=not (is_cow if species=='cow' else is_bird)
    frames=(1,5,9,13,17,21,25,29) if travel else (1,3,5,7,9,11,13,15)
    for f in frames:
        scene.frame_set(f)
        scene.render.filepath=os.path.join(root,'preview_frames',f'{species}_{f:02d}.png')
        bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(cam,do_unlink=True)
