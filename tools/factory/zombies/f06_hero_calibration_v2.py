"""F06 V2 NONCANONICAL infected appearance and directional animation calibration.

Requires F05_CAL_0.1 .blend source. Never publishes A00 master IDs or gameplay.
Usage: blender -b --factory-startup --python tools/factory/zombies/f06_hero_calibration_v2.py --
       --f05-blend /path/to/f05_noncanonical_calibration.blend --output /tmp/f06-v2
"""
import argparse
import hashlib
import json
import math
import random
import sys
from pathlib import Path

for sys_path in ('/usr/lib/python3.12/lib-dynload',
                 '/opt/codex/runtimes/codex-primary-runtime/dependencies/python/lib/python3.12/site-packages'):
    if sys_path not in sys.path:
        sys.path.append(sys_path)

import bpy
from mathutils import Vector

parser = argparse.ArgumentParser()
parser.add_argument('--f05-blend', required=True)
parser.add_argument('--output', required=True)
parser.add_argument('--samples', type=int, default=24)
parser.add_argument('--directions', type=int, choices=(4,8), default=4)
parser.add_argument('--profiles', nargs='*', choices=('civilian','hospital_orderly','security','injured_crawler'))
parser.add_argument('--preview-only',action='store_true')
parser.add_argument('--validate-crops',action='store_true')
args = parser.parse_args(sys.argv[sys.argv.index('--')+1:])
out = Path(args.output).resolve()
out.mkdir(parents=True,exist_ok=True)

PROFILES = {
    'civilian': {'seed':104,'skin':(.42,.43,.35),'shirt':(.24,.30,.26), 'pants':(.20,.22,.22),
                 'trim':(.11,.13,.13), 'stance':.11,'stride':.23,'drag':.25, 'outfit':'jacket'},
    'hospital_orderly': {'seed':205,'skin':(.45,.43,.37),'shirt':(.45,.49,.44),'pants':(.32,.39,.37),
                 'trim':(.24,.33,.32),'stance':.10,'stride':.17,'drag':.12,'outfit':'scrubs'},
    'security': {'seed':306,'skin':(.38,.38,.33),'shirt':(.17,.20,.22),'pants':(.16,.18,.19),
                 'trim':(.29,.31,.31),'stance':-.03,'stride':.25,'drag':.08,'outfit':'vest'},
    'injured_crawler': {'seed':407,'skin':(.41,.40,.34),'shirt':(.30,.30,.21),'pants':(.25,.23,.20),
                 'trim':(.16,.15,.12),'stance':.20,'stride':.10,'drag':.35,'outfit':'ripped'},
}
CLIPS = {'idle':(4,180),'shamble':(8,155),'fast_shamble':(8,90),
         'attack':(6,95),'stagger':(4,105),'knockdown':(7,110),
         'get_up':(7,130),'crawl':(8,145),'death':(7,135),'corpse':(1,1000)}
SELECTED = {'idle':(1,), 'shamble':(1,3,5,7), 'attack':(1,3,6),
            'crawl':(1,5), 'death':(1,7), 'corpse':(1,)}
DIRS = ('S','W','N','E') if args.directions==4 else ('S','SW','W','NW','N','NE','E','SE')

def mat(name,color,rough=.88,noise=.06):
    m=bpy.data.materials.new(name)
    m.diffuse_color=(*color,1)
    m.use_nodes=True
    nodes=m.node_tree.nodes
    nodes.clear()
    output=nodes.new('ShaderNodeOutputMaterial')
    principled=nodes.new('ShaderNodeBsdfPrincipled')
    principled.inputs['Roughness'].default_value=rough
    principled.inputs['Metallic'].default_value=0
    tex=nodes.new('ShaderNodeTexNoise')
    tex.inputs['Scale'].default_value=47
    tex.inputs['Detail'].default_value=2
    tint=nodes.new('ShaderNodeValToRGB')
    tint.color_ramp.elements[0].position=.17
    tint.color_ramp.elements[0].color=(*(max(0,c*(1-noise)) for c in color),1)
    tint.color_ramp.elements[1].position=.83
    tint.color_ramp.elements[1].color=(*(min(1,c*(1+noise)) for c in color),1)
    m.node_tree.links.new(tex.outputs['Fac'],tint.inputs['Fac'])
    m.node_tree.links.new(tint.outputs['Color'],principled.inputs['Base Color'])
    m.node_tree.links.new(principled.outputs[0],output.inputs[0])
    return m

