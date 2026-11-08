"""F07 NONCANONICAL geometry/rig/render calibration. Blender 4.0+.

Run: blender -b --factory-startup --python tools/factory/animals/calibrate.py -- OUT_DIR
Not a canonical asset work order; not a replacement for the missing V8 cow.
"""
import bpy
import math
import os
import sys
import json
import hashlib
from mathutils import Vector

OUT = os.path.abspath(sys.argv[sys.argv.index('--') + 1]) if '--' in sys.argv else '/tmp/f07-calibration'
only_species = sys.argv[sys.argv.index('--only')+1] if '--only' in sys.argv else None
os.makedirs(OUT, exist_ok=True)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

def material(name, color, roughness=0.84):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (*color, 1)
    bsdf.inputs['Roughness'].default_value = roughness
    return m

def patterned_material(name, primary, secondary, scale, threshold, roughness):
    """Original seeded 3D procedural hide/feather color; no external textures."""
    mat=material(name,primary,roughness)
    nt=mat.node_tree
    shader=nt.nodes.get('Principled BSDF')
    noise=nt.nodes.new('ShaderNodeTexNoise')
    noise.inputs['Scale'].default_value=scale
    noise.inputs['Detail'].default_value=3.2
    noise.inputs['Roughness'].default_value=.63
    mapping=nt.nodes.new('ShaderNodeTexCoord')
    nt.links.new(mapping.outputs['Generated'],noise.inputs['Vector'])
    ramp=nt.nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].position=max(0,threshold-.065)
    ramp.color_ramp.elements[0].color=(*secondary,1)
    ramp.color_ramp.elements[1].position=min(1,threshold+.065)
    ramp.color_ramp.elements[1].color=(*primary,1)
    nt.links.new(noise.outputs['Fac'],ramp.inputs['Fac'])
    nt.links.new(ramp.outputs['Color'],shader.inputs['Base Color'])
    return mat

def ellipsoid(name, pos, radii, mat):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=20, ring_count=12, location=pos)
    o = bpy.context.object
    o.name = name
    o.scale = radii
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.data.materials.append(mat)
    return o

def shell(name, lobes, mat):
    """Weld intersecting organic volumes into one continuous voxel shell."""
    parts=[]
    for x, y, z, rx, ry, rz in lobes:
        parts.append(ellipsoid(name+'_volume', (x,y,z), (rx,ry,rz),mat))
    bpy.ops.object.select_all(action='DESELECT')
    for part in parts:
        part.select_set(True)
    bpy.context.view_layer.objects.active=parts[0]
    bpy.ops.object.join()
    obj=bpy.context.object
    remesh=obj.modifiers.new('ContinuousShell','REMESH')
    remesh.mode='VOXEL'
    remesh.voxel_size=0.055 if name.startswith('Cow') else 0.025
    bpy.ops.object.modifier_apply(modifier=remesh.name)
    smooth=obj.modifiers.new('OrganicSurface','SMOOTH')
    smooth.factor=1.2
    smooth.iterations=3
    bpy.ops.object.modifier_apply(modifier=smooth.name)
    obj.name = name
    obj.data.materials.append(mat)
    # Generated source UVs are calibration only; final coats need reviewed UVs.
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(island_margin=0.02)
    bpy.ops.object.mode_set(mode='OBJECT')
    return obj

def rig(name, bones):
    arm = bpy.data.armatures.new(name + '_data')
    obj = bpy.data.objects.new(name, arm)
    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    for bone_name, head, tail, parent in bones:
        b = arm.edit_bones.new(bone_name)
        b.head, b.tail = head, tail
        if parent:
            b.parent = arm.edit_bones[parent]
            b.use_connect = False
    bpy.ops.object.mode_set(mode='OBJECT')
    return obj

def skin(mesh, arm):
    # Closest-segment blend is a deterministic calibration weighting scheme.
    pairs = []
    for bone in arm.data.bones:
        group = mesh.vertex_groups.new(name=bone.name)
        pairs.append((bone, group))
    for v in mesh.data.vertices:
        weights = []
        for bone, group in pairs:
            a, b = bone.head_local, bone.tail_local
            ab = b - a
            t = min(1.0, max(0.0, (v.co - a).dot(ab) / max(ab.length_squared, 1e-9)))
            dist = (v.co - (a + t * ab)).length
            weights.append((group, 1 / max(dist, 0.06)**5))
        weights.sort(key=lambda p: p[1], reverse=True)
        top = weights[:3]
        total = sum(w for _, w in top)
        for group, weight in top:
            group.add([v.index], weight / total, 'REPLACE')
    modifier = mesh.modifiers.new('ArmatureSkin', 'ARMATURE')
    modifier.object = arm
    mesh.parent = arm

