#!/usr/bin/env python3
"""Conservative 3114-candidate crosswalk to actual LAST LIGHT game/import data.

This is a production-necessity evidence layer, not automatic Notion admission.
"""
from collections import Counter
from pathlib import Path
import json
import re

ROOT=Path(__file__).resolve().parent
REPO=ROOT.parents[1]
PREFIXES=('llfood','llmedical','llhousehold','lltools','llcrafting','llfurniture','llgolden','llvehicle','llclothing','llweapon','llactor','llcharacter')

def token(s):
    normalized=re.sub('[^a-z0-9]', '',str(s).lower())
    for prefix in PREFIXES:
        if normalized.startswith(prefix):return normalized[len(prefix):]
    return normalized

def main():
    source=[]
    for p in sorted(ROOT.glob('a00_r02_review_*.jsonl')):
        source.extend(json.loads(s) for s in p.read_text().splitlines())
    original=[x for x in source if x['decision']=='PHYSICAL_MASTER_CANDIDATE']
    assert len(original)==3114
    gameplay=json.loads((REPO/'data/survival_items.json').read_text())['items']
    golden=json.loads((REPO/'data/golden40_items.json').read_text())['items']
    imported=json.loads((REPO/'assets/generated/master_import_v1/catalog.json').read_text())['resources']
    indexes={}
    for kind,values in [('live_survival',gameplay),('golden40_prototype',golden),('import_candidate',imported)]:
        mapping={}
        for v in values:
            value=v.get('stable_id') or v.get('id')
            if value:mapping.setdefault(token(value),set()).add(value)
        indexes[kind]=mapping
    out=[]
    for r in original:
        key=token(r['key'])
        matches={kind:sorted(ids.get(key,set())) for kind,ids in indexes.items()}
        model_ids=sorted(set(r.get('model_ids') or []))
        if matches['live_survival']:
            tier='LIVE_GAMEPLAY_IDENTITY_MATCH'
        elif matches['golden40_prototype']:
            tier='GOLDEN40_METADATA_IDENTITY_MATCH_NOT_VISUAL_APPROVAL'
        elif matches['import_candidate']:
            tier='TECHNICAL_ART_RESOURCE_MATCH'
        elif model_ids:
            tier='EXISTING_BLENDER_SOURCE_NAME_MATCH'
        else:
            tier='GAMEPLAY_NECESSITY_NOT_YET_DEMONSTRATED'
        out.append({'source_page_id':r['id'],'source_title':r['title'],'semantic_key':r['key'],
                    'family':r['family'],'evidence_tier':tier,'matches':matches,
                    'existing_360_model_ids':model_ids,
                    'identity_confidence':'exact_normalized_token_match_only',
                    'canonical_admitted':False,'visual_approved':False})
    dest=ROOT/'a00_r06_physical_candidates_3114.jsonl'
    dest.write_text(''.join(json.dumps(x,sort_keys=True)+'\n' for x in out))
    report={
        'candidate_references':len(out),
        'distinct_provisional_semantic_keys':len({(x['family'],x['semantic_key']) for x in out}),
        'evidence_tiers':dict(Counter(x['evidence_tier'] for x in out)),
        'live_survival_items_defined':len(gameplay),
        'golden40_prototype_items_defined':len(golden),
        'technical_import_resources_defined':len(imported),
        'scope':'Source-name-to-existing-game-ID reconciliation; not proof of physical geometry match, visual quality or gameplay necessity.',
        'source_art_rights':'research_only',
        'new_canonical_masters':0,
    }
    (ROOT/'a00_r06_gameplay_crosswalk_summary.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
