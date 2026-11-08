"""Deterministic full-canvas RGBA sprite packing, independent of the Godot runtime.

Usage: python tools/factory/zombies/f06_pack_atlas.py /path/to/f06-v2-output
Provisional sprite envelope. F12 has not approved camera/pivot/atlas semantics.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path

from PIL import Image

p=argparse.ArgumentParser()
p.add_argument('output',type=Path)
p.add_argument('--columns',type=int,default=7)
args=p.parse_args()
for folder in sorted(x for x in args.output.iterdir() if x.is_dir()):
    manifest=json.loads((folder/'manifest.json').read_text())
    frames=manifest['frames']
    cols=args.columns
    w,h=manifest['frame_canvas_px']
    pad=2
    cell_w,cell_h=w+2*pad,h+2*pad
    rows=math.ceil(len(frames)/cols)
    width,height=cols*cell_w,rows*cell_h
    # Conservative nonpower-of-two texture avoids padding a tiny calibration into a huge atlas.
    atlas=Image.new('RGBA',(width,height),(0,0,0,0))
    items=[]
    for i,f in enumerate(frames):
        col,row=i%cols,i//cols
        x,y=col*cell_w+pad,row*cell_h+pad
        with Image.open(folder/f['file']) as src:
            assert src.size==(w,h) and src.mode=='RGBA'
            atlas.paste(src,(x,y))
        items.append({'name':f['file'],'clip':f['clip'],'direction':f['direction'],
                      'frame_1_based':f['frame_1_based'],'duration_ms':f['duration_ms'],
                      'rect':[x,y,w,h],'pivot':f['pivot_px']})
    atlas.save(folder/'atlas.png',optimize=True)
    metadata={'schema_version':1,'status':'CALIBRATION_ONLY','profile':folder.name,
              'atlas_file':'atlas.png','atlas_size':[width,height],
              'padding_px':pad,'provisional_f12':True,'sprites':items,
              'visual_events':[manifest['contact_metadata']],
              'sha256':hashlib.sha256((folder/'atlas.png').read_bytes()).hexdigest()}
    (folder/'atlas.json').write_text(json.dumps(metadata,indent=2)+'\n')
    print('F06_ATLAS_PACKED',folder.name,atlas.size,len(items))
