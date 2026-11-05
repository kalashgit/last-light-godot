#!/usr/bin/env python3
"""Technical checks for the founder-approved Golden 40 reference import."""
from pathlib import Path
import hashlib
import json
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'assets' / 'last_light' / 'golden40'
manifest = json.loads((ASSETS / 'manifest.json').read_text(encoding='utf-8'))
items = manifest['items']
assert manifest['schema'] == 1
assert manifest['style_approved_by_founder'] is True
assert manifest['import_status'] == 'review_gallery_only_no_gameplay_binding'
assert len(items) == manifest['count'] == 40
assert len({item['id'] for item in items}) == 40
assert len({item['reference_url'] for item in items}) == 40
assert len({item['sha256'] for item in items}) == 40
for item in items:
    assert item['representation'] == 'inventory_icon_only', item['id']
    for variant, expected_size in [('icon', 64), ('master', 128), ('reference_master', 256)]:
        path = ASSETS / item[variant]
        assert path.is_file(), path
        with Image.open(path) as image:
            assert image.mode == 'RGBA', path
            assert image.size == (expected_size, expected_size), path
            a = image.getchannel('A')
            assert a.getextrema() == (0, 255), path
            # Padding and non-clipped object silhouette.
            assert a.getbbox() is not None, path
            assert all(image.getpixel((x, y))[3] == 0 for x, y in
                       [(0, 0), (0, expected_size-1), (expected_size-1, 0), (expected_size-1, expected_size-1)]), path
    digest = hashlib.sha256((ASSETS / item['icon']).read_bytes()).hexdigest()
    assert digest == item['sha256'], item['id']

scene = (ROOT / 'scenes/golden40_gallery.tscn').read_text()
script = (ROOT / 'scripts/golden40_gallery.gd').read_text()
assert 'golden40_gallery.gd' in scene
assert 'manifest.json' in script and 'entry.icon' in script
project = (ROOT / 'project.godot').read_text()
assert 'res://main.tscn' in project
print('GOLDEN40: PASS — 40 RGBA icons, 40 working masters, 40 reference masters, hashes and preview scene')
