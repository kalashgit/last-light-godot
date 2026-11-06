#!/usr/bin/env python3
"""Full official-source audit. Standard library + Pillow for private PNG checks.
No source pixels/HTML/scripts are copied to production outputs.
"""
import concurrent.futures,hashlib,json,os,re,time,tempfile,urllib.request,urllib.parse
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
CACHE=Path(os.environ.get('LL_RESEARCH_CACHE','/workspace/last_light_official_research'))
UA='LAST LIGHT catalog evidence audit; metadata only; original art separate'
def atomic(p,data):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);fd,tmp=tempfile.mkstemp(dir=p.parent,prefix='.audit-')
 try:
  with os.fdopen(fd,'wb') as stream:stream.write(data);stream.flush();os.fsync(stream.fileno())
  os.replace(tmp,p)
 finally:
  if os.path.exists(tmp):os.unlink(tmp)
def api(params):
 p={'format':'json','formatversion':2,**params};key=hashlib.sha256(json.dumps(p,sort_keys=True).encode()).hexdigest();f=CACHE/'api'/f'{key}.json'
 if f.exists():return json.loads(f.read_bytes())
 u='https://pzwiki.net/w/api.php?'+urllib.parse.urlencode(p)
 for retry in range(3):
  try:
   with urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':UA}),timeout=40) as r:data=r.read(24000000)
   j=json.loads(data)
   if 'error' in j:raise ValueError(j['error'])
   atomic(f,data);return j
  except Exception:
   if retry==2:raise
   time.sleep(retry+1)
