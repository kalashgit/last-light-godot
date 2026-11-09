"""Chicken rig root-height study with fixed world-space contact targets.

Noncanonical calibration only. Input is a previously grounded slope fixture.
"""
import bpy
import json
import os
import sys

out=os.path.abspath(sys.argv[sys.argv.index('--')+1])
raise_m=float(sys.argv[sys.argv.index('--')+2])
os.makedirs(out,exist_ok=True)
rig=bpy.data.objects['BirdRig_CAL']
scene=bpy.context.scene
for frame in range(1,34):
    scene.frame_set(frame)
    rig.location.z+=raise_m
    rig.keyframe_insert(data_path='location',frame=frame,group='F07BirdClearancePosture')
scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out,'f07_v9_bird_root_posture_noncanonical.blend'))
report={'status':'NONCANONICAL_CALIBRATION_ONLY','bird_rig_root_raise_m':raise_m,
        'IK_targets_modified':False,'requires_foot_and_body_reaudit':True}
with open(os.path.join(out,'posture_study.json'),'w') as f:json.dump(report,f,indent=2)
print('F07_BIRD_ROOT_STUDY',json.dumps(report))