def mesh_part(name,points,faces,bone,material,rig):
    mesh=bpy.data.meshes.new(name)
    mesh.from_pydata(points,[],faces)
    mesh.update()
    ob=bpy.data.objects.new(name,mesh)
    bpy.context.collection.objects.link(ob)
    ob.data.materials.append(material)
    group=ob.vertex_groups.new(name=bone)
    group.add(list(range(len(points))),1.0,'REPLACE')
    ob.parent=rig
    deform=ob.modifiers.new('F05 shared-armature compatibility','ARMATURE')
    deform.object=rig
    return ob

def tapered(name,center,z_min,z_max,bottom_xy,top_xy,bone,material,rig,segments=12):
    verts=[]
    for z,(rx,ry) in ((z_min,bottom_xy),(z_max,top_xy)):
        for i in range(segments):
            theta=math.tau*i/segments
            verts.append((center[0]+rx*math.cos(theta), center[1]+ry*math.sin(theta),z))
    faces=[]
    for i in range(segments):
        j=(i+1)%segments
        faces.append((i,j,j+segments,i+segments))
    faces.append(tuple(reversed(range(segments))))
    faces.append(tuple(range(segments,2*segments)))
    return mesh_part(name,verts,faces,bone,material,rig)

def ball(name,pos,scale,bone,material,rig,segments=12,rings=8):
    verts=[]
    for j in range(rings+1):
        phi=math.pi*j/rings
        for i in range(segments):
            theta=math.tau*i/segments
            verts.append((pos[0]+scale[0]*math.sin(phi)*math.cos(theta),
                          pos[1]+scale[1]*math.sin(phi)*math.sin(theta),
                          pos[2]+scale[2]*math.cos(phi)))
    faces=[]
    for j in range(rings):
        for i in range(segments):
            a=j*segments+i
            b=j*segments+(i+1)%segments
            faces.append((a,b,b+segments,a+segments))
    return mesh_part(name,verts,faces,bone,material,rig)

def segment(name,start,end,radius,bone,material,rig,steps=12):
    a,b=Vector(start),Vector(end)
    axis=(b-a).normalized()
    u=axis.cross(Vector((0,1,0)))
    if u.length<.02:u=axis.cross(Vector((1,0,0)))
    u.normalize()
    v=axis.cross(u).normalized()
    points=[]
    for anchor,radius_scale in ((a,1),(b,.83)):
        for i in range(steps):
            q=anchor+radius*radius_scale*(math.cos(math.tau*i/steps)*u+math.sin(math.tau*i/steps)*v)
            points.append(tuple(q))
    faces=[(i,(i+1)%steps,(i+1)%steps+steps,i+steps) for i in range(steps)]
    faces += [tuple(reversed(range(steps))),tuple(range(steps,steps*2))]
    return mesh_part(name,points,faces,bone,material,rig)

