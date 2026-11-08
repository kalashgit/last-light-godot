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
assert len([o for o in bpy.data.objects if o.type=='MESH']) >= 25
assert bpy.data.objects.get('F06_DIRECTION_TURNTABLE') is not None
for name in expected:
    action=bpy.data.actions[name]
    assert len(action.fcurves)>0,name
weighted=[o for o in bpy.data.objects if o.type=='MESH' and o.get('F06_WEIGHTED_JOINT')]
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
assert len([o for o in bpy.context.scene.objects if o.type=='MESH']) >= 25, 'GLB geometry lost'
if weighted:
    imported=[o for o in bpy.context.scene.objects if o.type=='MESH' and 'V5 deforming' in o.name]
    assert len(imported)>=6,('weighted sleeves not exported',len(imported))
    assert all(len(o.vertex_groups)>=2 for o in imported),'GLB skin weights lost'
    print('F06_V5_GLTF_SKINNING_PASS',len(imported),'dual-weight meshes')
print('F06_V2_BLENDER_REOPEN_PASS',path,len(expected),'actions','GLB import PASS')
