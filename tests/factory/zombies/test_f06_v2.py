"""Independent-of-Blender F06 calibration manifest and PNG integrity checks."""
import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image

parser=argparse.ArgumentParser()
parser.add_argument('directory',type=Path)
args=parser.parse_args()
failures=[]
report=[]
batch=json.loads((args.directory/'batch_manifest.json').read_text())
assert batch['canonical_verified_ids']==[]
for folder in sorted(p for p in args.directory.iterdir() if p.is_dir()):
    m=json.loads((folder/'manifest.json').read_text())
    assert m['status']=='CALIBRATION_ONLY' and m['canonical_master_id'] is None
    assert m['contact_metadata']['time_ms']==285
    assert m['contact_metadata']['frame_1_based']==3
    assert m['qa']['glb_export']=='PASS',f'{folder.name}: GLB export failed'
    assert (folder/'editable_noncanonical.blend').exists()
    assert (folder/'noncanonical.glb').exists()
    atlas_meta=json.loads((folder/'atlas.json').read_text())
    if len(atlas_meta['sprites'])!=len(m['frames']):
        failures.append(f'atlas frame-count mismatch {folder}')
    for page in atlas_meta['pages']:
        with Image.open(folder/page['file']) as atlas_img:
            if atlas_img.mode!='RGBA' or max(atlas_img.size)>2048:
                failures.append(f'oversize or invalid atlas {folder}')
            if hashlib.sha256((folder/page['file']).read_bytes()).hexdigest()!=page['sha256']:
                failures.append(f'atlas page hash mismatch {folder}/{page["file"]}')
            for entry in (e for e in atlas_meta['sprites'] if e['page']==page['file']):
                x,y,w,h=entry['rect']
                if x<0 or y<0 or x+w>atlas_img.width or y+h>atlas_img.height:
                    failures.append(f'out-of-bounds atlas rect {folder}/{entry["name"]}')
                    continue
                with Image.open(folder/entry['name']) as single:
                    if atlas_img.crop((x,y,x+w,y+h)).tobytes()!=single.tobytes():
                        failures.append(f'atlas pixels disagree {folder}/{entry["name"]}')
    bboxes={}
    for f in m['frames']:
        path=folder/f['file']
        if not path.exists(): failures.append(f'missing {path}');continue
        with Image.open(path) as image:
            if image.mode!='RGBA' or image.size!=(256,192):
                failures.append(f'bad format/canvas {path}')
            alpha=image.getchannel('A')
            bb=alpha.getbbox()
            if not bb: failures.append(f'empty sprite {path}')
            else:
                bboxes.setdefault((f['clip'],f['direction']),[]).append(bb)
                if bb[0]<=0 or bb[2]>=256 or bb[1]<=0 or bb[3]>=192:
                    failures.append(f'edge crop {path}: {bb}')
        digest=hashlib.sha256(path.read_bytes()).hexdigest()
        if digest!=m['sha256'][f['file']]: failures.append(f'hash mismatch {path}')
    for (clip,direction),boxes in bboxes.items():
        spread=max(b[3] for b in boxes)-min(b[3] for b in boxes)
        if spread>16 and clip not in {'death','crawl'}:
            # Detect anchor instability, but don't confuse mesh bounds with true world pivot.
            failures.append(f'{folder.name}/{clip}/{direction} image-bottom spread {spread}px (>16)')
    report.append({'profile':folder.name,'frames':len(m['frames']),
                   'clips':sorted(set(k[0] for k in bboxes)),'glb_export':m['qa']['glb_export']})
result={'status':'PASS' if not failures else 'FAIL','profiles':report,'failures':failures}
(args.directory/'qa_result.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
if failures: raise SystemExit(1)
