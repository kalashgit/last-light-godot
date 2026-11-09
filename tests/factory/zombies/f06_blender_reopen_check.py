"""Run once per F06 V2 exported .blend file through Blender CLI.

blender -b --factory-startup --python tests/factory/zombies/f06_blender_reopen_check.py -- /path/to/editable_noncanonical.blend
"""
import sys
from pathlib import Path
for sys_path in ('/usr/lib/python3.12/lib-dynload',
                 '/opt/codex/runtimes/codex-primary-runtime/dependencies/python/lib/python3.12/site-packages'):
    if sys_path not in sys.path:sys.path.append(sys_path)
import bpy

path=sys.argv[sys.argv.index('--')+1]
bpy.ops.wm.open_mainfile(filepath=path)
rig=bpy.data.objects.get('F05_TEST_RIG')
assert rig and rig.type=='ARMATURE'
expected={'F06_V2_CAL_'+clip for clip in
          ('idle','shamble','fast_shamble','attack','stagger',
           'knockdown','get_up','crawl','death','corpse')}
actual=set(bpy.data.actions.keys())
assert expected <= actual,(expected-actual)
# V9 deletes the V2/V7 disconnected proxies in favor of unified topology,
# so a lower object count is a success rather than missing geometry.
expected_meshes=20 if bpy.data.objects.get('V9 integrated craniofacial sculpt') else 25
assert len([o for o in bpy.data.objects if o.type=='MESH']) >= expected_meshes
assert bpy.data.objects.get('F06_DIRECTION_TURNTABLE') is not None
for name in expected:
    action=bpy.data.actions[name]
    assert len(action.fcurves)>0,name
weighted=[o for o in bpy.data.objects if o.type=='MESH' and o.get('F06_WEIGHTED_JOINT')]
continuous=[o for o in bpy.data.objects if o.type=='MESH' and o.get('F06_V6_SKINNED')]
anatomy=[o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('V7 ')]
v9face=bpy.data.objects.get('V9 integrated craniofacial sculpt')
v9garments=[o for o in bpy.data.objects if o.type=='MESH' and o.get('F06_V9_GARMENT_PANEL')]
v9drape=[o for o in bpy.data.objects if o.type=='MESH' and o.get('F06_V9_CLOTH_DRAPE')]
v8_materials=[m for m in bpy.data.materials if m.name.startswith('Worn woven cloth')
              and any(n.type=='BUMP' for n in m.node_tree.nodes)]
if v8_materials:
    assert not any(o.name.startswith(('V4 asymmetrical loose jacket shoulder',
                                     'V4 short scrub sleeve ','V4 security shoulder pad ',
                                     'V4 exposed wounded shoulder',
                                     'raised left lapel','raised right lapel','collar notch'))
                   for o in bpy.data.objects if o.type=='MESH'),'V8 oversized garment proxy present'
    for key in ('Worn woven cloth','Stained twill','Pallid skin'):
        m=next(m for m in bpy.data.materials if m.name.startswith(key))
        assert any(n.type=='BUMP' for n in m.node_tree.nodes),(key,'bump absent')
        ramp=next(n for n in m.node_tree.nodes if n.type=='VALTORGB')
        assert len(ramp.color_ramp.elements)>=5,(key,'macro value range absent')
    print('F06_V8_FABRIC_SKIN_MATERIAL_PASS',len(v8_materials),'five-step cloth recipes')
if anatomy and not v9face:
    assert bpy.data.objects.get('V7 sculpted skull and jaw') is not None
    assert len([o for o in anatomy if 'dangling finger' in o.name])==6
    assert bpy.data.objects['V7 sculpted skull and jaw'].get('F06_V7_ORBITS_CARVED',0)>0
    assert not any('hollow orbit' in o.name for o in anatomy)
    assert not any(o.name.startswith(('head / cheek and cranial volume',
                                     'uneven hair cap','jaw and chin'))
                   for o in bpy.data.objects if o.type=='MESH'), 'old head proxy duplicated'
    print('F06_V7_FACE_HAND_SOURCE_PASS',len(anatomy),'original sculpt elements')
if v9face:
    assert len(v9face.data.vertices)>=3000,'V9 sculpt too sparse'
    assert v9face.get('F06_V9_INTEGRATED_FACE')
    assert 'orbital_ao' in v9face.data.vertex_colors
    assert bpy.data.objects.get('V9 fitted scalp with receding hairline')
    assert bpy.data.objects.get('V9 tendons and neck volume')
    hands=[o for o in bpy.data.objects if o.type=='MESH' and
           o.get('F06_V9_CONNECTED_HAND')]
    assert len(hands)==2,('V9 tapered hands not connected',len(hands))
    assert not any(o.name.startswith(('V7 dangling finger','V7 hand palm'))
                   for o in bpy.data.objects if o.type=='MESH')
    assert not bpy.data.objects.get('V7 sculpted skull and jaw')
    assert len(v9drape)==5,('V9 expected five sculpted/draped parts',len(v9drape))
    assert all(len(o.data.vertices)>=400 for o in v9drape)
    if v9garments:
        assert len(v9garments)==2
        assert all(len(o.vertex_groups)==2 for o in v9garments)
        jacket=next(m for m in bpy.data.materials if m.name.startswith('V4 faded jacket panel'))
        assert any(n.type=='BUMP' for n in jacket.node_tree.nodes)
        jacket_ramp=next(n for n in jacket.node_tree.nodes if n.type=='VALTORGB')
        assert len(jacket_ramp.color_ramp.elements)==5
        assert all(bpy.data.objects[n].data.materials[0]==jacket for n in
                   ('V6 skinned arm L','V6 skinned arm R'))
    for key in ('Pallid skin','V7 skull orbital gradient'):
        m=next(m for m in bpy.data.materials if m.name.startswith(key))
        bump=next(n for n in m.node_tree.nodes if n.type=='BUMP')
        assert bump.inputs['Strength'].default_value<=.02
    print('F06_V9_SCULPT_GARMENT_SOURCE_PASS',len(v9face.data.vertices),
          len(v9drape),len(v9garments),len(hands))
