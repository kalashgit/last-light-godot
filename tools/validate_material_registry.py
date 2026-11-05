#!/usr/bin/env python3
"""Validate offline runtime material contracts and all existing kit/lab references."""
import hashlib
import json
import re
from pathlib import Path
from PIL import Image
ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / 'assets/materials/runtime_materials_v1.json'


def validate(data, root=ROOT):
    errors = []
    def check(ok, message):
        if not ok:
            errors.append(message)
    if not isinstance(data, dict):
        return ['registry must be an object']
    check(data.get('schema_version') == 1, 'unsupported schema')
    check(data.get('projection') == {'tile_px': [80, 40], 'pixels_per_unit': [40, 20]}, 'projection mismatch')
    assets, entries = data.get('assets'), data.get('materials')
    if not isinstance(assets, dict) or not isinstance(entries, list):
        return errors + ['invalid collections']
    loaded = {}
    for aid, asset in assets.items():
        if not isinstance(asset, dict):
            errors.append(f'invalid asset: {aid}')
            continue
        path = asset.get('path', '')
        local = (root / path.removeprefix('res://')).resolve()
        if not path.startswith('res://') or not local.is_relative_to(root.resolve()) or not local.is_file():
            errors.append(f'missing/unsafe asset: {aid}')
            continue
        check(hashlib.sha256(local.read_bytes()).hexdigest() == asset.get('sha256'), f'asset checksum: {aid}')
        with Image.open(local) as image:
            check(list(image.size) == asset.get('size_px'), f'asset dimensions: {aid}')
            loaded[aid] = image.size
            if asset.get('repeatable'):
                check(list(image.crop((0, 0, 1, image.height)).getdata()) == list(image.crop((image.width-1, 0, image.width, image.height)).getdata()), f'horizontal seam: {aid}')
                check(list(image.crop((0, 0, image.width, 1)).getdata()) == list(image.crop((0, image.height-1, image.width, image.height)).getdata()), f'vertical seam: {aid}')
    ids = set()
    for entry in entries:
        if not isinstance(entry, dict):
            errors.append('invalid entry')
            continue
        mid = entry.get('id', '')
        check(isinstance(mid, str) and re.fullmatch(r'[a-z][a-z0-9_]*', mid) and mid not in ids, f'invalid/duplicate ID: {mid}')
        ids.add(mid)
        check(entry.get('surfaces') in [['wall'], ['floor'], ['roof']], f'invalid surface: {mid}')
        palette = entry.get('palette')
        check(isinstance(palette, dict) and isinstance(palette.get('base'), str) and re.fullmatch(r'[0-9a-f]{6}', palette['base']), f'palette: {mid}')
        check(entry.get('tile_px') == [80, 40] and entry.get('world_cell_m') == 1, f'scale: {mid}')
        check(entry.get('spec_id') in data.get('specs', {}), f'missing source specification: {mid}')
        asset = entry.get('asset_id')
        check(asset is None or asset in assets, f'missing asset reference: {mid}')
        region = entry.get('atlas_region_px')
        if region is not None:
            valid = isinstance(region, list) and len(region) == 4 and all(isinstance(v, int) for v in region)
            check(valid, f'invalid region: {mid}')
            if valid:
                x, y, w, h = region
                size = loaded.get(asset, (0, 0))
                check(x >= 0 and y >= 0 and w > 2 and h > 2 and x+w <= size[0] and y+h <= size[1], f'atlas bounds: {mid}')
    return errors


def validate_bindings(data, catalog, lab):
    errors = []
    entries = {e['id']: e for e in data['materials']}
    def surface(mid, kind, context):
        if mid not in entries or kind not in entries[mid]['surfaces']:
            errors.append(f'{context}: incompatible/missing {kind} material {mid}')
    for kit, values in catalog['material_kits'].items():
        for key in ('wall', 'floor', 'roof', 'secondary_floor'):
            surface(values[key], 'floor' if key == 'secondary_floor' else key, kit)
    for building in lab['buildings']:
        for key in ('wall', 'floor', 'roof'):
            surface(building[key], key, building['id'])
        for zone in building.get('floor_zones', []):
            surface(zone['material'], 'floor', building['id'])
        for part in building.get('partitions', []):
            if 'material' in part:
                surface(part['material'], 'wall', building['id'])
    return errors


def main():
    data = json.loads(REGISTRY.read_text())
    errors = validate(data)
    if not errors:
        errors += validate_bindings(data, json.loads((ROOT / 'assets/buildings/building_archetypes_v1.json').read_text()), json.loads((ROOT / 'assets/buildings/five_building_lab_v2.json').read_text()))
    if errors:
        raise SystemExit('\n'.join(errors))
    print(f"PASS: {len(data['materials'])} runtime materials, {len(data['assets'])} shared textures, 8 kit and 5 live-building bindings")


if __name__ == '__main__':
    main()