def animate(arm, legs, is_bird):
    for clip, amplitude, frames in [('idle', 0.045, 12), ('walk', 0.25, 12)]:
        action = bpy.data.actions.new(arm.name + '_' + clip)
        arm.animation_data_create()
        arm.animation_data.action = action
        for frame in range(1, frames + 1):
            phase = 2 * math.pi * (frame - 1) / frames
            for i, name in enumerate(legs):
                pb = arm.pose.bones[name]
                pb.rotation_mode = 'XYZ'
                offset = i * math.pi if is_bird else (0, math.pi, math.pi, 0)[i]
                pb.rotation_euler[1] = amplitude * math.sin(phase + offset)
                pb.keyframe_insert(data_path='rotation_euler', frame=frame, group=name)
        action.use_fake_user = True
    arm.animation_data.action = bpy.data.actions[arm.name + '_idle']

hide = patterned_material('Original warm dairy cattle coat CAL',(.68,.60,.48),(.15,.105,.078),3.2,.49,.82)
feather = patterned_material('Original buff feather mass CAL',(.72,.66,.53),(.50,.41,.30),16,.30,.89)
dark = material('Hoof and eye', (0.085, 0.074, 0.062))
red = material('Comb red', (0.47, 0.08, 0.057))
beak = material('Beak ochre', (0.66, 0.43, 0.12))
horn = material('Horn bone',(.65,.60,.48))
udder_mat=material('Udder skin',(.54,.34,.29))

# X = forward, Y = sideways, Z = up. Legs are merged into continuous shell.
cow_lobes = [(-.10,0,1.18,1.08,.42,.46),(.68,0,1.28,.43,.43,.46),
             (.99,0,1.39,.33,.25,.38),(1.26,0,1.40,.34,.25,.24)]
for x in (-.76,.63):
    for y in (-.29,.29):
        cow_lobes += [(x,y,.78,.18,.16,.48),(x,y,.39,.115,.115,.36)]
cow = shell('Cow_CAL_NOT_CANONICAL', cow_lobes, hide)
for x in (-.76,.63):
    for y in (-.29,.29):
        for split in (-.055,.055):
            ellipsoid('SplitClovenHoof', (x+.045,y+split,.085),(.155,.067,.085), dark)
for y in (-.22,.22):
    ellipsoid('Eye', (1.42,y,1.47),(.045,.034,.04),dark)
    ellipsoid('CattleEar', (1.10,y*1.55,1.59),(.22,.12,.08),hide)
    ellipsoid('Horn',(1.13,y*1.15,1.73),(.075,.07,.16),horn)
ellipsoid('CattleMuzzle',(1.53,0,1.29),(.21,.22,.15),hide)
ellipsoid('CattleTail',(-1.2,0,.90),(.33,.065,.07),hide)
ellipsoid('CattleUdder',(-.37,0,.78),(.26,.20,.15),udder_mat)
cow_bones = [('root',(0,0,1.10),(0,0,1.38),None),('spine',(-.75,0,1.25),(.63,0,1.31),'root'),('neck',(.63,0,1.31),(1.08,0,1.43),'spine'),('head',(1.08,0,1.43),(1.51,0,1.40),'neck')]
cow_legs=[]
for side, y in [('L',.28),('R',-.28)]:
    for end,x in [('front',.63),('hind',-.76)]:
        n=end+'_'+side
        cow_bones += [(n,(x,y,1.07),(x,y,.49),'root'),(n+'_lower',(x,y,.49),(x,y,.085),n)]
        cow_legs.append(n)
cow_arm=rig('CowRig_CAL',cow_bones)
skin(cow,cow_arm)
animate(cow_arm,cow_legs,False)
cow_parts=set(bpy.context.scene.objects)

bird_lobes = [(3,0,.49,.40,.28,.30),(3.27,0,.65,.17,.16,.22),(3.40,0,.81,.13,.12,.14)]
for y in (-.16,.16):
    bird_lobes += [(2.97,y,.44,.21,.10,.16),(3.02,y,.20,.05,.05,.22)]
bird=shell('Chicken_CAL_NOT_CANONICAL',bird_lobes,feather)
ellipsoid('Beak',(3.53,0,.75),(.13,.09,.065),beak)
for x,z,radius in [(3.28,.94,.075),(3.38,1.01,.082),(3.47,.94,.07)]:
    ellipsoid('ScallopedComb',(x,0,z),(radius,.044,radius*1.20),red)
for offset,y in enumerate((-.13,0,.13)):
    ellipsoid('TailFeather',(2.65,y,.66+offset*.075),(.19,.075,.13),feather)
for y in (-.17,.17):
    ellipsoid('ChickenEye',(3.43,y*.78,.84),(.025,.025,.025),dark)
    for toe_y in (-.055,0,.055):
        ellipsoid('ChickenToe',(3.115,y+toe_y,.045),(.125,.025,.027),beak)
    ellipsoid('WingFeather',(2.94,y*1.4,.49),(.21,.075,.14),feather)
