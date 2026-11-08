"""Noncanonical F06 visual calibration using an existing F05 .blend armature.

blender -b --factory-startup --python tools/factory/zombies/f06_calibrate.py -- \
  --f05-blend /path/to/f05_noncanonical_calibration.blend --output /path/to/output
No canonical asset identity or production rig approval is implied.
"""
import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

# The host injects a Python runtime that omits _ctypes; use Blender-compatible
# system Python extension modules when available for the glTF exporter.
system_dynload = '/usr/lib/python3.12/lib-dynload'
if system_dynload not in sys.path:
    sys.path.insert(0, system_dynload)
system_packages = '/opt/codex/runtimes/codex-primary-runtime/dependencies/python/lib/python3.12/site-packages'
if system_packages not in sys.path:
    sys.path.append(system_packages)

import bpy
from mathutils import Vector

p = argparse.ArgumentParser()
p.add_argument('--f05-blend', required=True)
p.add_argument('--output', required=True)
a = p.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
out = Path(a.output).resolve()
out.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(Path(a.f05_blend).resolve()))
rig = bpy.data.objects.get('F05_TEST_RIG')
required = {'root','pelvis','spine','chest','neck','head','upper_arm_L','upper_arm_R',
            'forearm_L','forearm_R','thigh_L','thigh_R','shin_L','shin_R','foot_L','foot_R'}
assert rig and rig.type == 'ARMATURE', 'F05 calibration rig missing'
assert required <= set(rig.pose.bones.keys()), 'Incompatible F05 bone revision'

# Remove F05's temporary wearable/tool proxies, preserving body and rig.
for obj in list(bpy.data.objects):
    if obj.name in {'backpack test', 'held tool proxy'}:
        bpy.data.objects.remove(obj, do_unlink=True)

skin = bpy.data.materials.get('F05 test skin')
skin.name = 'F06 pallid damaged skin - CAL_ONLY'
skin.diffuse_color = (.37,.38,.31,1)
skin.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (.37,.38,.31,1)
fabric = bpy.data.materials.new('F06 soiled civilian fabric - CAL_ONLY')
fabric.diffuse_color = (.24,.25,.22,1)
fabric.use_nodes = True
fabric.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (.24,.25,.22,1)
fabric.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = .91
for obj in bpy.data.objects:
    if obj.type == 'MESH' and obj.name.startswith('underwear'):
        obj.data.materials.clear()
        obj.data.materials.append(fabric)

# F05_CAL_0.1 is a provisional calibration bone layout, not an approved shared rig.
# One pose library is reused for all proposed appearances; no unique masters minted.
clips = {'idle':(4,180), 'shamble':(8,155), 'fast_shamble':(8,90),
         'investigate':(4,160), 'attack':(6,95), 'stagger':(4,105),
         'knockdown':(7,110), 'get_up':(7,130), 'crawl':(8,145),
         'crawl_attack':(6,95), 'death':(7,135), 'corpse':(1,1000)}
for clip,(count,ms) in clips.items():
    act = bpy.data.actions.new('F06_CAL_' + clip)
    rig.animation_data_create()
    rig.animation_data.action = act
    act.use_fake_user = True
    for i in range(count):
        phase = 2 * math.pi * i/count
        locomotion = clip in {'shamble','fast_shamble','crawl'}
        prone = clip in {'crawl','crawl_attack','corpse'}
        falling = clip in {'knockdown','death'}
        rising = clip == 'get_up'
        decline = i/max(1,count-1)
        pitch = (1.1 if prone else (1.1*decline if falling else (1.1*(1-decline) if rising else .22)))
        for name, rot in {
            'spine':(pitch,0,.10), 'head':(-.18 if not prone else .2,0,.10),
            'upper_arm_L':(-.4 + (.45*math.sin(phase) if locomotion else 0),0,.05),
            'upper_arm_R':(-.55 - (.32*math.sin(phase) if locomotion else 0),0,-.05),
            'thigh_L':((.32 if clip=='fast_shamble' else .19)*math.sin(phase) if locomotion else 0,0,0),
            'thigh_R':(-(.24 if clip=='fast_shamble' else .14)*math.sin(phase) if locomotion else 0,0,0),
        }.items():
            bone = rig.pose.bones[name]
            bone.rotation_mode='XYZ'
            bone.rotation_euler=rot
            bone.keyframe_insert(data_path='rotation_euler', frame=i+1)
        # Attack contact pose is exactly the third 95ms frame in W03's draft.
        if clip in {'attack','crawl_attack'}:
            arm = rig.pose.bones['upper_arm_R']
            arm.rotation_euler.x = -.65 - (1.0 if i==2 else .25)
            arm.keyframe_insert(data_path='rotation_euler',frame=i+1)
    if clip == 'corpse':
        act.use_fake_user = True

