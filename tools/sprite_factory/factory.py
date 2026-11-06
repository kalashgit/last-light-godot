#!/usr/bin/env python3
"""LAST LIGHT candidate factory. No image-model API or visual approval is simulated."""
import argparse
import copy
import fcntl
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'production/sprite_factory'
GOLD = ROOT / 'assets/last_light/golden40'
CRITERIA = ['realism_identity', 'silhouette_readability', 'material_shading', 'style_lighting', 'pixel_cleanliness', 'originality_provenance']
DISPOSITIONS = {'new_original_logical_item', 'variant', 'state', 'duplicate', 'unsupported', 'deferred_world_furniture_vehicle_animation', 'requires_human_classification'}


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    """Atomic checkpoint: interrupted writes cannot leave a half JSON document."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(value, indent=2) + '\n')
    temp.replace(path)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def safe(path):
    path = (ROOT / path).resolve()
    if not path.is_relative_to(ROOT):
        raise ValueError('path outside repository')
    return path


def batch_dir(batch):
    if not re.fullmatch(r'LL-ICON-B\d{4}', batch):
        raise ValueError('invalid batch ID')
    return BASE / 'batches' / batch


def intake(sources):
    """Parse archived Notion catalog metadata; retain curated dispositions on resume."""
    previous = {x['reference_id']: x for x in read(BASE / 'catalog.json')['rows']} if (BASE / 'catalog.json').exists() else {}
    suggestions = {}
    for page in read(sources).get('classifications', []):
        for line in page['text'].splitlines():
            match = re.match(r'\| (\d+) \| \[(.*?)\]\((.*?)\) \| (.*?) \| (.*?) \| (.*?) \| (.*?) \|', line)
            if match:
                idx, name, url, category, family, variants, confidence = match.groups()
                if int(idx) in suggestions:
                    raise ValueError('duplicate legacy classification')
                suggestions[int(idx)] = dict(category=category, family_candidate=family, variant_clues=variants, confidence=confidence, source_page=page['url'], visually_verified=False)
    if suggestions and len(suggestions) != 4347:
        raise ValueError('incomplete legacy classification snapshot')
    rows = []
    for page in read(sources)['batches']:
        count = 0
        for line in page['text'].splitlines():
            m = re.match(r'\| (\d+) \| (.*?) \| \[Image\]\((.*?)\) \| \[Source\]\((.*?)\) \| (.*?) \|', line)
            if not m:
                continue
            idx, name, image_url, url, metadata = m.groups()
            ref = 'pzwiki:catalog:2026-11-05:' + idx
            row = dict(catalog_index=int(idx), reference_id=ref, source_filename=name, source_page_url=url, source_image_url=image_url, source_catalog_page='https://app.notion.com/p/' + page['id'], source_metadata=metadata, mediawiki_page_id=None, logical_item_id=None, category=None, family=None, physical_description=None, materials=[], states=[], gameplay_purpose=None, originality_requirements='Independent semantic composition; no source pixels or trade dress', priority='unassigned', disposition='requires_human_classification', reason='Metadata imported; no visual or mechanical equivalence confirmed', reviewed=False)
            if ref in previous:
                old = previous[ref]
                for key in ['catalog_index', 'source_filename', 'source_page_url']:
                    if row[key] != old[key]:
                        raise ValueError('source changed; manual reconciliation required: ' + ref)
                row = old
            if suggestions:
                row['legacy_provisional_classification'] = suggestions[int(idx)]
            rows.append(row)
            count += 1
        if count not in (100, 147, 200):
            raise ValueError('incomplete source page: ' + page['id'])
    indices = [x['catalog_index'] for x in rows]
    if len(indices) != 4347 or sorted(indices) != list(range(1, 4348)):
        raise ValueError('catalog must reconcile exactly to 1–4347, with no duplicates')
    if any(x['disposition'] not in DISPOSITIONS for x in rows):
        raise ValueError('invalid disposition')
    write(BASE / 'catalog.json', dict(schema=1, reference_count=4347, rows=rows))
    checkpoint()
    print('INTAKE PASS: 4347 immutable references; curated decisions preserved')


def extract(batch, revision, sheet=None, only=None):
    b = batch_dir(batch)
    plan = read(b / 'briefs.json')
    generation_path = b / ('generation_' + revision + '.json')
    if not generation_path.exists():
        generation_path = b / 'generation.json'
    generation = read(generation_path)
    sheet_path = Path(sheet) if sheet else b / 'source_sheet.png'
    source = Image.open(sheet_path)
    if source.mode != 'RGBA':
        raise ValueError('generation must supply transparent RGBA; no chroma-key assumptions')
    if source.getchannel('A').getextrema() != (0, 255):
        raise ValueError('source lacks meaningful full transparency')
    output = ROOT / 'assets/last_light/candidates' / batch / revision
    manifest_path = b / (revision + '.json')
    if manifest_path.exists():
        old = read(manifest_path)
        if old['source_sheet_sha256'] != digest(sheet_path):
            raise ValueError('immutable revision already exists with another source')
        print('RESUME: immutable revision exists; validate rather than overwrite')
        return
    if output.exists():
        # Resume an interrupted revision only if each existing output is identical.
        print('RESUME: comparing partial revision outputs')
    records = []
    for i, brief in enumerate(plan['items']):
        if only and brief['logical_item_id'] != only:
            continue
        col, row = i % 5, i // 5
        box = tuple(round(v) for v in (col * source.width / 5, row * source.height / 4, (col + 1) * source.width / 5, (row + 1) * source.height / 4))
        overrides = read(b / 'crop_overrides.json') if (b / 'crop_overrides.json').exists() else {}
        box = (0, 0, source.width, source.height) if only else tuple(overrides.get(brief['logical_item_id'], box))
        tile = source.crop(box)
        arr = np.asarray(tile).copy()
        mask = arr[:, :, 3] >= 128
        labels, count = ndimage.label(mask, np.ones((3, 3)))
        sizes = np.bincount(labels.ravel())
        # Detached low-alpha dust is removed; preserve all substantial disconnected parts.
        keep = sizes[labels] >= 64
        keep[labels == 0] = False
        arr[:, :, 3] = np.where(keep, 255, 0)
        arr[~keep, :3] = 0
        cleaned = Image.fromarray(arr)
        bounds = cleaned.getbbox()
        if bounds is None:
            raise ValueError('empty cell: ' + brief['logical_item_id'])
        if bounds[0] < 2 or bounds[1] < 2 or bounds[2] > tile.width - 2 or bounds[3] > tile.height - 2:
            raise ValueError('cell clipping risk: ' + brief['logical_item_id'])
        cropped = cleaned.crop(bounds)
        cropped.thumbnail((56, 56), Image.Resampling.NEAREST)
        # Adaptive palette without dither; this is normalization, not human pixel-art approval.
        alpha = cropped.getchannel('A')
        cropped = cropped.convert('RGB').quantize(colors=32, dither=Image.Dither.NONE).convert('RGBA')
        cropped.putalpha(alpha)
        icon = Image.new('RGBA', (64, 64))
        icon.alpha_composite(cropped, ((64 - cropped.width) // 2, (64 - cropped.height) // 2))
        path = output / brief['logical_item_id'] / 'icon.png'
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix('.tmp.png')
        icon.save(tmp)
        if path.exists() and digest(path) != digest(tmp):
            tmp.unlink()
            raise ValueError('partial revision conflict; use a new revision')
        tmp.replace(path)
        entry = copy.deepcopy(brief)
        entry.update(asset_id=f"art.{brief['logical_item_id']}.icon.{revision}", export_path=str(path.relative_to(ROOT)), content_sha256=digest(path), source_path=str(sheet_path.resolve().relative_to(ROOT)), source_crop=list(box), source_object_bounds=list(bounds), dimensions=[64, 64], alpha_format='RGBA_binary', generator=generation['tool'], generator_version=generation['model_version'], normalization_version='nearest64_palette32_alpha128_v1', provenance_path=str(generation_path.relative_to(ROOT)), style_bible=plan['style'], status='generated_candidate', technical_qa=None, visual_qa=None, godot_import_status='not_tested', iphone_xogot_status='not_tested')
        records.append(entry)
    if not records:
        raise ValueError('no matching item')
    write(manifest_path, dict(schema=1, batch_id=batch, revision=revision, source_sheet_sha256=digest(sheet_path), items=records))
    checkpoint()
    print(f'EXTRACT: {len(records)} individual 64px candidates; no visual approvals')


def validate_manifest(manifest):
    errors, warnings, stats = [], [], []
    known_refs = {x['reference_id'] for x in read(BASE / 'catalog.json')['rows']}
    if not manifest.get('items'):
        errors.append('manifest contains no exports')
    seen = {k: set() for k in ['logical_item_id', 'asset_id', 'export_path', 'content_sha256']}
    thumbs = []
    for x in manifest.get('items', []):
        ident = x.get('logical_item_id', '<missing>')
        def fail(reason):
            errors.append(ident + ': ' + reason)
        for key in seen:
            value = x.get(key)
            if not value or value in seen[key]:
                fail('missing or duplicate ' + key)
            seen[key].add(value)
        required = ['reference_ids', 'materials', 'style_bible', 'generator', 'generator_version', 'source_path', 'provenance_path', 'anchor', 'required_states', 'required_views', 'originality', 'family']
        if any(not x.get(k) for k in required):
            fail('missing required metadata')
        if any(ref not in known_refs for ref in x.get('reference_ids', [])):
            fail('broken source reference')
        if x.get('dimensions') != [64,64]:
            fail('unexpected canvas metadata')
        if not x.get('state') in x.get('required_states', []):
            fail('state does not satisfy brief')
        # A multi-state/view brief is not fulfilled by one icon.
        if x.get('required_states') != [x.get('state')] or x.get('required_views') != ['inventory_icon']:
            fail('required state/view missing; separate export records needed')
        if x.get('anchor') != [32, 32] or x.get('anchor_kind', '').startswith('inventory_center') is False:
            fail('invalid inventory anchor')
        try:
            path = safe(x['export_path'])
            if digest(path) != x['content_sha256']:
                fail('content hash mismatch')
            for key in ['source_path', 'provenance_path']:
                if not safe(x[key]).is_file():
                    fail('broken ' + key)
            provenance = read(safe(x['provenance_path']))
            if digest(safe(provenance['prompt_path'])) != provenance['prompt_sha256']:
                fail('prompt provenance hash mismatch')
            if digest(safe(x['source_path'])) != provenance['source_sheet_sha256']:
                fail('source artwork provenance hash mismatch')
            with Image.open(path) as im:
                im.load()
                if im.format != 'PNG' or im.mode != 'RGBA' or im.size != (64, 64):
                    fail('invalid PNG, alpha or dimensions')
                    continue
                a = np.asarray(im)[:, :, 3]
                bbox = im.getchannel('A').getbbox()
                opaque = int((a >= 128).sum())
                if bbox is None or opaque < 40:
                    fail('nearly empty sprite')
                elif min(bbox[0], bbox[1], 64-bbox[2], 64-bbox[3]) < 3:
                    fail('clipping / insufficient margin')
                if np.count_nonzero(a) > 0.85 * 4096:
                    fail('possible opaque background contamination')
                if a[:3].any() or a[-3:].any() or a[:, :3].any() or a[:, -3:].any():
                    fail('background or edge contamination')
                if np.any((a > 0) & (a < 255)):
                    warnings.append(ident + ': partial alpha requires halo review')
                labels, n = ndimage.label(a > 0, np.ones((3, 3)))
                sizes = np.bincount(labels.ravel())[1:]
                if any(sizes == 1):
                    warnings.append(ident + ': isolated single pixel requires inspection')
                stats.append(dict(id=ident, bbox=bbox, opaque_pixels=opaque, components=n))
                thumbs.append((ident, np.asarray(im.resize((16,16),Image.Resampling.NEAREST)).astype(float)))
        except (KeyError, ValueError, OSError) as exc:
            fail(str(exc))
    for i, (a, av) in enumerate(thumbs):
        for b, bv in thumbs[:i]:
            # Advisory comparison only, never evidence of identity or originality.
            distance = float(np.mean(np.abs(av - bv)))
            if distance < 6:
                warnings.append(f'near-identical advisory: {a} / {b} MAE={distance:.3f}')
    return dict(result='PASS' if not errors else 'FAIL', method='automated technical checks; no visual approval', errors=errors, warnings=warnings, measurements=stats)


def validate(batch, revision):
    b = batch_dir(batch); path = b / (revision + '.json'); m = read(path)
    report = validate_manifest(m)
    write(b / (revision + '-technical-qa.json'), report)
    for item in m['items']:
        item['technical_qa'] = {'result': 'FAIL' if any(e.startswith(item['logical_item_id'] + ':') for e in report['errors']) else report['result'], 'report': str((b / (revision + '-technical-qa.json')).relative_to(ROOT))}
    write(path, m)
    print(json.dumps({k:v for k,v in report.items() if k != 'measurements'}, indent=2))
    return not report['errors']


def sheets(batch, revision):
    b = batch_dir(batch); m = read(b / (revision + '.json'))
    out = b / 'reviews' / revision; out.mkdir(parents=True, exist_ok=True)
    for size in [32, 48, 64]:
        for theme, bg, fg in [('dark','#20282b','#e9e1d5'),('light','#eeece5','#303b40')]:
            im = Image.new('RGB', (5 * 176, 4 * 124), bg); d = ImageDraw.Draw(im)
            for i,x in enumerate(m['items']):
                icon = Image.open(safe(x['export_path'])).resize((size,size),Image.Resampling.NEAREST)
                ox=(i%5)*176;oy=(i//5)*124
                im.paste(icon,(ox+(176-size)//2,oy+8),icon)
                d.text((ox+5,oy+78),f"{i+1:02} {x['name']}",fill=fg)
                d.text((ox+5,oy+96),f"source #{x['reference_indices'][0]} / {size}px",fill=fg)
            im.save(out / f'{theme}_{size}.png')
    # Native vs Golden reference comparison for EVERY item, no claim all materials have golden exemplars.
    golden = read(GOLD / 'manifest.json')['items']
    match = {'food':1,'medical':10,'tools':20,'crafting':15,'household':13,'clothing':13}
    board=Image.new('RGB',(1000,720),'#20282b');d=ImageDraw.Draw(board)
    for i,x in enumerate(m['items']):
        ox=(i%5)*200;oy=(i//5)*180
        material_match = {'ll_food_water_bottle':6,'ll_medical_first_aid_case':6,'ll_medical_antibiotic_tablets':15,'ll_crafting_duct_tape':4,'ll_crafting_rope_coil':13,'ll_crafting_nail_box':0,'ll_household_shoe_box':0,'ll_household_field_notebook':0}
        exemplar_index = material_match.get(x['logical_item_id'],match[x['family']])
        for j,icon in enumerate([Image.open(safe(x['export_path'])),Image.open(GOLD/golden[exemplar_index]['icon'])]):
            icon=icon.resize((80,80),Image.Resampling.NEAREST);board.paste(icon,(ox+8+j*96,oy+8),icon)
        d.text((ox+5,oy+95),f"{i+1:02} {x['name']}",fill='#e9e1d5')
        d.text((ox+5,oy+113),'candidate | Golden reference',fill='#b9c3ba')
        d.text((ox+5,oy+131),golden[exemplar_index]['id'][10:30],fill='#b9c3ba')
    board.save(out/'golden_comparison.png')
    print('REVIEW SHEETS: 32/48/64px dark + light, 5x4; cross-material comparison')


def review(batch, revision, decisions):
    b=batch_dir(batch);p=b/(revision+'.json');m=read(p);data=read(decisions)
    if data.get('reviewer_type') not in ['engineer_visual_inspection','independent_reviewer','founder'] or not data.get('reviewer') or not data.get('evidence'):
        raise ValueError('named reviewer, actual inspection evidence and reviewer type required')
    for decision in data['items']:
        item=next(x for x in m['items'] if x['asset_id']==decision['asset_id'])
        if decision.get('content_sha256')!=item['content_sha256'] or digest(safe(item['export_path']))!=item['content_sha256']:
            raise ValueError('review must bind exact inspected bytes')
        scores=decision.get('scores',{})
        if set(scores)!=set(CRITERIA) or any(type(s) is not int or not 1<=s<=5 for s in scores.values()):
            raise ValueError('six actual inspection scores required')
        passed=min(scores.values())>=4 and not decision.get('critical_defects') and decision.get('result')=='PASS'
        if decision.get('result')=='PASS' and not passed:
            raise ValueError('invalid visual pass')
        item['visual_qa']=decision | {k:data[k] for k in ['reviewer','reviewer_type','evidence']}
        item['status']='visual_review_pass' if passed else 'rework'
    write(p,m);checkpoint()


def rework(batch, asset_id, defect, cause, change):
    b=batch_dir(batch);p=b/'rework.json';events=read(p) if p.exists() else []
    attempts=sum(e['asset_id']==asset_id for e in events)
    if attempts>=3:
        raise ValueError('retry limit reached; escalate for review')
    events.append(dict(asset_id=asset_id,attempt=attempts+1,defect=defect,likely_cause=cause,targeted_change=change,state='queued'))
    write(p,events)
    print('REWORK queued; use extract --only with a new revision; accepted files untouched')


def promote(batch, revision, approval):
    """Explicit founder calibration approval and six inspected criteria are required."""
    b=batch_dir(batch);m=read(b/(revision+'.json'));qa=validate_manifest(m);a=read(approval)
    if qa['errors']:
        raise ValueError('technical gate failed')
    if a.get('approval_type')!='founder' or a.get('batch_id')!=batch or not a.get('evidence_url') or not a.get('style_calibration_approved'):
        raise ValueError('founder approval of actual calibration artwork required')
    for x in m['items']:
        v=x.get('visual_qa') or {}
        if v.get('result')!='PASS' or v.get('critical_defects') or set(v.get('scores',{}))!=set(CRITERIA) or min(v['scores'].values())<4 or v.get('content_sha256')!=x['content_sha256']:
            raise ValueError('visual gate failed: '+x['logical_item_id'])
        if a.get('approved_hashes',{}).get(x['asset_id'])!=x['content_sha256']:
            raise ValueError('founder approval is not bound to exact asset hash')
    registry_path=BASE/'approved_registry.json';registry=read(registry_path)
    staged=[]
    for x in m['items']:
        existing = next((y for y in registry['items'] if y['logical_item_id'] == x['logical_item_id'] and y['asset_id'] != x['asset_id']), None)
        if existing and a.get('replaces', {}).get(x['logical_item_id']) != existing['asset_id']:
            raise ValueError('explicit version replacement approval required')
        asset_revision = x['asset_id'].rsplit('.',1)[-1]
        if not re.fullmatch(r'v\d{3}', asset_revision):
            raise ValueError('approved export needs an immutable asset revision')
        target=ROOT/'assets/last_light/approved'/x['logical_item_id']/asset_revision/'icon.png'
        if target.exists() and digest(target)!=x['content_sha256']:
            raise ValueError('approved master is immutable')
        y=copy.deepcopy(x);y['export_path']=str(target.relative_to(ROOT));y['status']='approved_inventory_export';y['founder_approval']=a['evidence_url'];staged.append((x,target,y))
    # Copies precede the atomic registry update; interrupted orphan copies are never consumed.
    for x,target,y in staged:
        target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(safe(x['export_path']),target)
    for _,_,y in staged:
        outgoing = [x for x in registry['items'] if x['logical_item_id'] == y['logical_item_id'] and x['asset_id'] != y['asset_id']]
        registry.setdefault('history', []).extend(outgoing)
        registry['items']=[x for x in registry['items'] if x['logical_item_id'] != y['logical_item_id']]+[y]
    write(registry_path,registry);checkpoint()


def checkpoint():
    rows=read(BASE/'catalog.json')['rows'];items=[]
    for p in sorted((BASE/'batches').glob('*/v*.json')):
        if re.fullmatch(r'v\d{3}',p.stem):
            items.extend(read(p)['items'])
    approved=read(BASE/'approved_registry.json')['items'] if (BASE/'approved_registry.json').exists() else []
    report=dict(reference_records_total=len(rows),legacy_keyword_provisional=sum(x.get('legacy_provisional_classification',{}).get('confidence')=='keyword-provisional' for x in rows),legacy_manual_review=sum(x.get('legacy_provisional_classification',{}).get('confidence')=='manual-review' for x in rows),reference_records_reviewed=sum(x['reviewed'] for x in rows),reference_records_semantically_classified=sum(x['reviewed'] and x['disposition']!='requires_human_classification' for x in rows),disposition_coverage=len(rows),requires_human_classification=sum(x['disposition']=='requires_human_classification' for x in rows),duplicate_references=sum(x['disposition']=='duplicate' for x in rows),deferred_references=sum(x['disposition'].startswith('deferred') for x in rows),semantic_briefs_authored=len({x['logical_item_id'] for p in (BASE/'batches').glob('*/briefs.json') for x in read(p)['items']}),founder_approved_briefs=0,candidate_icons_generated=len(items),pixel_normalized_icons=len(items),hand_pixel_cleaned_icons=0,visual_review_passes=sum((x.get('visual_qa') or {}).get('result')=='PASS' for x in items),rework_icons=sum(x['status']=='rework' for x in items),approved_inventory_exports=len(approved),world_sprites_generated=0,godot_candidate_imports_verified=sum(x.get('godot_import_status')=='verified_review_only' for x in items),godot_production_imports_verified=sum(x.get('godot_import_status')=='verified' for x in approved),iphone_xogot_verified=sum(x.get('iphone_xogot_status')=='verified' for x in items),scope='This factory run; pre-existing 300 procedural candidates and Golden40 counted separately',next_batch_gate='Founder calibration approval and no critical defects; no automatic mass expansion')
    write(BASE/'dashboard.json',report)
    return report


def assemble(batch, selection):
    b = batch_dir(batch)
    revisions = {p.stem: read(p) for p in b.glob('v*.json') if re.fullmatch(r'v\d{3}', p.stem)}
    choices = read(selection)
    items = []
    for brief in read(b / 'briefs.json')['items']:
        rev = choices[brief['logical_item_id']]
        items.append(next(x for x in revisions[rev]['items'] if x['logical_item_id'] == brief['logical_item_id']))
    if len(items) != 20:
        raise ValueError('calibration assembly must contain exactly 20 icons')
    write(b / 'active.json', dict(schema=1, batch_id=batch, revision='active', selection=choices, items=items))
    print('ASSEMBLE: 20 explicit version selections; no automatic promotion')


def audit_golden():
    m = read(GOLD / 'manifest.json')
    measurements = []
    for x in m['items']:
        im = Image.open(GOLD / x['icon'])
        if im.mode != 'RGBA' or im.size != (64,64) or digest(GOLD / x['icon']) != x['sha256']:
            raise ValueError('Golden file integrity failed: ' + x['id'])
        rgb = np.asarray(im)[:,:,:3]; a = np.asarray(im)[:,:,3]
        measurements.append(dict(asset_id=x['id'], path=str((GOLD/x['icon']).relative_to(ROOT)), sha256=x['sha256'], native_bbox=im.getchannel('A').getbbox(), partial_alpha_pixels=int(((a>0)&(a<255)).sum()), color_count=len(np.unique(rgb[a>0],axis=0)), provenance=x['source_provenance'], status=x['status']))
    write(BASE/'evidence/golden40_integrity.json',dict(count=len(measurements),starting_commit='65062417ae1167b6fed697a6f2ef8881f5719d97',tree='f33632400ca653eeb70302b73ab6000bb4983b0f',local_5286441_available=False,source_contact_sheets_available=False,provenance_limit='Founder attribution in existing manifest and Bible section 18; original full sheets absent, provenance not independently reconstructed',items=measurements))
    for size in [32,48,64]:
        im=Image.new('RGB',(8*150,5*120),'#20282b');d=ImageDraw.Draw(im)
        for i,x in enumerate(m['items']):
            icon=Image.open(GOLD/x['icon']).resize((size,size),Image.Resampling.NEAREST)
            ox=(i%8)*150;oy=(i//8)*120;im.paste(icon,(ox+(150-size)//2,oy+5),icon)
            d.text((ox+3,oy+78),f"{i+1:02} {x['name'][:20]}",fill='#e9e1d5')
        im.save(BASE/f'evidence/golden40_native_{size}.png')
    print('GOLDEN AUDIT PASS: 40 icons and hash bindings; provenance limits recorded')


def main():
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='cmd',required=True)
    p=sub.add_parser('intake');p.add_argument('sources')
    sub.add_parser('audit-golden')
    p=sub.add_parser('request');p.add_argument('batch')
    p=sub.add_parser('assemble');p.add_argument('batch');p.add_argument('--selection',required=True)
    for cmd in ['extract','validate','sheets','review','promote']:
        p=sub.add_parser(cmd);p.add_argument('batch');p.add_argument('--revision',default='v001',type=lambda s:s if re.fullmatch(r'v\d{3}|active',s) else parser.error('revision must be vNNN'))
        if cmd=='extract':p.add_argument('--sheet');p.add_argument('--only')
        if cmd=='review':p.add_argument('--decisions',required=True)
        if cmd=='promote':p.add_argument('--approval',required=True)
    p=sub.add_parser('rework');p.add_argument('batch');p.add_argument('asset_id');p.add_argument('--defect',required=True);p.add_argument('--cause',required=True);p.add_argument('--change',required=True)
    sub.add_parser('checkpoint')
    a=parser.parse_args()
    BASE.mkdir(parents=True, exist_ok=True)
    lock = open(BASE / '.factory.lock', 'a')
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        parser.exit(1, 'BLOCKED: another factory checkpoint is running\n')
    try:
        if a.cmd=='intake':intake(a.sources)
        elif a.cmd=='request':
            b = batch_dir(a.batch)
            payload = {'tool':'image_gen.imagegen','prompt':(b/'prompt.txt').read_text(),'referenced_image_paths':[str(BASE/'evidence/golden40_all.png')],'transparent_background':True}
            write(b/'generation_request.json',payload)
            print(json.dumps(payload))
        elif a.cmd=='audit-golden':audit_golden()
        elif a.cmd=='assemble':assemble(a.batch,a.selection)
        elif a.cmd=='extract':
            if a.revision=='active':raise ValueError('active is an assembly, not a generated revision')
            extract(a.batch,a.revision,a.sheet,a.only)
        elif a.cmd=='validate':sys.exit(0 if validate(a.batch,a.revision) else 1)
        elif a.cmd=='sheets':sheets(a.batch,a.revision)
        elif a.cmd=='review':review(a.batch,a.revision,a.decisions)
        elif a.cmd=='promote':promote(a.batch,a.revision,a.approval)
        elif a.cmd=='rework':rework(a.batch,a.asset_id,a.defect,a.cause,a.change)
        else:print(json.dumps(checkpoint(),indent=2))
    except (ValueError,KeyError,OSError) as exc:
        print('BLOCKED: '+str(exc),file=sys.stderr);sys.exit(1)

if __name__=='__main__':main()
