#!/usr/bin/env python3
"""Generate original architectural material-kit preview art (not runtime sprites).

Outputs a contact sheet for human review. Geometry, wall texture, roof and floor
composition deliberately align to a 2:1 isometric presentation. No source art.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

from building_factory import ROOT, load_catalog

OUTPUT = ROOT / "assets/generated/architecture"

PALETTE = {
    "plaster_cream": "#c5b99d", "concrete_block": "#898f89", "brick_aged": "#9b6c5c", "metal_panel": "#778385",
    "shingle_asphalt": "#58666c", "standing_seam_metal": "#768486", "flat_membrane": "#616968",
    "wood_oak": "#8a7051", "tile_ceramic": "#b8b8ab", "concrete_stained": "#777c76", "vinyl_check": "#a7a99d"
}


def shade(value: str, multiplier: float) -> tuple[int, int, int]:
    rgb = tuple(int(value[1+i:3+i], 16) for i in (0, 2, 4))
    return tuple(max(0, min(255, round(channel * multiplier))) for channel in rgb)


def roof_strokes(draw: ImageDraw.ImageDraw, material: str, x: int, y: int) -> None:
    dark = shade(PALETTE[material], .74)
    light = shade(PALETTE[material], 1.21)
    if material == "shingle_asphalt":
        for index in range(1, 6):
            offset = index * 7
            draw.line([(x-80+offset*2, y-43+offset), (x+offset*2, y-82+offset)], fill=dark, width=1)
    elif material == "standing_seam_metal":
        for index in range(1, 6):
            t = index/6
            draw.line([(round(x-85+85*t), y-47-round(36*t)),
                       (round(x+85*t), y-83+round(36*t))], fill=light, width=2)
    else:
        for index in range(1, 4):
            dy = index * 9
            draw.line([(x-74+dy*2, y-48+dy), (x+dy*2, y-83+dy)], fill=dark, width=1)


def kit_preview(draw: ImageDraw.ImageDraw, kit_id: str, kit: dict, index: int) -> None:
    col, row = index % 4, index // 4
    left, top = 22 + col * 337, 22 + row * 305
    x, y = left + 118, top + 158
    draw.rounded_rectangle((left, top, left + 320, top + 280), radius=13,
                           fill="#233033", outline="#60706a", width=2)
    draw.text((left + 16, top + 12), kit_id.upper(), fill="#e6dfcb", font=ImageFont.load_default())
    # Floor with a readable single-cell diamond and a darker edge.
    floor = PALETTE[kit["floor"]]
    draw.polygon([(x, y-42), (x+105, y+6), (x, y+52), (x-105, y+6)],
                 fill=shade(floor, 1.05), outline=shade(floor, .62), width=3)
    for t in (.33, .66):
        ax, ay = round(x-103+103*t), round(y+6-48*t)
        bx, by = round(x+103*t), round(y-42+48*t)
        draw.line((ax, ay, bx, by), fill=shade(floor, .82), width=1)
    # Structural faces and roof always share the world anchor of the floor.
    wall = PALETTE[kit["wall"]]
    draw.polygon([(x-85, y-7), (x, y+31), (x, y-26), (x-85, y-47)],
                 fill=shade(wall, .77), outline=shade(wall, .58))
    draw.polygon([(x, y+31), (x+85, y-7), (x+85, y-47), (x, y-26)],
                 fill=shade(wall, 1.02), outline=shade(wall, .72))
    if kit["wall"] == "brick_aged":
        for dy in range(10, 50, 10):
            draw.line((x, y+26-dy, x+82, y-11-dy), fill=shade(wall, .70), width=1)
    elif kit["wall"] == "metal_panel":
        for t in (.25, .5, .75):
            draw.line((x+85*t, y+31-38*t, x+85*t, y-26-39*t), fill=shade(wall, 1.14), width=1)
    else:
        draw.line((x, y+22, x+85, y-16), fill=shade(wall, .77), width=2)
    roof = PALETTE[kit["roof"]]
    roof_poly = [(x, y-83), (x+85, y-47), (x, y-9), (x-85, y-47)]
    draw.polygon(roof_poly, fill=roof, outline=shade(roof, .62), width=3)
    roof_strokes(draw, kit["roof"], x, y)
    # Short swatch labels keep kit distinctions visible on iPhone zoom.
    labels = [("W", kit["wall"]), ("R", kit["roof"]), ("F", kit["floor"])]
    draw.line((left + 14, top + 229, left + 305, top + 229), fill="#475b57", width=1)
    for j, (prefix, name) in enumerate(labels):
        draw.rectangle((left + 15, top + 238 + j*13, left + 22, top + 245 + j*13), fill=PALETTE[name])
        draw.text((left + 29, top + 235 + j*13), f"{prefix} {name}", fill="#d6ded3", font=ImageFont.load_default())
    draw.text((left+210, top+15), "ORIGINAL / WIP", fill="#a5b29d", font=ImageFont.load_default())


def main() -> None:
    catalog = load_catalog()
    image = Image.new("RGB", (1392, 634), "#152324")
    draw = ImageDraw.Draw(image)
    for i, (kit_id, kit) in enumerate(catalog["material_kits"].items()):
        kit_preview(draw, kit_id, kit, i)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    filename = OUTPUT / "kit_contact_sheet_v1.png"
    image.save(filename, optimize=True)
    manifest = {
        "schema_version": 1,
        "asset": "kit_contact_sheet_v1.png",
        "source": "original_procedural_Pillow_shapes_no_external_assets",
        "status": "contact_sheet_requires_visual_approval_not_runtime_art",
        "projection": catalog["projection"],
        "kit_ids": list(catalog["material_kits"]),
        "size_px": list(image.size),
        "sha256": hashlib.sha256(filename.read_bytes()).hexdigest(),
        "generator": "tools/generate_building_kit_previews.py",
    }
    (OUTPUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Generated {len(catalog['material_kits'])} original kit previews: {filename.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
