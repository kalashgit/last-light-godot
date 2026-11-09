"""F05 NONCANONICAL calibration: reproducible skinned humanoid, wearables and clips.

blender -b --factory-startup --python tools/actor_factory/f05_rig_calibration.py -- --output /tmp/f05-cal
No canonical asset IDs are assigned or implied by this script.
"""
import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector, Matrix

parser = argparse.ArgumentParser()
parser.add_argument('--output', required=True)
parser.add_argument('--physique', choices=('lean', 'broad'), default='lean', help='Noncanonical body-width calibration variant')
args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
out = Path(args.output).resolve()
out.mkdir(parents=True, exist_ok=True)
body_width = 1.0 if args.physique == 'lean' else 1.18
limb_width = 1.0 if args.physique == 'lean' else 1.12
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

def material(name, rgb, roughness=0.85):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*rgb, 1)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (*rgb, 1)
    bsdf.inputs['Roughness'].default_value = roughness
    return mat

skin = material('F05 test skin', (.53, .34, .24))
underwear = material('F05 test underwear', (.18, .20, .22))
fabric = material('F05 test canvas', (.16, .24, .20))
shirt = material('F05 test shirt cotton', (.28, .34, .39))
seam = material('F05 test seam', (.11, .14, .17))
hair = material('F05 test hair', (.14, .09, .06))
steel = material('F05 test tool', (.28, .32, .33), .43)

arm = bpy.data.armatures.new('F05 humanoid skeleton v0.1')
rig = bpy.data.objects.new('F05_TEST_RIG', arm)
bpy.context.collection.objects.link(rig)
bpy.context.view_layer.objects.active = rig
rig.select_set(True)
bpy.ops.object.mode_set(mode='EDIT')

specs = [
 ('root', None, (0,0,0), (0,0,.12)),
 ('pelvis','root',(0,0,.92),(0,0,1.05)),
 ('spine','pelvis',(0,0,1.05),(0,0,1.29)),
 ('chest','spine',(0,0,1.29),(0,0,1.47)),
 ('neck','chest',(0,0,1.47),(0,0,1.56)),
 ('head','neck',(0,0,1.56),(0,0,1.76)),
]
for side, sign in [('L',1),('R',-1)]:
    specs += [
      (f'shoulder_{side}','chest',(.15*sign,0,1.44),(.25*sign,0,1.43)),
      (f'upper_arm_{side}',f'shoulder_{side}',(.25*sign,0,1.43),(.34*sign,0,1.17)),
      (f'forearm_{side}',f'upper_arm_{side}',(.34*sign,0,1.17),(.37*sign,0,.94)),
      (f'hand_{side}',f'forearm_{side}',(.37*sign,0,.94),(.37*sign,0,.85)),
      (f'thigh_{side}','pelvis',(.115*sign,0,.92),(.12*sign,0,.55)),
      (f'shin_{side}',f'thigh_{side}',(.12*sign,0,.55),(.12*sign,0,.14)),
      (f'foot_{side}',f'shin_{side}',(.12*sign,0,.14),(.12*sign,-.15,.08)),
      (f'toe_{side}',f'foot_{side}',(.12*sign,-.15,.08),(.12*sign,-.23,.08)),
    ]
for name, parent, head_pos, tail_pos in specs:
    bone = arm.edit_bones.new(name)
    bone.head, bone.tail = head_pos, tail_pos
    if parent: bone.parent = arm.edit_bones[parent]
bpy.ops.object.mode_set(mode='OBJECT')
rig.select_set(False)

def ellipsoid(name, pos, scale, bone, mat):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=10, location=pos)
    ob = bpy.context.object
    ob.name = name
    ob.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    ob.data.materials.append(mat)
    group = ob.vertex_groups.new(name=bone)
    group.add(list(range(len(ob.data.vertices))), 1.0, 'REPLACE')
    ob.parent = rig
    modifier = ob.modifiers.new('F05 armature deformation', 'ARMATURE')
    modifier.object = rig
    return ob

def limb(name, a, b, radius, bone, mat):
    middle = (Vector(a)+Vector(b))/2
    o = ellipsoid(name, middle, (radius,radius,(Vector(b)-Vector(a)).length*.58),bone,mat)
    o.rotation_euler = (Vector(b)-Vector(a)).to_track_quat('Z','Y').to_euler()
    return o

