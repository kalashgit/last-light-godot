"""Rebuild comparisons/diagnostics from frozen hybrid candidates. No production artwork is generated or modified."""
import colorsys,hashlib,json,math,shutil,statistics
from pathlib import Path
from PIL import Image,ImageDraw
repo=Path(__file__).resolve().parents[4];root=repo/'production/sprite_factory_v4';out=root/'reviews/hybrid24';gold=repo/'assets/last_light/golden40'
rows=[json.loads(x) for x in (out/'manifest_snapshot.jsonl').read_text().splitlines()]
refs=json.loads((gold/'manifest.json').read_text())['items'];refbyid={r['id']:r for r in refs}
# Golden references are a separate style board, never per-item identity targets.
import sys
sys.path.insert(0,str(repo/'tools'))
from build_identity_safe_comparisons import build_comparisons
base=[json.loads(x) for x in (root/'baseline/manifest_range_000000000_000000024.jsonl').read_text().splitlines()]
comp=build_comparisons(out)

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