bird_bones=[('root',(3,0,.4),(3,0,.57),None),('body',(2.75,0,.48),(3.26,0,.48),'root'),('neck',(3.26,0,.55),(3.40,0,.80),'body'),('head',(3.40,0,.80),(3.49,0,.85),'neck'),('wing_L',(2.95,.08,.52),(3.05,.25,.39),'body'),('wing_R',(2.95,-.08,.52),(3.05,-.25,.39),'body')]
for s,y in [('L',.16),('R',-.16)]:
    bird_bones += [('leg_'+s,(3,y,.4),(3,y,.12),'root'),('foot_'+s,(3,y,.12),(3.12,y,.055),'leg_'+s)]
bird_arm=rig('BirdRig_CAL',bird_bones)
skin(bird,bird_arm)
animate(bird_arm,['leg_L','leg_R'],True)
bird_parts=set(bpy.context.scene.objects)-cow_parts

world = bpy.context.scene.world
world.color = (.20,.20,.20)
bpy.ops.object.light_add(type='AREA',location=(-3,-4,7))
bpy.context.object.data.energy=850
bpy.context.object.data.shape='DISK'
bpy.context.object.data.size=4

def render(name,target,center,scale,heading,pose):
    theta=heading*math.pi/4
    bpy.ops.object.camera_add(location=(center.x+6*math.cos(theta),center.y+6*math.sin(theta),center.z+5))
    cam=bpy.context.object
    direction=center-cam.location
    cam.rotation_euler=direction.to_track_quat('-Z','Y').to_euler()
    cam.data.type='ORTHO'
    cam.data.ortho_scale=scale
    bpy.context.scene.camera=cam
    scene=bpy.context.scene
    scene.render.engine='BLENDER_EEVEE'
    scene.render.resolution_x=256
    scene.render.resolution_y=256
    scene.render.resolution_percentage=100
    scene.render.film_transparent=True
    scene.render.image_settings.file_format='PNG'
    scene.render.filepath=os.path.join(OUT,'frames',f'{name}_{heading:02d}_{pose}.png')
    # Hide opposite calibration model and its accessories by spatial grouping.
    for ob in bpy.context.scene.objects:
        if ob.type in {'MESH','ARMATURE'}:
            ob.hide_render = ob not in (cow_parts if name=='cow' else bird_parts)
    bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(cam,do_unlink=True)

scene=bpy.context.scene
scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'f07_noncanonical_calibration.blend'))
os.makedirs(os.path.join(OUT,'frames'),exist_ok=True)
for species,mesh,center,scale,arm in [('cow',cow,Vector((.13,0,.98)),4.35,cow_arm),('chicken',bird,Vector((3,0,.45)),1.65,bird_arm)]:
    if only_species and species != only_species:
        continue
    for heading in range(8):
        for pose,frame in [('idle',1),('walk_a',4),('walk_b',10)]:
            arm.animation_data.action=bpy.data.actions[arm.name+('_idle' if pose=='idle' else '_walk')]
            scene.frame_set(frame)
            render(species,mesh,center,scale,heading,pose)

report={'identity':'NONCANONICAL_CALIBRATION_ONLY','blender':bpy.app.version_string,'meshes':{},'rigs':{},'outputs':{}}
for ob in (cow,bird):
    report['meshes'][ob.name]={'vertices':len(ob.data.vertices),'faces':len(ob.data.polygons),'uv_layers':len(ob.data.uv_layers),'weight_groups':len(ob.vertex_groups)}
for ob in (cow_arm,bird_arm):
    report['rigs'][ob.name]={'bones':len(ob.data.bones),'actions':[a.name for a in bpy.data.actions if a.name.startswith(ob.name)]}
for filename in ['f07_noncanonical_calibration.blend']:
    path=os.path.join(OUT,filename)
    report['outputs'][filename]={'bytes':os.path.getsize(path),'sha256':hashlib.sha256(open(path,'rb').read()).hexdigest()}
report['frames']={}
for filename in sorted(os.listdir(os.path.join(OUT,'frames'))):
    path=os.path.join(OUT,'frames',filename)
    report['frames'][filename]={'bytes':os.path.getsize(path),'sha256':hashlib.sha256(open(path,'rb').read()).hexdigest()}
report['checks']={
    'eight_headings_per_species':all(sum(n.startswith(s+'_') for n in report['frames'])==24 for s in ('cow','chicken')),
    'different_rig_anatomy':len(cow_arm.data.bones)!=len(bird_arm.data.bones),
    'has_uv_and_weights':all(len(o.data.uv_layers)>0 and len(o.vertex_groups)>0 for o in (cow,bird)),
    'walk_legs_out_of_phase_design_only':True, # no IK / stance quality assertion
    'foot_sliding_qa':'NOT_RUN',
    'aesthetic_approval':'NOT_APPROVED',
}
with open(os.path.join(OUT,'qa.json'),'w') as f:
    json.dump(report,f,indent=2)
print('F07_CALIBRATION_REPORT',json.dumps(report))
