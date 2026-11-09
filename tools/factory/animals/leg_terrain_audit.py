"""Evaluate both skinned bird shanks against a sloped ground test fixture."""
import bpy
import json
import os
import sys

out=os.path.abspath(sys.argv[sys.argv.index('--')+1])
slope=float(sys.argv[sys.argv.index('--')+2])
scene=bpy.context.scene
result={}
threshold=0.005
for name in ('ChickenShank_L_CAL','ChickenShank_R_CAL'):
    ob=bpy.data.objects[name]
    worst=(0,None)
    for frame in range(1,33):
        scene.frame_set(frame)
        ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get())
        mesh=ev.to_mesh()
        clearance=min((ev.matrix_world@v.co).z-slope*(ev.matrix_world@v.co).x for v in mesh.vertices)
        ev.to_mesh_clear()
        if clearance<worst[0]:worst=(clearance,frame)
    result[name]={'maximum_mesh_penetration_m':round(-worst[0],6),'worst_frame':worst[1]}
os.makedirs(out,exist_ok=True)
result['qa']={'mesh_penetration_threshold_m':threshold,
              'passed':all(entry['maximum_mesh_penetration_m']<=threshold
                           for name,entry in result.items() if name.startswith('ChickenShank_'))}
with open(os.path.join(out,'leg_terrain_audit.json'),'w') as f:json.dump(result,f,indent=2)
print('F07_SHANK_TERRAIN_AUDIT',json.dumps(result))
if '--strict' in sys.argv and not result['qa']['passed']:
    sys.exit(2)
