"""Run once per F06 V2 exported .blend file through Blender CLI.

blender -b --factory-startup --python tests/factory/zombies/f06_blender_reopen_check.py -- /path/to/editable_noncanonical.blend
"""
import sys
from pathlib import Path
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
glb=Path(path).with_name('noncanonical.glb')
assert glb.exists()
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=str(glb))
assert any(o.type=='ARMATURE' for o in bpy.context.scene.objects), 'GLB armature missing'
assert len([o for o in bpy.context.scene.objects if o.type=='MESH']) >= 25, 'GLB geometry lost'
print('F06_V2_BLENDER_REOPEN_PASS',path,len(expected),'actions','GLB import PASS')
