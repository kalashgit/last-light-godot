#!/usr/bin/env python3
"""LL-103 schema-1 authoring gate. Standard library only, diagnostics not exceptions."""
import argparse
import json
import math
import re
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
CONTRACT = json.loads((ROOT/'data/catalog/contracts_v1.json').read_text())
PARTS = tuple(CONTRACT['sections'])
PREFIX = CONTRACT['sections']
ID_RE = re.compile(r'^(item|prop|building|vehicle|entity|loot)[.][a-z][a-z0-9_]*(?:[.][a-z][a-z0-9_]*)*$')
ASSET_RE = re.compile(r'^asset[.][a-z][a-z0-9_]*(?:[.][a-z][a-z0-9_]*)*$')
def text(value): return isinstance(value,str) and bool(value.strip())
def strings(value): return isinstance(value,list) and all(text(v) for v in value) and len(set(value))==len(value)
def number(value): return type(value) in (float,int) and math.isfinite(value)
def validate_visuals(visuals):
    errors=[]
    if not isinstance(visuals,dict) or not number(visuals.get('schema')) or visuals['schema']!=1 or not isinstance(visuals.get('assets'),dict):
        return ['visuals: schema 1 and assets object required']
    for ident,asset in visuals['assets'].items():
        if not isinstance(ident,str) or not ASSET_RE.fullmatch(ident): errors.append(f'visuals: bad asset id {ident}')
        if not isinstance(asset,dict): errors.append(f'{ident}: expected asset object'); continue
        path=asset.get('path')
        if not text(path) or not path.startswith('res://') or '..' in path.split('/') or not (ROOT/path[6:]).is_file(): errors.append(f'{ident}: missing asset file')
        size=asset.get('size_px'); anchor=asset.get('anchor_px')
        if not isinstance(size,list) or len(size)!=2 or not all(number(v) and int(v)==v and 0<v<=2048 for v in size): errors.append(f'{ident}: invalid size_px')
        if not isinstance(anchor,list) or len(anchor)!=2 or not all(number(v) for v in anchor): errors.append(f'{ident}: invalid anchor_px')
        if not text(asset.get('source')) or not text(asset.get('license')): errors.append(f'{ident}: source and license required')
    return errors

def validate(data, visuals=None):
    if visuals is None: visuals=json.loads((ROOT/'data/catalog/visuals_v1.json').read_text())
    errors=validate_visuals(visuals)
    assets=visuals.get('assets',{}) if isinstance(visuals,dict) else {}
    if not isinstance(assets,dict): assets={}
    if not isinstance(data,dict): return errors+['catalog: expected object']
    if not number(data.get('schema')) or data['schema']!=1: errors.append('schema must equal 1')
    vocab=data.get('capability_vocabulary')
    if not strings(vocab) or set(vocab)!=set(CONTRACT['capabilities']): errors.append('invalid capability vocabulary')
    index={}; records={}
    for section in PARTS:
        entries=data.get(section)
        if not isinstance(entries,list): errors.append(f'{section}: expected array'); records[section]=[]; continue
        records[section]=[r for r in entries if isinstance(r,dict)]
        for offset,rec in enumerate(entries):
            key=f'{section}[{offset}]'
            if not isinstance(rec,dict): errors.append(f'{key}: expected object'); continue
            ident=rec.get('id')
            if not text(ident) or not ID_RE.fullmatch(ident) or not ident.startswith(PREFIX[section]): errors.append(f'{key}: bad id'); continue
            if ident in index: errors.append(f'{key}: duplicate id {ident}')
            index[ident]=section
            if section!='loot_profiles' and not text(rec.get('name')): errors.append(f'{ident}: name required')
            if section in ('items','props','vehicles'):
                caps=rec.get('capabilities')
                if not strings(caps): errors.append(f'{ident}: capabilities must be unique strings')
                elif any(c not in CONTRACT['capabilities'] for c in caps): errors.append(f'{ident}: unknown capability')
            if section=='items':
                if not text(rec.get('category')): errors.append(f'{ident}: category required')
                if not number(rec.get('weight_kg')) or rec['weight_kg']<0: errors.append(f'{ident}: invalid weight_kg')
                if not number(rec.get('stack_max')) or rec['stack_max']<1 or int(rec['stack_max'])!=rec['stack_max']: errors.append(f'{ident}: invalid stack_max')
                visual=rec.get('visual')
                refs=[visual.get(v) for v in ('icon','ground')] if isinstance(visual,dict) else [None]
            elif section in ('props','vehicles','enemies'): refs=[rec.get('visual')]
            else: refs=[]
            for ref in refs:
                if not text(ref) or ref not in assets: errors.append(f'{ident}: unknown visual asset {ref!r}')
            if section=='enemies' and not text(rec.get('behavior')): errors.append(f'{ident}: behavior required')
    def references(rec,field,target,label):
        values=rec.get(field)
        if not strings(values): errors.append(f'{rec.get("id")}: {field} must be unique strings'); return
        for value in values:
            if index.get(value)!=target: errors.append(f'{rec.get("id")}: unknown {label} {value}')
    for rec in records['buildings']:
        profile=rec.get('loot_profile')
        if not text(profile) or index.get(profile)!='loot_profiles': errors.append(f'{rec.get("id")}: unknown loot_profile')
        if not strings(rec.get('rooms')) or not rec['rooms']: errors.append(f'{rec.get("id")}: rooms missing')
        references(rec,'starter_props','props','starter prop')
    for rec in records['loot_profiles']: references(rec,'entries','items','loot item')
    return errors

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('catalog',nargs='?',default=str(ROOT/'data/catalog/starter_v1.json')); args=parser.parse_args()
    try: data=json.loads(Path(args.catalog).read_text(encoding='utf-8')); errors=validate(data)
    except (OSError,ValueError) as e: print('CATALOG FAIL:',e,file=sys.stderr); return 1
    if errors:
        for error in errors: print('CATALOG ERROR:',error,file=sys.stderr)
        return 1
    print('CATALOG PASS: '+', '.join(f'{p}={len(data[p])}' for p in PARTS)+'; definitions validated, gameplay integration pending')
    return 0
if __name__=='__main__': raise SystemExit(main())
