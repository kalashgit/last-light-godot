"""Batch GLB -> independently editable .blend conversion under headless Blender.

This importer does not replace original creation recipes. Requires Blender's
native glTF importer. All objects remain candidate-only, no Golden flags.
Usage: blender -b --factory-startup --python tools/.../convert_glb_to_blend.py -- --source build/candidates/models --output build/candidates/blend
"""
import argparse, sys, json, hashlib
from pathlib import Path
import bpy

argv=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
p=argparse.ArgumentParser();p.add_argument('--source',required=True,type=Path);p.add_argument('--output',required=True,type=Path)
a=p.parse_args(argv);a.output.mkdir(parents=True,exist_ok=True)
count=0
for glb in sorted(a.source.glob('*.glb')):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(glb.resolve()))
    meshes=[o for o in bpy.data.objects if o.type=='MESH']
    if len(meshes)<2 or sum(len(o.data.polygons) for o in meshes)<50:
        raise ValueError('Original submeshes did not survive import: '+glb.name)
    scene=bpy.context.scene
    scene['ll_candidate_only']=True
    scene['ll_founder_golden_approved']=False
    scene['ll_procedural_recipe_source']='tools/foundry_reference_seed/seed_3d_factory.py'
    scene['ll_glb_source_sha256']=hashlib.sha256(glb.read_bytes()).hexdigest()
    dest=a.output/(glb.stem+'.blend')
    bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(dest.resolve()),compress=False)
    if dest.open('rb').read(7)!=b'BLENDER':
        raise ValueError('Blender native source signature invalid: '+dest.name)
    count+=1
    print('LL_REFERENCE_NATIVE_BLEND_PASS',glb.stem,len(meshes),len(dest.read_bytes()),flush=True)
print('LL_REFERENCE_NATIVE_BATCH_PASS',count,'editable Blender sources',flush=True)
if count!=40:raise ValueError('Expected exactly 40 native source candidates')