def appearance(profile,rig):
    rng=random.Random(profile['seed'])
    skin=mat('Pallid skin / F11 provisional',profile['skin'],.78,.13)
    fabric=mat('Worn woven cloth / F11 provisional',profile['shirt'],.95,.12)
    pants=mat('Stained twill / F11 provisional',profile['pants'],.94,.10)
    trim=mat('Thread and seams / F11 provisional',profile['trim'],.82,.08)
    grime=mat('Localized grime / F11 provisional',(.19,.15,.13),.97,.23)
    shoe=mat('Aged leather and rubber / F11 provisional',(.13,.13,.12),.84,.09)
    eye=mat('Recessed eye',(.15,.17,.14),.88,.01)
    hair=mat('Short uneven hair',(.15,.14,.12),.92,.10)
    # Anatomical axes directly reuse F05 bone labels, with configurable original garment shapes.
    tapered('torso cloth / contoured jacket',(0,0),1.06,1.45,(.177,.133),(.235,.153),'chest',fabric,rig)
    tapered('hem / garment overlap',(0,0),1.04,1.13,(.178,.14),(.184,.145),'spine',fabric,rig)
    tapered('pelvis trousers',(0,0),.89,1.04,(.185,.142),(.18,.14),'pelvis',pants,rig)
    ball('neck skin',(0,-.005,1.51),(.084,.074,.105),'neck',skin,rig)
    ball('head / cheek and cranial volume',(0,-.008,1.65),(.121,.111,.160),'head',skin,rig)
    ball('jaw and chin',(0,-.042,1.555),(.097,.089,.074),'head',skin,rig)
    ball('nose',(0,-.124,1.648),(.030,.037,.052),'head',skin,rig)
    ball('left recessed eye',(-.048,-.104,1.687),(.029,.013,.018),'head',eye,rig)
    ball('right recessed eye',(.048,-.104,1.684),(.026,.013,.017),'head',eye,rig)
    ball('uneven hair cap',(0,.016,1.765),(.121,.109,.056),'head',hair,rig)
    # Collars, hems and material segregation make silhouettes legible without random noise.
    tapered('raised left lapel',(-.10,-.09),1.37,1.50,(.042,.024),(.04,.023),'chest',trim,rig,8)
    tapered('raised right lapel',(.10,-.09),1.37,1.50,(.042,.024),(.04,.023),'chest',trim,rig,8)
    for side,sign in (('L',1),('R',-1)):
        segment('upper sleeve '+side,(sign*.239,0,1.43),(sign*.34,0,1.18),.083,
                'upper_arm_'+side,fabric,rig)
        segment('forearm '+side,(sign*.34,0,1.18),(sign*.375,0,.95),.064,
                'forearm_'+side,skin if (side=='L' and profile['outfit']=='ripped') else fabric,rig)
        ball('hand '+side,(sign*.373,-.012,.88),(.057,.047,.091),'hand_'+side,skin,rig)
        segment('trouser leg '+side,(sign*.117,0,.92),(sign*.12,0,.56),.116,
                'thigh_'+side,pants,rig)
        segment('lower trouser '+side,(sign*.12,0,.56),(sign*.12,0,.14),.085,
                'shin_'+side,pants,rig)
        ball('shoe '+side,(sign*.12,-.112,.075),(.10,.171,.083),'foot_'+side,shoe,rig)
        # Elbow / knee seam band as independently editable garment topology.
        ball('sleeve cuff '+side,(sign*.363,0,.962),(.069,.063,.029),'forearm_'+side,trim,rig)
    if profile['outfit']=='jacket':
        tapered('button placket',(0,-.142),1.11,1.40,(.021,.016),(.026,.015),'chest',trim,rig,8)
        for z in (1.20,1.29,1.38):
            ball('dull button',(0,-.167,z),(.012,.009,.012),'chest',shoe,rig,8,5)
        ball('sagging left breast pocket',(-.126,-.147,1.29),(.078,.020,.060),'chest',trim,rig)
    elif profile['outfit']=='scrubs':
        for x in (-.12,.12):
            ball('scrub patch pocket',(x,-.142,1.20),(.066,.016,.065),'chest',trim,rig)
        ball('medical tag / no readable brand',(.105,-.162,1.38),(.042,.014,.018),'chest',grime,rig)
    elif profile['outfit']=='vest':
        tapered('padded uniform vest',(0,-.008),1.15,1.41,(.199,.174),(.239,.184),'chest',trim,rig)
        for x in (-.122,.122):
            ball('vest pouch',(x,-.179,1.237),(.075,.035,.069),'chest',fabric,rig)
        tapered('vest utility stripe',(0,-.192),1.31,1.332,(.14,.014),(.14,.014),'chest',fabric,rig,8)
    else:
        ball('torn shoulder flap',(.244,-.045,1.391),(.086,.062,.048),'upper_arm_R',grime,rig)
        ball('localized forearm abrasion',(-.36,-.047,1.09),(.045,.013,.072),'forearm_L',grime,rig)
    # Localized stains, not a screen-sized random splatter; tightly attached to body bones.
    stain_x=rng.choice((-.16,.16))
    ball('old chest stain',(stain_x,-.158,1.25),(.049,.014,.065),'chest',grime,rig)
    ball('grimy trouser knee',(-.12,-.090,.55),(.055,.012,.080),'shin_L',grime,rig)

def reset_pose(rig):
    rig.rotation_euler=(0,0,0)
    for bone in rig.pose.bones:
        bone.rotation_mode='XYZ'
        bone.rotation_euler=(0,0,0)
        bone.location=(0,0,0)

