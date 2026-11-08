"""F07 V4 NONCANONICAL Blender IK / stance-swing movement experiment.

Run: blender -b f07_noncanonical_calibration.blend --python tools/factory/animals/locomotion_calibration.py -- OUT_DIR
This is in-place locomotion. It does not assert root-motion/no-foot-slide under travel.
"""
import bpy
import json
import math
import os
import sys
from mathutils import Vector

out=os.path.abspath(sys.argv[sys.argv.index('--')+1])
os.makedirs(out,exist_ok=True)
FPS=16
STANCE=0.625
TARGETS={}

# Straight collinear chains are singular for two-bone IK. Add a small rest
# knee/hock bend before attaching targets, keeping segment endpoint heights.
arm=bpy.data.objects['CowRig_CAL']
bpy.context.view_layer.objects.active=arm
arm.select_set(True)
bpy.ops.object.mode_set(mode='EDIT')
for leg in ('front_L','hind_L','front_R','hind_R'):
    upper=arm.data.edit_bones[leg]
    lower=arm.data.edit_bones[leg+'_lower']
    offset=.095 if leg.startswith('front') else -.095
    upper.tail.x+=offset
    lower.head.x+=offset
bpy.ops.object.mode_set(mode='OBJECT')

def target_for(arm,bone_name):
    pb=arm.pose.bones[bone_name]
    rest=arm.matrix_world @ pb.tail
    ob=bpy.data.objects.new('F07_IK_'+arm.name+'_'+bone_name,None)
    bpy.context.collection.objects.link(ob)
    ob.location=rest
    ob.empty_display_type='SPHERE'
    ob.empty_display_size=.045
    con=pb.constraints.new('IK')
    con.name='F07_PlantIK'
    con.target=ob
    con.chain_count=2
    con.use_stretch=False
    return ob,rest.copy()

def add_gait(arm_name,legs,phase_offsets,step,lift):
    arm=bpy.data.objects[arm_name]
    results=[]
    for leg,phase_offset in zip(legs,phase_offsets):
        lower=leg+'_lower' if arm_name.startswith('Cow') else 'foot_'+leg[-1]
        target,rest=target_for(arm,lower)
        for clip in ('idle','walk'):
            action=bpy.data.actions.new(target.name+'_'+clip)
            target.animation_data_create()
            target.animation_data.action=action
            action.use_fake_user=True
            for frame in range(1,FPS+1):
                p=((frame-1)/FPS+phase_offset)%1
                if clip=='idle' or p<STANCE:
                    dx,dz=0,0
                else:
                    u=(p-STANCE)/(1-STANCE)
                    dx=step*math.sin(2*math.pi*u)
                    dz=lift*math.sin(math.pi*u)
                target.location=(rest.x+dx,rest.y,rest.z+dz)
                target.keyframe_insert(data_path='location',frame=frame,group='F07FootTarget')
            # Explicit loop boundary avoids last-to-first discontinuity.
            target.location=rest
            target.keyframe_insert(data_path='location',frame=FPS+1,group='F07FootTarget')
        target.animation_data.action=bpy.data.actions[target.name+'_walk']
        TARGETS[leg]={'arm':arm,'bone':lower,'target':target,'rest':rest,'phase':phase_offset,'step':step,'lift':lift}
        results.append(target.name)
    arm.animation_data.action=bpy.data.actions[arm.name+'_walk']
    return results

cow_legs=['front_L','hind_L','front_R','hind_R']
cow_targets=add_gait('CowRig_CAL',cow_legs,[0,.5,.5,0],.19,.13)
bird_targets=add_gait('BirdRig_CAL',['leg_L','leg_R'],[0,.5],.13,.09)

def bind_foot_accessories(prefix,arm_name,bone_names):
    arm=bpy.data.objects[arm_name]
    assignments=0
    for ob in tuple(bpy.data.objects):
        if not ob.name.startswith(prefix) or ob.type!='MESH':
            continue
        bone=min(bone_names,key=lambda b:(arm.matrix_world @ arm.data.bones[b].tail_local-ob.location).length)
        world=ob.matrix_world.copy()
        ob.parent=arm
        ob.parent_type='BONE'
        ob.parent_bone=bone
        ob.matrix_world=world
        assignments+=1
    return assignments

hoof_bindings=bind_foot_accessories('SplitClovenHoof','CowRig_CAL',[x+'_lower' for x in cow_legs])
toe_bindings=bind_foot_accessories('ChickenToe','BirdRig_CAL',['foot_L','foot_R'])

# Enforce the designed in-place contact phase at a full discrete cycle.
scene=bpy.context.scene
scene.frame_start=1
scene.frame_end=FPS
scene.render.fps=FPS
metrics={}
for leg,info in TARGETS.items():
    arm,target=info['arm'],info['target']
    support_x=[]
    errors=[]
    lift_samples=[]
    for frame in range(1,FPS+1):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        p=((frame-1)/FPS+info['phase'])%1
        end=arm.matrix_world @ arm.pose.bones[info['bone']].tail
        errors.append((end-target.location).length)
        if p<STANCE:
            support_x.append(target.location.x)
        else:
            lift_samples.append(target.location.z-info['rest'].z)
    metrics[leg]={'max_ik_target_error_m':round(max(errors),5),
                  'stance_target_x_range_m':round(max(support_x)-min(support_x),8),
                  'swing_lift_max_m':round(max(lift_samples),5),
                  'ik_present':any(c.type=='IK' for c in arm.pose.bones[info['bone']].constraints)}

# Keep source editable and source validation independent from rendered appearance.
scene.frame_set(1)
blend=os.path.join(out,'f07_v4_ik_inplace_noncanonical.blend')
bpy.ops.wm.save_as_mainfile(filepath=blend)
report={'identity':'NONCANONICAL_CALIBRATION_ONLY','rigs':{'cow':cow_targets,'chicken':bird_targets},
        'fps':FPS,'stance_duty':STANCE,'metrics':metrics,'bound_accessories':{'hooves':hoof_bindings,'toes':toe_bindings},
        'limitations':['root motion not authored','world-space feet on moving animal unverified',
                       'mesh deformation and hoof attachment require visual review',
                       'F12 direction/clip and W05/W07 timing not approved']}
path=os.path.join(out,'movement_qa.json')
with open(path,'w') as f: json.dump(report,f,indent=2)
print('F07_IK_QA',json.dumps(report))