def jwrite(p,v):atomic(p,(json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
def file_chunk(rows):
 names=['File:'+r['source_filename'] for r in rows];j=api({'action':'query','titles':'|'.join(names),'prop':'imageinfo|revisions|categories','iiprop':'url|size|sha1','rvprop':'ids|timestamp|content','rvslots':'main','cllimit':50})
 pages={p['title']:p for p in j['query']['pages']};out=[]
 for r in rows:
  p=pages.get('File:'+r['source_filename'],{});out.append({'reference_id':r['reference_id'],'catalog_index':r['catalog_index'],'api_page':p,'response_has_continuation':bool(j.get('continue'))})
 return out
def files():
 rows=json.loads((ROOT/'production/sprite_factory/catalog.json').read_text())['rows'];chunks=[rows[i:i+40] for i in range(0,len(rows),40)];result=[]
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
  fs={pool.submit(file_chunk,c):c for c in chunks}
  for f in concurrent.futures.as_completed(fs):
   try:result+=f.result()
   except Exception as e:
    result += [{'reference_id':r['reference_id'],'catalog_index':r['catalog_index'],'error':str(e)} for r in fs[f]]
   if len(result)%400<40:print('Official file records',len(result),'/',len(rows),flush=True)
 result.sort(key=lambda x:x['catalog_index']);jwrite(CACHE/'official_files.json',result);print('FILE CHECK COMPLETE',len(result),flush=True)
def list_items():
 p={'action':'query','list':'embeddedin','eititle':'Template:Infobox item','einamespace':0,'eilimit':500,'eifilterredir':'nonredirects'};allpages=[]
 while True:
  j=api(p);allpages+=j['query']['embeddedin'];print('Official infobox page discovery',len(allpages),flush=True)
  if 'continue' not in j:break
  p.update(j['continue'])
 result=[r for r in allpages if '/' not in r['title']];jwrite(CACHE/'item_page_index.json',result);print('English item pages',len(result),flush=True);return result
def article_chunk(rows):
 j=api({'action':'query','pageids':'|'.join(str(r['pageid']) for r in rows),'prop':'revisions','rvprop':'ids|timestamp|content','rvslots':'main'});return j['query']['pages']
def articles():
 rows=list_items();chunks=[rows[i:i+40] for i in range(0,len(rows),40)];done=0;errors=[]
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
  fs={pool.submit(article_chunk,c):c for c in chunks}
  for f in concurrent.futures.as_completed(fs):
   try:
    pages=f.result()
    for p in pages:jwrite(CACHE/'articles'/(str(p['pageid'])+'.json'),p)
    done+=len(pages)
   except Exception as e:errors.append({'pageids':[r['pageid'] for r in fs[f]],'error':str(e)})
   if done%400<40:print('Official item articles',done,'/',len(rows),flush=True)
 jwrite(CACHE/'article_fetch_summary.json',{'discovered':len(rows),'retrieved':done,'errors':errors});print('ARTICLE CHECK COMPLETE',done,'errors',len(errors),flush=True)

# Parse exact structured source facts. No fuzzy/keyword match can grant a binding.
def filename_key(value):
 import html,unicodedata
 value=unicodedata.normalize('NFC',html.unescape(value.strip().replace('_',' ')))
 if value.startswith('File:'):value=value[5:]
 return value[:1].upper()+value[1:]

def split_fields(body):
 fields=[];start=0;curly=square=0;i=0
 while i<len(body):
  pair=body[i:i+2]
  if pair=='{{':curly+=1;i+=2;continue
  if pair=='}}':curly-=1;i+=2;continue
  if pair=='[[':square+=1;i+=2;continue
  if pair==']]':square-=1;i+=2;continue
  if body[i]=='|' and curly==square==0:fields.append(body[start:i]);start=i+1
  i+=1
 fields.append(body[start:]);out={}
 for field in fields[1:]:
  if '=' in field:
   key,value=field.split('=',1);out[key.strip().lower()]=value.strip()
 return out

def infoboxes(text):
 text=re.sub(r'<!--.*?-->','',text,flags=re.S)
 for match in re.finditer(r'\{\{\s*Infobox[ _]+item\b',text,re.I):
  depth=1;i=match.end()
  while i<len(text)-1 and depth:
   if text[i:i+2]=='{{':depth+=1;i+=2
   elif text[i:i+2]=='}}':depth-=1;i+=2
   else:i+=1
  if not depth:yield split_fields(text[match.start()+2:i-2])

def plain(value):
 value=re.sub(r'\{\{(?:ll|l|Main)\|([^{}]*)\}\}',lambda m:m[1].split('|')[-1],value,flags=re.I)
 value=re.sub(r'\[\[([^\]]*)\]\]',lambda m:m[1].split('|')[-1],value)
 value=re.sub(r'<[^>]*>',' ',value).replace("'''",'').replace("''",'')
 return re.sub(r'\s+',' ',value).strip()

def article_bindings(page):
 revisions=page.get('revisions',[])
 if not revisions:return []
 rev=revisions[0];text=rev.get('slots',{}).get('main',{}).get('content','');sha=hashlib.sha256(text.encode()).hexdigest();rows=[]
 # Only the infobox's own icon fields establish identity, not illustrations in a recipe/history table.
 for box in infoboxes(text):
  ids=sorted({m for key,v in box.items() if re.fullmatch(r'item_id\d*',key) for m in re.findall(r'\b[A-Za-z][A-Za-z0-9_]*\.[A-Za-z0-9_]+\b',v)})
  script_icons={}
  for start in re.finditer(r'\bitem\s+([A-Za-z0-9_]+)\s*\{',text):
   depth=1;end=start.end()
   while end<len(text) and depth:
    if text[end]=='{':depth+=1
    elif text[end]=='}':depth-=1
    end+=1
   if depth:continue
   item_ids=[item for item in ids if item.rsplit('.',1)[-1]==start[1]]
   if not item_ids:continue
   body=text[start.end():end-1]
   for prop in re.finditer(r'^\s*(Icon|IconsForTexture)\s*=\s*([^\n]+)',body,re.M):
    for name in prop[2].strip().rstrip(',').split(';'):
     name=name.strip().strip('"')
     if not name or any(c in name for c in '{}[]=,'):continue
     key=filename_key(name if name.lower().endswith('.png') else name+'.png')
     script_icons.setdefault(key,set()).update(item_ids)
  for field,value in box.items():
   if not re.fullmatch(r'icon\d*',field):continue
   if not value.lower().endswith('.png') or any(c in value for c in '{}[]|\n'):continue
   suffix=field[4:]
   facts={key:plain(box[key]) for key in ['category','material','body_location','clothing_item','equipped'] if box.get(key)}
   matched_ids=sorted(script_icons.get(filename_key(value),[]))
   resolved_ids=matched_ids or ids
   rows.append({'icon_filename':value,'match_key':filename_key(value),'official_item_name':plain(box.get('name',page['title'])),'source_item_ids':resolved_ids,'all_infobox_item_ids':ids,'source_article_title':page['title'],'source_article_url':'https://pzwiki.net/wiki/'+urllib.parse.quote(page['title'].replace(' ','_')),'source_page_id':page['pageid'],'source_revision_id':rev.get('revid'),'source_revision_timestamp':rev.get('timestamp'),'context_sha256':sha,'icon_field':field,'icon_label':plain(box.get('icon_name'+suffix,'')),'icon_description':plain(box.get('icon_desc'+suffix,'')),'facts':facts,'binding_method':'exact_official_item_infobox_icon','script_icon_item_ids':matched_ids,'source_item_id_assignment':'single_exact_script_icon' if len(matched_ids)==1 else 'single' if len(resolved_ids)==1 else 'multiple_ids_not_assigned_to_individual_icon'})
 return rows

def analyze(source,file_record,image,bindings,manual=None):
 page=file_record.get('api_page',{});info=page.get('imageinfo',[{}])[0];reasons=[]
 # Original intake is retained in full. New official facts supplement it.
 row={'catalog_index':source['catalog_index'],'reference_id':source['reference_id'],'authoritative_source_record':source,'official_icon_filename':source['source_filename'],'source_page_url':source['source_page_url'],'source_image_url':source['source_image_url'],'official_bindings':bindings,'image_check':image,'official_file_check':{'page_id':page.get('pageid'),'current_title':page.get('title'),'exists':bool(page.get('pageid')) and not page.get('missing'),'source_dimensions':[info.get('width'),info.get('height')],'source_sha1':info.get('sha1'),'categories':[x['title'] for x in page.get('categories',[])],'metadata_error':file_record.get('error')},'review_kind':'automated_official_metadata_crosscheck','actual_visual_approval':False,'new_art_generated':False,'factory_render_ready':False}
 if not row['official_file_check']['exists']:reasons.append('official_file_missing_or_unavailable')
 if image.get('status')!='decoded_source_image':reasons.append('source_image_unavailable_or_invalid')
 elif [image.get('width'),image.get('height')]!=row['official_file_check']['source_dimensions']:reasons.append('served_image_dimensions_disagree_with_official_record')
 if bindings:
  titles={b['source_article_title'] for b in bindings}
  ids={item for b in bindings for item in b['source_item_ids']}
  if len(titles)>1:reasons.append('icon_shared_by_multiple_official_item_articles')
  elif not ids:reasons.append('official_infobox_has_no_item_id')
  elif len(ids)>1:reasons.append('multiple_official_item_ids_need_per_icon_state_variant_mapping')
  row['official_binding_status']='exact_icon_link_found'
 else:
  reasons.append('no_exact_official_infobox_icon_binding');row['official_binding_status']='unresolved'
 if manual and manual.get('classification_status')=='identity_verified':
  row['prior_inspected_identity']={k:manual[k] for k in ['identity_key','logical_item_id','disposition','identity_review']}
  row['source_identity_status']='previously_visually_and_context_verified'
 else:row['source_identity_status']='automated_exact_binding_candidate' if not reasons else 'review_required'
 row['blocking_reasons']=reasons
 row['next_stage']='independent_art_brief_and_original_master_required' if not reasons else 'source_context_review_required'
 row['ready_for_brief_draft']=not reasons
 row['canonical_item_id']=manual.get('logical_item_id') if manual and manual.get('classification_status')=='identity_verified' else None
 row['art_requirements']={'canvas':[64,64],'format':'transparent_RGBA_PNG','style':'MASTER_SPRITE_BIBLE_V2_founder_approved_V4_processing','pixel_source':'independently_authored_original_only','geometry':'must_be_authored_for_exact_verified_identity','state_and_variant_mapping':'requires_review','world_and_held_views':'separately_authored_when_needed'}
 return row

def report(output):
 from collections import Counter,defaultdict
 out=Path(output);out.mkdir(parents=True,exist_ok=True)
 sources=json.loads((ROOT/'production/sprite_factory/catalog.json').read_text())['rows'];files_by_id={r['reference_id']:r for r in json.loads((CACHE/'official_files.json').read_text())};images={r['reference_id']:r for r in json.loads((CACHE/'image_checks.json').read_text())}
 manual={r['reference_id']:r for r in (json.loads(line) for line in (ROOT/'production/source_identity/ledger.jsonl').read_text().splitlines())};index=defaultdict(list)
 for path in sorted((CACHE/'articles').glob('*.json')):
  for b in article_bindings(json.loads(path.read_text())):index[b['match_key']].append(b)
 rows=[analyze(s,files_by_id.get(s['reference_id'],{}),images.get(s['reference_id'],{}),index.get(filename_key(s['source_filename']),[]),manual.get(s['reference_id'])) for s in sources]
 assert len(rows)==4347 and len({r['reference_id'] for r in rows})==4347
 # Do not silently collapse identical pictures into logical objects; queue duplicate flags separately.
 identical=defaultdict(list)
 for row in rows:
  image=row['image_check']
  if image.get('pixel_sha256'):identical[(image['width'],image['height'],image['pixel_sha256'])].append(row['reference_id'])
 groups=[ids for ids in identical.values() if len(ids)>1]
 for row in rows:
  image=row['image_check'];key=(image.get('width'),image.get('height'),image.get('pixel_sha256'))
  row['identical_pixel_references']=[ref for ref in identical.get(key,[]) if ref!=row['reference_id']]
 def jsonl(name,values):atomic(out/name,(''.join(json.dumps(r,sort_keys=True,ensure_ascii=False)+'\n' for r in values)).encode())
 jsonl('readiness_manifest.jsonl',rows)
 ready=[r for r in rows if r['ready_for_brief_draft']]
 drafts=[]
 for r in ready:
  b=r['official_bindings'][0]
  drafts.append({'source_reference_id':r['reference_id'],'official_source_filename':r['official_icon_filename'],'official_item_name':b['official_item_name'],'source_item_ids':b['source_item_ids'],'source_article_url':b['source_article_url'],'source_context_sha256':b['context_sha256'],'draft_brief':'Independently design one '+b['official_item_name']+' representing this exact official source record. Preserve its functional identity; choose original construction, packaging and pixel composition. State/view/material details require independent art-direction review.','status':'identity_bound_brief_draft_requires_art_design','factory_render_ready':False,'source_pixels_may_be_used_as_art':False,'canonical_item_id':r['canonical_item_id'],'required_unresolved_fields':['reviewed_physical_parts','original_geometry','verified_state_view','material_assignment','original_art_master','visual_identity_QA']})
 jsonl('identity_bound_brief_drafts.jsonl',drafts)
 jsonl('exceptions.jsonl',[r for r in rows if r['blocking_reasons']])
 remaining={ref for ref,r in manual.items() if r['classification_status']!='identity_verified'}
 write={'total_source_records':len(rows),'official_file_checks_completed':len(files_by_id),'source_png_checks_completed':len(images),'valid_source_pngs':sum(r['image_check'].get('status')=='decoded_source_image' for r in rows),'source_fetch_failures':sum(r['image_check'].get('status')!='decoded_source_image' for r in rows),'exact_official_icon_bindings_found':sum(bool(r['official_bindings']) for r in rows),'identity_bound_brief_drafts':len(drafts),'source_exceptions':sum(bool(r['blocking_reasons']) for r in rows),'requested_remaining_records_automatically_checked':len(remaining),'remaining_identity_bound_brief_drafts':sum(r['ready_for_brief_draft'] and r['reference_id'] in remaining for r in rows),'remaining_source_exceptions':sum(bool(r['blocking_reasons']) and r['reference_id'] in remaining for r in rows),'prior_actual_visual_identity_reviews_verified':sum(r['source_identity_status']=='previously_visually_and_context_verified' for r in rows),'new_actual_visual_identity_approvals':0,'original_master_templates_in_V4':24,'new_original_art_generated':0,'new_factory_render_ready_records':0,'identical_source_pixel_groups':len(groups),'blocking_reason_counts':dict(Counter(x for r in rows for x in r['blocking_reasons'])),'catalog_sha256':hashlib.sha256((ROOT/'production/sprite_factory/catalog.json').read_bytes()).hexdigest(),'readiness_manifest_sha256':hashlib.sha256((out/'readiness_manifest.jsonl').read_bytes()).hexdigest(),'method':'Exact official item infobox icon fields plus item IDs, source file metadata and decoded PNG integrity. Automated source crosscheck; not human-level semantic/visual approval.'}
 jwrite(out/'dashboard.json',write);jwrite(out/'identical_source_pixel_groups.json',groups)
 batches=[]
 for i in range(0,len(rows),20):batches.append({'batch_id':'LL-SOURCE-CHECK-%04d'%(i//20+1),'reference_ids':[r['reference_id'] for r in rows[i:i+20]],'source_range':[rows[i]['catalog_index'],rows[min(i+19,len(rows)-1)]['catalog_index']],'status':'automated_checked_visual_review_pending'})
 jwrite(out/'batches.json',batches);print(json.dumps(write,indent=2));return rows

def fetch_images():
 import io
 from PIL import Image
 images=CACHE/'images';images.mkdir(exist_ok=True)
 def job(r):
  p=images/(str(r['catalog_index'])+'.png');m=p.with_suffix('.json');meta={k:r[k] for k in ['reference_id','catalog_index','source_filename','source_image_url']}
  try:
   if p.exists() and m.exists():
    try:
     old=json.loads(m.read_text());data=p.read_bytes()
     if old.get('status')=='decoded_source_image' and old.get('source_image_url')==r['source_image_url'] and old.get('sha256')==hashlib.sha256(data).hexdigest():return old
    except (ValueError,OSError):pass
   u=urllib.parse.quote(r['source_image_url'],safe=':/_%')
   with urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'LAST LIGHT catalog evidence research'}),timeout=25) as res:data=res.read(4*1024*1024+1)
   if len(data)>4*1024*1024:raise ValueError('Research image too large')
   with Image.open(io.BytesIO(data)) as im:
    im.load();rgba=im.convert('RGBA');meta.update(width=im.width,height=im.height,format=im.format,mode=im.mode,alpha_bbox=rgba.getchannel('A').getbbox(),pixel_sha256=hashlib.sha256(rgba.tobytes()).hexdigest())
   tmp=p.with_suffix('.tmp');tmp.write_bytes(data);os.replace(tmp,p)
   meta.update(sha256=hashlib.sha256(data).hexdigest(),bytes=len(data),status='decoded_source_image')
  except Exception as e:meta.update(status='source_fetch_failed',error=str(e))
  jwrite(m,meta);return meta
 rows=json.loads((ROOT/'production/sprite_factory/catalog.json').read_text())['rows'];out=[]
 with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
  for meta in pool.map(job,rows):
   out.append(meta)
   if len(out)%400==0:print('Source icon checks',len(out),'/',len(rows),flush=True)
 jwrite(CACHE/'image_checks.json',out)
 print('IMAGE CHECK COMPLETE',len(out),'decoded',sum(x['status']=='decoded_source_image' for x in out),flush=True)
 return out

def main():
 import argparse
 parser=argparse.ArgumentParser(description='Audit every official source; no reference pixels become game art.')
 parser.add_argument('command',choices=['fetch-official','fetch-images','report']);parser.add_argument('--cache',type=Path,required=True);parser.add_argument('--output',type=Path,default=ROOT/'production/catalog_readiness')
 args=parser.parse_args();global CACHE;CACHE=args.cache.resolve()
 if CACHE==ROOT or ROOT in CACHE.parents:parser.error('Research cache must stay outside the repository')
 CACHE.mkdir(parents=True,exist_ok=True)
 if args.command=='fetch-official':
  with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
   jobs=[pool.submit(files),pool.submit(articles)]
   for job in jobs:job.result()
 elif args.command=='fetch-images':fetch_images()
 else:report(args.output)
if __name__=='__main__':main()
