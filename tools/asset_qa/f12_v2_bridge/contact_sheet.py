#!/usr/bin/env python3
"""Native-size QA contact sheet for an LL_ATLAS_OUTPUTS_V2 package.

Rows = frames (clip/direction order). Columns = 100%, 220%, 325% nearest-neighbour
zoom, each over light / dark / grass-green backgrounds with the 80x40 ground
diamond drawn at the ground pivot. Visual evidence only; not an approval.
"""
import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw

ZOOMS = (1.0, 2.2, 3.25)
BACKGROUNDS = ((236, 232, 222, 255), (28, 30, 34, 255), (74, 96, 52, 255))


def frame_image(root, doc, f):
    page = Image.open(root / doc["pages"][f["page"]]["file"]).convert("RGBA")
    x, y, w, h = f["rect"]
    cw, ch = f["canvas_px"]
    tx, ty = f["trim_offset_px"]
    canvas = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    canvas.paste(page.crop((x, y, x + w, y + h)), (tx, ty))
    return canvas


def cell(img, pivot, zoom, bg):
    w, h = img.size
    zw, zh = round(w * zoom), round(h * zoom)
    out = Image.new("RGBA", (zw, zh), bg)
    d = ImageDraw.Draw(out)
    gx, gy = pivot[0] * zoom, pivot[1] * zoom
    d.polygon([(gx - 40 * zoom, gy), (gx, gy - 20 * zoom), (gx + 40 * zoom, gy), (gx, gy + 20 * zoom)],
              outline=(255, 64, 64, 255))
    out.alpha_composite(img.resize((zw, zh), Image.NEAREST))
    d = ImageDraw.Draw(out)
    d.line([(gx - 3, gy), (gx + 3, gy)], fill=(0, 255, 255, 255))
    d.line([(gx, gy - 3), (gx, gy + 3)], fill=(0, 255, 255, 255))
    return out


def build(outputs_path: Path, dest: Path):
    root = outputs_path.parent
    doc = json.loads(outputs_path.read_text())
    frames = sorted(doc["frames"], key=lambda f: (f["clip"], f["direction"], f["frame_index"]))
    rows = []
    for f in frames:
        img = frame_image(root, doc, f)
        cells = [cell(img, f["ground_pivot_px"], z, bg) for z in ZOOMS for bg in BACKGROUNDS]
        rows.append((f["key"], cells))
    pad, label_h = 6, 14
    width = pad + sum(c.size[0] + pad for c in rows[0][1])
    height = sum(max(c.size[1] for c in cs) + label_h + pad for _, cs in rows) + pad
    sheet = Image.new("RGBA", (width, height), (128, 128, 128, 255))
    d = ImageDraw.Draw(sheet)
    y = pad
    for key, cells in rows:
        d.text((pad, y), f"{key}   zoom 1.0 / 2.2 / 3.25   CALIBRATION ONLY - NOT GOLDEN", fill=(0, 0, 0, 255))
        x = pad
        for c in cells:
            sheet.alpha_composite(c, (x, y + label_h))
            x += c.size[0] + pad
        y += max(c.size[1] for c in cells) + label_h + pad
    dest.parent.mkdir(parents=True, exist_ok=True)
    sheet.convert("RGB").save(dest, format="PNG", optimize=True)
    return dest


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("outputs", type=Path)
    ap.add_argument("--output", type=Path, required=True)
    a = ap.parse_args()
    print(build(a.outputs, a.output))
