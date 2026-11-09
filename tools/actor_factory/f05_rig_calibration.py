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
sys.path.insert(0, str(Path(__file__).resolve().parent))
from f05_geometry import loft_chain, leg_sections, arm_sections, sleeve_sections, torso_sections, collar_sections
from f05_gait import gait_pose, torso_pose, LOCOMOTION
from f05_face_variants import build_face, HAIR_STYLES

parser = argparse.ArgumentParser()
parser.add_argument('--output', required=True)
parser.add_argument('--physique', choices=('lean', 'broad'), default='lean', help='Noncanonical body-width calibration variant')
parser.add_argument('--head-style', choices=HAIR_STYLES, default='short_sidepart', help='Original rig-compatible hairstyle silhouette')
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
hair = material('F05 test hair', (.19, .125, .079))
hair_shade = material('F05 original hair depth', (.135, .085, .050))
face_sclera = material('F05 soft nonwhite sclera', (.70, .65, .55), .63)
face_iris = material('F05 original eye iris', (.18, .22, .20), .62)
face_lip = material('F05 natural lip variation', (.45, .255, .215))
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

loft_chain('torso skin', torso_sections(body_width), 'chest', 'spine', skin)
ellipsoid('underwear actual geometry', (0,0,.96),(.21*body_width,.155*body_width,.14),'pelvis',underwear)
ellipsoid('head', (0,-.015,1.64),(.119,.111,.149),'head',skin)
ellipsoid('hair cap test', (0,.012,1.76),(.121,.113,.054),'head',hair)
face_source_meshes = build_face(ellipsoid, skin, hair, hair_shade, face_sclera,
                                face_iris, face_lip, args.head_style)
for side, sign in [('L',1),('R',-1)]:
    loft_chain('arm_skin_'+side, arm_sections(sign, limb_width),
               'upper_arm_'+side, 'forearm_'+side, skin)
    loft_chain('leg_skin_'+side, leg_sections(sign, 1.0, limb_width),
               'thigh_'+side, 'shin_'+side, skin)
    ellipsoid('hand '+side,(sign*.37,0,.88),
              (.052*limb_width,.045*limb_width,.079),'hand_'+side,skin)
    ellipsoid('foot '+side,(sign*.12,-.105,.08),
              (.087*limb_width,.145,.08),'foot_'+side,underwear)

# Separate outer garments: fit envelopes scale with the selected physique.
# Geometry remains rigid-weighted; shoulder/elbow deformation QA is not yet approved.
loft_chain('wearable_shirt_body', torso_sections(body_width, garment=True),
           'chest', 'spine', shirt)
loft_chain('wearable_shirt_collar', collar_sections(body_width),
           'neck', 'chest', seam)
for side, sign in [('L',1),('R',-1)]:
    loft_chain('wearable_shirt_sleeve_'+side, sleeve_sections(sign, limb_width),
               'upper_arm_'+side, 'forearm_'+side, shirt)
    loft_chain('wearable_pants_'+side,
               leg_sections(sign, 1.0, limb_width, garment=True),
               'thigh_'+side, 'shin_'+side, fabric)
# Contrasting belt visually distinguishes torso and pelvis in 2.5D preview.
ellipsoid('wearable_waist_band', (0,0,1.035),
          (.210*body_width,.161*body_width,.022),'pelvis',seam)

# Explicitly noncanonical calibration props; imported from no outside source.
ellipsoid('backpack test', (0,.19,1.31),(.19*body_width,.12,.27),'chest',fabric)
limb('held tool proxy',(-.37,0,.83),(-.37,0,1.23),.021,'hand_R',steel)

# Socket empties are attached to named bones, not silently baked into sprites.
sockets = {'floor_feet':('root',(0,0,0)), 'hand_R':('hand_R',(-.37,0,.89)),
           'hand_L':('hand_L',(.37,0,.89)), 'backpack':('chest',(0,.18,1.30)),
           'headwear':('head',(0,0,1.78)), 'waist':('pelvis',(0,0,.96)),
           'holster':('pelvis',(.2,0,.95)), 'held_item_tip':('hand_R',(-.37,0,1.23)),
           'attack_contact':('hand_R',(-.37,0,1.23)), 'depth_sort':('root',(0,0,.9))}
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
        phase = frame / frames
        for side, sign in [('L', 1), ('R', -1)]:
            if clip not in LOCOMOTION:
                continue
            p = gait_pose(clip, phase, sign)
            for bone_name, euler in (
                ('thigh_'+side, (p["hip_x"], 0, 0)),
                ('shin_'+side, (p["knee_x"], 0, 0)),
                ('foot_'+side, (p["ankle_x"], 0, 0)),
                ('shoulder_'+side, (p["shoulder_x"], 0, p["shoulder_z"])),
                ('upper_arm_'+side, (p["arm_x"], 0, 0)),
                ('forearm_'+side, (p["elbow_x"], 0, 0)),
            ):
                pose_bone = rig.pose.bones[bone_name]
                pose_bone.rotation_mode = 'XYZ'
                pose_bone.rotation_euler = euler
                pose_bone.keyframe_insert(data_path='rotation_euler', frame=frame+1)

    # Preserve explicit, provisional gesture poses for non-locomotion clips;
    # locomotion adds opposed pelvic/thoracic yaw and neck stabilization.
    amplitudes = {'idle': .015, 'walk': .025, 'run': .055,
                  'sneak': -.10, 'interact': .20, 'attack': .40,
                  'hurt': -.25, 'death': -1.10}
    chest = rig.pose.bones['chest']
    head = rig.pose.bones['head']
    pelvis = rig.pose.bones['pelvis']
    neck = rig.pose.bones['neck']
    for bone in (chest, head, pelvis, neck):
        bone.rotation_mode = 'XYZ'
    for frame in range(frames):
        phase = frame / frames
        wave = math.sin(2 * math.pi * phase)
        if clip in LOCOMOTION:
            p = torso_pose(clip, phase)
            chest.rotation_euler = (p["chest_x"], 0, p["chest_z"])
            pelvis.rotation_euler = (0, p["pelvis_y"], p["pelvis_z"])
            neck.rotation_euler = (p["neck_x"], 0, p["neck_z"])
            head.rotation_euler = (p["head_x"], 0, 0)
            for bone in (pelvis, neck):
                bone.keyframe_insert(data_path='rotation_euler', frame=frame+1)
        else:
            gesture_progress = frame / max(1, frames - 1)
            chest.rotation_euler = (
                amplitudes[clip] * (gesture_progress if clip in ('death', 'hurt', 'attack', 'interact') else wave),
                0, 0)
            head.rotation_euler = ((.08 if clip == 'hurt' else .02) * wave, 0, 0)
        chest.keyframe_insert(data_path='rotation_euler', frame=frame+1)
        head.keyframe_insert(data_path='rotation_euler', frame=frame+1)
    action.use_fake_user=True

