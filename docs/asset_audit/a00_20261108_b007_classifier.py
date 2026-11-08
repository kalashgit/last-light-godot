"""A00 Batch 007: eight thousand PZwiki File-page metadata references.

This is an evidence-preserving *reference* audit, not an eight-thousand-master
approval run.  Source images, states and tile fragments never become original
LAST LIGHT models merely because their filenames look plausible.
"""
from __future__ import annotations

import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).parent
SOURCE = ROOT / 'archive_a00/complete_source_file_registry.jsonl'
OUT = ROOT / 'a00_batch_0007_8000.jsonl'
SUMMARY = ROOT / 'a00_batch_0007_summary.json'
START, END = 8100, 16100
BATCH = 'A00-20261108-B007'

# The only individually reconciled identities for this batch, each also
# checked against the existing 360-source GLB manifest and Notion master IDs.
# All other rows remain provisional. A model screenshot is a linked source,
# not a second independent master.
VERIFIED_SOURCE_LINKS = {
    115897: 'll_household_bucket',
    116081: 'll_household_match_box',
    140345: 'll_tools_hand_drill',
    118353: 'll_crafting_glass_pane',
    116243: 'll_crafting_steel_wool',
    140515: 'll_crafting_steel_wool',
    117079: 'll_household_photo_album',
    142581: 'll_household_photo_album',
}
VERIFIED_MASTER_IDS = set(VERIFIED_SOURCE_LINKS.values())

sources = [json.loads(line) for line in SOURCE.open(encoding='utf-8')]
assert len(sources) == 21025, 'Expected existing complete census (not a new scan)'

def stem(title: str) -> str:
    return re.sub(r'\.[^.]+$', '', title.removeprefix('File:')).strip()

def normal(name: str) -> str:
    return re.sub(r'[^a-z0-9]+', '', name.casefold())

source_by_stem = defaultdict(list)
for source in sources:
    source_by_stem[normal(stem(source['title']))].append(source)

state_suffix = {
    'overdone': 'overcooked', 'rotten': 'spoiled', 'cooked': 'cooked',
    'burnt': 'burnt', 'burned': 'burnt', 'broken': 'broken',
    'smashed': 'smashed', 'dirty': 'dirty', 'clean': 'clean',
    'opened': 'open', 'closed': 'closed', 'open': 'open',
    'empty': 'empty', 'full': 'full', 'frozen': 'frozen',
    'wet': 'wet', 'dry': 'dry', 'lit': 'lit', 'unlit': 'unlit',
    'dead': 'dead', 'unfired': 'unfired', 'melted': 'melted',
    'filled': 'filled', 'bloody': 'bloodied', 'fresh': 'fresh',
}
colors = set('black blue brown darkblue green grey gray orange pink sand white red purple beige yellow khaki navy lightblue turquoise cyan tan cream olive silver gold burgundy maroon teal'.split())
wearable_prefixes = ('hat', 'jacket', 'tshirt', 'shirt', 'vest', 'pants', 'shoes',
                     'socks', 'scarf', 'dress', 'bandeau', 'belt', 'boots',
                     'gloves', 'glove', 'hoodie', 'helmet', 'coat', 'sweater',
                     'mask', 'apron', 'trousers', 'underwear', 'shorts', 'skirt',
                     'bra', 'bikini', 'goggles', 'earmuffs', 'boilersuit',
                     'overalls', 'waistcoat', 'necklace', 'ring', 'wristwatch')
appearance_patterns = ('camo', 'denim', 'flowery', 'floral', 'plaid', 'striped',
                       'polkadot', 'leopard', 'leather', 'paisley', 'printed')

def is_wearable(name: str) -> bool:
    low = normal(name)
    return any(low.startswith(prefix) for prefix in wearable_prefixes)

def ending_state(name: str):
    word = re.sub(r'[^a-z0-9]+$', '', name.casefold())
    for suffix, value in state_suffix.items():
        if word.endswith(suffix) and len(word) > len(suffix) + 2:
            return name[:len(name)-len(suffix)].rstrip(' _-'), value
    return None, None

