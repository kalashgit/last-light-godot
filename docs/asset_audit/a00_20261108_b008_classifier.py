"""A00 B008: complete the original 21,025-record census with evidence gating.

This classifies archive rows 16,100–21,024; it does not certify that every
individual source image has undergone visual semantic review. Source materials
remain research-only. No imported third-party art or Golden approval is implied.
"""
from __future__ import annotations

import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).parent
SOURCE = ROOT / 'archive_a00/complete_source_file_registry.jsonl'
OUT = ROOT / 'a00_batch_0008_4925.jsonl'
SUMMARY = ROOT / 'a00_batch_0008_summary.json'
START, END = 16100, 21025
BATCH = 'A00-20261108-B008'

# Individually reconciled IDs. Other lexical 360 matches remain crosswalk
# evidence, and images labeled "Model" are never independent mesh masters.
VERIFIED_SOURCE_LINKS = {
    181171: 'll_crafting_firewood',
    181131: 'll_golden_bone_club',
}
EXISTING_MASTER_LINKS = {
    175891: 'll_household_match_box',
    182135: 'll_household_shoe_box',
}

sources = [json.loads(line) for line in SOURCE.open(encoding='utf8')]
assert len(sources) == 21025
assert len({s['mediawiki_page_id'] for s in sources}) == len(sources)

def stem(title: str) -> str:
    return re.sub(r'\.[^.]+$', '', title.removeprefix('File:')).strip()

def normal(name: str) -> str:
    return re.sub('[^a-z0-9]+', '', name.casefold())

all_by_stem = defaultdict(list)
for source in sources:
    all_by_stem[normal(stem(source['title']))].append(source)

states = {'overdone':'overcooked','rotten':'spoiled','cooked':'cooked',
          'burnt':'burnt','burned':'burnt','broken':'broken','smashed':'smashed',
          'dirty':'dirty','opened':'open','closed':'closed','open':'open',
          'empty':'empty','full':'full','frozen':'frozen','wet':'wet',
          'dry':'dry','unlit':'unlit','lit':'lit','dead':'dead',
          'unfired':'unfired','melted':'melted','filled':'filled',
          'bloody':'bloodied','fresh':'fresh','used':'used'}
colors = set('black blue brown green grey gray orange pink white red purple beige yellow khaki navy lightblue tan cream olive silver gold'.split())
wearables = ('hat','jacket','shirt','tshirt','vest','pants','shoes','socks',
             'scarf','dress','bandeau','belt','boots','glove','hoodie',
             'helmet','coat','sweater','mask','apron','trousers','underwear',
             'shorts','skirt','bra','bikini','goggles','overalls','boilersuit')

def wearing(name: str) -> bool:
    return normal(name).startswith(wearables)

def has(cats: str, *words: str) -> bool:
    return any(w in cats for w in words)

def ending_state(name: str):
    word = re.sub('[^a-z0-9]+$', '', name.casefold())
    for end, value in states.items():
        if word.endswith(end) and len(word) > len(end)+2:
            return name[:-len(end)].rstrip(' _-'), value
    return None, None

def color_variant(name: str):
    p = re.split('[ _-]+', name)
    if len(p) > 1 and p[-1].casefold() in colors:
        return name[:name.rfind(p[-1])].rstrip(' _-'), p[-1].casefold()
    return None, None

