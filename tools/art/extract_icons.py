"""Cut item icons out of the reference sprite sheets (assets/art/sheets) using data/icon_map.json.

python3 -I tools/art/extract_icons.py <project dir> [check_sheet.png]
Each mapped sprite is cropped, its black backdrop removed by flood fill from the crop edge (dark
outlines inside the sprite survive), fitted into 48x48 and written to assets/art/icons/<item>.png.
Items without an entry keep their procedural icon.
"""
import sys, json, os
from collections import deque
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from slice_sheets import sprites

root = sys.argv[1]
mp = json.load(open(os.path.join(root, "data/icon_map.json")))
boxes = {}
ims = {}
for tag in ("a", "b"):
    im, bs = sprites(os.path.join(root, "assets/art/sheets/sheet_%s.png" % tag))
    ims[tag] = im.convert("RGBA")
    boxes[tag] = bs
out_dir = os.path.join(root, "assets/art/icons")
os.makedirs(out_dir, exist_ok=True)

def cut(tag, idx):
    b = boxes[tag][idx]
    im = ims[tag]
    crop = im.crop((max(0, b[0] - 2), max(0, b[1] - 2), min(im.width, b[2] + 3), min(im.height, b[3] + 3)))
    w, h = crop.size
    px = crop.load()
    dark = lambda p: p[0] + p[1] + p[2] < 60
    seen = set()
    q = deque([(x, y) for x in range(w) for y in (0, h - 1)] + [(x, y) for y in range(h) for x in (0, w - 1)])
    while q:
        x, y = q.popleft()
        if (x, y) in seen or not (0 <= x < w and 0 <= y < h) or not dark(px[x, y]):
            continue
        seen.add((x, y))
        px[x, y] = (0, 0, 0, 0)
        q.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))
    # keep only the sprite itself: the largest connected shape (drops scraps of the neighbours)
    seen2 = set(); best = []
    for sy in range(h):
        for sx in range(w):
            if px[sx, sy][3] > 0 and (sx, sy) not in seen2:
                comp = []; q2 = deque([(sx, sy)]); seen2.add((sx, sy))
                while q2:
                    x, y = q2.popleft(); comp.append((x, y))
                    for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                        if 0 <= nx < w and 0 <= ny < h and (nx, ny) not in seen2 and px[nx, ny][3] > 0:
                            seen2.add((nx, ny)); q2.append((nx, ny))
                if len(comp) > len(best): best = comp
    keep = set(best)
    for y in range(h):
        for x in range(w):
            if (x, y) not in keep: px[x, y] = (0, 0, 0, 0)
    bb = crop.getbbox()
    if bb: crop = crop.crop(bb)
    k = 46.0 / max(crop.size)
    crop = crop.resize((max(1, round(crop.width * k)), max(1, round(crop.height * k))), Image.LANCZOS)
    out = Image.new("RGBA", (48, 48), (0, 0, 0, 0))
    out.paste(crop, ((48 - crop.width) // 2, (48 - crop.height) // 2), crop)
    return out

made = {}
for item, (tag, idx) in mp.items():
    if idx >= len(boxes[tag]):
        print("out of range", item, tag, idx); continue
    icon = cut(tag, idx)
    icon.save(os.path.join(out_dir, item + ".png"))
    made[item] = icon
print("icons written:", len(made))
if len(sys.argv) > 2:
    names = sorted(made)
    cols = 12
    sheet = Image.new("RGB", (cols * 128, ((len(names) + cols - 1) // cols) * 72), (24, 24, 24))
    d = ImageDraw.Draw(sheet)
    for i, n in enumerate(names):
        x, y = (i % cols) * 128, (i // cols) * 72
        sheet.paste(made[n], (x + 40, y + 2), made[n])
        d.text((x + 2, y + 52), n[:20], fill=(255, 230, 120))
    sheet.save(sys.argv[2])