def ending_color(name: str):
    # Require a separator: "Blacksmith" must not be split into "Black".
    parts = re.split(r'[ _-]+', name)
    if len(parts) > 1 and parts[-1].casefold() in colors:
        return name[:name.rfind(parts[-1])].rstrip(' _-'), parts[-1].casefold()
    return None, None

def has(cats: str, *phrases: str) -> bool:
    return any(phrase in cats for phrase in phrases)

rows = []
for source in sources[START:END]:
    name = stem(source['title'])
    low = name.casefold()
    cats = ' | '.join(source['categories']).casefold()
    cls, reason = 'NEEDS_MANUAL_REVIEW', 'Metadata insufficient to decide original standalone asset identity'
    rep = None
    parent_stem = None
    state = None
    variant = None
    queue = None

    if source['file_page_status'] in ('redirect', 'confirmed_file_redirect'):
        cls, reason = 'DUPLICATE_ALIAS', 'Confirmed MediaWiki file redirect: resolve target; never create a second master'
        rep = 'FILE_ALIAS'
    elif has(cats, 'straightened logos', 'recreated logos', 'company logos', 'wiki history images') or 'logo' in low:
        cls, reason = 'OUT_OF_SCOPE', 'Franchise/source branding, wiki-history or logo research is not a reusable original game asset'
        rep = 'BRANDING_OR_WIKI_REFERENCE'
    elif has(cats, 'louisville images', 'west point images', 'muldraugh images',
             'valley station images', 'brandenburg images', 'irvington images',
             'ekron images', 'echo creek images', 'coalfield images',
             'doe valley images', 'annotated maps images', 'map images',
             'devblog images', 'devblog thumbnails', 'video thumbnails',
             'indiedb thumbnails', 'screenshots', 'survivor story images',
             'modding images', 'newspaper images', 'the forgotten element images'):
        cls, reason = 'COMPOSITION_REFERENCE', 'Location, media, screenshot or documentation composition; not a standalone reusable 3D master'
        rep = 'RESEARCH_SCENE_OR_DOCUMENT'
    elif has(cats, 'recipe icons', 'moodle icons', 'occupation icons',
             'trait icons', 'miscellaneous ui icons', 'left hud icons',
             'foraging icons', 'emote icons', 'map icons', 'ui screenshots',
             'body part icons'):
        cls, reason = 'UI_ICON_ONLY', 'Interface/recipe/HUD representation, not a physical Blender geometry master'
        rep = 'UI_OR_RECIPE_VISUAL'
        # F12 is the 2.5D renderer/exporter, not a UI-design ownership queue.
        queue = None
    elif has(cats, 'outfit images'):
        cls, reason = 'COMPOSITION_REFERENCE', 'Outfit presentation; decompose into body rig, clothing, equipment variants before F05 admission'
        rep = 'OUTFIT_ASSEMBLY_VIEW'
        queue = 'F05'
    elif has(cats, 'item models', 'food models', 'bag models', 'vehicle models') or low.endswith(' model'):
        cls, reason = 'COMPOSITION_REFERENCE', 'Model-view representation of a semantic object, never another reconstruction simply for a different view'
        rep = 'MODEL_VIEW_REFERENCE'
        parent_stem = re.sub(r'[ _-]+model$', '', name, flags=re.I)
        parent_stem, state = ending_state(parent_stem) if ending_state(parent_stem)[1] else (parent_stem, None)
        queue = 'F10' if 'vehicle models' in cats else ('F05' if is_wearable(name) else ('F01' if 'appliance' in low else 'F09'))
    elif has(cats, 'animated tile images', 'animated images'):
        if 'my user page' in low:
            cls, reason = 'OUT_OF_SCOPE', 'Personal user-page animation unrelated to LAST LIGHT content'
            rep = 'WIKI_USER_MEDIA'
        else:
            cls, reason = 'ANIMATION_FRAME_REFERENCE', 'Possible animation research or frame sequence; verify relevance, parent action and timing before modeling'
            rep = 'ANIMATION_OR_FRAME'
            queue = 'F12'
    elif has(cats, 'texture images', 'material images', 'decals'):
        cls, reason = 'MATERIAL_TEXTURE', 'Texture, marking or decal layer; reusable material recipe or overlay, not standalone geometry'
        rep = 'MATERIAL_OR_DECAL'
        queue = 'F11'
    elif has(cats, 'flier images'):
        cls, reason = 'MEANINGFUL_VARIANT', 'Artwork/print variant of a reusable paper document or flier master; paper geometry shared'
        rep = 'PRINTED_PAPER_VARIANT'
        parent_stem = 'Paper Flier'
        queue = 'F09'
    elif has(cats, 'vegetation tile images'):
        cls, reason = 'COMPOSITION_REFERENCE', 'Source vegetation tile fragment; cluster species, growth state and seasonal appearance into botanical masters'
        rep = 'VEGETATION_TILE_FRAGMENT'
        queue = 'F04'
    elif has(cats, 'furniture tile images', 'appliance tile images', 'fixture tile images',
             'recreational tile images', 'camping tile images', 'lighting tile images',
             'carpentry tile images', 'wall tile images', 'crafted tile images',
             'location tile images', 'floor tile images', 'tile images'):
        cls, reason = 'COMPOSITION_REFERENCE', 'Numbered source tile/atlas fragment; requires component semantics and 360-model crosswalk before master admission'
        rep = 'TILE_ATLAS_FRAGMENT'
        if 'floor tile images' in cats: queue = 'F03'
        elif 'wall tile images' in cats: queue = 'F02'
        elif 'furniture tile images' in cats or 'appliance tile images' in cats: queue = 'F01'
        elif 'location tile images' in cats: queue = 'F02'
    else:
        parent_stem, state = ending_state(name)
        if state:
            cls, reason = 'STATE_OR_DIRECTION', f'{state} state of the same physical master; inspect functional geometry differences'
            rep = 'OBJECT_STATE'
            queue = 'F05' if is_wearable(name) else 'F09'
        else:
            parent_stem, variant = ending_color(name)
            if variant:
                cls, reason = 'MEANINGFUL_VARIANT', 'Color/material variant; share geometry when silhouette and gameplay are unchanged'
                rep = 'APPEARANCE_VARIANT'
                queue = 'F05' if is_wearable(name) else 'F09'
            elif is_wearable(name) and has(cats, 'item icons') and any(p in normal(name) for p in appearance_patterns):
                cls, reason = 'MEANINGFUL_VARIANT', 'Wearable fabric, print or material variant; F05 must validate silhouette and shared clothing rig before accepting a separate master'
                rep = 'CLOTHING_MATERIAL_VARIANT'
                queue = 'F05'
                parent_stem = re.split(r'[ _-]+', name)[0]
            elif has(cats, 'item icons', 'food icons', 'jewelry icons', 'weapon icons', 'tool icons', 'material icons'):
                cls, reason = 'CANONICAL_MASTER_CANDIDATE', 'Physical inventory identity candidate; gameplay necessity, duplicate master and original-art rights still unverified'
                rep = 'INVENTORY_REFERENCE_ICON'
                queue = 'F05' if is_wearable(name) else 'F09'
            elif has(cats, 'animal images'):
                cls, reason = 'COMPOSITION_REFERENCE', 'Animal research image; species and rig identity needs a separate evidence check'
                rep = 'ANIMAL_REFERENCE'
                queue = 'F07'

    parent_source = None
    if parent_stem:
        candidate = source_by_stem.get(normal(parent_stem), [])
        # Do not point to self, or promote a possible parent to canonical without independent review.
        candidate = [x for x in candidate if x['mediawiki_page_id'] != source['mediawiki_page_id']]
        parent_source = candidate[0] if candidate else None
    rows.append({
        'batch_id': BATCH,
        'source_page_id': source['mediawiki_page_id'],
        'source_title': source['title'],
        'source_url': source['file_page'],
        'source_categories': source['categories'],
        'primary_class': cls,
        'reason': reason,
        'suggested_queue': queue,
        'parent_source_page_id': parent_source['mediawiki_page_id'] if parent_source else None,
        'parent_source_title': parent_source['title'] if parent_source else None,
        'proposed_parent_stem': parent_stem,
        'representation_kind': rep,
        'state_key': state,
        'variant_key': variant,
        'master_id': VERIFIED_SOURCE_LINKS.get(source['mediawiki_page_id']),
        'semantic_status': ('LINKED_VERIFIED_MASTER_REFERENCE' if rep == 'MODEL_VIEW_REFERENCE' else 'RECONCILED_CANONICAL_MASTER_SOURCE') if source['mediawiki_page_id'] in VERIFIED_SOURCE_LINKS else 'PROVISIONAL_METADATA_TRIAGE',
        'existing_360_reconciliation': 'EXACT_NAME_MANIFEST_MATCH_GEOMETRY_UNAPPROVED' if source['mediawiki_page_id'] in VERIFIED_SOURCE_LINKS else 'PENDING_INDIVIDUAL_CROSSWALK',
        'visual_review': source['visual_review'],
        'rights': source['rights'],
        'file_page_status': source['file_page_status'],
    })