records = []
for source in sources[START:END]:
    name = stem(source['title'])
    low = name.casefold()
    cats = ' | '.join(source['categories']).casefold()
    kind, reason = 'NEEDS_MANUAL_REVIEW', 'Reference identity or gameplay necessity cannot be established from source metadata alone'
    rep = parent_stem = state = variant = queue = family_hint = None

    if source['file_page_status'] in ('redirect','confirmed_file_redirect'):
        kind, reason, rep = 'DUPLICATE_ALIAS', 'Source-file redirect, not a second game object', 'MEDIAWIKI_ALIAS'
    elif has(cats, 'straightened logos','recreated logos','company logos','wiki history images') or 'logo' in low:
        kind, reason, rep = 'OUT_OF_SCOPE', 'External franchise/logo or wiki-history image, not LAST LIGHT original art', 'BRANDING_OR_WIKI'
    elif has(cats, 'user images','user created district maps','user page'):
        kind, reason, rep = 'OUT_OF_SCOPE', 'Wiki-user contribution/reference, not a directly usable original game asset', 'USER_MEDIA'
    elif has(cats, 'animated images','animated tile images'):
        kind, reason, rep = 'ANIMATION_FRAME_REFERENCE', 'Animated visual reference; timing, parent action and actual frame sequence must be verified', 'ANIMATION_OR_GIF'
        queue = 'F12'
    elif has(cats, 'recipe icons','moodle icons','table ui icons','animal actions icons','occupation icons','trait icons','ui screenshots','map icons','foraging icons','left hud icons'):
        kind, reason, rep = 'UI_ICON_ONLY', 'UI/recipe/interaction icon reference; not a standalone physical Blender asset', 'UI_OR_RECIPE'
    elif has(cats, 'basement images','louisville images','rosewood images','riverside images','muldraugh images','valley station images','irvington images',
             'doe valley images','fellas lake images','fallas lake images','annotated maps images','spiffo images',
             'screenshots','help screenshots','modding images','newspaper images','devblog images','developer images',
             'video thumbnails','build thumbnails','rosewood starting locations images','muldraugh starting locations images',
             'abandoned town images'):
        kind, reason, rep = 'COMPOSITION_REFERENCE', 'Map, media, building scene or documentation composition; requires semantic component decomposition', 'RESEARCH_SCENE_OR_DOCUMENT'
        if has(cats,'basement images'): queue='F02'
    elif has(cats,'outfit images'):
        kind, reason, rep, queue = 'COMPOSITION_REFERENCE', 'Full assembled outfit view; F05 clothing and body meshes must be factored into reusable layers', 'OUTFIT_ASSEMBLY_VIEW', 'F05'
    elif has(cats,'food models','item models','literature models','firearm models','bag models','vehicle models') or low.endswith(' model'):
        kind, reason, rep = 'COMPOSITION_REFERENCE', 'Model-view reference for an object; never a second 3D reconstruction merely because the view is separate', 'MODEL_VIEW_REFERENCE'
        parent_stem = re.sub(r'[ _-]+model$','',name,flags=re.I)
        guess_parent, state = ending_state(parent_stem)
        if state: parent_stem = guess_parent
        queue = 'F10' if 'vehicle models' in cats else ('F05' if wearing(name) else 'F09')
        if 'literature models' in cats:
            family_hint = 'BOOK_COVER_OR_PAGE_VARIANT_SHARED_BOOK_MORPHOLOGY'
            queue = 'F09'
    elif has(cats,'vegetation tile images'):
        condition = re.search(r'vegetation[ _-]+farming[ _-]+(dead|dying|trampled|unhealthy|healthy|wilted|growing|ripe)\b', low)
        if condition:
            state = condition.group(1)
            kind, reason, rep = 'STATE_OR_DIRECTION', f'Vegetation atlas fragment depicting {state} crop condition; same botanical archetype family, species identity not established', 'VEGETATION_STATE_ATLAS_FRAGMENT'
        else:
            kind, reason, rep = 'COMPOSITION_REFERENCE', 'Vegetation tile fragment, botanical identity and growth stage require F04 kit grouping', 'VEGETATION_TILE_FRAGMENT'
        family_hint, queue = 'F04_CROP_STATE_KIT_NOT_A_SINGLE_PLANT_MASTER', 'F04'
    elif has(cats,'crafted tile images','carpentry tile images','furniture tile images','fixture tile images',
             'recreational tile images','camping tile images','location tile images','wall tile images',
             'appliance tile images','tile images','floor tile images','lighting tile images'):
        kind, reason, rep = 'COMPOSITION_REFERENCE', 'Atlas/tile fragment with numbered directions or components; preserve for module recipe without false asset admission', 'TILE_ATLAS_FRAGMENT'
        queue = 'F01' if 'furniture tile images' in cats or 'appliance tile images' in cats else ('F03' if 'floor tile images' in cats else 'F02')
    elif has(cats,'texture images','material images','decals'):
        kind, reason, rep, queue = 'MATERIAL_TEXTURE', 'Material/decal layer, not separate physical mesh', 'MATERIAL_OR_DECAL', 'F11'
    else:
        parent_stem, state = ending_state(name)
        if state:
            kind, reason, rep = 'STATE_OR_DIRECTION', f'{state} appearance or preparation state; parent mesh must be shared unless a distinct function is proven', 'OBJECT_STATE'
            queue = 'F05' if wearing(name) else 'F09'
        else:
            parent_stem, variant = color_variant(name)
            if variant:
                kind, reason, rep = 'MEANINGFUL_VARIANT', 'Color/material variant, not a new independent geometry master by default', 'APPEARANCE_VARIANT'
                queue = 'F05' if wearing(name) else 'F09'
            elif has(cats,'item icons','food icons','weapon icons','tool icons','water container icons','material icons'):
                kind, reason, rep = 'CANONICAL_MASTER_CANDIDATE', 'Possible needed physical inventory item, requiring independent gameplay and existing-model verification', 'INVENTORY_REFERENCE_ICON'
                queue = 'F05' if wearing(name) else 'F09'
            elif has(cats,'animal images'):
                kind, reason, rep, queue = 'COMPOSITION_REFERENCE', 'Animal source view; verify species and rig master identity', 'ANIMAL_REFERENCE', 'F07'

    parents = [x for x in all_by_stem.get(normal(parent_stem), []) if x['mediawiki_page_id'] != source['mediawiki_page_id']] if parent_stem else []
    parent = parents[0] if parents else None
    source_id = source['mediawiki_page_id']
    linked = VERIFIED_SOURCE_LINKS.get(source_id) or EXISTING_MASTER_LINKS.get(source_id)
    if source_id in VERIFIED_SOURCE_LINKS:
        status = 'LINKED_VERIFIED_MASTER_REFERENCE' if rep == 'MODEL_VIEW_REFERENCE' else 'RECONCILED_CANONICAL_MASTER_SOURCE'
    elif source_id in EXISTING_MASTER_LINKS:
        status = 'LINKED_TO_PREEXISTING_NOTION_MASTER'
    else:
        status = 'PROVISIONAL_METADATA_TRIAGE'
    records.append({
        'batch_id':BATCH, 'source_page_id':source_id,'source_title':source['title'],
        'source_url':source['file_page'], 'source_categories':source['categories'],
        'primary_class':kind,'reason':reason,'representation_kind':rep,
        'suggested_queue':queue,'family_hypothesis':family_hint,
        'parent_source_page_id':parent['mediawiki_page_id'] if parent else None,
        'parent_source_title':parent['title'] if parent else None,
        'proposed_parent_stem':parent_stem,'state_key':state,'variant_key':variant,
        'master_id':linked,'semantic_status':status,
        'visual_review':source['visual_review'],'rights':source['rights'],
        'file_page_status':source['file_page_status'],
    })

