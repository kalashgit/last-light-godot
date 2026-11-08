"""Debug previews: ASCII floor plans (phone friendly) and optional top-down PNG.

The PNG is a debug overlay, not game art. Pillow is optional; ASCII always works.
"""
from __future__ import annotations

from .core import rect_cells

FURN_GLYPH = {"fridge": "F", "stove": "S", "sink": "K", "counter": "C", "cupboard": "c", "dining_table": "T", "chair": "h",
              "sofa": "O", "sofa_large": "O", "armchair": "a", "coffee_table": "t", "tv_stand": "V", "bookcase": "B",
              "double_bed": "D", "single_bed": "b", "nightstand": "n", "dresser": "d", "wardrobe": "W", "toilet": "L",
              "bathtub": "U", "vanity": "v", "medicine_cabinet": "M", "washer": "X", "utility_shelf": "H", "pantry_shelf": "P",
              "desk": "E", "filing_cabinet": "f", "workbench": "J", "tool_locker": "l", "crate": "x", "retail_shelf": "|",
              "cold_case": "Q", "checkout": "$", "coat_rack": "r", "tire_stack": "o", "electrical_panel": "e", "vehicle": "%",
              "vehicle_h": "%"}


def ascii_floor(b, z=0):
    floor = next(f for f in b["floors"] if f["z"] == z)
    cells = {}
    for r in floor["rooms"]:
        for c in rect_cells(r["rect"]):
            cells[tuple(c)] = (r.get("code") or r["id"].rsplit(".", 1)[-1])[0].lower()
    for s in b.get("stairs", []):
        for c in rect_cells(s["rect"]):
            cells[tuple(c)] = "="
    for item in floor["furniture"]:
        for c in rect_cells(item["rect"]):
            cells[tuple(c)] = FURN_GLYPH.get(item["type"], "#")
    xs = [c[0] for c in cells]
    ys = [c[1] for c in cells]
    lines = []
    for y in range(min(ys), max(ys) + 1):
        lines.append("".join(cells.get((x, y), " ") for x in range(min(xs), max(xs) + 1)))
    legend = ", ".join(f"{(r.get('code') or r['id'].rsplit('.', 1)[-1])}={r['type']}{r['rect']}" for r in floor["rooms"])
    doors = ", ".join(f"{d['kind'][0]}:{d['a']}-{d['b']}" for d in floor["doors"])
    return "\n".join(lines) + f"\nrooms: {legend}\ndoors: {doors}\n"


TERRAIN_RGB = {"grass": (74, 94, 62), "asphalt": (58, 60, 62), "sidewalk": (140, 138, 128), "driveway": (120, 118, 110),
               "path": (150, 140, 118), "gravel": (118, 108, 92), "dirt": (102, 86, 66), "field": (128, 118, 64),
               "forest": (44, 66, 46), "water": (58, 92, 118), "lot": (80, 100, 66), "floor": (150, 130, 100), "curb": (170, 170, 160)}
ROOM_RGB = {"kitchen": (196, 190, 160), "bathroom": (150, 182, 186), "restroom": (150, 182, 186), "bedroom": (170, 140, 120),
            "living": (180, 150, 110), "hall": (160, 150, 130), "corridor": (160, 150, 130), "landing": (160, 150, 130),
            "garage": (130, 130, 128), "bay": (130, 130, 128), "sales": (200, 196, 180), "front": (200, 196, 180)}


def png_world(world, path, scale=10, z=0):
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        return False
    x0, y0, w, h = world["bounds"]
    img = Image.new("RGB", (w * scale, h * scale), (30, 40, 34))
    d = ImageDraw.Draw(img)

    def px(p):
        return ((p[0] - x0) * scale, (p[1] - y0) * scale)

    for row_y, row in enumerate(world["terrain_rows"]):
        for col, t in enumerate(row):
            x, y = x0 + col, y0 + row_y
            d.rectangle([*px((x, y)), px((x + 1, y + 1))[0] - 1, px((x + 1, y + 1))[1] - 1], fill=TERRAIN_RGB.get(t, (255, 0, 255)))
    for b in world["buildings"]:
        floor = next((f for f in b["floors"] if f["z"] == z), None)
        if not floor:
            continue
        for r in floor["rooms"]:
            x, y, rw, rh = r["rect"]
            d.rectangle([*px((x, y)), *px((x + rw, y + rh))], fill=ROOM_RGB.get(r["type"], (170, 160, 140)))
        for s in b.get("stairs", []):
            x, y, rw, rh = s["rect"]
            d.rectangle([*px((x, y)), *px((x + rw, y + rh))], fill=(110, 90, 70))
        for item in floor["furniture"]:
            x, y, rw, rh = item["solid_rect"]
            d.rectangle([*px((x, y)), *px((x + rw, y + rh))], fill=(205, 170, 70) if item["container"] else (95, 85, 75))
        for wall in floor["walls"]:
            d.line([px(wall["a"]), px(wall["b"])], fill=(25, 25, 25) if wall["exterior"] else (60, 55, 50), width=3 if wall["exterior"] else 2)
        for win in floor["windows"]:
            d.line([px(win["a"]), px(win["b"])], fill=(120, 190, 220), width=3)
        for door in floor["doors"]:
            color = (220, 60, 50) if door["kind"] == "exterior" else (240, 140, 40) if door["kind"] == "garage" else (230, 220, 120)
            if door["kind"] != "opening":
                d.line([px(door["a"]), px(door["b"])], fill=color, width=3)
    for prop in world.get("props", []):
        x, y, rw, rh = prop["solid_rect"]
        color = {"tree": (34, 90, 40), "bush": (60, 110, 60), "vehicle": (150, 60, 50), "vehicle_h": (150, 60, 50)}.get(prop["type"], (200, 200, 200))
        if prop["type"] == "tree":
            d.ellipse([*px((x - 0.4, y - 0.4)), *px((x + rw + 0.4, y + rh + 0.4))], fill=color)
        else:
            d.rectangle([*px((x, y)), *px((x + rw, y + rh))], fill=color)
    for f in world.get("fences", []):
        d.line([px(f["a"]), px(f["b"])], fill=(150, 120, 80), width=2)
    sp = world.get("spawn")
    if sp:
        d.ellipse([*px((sp[0] - 0.4, sp[1] - 0.4)), *px((sp[0] + 0.4, sp[1] + 0.4))], fill=(240, 240, 255))
    img.save(path)
    return True