assert len(rows) == END - START == 8000
assert len({r['source_page_id'] for r in rows}) == len(rows)
assert rows[0]['source_page_id'] == 95489 and rows[-1]['source_page_id'] == 163719
assert all(x['source_url'] and x['primary_class'] and x['reason'] for x in rows)
assert len([x for x in rows if x['master_id']]) == len(VERIFIED_SOURCE_LINKS)
assert {x['master_id'] for x in rows if x['master_id']} == VERIFIED_MASTER_IDS
assert all(x['master_id'] or x['semantic_status'] == 'PROVISIONAL_METADATA_TRIAGE' for x in rows)
body = ''.join(json.dumps(r, sort_keys=True, ensure_ascii=False) + '\n' for r in rows)
OUT.write_text(body, encoding='utf-8')

counts = Counter(x['primary_class'] for x in rows)
reps = Counter(x['representation_kind'] for x in rows)
queues = Counter(x['suggested_queue'] for x in rows if x['suggested_queue'])
samples = {}
for row in rows:
    samples.setdefault(row['primary_class'], [])
    if len(samples[row['primary_class']]) < 4:
        samples[row['primary_class']].append({k:row[k] for k in ('source_page_id','source_title','source_url','reason','parent_source_page_id','suggested_queue')})
summary = {
    'batch_id': BATCH,
    'actual_fetched': len(rows), 'classified': len(rows),
    'cumulative_fetched_and_metadata_classified': END,
    'archive_offsets': {'start_inclusive': START, 'end_exclusive': END},
    'source_first': rows[0]['source_page_id'], 'source_last': rows[-1]['source_page_id'],
    'primary_classes': dict(sorted(counts.items())),
    'representations': dict(sorted(reps.items(), key=lambda pair: str(pair[0]))),
    'suggested_queue_counts': dict(sorted(queues.items())),
    'provisional_parent_source_links': sum(x['parent_source_page_id'] is not None for x in rows),
    'unresolved_parent_stems': sum(bool(x['proposed_parent_stem']) and x['parent_source_page_id'] is None for x in rows),
    'redirect_references': counts.get('DUPLICATE_ALIAS',0),
    'semantic_identities_individually_verified': len(VERIFIED_MASTER_IDS),
    'new_notion_master_rows': len(VERIFIED_MASTER_IDS),
    'source_records_linked_to_published_masters': len(VERIFIED_SOURCE_LINKS),
    'metadata_only_not_approved': len(rows)-len(VERIFIED_SOURCE_LINKS),
    'source_art_research_only_records': sum(x['rights'] == 'source_research_only' for x in rows),
    'geometry_360_index_checked': 360,
    'geometry_exact_match_source_records': 14,
    'geometry_exact_match_unique_ids': 11,
    'crosswalk_report': 'docs/asset_audit/a00_20261108_b007_360_crosswalk.json',
    'semantic_work_orders': 'docs/asset_audit/a00_20261108_b007_semantic_work_orders.jsonl',
    'metadata_class_spot_check_examples': sum(min(4, n) for n in counts.values()),
    'source_snapshot_sha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    'ledger_sha256': hashlib.sha256(body.encode()).hexdigest(),
    'next_cursor': {'offset': END, 'source_page_id_after': rows[-1]['source_page_id']},
    'remaining_after_batch': len(sources)-END,
    'golden_visual_approved_in_batch': 0,
    'class_examples_for_qa': samples,
}
SUMMARY.write_text(json.dumps(summary, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
print(json.dumps({k:v for k,v in summary.items() if k not in ('representations','class_examples_for_qa')}, indent=2))