if continuous:
    assert len(continuous)==5,('expected torso plus four complete limbs',len(continuous))
    assert not any(o.name.startswith(('V5 deforming ','upper sleeve ','forearm ',
                                     'trouser leg ','lower trouser ',
                                     'V3 anatomical torso garment'))
                   for o in bpy.data.objects if o.type=='MESH'), 'duplicate rigid proxy shells'
    for obj in continuous:
        assert len(obj.vertex_groups)>=2,(obj.name,'not multiply skinned')
        assert len(obj.data.vertices)>=120,(obj.name,'mesh too sparse')
        mixed=sum(1 for vertex in obj.data.vertices
                  if len(vertex.groups)>=2 and min(g.weight for g in vertex.groups)>.02)
        assert mixed>=20,(obj.name,'no blended deformation rings',mixed)
    rig.animation_data.action=bpy.data.actions['F06_V2_CAL_attack']
    sample=[]
    arm=next(o for o in continuous if o.name=='V6 skinned arm R')
    for frame in (1,3):
        bpy.context.scene.frame_set(frame)
        evaluated=arm.evaluated_get(bpy.context.evaluated_depsgraph_get())
        mesh=evaluated.to_mesh()
        sample.append(tuple(mesh.vertices[0].co))
        evaluated.to_mesh_clear()
    assert sum((a-b)**2 for a,b in zip(*sample))>1e-5,('V6 arm did not deform',sample)
    print('F06_V6_CONTINUOUS_SKINNING_PASS',len(continuous),'body meshes','attack deformation PASS')
if weighted:
    assert len(weighted)>=6,('weighted joints missing',len(weighted))
    for obj in weighted:
        assert len(obj.vertex_groups)==2,(obj.name,'expected two joint influences')
        # At least three rings must blend both bones, not swap rigid ownership.
        mixed=0
        for vertex in obj.data.vertices:
            influences=[assignment.weight for assignment in vertex.groups]
            if len(influences)==2 and .05<min(influences)<.95:mixed+=1
        assert mixed>=16,(obj.name,'no smoothly blended rings',mixed)
    rig.animation_data.action=bpy.data.actions['F06_V2_CAL_attack']
    obj=next(o for o in weighted if 'elbow sleeve R' in o.name)
    sample=[]
    for frame in (1,3):
        bpy.context.scene.frame_set(frame)
        depsgraph=bpy.context.evaluated_depsgraph_get()
        eval_obj=obj.evaluated_get(depsgraph)
        mesh=eval_obj.to_mesh()
        sample.append(tuple(mesh.vertices[0].co))
        eval_obj.to_mesh_clear()
    assert sum((a-b)**2 for a,b in zip(*sample))>1e-5,('weighted joint did not deform',sample)
    print('F06_V5_DUAL_WEIGHT_QA_PASS',len(weighted),'smooth joints','deformation PASS')
glb=Path(path).with_name('noncanonical.glb')
assert glb.exists()
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=str(glb))
assert any(o.type=='ARMATURE' for o in bpy.context.scene.objects), 'GLB armature missing'
assert len([o for o in bpy.context.scene.objects if o.type=='MESH']) >= expected_meshes, 'GLB geometry lost'
if weighted:
    imported=[o for o in bpy.context.scene.objects if o.type=='MESH' and 'V5 deforming' in o.name]
    assert len(imported)>=6,('weighted sleeves not exported',len(imported))
    assert all(len(o.vertex_groups)>=2 for o in imported),'GLB skin weights lost'
    print('F06_V5_GLTF_SKINNING_PASS',len(imported),'dual-weight meshes')
if continuous:
    imported=[o for o in bpy.context.scene.objects if o.type=='MESH' and 'V6 skinned' in o.name or o.type=='MESH' and 'V6 continuous torso' in o.name]
    assert len(imported)>=5,('V6 skinned meshes missing in GLB',len(imported))
    assert all(len(o.vertex_groups)>=2 for o in imported),'V6 GLB skin groups missing'
    print('F06_V6_GLTF_SKINNING_PASS',len(imported),'continuous skinned meshes')
if anatomy and not v9face:
    assert any(o.type=='MESH' and 'V7 sculpted skull and jaw' in o.name
               for o in bpy.context.scene.objects),'V7 sculpted head missing in GLB'
    assert len([o for o in bpy.context.scene.objects
                if o.type=='MESH' and 'V7 dangling finger' in o.name])==6
    print('F06_V7_HEAD_HAND_GLTF_PASS')
if v9face:
    assert any(o.type=='MESH' and 'V9 integrated craniofacial sculpt' in o.name
               for o in bpy.context.scene.objects),'V9 face missing in GLB'
    assert any(o.type=='MESH' and 'V9 fitted scalp' in o.name
               for o in bpy.context.scene.objects),'V9 hair missing in GLB'
    assert len([o for o in bpy.context.scene.objects if o.type=='MESH' and
                'V9 anatomically tapered hand' in o.name])==2
    if v9garments:
        imported_panels=[o for o in bpy.context.scene.objects
                         if o.type=='MESH' and 'V9 tailored open jacket' in o.name]
        assert len(imported_panels)==2
        assert all(len(o.vertex_groups)>=2 for o in imported_panels)
    print('F06_V9_FACE_CLOTH_GLTF_PASS')
print('F06_V2_BLENDER_REOPEN_PASS',path,len(expected),'actions','GLB import PASS')
