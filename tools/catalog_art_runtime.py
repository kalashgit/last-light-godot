"""Embedded original catalog candidates: no reference art or production promotion."""
import base64,hashlib,io,json,os,tempfile,zipfile
from pathlib import Path

def atomic(path,data):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);fd,tmp=tempfile.mkstemp(dir=path.parent)
 try:
  with os.fdopen(fd,'wb') as f:f.write(data);f.flush();os.fsync(f.fileno())
  os.replace(tmp,path)
 finally:
  if os.path.exists(tmp):os.unlink(tmp)

def export(pack,base,renderer):
 folder=Path(base)/'catalog_candidates'/pack['batch_id'];records=[];generated=resumed=0
 ids=set();refs=set();paths=set()
 # Validate the whole batch before writing any output.
 for asset in pack['assets']:
  record=asset['record'];ref=record['reference_id'];logical=record['logical_item_id']
  if logical in ids or ref in refs:raise ValueError('Duplicate catalog identity')
  ids.add(logical);refs.add(ref)
  if record['visual_qa']['decision']!='PASS_CANDIDATE' or record['visual_qa']['reviewed_sha256']!=record['sha256']:raise ValueError('Candidate visual gate missing/hash changed')
  if not record['identity_review']['actual_source_pixels_inspected'] or not record['identity_review']['official_context_inspected']:raise ValueError('Source identity review missing')
  data=base64.b64decode(asset['png'])
  if hashlib.sha256(data).hexdigest()!=record['sha256']:raise ValueError('Original candidate hash mismatch')
  with renderer.Image.open(io.BytesIO(data)) as im:
   qa=renderer.technical_qa(im)
  if not qa['passed']:raise ValueError('Candidate PNG technical gate failed')
  path=folder/'art/items'/record['family']/record['design']/'icon.png'
  if path in paths:raise ValueError('Conflicting export path')
  paths.add(path)
 for i,asset in enumerate(pack['assets'],1):
  record=dict(asset['record']);data=base64.b64decode(asset['png'])
  path=folder/'art/items'/record['family']/record['design']/'icon.png';sidecar=path.with_name('asset.json')
  if path.exists() and hashlib.sha256(path.read_bytes()).hexdigest()==record['sha256']:resumed+=1
  elif path.exists():
   previous=json.loads(sidecar.read_text()) if sidecar.exists() else {}
   if previous.get('founder_approved') or previous.get('production_status')=='founder_approved':raise PermissionError('Approved catalog art is immutable')
   if previous.get('sha256')!=record['sha256']:raise FileExistsError('Unmanaged/changed candidate is preserved: '+str(path))
   atomic(folder/'rework_history'/record['design']/('corrupt_'+hashlib.sha256(path.read_bytes()).hexdigest()+'.png'),path.read_bytes())
   atomic(path,data);generated+=1
  else:atomic(path,data);generated+=1
  record.update(relative_path=str(path.relative_to(folder)),source_reference_ids=[record['reference_id']],production_status='visual_review_required',founder_approved=False,base_dir=str(folder),qa_status='technical_qa_passed')
  if sidecar.exists():
   try:prior=json.loads(sidecar.read_text())
   except ValueError:prior={}
   if prior.get('founder_approved'):
    raise PermissionError('Approved sidecar preserved; candidate exporter cannot change approval records')
  atomic(sidecar,(json.dumps(record,indent=2)+'\n').encode());records.append(record)
  print('Catalog candidate',i,'/',len(pack['assets']),record['official_item_name'])
 atomic(folder/'manifest.jsonl',''.join(json.dumps(r,sort_keys=True)+'\n' for r in records).encode())
 sheets=renderer.make_review_sheets(records,folder/'review_sheets','catalog20')
 archive=folder/'catalog20_candidates.zip';fd,tmp=tempfile.mkstemp(dir=folder);os.close(fd)
 try:
  with zipfile.ZipFile(tmp,'w',zipfile.ZIP_DEFLATED) as z:
   for r in records:
    p=folder/r['relative_path'];z.write(p,p.relative_to(folder));z.write(p.with_name('asset.json'),p.with_name('asset.json').relative_to(folder))
   z.write(folder/'manifest.jsonl','manifest.jsonl')
  with zipfile.ZipFile(tmp) as z:
   if z.testzip():raise ValueError('Candidate ZIP verification failed')
  os.replace(tmp,archive)
 finally:
  if os.path.exists(tmp):os.unlink(tmp)
 return {'catalog_candidate_pngs':len(records),'new_catalog_sprites_generated':generated,'resumed':resumed,'technical_qa_passes':len(records),'independent_visual_candidate_passes':len(records),'founder_approvals':0,'production_promotions':0,'manifest_path':str(folder/'manifest.jsonl'),'review_sheets':sheets,'zip_path':str(archive)}
