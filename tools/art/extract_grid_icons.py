"""Cut item icons out of the grid-laid reference sheets in art_src/sheets, using data/icon_map_grid.json.

python3 -I tools/art/extract_grid_icons.py <project dir> [check_sheet.png]

Each sheet is a regular grid (cols x rows) of sprites, sometimes with a number printed under each one.
The backdrop is removed according to the sheet's "bg":
  alpha  the sheet has real transparency (whatever colour sits under transparent pixels is ignored)
  light  white, light grey or a grey checkerboard: low-saturation bright pixels reached from the
         sheet's edge are cleared (the dark outline around every sprite stops the fill)
  dark   a flat dark grey: the same, for low-saturation pixels close to that grey
Inside each grid cell the largest shape is the sprite; other shapes are kept only if they are at
least 6% of its size (the second boot of a pair, a strap) and are not a short shape lying wholly
above or below it (a printed number), so labels and stray specks drop out.
An entry is [sheet, row, col], or [sheet, "at", x, y] for a sheet whose columns drift: the cell is
then a grid-sized box centred on that pixel, or [sheet, "band", row, k] for a dense sheet whose
columns do not line up at all: the k-th sprite from the left in that row, sprites being separated
by clear vertical gaps. Items listed in "fill_holes" (rings: a belt, a wheel)
also lose backdrop-coloured pixels enclosed by the sprite. The result is fitted into 48x48 (resampled with premultiplied alpha, so no backdrop
colour bleeds into the edge) and written to assets/art/icons/<item>.png.
The sheets live in art_src/ (ignored by Godot), so only the small icons ship with the game.
"""
import sys, json, os
from collections import deque
import numpy as np
from PIL import Image, ImageDraw

root = sys.argv[1]
cfg = json.load(open(os.path.join(root, "data/icon_map_grid.json")))
out_dir = os.path.join(root, "assets/art/icons")
os.makedirs(out_dir, exist_ok=True)


def edge_flood(pred):
    """pixels of pred connected to the image border"""
    reach = np.zeros_like(pred)
    reach[0, :] = pred[0, :]; reach[-1, :] = pred[-1, :]
    reach[:, 0] = pred[:, 0]; reach[:, -1] = pred[:, -1]
    while True:
        grown = reach.copy()
        grown[1:, :] |= reach[:-1, :]; grown[:-1, :] |= reach[1:, :]
        grown[:, 1:] |= reach[:, :-1]; grown[:, :-1] |= reach[:, 1:]
        grown &= pred
        if (grown == reach).all():
            return reach
        reach = grown


def backdrop(im, bg):
    """pixels that look like the sheet's backdrop, wherever they are"""
    a = np.asarray(im).astype(np.int16)
    rgb = a[:, :, :3]
    mx = rgb.max(axis=2); mn = rgb.min(axis=2); mean = rgb.mean(axis=2)
    if bg == "alpha":
        return a[:, :, 3] <= 100
    if bg == "light":
        return (mx - mn < 20) & (mn > 196)
    return (mx - mn < 16) & (mean > 30) & (mean < 80)


def foreground(path, bg):
    im = Image.open(path).convert("RGBA")
    a = np.asarray(im).astype(np.int16)
    rgb = a[:, :, :3]
    if bg == "alpha":
        fg = a[:, :, 3] > 100
    else:
        mx = rgb.max(axis=2); mn = rgb.min(axis=2); mean = rgb.mean(axis=2)
        if bg == "light":
            pred = (mx - mn < 20) & (mn > 196)
        else:
            pred = (mx - mn < 16) & (mean > 30) & (mean < 80)
        fg = ~edge_flood(pred)
    return im, fg


def components(mask):
    h, w = mask.shape
    seen = np.zeros_like(mask)
    comps = []
    for sy, sx in zip(*np.nonzero(mask)):
        if seen[sy, sx]:
            continue
        seen[sy, sx] = True
        q = deque([(sy, sx)]); pts = []
        while q:
            y, x = q.popleft(); pts.append((y, x))
            for ny in (y - 1, y, y + 1):
                for nx in (x - 1, x, x + 1):
                    if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not seen[ny, nx]:
                        seen[ny, nx] = True; q.append((ny, nx))
        comps.append(pts)
    return comps


def row_bands(fg, rows, label_px):
    """the sheet's real rows: runs of lines with sprite pixels, split where (almost) none are.
    Bands too short to hold a sprite are printed numbers. Returns None if the count is not `rows`."""
    prof = fg.sum(axis=1)
    bands = []; start = None
    for y in range(len(prof) + 1):
        busy = y < len(prof) and prof[y] >= 40
        if busy and start is None:
            start = y
        elif not busy and start is not None:
            if y - start >= 40:
                bands.append([start, y])
            start = None
    if len(bands) != rows:
        return None
    if label_px:
        for b in bands:
            fg[b[1] - label_px:b[1], :] = False      # the number printed along the bottom of the row
            b[1] -= label_px
    return bands


_band_cache = {}