scene=bpy.context.scene
scene.render.engine='BLENDER_EEVEE'
scene.render.film_transparent=True
scene.render.resolution_x=256
scene.render.resolution_y=256
scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.render.image_settings.color_mode='RGBA'
scene.camera.data.type='ORTHO'
scene.camera.data.ortho_scale=2.75
rendered=[]
for clip,frames in [('idle',[1]),('shamble',[1,3,5,7]),('attack',[1,3,6]),
                    ('stagger',[1,3]),('crawl',[1,3,5]),('death',[1,4,7]),('corpse',[1])]:
    rig.animation_data.action=bpy.data.actions['F06_CAL_'+clip]
    for frame in frames:
        scene.frame_set(frame)
        name=f'{clip}_{frame:02d}.png'
        scene.render.filepath=str(out/name)
        bpy.ops.render.render(write_still=True)
        rendered.append(name)
rig.animation_data.action=bpy.data.actions['F06_CAL_idle']
bpy.ops.wm.save_as_mainfile(filepath=str(out/'f06_noncanonical_calibration.blend'))
bpy.ops.object.select_all(action='DESELECT')
rig.select_set(True)
for obj in bpy.data.objects:
    if obj.type=='MESH' or obj.name.startswith('socket_'): obj.select_set(True)
bpy.context.view_layer.objects.active=rig
glb_error=None
try:
    bpy.ops.export_scene.gltf(filepath=str(out/'f06_noncanonical_calibration.glb'),
                              export_format='GLB',use_selection=True)
except Exception as e:
    glb_error=str(e)
manifest={
    'status':'CALIBRATION_ONLY','canonical_master_id':None,'source_rig':'F05_CAL_0.1',
    'rig_approved':False,'w03_pr_head':'67d9f55222e43610cc820b55448deb1df2c34bdd',
    'projection':'PROVISIONAL_F05_CAMERA_NOT_F12_APPROVED',
    'clips':{k:{'frames':v[0],'ms_per_frame':v[1]} for k,v in clips.items()},
    'events':{'attack':[{'type':'attack_contact','frame_1_based':3,'time_ms':285,
                          'authority':'W03_ONE_HIT_ONLY'}]},
    'state_mapping_proposal':{'wander':'shamble','investigate':'shamble',
                              'pursue':'fast_shamble','attack':'attack',
                              'stagger':'stagger','knockdown':'knockdown',
                              'getup':'get_up','crawl':'crawl','death':'death','corpse':'corpse'},
    'qa':{'rig_required_bones':'PASS','glb_export':'FAIL' if glb_error else 'PASS',
          'glb_error':glb_error,'foot_lock':'NOT_RUN','garment_clipping':'NOT_RUN',
          'directional_f12':'NOT_RUN','w03_integration':'NOT_RUN','founder_visual':'NOT_APPROVED',
          'iphone':'NOT_RUN'},'rendered_frames':rendered,
}
for file in sorted(out.iterdir()):
    if file.is_file(): manifest.setdefault('sha256',{})[file.name]=hashlib.sha256(file.read_bytes()).hexdigest()
(out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('F06_CALIBRATION_COMPLETE',out)
