"""F07 V5 NONCANONICAL traveling root and world-planted stance feet.

Run with V4 .blend open: blender -b V4.blend --python traveling_gait_calibration.py -- OUT
Frame-by-frame root motion and IK contacts are a technical fixture, not final speed/gameplay.
"""
import bpy
import json
import math
import os
import sys
from mathutils import Vector

out=os.path.abspath(sys.argv[sys.argv.index('--')+1])
os.makedirs(out,exist_ok=True)
FRAMES=32
CYCLE=16
DUTY=.625
ROOT_SPEED=.011  # metres per frame, unapproved calibration speed
LIFT={'cow':.13,'chicken':.09}
SPECIES={
 'cow':('CowRig_CAL',{'front_L':0,'hind_L':.5,'front_R':.5,'hind_R':0}),
 'chicken':('BirdRig_CAL',{'leg_L':0,'leg_R':.5}),
}

ACCESSORIES={
 'CowRig_CAL':('Eye','CattleEar','Horn','CattleMuzzle','CattleTail','CattleUdder'),
 'BirdRig_CAL':('Beak','ScallopedComb','TailFeather','ChickenEye','WingFeather'),
}

def attach_non_skinned_details(arm):
    count=0
    for ob in tuple(bpy.data.objects):
        if ob.type!='MESH' or ob.parent is not None:
            continue
        if not ob.name.startswith(ACCESSORIES[arm.name]):
            continue
        world=ob.matrix_world.copy()
        ob.parent=arm
        ob.matrix_world=world
        count+=1
    return count

def ease(x):
    return x*x*(3-2*x)

scene=bpy.context.scene
scene.frame_start=1
scene.frame_end=FRAMES
results={}

for species,(name,leg_phases) in SPECIES.items():
    arm=bpy.data.objects[name]
    accessory_count=attach_non_skinned_details(arm)
    arm.animation_data_create()
    arm.animation_data.action=bpy.data.actions[name+'_walk']
    arm.location.x=0
    targets={}
    original={}
    for leg in leg_phases:
        lower=leg+'_lower' if species=='cow' else 'foot_'+leg[-1]
        ob=bpy.data.objects['F07_IK_'+name+'_'+lower]
        targets[leg]=ob
        original[leg]=ob.location.copy()
        ob.animation_data.action=bpy.data.actions[ob.name+'_walk']
    for frame in range(1,FRAMES+2):
        t=(frame-1)/CYCLE
        arm.location.x=ROOT_SPEED*(frame-1)
        arm.keyframe_insert(data_path='location',frame=frame,group='F07RootTravel')
        for leg,phase in leg_phases.items():
            target=targets[leg]
            position=t+phase
            cycle=math.floor(position)
            p=position-cycle
            old_contact_x=original[leg].x+ROOT_SPEED*CYCLE*(cycle-phase)
            next_contact_x=old_contact_x+ROOT_SPEED*CYCLE
            if p<DUTY:
                x,z=old_contact_x,original[leg].z
            else:
                u=(p-DUTY)/(1-DUTY)
                x=old_contact_x+(next_contact_x-old_contact_x)*ease(u)
                z=original[leg].z+LIFT[species]*math.sin(math.pi*u)
            target.location=(x,original[leg].y,z)
            target.keyframe_insert(data_path='location',frame=frame,group='F07WorldFoot')
    arm.animation_data.action.use_fake_user=True
    results[species]={'root_travel_m':ROOT_SPEED*(FRAMES-1),'body_detail_attachments':accessory_count,'legs':{}}
    for leg,phase in leg_phases.items():
        target=targets[leg]
        lower=leg+'_lower' if species=='cow' else 'foot_'+leg[-1]
        errors=[]
        contacts={}
        z_min_delta=100
        for frame in range(1,FRAMES+1):
            scene.frame_set(frame)
            bpy.context.view_layer.update()
            p=((frame-1)/CYCLE+phase)%1
            # Use floor cycle index so discontinuity at adjacent cycles is not hidden.
            cycle=math.floor((frame-1)/CYCLE+phase)
            tip=arm.matrix_world @ arm.pose.bones[lower].tail
            errors.append((tip-target.location).length)
            if p<DUTY:
                contacts.setdefault(cycle,[]).append(tip.copy())
            z_min_delta=min(z_min_delta,tip.z-original[leg].z)
        drift=max((max(v.x for v in contact)-min(v.x for v in contact)) for contact in contacts.values())
        results[species]['legs'][leg]={
            'max_ik_error_m':round(max(errors),6),
            'max_stance_foot_world_x_drift_m':round(drift,6),
            'minimum_tip_z_vs_reference_m':round(z_min_delta,6),
            'stance_group_count':len(contacts),
        }

scene.frame_set(1)
blend=os.path.join(out,'f07_v5_traveling_gait_noncanonical.blend')
bpy.ops.wm.save_as_mainfile(filepath=blend)
report={'identity':'NONCANONICAL_CALIBRATION_ONLY','frame_count':FRAMES,'cycle_frames':CYCLE,
        'stance_duty':DUTY,'root_speed_m_per_frame':ROOT_SPEED,'results':results,
        'limitations':['root speed is an unapproved study','no locomotion direction blending',
                       'physical hoof/toe surface contact not measured','W05/W07/F12 timing not approved']}
with open(os.path.join(out,'travel_qa.json'),'w') as f:json.dump(report,f,indent=2)
print('F07_TRAVEL_QA',json.dumps(report))
