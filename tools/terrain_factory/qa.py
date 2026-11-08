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


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--sources", type=Path, required=True)
    p.add_argument("--expected", type=int, required=True)
    p.add_argument("--sheet", type=Path, required=True)
    a = p.parse_args()
    assets = verify(a.sources, a.expected)
    a.sheet.parent.mkdir(parents=True, exist_ok=True)
    sheet(a.sources, assets, a.sheet)
    print("LL_TERRAIN_QA_PASS", len(assets), a.sheet, flush=True)


if __name__ == "__main__":
    main()