# Per-frame floor-contact solution in locomotion calibration clips. The
# lowest evaluated foot sole targets ~12 mm above Z=0 before NLA interpolation; the exhaustive\n# frame-and-half-frame QA independently limits rendered hover and penetration.
# This is a root-height-only calibration, not real planted-foot IK.
for clip in ('idle', 'walk', 'run', 'sneak'):
    rig.animation_data.action = bpy.data.actions['F05_CAL_' + clip]
    root = rig.pose.bones['root']
    root.rotation_mode = 'XYZ'
    root.location = (0,0,0)
    for frame in range(1, clips[clip][0] + 1):
        bpy.context.scene.frame_set(frame)
        root.location = (0,0,0)
        bpy.context.view_layer.update()
        depsgraph = bpy.context.evaluated_depsgraph_get()
        floor = 1e8
        for side in ('L','R'):
            foot = bpy.data.objects['foot '+side].evaluated_get(depsgraph)
            mesh = foot.to_mesh()
            try:
                matrix = foot.matrix_world
                floor = min(floor, *( (matrix @ vert.co).z for vert in mesh.vertices ))
            finally:
                foot.to_mesh_clear()
        root.location = (0,0, max(-.05, min(.30, .012 - floor)))
        root.keyframe_insert(data_path='location',frame=frame)
    root.location = (0,0,0)

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

# Align the finished NLA-evaluated character to the ground, not merely
# the source Action's pose. This calibrates the same evaluated foot geometry
# used by exhaustive F05 joint QA, including half-frame interpolation.
rig.location.z = 0.0
lowest_raw_sole = float('inf')
highest_raw_sole = float('-inf')
for contact_clip in ('idle', 'walk', 'run', 'sneak'):
    for track in rig.animation_data.nla_tracks:
        track.mute = track.name != 'F05_CAL_' + contact_clip
    sample_points = [(f, 0.0) for f in range(1, clips[contact_clip][0] + 1)]
    sample_points += [(f, .5) for f in range(1, clips[contact_clip][0])]
    for frame, subframe in sample_points:
        bpy.context.scene.frame_set(frame, subframe=subframe)
        graph = bpy.context.evaluated_depsgraph_get()
        floor = float('inf')
        for side in ('L', 'R'):
            evaluated = bpy.data.objects['foot '+side].evaluated_get(graph)
            mesh = evaluated.to_mesh()
            try:
                floor = min(floor, *( (evaluated.matrix_world @ v.co).z for v in mesh.vertices ))
            finally:
                evaluated.to_mesh_clear()
        lowest_raw_sole = min(lowest_raw_sole, floor)
        highest_raw_sole = max(highest_raw_sole, floor)
floor_origin_adjustment = max(0.0, .001 - lowest_raw_sole)
if highest_raw_sole + floor_origin_adjustment > .025:
    raise RuntimeError('F05 floor pose range exceeds 25mm contact window: ' +
                       repr((lowest_raw_sole, highest_raw_sole)))
rig.location.z = floor_origin_adjustment
for track in rig.animation_data.nla_tracks:
    track.mute = track.name != 'F05_CAL_idle'
bpy.context.scene.frame_set(1, subframe=0.0)
print('F05_NLA_FLOOR_ALIGNMENT', 'raw_min', round(lowest_raw_sole,5),
      'raw_max', round(highest_raw_sole,5),
      'rig_shift', round(floor_origin_adjustment,5))

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
manifest={'status':'CALIBRATION_ONLY','physique':args.physique,'original_face_style':args.head_style,'original_face_meshes':face_source_meshes,'face_mesh_count':len(face_source_meshes),'body_width_factor':body_width,'limb_width_factor':limb_width,'canonical_master_id':None,'rig_version':'F05_CAL_0.8','proportion_profile':'F05_ADULT_CALIBRATION_V1','gait_contract':'F05_COUNTERROTATION_V1','wearable_layers':['shirt_body','shirt_sleeves','shirt_collar','pants_loft','waist_band'],'continuous_limb_shells':True,'floor_contact':'ROOT_HEIGHT_CALIBRATION','nla_floor_shift_m':round(floor_origin_adjustment,6),
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
