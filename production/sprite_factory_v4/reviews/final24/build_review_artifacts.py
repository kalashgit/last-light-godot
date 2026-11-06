"""Rebuild diagnostics/comparison boards from frozen reviewed PNGs; never render/copy Golden pixels into production icons."""
import colorsys,hashlib,json,math,shutil,statistics
from pathlib import Path
from PIL import Image,ImageDraw
repo=Path(__file__).resolve().parents[4];root=repo/'production/sprite_factory_v4';out=root/'reviews/final24';gold=repo/'assets/last_light/golden40'
rows=[json.loads(x) for x in (out/'manifest_snapshot.jsonl').read_text().splitlines()]
refs=json.loads((gold/'manifest.json').read_text())['items'];refbyid={r['id']:r for r in refs}
# Material/construction analogues only. Differing objects are explicitly not silhouette targets.
analogs=[('aerosol_canister','curved steel and wrapped label'),('aerosol_canister','curved steel and wrapped label'),('acorn','organic volume; different species'),('acorn','organic volume; different species'),('ammunition_case','lid seam and case hardware'),('ammo_box_40cal','folded matte carton'),('hand_axe','forged metal joined to wood'),('basic_mace','metal head joined to wood'),('hunting_knife','metal shaft/blade and constructed grip'),('pocket_knife','metal shaft/blade and constructed grip'),('butterfly_knife_folded','machined metal joints'),('crowbar','painted steel'),('baseball_bat','directional wood grain'),('aluminum_ingot','solid metal stock; different alloy'),('air_filter_tape','wound roll/core construction'),('stone_axe','rope binding/fiber; different assembly'),('field_pack_olive','loaded sewn canvas pack'),('field_pack_sand','sewn canvas volume; different bag design'),('hunting_knife','leather handle cues; different object'),('field_pack_olive','woven cloth shading; different fabric construction'),('digital_alarm_clock','molded dark housing and controls'),('aerosol_canister','curved metal thickness; different object'),('isopropyl_alcohol','translucent bottle thickness'),('aerosol_canister','curved metal and rolled rims; different object')]
assert len(rows)==len(analogs)==24
for r in rows:
 p=out/(r['logical_item_id'].split('.')[-1]+'.png')
 if hashlib.sha256(p.read_bytes()).hexdigest()!=r['sha256']:raise ValueError('Frozen review snapshot hash mismatch: '+str(p))
base=[json.loads(x) for x in (root/'baseline/manifest_range_000000000_000000024.jsonl').read_text().splitlines()];basebyid={x['logical_item_id']:x for x in base}
comp=[]
for i,(r,(refslug,reason)) in enumerate(zip(rows,analogs),1):
 gr=refbyid['ll_golden_'+refslug];br=basebyid[r['logical_item_id']];slug=r['logical_item_id'].split('.')[-1]
 comp.append({'index':i,'logical_item_id':r['logical_item_id'],'golden_reference_id':gr['id'],'golden_reference_index':refs.index(gr)+1,'comparison_basis':reason,'paths':[gold/gr['icon'],root/'baseline/output'/br['relative_path'],out/(slug+'.png')],'original_v4_path':r['relative_path'],'manifest_sha256':r['sha256'],'generator_version':r['generator_version']})
for size in [32,48,64,192]:
 cw=max(220,3*size+24);ch=size+48;board=Image.new('RGB',(3*cw,8*ch),(38,42,46));d=ImageDraw.Draw(board)
 for i,r in enumerate(comp):
  bx=i%3*cw;by=i//3*ch;d.text((bx+5,by+3),f'{i+1:02d} '+r['logical_item_id'].split('.')[-1],fill=(232,231,220))
  centers=[cw/6,cw/2,5*cw/6]
  for j,path in enumerate(r['paths']):
   with Image.open(path) as im:icon=im.convert('RGBA').resize((size,size),Image.Resampling.NEAREST)
   x=round(bx+centers[j]-size/2);y=by+30;board.paste(icon,(x,y),icon);d.text((x,by+17),f'G{r["golden_reference_index"]:02d}' if j==0 else ('V3' if j==1 else 'V4'),fill=(205,207,198))
 board.save(out/(f'golden_v3_v4_native{size}.png' if size<100 else 'golden_v3_v4_nearest3x.png'))

