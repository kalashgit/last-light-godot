import base64,hashlib,json,shutil
from collections import deque
from pathlib import Path
from PIL import Image,ImageDraw
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import LAST_LIGHT_MASTER_SPRITE_FACTORY_V4 as v
root=Path(__file__).resolve().parents[1];b=root/'production/sprite_factory_v4/hybrid_source';b.mkdir(exist_ok=True)
src=b/'original_generated_sheet.png';im=Image.open(src)
payload={};records=[];board=Image.new('RGB',(6*160,4*160),'#20282b');draw=ImageDraw.Draw(board)
for i,r in enumerate(v.demo_recipes()):
 box=(i%6*256,i//6*256,i%6*256+256,i//6*256+256);tile=im.crop(box)
 # Explicit native-pixel cleanup: binary matte, component removal, undithered palette.
 a=tile.getchannel('A').point(lambda x:255 if x>=128 else 0);pixels=a.load();seen=set()
 for y in range(256):
  for x in range(256):
   if not pixels[x,y] or (x,y) in seen:continue
   stack=[(x,y)];seen.add((x,y));component=[]
   while stack:
    xx,yy=stack.pop();component.append((xx,yy))
    for dy in [-1,0,1]:
     for dx in [-1,0,1]:
      nx,ny=xx+dx,yy+dy
      if 0<=nx<256 and 0<=ny<256 and (nx,ny) not in seen and pixels[nx,ny]:seen.add((nx,ny));stack.append((nx,ny))
   if len(component)<40:
    for xx,yy in component:pixels[xx,yy]=0
 tile.putalpha(a);bbox=a.getbbox()
 if not bbox:raise ValueError(r['id'])
 if min(bbox[0],bbox[1],256-bbox[2],256-bbox[3])<2:print('CROP REVIEW',r['id'],bbox)
 tile=tile.crop(bbox);tile.thumbnail((56,56),Image.Resampling.NEAREST)
 alpha=tile.getchannel('A');tile=tile.convert('RGB').quantize(colors=48,dither=Image.Dither.NONE).convert('RGBA');tile.putalpha(alpha)
 out=Image.new('RGBA',(64,64));out.alpha_composite(tile,((64-tile.width)//2,(64-tile.height)//2))
 # Clear hidden colors explicitly and retain clean binary alpha.
 p=out.load()
 for y in range(64):
  for x in range(64):
   if not p[x,y][3]:p[x,y]=(0,0,0,0)
 path=b/(r['design']+'.png');out.save(path)
 payload[r['design']]=base64.b64encode(path.read_bytes()).decode()
 records.append({'recipe_id':r['id'],'design':r['design'],'source_crop':box,'source_object_bounds':bbox,'native_png':str(path.relative_to(root)),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
 zoom=out.resize((128,128),Image.Resampling.NEAREST);board.paste(zoom,((i%6)*160,(i//6)*160),zoom);draw.text(((i%6)*160,(i//6)*160+132),r['design'],fill='white')
board.save(b/'native_templates_review.png')
meta={'tool':'image_gen.imagegen','tool_model_version':'not exposed','seed':'not exposed','source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'prompt_path':'production/sprite_factory_v4/hybrid_prompt.txt','prompt_sha256':hashlib.sha256((root/'production/sprite_factory_v4/hybrid_prompt.txt').read_bytes()).hexdigest(),'reference':'Original founder Golden40 board only; no PZwiki artwork used','method':'Original AI-assisted source templates; native64 nearest sampling, component/matte cleanup and undithered48-color palette; not purely procedural artwork or hand-pixel approval','records':records}
(b/'provenance.json').write_text(json.dumps(meta,indent=2)+'\n')
(b/'template_payload.json').write_text(json.dumps(payload,separators=(',',':')))
print('24 templates:',sum(len(x) for x in payload.values()),'base64 chars')
