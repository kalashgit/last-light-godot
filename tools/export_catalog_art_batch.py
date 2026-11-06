#!/usr/bin/env python3
"""Export original AI-assisted sources with the approved V4 native64 cleanup.
No source-reference pixels are read. Review-only candidates, never promotion.
"""
import argparse,hashlib,json,sys
from pathlib import Path
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import LAST_LIGHT_MASTER_SPRITE_FACTORY_V4 as v

def export(folder):
 folder=Path(folder);briefs=json.loads((folder/'briefs.json').read_text());src=folder/'original_generated_sheet.png';im=Image.open(src).convert('RGBA');rows=[]
 board=Image.new('RGB',(5*180,4*200),'#263035');d=ImageDraw.Draw(board)
 for i,r in enumerate(briefs):
  box=(round(i%5*im.width/5),round(i//5*im.height/4),round((i%5+1)*im.width/5),round((i//5+1)*im.height/4))
  if r['design']=='firefighter_axe':box=(box[0]-20,box[1]-70,min(im.width,box[2]+40),box[3])
  tile=im.crop(box)
  replacement=folder/'corrections'/(r['design']+'.png')
  if replacement.exists():tile=Image.open(replacement).convert('RGBA')
  alpha=tile.getchannel('A').point(lambda n:255 if n>=128 else 0)
  # The same connected-component cleanup as the approved V4 authoring pipeline.
  pixels=alpha.load();seen=set();components=[]
  for yy in range(alpha.height):
   for xx in range(alpha.width):
    if not pixels[xx,yy] or (xx,yy) in seen:continue
    stack=[(xx,yy)];seen.add((xx,yy));component=[]
    while stack:
     cx,cy=stack.pop();component.append((cx,cy))
     for dx,dy in [(-1,-1),(0,-1),(1,-1),(-1,0),(1,0),(-1,1),(0,1),(1,1)]:
      nx,ny=cx+dx,cy+dy
      if 0<=nx<alpha.width and 0<=ny<alpha.height and pixels[nx,ny] and (nx,ny) not in seen:seen.add((nx,ny));stack.append((nx,ny))
    components.append(component)
    if len(component)<40:
     for cx,cy in component:pixels[cx,cy]=0
  if r['design']=='firefighter_axe':
   largest=max(components,key=len)
   for component in components:
    if component is not largest:
     for cx,cy in component:pixels[cx,cy]=0
  tile.putalpha(alpha);bbox=alpha.getbbox()
  if not bbox:raise ValueError('Empty source cell '+r['design'])
  source_margin=min(bbox[0],bbox[1],tile.width-bbox[2],tile.height-bbox[3])
  tile=tile.crop(bbox);tile.thumbnail((56,56),Image.Resampling.NEAREST)
  alpha=tile.getchannel('A');tile=tile.convert('RGB').quantize(colors=48,dither=Image.Dither.NONE).convert('RGBA');tile.putalpha(alpha)
  out=Image.new('RGBA',(64,64));out.alpha_composite(tile,((64-tile.width)//2,(64-tile.height)//2))
  pix=out.load()
  for y in range(64):
   for x in range(64):
    if pix[x,y][3]==0:pix[x,y]=(0,0,0,0)
  path=folder/'candidates'/r['design']/'icon.png';path.parent.mkdir(parents=True,exist_ok=True);out.save(path)
  qa=v.technical_qa(out)
  rec={**r,'asset_id':'art.'+r['logical_item_id']+'.icon.candidate_v001','relative_path':str(path.relative_to(folder)),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'width':64,'height':64,'format':'RGBA_PNG','technical_qa':qa,'source_crop':box,'source_bounds':bbox,'source_margin':source_margin,'source_clipping_review_required':source_margin<3,'provenance':{'method':'Original AI-assisted source; native64 nearest sampling, binary-alpha cleanup and undithered48-color palette','tool':'image_gen.imagegen','model_version':'not exposed','seed':'not exposed','source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'replacement_source':str(replacement.relative_to(folder)) if replacement.exists() else None,'replacement_sha256':hashlib.sha256(replacement.read_bytes()).hexdigest() if replacement.exists() else None,'reference_pixels_used':False},'production_status':'visual_review_required','founder_approved':False,'godot_imported':False,'device_verified':False}
  rows.append(rec);d.text((i%5*180+4,i//5*200+1),str(i+1)+' '+r['design'][:25],fill='white');zoom=out.resize((128,128),Image.Resampling.NEAREST);board.paste(zoom,(i%5*180+26,i//5*200+25),zoom)
  d.text((i%5*180+4,i//5*200+160),'source #'+str(r['catalog_index']),fill='white')
 board.save(folder/'review_3x.png');(folder/'manifest.json').write_text(json.dumps(rows,indent=2)+'\n')
 print(json.dumps({'exported':len(rows),'technical_passes':sum(r['technical_qa']['passed'] for r in rows),'source_clipping_flags':[r['design'] for r in rows if r['source_clipping_review_required']]}))
 return rows
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('folder',type=Path);export(p.parse_args().folder)
