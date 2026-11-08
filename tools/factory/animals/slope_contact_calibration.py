"""F07 V7 noncanonical sloped-ground contact study from V6 Blender source.

Usage: blender -b V6.blend --python slope_contact_calibration.py -- OUT_DIR SLOPE
Surface: z = SLOPE*x (metres); no F03 terrain ownership or integration implied.
"""
import bpy
import json
import math
import os
import sys
from collections import defaultdict

out=os.path.abspath(sys.argv[sys.argv.index('--')+1])
slope=float(sys.argv[sys.argv.index('--')+2])
assert abs(slope)<=.20
os.makedirs(out,exist_ok=True)
scene=bpy.context.scene
scene.frame_start=1
scene.frame_end=32
arms=[bpy.data.objects[n] for n in ('CowRig_CAL','BirdRig_CAL')]
targets=[o for o in scene.objects if o.name.startswith('F07_IK_')]
feet=[o for o in scene.objects if o.type=='MESH' and o.name.startswith(('SplitClovenHoof','ChickenToe'))]

# Snapshot the original flat-ground animation before adding a new z curve.
baseline={}
for frame in range(1,34):
    scene.frame_set(frame)
    baseline[frame]={'root':{a.name:a.location.copy() for a in arms},
                     'targets':{t.name:t.location.copy() for t in targets}}

for frame in range(1,34):
    scene.frame_set(frame)
    for arm in arms:
        src=baseline[frame]['root'][arm.name]
        arm.location.z=src.z+slope*src.x
        arm.keyframe_insert(data_path='location',frame=frame,group='F07SlopeRoot')
    for target in targets:
        src=baseline[frame]['targets'][target.name]
        target.location.z=src.z+slope*src.x
        target.keyframe_insert(data_path='location',frame=frame,group='F07SlopeFoot')
        target.rotation_euler[1]=-math.atan(slope)

# The visible skinned body can intersect terrain even when foot accessories clear.
# Preserve the IK rig; adjust only low body-shell vertices in this calibration.
body_lifts={}
for body_name,arm_name in [('Cow_CAL_NOT_CANONICAL','CowRig_CAL'),('Chicken_CAL_NOT_CANONICAL','BirdRig_CAL')]:
    body=bpy.data.objects[body_name]
    arm=bpy.data.objects[arm_name]
    minimum=1e9
    for frame in range(1,33):
        scene.frame_set(frame)
        deps=bpy.context.evaluated_depsgraph_get()
        ev=body.evaluated_get(deps)
        mesh_eval=ev.to_mesh()
        minimum=min(minimum,min((ev.matrix_world@v.co).z-slope*(ev.matrix_world@v.co).x for v in mesh_eval.vertices))
        ev.to_mesh_clear()
    lift=max(0,-minimum+.005)
    body_lifts[body_name]=round(lift,6)
    if lift:
        for v in body.data.vertices:
            influence=max(0,min(1,(.60-v.co.z)/.50))
            v.co.z+=lift*influence
        body.data.update()

# Align contact surfaces, not merely IK pivots, to the inclined plane.
scene.frame_set(1)
corrections={}
for ob in feet:
    bpy.context.view_layer.update()
    clearance=min((ob.matrix_world@v.co).z-slope*(ob.matrix_world@v.co).x for v in ob.data.vertices)
    world=ob.matrix_world.copy()
    world.translation.z-=clearance
    ob.matrix_world=world
    corrections[ob.name]=round(-clearance,6)

report={'identity':'NONCANONICAL_CALIBRATION_ONLY','slope':slope,'feet':{},'body_root_clearance_lifts_m':body_lifts,'summary':{}}
for ob in feet:
    target=ob.parent
    leg=target.name.split('_CAL_',1)[-1]
    phase=0 if leg in ('front_L_lower','hind_R_lower','foot_L') else .5
    samples=defaultdict(list)
    minimum=1e9
    target_errors=[]
    for frame in range(1,33):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        points=[ob.matrix_world@v.co for v in ob.data.vertices]
        clearance=min(p.z-slope*p.x for p in points)
        minimum=min(minimum,clearance)
        p=((frame-1)/16+phase)%1
        cyc=math.floor((frame-1)/16+phase)
        if p<.625:
            samples[cyc].append(ob.matrix_world.translation.copy())
    drift=max(max(p.x for p in a)-min(p.x for p in a) for a in samples.values())
    report['feet'][ob.name]={'minimum_mesh_plane_clearance_m':round(minimum,6),
                            'maximum_stance_origin_x_drift_m':round(drift,6),
                            'frame1_correction_m':corrections[ob.name]}
report['summary']={'maximum_penetration_m':round(max(0,-min(v['minimum_mesh_plane_clearance_m'] for v in report['feet'].values())),6),
                   'maximum_stance_origin_x_drift_m':round(max(v['maximum_stance_origin_x_drift_m'] for v in report['feet'].values()),6),
                   'tested_foot_objects':len(feet)}
# A visible fixture plane for visual review, not a game terrain tile.
verts=[(x,y,slope*x) for x,y in ((-2,-2),(5,-2),(5,2),(-2,2))]
mesh=bpy.data.meshes.new('F07SlopeTestPlaneGeometry')
mesh.from_pydata(verts,[],[(0,1,2,3)])
mesh.update()
plane=bpy.data.objects.new('F07SlopeTestPlane',mesh)
bpy.context.collection.objects.link(plane)
mat=bpy.data.materials.new('F07 inclined terrain fixture')
mat.diffuse_color=(.18,.23,.18,1)
mesh.materials.append(mat)
scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out,'f07_v7_slope_noncanonical.blend'))
with open(os.path.join(out,'slope_qa.json'),'w') as f:json.dump(report,f,indent=2)
print('F07_SLOPE_QA',json.dumps(report['summary']))
