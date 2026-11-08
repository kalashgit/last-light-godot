"""Read-only Blender mesh-level foot contact audit on the V5 traveling fixture.

Run: blender -b V5.blend --python surface_contact_audit.py -- OUT_DIR
The z=0 surface is a temporary flat calibration plane, not F03 terrain.
"""
import bpy
import json
import math
import os
import sys
from collections import defaultdict

out=os.path.abspath(sys.argv[sys.argv.index('--')+1])
os.makedirs(out,exist_ok=True)
scene=bpy.context.scene
foot_objects=[o for o in scene.objects if o.type=='MESH' and o.name.startswith(('SplitClovenHoof','ChickenToe'))]
report={'fixture':'F07_V5_NONCANONICAL','ground_z_m':0,'objects':{},'species':{}}
for ob in foot_objects:
    side='cow' if ob.name.startswith('SplitClovenHoof') else 'chicken'
    leg=ob.parent_bone if ob.parent_type=='BONE' else ob.parent.name.split('_CAL_',1)[-1]
    phase=0 if leg in ('front_L_lower','hind_R_lower','foot_L') else .5
    contacts=defaultdict(list)
    min_z=1e9
    max_penetration=0
    for frame in range(1,33):
        scene.frame_set(frame)
        deps=bpy.context.evaluated_depsgraph_get()
        ev=ob.evaluated_get(deps)
        world=ev.matrix_world
        vertices=[world@v.co for v in ev.data.vertices]
        min_frame_z=min(v.z for v in vertices)
        min_z=min(min_z,min_frame_z)
        max_penetration=max(max_penetration,-min_frame_z)
        cycle=math.floor((frame-1)/16+phase)
        p=((frame-1)/16+phase)%1
        if p<.625:
            contacts[cycle].append(world.translation.copy())
    drift=max(max(v.x for v in samples)-min(v.x for v in samples) for samples in contacts.values())
    report['objects'][ob.name]={'species':side,'leg':leg,
       'minimum_mesh_vertex_z_m':round(min_z,6),
       'max_ground_penetration_m':round(max_penetration,6),
       'max_stance_accessory_origin_x_drift_m':round(drift,6)}
for species in ('cow','chicken'):
    vals=[v for v in report['objects'].values() if v['species']==species]
    report['species'][species]={'foot_object_count':len(vals),
      'maximum_ground_penetration_m':max(v['max_ground_penetration_m'] for v in vals),
      'maximum_stance_accessory_drift_m':max(v['max_stance_accessory_origin_x_drift_m'] for v in vals)}
with open(os.path.join(out,'surface_contact_audit.json'),'w') as f:json.dump(report,f,indent=2)
print('F07_SURFACE_AUDIT',json.dumps(report['species']))
