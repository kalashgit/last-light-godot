#!/usr/bin/env python3
"""Package the unchanged working renderer and audited catalog into one phone file."""
import base64,hashlib,zlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
TEMPLATE=r'''"""LAST LIGHT master — approved V4 demo renderer + source-design queue.
Pillow + Python standard library. Contains 24 completed sprite designs and 2,745
remaining source-linked brief drafts. New artwork recipes are still required.
"""
import argparse,base64,hashlib,json,os,sys,tempfile,types,zlib
from pathlib import Path
CUSTOM_WORK_FOLDER = ''  # Set an optional persistent CodePad Documents/Files folder.
DEFAULT_ACTION = 'setup_and_demo'
RENDERER_SHA256 = '@RENDER_SHA@'
CATALOG_CHECKER_SHA256 = '@CHECK_SHA@'
_RENDERER = '@RENDER@'
_CHECKER = '@CHECK@'

def component(name,payload,expected):
    raw=zlib.decompress(base64.b64decode(payload))
    if hashlib.sha256(raw).hexdigest()!=expected:raise ValueError('Embedded component integrity failure: '+name)
    module=types.ModuleType(name);module.__file__=str(Path(__file__).resolve());sys.modules[name]=module
    exec(compile(raw,name+'.py','exec'),module.__dict__)
    return module

def renderer():return component('_last_light_master_renderer',_RENDERER,RENDERER_SHA256)
def checker():return component('_last_light_master_catalog',_CHECKER,CATALOG_CHECKER_SHA256)

def durable_export(folder,name,lines):
    """Preserve edited queues; store a versioned replacement rather than overwrite."""
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
    fd,temp=tempfile.mkstemp(dir=folder,prefix='.queue-')
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as stream:
            for line in lines:stream.write(line+'\n')
            stream.flush();os.fsync(stream.fileno())
        new_hash=hashlib.sha256(Path(temp).read_bytes()).hexdigest()
        target=folder/name
        if target.exists():
            if hashlib.sha256(target.read_bytes()).hexdigest()==new_hash:return str(target)
            version=1
            while target.exists():
                target=folder/(Path(name).stem+'.v%03d'%version+Path(name).suffix);version+=1
        os.replace(temp,target);return str(target)
    finally:
        if os.path.exists(temp):os.unlink(temp)

def brief_lines(catalog):
    for raw in catalog.lines():
        row=json.loads(raw)
        if not row['ready_for_brief_draft'] or row['source_identity_status']=='previously_visually_and_context_verified':continue
        bindings=row['official_bindings']
        yield json.dumps({'source_reference_ids':[row['reference_id']],'catalog_index':row['catalog_index'],
            'official_source_filename':row['official_icon_filename'],
            'official_item_names':sorted({b['official_item_name'] for b in bindings}),
            'official_item_ids':sorted({v for b in bindings for v in b['source_item_ids']}),
            'source_article_urls':sorted({b['source_article_url'] for b in bindings}),
            'source_image_url':row['source_image_url'],
            'source_context_sha256':sorted({b['context_sha256'] for b in bindings}),
            'art_requirements':row['art_requirements'],
            'status':'needs_original_art_recipe','factory_render_ready':False,
            'instruction':'Author original geometry/art for this exact verified source identity using the approved V4 process. Do not relabel another object or use research pixels as artwork.'},sort_keys=True)

def run(output='',action=DEFAULT_ACTION,recipes='',classification=''):
    if action not in ('setup_and_demo','catalog_only','demo_only','render_recipes'):raise ValueError('Unknown action')
    if action=='render_recipes' and not recipes:raise ValueError('Provide --recipes with finished original-art recipes; source-design queues are not render recipes.')
    catalog=checker();catalog.CUSTOM_WORK_FOLDER=CUSTOM_WORK_FOLDER
    base=catalog.choose_folder(output or (str(Path(CUSTOM_WORK_FOLDER)/'LAST_LIGHT_MASTER') if CUSTOM_WORK_FOLDER else ''))
    # Keep this master separate from the earlier standalone checker output.
    if not output and not CUSTOM_WORK_FOLDER:base=base.parent/'LAST_LIGHT_MASTER';base.mkdir(parents=True,exist_ok=True)
    print('LAST LIGHT MASTER | completed designs: 24 | source-design briefs queued: 2745')
    print('109 was the previous passing test count, not a sprite count.')
    print('Master folder:',base)
    source_result=None;art_result=None;queue=None
    if action in ('setup_and_demo','catalog_only'):
        source_result=catalog.run(str(base/'source_checks'))
        queue=durable_export(base/'design_queue','source_design_queue.jsonl',brief_lines(catalog))
        print('SOURCE DESIGN QUEUE:',queue)
        print('New source briefs require artwork recipes; no mass-generation approval is inferred.')
    if action in ('setup_and_demo','demo_only','render_recipes'):
        try:art=renderer()
        except ImportError as error:raise RuntimeError('Pillow is required. Use the same CodePad environment that ran V4 successfully.') from error
        if action=='render_recipes':
            def catalog_recipes():
                for row in art.load_recipe_file(recipes):
                    if not row.get('source_reference_ids'):
                        raise ValueError('Catalog recipe needs exact source IDs; demo/renamed templates do not cover catalog items.')
                    yield row
            recipe_rows=catalog_recipes()
            art_result=art.run_batch(recipe_rows,base/'catalog_candidates',limit=24,classification_path=classification or None)
        else:
            art_result=art.run_batch(art.demo_recipes(),base/'approved_style_demo',limit=24)
    result={'completed_designs_available':24,'new_catalog_sprites_generated':0,
        'source_briefs_requiring_original_art_recipes':2745,'remaining_source_exceptions':1578,
        'new_catalog_render_ready_records':0,'design_queue_path':queue,
        'source_checks':source_result,'demo_or_recipe_result':art_result,
        'note':'Source verification and test passes do not add new sprite artwork. Existing V4 art processing is unchanged.'}
    if action=='render_recipes':
        result['new_catalog_sprites_generated']=art_result.get('generated',0)
        result['new_catalog_render_ready_records']=None
    durable_export(base,'master_summary.json',[json.dumps(result,indent=2)])
    print('MASTER RESULT:',json.dumps({k:v for k,v in result.items() if k not in ('source_checks','demo_or_recipe_result')},sort_keys=True))
    return result

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',default='')
    parser.add_argument('--action',choices=['setup_and_demo','catalog_only','demo_only','render_recipes'],default=DEFAULT_ACTION)
    parser.add_argument('--recipes',default='')
    parser.add_argument('--classification-ledger',default='')
    args=parser.parse_args()
    try:run(args.output,args.action,args.recipes,args.classification_ledger)
    except Exception as error:
        print('MASTER STOPPED:',type(error).__name__,str(error));raise
'''

def build():
 renderer=(ROOT/'LAST_LIGHT_MASTER_SPRITE_FACTORY_V4.py').read_bytes();checker=(ROOT/'LAST_LIGHT_CATALOG_CHECKS.py').read_bytes()
 code=TEMPLATE.replace('@RENDER_SHA@',hashlib.sha256(renderer).hexdigest()).replace('@CHECK_SHA@',hashlib.sha256(checker).hexdigest()).replace('@RENDER@',base64.b64encode(zlib.compress(renderer,9)).decode()).replace('@CHECK@',base64.b64encode(zlib.compress(checker,9)).decode())
 out=ROOT/'LAST_LIGHT_MASTER.py';out.write_text(code);return out
if __name__=='__main__':print(build())
