"""Fail closed on role, source, projection, pivot, footprint or support mismatch."""
import hashlib,json,math
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[2]
def validate(doc,root=ROOT):
 errors=[];seen=set();root=root.resolve()
 for path,expected in doc.get('source_hashes',{}).items():
  source=(root/path).resolve()
  if not source.is_relative_to(root) or not source.is_file() or hashlib.sha256(source.read_bytes()).hexdigest()!=expected:errors.append('stale_source:'+path)
 if doc.get('schema')!='last-light.world-art.v1':errors.append('unsupported_schema')
 p=doc.get('projection',{})
 if p.get('tile_px')!=[80,40] or p.get('half_tile_px')!=[40,20] or p.get('world_zoom_applications')!=1:errors.append('projection_contract')
 for r in doc.get('assets',[]):
  id=r.get('definition_id');prefix=str(id)+':'
  if not isinstance(id,str) or id in seen:errors.append(prefix+'duplicate_or_invalid_id')
  seen.add(id)
  path=r.get('world_sprite_path')
  if not path:
   if r.get('world_asset_id') is not None or r.get('world_state')!='world_view_missing_temporary_marker':errors.append(prefix+'inconsistent_missing_view')
   if not 0<float(r.get('marker_radius_px',0))<=3:errors.append(prefix+'oversized_marker')
   continue
  if id.startswith('ll_golden_') or '/golden40/' in path or Path(path).name!='ground.png':errors.append(prefix+'icon_cannot_be_world_art')
  source=(root/path).resolve()
  if not source.is_relative_to(root) or not source.is_file():errors.append(prefix+'missing_or_external_path');continue
  if hashlib.sha256(source.read_bytes()).hexdigest()!=r.get('sha256'):errors.append(prefix+'source_hash')
  dims=r.get('dimensions_m');foot=r.get('ground_footprint_m')
  if not isinstance(dims,list) or len(dims)!=3 or any(not isinstance(n,(float,int)) or not math.isfinite(n) or n<=0 for n in dims):errors.append(prefix+'dimensions')
  if not isinstance(foot,list) or len(foot)!=2 or any(not isinstance(n,(float,int)) or not math.isfinite(n) or n<=0 for n in foot):errors.append(prefix+'footprint')
  if not r.get('available_facings') or r.get('facing') not in r['available_facings']:errors.append(prefix+'unsupported_facing')
  with Image.open(source) as image:
   image.load()
   if image.mode!='RGBA' or image.getchannel('A').getbbox() is None:errors.append(prefix+'alpha')
   if image.getchannel('A').getextrema()[0]!=0:errors.append(prefix+'opaque_plate')
   crop=r.get('crop_rect_px',[]);canvas=r.get('source_canvas_px',[]);anchor=r.get('anchor_px',[])
   if len(crop)!=4 or len(canvas)!=2 or len(anchor)!=2:errors.append(prefix+'crop_anchor_metadata');continue
   if (crop[2]-crop[0],crop[3]-crop[1])!=image.size or not (0<=crop[0]<crop[2]<=canvas[0] and 0<=crop[1]<crop[3]<=canvas[1]):errors.append(prefix+'crop_dimensions')
   # Cropping preserves the factory source contact at [128,192].
   if [anchor[0]+crop[0],anchor[1]+crop[1]]!=[128,192] or anchor!=r.get('contact_px'):errors.append(prefix+'contact_pivot')
 return errors
if __name__=='__main__':
 doc=json.loads((ROOT/'data/world_art_manifest.json').read_text());errors=validate(doc)
 print(json.dumps({'records':len(doc['assets']),'errors':errors,'visual_approval':False},indent=2));raise SystemExit(bool(errors))