def band_runs(fg, band):
    """the sprites of one row, left to right, as [x0, x1) spans: each shape of a reasonable size in
    the row, with small pieces folded into the shape they sit over"""
    key = (id(fg), band[0], band[1])
    if key in _band_cache:
        return _band_cache[key]
    comps = components(fg[band[0]:band[1], :])
    spans = []
    for pts in comps:
        xs = [p[1] for p in pts]
        spans.append([min(xs), max(xs) + 1, len(pts)])
    big = max([sp[2] for sp in spans] + [1])
    main = sorted([sp for sp in spans if sp[2] >= big * 0.08], key=lambda sp: sp[0])
    for sp in spans:
        if sp[2] < big * 0.08:
            cx = (sp[0] + sp[1]) / 2
            for m in main:
                if m[0] <= cx < m[1]:
                    m[0] = min(m[0], sp[0]); m[1] = max(m[1], sp[1])
                    break
    runs = [[m[0], m[1]] for m in main]
    _band_cache[key] = runs
    return runs


def cut(im, fg, cols, rows, cell, bands, holes=None, size=48):
    W, H = im.size
    cw, ch = W / cols, H / rows
    if cell[0] == "band":
        if not bands:
            bands = [[int(r * ch), int((r + 1) * ch)] for r in range(rows)]
        run = band_runs(fg, bands[cell[1]])[cell[2]]
        bx0, cw = run[0], run[1] - run[0]
        by0, by1 = bands[cell[1]]
        y0, y1 = by0, by1
    elif cell[0] == "at":
        bx0, by0 = cell[1] - cw / 2, cell[2] - ch / 2
        by1 = by0 + ch
        y0 = max(0, int(by0 - ch * 0.5)); y1 = min(H, int(by1 + ch * 0.5))
    elif bands:
        bx0 = cell[1] * cw
        by0, by1 = bands[cell[0]]
        y0, y1 = by0, by1
    else:
        bx0, by0 = cell[1] * cw, cell[0] * ch
        by1 = by0 + ch
        y0 = max(0, int(by0 - ch * 0.5)); y1 = min(H, int(by1 + ch * 0.5))
    bx1 = bx0 + cw
    # look a little beyond the cell, but keep only shapes centred inside it
    # (wide enough that a neighbour is never cut in half and mistaken for a piece of this sprite)
    x0 = max(0, int(bx0 - cw * 0.8)); x1 = min(W, int(bx1 + cw * 0.8))
    win = fg[y0:y1, x0:x1]
    inside = []
    for pts in components(win):
        cy = sum(p[0] for p in pts) / len(pts) + y0
        cx = sum(p[1] for p in pts) / len(pts) + x0
        if bx0 <= cx < bx1 and by0 <= cy < by1:
            inside.append(pts)
    if not inside:
        return None
    main_pts = max(inside, key=len)
    main = len(main_pts)
    m_top = min(p[0] for p in main_pts); m_bot = max(p[0] for p in main_pts)
    keep = []
    for p in inside:
        if len(p) < main * 0.06:
            continue
        top = min(q[0] for q in p); bot = max(q[0] for q in p)
        if p is not main_pts and bot - top < ch * 0.22 and (top >= m_bot - 4 or bot <= m_top + 4):
            continue      # a printed number above or below the sprite
        keep.append(p)
    m = np.zeros(win.shape, dtype=bool)
    for pts in keep:
        ys, xs = zip(*pts)
        m[list(ys), list(xs)] = True
    src = np.asarray(im)[y0:y1, x0:x1].copy()
    if holes is not None:
        m &= ~holes[y0:y1, x0:x1]
    src[:, :, 3] = np.where(m, src[:, :, 3], 0).astype(np.uint8)
    spr = Image.fromarray(src, "RGBA")
    bb = spr.getbbox()
    spr = spr.crop(bb)
    k = (size - 2.0) / max(spr.size)
    dims = (max(1, round(spr.width * k)), max(1, round(spr.height * k)))
    spr = spr.convert("RGBa").resize(dims, Image.LANCZOS).convert("RGBA")
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    out.paste(spr, ((size - spr.width) // 2, (size - spr.height) // 2), spr)
    return out


made = {}
loaded = {}
for item, entry in cfg["icons"].items():
    tag, cell = entry[0], entry[1:]
    sh = cfg["sheets"][tag]
    if tag not in loaded:
        im0, fg0 = foreground(os.path.join(root, "art_src/sheets", sh["file"]), sh["bg"])
        loaded[tag] = (im0, fg0, row_bands(fg0, sh["rows"], int(sh.get("label_px", 0))))
    im, fg, bands = loaded[tag]
    holes = backdrop(im, sh["bg"]) if item in cfg.get("fill_holes", []) else None
    icon = cut(im, fg, sh["cols"], sh["rows"], cell, bands, holes)
    if icon is None:
        print("nothing found for", item, entry)
        continue
    icon.save(os.path.join(out_dir, item + ".png"))
    made[item] = icon
print("icons written:", len(made))

if len(sys.argv) > 2:
    names = sorted(made)
    cols = 10
    sheet = Image.new("RGB", (cols * 150, ((len(names) + cols - 1) // cols) * 120), (34, 36, 38))
    d = ImageDraw.Draw(sheet)
    for i, n in enumerate(names):
        x, y = (i % cols) * 150, (i // cols) * 120
        big = made[n].resize((96, 96), Image.NEAREST)
        sheet.paste(big, (x + 27, y + 2), big)
        d.text((x + 4, y + 102), n[:24], fill=(255, 230, 120))
    sheet.save(sys.argv[2])