ellipsoid('torso skin', (0,0,1.30),(.245*body_width,.145*body_width,.265),'chest',skin)
ellipsoid('underwear actual geometry', (0,0,.96),(.21*body_width,.155*body_width,.14),'pelvis',underwear)
ellipsoid('head', (0,-.015,1.64),(.125,.117,.16),'head',skin)
ellipsoid('hair cap test', (0,.012,1.76),(.127,.118,.065),'head',hair)
for side, sign in [('L',1),('R',-1)]:
    limb('upper arm '+side,(sign*.25,0,1.43),(sign*.34,0,1.17),.071*limb_width,'upper_arm_'+side,skin)
    limb('forearm '+side,(sign*.34,0,1.17),(sign*.37,0,.94),.055*limb_width,'forearm_'+side,skin)
    ellipsoid('hand '+side,(sign*.37,0,.88),(.057*limb_width,.048*limb_width,.087),'hand_'+side,skin)
    limb('thigh '+side,(sign*.115,0,.91),(sign*.12,0,.55),.102*limb_width,'thigh_'+side,skin)
    limb('shin '+side,(sign*.12,0,.55),(sign*.12,0,.14),.075*limb_width,'shin_'+side,skin)
    ellipsoid('foot '+side,(sign*.12,-.105,.08),(.09*limb_width,.17,.08),'foot_'+side,underwear)

# Separate outer garments: fit envelopes scale with the selected physique.
# Geometry remains rigid-weighted; shoulder/elbow deformation QA is not yet approved.
ellipsoid('wearable_shirt_body', (0,-.003,1.30),
          (.258*body_width,.158*body_width,.274),'chest',shirt)
for side, sign in [('L',1),('R',-1)]:
    limb('wearable_shirt_sleeve_'+side,
         (sign*.25,0,1.43),(sign*.29,0,1.31),
         .084*limb_width,'upper_arm_'+side,shirt)
    limb('wearable_pants_upper_'+side,
         (sign*.115,0,.91),(sign*.12,0,.55),
         .113*limb_width,'thigh_'+side,fabric)
    limb('wearable_pants_lower_'+side,
         (sign*.12,0,.55),(sign*.12,0,.14),
         .087*limb_width,'shin_'+side,fabric)
# Contrasting belt visually distinguishes torso and pelvis in 2.5D preview.
ellipsoid('wearable_waist_band', (0,0,1.035),
          (.218*body_width,.164*body_width,.025),'pelvis',seam)

# Explicitly noncanonical calibration props; imported from no outside source.
ellipsoid('backpack test', (0,.19,1.31),(.19*body_width,.12,.27),'chest',fabric)
limb('held tool proxy',(.37,0,.83),(.37,0,1.23),.021,'hand_R',steel)

# Socket empties are attached to named bones, not silently baked into sprites.
sockets = {'floor_feet':('root',(0,0,0)), 'hand_R':('hand_R',(.37,0,.89)),
           'hand_L':('hand_L',(-.37,0,.89)), 'backpack':('chest',(0,.18,1.30)),
           'headwear':('head',(0,0,1.78)), 'waist':('pelvis',(0,0,.96)),
           'holster':('pelvis',(.2,0,.95)), 'held_item_tip':('hand_R',(.37,0,1.23)),
           'attack_contact':('hand_R',(.37,0,1.23)), 'depth_sort':('root',(0,0,.9))}
for name,(bone,point) in sockets.items():
    ob=bpy.data.objects.new('socket_'+name,None)
    bpy.context.collection.objects.link(ob)
    ob.parent=rig
    ob.parent_type='BONE'
    ob.parent_bone=bone
    # Use a bone-local offset from the rest-pose head rather than treating
    # a world-space point as a bone-space location.
    rest = rig.data.bones[bone]
    ob.matrix_parent_inverse = Matrix.Identity(4)
    ob.location = rest.matrix_local.inverted() @ Vector(point)
    ob.empty_display_size=.035

clips={'idle':(4,180),'walk':(8,105),'run':(8,75),'sneak':(8,125),
       'interact':(6,110),'attack':(6,85),'hurt':(3,100),'death':(7,125)}
for clip,(frames,duration) in clips.items():
    action=bpy.data.actions.new('F05_CAL_'+clip)
    rig.animation_data_create()
    rig.animation_data.action=action
    for frame in range(frames):
        angle=2*math.pi*frame/frames
        for side,sign in [('L',1),('R',-1)]:
            upper=rig.pose.bones['thigh_'+side]
            upper.rotation_mode='XYZ'
            upper.rotation_euler=(math.sin(angle)*sign*(.27 if clip in ('walk','run','sneak') else 0),0,0)
            upper.keyframe_insert(data_path='rotation_euler',frame=frame+1)
            arm_bone=rig.pose.bones['upper_arm_'+side]
            arm_bone.rotation_mode='XYZ'
            arm_bone.rotation_euler=(-math.sin(angle)*sign*(.19 if clip in ('walk','run') else 0),0,0)
            arm_bone.keyframe_insert(data_path='rotation_euler',frame=frame+1)
    # Non-locomotion clips must not silently duplicate the idle animation.
    # These are procedural calibration poses, not approved W07 gameplay motions.
    amplitudes = {'idle': .015, 'walk': .025, 'run': .055,
                  'sneak': -.10, 'interact': .20, 'attack': .40,
                  'hurt': -.25, 'death': -1.10}
    chest = rig.pose.bones['chest']
    chest.rotation_mode = 'XYZ'
    head = rig.pose.bones['head']
    head.rotation_mode = 'XYZ'
    for frame in range(frames):
        phase = frame / max(1, frames - 1)
        wave = math.sin(2 * math.pi * phase)
        chest.rotation_euler = (
            amplitudes[clip] * (phase if clip in ('death', 'hurt', 'attack', 'interact') else wave),
            0, 0)
        head.rotation_euler = (
            (.08 if clip == 'hurt' else .02) * wave,
            0, 0)
        chest.keyframe_insert(data_path='rotation_euler', frame=frame + 1)
        head.keyframe_insert(data_path='rotation_euler', frame=frame + 1)
    action.use_fake_user=True

