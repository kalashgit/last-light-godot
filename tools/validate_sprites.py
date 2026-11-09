"""Validate offline sprite output: python tools/validate_sprites.py OUTPUT_DIR."""
import json
import sys
from pathlib import Path
from PIL import Image

folder = Path(sys.argv[1])
manifest = json.loads((folder / 'manifest.json').read_text())
assert manifest['schema'] == 1
assert manifest['tile_px'] == [80, 40]
assert manifest['source'] and manifest['license']
for frame in manifest['frames']:
    image = Image.open(folder / frame['file'])
    assert image.mode == 'RGBA', image.mode
    assert list(image.size) == manifest['canvas_px']
    alpha = image.getchannel('A')
    box = alpha.getbbox()
    assert box, 'Empty image'
    assert min(alpha.getextrema()) == 0, 'No transparent background'
    assert box[0] > 0 and box[1] > 0 and box[2] < image.width and box[3] < image.height, 'Clipped sprite: enlarge common canvas'
    assert frame['anchor_px'] == [128, 192]
print(f"PASS: {len(manifest['frames'])} RGBA frames, dimensions, padding, anchors and provenance")
