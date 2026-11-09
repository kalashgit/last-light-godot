"""Single-frame diagnostic side/isometric render of F07 bird anatomy."""
import bpy
import os
import sys
from mathutils import Vector

path=os.path.abspath(sys.argv[sys.argv.index('--')+1])
frame=int(sys.argv[sys.argv.index('--')+2])
scene=bpy.context.scene
scene.render.engine='BLENDER_EEVEE'
scene.eevee.taa_render_samples=32
scene.render.resolution_x=512
scene.render.resolution_y=512
scene.render.resolution_percentage=100
scene.render.film_transparent=True
scene.render.image_settings.file_format='PNG'
center=Vector((3.2,0,.65))
bpy.ops.object.camera_add(location=(center.x+4.5,center.y-6,center.z+4.4))
cam=bpy.context.object
cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler()
cam.data.type='ORTHO'
cam.data.ortho_scale=2.0
scene.camera=cam
for ob in scene.objects:
    if ob.type=='MESH':
        ob.hide_render=not ob.name.startswith(('Chicken_CAL','ChickenShank','Beak','ScallopedComb',
                                             'TailFeather','ChickenEye','ChickenToe','WingFeather',
                                             'F07SlopeTestPlane'))
scene.frame_set(frame)
scene.render.filepath=path
bpy.ops.render.render(write_still=True)
print('F07_BIRD_QUICK_RENDER',path)
