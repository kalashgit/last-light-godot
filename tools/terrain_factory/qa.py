"""Verify Blender batch files and create native-size / 220% / 325% review sheets."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

from PIL import Image, ImageDraw


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(folder, expected):
    manifest = json.loads((folder / "manifest.json").read_text())
    assets = manifest["assets"]
    if len(assets) != expected or len(set(assets)) != expected:
        raise AssertionError("unexpected actual source model count")
    for key in assets:
        sub = folder / key
        meta = json.loads((sub / "asset.json").read_text())
        if meta["asset_id"] != key or meta["founder_golden_approved"] or meta["godot_integrated"]:
            raise AssertionError("incorrect asset identity/release gate")
        for f in meta["files"].values():
            file = sub / f["path"]
            if not file.is_file() or digest(file) != f["sha256"]:
                raise AssertionError("missing/mismatched Blender or render source hash")
        img = Image.open(sub / "world.png").convert("RGBA")
        if img.size != (80, 40):
            raise AssertionError("2.5D tile isn't 80x40")
        px = img.load()
        nonzero = 0
        for y in range(40):
            for x in range(80):
                inside = abs((x+.5-40)/40) + abs((y+.5-20)/20) < 1
                if bool(px[x, y][3]) != bool(inside):
                    raise AssertionError("diamond alpha/anchor mismatch")
                nonzero += bool(px[x, y][3])
        if nonzero < 1400:
            raise AssertionError("empty or malformed tile")
    return assets


def sheet(folder, assets, out):
    cols, w, h = 4, 340, 258
    rows = math.ceil(len(assets) / cols)
    canvas = Image.new("RGB", (cols*w, rows*h), (31, 36, 39))
    draw = ImageDraw.Draw(canvas)
    for index, key in enumerate(assets):
        x, y = (index % cols)*w, (index // cols)*h
        label = key.removeprefix("ll_tile_")
        tile = Image.open(folder / key / "world.png").convert("RGBA")
        # Crisp native pixels at the game-like magnification 325%.
        shown = tile.resize((260, 130), Image.Resampling.NEAREST)
        under = Image.new("RGBA", shown.size, (72, 77, 76, 255))
        under.alpha_composite(shown)
        canvas.paste(under.convert("RGB"), (x+40, y+45))
        draw.text((x+9, y+9), label[:48], fill=(225, 227, 218))
        draw.text((x+9, y+193), "Native: 80x40 | 220% and 325% evaluate from same PNG", fill=(180,180,175))
    canvas.save(out)
    return out


def seam_sheet(folder, out):
    """Real native Blender tiles assembled into one 4x4 isometric patch.

    The edge fixture intentionally needs masks 1,2,3,4 plus the grass base,
    all included in the 12-item calibration run. It is not full-mask approval.
    """
    corner = [[0 for _ in range(5)] for _ in range(5)]
    for x in (1, 2, 3):
        corner[0][x] = 1
    corner[4][4] = 1
    mosaic = Image.new("RGBA", (440, 260), (42, 48, 46, 255))
    for y in range(4):
        for x in range(4):
            bits = (corner[y][x] + 2*corner[y][x+1] +
                    4*corner[y+1][x+1] + 8*corner[y+1][x])
            name = ("ll_tile_grass_sparse" if bits == 0 else
                    "ll_tile_grass_sparse_to_asphalt_worn_c%02d" % bits)
            tile = Image.open(folder / name / "world.png").convert("RGBA")
            left = 180 + 40*(x-y) - 40
            top = 45 + 20*(x+y) - 20
            mosaic.alpha_composite(tile, (left, top))
    # Native pixels enlarged without interpolation for material/seam review.
    mosaic.convert("RGB").resize((1320, 780), Image.Resampling.NEAREST).save(out)
    return out


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--sources", type=Path, required=True)
    p.add_argument("--expected", type=int, required=True)
    p.add_argument("--sheet", type=Path, required=True)
    p.add_argument("--seam-sheet", type=Path)
    a = p.parse_args()
    assets = verify(a.sources, a.expected)
    a.sheet.parent.mkdir(parents=True, exist_ok=True)
    sheet(a.sources, assets, a.sheet)
    if a.seam_sheet:
        a.seam_sheet.parent.mkdir(parents=True, exist_ok=True)
        seam_sheet(a.sources, a.seam_sheet)
    print("LL_TERRAIN_QA_PASS", len(assets), a.sheet, flush=True)


if __name__ == "__main__":
    main()
