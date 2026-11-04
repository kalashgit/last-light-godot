"""Runtime validation + canonical style/scale contracts. Requires Python + Pillow."""
import argparse, collections, hashlib, json, math, re, sys
from pathlib import Path
from PIL import Image
sys.path.insert(0,str(Path(__file__).parent))
from catalog import registry, DIMS
p=argparse.ArgumentParser(); p.add_argument('folder',type=Path); p.add_argument('--count',type=int,default=300); args=p.parse_args()
m=json.loads((args.folder/'manifest.json').read_text()); objects=m['objects']; canonical={o['id']:o for o in registry()}
assert len(objects)==args.count
assert m['tile_px']==[80,40] and m['ground_anchor_px']==[128,192] and m['style']=='ll_worn_residential_v1'
assert len({o['id'] for o in objects})==len(objects)
seen=set(); hashes=set(); modes=collections.Counter(); pixels=0
for obj in objects:
 assert re.fullmatch(r'll_[a-z]+_[a-z0-9_]+',obj['id']),obj['id']
 assert obj['id'] in canonical
 for key in ['dimensions_m','family','material','color_variant','wear','visible_carry','name','category','license','source']:
  assert obj[key]==canonical[obj['id']][key],(obj['id'],key)
 assert obj['source_hash']==m['source_hash']
 assert len(obj['frames'])==(10 if obj['visible_carry'] else 2),obj['id']
 assert collections.Counter(f['mode'] for f in obj['frames'])=={'ground':1,'icon':1,**({'held':8} if obj['visible_carry'] else {})}
 if obj['visible_carry']: assert sorted(f['angle_degrees'] for f in obj['frames'] if f['mode']=='held')==list(range(0,360,45))
 # Geometry bounding box stays at parametric metre scale; no per-ground auto-fit.
 lo,hi=obj['ground_bounds_m']; dims=obj['dimensions_m']
 assert -.03<=lo[2]<=.12,('grounding',obj['id'],lo[2])
 assert .6<=((hi[2]-lo[2])/dims[2])<=1.65,('height',obj['id'])
 for f in obj['frames']:
  assert f['file'] not in seen
  seen.add(f['file']); modes[f['mode']]+=1
  assert f['file']==f'sprites/{obj["id"]}/'+('held_%02d.png'%(f['angle_degrees']//45) if f['mode']=='held' else f['mode']+'.png')
  path=args.folder/f['file']; assert path.is_file(),path
  im=Image.open(path); assert im.mode=='RGBA' and list(im.size)==f['size_px']
  alpha=im.getchannel('A'); box=alpha.getbbox(); assert box
  assert alpha.getextrema()[0]==0 and box[0]>0 and box[1]>0 and box[2]<im.width and box[3]<im.height,('alpha/clipping',path)
  x,y,x2,y2=f['crop_rect_px']; assert [x2-x,y2-y]==f['size_px']
  original=[64,64] if f['mode']=='icon' else [128,192]
  assert f['anchor_px']==[original[0]-x,original[1]-y],('anchor',path)
  assert f['source_canvas_px']==([128,128] if f['mode']=='icon' else [256,256])
  if f['mode']=='icon':
   assert im.size==(128,128)
   hashes.add(hashlib.sha256(im.tobytes()).hexdigest())
   assert max(box[2]-box[0],box[3]-box[1])>=65,('undersized icon',obj['id'])
  else:
   # Reconstructed crop fits original calibrated frame, with >1px padding.
   assert 0<=x<x2<=256 and 0<=y<y2<=256
  pixels+=im.width*im.height
  # Style guard catches saturated outliers; visual review remains necessary.
  rgb=[c[:3] for c in (im.get_flattened_data() if hasattr(im,'get_flattened_data') else im.getdata()) if c[3]>200]
  saturated=sum(max(c)-min(c)>160 for c in rgb)
  assert saturated/max(1,len(rgb))<.01,('palette outlier',path)
all_png={str(p.relative_to(args.folder)) for p in (args.folder/'sprites').rglob('*.png')}
assert seen==all_png,('unreferenced/missing sprites',len(seen^all_png))
assert len(hashes)==len(objects), 'Duplicate inventory icon pixels: differentiate actual recipes'
print(json.dumps(dict(status='PASS',objects=len(objects),families=len({o['family'] for o in objects}),categories=dict(collections.Counter(o['category'] for o in objects)),frames=dict(modes),distinct_icon_pixels=len(hashes),png_bytes=sum((args.folder/p).stat().st_size for p in seen),decoded_rgba_bytes=pixels*4),indent=2))