def metrics(path):
 with Image.open(path) as original:im=original.convert('RGBA')
 pixels=list(im.getdata());rgb=[p[:3] for p in pixels if p[3]>=230];lum=sorted(.2126*r+.7152*g+.0722*b for r,g,b in rgb);sats=sorted(colorsys.rgb_to_hsv(r/255,g/255,b/255)[1] for r,g,b in rgb)
 def percentile(a,p):return round(a[min(len(a)-1,round((len(a)-1)*p))],4)
 pix=im.load();seen=set();clusters=[];opaque=sum(p[3]>=230 for p in pixels)
 for y in range(im.height):
  for x in range(im.width):
   if (x,y) in seen or pix[x,y][3]<230:continue
   color=pix[x,y][:3];stack=[(x,y)];seen.add((x,y));n=0
   while stack:
    xx,yy=stack.pop();n+=1
    for nx,ny in [(xx-1,yy),(xx+1,yy),(xx,yy-1),(xx,yy+1)]:
     if 0<=nx<im.width and 0<=ny<im.height and (nx,ny) not in seen and pix[nx,ny][3]>=230 and pix[nx,ny][:3]==color:seen.add((nx,ny));stack.append((nx,ny))
   clusters.append(n)
 bounds=im.getchannel('A').getbbox();vals={'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'dimensions':list(im.size),'alpha_bounds':list(bounds),'occupied_alpha_fraction':round(sum(p[3]>0 for p in pixels)/len(pixels),5),'nearly_opaque_pixels':opaque,'partial_alpha_fraction':round(sum(0<p[3]<255 for p in pixels)/len(pixels),5),'opaque_unique_colors':len(set(rgb)),'srgb_luminance_p05':percentile(lum,.05),'srgb_luminance_p50':percentile(lum,.5),'srgb_luminance_p95':percentile(lum,.95),'hsv_saturation_p50':percentile(sats,.5),'exact_rgb_cluster_count':len(clusters),'singleton_pixel_fraction':round(sum(n==1 for n in clusters)/opaque,5),'largest_exact_color_cluster_fraction':round(max(clusters)/opaque,5)}
 return vals
metricsets={}
for name,paths in [('golden40',[(r['id'],gold/r['icon']) for r in refs]),('v3',[(r['logical_item_id'],root/'baseline/output'/r['relative_path']) for r in base]),('v4',[(r['logical_item_id'],out/(r['logical_item_id'].split('.')[-1]+'.png')) for r in rows])]:
 metricsets[name]=[dict(id=ident,**metrics(path)) for ident,path in paths]
summary={}
for name,arr in metricsets.items():
 summary[name]={'count':len(arr),'medians':{k:round(statistics.median(r[k] for r in arr),5) for k in ['occupied_alpha_fraction','partial_alpha_fraction','opaque_unique_colors','srgb_luminance_p05','srgb_luminance_p50','srgb_luminance_p95','hsv_saturation_p50','singleton_pixel_fraction','largest_exact_color_cluster_fraction']}}
meta={'schema_version':1,'method':'Native64 PNG samples with alpha>=230; sRGB weighted luminance (diagnostic, not physical linear light); HSV saturation; exact RGB 4-connected cluster counting.','limitations':['Golden40 exports contain resampling/JPEG-derived matte artifacts. Color counts and singleton clusters cannot be treated as a Golden target.','Different objects and material proportions make aggregate distributions descriptive only.','Metrics do not prove style, object correctness, originality or visual approval.'],'summary':summary,'sets':metricsets}
(out/'visual_diagnostics.json').write_text(json.dumps(meta,indent=2)+'\n')
for r in comp:r['paths']=[str(p.relative_to(repo)) for p in r['paths']]
(out/'comparison_map.json').write_text(json.dumps(comp,indent=2)+'\n')
print(json.dumps(summary,indent=2))
