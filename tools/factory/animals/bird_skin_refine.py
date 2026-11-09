"""F07 V8 noncanonical chicken skin-weight redesign, preserving topology/rig.

Run with V6 blend open. Produces a new source, never overwrites V6.
"""
import bpy
import json
import os
import sys

out=os.path.abspath(sys.argv[sys.argv.index('--')+1])
leg_cap=float(sys.argv[sys.argv.index('--')+2]) if len(sys.argv)>sys.argv.index('--')+2 else 1.0
assert 0 <= leg_cap <= 1
os.makedirs(out,exist_ok=True)
mesh=bpy.data.objects['Chicken_CAL_NOT_CANONICAL']
arm=bpy.data.objects['BirdRig_CAL']
names=[b.name for b in arm.data.bones]
for group in tuple(mesh.vertex_groups):
    mesh.vertex_groups.remove(group)
groups={name:mesh.vertex_groups.new(name=name) for name in names}

counts={'leg_dominant':0,'body_dominant':0,'head_neck_dominant':0}
for v in mesh.data.vertices:
    x,y,z=mesh.matrix_world@v.co
    side='L' if y>=0 else 'R'
    leg='leg_'+side
    foot='foot_'+side
    weights={}
    # Leg/torso transition with a strictly normalized blend at every vertex.
    leg_factor=leg_cap*max(0.0,min(1.0,(.52-z)/.23))
    if leg_factor>0:
        foot_factor=max(0.0,min(1.0,(.30-z)/.20))
        weights[leg]=leg_factor*(1-foot_factor)
        weights[foot]=leg_factor*foot_factor
    remain=1-leg_factor
    if x>3.32 and z>.63:
        head_factor=max(0.0,min(1.0,(x-3.30)/.17))
        weights['head']=remain*head_factor
        weights['neck']=remain*(1-head_factor)
        counts['head_neck_dominant']+=1
    else:
        wing_factor=.24 if abs(y)>.14 and z>.38 else 0
        weights['body']=remain*(1-wing_factor)
        if wing_factor:
            weights['wing_'+side]=remain*wing_factor
        counts['body_dominant']+=1
    if leg_factor>.6:counts['leg_dominant']+=1
    weights={name:w for name,w in weights.items() if w>1e-7}
    norm=sum(weights.values())
    if norm<=0:raise RuntimeError('Unweighted vertex '+str(v.index))
    for name,weight in weights.items():
        groups[name].add([v.index],weight/norm,'REPLACE')

bpy.context.scene.frame_set(1)
path=os.path.join(out,'f07_v8_bird_skin_noncanonical.blend')
bpy.ops.wm.save_as_mainfile(filepath=path)
summary={'status':'NONCANONICAL_CALIBRATION_ONLY','body_vertices':len(mesh.data.vertices),
         'groups':len(mesh.vertex_groups),'weighted_counts':counts,
         'topology_rebuilt':False,'weighting_redesigned':True, 'leg_cap':leg_cap}
with open(os.path.join(out,'bird_skin_refine.json'),'w') as f:json.dump(summary,f,indent=2)
print('F07_BIRD_SKIN',json.dumps(summary))
