#!/usr/bin/env python3
"""LAST LIGHT Unified Content Factory: UCF-001 deterministic layout compiler.

Standard-library-only, offline and safe on iPhone Python environments.
This stage produces original geometry / placement manifests, not finished art.

Usage: python tools/unified_content_factory.py [--seed 20261106] [--out PATH]
       python tools/unified_content_factory.py --verify PATH
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
from pathlib import Path

VERSION = 'ucf-001.0'
SCHEMA = 'last_light.unified_world.v1'
RECIPE_SCHEMA = 'last_light.district_recipe.v1'
ROOM_SET = ['kitchen', 'bedroom', 'bathroom', 'living']
ASSET_BY_ROOM = {
    'kitchen': 'll_furniture_kitchen_counter',
    'bedroom': 'll_furniture_single_bed',
    'bathroom': 'll_furniture_toilet',
    'living': 'll_furniture_two_seat_sofa',
}
MATERIAL_SETS = [
    {'walls': 'plaster_cream', 'floor': 'wood_oak', 'roof': 'shingle_asphalt'},
    {'walls': 'brick_aged', 'floor': 'wood_oak', 'roof': 'standing_seam_metal'},
    {'walls': 'plaster_cream', 'floor': 'tile_ceramic', 'roof': 'shingle_asphalt'},
]
DEFAULT_RECIPE = {
    'schema': RECIPE_SCHEMA,
    'district_id': 'll.district.demo_street',
    'world_seed': 20261106,
    'road': {'id': 'll.road.main', 'rect': [0, 14, 43, 4], 'material': 'asphalt_worn'},
    'lots': [
        {'id': 'll.lot.001', 'rect': [0, 0, 13, 14], 'archetype_id': 'house_small', 'variant': 0},
        {'id': 'll.lot.002', 'rect': [15, 0, 13, 14], 'archetype_id': 'house_small', 'variant': 1},
        {'id': 'll.lot.003', 'rect': [30, 0, 13, 14], 'archetype_id': 'house_small', 'variant': 2},
    ],
}


def derive_seed(seed: int, *parts: object) -> int:
    data = '|'.join(str(v) for v in (VERSION, seed, *parts)).encode('utf-8')
    return int.from_bytes(hashlib.sha256(data).digest()[:8], 'big')


def overlaps(a: list[int], b: list[int]) -> bool:
    return a[0] < b[0] + b[2] and b[0] < a[0] + a[2] and a[1] < b[1] + b[3] and b[1] < a[1] + a[3]


def contains(outer: list[int], inner: list[int]) -> bool:
    return inner[0] >= outer[0] and inner[1] >= outer[1] and inner[0] + inner[2] <= outer[0] + outer[2] and inner[1] + inner[3] <= outer[1] + outer[3]


def validate_recipe(recipe: dict) -> None:
    if recipe.get('schema') != RECIPE_SCHEMA:
        raise ValueError('Invalid recipe schema')
    road = recipe.get('road')
    lots = recipe.get('lots')
    if not isinstance(road, dict) or not isinstance(lots, list) or not lots:
        raise ValueError('Missing road or lots')
    road_rect = road.get('rect')
    if not isinstance(road_rect, list) or len(road_rect) != 4 or min(road_rect[2:]) <= 0:
        raise ValueError('Invalid road geometry')
    ids = set()
    for lot in lots:
        if lot.get('archetype_id') != 'house_small':
            raise ValueError('UCF-001 supports house_small only; other archetypes are future work')
        rect = lot.get('rect')
        if not isinstance(rect, list) or len(rect) != 4 or min(rect[2:]) < 9:
            raise ValueError('Invalid lot geometry')
        if lot['id'] in ids:
            raise ValueError('Duplicate lot ID')
        ids.add(lot['id'])
        if overlaps(rect, road_rect):
            raise ValueError('Lot overlaps road')
        # This pilot's houses must access the horizontal road from the south.
        if rect[1] + rect[3] != road_rect[1] or not (road_rect[0] <= rect[0] and rect[0] + rect[2] <= road_rect[0] + road_rect[2]):
            raise ValueError('Lot must adjoin road')
    for i, lot in enumerate(lots):
        for other in lots[i + 1:]:
            if overlaps(lot['rect'], other['rect']):
                raise ValueError('Overlapping lots')


def build_house(lot: dict, world_seed: int) -> dict:
    seed = derive_seed(world_seed, lot['id'], 'house')
    rng = random.Random(seed)
    # World seed rotates the distinct approved shape/layout families, while
    # lot.variant guarantees three different houses within the pilot street.
    index = (int(lot.get('variant', 0)) + world_seed % 3) % 3
    width = [8, 9, 10][index]
    height = [8, 9, 8][index]
    lot_rect = lot['rect']
    house_x = lot_rect[0] + (lot_rect[2] - width) // 2
    house_y = lot_rect[1] + 1 + (index == 1)
    bounds = [house_x, house_y, width, height]
    hall_width = 2
    left_width = width // 2 - 1
    hall_x = house_x + left_width
    right_x = hall_x + hall_width
    right_width = width - (left_width + hall_width)
    top_height = height // 2
    bottom_height = height - top_height
    # Every variant changes physical width and/or height, layout, roof, facade and porch.
    arrangements = [
        ['kitchen', 'bedroom', 'living', 'bathroom'],
        ['bedroom', 'bathroom', 'kitchen', 'living'],
        ['bathroom', 'kitchen', 'living', 'bedroom'],
    ]
    mapping = arrangements[index]
    regions = [
        [house_x, house_y, left_width, top_height],
        [right_x, house_y, right_width, top_height],
        [house_x, house_y + top_height, left_width, bottom_height],
        [right_x, house_y + top_height, right_width, bottom_height],
    ]
    house_id = f"{lot['id']}.b01"
    rooms = []
    doors = []
    fixtures = []
    for i, (room_type, rect) in enumerate(zip(mapping, regions)):
        room_id = f'{house_id}.r{i + 1:02d}'
        wall_x = hall_x if i % 2 == 0 else right_x
        mid_y = rect[1] + rect[3] // 2
        door_id = f'{room_id}.door'
        doors.append({'id': door_id, 'type': 'interior', 'pos': [wall_x, mid_y], 'width': 1, 'connects': [room_id, f'{house_id}.hall']})
        rooms.append({'id': room_id, 'type': room_type, 'rect': rect, 'door_id': door_id, 'loot_tags': [room_type], 'seed': derive_seed(world_seed, room_id)})
        # Place one functional prop near a far wall, away from corridor doors.
        side_x = rect[0] if i % 2 == 0 else rect[0] + rect[2] - 1
        fixtures.append({'id': f'{room_id}.fixture01', 'room_id': room_id, 'asset_id': ASSET_BY_ROOM[room_type], 'pos': [side_x + 0.5, rect[1] + 1.0], 'status': 'placeholder_placement'})
    hall = [hall_x, house_y, hall_width, height]
    door_pos = [hall_x + hall_width // 2, house_y + height]
    doors.append({'id': f'{house_id}.entry', 'type': 'exterior', 'pos': door_pos, 'width': 1, 'connects': [f'{house_id}.hall', 'exterior']})
    porch = [door_pos[0] - 1, door_pos[1], 3 if index != 2 else 4, 1]
    footpath = {'id': f'{house_id}.path', 'from': [door_pos[0], door_pos[1] + 1], 'to': [door_pos[0], lot_rect[1] + lot_rect[3]], 'material': 'paver_gray'}
    mats = MATERIAL_SETS[index].copy()
    mats['wear'] = rng.choice(['clean', 'worn', 'weathered'])
    return {'id': house_id, 'lot_id': lot['id'], 'archetype_id': 'house_small', 'seed': seed,
            'bounds': bounds, 'hall': {'id': f'{house_id}.hall', 'rect': hall},
            'rooms': rooms, 'doors': doors, 'fixtures': fixtures, 'porch': porch,
            'path': footpath, 'materials': mats, 'roof_profile': ['gable', 'hip', 'offset_gable'][index],
            'layout_variant': index, 'state': {'roof_cutaway': 'runtime', 'loot_seed': derive_seed(world_seed, house_id, 'loot')}}


def compile_world(recipe: dict, seed_override: int | None = None) -> dict:
    validate_recipe(recipe)
    world_seed = int(recipe.get('world_seed', 20261106)) if seed_override is None else seed_override
    buildings = [build_house(lot, world_seed) for lot in recipe['lots']]
    world = {'schema': SCHEMA, 'factory_version': VERSION, 'recipe_schema': recipe['schema'],
             'district_id': recipe['district_id'], 'world_seed': world_seed,
             'projection': {'tile_px': [80, 40], 'iso_x': 40, 'iso_y': 20},
             'road': recipe['road'], 'lots': recipe['lots'], 'buildings': buildings,
             'content_status': 'generated_layout_candidate',
             'art_status': 'existing_asset_references_plus_original_geometry_placeholders'}
    validate_world(world)
    return world


def validate_world(world: dict) -> None:
    if world.get('schema') != SCHEMA:
        raise ValueError('Invalid generated world schema')
    all_ids = set()
    footprints = []
    lot_by_id = {x['id']: x['rect'] for x in world['lots']}
    for b in world['buildings']:
        if b['id'] in all_ids:
            raise ValueError('Duplicate building ID')
        all_ids.add(b['id'])
        if not contains(lot_by_id[b['lot_id']], b['bounds']):
            raise ValueError('Building leaves its lot')
        if any(overlaps(b['bounds'], prior) for prior in footprints):
            raise ValueError('Buildings overlap')
        footprints.append(b['bounds'])
        hall_id = b['hall']['id']
        room_ids = {r['id'] for r in b['rooms']}
        if len(room_ids) != 4 or set(r['type'] for r in b['rooms']) != set(ROOM_SET):
            raise ValueError('Invalid room coverage')
        for rect in (r['rect'] for r in b['rooms']):
            if not contains(b['bounds'], rect) or overlaps(rect, b['hall']['rect']):
                raise ValueError('Room outside footprint or into hall')
        for a, room in enumerate(b['rooms']):
            if any(overlaps(room['rect'], other['rect']) for other in b['rooms'][a + 1:]):
                raise ValueError('Rooms overlap')
        doors = b['doors']
        if sum(d['type'] == 'exterior' and 'exterior' in d['connects'] for d in doors) != 1:
            raise ValueError('Building missing exterior exit')
        for room_id in room_ids:
            if sum(set(d['connects']) == {room_id, hall_id} for d in doors) != 1:
                raise ValueError('Room not connected to corridor')
        for item in [*b['rooms'], *doors, *b['fixtures'], b['path'], b['hall']]:
            object_id = item['id']
            if object_id in all_ids:
                raise ValueError('Duplicate world instance ID')
            all_ids.add(object_id)
        if b['path']['to'][1] != world['road']['rect'][1]:
            raise ValueError('House footpath fails to meet road')
    if len(world['buildings']) != len(world['lots']):
        raise ValueError('Not every lot has a building')


def dumps(data: dict) -> bytes:
    return (json.dumps(data, sort_keys=True, indent=2, ensure_ascii=False) + '\n').encode('utf-8')


def atomic_write(path: Path, raw: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_bytes(raw)
    temp.replace(path)


def main(argv: list[str] | None = None) -> int:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--recipe', type=Path, default=root / 'data/factory/ucf001_street_recipe.json')
    parser.add_argument('--out', type=Path, default=root / 'data/generated/unified_factory/ucf001_street.json')
    parser.add_argument('--seed', type=int)
    parser.add_argument('--verify', type=Path, help='Validate an existing generated world JSON instead of writing')
    args = parser.parse_args(argv)
    if args.verify:
        world = json.loads(args.verify.read_text('utf-8'))
        validate_world(world)
        print('PASS', args.verify, 'buildings=', len(world['buildings']))
        return 0
    # Standalone iPhone copy works without the separate repo recipe.
    recipe = json.loads(args.recipe.read_text('utf-8')) if args.recipe.exists() else DEFAULT_RECIPE
    world = compile_world(recipe, args.seed)
    raw = dumps(world)
    atomic_write(args.out, raw)
    print('LAST LIGHT UCF-001 layout compiler')
    print('Output:', args.out)
    print('Buildings:', len(world['buildings']), '| Rooms:', sum(len(b['rooms']) for b in world['buildings']))
    print('Seed:', world['world_seed'], '| SHA256:', hashlib.sha256(raw).hexdigest())
    print('Note: geometry/layout candidate, not Golden 40 final art or an iPhone-verified Godot integration')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())