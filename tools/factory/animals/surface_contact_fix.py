"""F07 V6: convert foot accessories to target-following mesh contacts.

Run with V5 .blend open. Preserves V5 file; creates separate V6 source.
"""
import bpy
import json
import os
import sys
from mathutils import Matrix

out=os.path.abspath(sys.argv[sys.argv.index('--')+1])
os.makedirs(out,exist_ok=True)
scene=bpy.context.scene
scene.frame_set(1)
report={'identity':'NONCANONICAL_CALIBRATION_ONLY','bindings':{}}
for ob in tuple(scene.objects):
    if ob.type!='MESH' or not ob.name.startswith(('SplitClovenHoof','ChickenToe')):
        continue
    arm=ob.parent
    if not arm or arm.type!='ARMATURE':
        raise RuntimeError('Expected bone-bound foot mesh: '+ob.name)
    bone=ob.parent_bone
    target=bpy.data.objects['F07_IK_'+arm.name+'_'+bone]
    world=ob.matrix_world.copy()
    ob.parent=target
    ob.parent_type='OBJECT'
    ob.parent_bone=''
    ob.matrix_world=world
    bpy.context.view_layer.update()
    # Preserve X/Y placement while grounding actual mesh vertices at frame 1.
    minimum=min((ob.matrix_world@v.co).z for v in ob.data.vertices)
    correction=max(0,-minimum)
    moved=ob.matrix_world.copy()
    moved.translation.z+=correction
    ob.matrix_world=moved
    report['bindings'][ob.name]={'ik_target':target.name,'ground_correction_m':round(correction,6)}
scene.frame_set(1)
path=os.path.join(out,'f07_v6_contact_surface_noncanonical.blend')
bpy.ops.wm.save_as_mainfile(filepath=path)
with open(os.path.join(out,'surface_fix.json'),'w') as f:json.dump(report,f,indent=2)
print('F07_SURFACE_FIX',json.dumps({'objects':len(report['bindings']),
    'max_correction_m':max(v['ground_correction_m'] for v in report['bindings'].values())}))
