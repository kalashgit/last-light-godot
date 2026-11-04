"""Crop sprites without losing anchors; validate before packing and build review sheets."""
import argparse, json, math, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0,str(Path(__file__).parent))
from catalog import registry
p=argparse.ArgumentParser(); p.add_argument('raw',type=Path); p.add_argument('--representatives',action='store_true'); p.add_argument('--output',type=Path,default=Path('assets/generated/factory')); p.add_argument('--sheets',type=Path,default=Path('docs/asset-factory')); a=p.parse_args()
a.output.mkdir(parents=True,exist_ok=True); a.sheets.mkdir(parents=True,exist_ok=True)
batch=json.loads((a.raw/'batch.json').read_text()); specs={o['id']:o for o in registry()}; result=[]
for record in batch['objects']:
 if a.representatives and specs[record['id']]['name'] not in __import__('catalog').REPRESENTATIVE_NAMES: continue
 spec=specs[record['id']].copy(); spec['frames']=[]
 for f in record['frames']:
  im=Image.open(a.raw/spec['id']/f['file']).convert('RGBA'); box=im.getchannel('A').getbbox()
  if not box or box[0]<2 or box[1]<2 or box[2]>im.width-2 or box[3]>im.height-2: raise ValueError(f'Empty/clipped {spec["id"]} {f["file"]}: {box}')
  if im.getchannel('A').getextrema()[0]!=0: raise ValueError('Opaque background')
  if f['mode']=='icon': rect=(0,0,128,128)
  else: rect=(box[0]-1,box[1]-1,box[2]+1,box[3]+1)
  dest=a.output/'sprites'/spec['id']/f['file']; dest.parent.mkdir(parents=True,exist_ok=True)
  im.crop(rect).save(dest,optimize=True)
  spec['frames'].append(dict(file=dest.relative_to(a.output).as_posix(),mode=f['mode'],angle_degrees=f['angle_degrees'],size_px=[rect[2]-rect[0],rect[3]-rect[1]],anchor_px=[f['anchor_px'][0]-rect[0],f['anchor_px'][1]-rect[1]],source_canvas_px=f['canvas_px'],crop_rect_px=list(rect)))
 spec['ground_bounds_m']=record['ground_bounds_m']; spec['source_hash']=record['source_hash']; result.append(spec)
manifest=dict(schema=1,tile_px=[80,40],style='ll_worn_residential_v1',ground_anchor_px=[128,192],blender=batch['blender'],source_hash=batch['source_hash'],objects=result)
(a.output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',11) if Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf').exists() else ImageFont.load_default()
for page in range(math.ceil(len(result)/30)):
 group=result[page*30:(page+1)*30]; sheet=Image.new('RGB',(1200,math.ceil(len(group)/6)*190),(32,38,36)); draw=ImageDraw.Draw(sheet)
 for i,spec in enumerate(group):
  x=(i%6)*200; y=(i//6)*190
  draw.rectangle((x+3,y+3,x+196,y+186),fill=(45,52,48))
  icon=next(f for f in spec['frames'] if f['mode']=='icon'); im=Image.open(a.output/icon['file']); sheet.paste(im,(x+36,y+4),im)
  draw.text((x+7,y+131),spec['name'],font=font,fill=(222,216,194))
  # Full stable ID wraps, never truncated out of review evidence.
  idtext=spec['id']; parts=[idtext[j:j+27] for j in range(0,len(idtext),27)]
  for line,t in enumerate(parts): draw.text((x+7,y+148+line*13),t,font=font,fill=(155,176,161))
 sheet.save(a.sheets/f'contact_{page+1:02}.jpg',quality=90)
# Representative ground scale review: all at 1:1 on 80x40 diamonds.
selected=[s for s in result if s['name'] in __import__('catalog').REPRESENTATIVE_NAMES]
sheet=Image.new('RGB',(1200,math.ceil(len(selected)/5)*220),(32,38,36)); draw=ImageDraw.Draw(sheet)
for i,spec in enumerate(selected):
 x=(i%5)*240+120; y=(i//5)*220+165
 draw.polygon([(x,y-20),(x+40,y),(x,y+20),(x-40,y)],fill=(69,79,68),outline=(112,122,99))
 f=next(f for f in spec['frames'] if f['mode']=='ground'); im=Image.open(a.output/f['file']); sheet.paste(im,(x-f['anchor_px'][0],y-f['anchor_px'][1]),im)
 draw.text((x-110,y+28),spec['name'],font=font,fill=(222,216,194))
sheet.save(a.sheets/'ground_scale.png')
print(f'PACKED {len(result)} objects, {sum(len(s["frames"]) for s in result)} frames')
carried=[s for s in selected if s['visible_carry']]
if carried:
 sheet=Image.new('RGB',(1280,len(carried)*200),(32,38,36)); draw=ImageDraw.Draw(sheet)
 for row,spec in enumerate(carried):
  for col,f in enumerate(f for f in spec['frames'] if f['mode']=='held'):
   x=col*160+80; y=row*200+130
   im=Image.open(a.output/f['file']); sheet.paste(im,(x-f['anchor_px'][0],y-f['anchor_px'][1]),im)
   draw.ellipse((x-2,y-2,x+2,y+2),fill=(220,180,120))
   draw.text((x-73,y+20),spec['name'],font=font,fill=(222,216,194))
   draw.text((x-73,y+37),str(f['angle_degrees'])+' deg / grip',font=font,fill=(155,176,161))
 sheet.save(a.sheets/'held_directions.png')
