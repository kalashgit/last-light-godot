"""Build 3D model specs (data/model_specs.json) for every item and the world props.

python3 -I tools/art/model_specs.py <project dir>

Each spec is a list of primitive parts in metres, in a local frame where X is the item's length,
Y its width and Z up, with the origin on the ground under its centre. Sizes come from the founder's
mesh-recipe catalog (art_src/catalog: real-world dimensions per asset, plus placed parts for the
inspected archetypes) where an item matches an asset; otherwise from the template's own real-world
defaults. The part structure follows the catalog's family seeds (a striking tool is a handle, a
working head and a mount; a firearm a receiver, barrel, grip or stock, trigger guard and sight; and
so on). Colours are sampled from the item's sheet icon, so a model keeps the sheet's palette.

Long things (weapons and tools) are modelled lying along X with their working profile in the XY
plane, so the same model reads lying on the ground (seen from above) and held in the hand (seen
from the side). "grip" marks where the hand holds them.
"""
import sys, os, re, json, math, colorsys
from PIL import Image

root = sys.argv[1]
CAT = os.path.join(root, "art_src/catalog")
assets = json.load(open(os.path.join(CAT, "assets.json")))
kits = json.load(open(os.path.join(CAT, "kits.json")))


def norm(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


by_name = {}
for a in assets:
    for k in (norm(a.get("name")), norm((a.get("file") or "").replace(".png", ""))):
        if k and k not in by_name:
            by_name[k] = a

# ------------------------------------------------------------------ the items, from the game's own data
src = open(os.path.join(root, "scripts/data/items.gd")).read()
ITEMS = {}
for m in re.finditer(r'_i\("([a-z0-9_]+)", "([^"]+)", "([a-z]+)", ([0-9.]+), \["([a-z_]+)", "([0-9a-f]{6})", "([0-9a-f]{6})"\](.*)', src):
    ITEMS[m.group(1)] = {"n": m.group(2), "cat": m.group(3), "w": float(m.group(4)), "shape": m.group(5), "c1": "#" + m.group(6), "c2": "#" + m.group(7), "rest": m.group(8)}
# the study manuals are generated in code
for sk in re.search(r"const MANUAL_SKILLS := \[(.*?)\]", src, re.S).group(1).replace('"', "").replace("\n", "").split(","):
    sk = sk.strip()
    if sk and "book_" + sk not in ITEMS:
        ITEMS["book_" + sk] = {"n": sk.replace("_", " ").title() + " Manual", "cat": "book", "w": 0.5, "shape": "book", "c1": "#6a5a4a", "c2": "#f0ece0", "rest": ""}


# ------------------------------------------------------------------ colours from the sheet art
def palette(iid):
    """three colours from the item's icon, most common first (outline ink and transparency ignored)"""
    path = os.path.join(root, "assets/art/icons/%s.png" % iid)
    it = ITEMS.get(iid, {})
    fallback = [it.get("c1", "#888888"), it.get("c2", "#cccccc"), "#5a5a5a"]
    if not os.path.exists(path):
        return fallback
    im = Image.open(path).convert("RGBA")
    px = [p for p in (im.get_flattened_data() if hasattr(im, 'get_flattened_data') else im.getdata()) if p[3] > 160 and (p[0] + p[1] + p[2]) > 70]
    if len(px) < 12:
        return fallback
    # a few rounds of k-means on 4 clusters
    pts = [(p[0], p[1], p[2]) for p in px[:: max(1, len(px) // 600)]]
    pts.sort(key=lambda c: sum(c))
    cents = [pts[int(len(pts) * f)] for f in (0.15, 0.4, 0.65, 0.9)]
    for _ in range(8):
        groups = [[] for _ in cents]
        for c in pts:
            j = min(range(len(cents)), key=lambda k: sum((c[i] - cents[k][i]) ** 2 for i in range(3)))
            groups[j].append(c)
        cents = [tuple(sum(c[i] for c in g) / len(g) for i in range(3)) if g else cents[k] for k, g in enumerate(groups)]
    order = sorted(range(len(cents)), key=lambda k: -len(groups[k]))
    out = ["#%02x%02x%02x" % tuple(int(v) for v in cents[k]) for k in order if groups[k]]
    while len(out) < 3:
        out.append(fallback[len(out) % 2])
    return out[:3]


def shade(hexc, k):
    r, g, b = int(hexc[1:3], 16), int(hexc[3:5], 16), int(hexc[5:7], 16)
    return "#%02x%02x%02x" % tuple(max(0, min(255, int(v * k))) for v in (r, g, b))


METAL, DARKMETAL, WOOD, RUBBER, GLASS, PAPER, BONE = "#8f989d", "#4a4d50", "#8a6644", "#2a2c2e", "#bcd4dc", "#e2dcc6", "#d6c8a8"


# ------------------------------------------------------------------ primitives
def P(kind, c, s, col, m="plastic", r=(0, 0, 0), t=1.0):
    d = {"p": kind, "c": [round(v, 4) for v in c], "s": [round(max(v, 0.002), 4) for v in s], "col": col, "m": m}
    if any(r):
        d["r"] = list(r)
    if t != 1.0:
        d["t"] = t
    return d


def rod_x(x0, x1, d, col, m, y=0.0, z=None, t=1.0):
    """a cylinder lying along X from x0 to x1"""
    z = d / 2 if z is None else z
    return P("cyl", ((x0 + x1) / 2, y, z), (d, d, abs(x1 - x0)), col, m, (0, 90, 0), t)


# ------------------------------------------------------------------ templates: (L, W, H) in metres, palette -> parts
def T_can(L, W, H, pal, flat=False):
    d = max(L, W)
    if flat:   # a flat tin (sardines)
        return [P("box", (0, 0, H / 2), (L, W, H), pal[0], "metal"), P("box", (0, 0, H - 0.002), (L * 0.96, W * 0.92, 0.004), METAL, "metal")]
    return [P("cyl", (0, 0, H / 2), (d, d, H * 0.94), pal[0], "metal"), P("cyl", (0, 0, H * 0.97), (d * 0.98, d * 0.98, H * 0.06), METAL, "metal"),
            P("cyl", (0, 0, H * 0.03), (d * 0.98, d * 0.98, H * 0.06), METAL, "metal"), P("cyl", (0, 0, H * 0.5), (d * 1.004, d * 1.004, H * 0.42), pal[1], "paper")]


def T_bottle(L, W, H, pal, glass=False, cap=None):
    d = max(L, W)
    m = "glass" if glass else "plastic"
    return [P("cyl", (0, 0, H * 0.32), (d, d, H * 0.64), pal[0], m), P("cyl", (0, 0, H * 0.72), (d, d, H * 0.16), pal[0], m, t=0.45),
            P("cyl", (0, 0, H * 0.87), (d * 0.42, d * 0.42, H * 0.16), pal[0], m), P("cyl", (0, 0, H * 0.97), (d * 0.46, d * 0.46, H * 0.06), cap or pal[2], "plastic"),
            P("cyl", (0, 0, H * 0.35), (d * 1.01, d * 1.01, H * 0.3), pal[1], "paper")]


def T_jug(L, W, H, pal):
    return [P("box", (0, 0, H * 0.42), (L, W, H * 0.84), pal[0], "plastic"), P("cyl", (L * 0.25, 0, H * 0.9), (L * 0.28, L * 0.28, H * 0.14), pal[0], "plastic"),
            P("cyl", (L * 0.25, 0, H * 0.98), (L * 0.3, L * 0.3, H * 0.05), pal[1], "plastic"), P("box", (-L * 0.15, 0, H * 0.9), (L * 0.4, W * 0.25, H * 0.12), pal[0], "plastic")]


def T_box(L, W, H, pal, m="paper", band=True):
    out = [P("box", (0, 0, H / 2), (L, W, H), pal[0], m)]
    if band:
        out.append(P("box", (0, 0, H * 0.55), (L * 1.004, W * 1.004, H * 0.3), pal[1], m))
    return out


def T_book(L, W, H, pal):
    return [P("box", (0, 0, H / 2), (L, W, H), pal[0], "paper"), P("box", (L * 0.02, W * 0.02, H / 2), (L * 0.97, W * 0.97, H * 0.82), PAPER, "paper"),
            P("box", (-L * 0.47, 0, H / 2), (L * 0.06, W * 1.0, H * 1.02), shade(pal[0], 0.8), "paper")]


def T_paper(L, W, H, pal):
    return [P("box", (0, 0, max(H, 0.002) / 2), (L, W, max(H, 0.002)), pal[0] if pal else PAPER, "paper"), P("box", (0, -W * 0.1, max(H, 0.002) + 0.0006), (L * 0.7, W * 0.04, 0.001), shade(pal[1], 0.7), "paper")]


def T_jar(L, W, H, pal):
    d = max(L, W)
    return [P("cyl", (0, 0, H * 0.42), (d, d, H * 0.84), pal[0], "glass"), P("cyl", (0, 0, H * 0.92), (d * 0.92, d * 0.92, H * 0.16), pal[1], "metal"),
            P("cyl", (0, 0, H * 0.45), (d * 1.01, d * 1.01, H * 0.36), pal[2], "paper")]


def T_round(L, W, H, pal, stem=False, leaf=False):
    out = [P("sph", (0, 0, H / 2), (L, W, H), pal[0], "organic")]
    if stem:
        out.append(P("cyl", (0, 0, H * 1.02), (L * 0.08, L * 0.08, H * 0.18), "#5a4028", "organic"))
    if leaf:
        out.append(P("sph", (L * 0.12, 0, H * 1.0), (L * 0.32, W * 0.16, H * 0.08), "#4f7a36", "organic", (0, 0, 30)))
    return out


def T_cluster(L, W, H, pal, n=7):
    out = []
    for i in range(n):
        a = i * 2.39996
        rr = 0.33 * math.sqrt(i / n)
        d = min(L, W) * 0.36
        out.append(P("sph", (math.cos(a) * L * rr, math.sin(a) * W * rr, d / 2 + (0.3 * d if i % 3 == 0 else 0)), (d, d, d), pal[i % 2], "organic"))
    return out


def T_carrot(L, W, H, pal):
    return [P("cyl", (0, 0, H / 2), (W, W, L * 0.85), pal[0], "organic", (0, 90, 0), t=0.2), P("sph", (-L * 0.48, 0, H / 2), (L * 0.22, W * 0.8, H * 0.6), "#4f7a36", "organic")]


def T_banana(L, W, H, pal):
    out = []
    for i in range(4):
        a = -0.6 + i * 0.4
        out.append(P("cap", (math.sin(a) * L * 0.4, (1 - math.cos(a)) * L * 0.5 - L * 0.12, H / 2), (W, W, L * 0.36), pal[0], "organic", (0, 90, math.degrees(a))))
    return out


def T_slab(L, W, H, pal, m="organic", rounded=True):
    if rounded:
        return [P("sph", (0, 0, H / 2), (L, W, H * 1.4), pal[0], m), P("box", (0, 0, H * 0.25), (L * 0.8, W * 0.8, H * 0.5), pal[0], m)]
    return [P("box", (0, 0, H / 2), (L, W, H), pal[0], m)]


def T_loaf(L, W, H, pal):
    return [P("box", (0, 0, H * 0.35), (L, W, H * 0.7), pal[0], "organic"), P("cyl", (0, 0, H * 0.7), (W, W * 0.6, L), shade(pal[0], 1.05), "organic", (0, 90, 0))]


def T_capsule(L, W, H, pal, m="organic"):
    return [P("cap", (0, 0, H / 2), (W, H, L), pal[0], m, (0, 90, 0))]


def T_torus(L, W, H, pal, m="organic"):
    return [P("tor", (0, 0, H / 2), (L, W, H), pal[0], m)]


def T_stack(L, W, H, pal, layers):
    out = []
    z = 0.0
    for frac, col, kind in layers:
        h = H * frac
        out.append(P(kind, (0, 0, z + h / 2), (L, W, h), col, "organic"))
        z += h
    return out


def T_cloth(L, W, H, pal):
    """a garment folded flat on the ground"""
    return [P("box", (0, 0, H * 0.45), (L, W, H * 0.9), pal[0], "cloth"), P("sph", (0, 0, H * 0.75), (L * 0.98, W * 0.98, H * 0.6), pal[0], "cloth"),
            P("box", (0, W * 0.22, H * 0.92), (L * 0.9, W * 0.06, H * 0.12), pal[1], "cloth")]


def T_hat(L, W, H, pal, brim=0.0, peak=0.0, hard=False):
    m = "plastic" if hard else "cloth"
    out = [P("sph", (0, 0, 0), (L * 0.86, W * 0.86, H * 2.0), pal[0], m)]
    if brim:
        out.append(P("cyl", (0, 0, 0.004), (L * (1 + brim), W * (1 + brim), 0.008), pal[0], m))
    if peak:
        out.append(P("box", (L * 0.5, 0, 0.005), (L * peak, W * 0.7, 0.01), pal[1], m))
    return out


def T_boots(L, W, H, pal, m="cloth"):
    out = []
    for y in (-W * 0.25, W * 0.25):
        out += [P("box", (0, y, 0.012), (L, W * 0.42, 0.024), RUBBER, "rubber"), P("box", (-L * 0.18, y, H * 0.5), (L * 0.42, W * 0.38, H * 0.95), pal[0], m),
                P("sph", (L * 0.16, y, H * 0.18), (L * 0.6, W * 0.4, H * 0.4), pal[0], m)]
    return out


def T_gloves(L, W, H, pal):
    out = []
    for y in (-W * 0.24, W * 0.24):
        out += [P("box", (0, y, H / 2), (L, W * 0.42, H), pal[0], "cloth"), P("box", (L * 0.42, y + W * 0.12, H / 2), (L * 0.3, W * 0.1, H * 0.9), pal[0], "cloth")]
    return out


def T_bag(L, W, H, pal, m="cloth"):
    return [P("box", (0, 0, H * 0.45), (L, W, H * 0.9), pal[0], m), P("sph", (0, 0, H * 0.88), (L, W, H * 0.28), pal[0], m),
            P("box", (0, W * 0.52, H * 0.35), (L * 0.7, W * 0.12, H * 0.4), pal[1], m), P("box", (0, -W * 0.5, H * 0.5), (L * 0.12, W * 0.06, H * 0.8), pal[2], m)]


def T_duffel(L, W, H, pal):
    return [P("cap", (0, 0, H / 2), (W, H, L), pal[0], "cloth", (0, 90, 0)), P("tor", (0, 0, H * 0.95), (L * 0.3, W * 0.4, 0.02), pal[1], "cloth", (90, 0, 0))]


def T_coil(L, W, H, pal, m="cloth"):
    return [P("tor", (0, 0, H * 0.25), (L, W, H * 0.5), pal[0], m), P("tor", (0, 0, H * 0.7), (L * 0.92, W * 0.92, H * 0.5), shade(pal[0], 0.92), m)]


def T_animal(L, W, H, pal, legs=4, tail=0.0):
    """a dead animal lying on its side, legs out to one side"""
    out = [P("sph", (0, 0, H * 0.5), (L * 0.66, W, H), pal[0], "organic"), P("sph", (L * 0.4, W * 0.05, H * 0.4), (L * 0.22, W * 0.62, H * 0.55), shade(pal[0], 0.92), "organic"),
           P("sph", (L * 0.5, W * 0.05, H * 0.32), (L * 0.1, W * 0.3, H * 0.28), shade(pal[0], 0.85), "organic")]
    for i in range(legs):
        x = (-0.22 if i < legs / 2 else 0.16) * L + (i % 2) * L * 0.06
        out.append(P("cap", (x, W * 0.5 + L * 0.1, H * 0.18), (H * 0.16, H * 0.16, L * 0.28), shade(pal[0], 0.82), "organic", (90, 0, 8 * (i % 2))))
    if tail:
        out.append(rod_x(-L * 0.33, -L * (0.33 + tail), H * 0.14, shade(pal[0], 0.9), "organic", z=H * 0.45, t=0.4))
    return out


def T_bird(L, W, H, pal):
    return [P("sph", (0, 0, H * 0.5), (L * 0.65, W, H), pal[0], "organic"), P("sph", (L * 0.38, 0, H * 0.55), (L * 0.22, W * 0.6, H * 0.5), shade(pal[0], 0.9), "organic"),
            P("wedge", (-L * 0.42, 0, H * 0.5), (L * 0.25, W * 0.8, H * 0.2), shade(pal[0], 0.8), "organic", (0, 90, 0))]


# ---- long things: along X, working profile in XY, lying on the ground
def T_bat(L, W, H, pal, nails=False):
    d = max(W, H)
    out = [rod_x(-L / 2, L * 0.05, d * 0.5, pal[0], "wood", t=1.5), rod_x(L * 0.05, L / 2, d, pal[0], "wood"), rod_x(-L / 2, -L * 0.3, d * 0.56, pal[1], "rubber")]
    if nails:
        for i in range(6):
            x = L * (0.15 + 0.06 * i)
            out.append(P("cyl", (x, d * 0.45, d / 2), (0.006, 0.006, d * 0.7), METAL, "metal", (90, 0, (i % 2) * 40)))
    return out


def T_shaft_head(L, W, H, pal, head="axe", shaft=None, headcol=None, grip_len=0.0):
    """handle + working head (axe, hammer, sledge, pick)"""
    shaft = shaft or max(0.028, min(W, H) * 0.42)
    hc = headcol or DARKMETAL
    out = [rod_x(-L / 2, L / 2 - shaft * 0.5, shaft, pal[0] if head not in ("stone",) else WOOD, "wood")]
    hx = L / 2 - max(0.03, W * 0.2)
    if head == "axe":
        # the eye round the handle, and a flared bit out to one side
        out += [P("box", (hx, W * 0.05, shaft / 2), (0.075, W * 0.6, shaft * 1.25), hc, "metal"),
                P("box", (hx, W * 0.46, shaft / 2), (W * 0.5, W * 0.32, shaft * 0.45), hc, "metal"),
                P("box", (hx, W * 0.63, shaft / 2), (W * 0.58, W * 0.05, shaft * 0.25), "#c8ced2", "metal")]
    elif head == "hammer":
        out += [P("box", (hx, 0, shaft / 2), (0.04, W, shaft * 1.3), hc, "metal"), P("box", (hx, W * 0.5, shaft / 2), (0.05, W * 0.12, shaft * 1.5), hc, "metal")]
    elif head == "sledge":
        out += [P("box", (hx, 0, shaft * 0.8), (W * 0.4, W, W * 0.4), hc, "metal")]
    elif head == "stone":
        out += [P("sph", (hx, 0, shaft * 0.7), (W * 0.4, W * 0.75, W * 0.45), hc, "stone"), P("cyl", (hx - W * 0.1, 0, shaft * 0.6), (shaft * 1.6, shaft * 1.6, W * 0.25), "#a08860", "cloth", (0, 90, 0))]
    if grip_len:
        out.append(rod_x(-L / 2, -L / 2 + grip_len, shaft * 1.12, pal[1], "rubber"))
    return out


def T_blade(L, W, H, pal, blade_frac=0.62, handle_col=None, guard=False):
    """a knife or machete: blade along +X, grip at -X"""
    bl = L * blade_frac
    hl = L - bl
    out = [P("box", (L / 2 - bl / 2, 0, max(H, 0.004) / 2), (bl, W, max(H * 0.3, 0.003)), "#c8ced2", "metal"),
           P("wedge", (L / 2 - 0.004, 0, max(H, 0.004) / 2), (W, 0.01, max(H * 0.3, 0.003)), "#c8ced2", "metal", (0, 0, 90)),
           P("box", (-L / 2 + hl / 2, 0, H / 2), (hl, W * 0.55, H), handle_col or pal[1], "wood")]
    if guard:
        out.append(P("box", (-L / 2 + hl, 0, H / 2), (0.012, W * 1.2, H * 1.1), DARKMETAL, "metal"))
    return out


def T_spear(L, W, H, pal, tip_col=METAL, shaft_col=None):
    d = max(0.024, min(W, H))
    return [rod_x(-L / 2, L / 2 - 0.22, d, shaft_col or pal[0], "wood"), P("cyl", (L / 2 - 0.11, 0, d / 2), (d * 1.6, d * 0.6, 0.22), tip_col, "metal", (0, 90, 0), t=0.0)]


def T_shovel(L, W, H, pal, small=False):
    d = 0.034 if not small else 0.028
    bw = 0.24 if not small else 0.15
    out = [rod_x(-L / 2 + 0.08, L / 2 - bw, d, pal[0] if not small else DARKMETAL, "wood"),
           P("box", (L / 2 - bw * 0.55, 0, 0.012), (bw * 1.1, bw, 0.018), DARKMETAL if not small else "#5a6a3a", "metal"),
           P("wedge", (L / 2 - 0.02, 0, 0.012), (bw, 0.06, 0.018), DARKMETAL, "metal", (0, 0, 90)), P("box", (-L / 2 + 0.04, 0, d / 2), (0.08, 0.13, d), pal[1], "plastic")]
    return out


def T_gun(L, W, H, pal, kind="pistol"):
    """a firearm lying along X: its height (H) runs along Y, its thickness (W) along Z"""
    blk = "#2b2d30"
    z = W * 0.5
    if kind == "pistol":
        return [P("box", (L * 0.1, H * 0.22, z), (L * 0.8, H * 0.3, W), blk, "metal"), P("box", (-L * 0.32, -H * 0.12, z), (L * 0.26, H * 0.6, W * 0.9), "#3a3226", "plastic", (0, 0, 14)),
                P("tor", (-L * 0.06, -H * 0.05, z), (H * 0.3, H * 0.3, 0.006), blk, "metal", (90, 0, 0))]
    if kind == "revolver":
        return [rod_x(L * 0.05, L / 2, H * 0.14, blk, "metal", y=H * 0.25, z=z), P("cyl", (-L * 0.05, H * 0.18, z), (H * 0.32, H * 0.32, L * 0.16), "#55595d", "metal", (0, 90, 0)),
                P("box", (-L * 0.36, -H * 0.12, z), (L * 0.22, H * 0.55, W * 0.8), "#6a4428", "wood", (0, 0, 20)), P("box", (-L * 0.2, H * 0.12, z), (L * 0.18, H * 0.3, W * 0.9), blk, "metal")]
    if kind == "rifle":
        return [P("box", (-L * 0.32, -H * 0.06, z), (L * 0.36, H * 0.55, W * 0.8), "#6a4428", "wood", (0, 0, -4)),
                P("box", (0, H * 0.06, z), (L * 0.3, H * 0.36, W), blk, "metal"), rod_x(L * 0.12, L / 2, H * 0.12, blk, "metal", y=H * 0.12, z=z),
                P("cyl", (-L * 0.02, H * 0.34, z), (H * 0.16, H * 0.16, L * 0.26), "#1c1d1f", "metal", (0, 90, 0)),
                P("box", (L * 0.18, H * 0.02, z), (L * 0.24, H * 0.18, W * 0.85), "#6a4428", "wood")]
    return [P("box", (-L * 0.33, -H * 0.06, z), (L * 0.34, H * 0.55, W * 0.8), "#6a4428", "wood", (0, 0, -4)), P("box", (-L * 0.05, H * 0.06, z), (L * 0.22, H * 0.38, W), blk, "metal"),
            rod_x(L * 0.05, L / 2, H * 0.14, blk, "metal", y=H * 0.16, z=z), rod_x(L * 0.05, L * 0.42, H * 0.14, blk, "metal", y=H * 0.02, z=z),
            P("box", (L * 0.2, H * 0.0, z), (L * 0.18, H * 0.2, W * 0.9), "#6a4428", "wood")]


def T_flat_tool(L, W, H, pal, jaw=True):
    """a wrench / bar: a flat bar with a head"""
    out = [P("box", (0, 0, H / 2), (L * 0.85, W * 0.28, H), pal[0] if pal[0] else METAL, "metal")]
    if jaw:
        out.append(P("box", (L * 0.42, 0, H / 2), (L * 0.16, W, H * 1.1), pal[0], "metal"))
    return out


def T_pan(L, W, H, pal):
    d = W
    return [P("cyl", (L / 2 - d / 2, 0, H / 2), (d, d, H), DARKMETAL, "metal"), P("cyl", (L / 2 - d / 2, 0, H * 0.8), (d * 0.86, d * 0.86, H * 0.3), "#3a3c3e", "metal"),
            rod_x(-L / 2, L / 2 - d * 0.95, 0.025, "#2a2420", "plastic", z=H * 0.7)]


def T_saw(L, W, H, pal):
    return [P("box", (L * 0.12, -W * 0.05, 0.002), (L * 0.75, W * 0.75, 0.003), "#c8ced2", "metal"), P("box", (L * 0.12, -W * 0.43, 0.002), (L * 0.75, W * 0.04, 0.003), "#8a9094", "metal"),
            P("box", (-L * 0.38, 0, 0.012), (L * 0.22, W * 0.8, 0.024), pal[0], "wood")]


def T_small_tool(L, W, H, pal):
    return [rod_x(-L / 2, -L * 0.05, max(W, H) * 0.9, pal[0], "plastic"), rod_x(-L * 0.05, L / 2, max(W, H) * 0.32, METAL, "metal", z=max(W, H) * 0.45)]


def T_pliers(L, W, H, pal):
    return [P("box", (-L * 0.15, -W * 0.18, H / 2), (L * 0.7, W * 0.22, H), pal[0], "plastic", (0, 0, 6)), P("box", (-L * 0.15, W * 0.18, H / 2), (L * 0.7, W * 0.22, H), pal[0], "plastic", (0, 0, -6)),
            P("box", (L * 0.32, 0, H / 2), (L * 0.36, W * 0.32, H), METAL, "metal")]


def T_cylinder_upright(L, W, H, pal, m="metal", top=None):
    d = max(L, W)
    out = [P("cyl", (0, 0, H / 2), (d, d, H), pal[0], m)]
    if top:
        out.append(P("cyl", (0, 0, H + 0.005), (d * 0.9, d * 0.9, 0.01), top, m))
    return out


def T_lantern(L, W, H, pal):
    d = max(L, W)
    return [P("cyl", (0, 0, H * 0.1), (d, d, H * 0.2), pal[0], "metal"), P("cyl", (0, 0, H * 0.5), (d * 0.8, d * 0.8, H * 0.6), "#f0e090", "glass"),
            P("cyl", (0, 0, H * 0.86), (d * 0.9, d * 0.9, H * 0.12), pal[0], "metal", t=0.6), P("tor", (0, 0, H * 0.97), (d * 0.5, d * 0.5, 0.008), DARKMETAL, "metal", (90, 0, 0))]


def T_radio(L, W, H, pal):
    return [P("box", (0, 0, H / 2), (L, W, H), pal[0], "plastic"), P("cyl", (-L * 0.2, -W * 0.51, H * 0.5), (H * 0.6, H * 0.6, 0.006), DARKMETAL, "metal", (90, 0, 0)),
            P("cyl", (L * 0.35, 0, H + 0.12), (0.006, 0.006, 0.24), METAL, "metal")]


def T_tyre(L, W, H, pal, upright=False):
    d = max(L, W)
    r = (90, 0, 0) if upright else (0, 0, 0)
    zc = d / 2 if upright else H / 2
    return [P("tor", (0, 0, zc), (d, d, d * 0.32), RUBBER, "rubber", r), P("cyl", (0, 0, zc), (d * 0.6, d * 0.6, d * 0.22), METAL, "metal", r)]


def T_glass_panel(L, W, H, pal, frame=None):
    out = [P("box", (0, 0, H / 2), (L, W, H), GLASS, "glass")]
    if frame:
        out.append(P("box", (0, 0, H * 0.04), (L, W, H * 0.08), frame, "rubber"))
    return out


def T_door(L, W, H, pal):
    """a car door lying flat: L long, W tall (now across the ground), H thick"""
    return [P("box", (0, -W * 0.25, H / 2), (L, W * 0.5, H), pal[0], "metal"), P("box", (0, W * 0.25, H * 0.3), (L * 0.92, W * 0.5, H * 0.3), GLASS, "glass"),
            P("box", (0, W * 0.48, H * 0.5), (L * 0.95, W * 0.04, H * 0.8), DARKMETAL, "metal"), P("box", (L * 0.3, -W * 0.1, H + 0.01), (L * 0.12, 0.03, 0.02), DARKMETAL, "metal")]


def T_generic(L, W, H, pal, m="plastic"):
    return [P("box", (0, 0, H / 2), (L, W, H), pal[0], m), P("box", (0, 0, H * 0.75), (L * 0.85, W * 0.85, H * 0.35), pal[1], m)]


def T_money(L, W, H, pal):
    return [P("box", (0, 0, H / 2), (L, W, H), "#8fae7a", "paper"), P("box", (0, 0, H * 0.5), (L * 0.15, W * 1.01, H * 1.01), "#e8e0c0", "paper")]


def T_toy(L, W, H, pal):
    return [P("sph", (0, 0, H * 0.3), (L * 0.7, W * 0.7, H * 0.6), pal[0], "cloth"), P("sph", (0, 0, H * 0.75), (L * 0.55, W * 0.55, H * 0.45), pal[0], "cloth"),
            P("sph", (-L * 0.2, 0, H * 0.95), (L * 0.18, W * 0.18, H * 0.18), pal[0], "cloth"), P("sph", (L * 0.2, 0, H * 0.95), (L * 0.18, W * 0.18, H * 0.18), pal[0], "cloth")]


def T_pillow(L, W, H, pal):
    return [P("sph", (0, 0, H / 2), (L, W, H), pal[0], "cloth"), P("box", (0, 0, H * 0.35), (L * 0.8, W * 0.8, H * 0.6), pal[0], "cloth")]


def T_bone(L, W, H, pal):
    d = max(W, H)
    return [rod_x(-L * 0.38, L * 0.38, d * 0.45, BONE, "organic"), P("sph", (-L * 0.42, 0, d / 2), (d * 1.1, d, d), BONE, "organic"), P("sph", (L * 0.42, 0, d / 2), (d * 1.1, d, d), BONE, "organic")]


def T_armor_piece(L, W, H, pal, m="metal"):
    return [P("cyl", (0, 0, H / 2), (W, H * 2, L), pal[0], m, (0, 90, 0)), P("box", (0, 0, H * 0.1), (L * 0.95, W * 0.9, H * 0.2), pal[1], "cloth")]


def T_mask(L, W, H, pal, m="cloth"):
    return [P("sph", (0, 0, 0), (L, W, H * 2), pal[0], m), P("sph", (L * 0.18, W * 0.2, H * 0.6), (L * 0.18, W * 0.14, H * 0.2), "#1a1a1a", m), P("sph", (L * 0.18, -W * 0.2, H * 0.6), (L * 0.18, W * 0.14, H * 0.2), "#1a1a1a", m)]


def T_goggles(L, W, H, pal):
    return [P("cyl", (0, W * 0.25, H / 2), (W * 0.45, W * 0.45, H), GLASS, "glass", (0, 90, 0)), P("cyl", (0, -W * 0.25, H / 2), (W * 0.45, W * 0.45, H), GLASS, "glass", (0, 90, 0)),
            P("box", (-L * 0.1, 0, H * 0.3), (L * 0.2, W * 1.1, H * 0.2), "#2a2a2a", "rubber")]


def T_binoculars(L, W, H, pal):
    return [rod_x(-L / 2, L / 2, H, pal[0], "plastic", y=W * 0.25, t=1.15), rod_x(-L / 2, L / 2, H, pal[0], "plastic", y=-W * 0.25, t=1.15), P("box", (0, 0, H / 2), (L * 0.3, W * 0.5, H * 0.5), DARKMETAL, "metal")]


def T_candle(L, W, H, pal):
    d = max(L, W)
    return [P("cyl", (0, 0, H / 2), (d, d, H), "#f0e6c8", "organic"), P("cyl", (0, 0, H + 0.006), (0.004, 0.004, 0.012), "#2a2a2a", "cloth")]


def T_extinguisher(L, W, H, pal):
    d = max(L, W)
    return [P("cyl", (0, 0, H * 0.44), (d, d, H * 0.88), "#c0392b", "metal"), P("sph", (0, 0, H * 0.88), (d, d, d * 0.6), "#c0392b", "metal"),
            P("box", (0, 0, H * 0.98), (d * 0.8, d * 0.25, H * 0.06), DARKMETAL, "metal")]


def T_gascan(L, W, H, pal):
    return [P("box", (0, 0, H * 0.42), (L, W, H * 0.84), pal[0], "plastic"), P("cyl", (L * 0.32, 0, H * 0.95), (W * 0.25, W * 0.25, H * 0.2), pal[0], "plastic", (0, 30, 0)),
            P("box", (-L * 0.1, 0, H * 0.9), (L * 0.5, W * 0.2, H * 0.1), pal[0], "plastic")]


def T_battery(L, W, H, pal):
    return [P("box", (0, 0, H * 0.45), (L, W, H * 0.9), "#2a2c2e", "plastic"), P("box", (0, 0, H * 0.92), (L, W, H * 0.06), pal[0], "plastic"),
            P("cyl", (-L * 0.32, 0, H * 0.98), (W * 0.12, W * 0.12, H * 0.06), "#c0392b", "metal"), P("cyl", (L * 0.32, 0, H * 0.98), (W * 0.12, W * 0.12, H * 0.06), METAL, "metal")]


def T_sheet(L, W, H, pal, m="cloth"):
    return [P("box", (0, 0, H / 2), (L, W, H), pal[0], m), P("box", (0, 0, H * 0.9), (L * 0.98, W * 0.5, H * 0.2), shade(pal[0], 1.08), m)]


def T_plank(L, W, H, pal):
    return [P("box", (0, 0, H / 2), (L, W, H), pal[0] if pal[0] != "#888888" else WOOD, "wood")]


def T_log(L, W, H, pal):
    d = max(W, H)
    return [rod_x(-L / 2, L / 2, d, "#6a4a30", "wood"), P("cyl", (L / 2, 0, d / 2), (d * 0.92, d * 0.92, 0.004), "#c8a070", "wood", (0, 90, 0))]


def T_stone(L, W, H, pal):
    return [P("sph", (0, 0, H / 2), (L, W, H), pal[0], "stone"), P("sph", (L * 0.15, W * 0.1, H * 0.6), (L * 0.6, W * 0.6, H * 0.7), shade(pal[0], 1.06), "stone")]


def T_lump(L, W, H, pal, m="organic"):
    return [P("sph", (0, 0, H / 2), (L, W, H), pal[0], m), P("sph", (-L * 0.2, W * 0.1, H * 0.45), (L * 0.6, W * 0.7, H * 0.8), shade(pal[0], 0.95), m)]


def T_pot(L, W, H, pal, m="metal", handles=True):
    d = max(L, W)
    out = [P("cyl", (0, 0, H / 2), (d, d, H), pal[0], m), P("cyl", (0, 0, H * 0.96), (d * 0.88, d * 0.88, H * 0.06), shade(pal[0], 0.6), m)]
    if handles:
        out += [P("box", (d * 0.55, 0, H * 0.8), (d * 0.16, d * 0.12, 0.012), DARKMETAL, "metal"), P("box", (-d * 0.55, 0, H * 0.8), (d * 0.16, d * 0.12, 0.012), DARKMETAL, "metal")]
    return out


def T_bucket(L, W, H, pal):
    d = max(L, W)
    return [P("cyl", (0, 0, H / 2), (d, d, H), pal[0], "metal", t=1.18), P("cyl", (0, 0, H * 0.97), (d * 1.08, d * 1.08, H * 0.04), shade(pal[0], 0.8), "metal"),
            P("tor", (0, 0, H), (d * 1.0, d * 1.0, 0.006), DARKMETAL, "metal", (90, 0, 0))]


def T_cone_upright(L, W, H, pal):
    d = max(L, W)
    return [P("box", (0, 0, 0.01), (d * 1.1, d * 1.1, 0.02), "#1a1a1a", "rubber"), P("cyl", (0, 0, H / 2), (d * 0.85, d * 0.85, H), "#e86a1a", "plastic", t=0.12),
            P("cyl", (0, 0, H * 0.55), (d * 0.52, d * 0.52, H * 0.1), "#f4f4f0", "plastic", t=0.8), P("cyl", (0, 0, H * 0.32), (d * 0.68, d * 0.68, H * 0.08), "#f4f4f0", "plastic", t=0.88)]


def T_coffin(L, W, H, pal):
    return [P("box", (0, 0, H * 0.45), (L, W, H * 0.9), "#8a5530", "wood"), P("box", (0, 0, H * 0.94), (L * 0.98, W * 0.94, H * 0.12), "#a86a3a", "wood"),
            P("box", (L * 0.2, 0, H * 1.0), (L * 0.04, W * 0.6, 0.01), "#c8a050", "metal")]


def T_cooler(L, W, H, pal):
    return [P("box", (0, 0, H * 0.4), (L, W, H * 0.8), "#2a62b8", "plastic"), P("box", (0, 0, H * 0.9), (L * 1.02, W * 1.02, H * 0.2), "#f2f2f0", "plastic"),
            P("box", (0, -W * 0.52, H * 0.82), (L * 0.3, 0.02, 0.04), "#f2f2f0", "plastic")]


def T_barrel(L, W, H, pal):
    d = max(L, W)
    return [P("cyl", (0, 0, H / 2), (d, d, H), "#3d6a8a", "metal"), P("tor", (0, 0, H * 0.33), (d * 1.02, d * 1.02, 0.02), "#2e5470", "metal"),
            P("tor", (0, 0, H * 0.66), (d * 1.02, d * 1.02, 0.02), "#2e5470", "metal"), P("cyl", (0, 0, H + 0.004), (d * 0.94, d * 0.94, 0.008), "#335a76", "metal"),
            P("cyl", (d * 0.25, 0, H + 0.01), (0.05, 0.05, 0.02), "#2a2a2a", "metal")]


def T_crate(L, W, H, pal, col="#4f5a36"):
    return [P("box", (0, 0, H * 0.42), (L, W, H * 0.84), col, "metal"), P("box", (0, 0, H * 0.92), (L * 1.02, W * 1.02, H * 0.16), shade(col, 1.1), "metal"),
            P("box", (L * 0.3, 0, H * 0.5), (0.04, W * 1.03, H * 0.86), shade(col, 0.8), "metal"), P("box", (-L * 0.3, 0, H * 0.5), (0.04, W * 1.03, H * 0.86), shade(col, 0.8), "metal"),
            P("box", (0, -W * 0.52, H * 0.78), (0.06, 0.02, 0.08), METAL, "metal")]


def T_boxes(L, W, H, pal):
    return [P("box", (-L * 0.08, W * 0.05, H * 0.27), (L * 0.85, W * 0.85, H * 0.54), "#b08a5a", "paper"), P("box", (-L * 0.08, W * 0.05, H * 0.535), (L * 0.86, 0.06, 0.004), "#d8c8a0", "paper"),
            P("box", (L * 0.1, -W * 0.08, H * 0.77), (L * 0.6, W * 0.6, H * 0.46), "#a07c50", "paper", (0, 0, 14))]


def T_tyre_pile(L, W, H, pal):
    out = []
    for i in range(3):
        out += [P("tor", (0, 0, 0.11 + i * 0.2), (0.64, 0.64, 0.2), RUBBER, "rubber")]
    out.append(P("tor", (0.55, 0.15, 0.32), (0.64, 0.64, 0.2), RUBBER, "rubber", (78, 0, 20)))
    out.append(P("cyl", (0.55, 0.15, 0.32), (0.36, 0.36, 0.14), METAL, "metal", (78, 0, 20)))
    return out


# ------------------------------------------------------------------ which template each item uses
def kind_of(iid, it):
    n = it["n"].lower()
    cat = it["cat"]
    s = it["shape"]
    rules = [
        # weapons and long tools
        (r"^(baseball_bat)$", "bat"), (r"^nail_bat$", "nailbat"), (r"^(golf_club)$", "golf"), (r"^hockey_stick$", "hockey"), (r"^baton$", "baton"),
        (r"^(pipe|metal_bar)$", "pipe"), (r"^crowbar$", "crowbar"), (r"^tire_iron$", "tireiron"), (r"^(axe|fire_axe)$", "axe_long"), (r"^hatchet$", "hatchet"),
        (r"^stone_axe$", "stoneaxe"), (r"^(hammer)$", "hammer"), (r"^sledgehammer$", "sledge"), (r"^stone_hammer$", "stonehammer"), (r"^(shovel)$", "shovel"),
        (r"^folding_shovel$", "fshovel"), (r"^(spear)$", "spear_wood"), (r"^metal_spear$", "spear_metal"), (r"^(kitchen_knife)$", "knife"), (r"^hunting_knife$", "knife_hunt"),
        (r"^machete$", "machete"), (r"^cleaver$", "cleaver"), (r"^stone_knife$", "knife_stone"), (r"^bone_shiv$", "shiv"), (r"^bone_club$", "boneclub"),
        (r"^frying_pan$", "pan"), (r"^pistol$", "pistol"), (r"^revolver$", "revolver"), (r"^rifle$", "rifle"), (r"^shotgun$", "shotgun"),
        (r"^(wrench|pipe_wrench)$", "wrench"), (r"^screwdriver$", "screwdriver"), (r"^(saw|hand_saw)$", "saw"), (r"^hacksaw$", "hacksaw"), (r"^(pliers|wire_cutters|bolt_cutters)$", "pliers"),
        (r"^scissors$", "pliers_small"), (r"^trowel$", "trowel"), (r"^fishing_rod$", "rod"), (r"^pocket_knife$", "pocketknife"), (r"^multitool$", "multitool"), (r"^wooden_handle$", "handle"),
        (r"^(branch)$", "branch"), (r"^log$", "log"), (r"^plank$", "plank"), (r"^(bone)$", "bone"), (r"^(pencil)$", "pencil"), (r"^tweezers$", "tweezers"),
        # vehicle parts and big things
        (r"^(spare_wheel)$", "tyre"), (r"^tyre_kit$", "box_small"), (r"^car_door$", "cardoor"), (r"^windscreen$", "windscreen"), (r"^glass_pane$", "glasspane"),
        (r"^radiator$", "radiator"), (r"^(alternator|starter_motor|fuel_pump)$", "motorpart"), (r"^spark_plug$", "sparkplug"), (r"^fan_belt$", "belt"),
        (r"^(air_filter|oil_filter|water_filter)$", "filter"), (r"^headlight_bulb$", "bulb"), (r"^muffler$", "muffler"), (r"^car_battery$", "battery"),
        (r"^generator_item$", "generator"), (r"^(gas_can)$", "gascan"), (r"^fire_extinguisher$", "extinguisher"), (r"^(motor_oil|bleach)$", "jug"),
        # containers and bottles
        (r"^(water_jug|empty_water_jug)$", "waterjug"), (r"^(canteen)$", "canteen"), (r"^(bucket)$", "bucket"), (r"^watering_can$", "wateringcan"),
        (r"^(cooking_pot|clay_pot|unfired_pot)$", "pot"), (r"^(stew|rice_bowl|pasta_bowl|pumpkin_soup|noodle_soup)$", "potfull"),
        (r"^(beer|wine|whiskey|brandy|champagne|cider|coffee_liqueur|empty_bottle|vinegar)$", "bottle_glass"),
        (r"^(water_bottle|sports_drink|disinfectant|iodine|gun_oil|plant_cure|milk)$", "bottle"),
        (r"^(soda|orange_soda|lemon_soda|energy_drink|canned_water)$", "sodacan"), (r"^(sardines|canned_tuna|cat_food|dog_food)$", "tin_flat"),
        (r"^(canned_|black_beans|mixed_veg|fruit_cocktail|condensed_milk|empty_can|powdered_milk)", "can"),
        (r"^(peanut_butter|jam|honey|preserves|pickles|glass_jar|vitamins|coffee|cocoa)$", "jar"),
        (r"^(antibiotics|antidepressants|aspirin|beta_blockers|painkillers|sleeping_pills|cold_medicine)$", "pills"),
        # food
        (r"^(apple|orange|tomato|onion|pepper|avocado|garlic|radish|beet|egg|cooked_egg|potato|mushroom|oyster_mushroom)$", "fruit"),
        (r"^(cabbage|lettuce|cauliflower|broccoli|pumpkin|squash|spinach)$", "veg_big"), (r"^(carrot)$", "carrot"), (r"^banana$", "banana"),
        (r"^(berries|blueberries|blackberries|cherries|brussels_sprouts|strawberry|mixed_nuts|trail_mix|dried_fruit|caramels|gummy_candy)$", "cluster"),
        (r"^(corn|cooked_corn|cucumber|pea|beans|baguette|hot_dog|corn_dog)$", "longfood"), (r"^(bread|cornbread|bologna)$", "loaf"),
        (r"^(bagel)$", "bagel"), (r"^(cake|cinnamon_roll|burger|cheese)$", "stackfood"), (r"^(sandwich)$", "sandwich"),
        (r"^(raw_|cooked_|smoked_|burnt_food|roast_veg|jerky)", "meat"),
        (r"^(juice|cranberry_juice)$", "carton"), (r"^(chips|crackers|cereal|cookies|oats|pasta|rice|instant_noodles|flour|sugar|salt|fertilizer|sand|charcoal|mre|crispbread)$", "pack"), (r"^gunpowder$", "can"),
        (r"^(chocolate|granola_bar|protein_bar|chewing_gum)$", "bar"), (r"^(ice_cream)$", "icecream"), (r"^(tea|calming_tea)$", "box_small"),
        (r"^seeds_", "seedpacket"), (r"^(wheat|herbs|sunflower)$", "bundle"),
        # clothing
        (r"^(boots|hiking_boots|rubber_boots|cowboy_boots|sneakers)$", "boots"), (r"^(leather_gloves|work_gloves|chainmail_glove)$", "gloves"),
        (r"^(baseball_cap|police_cap)$", "cap"), (r"^(hard_hat|bike_helmet|combat_helmet|moto_helmet|riot_helmet)$", "helmet"),
        (r"^(beanie|wool_hat|beret|chef_hat|bucket_hat|balaclava)$", "softhat"), (r"^cowboy_hat$", "cowboyhat"),
        (r"^(gas_mask|dust_mask|bone_mask|bandana)$", "mask"), (r"^goggles$", "goggles"),
        (r"^(scrap_shin_guards|riot_shin_guards|bone_shin_guards|scrap_shoulder_pads|bone_bracers|leather_bracers|studded_bracers|chainmail_sleeve|arm_wraps)$", "armorpiece"),
        (r"^(kevlar_vest|chest_protector|bone_chest)$", "vest_hard"),
        # bags
        (r"^(backpack|hiking_pack|military_pack|school_bag)$", "backpack"), (r"^(duffel_bag)$", "duffel"), (r"^(satchel|tote_bag|fanny_pack|chest_rig|first_aid_pouch)$", "satchel"),
        # paper
        (r"^book_|^(novel|diary|notebook|road_atlas)$", "book"), (r"^(comic)$", "comic"),
        (r"^(newspaper|letter|note|survivor_note|bulletin|evac_flyer|hospital_note|inventory_list|lab_report|local_map|maintenance_log|radio_transcript|recipe_note|family_photo)$", "paper"),
        (r"^(playing_cards|matches|cigarettes|cigar|lighter|alcohol_wipes|antiseptic_wipes|sterile_dressing|ammo_9mm|shells|rifle_rounds|battery|glowstick|chess_set|whetstone|brick)$", "box_small"),
        (r"^(first_aid_kit|suture_kit|sewing_kit)$", "kitbox"),
        # misc
        (r"^(rope|twine|wire|duct_tape)$", "coil"), (r"^(sheet|rag|tarp|plastic_sheet|leather|bedroll_item|garbage_bag)$", "sheet"),
        (r"^(scrap_metal|sheet_metal)$", "scrap"), (r"^(stone|clay)$", "stone"), (r"^(nails|screws)$", "nails"),
        (r"^(lantern|flashlight|headlamp)$", "lantern"), (r"^(radio|crank_radio|alarm_clock)$", "radio"), (r"^binoculars$", "binoculars"), (r"^compass$", "compass"),
        (r"^candle$", "candle"), (r"^(can_opener|car_keys|needle_thread|hand_bell|snare)$", "small"), (r"^(money)$", "money"), (r"^toy$", "toy"), (r"^pillow$", "pillow"),
        (r"^(bandage|field_splint|splint)$", "bandage"), (r"^(glue|herbs)$", "small"),
        (r"^carcass_(deer|boar|dog|fox)$", "animal_big"), (r"^carcass_(rabbit|hare|squirrel|rat|mouse|frog)$", "animal_small"), (r"^carcass_snake$", "snake"),
        (r"^carcass_", "bird"),
    ]
    for pat, k in rules:
        if re.search(pat, iid):
            return k
    if cat == "clothing":
        slot = re.search(r'"slot": "([a-z]+)"', it.get("rest", ""))
        return "cloth_legs" if slot and slot.group(1) == "legs" else "cloth_torso"
    return "generic"


# default real-world sizes (L, W, H) in metres for each template, used where the catalog has no match
DEFAULT = {
    "bat": (0.84, 0.068, 0.068), "nailbat": (0.84, 0.07, 0.07), "golf": (1.0, 0.1, 0.04), "hockey": (1.5, 0.3, 0.03), "baton": (0.55, 0.035, 0.035), "pipe": (0.6, 0.035, 0.035),
    "crowbar": (0.75, 0.06, 0.03), "tireiron": (0.55, 0.12, 0.03), "axe_long": (0.9, 0.22, 0.06), "hatchet": (0.38, 0.16, 0.04), "stoneaxe": (0.5, 0.15, 0.06),
    "hammer": (0.32, 0.12, 0.03), "sledge": (0.9, 0.2, 0.08), "stonehammer": (0.38, 0.12, 0.08), "shovel": (1.1, 0.24, 0.05), "fshovel": (0.6, 0.15, 0.04),
    "spear_wood": (1.6, 0.04, 0.04), "spear_metal": (1.4, 0.05, 0.05), "knife": (0.32, 0.045, 0.02), "knife_hunt": (0.3, 0.04, 0.025), "machete": (0.6, 0.06, 0.025),
    "cleaver": (0.32, 0.09, 0.02), "knife_stone": (0.22, 0.05, 0.02), "shiv": (0.2, 0.03, 0.025), "boneclub": (0.45, 0.07, 0.06), "pan": (0.48, 0.26, 0.05),
    "pistol": (0.2, 0.035, 0.14), "revolver": (0.27, 0.04, 0.15), "rifle": (1.1, 0.06, 0.2), "shotgun": (1.05, 0.06, 0.18), "wrench": (0.3, 0.07, 0.015),
    "screwdriver": (0.22, 0.03, 0.03), "saw": (0.6, 0.14, 0.02), "hacksaw": (0.4, 0.12, 0.02), "pliers": (0.22, 0.07, 0.015), "pliers_small": (0.18, 0.08, 0.012),
    "trowel": (0.3, 0.09, 0.03), "rod": (1.8, 0.05, 0.03), "pocketknife": (0.1, 0.03, 0.015), "multitool": (0.11, 0.04, 0.02), "nails": (0.1, 0.08, 0.03), "handle": (0.45, 0.04, 0.04), "branch": (0.9, 0.05, 0.05), "log": (1.2, 0.25, 0.25),
    "plank": (1.2, 0.15, 0.03), "bone": (0.3, 0.05, 0.04), "pencil": (0.18, 0.008, 0.008), "tweezers": (0.1, 0.012, 0.006),
    "tyre": (0.64, 0.64, 0.2), "cardoor": (1.1, 1.0, 0.12), "windscreen": (1.4, 0.8, 0.06), "glasspane": (0.6, 0.5, 0.008), "radiator": (0.6, 0.05, 0.45),
    "motorpart": (0.22, 0.16, 0.16), "sparkplug": (0.09, 0.022, 0.022), "belt": (0.3, 0.12, 0.02), "filter": (0.12, 0.12, 0.14), "bulb": (0.07, 0.03, 0.03), "muffler": (0.7, 0.22, 0.14),
    "battery": (0.28, 0.17, 0.2), "generator": (0.6, 0.45, 0.45), "gascan": (0.32, 0.17, 0.32), "extinguisher": (0.16, 0.16, 0.5), "jug": (0.14, 0.09, 0.28),
    "waterjug": (0.34, 0.2, 0.4), "canteen": (0.15, 0.07, 0.2), "bucket": (0.3, 0.3, 0.3), "wateringcan": (0.42, 0.18, 0.3), "pot": (0.26, 0.26, 0.16), "potfull": (0.26, 0.26, 0.16),
    "bottle_glass": (0.075, 0.075, 0.3), "bottle": (0.065, 0.065, 0.22), "sodacan": (0.066, 0.066, 0.122), "tin_flat": (0.105, 0.075, 0.03), "can": (0.075, 0.075, 0.11),
    "jar": (0.08, 0.08, 0.11), "pills": (0.045, 0.045, 0.08), "fruit": (0.08, 0.08, 0.075), "veg_big": (0.18, 0.18, 0.15), "carrot": (0.18, 0.03, 0.03), "banana": (0.2, 0.04, 0.04),
    "cluster": (0.1, 0.08, 0.04), "longfood": (0.2, 0.05, 0.05), "loaf": (0.25, 0.12, 0.1), "bagel": (0.11, 0.11, 0.035), "stackfood": (0.2, 0.2, 0.09), "sandwich": (0.14, 0.1, 0.06),
    "meat": (0.2, 0.12, 0.03), "pack": (0.19, 0.07, 0.28), "carton": (0.065, 0.065, 0.13), "bar": (0.11, 0.035, 0.015), "icecream": (0.16, 0.1, 0.08), "seedpacket": (0.08, 0.005, 0.12), "bundle": (0.45, 0.08, 0.08),
    "boots": (0.3, 0.24, 0.22), "gloves": (0.24, 0.2, 0.03), "cap": (0.2, 0.2, 0.1), "helmet": (0.28, 0.24, 0.16), "softhat": (0.22, 0.2, 0.1), "cowboyhat": (0.38, 0.3, 0.13),
    "mask": (0.2, 0.18, 0.12), "goggles": (0.18, 0.09, 0.06), "armorpiece": (0.32, 0.14, 0.06), "vest_hard": (0.45, 0.35, 0.08), "backpack": (0.34, 0.22, 0.48), "duffel": (0.6, 0.3, 0.3),
    "satchel": (0.3, 0.1, 0.25), "book": (0.22, 0.15, 0.03), "comic": (0.26, 0.17, 0.006), "paper": (0.28, 0.21, 0.004), "box_small": (0.1, 0.06, 0.04), "kitbox": (0.25, 0.18, 0.08),
    "coil": (0.25, 0.25, 0.08), "sheet": (0.4, 0.3, 0.06), "scrap": (0.35, 0.25, 0.05), "stone": (0.12, 0.1, 0.08), "lantern": (0.12, 0.12, 0.25), "radio": (0.24, 0.08, 0.14),
    "binoculars": (0.16, 0.12, 0.06), "compass": (0.07, 0.07, 0.02), "candle": (0.05, 0.05, 0.14), "small": (0.12, 0.05, 0.03), "money": (0.16, 0.07, 0.02), "toy": (0.2, 0.15, 0.25),
    "pillow": (0.6, 0.4, 0.14), "bandage": (0.08, 0.08, 0.06), "animal_big": (1.5, 0.4, 0.45), "animal_small": (0.4, 0.15, 0.13), "snake": (1.1, 0.06, 0.05), "bird": (0.35, 0.18, 0.16),
    "cloth_torso": (0.4, 0.32, 0.07), "cloth_legs": (0.38, 0.3, 0.06), "generic": (0.15, 0.1, 0.08),
}
# sizes the catalog's estimates get wrong for the game's own items, or that differ by species
SIZE = {"carcass_deer": (1.6, 0.42, 0.5), "carcass_boar": (1.3, 0.45, 0.45), "carcass_dog": (0.9, 0.3, 0.3), "carcass_fox": (0.75, 0.22, 0.22),
        "carcass_rabbit": (0.42, 0.16, 0.14), "carcass_hare": (0.5, 0.17, 0.15), "carcass_squirrel": (0.3, 0.1, 0.09), "carcass_rat": (0.25, 0.08, 0.07), "carcass_mouse": (0.1, 0.04, 0.035),
        "carcass_frog": (0.12, 0.07, 0.05), "carcass_turkey": (0.8, 0.4, 0.35), "carcass_goose": (0.7, 0.3, 0.25), "carcass_duck": (0.5, 0.22, 0.18), "carcass_chicken": (0.42, 0.22, 0.2),
        "carcass_pigeon": (0.3, 0.14, 0.12), "carcass_crow": (0.4, 0.16, 0.12), "carcass_bird": (0.6, 0.22, 0.18), "pumpkin": (0.32, 0.32, 0.26), "cabbage": (0.18, 0.18, 0.16),
        "lettuce": (0.2, 0.2, 0.13), "egg": (0.06, 0.045, 0.045), "cooked_egg": (0.12, 0.1, 0.012), "garlic": (0.05, 0.05, 0.05), "radish": (0.04, 0.04, 0.04), "potato": (0.09, 0.06, 0.05),
        "mushroom": (0.07, 0.07, 0.05), "oyster_mushroom": (0.08, 0.06, 0.03), "corn": (0.22, 0.05, 0.05), "cucumber": (0.2, 0.045, 0.045), "pea": (0.09, 0.015, 0.012), "beans": (0.12, 0.012, 0.012),
        "baguette": (0.6, 0.07, 0.06), "hot_dog": (0.18, 0.05, 0.05), "corn_dog": (0.25, 0.04, 0.04), "cheese": (0.12, 0.08, 0.06), "cake": (0.22, 0.22, 0.1), "cinnamon_roll": (0.1, 0.1, 0.05),
        "burger": (0.11, 0.11, 0.08), "bologna": (0.28, 0.07, 0.07), "bread": (0.25, 0.12, 0.1), "cornbread": (0.18, 0.12, 0.05), "money": (0.16, 0.07, 0.015),
        "playing_cards": (0.09, 0.064, 0.02), "matches": (0.05, 0.035, 0.015), "cigarettes": (0.055, 0.022, 0.085), "cigar": (0.14, 0.02, 0.02), "lighter": (0.08, 0.025, 0.012),
        "chess_set": (0.4, 0.2, 0.05), "whetstone": (0.18, 0.06, 0.03), "brick": (0.21, 0.1, 0.065), "battery": (0.05, 0.014, 0.014), "glowstick": (0.15, 0.015, 0.015),
        "ammo_9mm": (0.1, 0.06, 0.04), "shells": (0.11, 0.07, 0.07), "rifle_rounds": (0.1, 0.05, 0.07), "nails": (0.12, 0.08, 0.05), "screws": (0.1, 0.07, 0.04),
        "alcohol_wipes": (0.08, 0.06, 0.01), "antiseptic_wipes": (0.15, 0.1, 0.015), "sterile_dressing": (0.1, 0.1, 0.01), "tea": (0.12, 0.07, 0.07), "calming_tea": (0.12, 0.07, 0.07),
        "tyre_kit": (0.2, 0.12, 0.06), "car_keys": (0.08, 0.04, 0.01), "can_opener": (0.18, 0.05, 0.02), "needle_thread": (0.04, 0.04, 0.05), "hand_bell": (0.1, 0.1, 0.18),
        "snare": (0.3, 0.3, 0.02), "glue": (0.15, 0.03, 0.03), "herbs": (0.15, 0.06, 0.04), "tarp": (0.5, 0.35, 0.08), "bedroll_item": (0.6, 0.2, 0.2), "garbage_bag": (0.5, 0.4, 0.3),
        "leather": (0.5, 0.4, 0.02), "rag": (0.25, 0.2, 0.02), "plastic_sheet": (0.4, 0.3, 0.04), "sheet_metal": (0.6, 0.4, 0.004), "scrap_metal": (0.35, 0.25, 0.06), "metal_bar": (0.5, 0.03, 0.03),
        "twine": (0.12, 0.12, 0.06), "duct_tape": (0.12, 0.12, 0.05), "wire": (0.2, 0.2, 0.05), "rope": (0.35, 0.35, 0.1), "family_photo": (0.15, 0.1, 0.005), "local_map": (0.25, 0.2, 0.005),
        "road_atlas": (0.3, 0.22, 0.015), "diary": (0.18, 0.13, 0.025), "notebook": (0.21, 0.15, 0.012), "novel": (0.18, 0.11, 0.03), "chest_rig": (0.4, 0.3, 0.06), "fanny_pack": (0.3, 0.1, 0.1),
        "first_aid_pouch": (0.2, 0.08, 0.14), "tote_bag": (0.4, 0.12, 0.38), "school_bag": (0.3, 0.18, 0.4), "military_pack": (0.4, 0.28, 0.58), "hiking_pack": (0.36, 0.26, 0.62),
        "flashlight": (0.25, 0.05, 0.05), "headlamp": (0.1, 0.08, 0.05), "alarm_clock": (0.12, 0.07, 0.14), "crank_radio": (0.18, 0.07, 0.12), "clay_pot": (0.22, 0.22, 0.2),
        "unfired_pot": (0.22, 0.22, 0.2), "milk": (0.08, 0.08, 0.2), "iodine": (0.04, 0.04, 0.09), "gun_oil": (0.05, 0.05, 0.1), "vinegar": (0.07, 0.07, 0.25), "empty_bottle": (0.065, 0.065, 0.22),
        "coffee": (0.1, 0.1, 0.14), "cocoa": (0.1, 0.1, 0.12), "vitamins": (0.05, 0.05, 0.09), "powdered_milk": (0.12, 0.12, 0.16), "flour": (0.2, 0.1, 0.3), "sugar": (0.15, 0.08, 0.22),
        "salt": (0.08, 0.05, 0.13), "sand": (0.35, 0.15, 0.5), "fertilizer": (0.4, 0.15, 0.6), "charcoal": (0.3, 0.12, 0.45), "gunpowder": (0.1, 0.1, 0.13), "mre": (0.25, 0.13, 0.05),
        "crispbread": (0.2, 0.1, 0.06), "pasta": (0.2, 0.06, 0.25), "rice": (0.15, 0.08, 0.25), "oats": (0.15, 0.08, 0.22), "instant_noodles": (0.12, 0.12, 0.04), "chips": (0.2, 0.08, 0.28),
        "cooking_pot": (0.26, 0.26, 0.16), "watering_can": (0.45, 0.18, 0.3), "canteen": (0.15, 0.07, 0.2), "toy": (0.2, 0.15, 0.25), "bandage": (0.08, 0.08, 0.06),
        "splint": (0.4, 0.08, 0.04), "field_splint": (0.45, 0.1, 0.04), "gas_mask": (0.22, 0.18, 0.16), "dust_mask": (0.15, 0.12, 0.06), "bandana": (0.25, 0.25, 0.01), "winter_coat": (0.5, 0.4, 0.1),
        "padded_jacket": (0.48, 0.38, 0.1), "firefighter_coat": (0.5, 0.4, 0.12), "rain_poncho": (0.35, 0.25, 0.05), "scarf": (0.4, 0.12, 0.03), "riot_helmet": (0.3, 0.26, 0.2)}

# shapes catalog dimensions describe standing up; ours lie along X
LONG = {"bat", "nailbat", "golf", "hockey", "baton", "pipe", "crowbar", "tireiron", "axe_long", "hatchet", "stoneaxe", "hammer", "sledge", "stonehammer", "shovel", "fshovel",
        "spear_wood", "spear_metal", "knife", "knife_hunt", "machete", "cleaver", "knife_stone", "shiv", "boneclub", "pan", "wrench", "screwdriver", "saw", "hacksaw", "pliers",
        "pliers_small", "trowel", "rod", "pocketknife", "handle", "branch", "log", "plank", "bone", "pencil", "tweezers", "pistol", "revolver", "rifle", "shotgun"}
HELD = LONG - {"branch", "log", "plank", "bone", "pencil", "tweezers", "pocketknife", "handle", "rod"}


def dims_for(iid, kind):
    if iid in SIZE:
        return SIZE[iid], "LAST_LIGHT_SIZE_TABLE"
    it = ITEMS[iid]
    cands = [norm(it["n"]), norm(iid), norm(it["n"].replace("Canned ", "")) + "can"]
    a = next((by_name[c] for c in cands if c in by_name), None)
    dflt = DEFAULT.get(kind, DEFAULT["generic"])
    if a and a.get("dims"):
        d = sorted([float(v) for v in a["dims"]], reverse=True)
        L, W, H = d[0], d[1], d[2]
        # the catalog's numbers are estimates: keep them when they agree with the template within a factor of 2.5
        ok = 0.4 <= L / dflt[0] <= 2.5
        if ok:
            if kind in LONG or kind in ("cloth_torso", "cloth_legs", "sheet", "paper", "book", "comic", "meat"):
                return (L, W, H), a["id"]
            # upright things: catalog Z is height
            x, y, z = [float(v) for v in a["dims"]]
            return (max(x, y), min(x, y), z), a["id"]
    return dflt, "TEMPLATE_DEFAULT"


def build(iid, kind, L, W, H, pal):
    if kind == "bat": return T_bat(L, W, H, pal)
    if kind == "nailbat": return T_bat(L, W, H, pal, nails=True)
    if kind == "golf": return [rod_x(-L / 2, L / 2 - 0.08, 0.014, METAL, "metal", t=1.0), P("box", (L / 2 - 0.04, W * 0.2, 0.025), (0.08, W * 0.5, 0.04), DARKMETAL, "metal"), rod_x(-L / 2, -L / 2 + 0.25, 0.026, "#1a1a1a", "rubber")]
    if kind == "hockey": return [rod_x(-L / 2, L / 2 - 0.25, 0.03, pal[0], "wood"), P("box", (L / 2 - 0.13, W * 0.25, 0.02), (0.3, 0.08, 0.03), pal[0], "wood", (0, 0, -25)), rod_x(-L / 2, -L / 2 + 0.2, 0.034, "#1a1a1a", "rubber")]
    if kind == "baton": return [rod_x(-L / 2, L / 2, max(W, H), "#1c1d20", "rubber"), rod_x(-L / 2, -L / 2 + 0.15, max(W, H) * 1.15, "#2a2a2a", "rubber")]
    if kind == "pipe": return [rod_x(-L / 2, L / 2, max(W, H), METAL if iid != "pipe" else "#7a7f84", "metal")]
    if kind == "crowbar": return [rod_x(-L / 2, L / 2 - 0.08, 0.025, "#b03028", "metal"), P("tor", (L / 2 - 0.06, 0.04, 0.0125), (0.12, 0.12, 0.025), "#b03028", "metal")]
    if kind == "tireiron": return [rod_x(-L / 2, L / 2, 0.022, DARKMETAL, "metal"), P("cyl", (L / 2 - 0.01, W * 0.4, 0.011), (0.022, 0.022, W * 0.8), DARKMETAL, "metal", (90, 0, 0))]
    if kind == "axe_long": return T_shaft_head(L, W, H, pal, "axe", 0.038, "#b03028" if iid == "fire_axe" else DARKMETAL)
    if kind == "hatchet": return T_shaft_head(L, W, H, pal, "axe", 0.03, DARKMETAL, grip_len=0.1)
    if kind == "stoneaxe": return T_shaft_head(L, W, H, pal, "stone", 0.03, "#8a8680")
    if kind == "hammer": return T_shaft_head(L, W, H, pal, "hammer", 0.028, DARKMETAL, grip_len=0.12)
    if kind == "sledge": return T_shaft_head(L, W, H, pal, "sledge", 0.04, DARKMETAL)
    if kind == "stonehammer": return T_shaft_head(L, W, H, pal, "stone", 0.03, "#7a7670")
    if kind == "shovel": return T_shovel(L, W, H, pal)
    if kind == "fshovel": return T_shovel(L, W, H, pal, small=True)
    if kind == "spear_wood": return T_spear(L, W, H, pal, tip_col="#8a8680", shaft_col=WOOD)
    if kind == "spear_metal": return T_spear(L, W, H, pal, tip_col=METAL, shaft_col="#7a7f84")
    if kind == "knife": return T_blade(L, W, H, pal, 0.62, "#2a2420")
    if kind == "knife_hunt": return T_blade(L, W, H, pal, 0.55, "#5a3a24", guard=True)
    if kind == "machete": return T_blade(L, W, H, pal, 0.75, "#2a2420")
    if kind == "cleaver": return T_blade(L, W, H, pal, 0.6, "#2a2420")
    if kind == "knife_stone": return [P("wedge", (L * 0.15, 0, H / 2), (W, L * 0.7, H), "#7a7670", "stone", (0, 0, -90)), rod_x(-L / 2, -L * 0.15, W * 0.55, "#8a6a44", "wood", z=H / 2)]
    if kind == "shiv": return [P("cyl", (L * 0.15, 0, H / 2), (W, W, L * 0.7), BONE, "organic", (0, 90, 0), t=0.05), P("sph", (-L * 0.38, 0, H / 2), (L * 0.25, W * 1.3, H * 1.3), BONE, "organic")]
    if kind == "boneclub": return [rod_x(-L / 2, L * 0.3, W * 0.5, BONE, "organic"), P("sph", (L * 0.38, 0, W / 2), (L * 0.28, W, W), BONE, "organic"), rod_x(-L / 2, -L * 0.25, W * 0.6, "#5a4028", "cloth")]
    if kind == "pan": return T_pan(L, W, H, pal)
    if kind in ("pistol", "revolver", "rifle", "shotgun"): return T_gun(L, W, H, pal, kind)
    if kind == "wrench": return T_flat_tool(L, W, H, ["#b03028" if iid == "pipe_wrench" else METAL])
    if kind == "screwdriver": return T_small_tool(L, W, H, [pal[0] if pal[0] != "#888888" else "#c0392b"])
    if kind in ("saw", "hacksaw"): return T_saw(L, W, H, pal) if kind == "saw" else [P("box", (0, 0, 0.003), (L * 0.8, 0.012, 0.004), "#c8ced2", "metal"), P("box", (0, W * 0.4, 0.008), (L * 0.8, 0.012, 0.012), "#e0b030", "metal"), P("box", (-L * 0.42, W * 0.2, 0.008), (0.03, W * 0.6, 0.012), "#e0b030", "metal")]
    if kind in ("pliers", "pliers_small"): return T_pliers(L, W, H, pal)
    if kind == "trowel": return [P("wedge", (L * 0.18, 0, 0.004), (W, L * 0.6, 0.006), METAL, "metal", (0, 0, -90)), rod_x(-L / 2, -L * 0.1, 0.03, "#8a6a44", "wood", z=0.02)]
    if kind == "rod": return [rod_x(-L / 2, L / 2, 0.012, "#3a3a3a", "plastic", t=0.3), P("cyl", (-L * 0.3, 0.02, 0.025), (0.05, 0.05, 0.04), METAL, "metal", (90, 0, 0))]
    if kind == "pocketknife": return [P("box", (0, 0, H / 2), (L, W, H), "#c0392b" if iid == "pocket_knife" else METAL, "metal")]
    if kind in ("handle", "branch"): return [rod_x(-L / 2, L / 2, max(W, H), "#8a6a44" if kind == "handle" else "#6a4a30", "wood", t=0.8)]
    if kind == "log": return T_log(L, W, H, pal)
    if kind == "plank": return T_plank(L, W, H, pal)
    if kind == "bone": return T_bone(L, W, H, pal)
    if kind == "pencil": return [rod_x(-L / 2, L / 2, max(W, H), "#e0b030", "wood")]
    if kind == "tweezers": return [P("box", (0, -0.004, 0.002), (L, 0.004, 0.002), METAL, "metal", (0, 0, 3)), P("box", (0, 0.004, 0.002), (L, 0.004, 0.002), METAL, "metal", (0, 0, -3))]
    if kind == "multitool": return T_pliers(L, W, H, ["#5a5d60"])
    if kind == "nails":
        out = []
        for k in range(7):
            a = k * 0.9
            cx, cy = math.cos(a) * L * 0.25 * (k % 3) / 2, math.sin(a) * W * 0.25 * (k % 3) / 2
            out.append(P("cyl", (cx, cy, 0.003 + (k % 2) * 0.004), (0.004, 0.004, 0.06 if iid == "nails" else 0.035), METAL, "metal", (0, 90, math.degrees(a) * 1.7)))
            out.append(P("cyl", (cx - math.cos(math.radians(math.degrees(a) * 1.7)) * 0.03, cy - math.sin(math.radians(math.degrees(a) * 1.7)) * 0.03, 0.004 + (k % 2) * 0.004), (0.01, 0.01, 0.002), METAL, "metal", (0, 90, math.degrees(a) * 1.7)))
        return out
    if kind == "tyre": return T_tyre(L, W, H, pal)
    if kind == "cardoor": return T_door(L, W, H, pal)
    if kind == "windscreen": return T_glass_panel(L, W, H, pal, "#1a1a1a")
    if kind == "glasspane": return T_glass_panel(L, W, H, pal)
    if kind == "radiator": return [P("box", (0, 0, H / 2), (L, W, H), "#7a7f84", "metal"), P("box", (0, -W * 0.51, H / 2), (L * 0.9, 0.004, H * 0.8), "#4a4d50", "metal")]
    if kind == "motorpart": return [P("cyl", (0, 0, H / 2), (W, H, L), "#7a7f84", "metal", (0, 90, 0)), P("cyl", (L * 0.42, 0, H / 2), (W * 0.5, H * 0.5, L * 0.16), DARKMETAL, "metal", (0, 90, 0))]
    if kind == "sparkplug": return [rod_x(-L / 2, L * 0.1, W, "#e8e8e0", "plastic"), rod_x(L * 0.1, L / 2, W * 0.7, METAL, "metal", z=W / 2)]
    if kind == "belt": return [P("tor", (0, 0, 0.01), (L, W * 2, 0.012), "#1a1a1a", "rubber")]
    if kind == "filter": return T_cylinder_upright(L, W, H, [pal[0] if pal[0] != "#888888" else "#e07a28"], "metal", top=DARKMETAL)
    if kind == "bulb": return [rod_x(-L / 2, 0, W * 0.6, METAL, "metal"), P("sph", (L * 0.2, 0, W / 2), (L * 0.6, W, W), "#f0f0e0", "glass")]
    if kind == "muffler": return [P("cap", (0, 0, H / 2), (W, H, L * 0.7), "#8a7a6a", "metal", (0, 90, 0)), rod_x(-L / 2, -L * 0.3, 0.05, "#7a6a5a", "metal", z=H / 2), rod_x(L * 0.3, L / 2, 0.05, "#7a6a5a", "metal", z=H / 2)]
    if kind == "battery": return T_battery(L, W, H, pal)
    if kind == "generator": return [P("box", (0, 0, H * 0.4), (L, W, H * 0.8), "#c0392b", "metal"), P("cyl", (0, 0, H * 0.9), (W * 0.5, W * 0.5, H * 0.2), DARKMETAL, "metal")]
    if kind == "gascan": return T_gascan(L, W, H, [pal[0] if pal[0] != "#888888" else "#c0392b"])
    if kind == "extinguisher": return T_extinguisher(L, W, H, pal)
    if kind == "jug": return T_jug(L, W, H, pal)
    if kind == "waterjug": return T_jug(L, W, H, ["#2a62b8", "#2a2a2a", "#2a2a2a"])
    if kind == "canteen": return [P("box", (0, 0, H * 0.45), (L, W, H * 0.9), pal[0], "metal"), P("cyl", (0, 0, H * 0.95), (W * 0.5, W * 0.5, H * 0.12), DARKMETAL, "metal")]
    if kind == "bucket": return T_bucket(L, W, H, pal)
    if kind == "wateringcan": return [P("cyl", (0, 0, H * 0.4), (W * 1.2, W * 1.2, H * 0.8), pal[0], "metal"), rod_x(W * 0.5, L / 2, 0.025, pal[0], "metal", z=H * 0.6), P("tor", (-W * 0.1, 0, H * 0.82), (W * 0.9, W * 0.9, 0.01), pal[0], "metal", (90, 0, 0))]
    if kind == "pot": return T_pot(L, W, H, pal, "metal" if iid == "cooking_pot" else "organic", handles=iid == "cooking_pot")
    if kind == "potfull": return T_pot(L, W, H, [DARKMETAL]) + [P("cyl", (0, 0, H * 0.9), (max(L, W) * 0.86, max(L, W) * 0.86, H * 0.04), pal[0] if pal[0] != "#55585a" else pal[1], "organic")]
    if kind == "bottle_glass": return T_bottle(L, W, H, [pal[0], pal[1], pal[2]], glass=True)
    if kind == "bottle": return T_bottle(L, W, H, pal)
    if kind == "sodacan": return T_can(L, W, H, [pal[0], pal[0], pal[1]])
    if kind == "tin_flat": return T_can(L, W, H, pal, flat=True)
    if kind == "can": return T_can(L, W, H, pal)
    if kind == "jar": return T_jar(L, W, H, pal)
    if kind == "pills": return T_jar(L, W, H, [ "#e09030", "#f2f2f0", "#f2f2f0"])
    if kind == "fruit": return T_round(L, W, H, pal, stem=iid in ("apple", "pepper", "tomato"), leaf=iid == "apple")
    if kind == "veg_big": return T_round(L, W, H, pal, stem=iid == "pumpkin")
    if kind == "carrot": return T_carrot(L, W, H, pal)
    if kind == "banana": return T_banana(L, W, H, ["#e8c840"])
    if kind == "cluster": return T_cluster(L, W, H, pal)
    if kind == "longfood": return T_capsule(L, W, H, pal) if iid not in ("hot_dog", "corn_dog") else T_capsule(L, W, H, pal) + [P("cap", (0, 0, H * 0.7), (W * 0.6, W * 0.6, L * 1.05), "#b04030", "organic", (0, 90, 0))]
    if kind == "loaf": return T_loaf(L, W, H, pal)
    if kind == "bagel": return T_torus(L, W, H, pal)
    if kind == "stackfood":
        if iid == "burger": return T_stack(L, W, H, pal, [(0.3, "#c89050", "cyl"), (0.25, "#6a3a20", "cyl"), (0.1, "#5a9a3a", "cyl"), (0.35, "#c89050", "sph")])
        if iid == "cake": return T_stack(L, W, H, pal, [(0.8, pal[0], "cyl"), (0.2, "#f0e8e0", "cyl")])
        return [P("cyl", (0, 0, H / 2), (L, W, H), pal[0], "organic")] if iid != "cheese" else [P("wedge", (0, 0, H / 2), (L, W, H), "#e8c040", "organic", (0, 0, 90))]
    if kind == "sandwich": return T_stack(L, W, H, pal, [(0.3, "#d8b080", "box"), (0.15, "#5a9a3a", "box"), (0.2, "#c87060", "box"), (0.35, "#d8b080", "box")])
    if kind == "meat": return T_slab(L, W, H, pal)
    if kind == "pack": return T_box(L, W, H, pal)
    if kind == "carton": return T_box(L, W, H, pal) + [P("wedge", (0, 0, H + W * 0.2), (L, W, W * 0.4), pal[0], "paper", (0, 0, 90))]
    if kind == "bar": return T_box(L, W, H, pal, band=True)
    if kind == "icecream": return T_box(L, W, H, ["#f0ece0", "#c89050"], "paper")
    if kind == "seedpacket": return [P("box", (0, 0, 0.003), (H, L, 0.005), pal[0], "paper")]
    if kind == "bundle": return [rod_x(-L / 2, L / 2, W * 0.3, pal[0], "organic", y=W * (i - 1) * 0.25, z=W * 0.15 + (i % 2) * 0.01) for i in range(3)]
    if kind == "boots": return T_boots(L, W, H, pal, "rubber" if iid == "rubber_boots" else "cloth")
    if kind == "gloves": return T_gloves(L, W, H, pal if iid != "chainmail_glove" else [METAL])
    if kind == "cap": return T_hat(L, W, H, pal, peak=0.55)
    if kind == "helmet": return T_hat(L, W, H, pal, brim=0.12 if iid == "hard_hat" else 0.0, hard=True)
    if kind == "softhat": return T_hat(L, W, H, pal, brim=0.25 if iid == "bucket_hat" else 0.0)
    if kind == "cowboyhat": return T_hat(L * 0.55, W * 0.6, H, pal) + [P("cyl", (0, 0, 0.005), (L, W, 0.01), pal[0], "cloth")]
    if kind == "mask": return T_mask(L, W, H, pal, "organic" if iid == "bone_mask" else "cloth")
    if kind == "goggles": return T_goggles(L, W, H, pal)
    if kind == "armorpiece": return T_armor_piece(L, W, H, [pal[0], pal[1]], "metal" if "scrap" in iid or "chain" in iid or "riot" in iid else ("organic" if "bone" in iid else "cloth"))
    if kind == "vest_hard": return T_cloth(L, W, H, pal)
    if kind == "backpack": return T_bag(L, W, H, pal)
    if kind == "duffel": return T_duffel(L, W, H, pal)
    if kind == "satchel": return T_bag(L, W, H, pal)
    if kind == "book": return T_book(L, W, H, pal)
    if kind == "comic": return T_paper(L, W, H, pal)
    if kind == "paper": return T_paper(L, W, H, [PAPER if iid not in ("family_photo", "local_map") else pal[0], pal[1]])
    if kind == "box_small": return T_box(L, W, H, pal, "paper")
    if kind == "kitbox": return T_box(L, W, H, ["#c0392b", "#f2f2f0"], "plastic")
    if kind == "coil": return T_coil(L, W, H, pal, "plastic" if iid == "duct_tape" else "cloth")
    if kind == "sheet": return T_sheet(L, W, H, pal, "plastic" if iid in ("plastic_sheet", "garbage_bag", "tarp") else "cloth")
    if kind == "scrap": return [P("box", (0, 0, 0.01), (L, W, 0.008), "#7a7f84", "metal", (4, 0, 8)), P("box", (L * 0.1, W * 0.1, 0.025), (L * 0.6, W * 0.5, 0.006), "#8a6a5a", "metal", (-6, 3, -20))]
    if kind == "stone": return T_stone(L, W, H, pal) if iid != "clay" else T_lump(L, W, H, ["#9a7a5a"])
    if kind == "lantern": return T_lantern(L, W, H, pal) if iid == "lantern" else [rod_x(-L / 2, L / 2, max(W, H), pal[0], "metal", t=1.3)]
    if kind == "radio": return T_radio(L, W, H, pal) if iid != "alarm_clock" else [P("cyl", (0, 0, H / 2), (L, W * 0.6, H), pal[0], "metal", (90, 0, 0))]
    if kind == "binoculars": return T_binoculars(L, W, H, pal)
    if kind == "compass": return [P("cyl", (0, 0, H / 2), (L, W, H), "#5a3a24", "metal"), P("cyl", (0, 0, H), (L * 0.85, W * 0.85, 0.002), "#f0ece0", "paper")]
    if kind == "candle": return T_candle(L, W, H, pal)
    if kind == "money": return T_money(L, W, H, pal)
    if kind == "toy": return T_toy(L, W, H, pal)
    if kind == "pillow": return T_pillow(L, W, H, pal)
    if kind == "bandage": return T_cylinder_upright(L, W, H, ["#f0ece0"], "cloth") if iid == "bandage" else [rod_x(-L / 2, L / 2, 0.02, WOOD, "wood", y=0.025), rod_x(-L / 2, L / 2, 0.02, WOOD, "wood", y=-0.025), P("box", (0, 0, 0.012), (0.08, W, 0.025), "#e8e0d0", "cloth")]
    if kind == "small": return T_generic(L, W, H, pal, "metal")
    if kind == "animal_big": return T_animal(L, W, H, pal, tail=0.12)
    if kind == "animal_small": return T_animal(L, W, H, pal, tail=0.05)
    if kind == "snake": return [rod_x(-L / 2 + i * L / 6, -L / 2 + (i + 1) * L / 6, W, pal[0], "organic", y=math.sin(i * 1.4) * W * 1.5) for i in range(6)]
    if kind == "bird": return T_bird(L, W, H, pal)
    if kind in ("cloth_torso", "cloth_legs"): return T_cloth(L, W, H, pal)
    return T_generic(L, W, H, pal)


def grip_of(kind, L, W, H):
    """where the hand holds a long thing (model coordinates)"""
    if kind in ("pistol", "revolver"): return [-L * 0.34, -H * 0.2, W * 0.5]
    if kind in ("rifle", "shotgun"): return [-L * 0.12, -H * 0.1, W * 0.5]
    if kind in ("spear_wood", "spear_metal"): return [-L * 0.1, 0, max(W, H) / 2]
    if kind in ("knife", "knife_hunt", "machete", "cleaver", "knife_stone", "shiv"): return [-L * 0.36, 0, H / 2]
    if kind == "pan": return [-L * 0.38, 0, H * 0.7]
    return [-L * 0.4, 0, max(W, H) / 2]


# ------------------------------------------------------------------ world props (upright, in the world)
PROPS = {
    "barrel": ((0.58, 0.58, 0.88), T_barrel), "cardboard_boxes": ((0.6, 0.5, 0.7), T_boxes), "ammo_crate": ((0.75, 0.45, 0.42), T_crate),
    "tyre_pile": ((0.9, 0.7, 0.62), T_tyre_pile), "traffic_cone": ((0.36, 0.36, 0.7), T_cone_upright), "cooler": ((0.6, 0.38, 0.42), T_cooler), "coffin": ((2.0, 0.6, 0.55), T_coffin),
}

# items whose inventory icon is cut from the reference sheets (the rest are rendered from their model)
SHEET_ICONS = set(json.load(open(os.path.join(root, "data/icon_map.json"))).keys()) | {k for k in json.load(open(os.path.join(root, "data/icon_map_grid.json")))["icons"] if "__" not in k}
out = {"scale": {"px_per_m": 30.37, "vertical_px_per_m": 26.3, "tile_m": 1.49, "note": "orthographic camera, azimuth 45 deg, elevation 30 deg"}, "items": {}, "props": {}}
for iid, it in sorted(ITEMS.items()):
    kind = kind_of(iid, it)
    (L, W, H), src_id = dims_for(iid, kind)
    pal = palette(iid)
    parts = build(iid, kind, L, W, H, pal)
    spec = {"kind": kind, "dims": [round(L, 4), round(W, 4), round(H, 4)], "source": src_id, "parts": parts}
    if kind in HELD:
        spec["grip"] = [round(v, 4) for v in grip_of(kind, L, W, H)]
        spec["held"] = True
    if iid not in SHEET_ICONS or iid in ("kitchen_knife", "hunting_knife"):
        spec["icon"] = True      # no usable sheet icon: the inventory icon is rendered from the model too
    out["items"][iid] = spec
for name, (dims, fn) in PROPS.items():
    L, W, H = dims
    out["props"][name] = {"dims": list(dims), "parts": fn(L, W, H, ["#888888", "#aaaaaa", "#555555"])}
json.dump(out, open(os.path.join(root, "data/model_specs.json"), "w"), indent=None, separators=(",", ":"))
kinds = {}
for v in out["items"].values():
    kinds[v["kind"]] = kinds.get(v["kind"], 0) + 1
print("items:", len(out["items"]), "props:", len(out["props"]), "from catalog sizes:", sum(1 for v in out["items"].values() if v["source"].startswith("PZWIKI")),
      "generic:", kinds.get("generic", 0), "icons to render:", sum(1 for v in out["items"].values() if v.get("icon")))
print(sorted(i for i, v in out["items"].items() if v["kind"] == "generic"))