def pose(rig,clip,frame,profile):
    reset_pose(rig)
    total=CLIPS[clip][0]
    phase=math.tau*(frame-1)/total
    prog=(frame-1)/max(1,total-1)
    crawling=clip in ('crawl','corpse') or profile['outfit']=='ripped' and clip not in ('death','knockdown','get_up')
    fall=clip in ('knockdown','death')
    down=clip=='corpse'
    rig.rotation_euler.x=(1.18 if crawling else 1.43 if down else 1.4*prog if fall else 0)
    spine=rig.pose.bones['spine']
    spine.rotation_euler=(profile['stance'] + (.09*math.sin(phase) if clip in ('idle','shamble') else 0),0,.10)
    rig.pose.bones['head'].rotation_euler=(-.12,0,-.18)
    for side,sign in (('L',1),('R',-1)):
        thigh=rig.pose.bones['thigh_'+side]
        arm=rig.pose.bones['upper_arm_'+side]
        fore=rig.pose.bones['forearm_'+side]
        shin=rig.pose.bones['shin_'+side]
        stride=profile['stride']
        if clip in ('shamble','fast_shamble','crawl'):
            multiplier=1.6 if clip=='fast_shamble' else 1
            thigh.rotation_euler.x=sign*stride*multiplier*math.sin(phase)
            if side=='L': thigh.rotation_euler.x*=1-profile['drag']
            shin.rotation_euler.x=.13+(.18 if side=='L' else .07)*max(0,math.sin(phase))
            arm.rotation_euler.x=-.24-sign*.28*math.sin(phase)
        else:
            arm.rotation_euler.x=-.38+(sign*.09)
        fore.rotation_euler.x=-.09
        if crawling:
            arm.rotation_euler.x=-.8+.19*math.sin(phase)*sign
            fore.rotation_euler.x=-.50
            thigh.rotation_euler.x=.49+sign*.15*math.sin(phase)
            shin.rotation_euler.x=-.62
    if clip=='attack':
        reach=(0,.23,1,.6,.3,.02)[frame-1]
        rig.pose.bones['upper_arm_R'].rotation_euler.x=-.5-1.12*reach
        rig.pose.bones['forearm_R'].rotation_euler.x=-.35
        rig.pose.bones['chest'].rotation_euler.z=-.18*reach
    if clip=='stagger':
        spine.rotation_euler.x=-.2*math.sin(math.pi*prog)

def bake_actions(rig,profile,scene):
    """Persist sampled F06 animation in actual editable Blender Actions."""
    rig.animation_data_create()
    for clip,(count,ms) in CLIPS.items():
        action=bpy.data.actions.new('F06_V2_CAL_'+clip)
        rig.animation_data.action=action
        action.use_fake_user=True
        for frame in range(1,count+1):
            scene.frame_set(frame)
            pose(rig,clip,frame,profile)
            rig.keyframe_insert(data_path='rotation_euler',frame=frame)
            for bone in rig.pose.bones:
                bone.keyframe_insert(data_path='rotation_euler',frame=frame)
        action.use_fake_user=True
    reset_pose(rig)

