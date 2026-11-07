"""Adapt existing original assets; never convert inventory pixels into world views.
Run from project root. Deterministic metadata only. Originals stay unchanged.
"""
import hashlib,json,csv,io
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def build():
 factory=json.loads((ROOT/'assets/generated/factory/manifest.json').read_text());gold=json.loads((ROOT/'assets/last_light/golden40/manifest.json').read_text());layout=json.loads((ROOT/'data/house_layout.json').read_text())
 needed={r['asset_id'] for r in layout['furniture']+layout['decorations']}
 needed.update(r['art_id'] for r in json.loads((ROOT/'data/survival_items.json').read_text()).get('items',[]))
 rows=[];qc=[]
 def inspect(path,id,role):
  with Image.open(ROOT/path) as im:
   im.load();rgba=im.convert('RGBA');a=rgba.getchannel('A');bbox=a.getbbox();pix=rgba.load();bright=0;edge=0;opaque=0
   for y in range(im.height):
    for x in range(im.width):
     r,g,b,alpha=pix[x,y]
     if not alpha:continue
     opaque+=1
     perimeter=any(nx<0 or ny<0 or nx>=im.width or ny>=im.height or pix[nx,ny][3]<alpha for nx,ny in [(x-1,y),(x+1,y),(x,y-1),(x,y+1)])
     if perimeter:
      edge+=1
      if min(r,g,b)>210 and max(r,g,b)-min(r,g,b)<25:bright+=1
   status='manual_review_required_bright_edge' if bright else 'no_bright_edge_detected_visual_review_pending'
   qc.append(dict(asset_id=id,role=role,path=path,sha256=sha(ROOT/path),mode=im.mode,size=list(im.size),bbox=bbox,alpha_extrema=a.getextrema(),opaque_pixels=opaque,edge_pixels=edge,bright_edge_pixels=bright,status=status,rule='4-connected alpha-boundary; RGB minimum >210 and channel spread <25; white materials can legitimately trigger; not an art approval'))
   return status
 for item in factory['objects']:
  if item['id'] not in needed:continue
  frame=next(f for f in item['frames'] if f['mode']=='ground');path='assets/generated/factory/'+frame['file'];qcstatus=inspect(path,item['id'],'world')
  rows.append(dict(definition_id=item['id'],icon_asset_id=item['id'],world_asset_id=item['id'],world_state='existing_original_world_candidate',world_sprite_path=path,ground_footprint_m=item['dimensions_m'][:2],dimensions_m=item['dimensions_m'],tile_occupancy=item['collision']['footprint_m'],source_canvas_px=frame['source_canvas_px'],crop_rect_px=frame['crop_rect_px'],anchor_px=frame['anchor_px'],contact_px=frame['anchor_px'],draw_scale=1.0,facing='factory_authored_0',available_facings=['factory_authored_0'],z_height_m=0,render_layer='furniture' if item['category']=='furniture' else 'ground_prop',occlusion_group='ground_contact',shadow_profile='footprint_contact',alpha_qc_status=qcstatus,provenance=item['source'],approval_status='existing_original_candidate_not_newly_approved',sha256=sha(ROOT/path)))
 for item in gold['items']:
  path='assets/last_light/golden40/'+item['icon'];status=inspect(path,item['id'],'inventory_only')
  rows.append(dict(definition_id=item['id'],icon_asset_id=item['id'],icon_path=path,world_asset_id=None,world_sprite_path=None,world_state='world_view_missing_temporary_marker',ground_footprint_m=None,dimensions_m=None,tile_occupancy=None,source_canvas_px=None,crop_rect_px=None,anchor_px=None,contact_px=None,draw_scale=1.0,facing=None,available_facings=[],z_height_m=0,render_layer='ground_loot',occlusion_group='ground_contact',shadow_profile='none_for_test_marker',marker_radius_px=2.5,alpha_qc_status=status,provenance=item['source_provenance'],approval_status='founder_style_reference_only_world_not_approved',sha256=sha(ROOT/path)))
 bindings=[]
 support={0:'house.kitchen.counter',1:'house.kitchen.counter',2:'house.kitchen.counter',3:'house.kitchen.table',4:'house.kitchen.table',5:'house.kitchen.stove',6:'house.bedroom.nightstand',10:'house.living.coffee_table',11:'house.living.coffee_table',12:'house.living.bookcase',13:'house.living.bookcase',15:'house.bathroom.medicine',16:'house.bathroom.medicine',17:'house.bathroom.sink',18:'house.bathroom.tub',19:'house.bathroom.toilet'}
 # Actual object surfaces, not total heights: a shelf and toilet cistern differ.
 surfaces={'house.kitchen.counter':.81,'house.kitchen.table':.72,'house.kitchen.stove':.945,'house.bedroom.nightstand':.816,'house.living.coffee_table':.81,'house.living.bookcase':None,'house.bathroom.medicine':.85,'house.bathroom.sink':.864,'house.bathroom.toilet':None,'house.bathroom.tub':.495}
 for i,prop in enumerate(layout['decorations']):
  parent=support.get(i)
  bindings.append(dict(decoration_index=i,asset_id=prop['asset_id'],parent_support=parent,surface_height_m=surfaces.get(parent),legacy_height_px=prop.get('height',0),status='calibrated_support' if parent else ('unsupported_raised_prop_manual_review' if prop.get('height',0)>0 else 'ground_supported')))
 placements=[]
 by_id={r['definition_id']:r for r in rows}
 for item in layout['furniture']:
  asset=by_id[item['asset_id']];d=asset['dimensions_m'];scale=min(item['size'][0]/d[0],item['size'][1]/d[1]);fitted=item.get('render')=='fitted_bed'
  placements.append(dict(instance_id=item['id'],definition_id=item['asset_id'],world_asset_id=None if fitted else item['asset_id'],render_mode='legacy_fitted_procedural_candidate' if fitted else 'original_ground_sprite',ground_footprint_m=item['size'],dimensions_m=[*item['size'],29/48.989795] if fitted else [v*scale for v in d],native_dimensions_m=d,draw_scale=None if fitted else scale,world_contact_m=[item['pos'][i]+item['size'][i]*.5 for i in (0,1)],anchor_px=None if fitted else asset['anchor_px'],contact_px=None if fitted else asset['contact_px'],facing='existing_authored_view',render_layer='furniture',shadow_profile='footprint_contact',interaction_reach_face='existing_distance_to_rect_not_authored_front',approval_status='visual_review_required',known_issue='compact collision footprint is not realistic single-bed anatomy' if fitted else None))
 doc=dict(schema='last-light.world-art.v1',projection=dict(tile_px=[80,40],half_tile_px=[40,20],units='gameplay_metres',vertical_px_per_m=48.989795,world_zoom_applications=1),source_hashes={p:sha(ROOT/p) for p in ['assets/generated/factory/manifest.json','assets/last_light/golden40/manifest.json','data/house_layout.json']},assets=sorted(rows,key=lambda r:r['definition_id']),placements=placements,decoration_supports=bindings,limitations=['All Golden 40 world views unavailable: neutral markers only.','Legacy compact fitted-bed visual retains collision size and is not a realistic single bed.','Unsupported raised blanket/towel await furniture layout approval.','No new asset or device approval is inferred.'])
 (ROOT/'data/world_art_manifest.json').write_text(json.dumps(doc,indent=2)+'\n')
 out=ROOT/'docs/checkpoints/world-art';out.mkdir(parents=True,exist_ok=True);(out/'alpha_qc.json').write_text(json.dumps(qc,indent=2)+'\n')
 with (out/'alpha_qc.csv').open('w',newline='') as f:
  writer=csv.DictWriter(f,lineterminator='\n',fieldnames=['asset_id','role','path','sha256','bright_edge_pixels','status']);writer.writeheader();writer.writerows({k:r[k] for k in writer.fieldnames} for r in qc)
 print(json.dumps({'asset_records':len(rows),'golden_world_markers':40,'qc_records':len(qc),'bright_edge_flags':sum(r['bright_edge_pixels']>0 for r in qc)}))
if __name__=='__main__':build()
