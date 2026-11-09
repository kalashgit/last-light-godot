#!/usr/bin/env python3
"""Create F11 diagnostic sprite review at 100%, 220%, 325% gameplay zoom.

Uses F12-compatible premultiplied-alpha outputs from existing V3 packer.
No new camera, pixel-art conversion policy, or Golden approval is asserted.
"""
import argparse
import json
from pathlib import Path
from PIL import Image, ImageDraw


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    data = json.loads((args.source / "manifest.json").read_text())
    assert len(data["items"]) == 3
    zoom = (1.0, 2.2, 3.25)
    # Largest sofa sprite at 325% is ~393px wide; preserve breathing room.
    width, height = 460, 450
    sheet = Image.new("RGB", (3 * width, len(zoom) * height), (126, 135, 122))
    draw = ImageDraw.Draw(sheet)
    for row, factor in enumerate(zoom):
        for col, record in enumerate(data["items"]):
            with Image.open(args.source / record["world_sprite"]) as im:
                sprite = im.convert("RGBA")
                size = (round(sprite.width * factor), round(sprite.height * factor))
                sprite = sprite.resize(size, Image.Resampling.NEAREST)
                tile = Image.new("RGBA", (width, height), (126, 135, 122, 255))
                x = (width - sprite.width) // 2
                y = min(height - sprite.height, 80 + max(0, (height - 160 - sprite.height) // 2))
                tile.alpha_composite(sprite, (x, y))
                sheet.paste(tile.convert("RGB"), (col * width, row * height))
                draw.text((col * width + 12, row * height + 15),
                          f"{record['name']} / {factor * 100:g}% native nearest",
                          fill="white", stroke_width=1, stroke_fill="black")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(args.out)
    print("LL_F11_NATIVE_ZOOM_REVIEW_READY", len(data["items"]), "heroes", len(zoom), "zoom levels")


if __name__ == "__main__":
    main()
