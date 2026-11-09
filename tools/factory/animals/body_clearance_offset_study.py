"""Explore global bird shell clearance on an existing noncanonical slope fixture.

Diagnostic only. The merged lower-leg shell is not production anatomy.
"""
import bpy
import json
import os
import sys

out=os.path.abspath(sys.argv[sys.argv.index('--')+1])
offset=float(sys.argv[sys.argv.index('--')+2])
os.makedirs(out,exist_ok=True)
body=bpy.data.objects['Chicken_CAL_NOT_CANONICAL']
body.location.z+=offset
bpy.context.scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out,'f07_v9_slope_offset_study.blend'))
report={'status':'NONCANONICAL_FIXTURE_ONLY','chicken_body_shell_offset_m':offset,
        'foot_accessories_unchanged':True,'needs_visual_qa':True}
with open(os.path.join(out,'offset_study.json'),'w') as f:json.dump(report,f,indent=2)
print('F07_BODY_OFFSET',json.dumps(report))
