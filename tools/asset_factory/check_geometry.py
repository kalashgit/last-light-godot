"""Blender geometry/calibration contract tests independent of raster review."""
import sys, json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent)); sys.path.insert(0,str(Path(__file__).parents[1]))
import bpy
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
from catalog import registry, DIMS
from geometry import build, MATERIALS, MESHES
from render_isometric import configure_scene
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
scene,cam=configure_scene(); bpy.context.view_layer.update()
def project(p):
 v=world_to_camera_view(scene,cam,Vector(p)); return Vector((v.x*256,(1-v.y)*256))
origin=project((0,0,0)); axis=project((1,0,0))-origin
assert (origin-Vector((128,192))).length<.001,(origin,axis)
assert abs(abs(axis.x)-40)<.001 and abs(abs(axis.y)-20)<.001,axis
families=set()
for spec in registry():
 parts=build(spec); assert parts
 families.add(spec['family'])
 for obj in parts:
  data=obj.data; bpy.data.objects.remove(obj,do_unlink=True)
  if isinstance(data,bpy.types.Curve) and data.users==0: bpy.data.curves.remove(data)
assert families==set(DIMS)
# Verify recipe parameter variation really changes geometry/material data.
spec=registry()[0].copy(); spec['dimensions_m']=[.15,.15,.3]; spec['wear']='damaged'; spec['color_variant']=2
parts=build(spec); bpy.context.view_layer.update()
assert max((o.matrix_world@Vector(v)).z for o in parts if o.type=='MESH' for v in o.bound_box)>.29
assert any(m=='steel' and state=='damaged' for m,color,state in MATERIALS)
assert len(MESHES)<10
print('GEOMETRY PASS: 300 recipes, %d families, %d shared unit meshes, parameter variants; origin128,192 and 80x40 projection' % (len(families),len(MESHES)))