# Store every provisional action in a named NLA track. A fake-user action alone
# is not evidence that the glTF exporter will include it.
rig.animation_data.action = None
for clip, (frames, duration) in clips.items():
    track = rig.animation_data.nla_tracks.new()
    track.name = 'F05_CAL_' + clip
    strip = track.strips.new('F05_CAL_' + clip, 1, bpy.data.actions['F05_CAL_' + clip])
    strip.action_frame_start = 1
    strip.action_frame_end = frames
    strip.mute = False
    track.mute = False
# Keep only idle visible for the still render; NLA tracks remain available to export.
for track in rig.animation_data.nla_tracks:
    track.mute = track.name != 'F05_CAL_idle'

world=bpy.context.scene.world
world.color=(.15,.15,.15)
camera_data=bpy.data.cameras.new('F05 orthographic iso')
camera=bpy.data.objects.new('F05 orthographic iso',camera_data)
bpy.context.collection.objects.link(camera)
camera.location=(3,-3,3.0)
camera.rotation_euler=(Vector((0,0,.9))-camera.location).to_track_quat('-Z','Y').to_euler()
camera_data.type='ORTHO'
camera_data.ortho_scale=2.75
bpy.context.scene.camera=camera
light_data=bpy.data.lights.new('F05 upper-left key','AREA')
light=bpy.data.objects.new('F05 upper-left key',light_data)
bpy.context.collection.objects.link(light)
light.location=(-3,-4,6)
light_data.energy=550
light_data.shape='DISK'
light_data.size=4
bpy.context.scene.render.engine='BLENDER_EEVEE'
bpy.context.scene.render.resolution_x=256
bpy.context.scene.render.resolution_y=256
bpy.context.scene.render.resolution_percentage=100
bpy.context.scene.render.film_transparent=True
bpy.context.scene.render.image_settings.file_format='PNG'
bpy.context.scene.render.image_settings.color_mode='RGBA'
bpy.context.scene.render.filepath=str(out/'calibration.png')
bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str(out/'f05_noncanonical_calibration.blend'))
# Export all tracks, not just the idle track used for the preview.
for track in rig.animation_data.nla_tracks:
    track.mute = False
# Export explicitly excludes camera/lights; Blender GLB exporter includes skinned armature.
bpy.ops.object.select_all(action='DESELECT')
rig.select_set(True)
for ob in bpy.data.objects:
    if ob.type=='MESH' or ob.name.startswith('socket_'): ob.select_set(True)
bpy.context.view_layer.objects.active=rig
glb_error = None
try:
    bpy.ops.export_scene.gltf(filepath=str(out/'f05_noncanonical_calibration.glb'),export_format='GLB',use_selection=True,export_animations=True,export_nla_strips=True)
except Exception as exc:
    glb_error = str(exc)
manifest={'status':'CALIBRATION_ONLY','physique':args.physique,'body_width_factor':body_width,'limb_width_factor':limb_width,'canonical_master_id':None,'rig_version':'F05_CAL_0.2','wearable_layers':['shirt_body','shirt_sleeves','pants_upper','pants_lower','waist_band'],
          'blender_version':bpy.app.version_string,'bones':[v[0] for v in specs],
          'sockets':list(sockets),'clips':{k:{'frames':v[0],'ms_per_frame':v[1],
          'contract':'PROVISIONAL_W07_APPROVAL_REQUIRED'} for k,v in clips.items()},
          'qa':{'geometry':'NOT_INDEPENDENTLY_REVIEWED','glb_export': 'FAIL' if glb_error else 'PASS',
                'glb_error':glb_error,'clothing_clipping':'NOT_RUN',
                'foot_contact':'NOT_RUN','native_visual':'NOT_APPROVED',
                'godot_import':'NOT_RUN'}}
for name in ('calibration.png','f05_noncanonical_calibration.blend','f05_noncanonical_calibration.glb'):
    p=out/name
    if p.exists(): manifest.setdefault('sha256',{})[name]=hashlib.sha256(p.read_bytes()).hexdigest()
(out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('F05_CALIBRATION_COMPLETE',out)
if glb_error:
    print('F05_GLTF_EXPORT_FAILED', glb_error, file=sys.stderr)
    sys.exit(2)
