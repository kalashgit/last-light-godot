"""Check evaluated skinned animal body vertices against V7 incline fixture."""
import bpy
import json
import os
import sys

out=os.path.abspath(sys.argv[sys.argv.index('--')+1])
slope=float(sys.argv[sys.argv.index('--')+2])
scene=bpy.context.scene
result={}
for name in ('Cow_CAL_NOT_CANONICAL','Chicken_CAL_NOT_CANONICAL'):
    obj=bpy.data.objects[name]
    worst=(0,None)
    for frame in range(1,33):
        scene.frame_set(frame)
        deps=bpy.context.evaluated_depsgraph_get()
        ob=obj.evaluated_get(deps)
        mesh=ob.to_mesh()
        clearance=min((ob.matrix_world@v.co).z-slope*(ob.matrix_world@v.co).x for v in mesh.vertices)
        ob.to_mesh_clear()
        if clearance<worst[0]:
            worst=(clearance,frame)
    result[name]={'maximum_body_mesh_penetration_m':round(-worst[0],6),'worst_frame':worst[1]}
os.makedirs(out,exist_ok=True)
with open(os.path.join(out,'body_terrain_audit.json'),'w') as f:json.dump(result,f,indent=2)
print('F07_BODY_TERRAIN_AUDIT',json.dumps(result))
