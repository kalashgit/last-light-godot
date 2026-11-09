#!/usr/bin/env python3
"""Independent QA: validate all reference-derived 3D candidates.

Never grants Golden status. Checks actual GLB loading, independent meshes,
geometry diversity, provenance, derived sprites and eight-way atlases.
"""
import hashlib, json, sys, os
from pathlib import Path
import numpy as np
import trimesh
from PIL import Image

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for x in iter(lambda:f.read(1<<20),b''):h.update(x)
    return h.hexdigest()

def verify(directory):
    base=Path(directory).resolve()
    data=json.loads((base/'candidate_manifest.json').read_text())
    if data['schema']!='last-light.reference-seed-3d.v1' or data['status']!='TECHNICAL_CANDIDATE_NOT_GOLDEN' or data.get('golden_approved') is not False:
        raise ValueError('bad source status/Golden gate')
    records=data['assets']
    if len(records)!=40 or len({r['candidate_id'] for r in records})!=40 or len({r['recipe_key'] for r in records})!=40:
        raise ValueError('not 40 independent models')
    hashes=set();counts={'verified_glbs':0,'component_meshes':0,'triangles':0,'sprites_64':0,'directional_world_frames':0,'strictly_unique_glbs':0,'visual_qa_status':'NOT_VISUALLY_APPROVED'}
    for i,item in enumerate(records):
        rel=Path(item['glb']);path=(base/rel).resolve()
        if rel.is_absolute() or not path.is_relative_to(base) or not path.is_file():raise ValueError('unsafe/missing GLB')
        if path.read_bytes()[:4]!=b'glTF' or sha(path)!=item['glb_sha256']:raise ValueError('tampered model '+str(item['candidate_id']))
        model=trimesh.load(path,force='scene')
        meshes=list(model.geometry.values())
        if len(meshes)!=item['parts'] or len(meshes)<2:raise ValueError('editable components missing '+str(item['recipe_key']))
        nfaces=sum(len(mesh.faces) for mesh in meshes)
        if nfaces!=item['triangles'] or nfaces<50:raise ValueError('bad triangles '+item['recipe_key'])
        if not np.isfinite(model.bounds).all() or np.min(np.ptp(model.bounds,axis=0))<0.015:raise ValueError('degenerate 3D bounds '+item['recipe_key'])
        if not all(len(mesh.vertices)>0 and np.isfinite(mesh.vertices).all() for mesh in meshes):raise ValueError('bad geometry')
        if item['visual_qa']!='PENDING_FOUNDER_REVIEW' or item['golden'] is not False:raise ValueError('approval cannot auto-pass')
        if len(item.get('editable_components',[]))!=item['parts']:raise ValueError('component inventory mismatch')
        preview=(base/item['preview']).resolve()
        with Image.open(preview) as im:
            if im.size!=(144,144) or im.mode!='RGBA' or im.getchannel('A').getbbox() is None:raise ValueError('invalid preview')
        sprite=(base/item['inventory_sprite']).resolve()
        with Image.open(sprite) as im:
            if im.size!=(64,64) or im.mode!='RGBA':raise ValueError('bad 64 sprite')
            alpha=np.asarray(im.getchannel('A'));fraction=(alpha>0).mean()
            if not 0.03<fraction<0.95:raise ValueError('sprite alpha coverage outside sensible bounds '+item['recipe_key'])
        world=(base/item['world_atlas_8']).resolve()
        with Image.open(world) as im:
            if im.size!=(64,512) or im.mode!='RGBA':raise ValueError('bad eight-direction sheet')
            for direction in range(8):
                if im.crop((0,direction*64,64,(direction+1)*64)).getchannel('A').getbbox() is None:
                    raise ValueError('blank directional frame')
        counts['verified_glbs']+=1;counts['component_meshes']+=len(meshes);counts['triangles']+=nfaces
        counts['sprites_64']+=1;counts['directional_world_frames']+=8
        if item['glb_sha256'] in hashes:raise ValueError('duplicate GLB detected')
        hashes.add(item['glb_sha256'])
    with Image.open(base/'inventory_40_items_64px.png') as atlas:
        if atlas.mode!='RGBA' or atlas.size!=(512,320):raise ValueError('incorrect 40-item atlas')
        for i,record in enumerate(records):
            with Image.open(base/record['inventory_sprite']) as src:
                crop=atlas.crop(((i%8)*64,(i//8)*64,(i%8+1)*64,(i//8+1)*64))
                if src.tobytes()!=crop.tobytes():raise ValueError('inventory atlas pixel drift')
    counts['strictly_unique_glbs']=len(hashes)
    return counts

if __name__=='__main__':
    result=verify(sys.argv[1]);print('LL_REFERENCE_MODEL_QA_PASS',json.dumps(result,sort_keys=True))