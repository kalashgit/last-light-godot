"""Create inspectable F05 contact sheet from Blender motion frames.

Usage: /usr/bin/python3 tools/actor_factory/f05_contact_sheet.py build/f05-cal
Uses system python3-pil; not required by Blender itself.
"""
import argparse
import base64
from pathlib import Path
from PIL import Image, ImageDraw

parser = argparse.ArgumentParser()
parser.add_argument("directory", type=Path)
parser.add_argument("--log-preview", action="store_true")
args = parser.parse_args()
folder = args.directory / "motion_frames"
clips = ("idle", "walk", "run", "sneak", "interact", "attack", "hurt", "death")
tiles = [(clip, stage) for clip in clips for stage in (0, 1)]
tile_w, tile_h = 152, 166
sheet = Image.new("RGB", (tile_w * 4, tile_h * 4), (37, 39, 44))
draw = ImageDraw.Draw(sheet)
for i, (clip, stage) in enumerate(tiles):
    path = folder / f"{clip}_{stage:02d}.png"
    if not path.is_file():
        raise SystemExit("F05_CONTACT_SHEET_MISSING_FRAME " + str(path))
    img = Image.open(path).convert("RGBA")
    img.thumbnail((128, 128))
    col, row = i % 4, i // 4
    x, y = col * tile_w + 12, row * tile_h + 8
    back = Image.new("RGBA", img.size, (81, 84, 88, 255))
    back.alpha_composite(img)
    sheet.paste(back.convert("RGB"), (x, y))
    draw.text((x, y + 132), f"{clip} {stage + 1}", fill=(239, 240, 242))
output = args.directory / "motion_contact_sheet.jpg"
sheet.save(output, "JPEG", quality=78, optimize=True)
print("F05_CONTACT_SHEET", output, "bytes", output.stat().st_size)
if args.log_preview:
    # Short labeled log lines allow a reviewer to reconstruct and inspect the
    # actual runner render without claiming the pictures are production-approved.
    raw = base64.b64encode(output.read_bytes()).decode("ascii")
    print("F05_PREVIEW_BASE64_BEGIN")
    for pos in range(0, len(raw), 180):
        print("F05_PREVIEW:" + raw[pos:pos + 180])
    print("F05_PREVIEW_BASE64_END")