def export_variant(profile_name,profile):
    bpy.ops.wm.open_mainfile(filepath=str(Path(args.f05_blend).resolve()))
    rig=bpy.data.objects['F05_TEST_RIG']
    assert {'root','pelvis','spine','chest','head','upper_arm_R','foot_L','foot_R'} <= set(rig.pose.bones.keys())
    # Preserve only armature and F05 socket objects; replace training mannequin/proxies.
    for obj in list(bpy.data.objects):
        if obj.type=='MESH': bpy.data.objects.remove(obj,do_unlink=True)
    appearance(profile,rig)
    scene=bpy.context.scene
    turntable=bpy.data.objects.new('F06_DIRECTION_TURNTABLE',None)
    bpy.context.collection.objects.link(turntable)
    rig.parent=turntable
    bake_actions(rig,profile,scene)
    scene.render.engine='BLENDER_EEVEE'
    scene.eevee.taa_render_samples=args.samples
    scene.render.resolution_x=256
    scene.render.resolution_y=192
    scene.render.resolution_percentage=100
    scene.render.film_transparent=True
    scene.render.image_settings.file_format='PNG'
    scene.render.image_settings.color_mode='RGBA'
    scene.view_settings.view_transform='Standard'
    scene.camera.data.type='ORTHO'
    # Entire prone-to-standing envelope must fit the same canvas in every facing.
    scene.camera.data.ortho_scale=3.5
    scene.camera.location=(3.5,-3.5,3.25)
    scene.camera.rotation_euler=(Vector((0,0,.77))-scene.camera.location).to_track_quat('-Z','Y').to_euler()
    scene.world.color=(.12,.12,.12)
    for o in bpy.data.objects:
        if o.type=='LIGHT':
            o.location=(-3,-4,6)
            o.data.energy=680
            o.data.size=3.1
    rendered=[]
    image_frames=[]
    folder=out/profile_name
    folder.mkdir(parents=True,exist_ok=True)
    clip_selection=({'shamble':(3,),'attack':(3,),'corpse':(1,),'idle':(1,)}
                    if args.validate_crops else
                    {'idle':(1,),'corpse':(1,)} if args.preview_only else SELECTED)
    for clip,frames in clip_selection.items():
        rig.animation_data.action=bpy.data.actions['F06_V2_CAL_'+clip]
        for frame in frames:
            scene.frame_set(frame)
            for n,dir_name in enumerate(DIRS):
                turntable.rotation_euler.z=(math.tau*n/args.directions)
                name=f'{clip}_{dir_name}_{frame:02d}.png'
                scene.render.filepath=str(folder/name)
                bpy.ops.render.render(write_still=True)
                rendered.append(name)
                image_frames.append({'clip':clip,'frame_1_based':frame,
                                     'direction':dir_name,'file':name,
                                     'duration_ms':CLIPS[clip][1],
                                     'pivot_px':[128,143]})
    reset_pose(rig)
    turntable.rotation_euler.z=0
    rig.animation_data.action=bpy.data.actions['F06_V2_CAL_idle']
    bpy.ops.wm.save_as_mainfile(filepath=str(folder/'editable_noncanonical.blend'))
    bpy.ops.object.select_all(action='DESELECT')
    rig.select_set(True)
    for o in bpy.data.objects:
        if o.type=='MESH' or o.name.startswith('socket_'): o.select_set(True)
    bpy.context.view_layer.objects.active=rig
    export_error=None
    try:
        bpy.ops.export_scene.gltf(filepath=str(folder/'noncanonical.glb'),export_format='GLB',use_selection=True)
    except Exception as exc:
        export_error=str(exc)
    result={'status':'CALIBRATION_ONLY','canonical_master_id':None,'profile':profile_name,
            'source_f05_rig':'F05_CAL_0.1','f12_approved':False,
            'frame_canvas_px':[256,192],'pivot_px':[128,143],
            'directions':list(DIRS),'frames':image_frames,
            'contact_metadata':{'clip':'attack','frame_1_based':3,'time_ms':285,
                                'event':'VISUAL_MARKER_ONLY_W03_OWNS_DAMAGE'},
            'qa':{'source_generated':'PASS','glb_export':'FAIL' if export_error else 'PASS',
                  'glb_error':export_error,'f05_final_rig':'BLOCKED',
                  'foot_grounding':'NOT_APPROVED','collision_contract':'NOT_RUN',
                  'pixel_readability':'FOUNDER_REVIEW_REQUIRED','godot':'NOT_RUN',
                  'iphone':'NOT_RUN'},
            'sha256':{}}
    for file in sorted(folder.iterdir()):
        if file.is_file(): result['sha256'][file.name]=hashlib.sha256(file.read_bytes()).hexdigest()
    (folder/'manifest.json').write_text(json.dumps(result,indent=2)+'\n')
    print('F06_V2_VARIANT_COMPLETE',profile_name,len(rendered),'frames','glb',not export_error)
    return result

report=[]
for name,profile in PROFILES.items():
    if args.profiles and name not in args.profiles:continue
    report.append(export_variant(name,profile))
(out/'batch_manifest.json').write_text(json.dumps({'status':'CALIBRATION_ONLY',
    'canonical_verified_ids':[],'profile_count':len(report),
    'rendered_frames':sum(len(r['frames']) for r in report),
    'w03_owns_damage_loot_and_ai':True},indent=2)+'\n')
print('F06_V2_COMPLETE',out)