assert len(records)==END-START==4925
assert len({r['source_page_id'] for r in records})==len(records)
assert records[0]['source_page_id']==163721 and records[-1]['source_page_id']==637297
assert all(r['source_url'] and r['reason'] and r['primary_class'] for r in records)
assert {r['master_id'] for r in records if r['semantic_status'] in ('RECONCILED_CANONICAL_MASTER_SOURCE','LINKED_VERIFIED_MASTER_REFERENCE')}==set(VERIFIED_SOURCE_LINKS.values())

body = ''.join(json.dumps(r,ensure_ascii=False,sort_keys=True)+'\n' for r in records)
OUT.write_text(body,encoding='utf8')
counts = Counter(x['primary_class'] for x in records)
representations = Counter(x['representation_kind'] for x in records)
queues = Counter(x['suggested_queue'] for x in records if x['suggested_queue'])
conditions = Counter(x['state_key'] for x in records if x['representation_kind']=='VEGETATION_STATE_ATLAS_FRAGMENT')
samples = defaultdict(list)
for x in records:
    if len(samples[x['primary_class']]) < 4:
        samples[x['primary_class']].append({k:x[k] for k in ('source_page_id','source_title','source_url','primary_class','reason','state_key','suggested_queue')})
summary = {
 'batch_id':BATCH,'actual_fetched':len(records),'classified':len(records),
 'cumulative_fetched_and_metadata_classified':END,
 'source_first':records[0]['source_page_id'],'source_last':records[-1]['source_page_id'],
 'archive_offsets':{'start_inclusive':START,'end_exclusive':END},
 'primary_classes':dict(sorted(counts.items())),
 'representation_kinds':dict(sorted(representations.items(),key=lambda kv:str(kv[0]))),
 'suggested_queue_counts':dict(sorted(queues.items())),
 'vegetation_state_tile_fragments_by_condition':dict(sorted(conditions.items())),
 'provisional_parent_source_links':sum(x['parent_source_page_id'] is not None for x in records),
 'unresolved_parent_stems':sum(bool(x['proposed_parent_stem']) and x['parent_source_page_id'] is None for x in records),
 'semantic_identities_individually_verified':len(set(VERIFIED_SOURCE_LINKS.values())),
 'new_notion_master_rows':len(set(VERIFIED_SOURCE_LINKS.values())),
 'source_records_linked_to_published_masters':len(VERIFIED_SOURCE_LINKS),
 'source_records_linked_to_preexisting_masters':len(EXISTING_MASTER_LINKS),
 'existing_360_geometry_index_checked':360,
 'geometry_exact_name_matched_source_records':6,
 'geometry_exact_name_matched_unique_model_ids':5,
 'geometry_crosswalk_report':'docs/asset_audit/a00_20261108_b008_360_crosswalk.json',
 'semantic_work_orders':'docs/asset_audit/a00_20261108_b008_semantic_work_orders.jsonl',
 'source_research_only_records':sum(x['rights']=='source_research_only' for x in records),
 'source_snapshot_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
 'ledger_sha256':hashlib.sha256(body.encode()).hexdigest(),
 'next_cursor':None,'remaining_after_batch':0,'golden_visual_approved_in_batch':0,
 'stratified_metadata_spotcheck_samples':dict(samples),
}
SUMMARY.write_text(json.dumps(summary,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
print(json.dumps({k:v for k,v in summary.items() if k not in ('representation_kinds','stratified_metadata_spotcheck_samples')},indent=2))
