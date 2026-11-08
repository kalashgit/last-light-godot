"""Pure-Python terrain compiler shared by Blender and regression tests.

For a blend, mask bits describe the four *corner material identities* in
NW, NE, SE, SW order. Adjacent cells that share corner identities share
their edge coverage, color phase, and zero-height boundary exactly.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

RECIPE_PATH = Path(__file__).with_name("recipes.json")
TAU = 2.0 * math.pi


def catalog():
    return json.loads(RECIPE_PATH.read_text(encoding="utf-8"))


def asset_id(a, b=None, mask=None):
    if b is None:
        return f"ll_tile_{a}"
    return f"ll_tile_{a}_to_{b}_c{mask:02d}"


def plan():
    recipes = catalog()
    names = {s["id"] for s in recipes["surfaces"]}
    jobs = [{"asset_id": asset_id(s["id"]), "a": s["id"], "b": None,
             "mask": 0, "kind": "center"} for s in recipes["surfaces"]]
    aliases = {}
    for a, b in recipes["transitions"]:
        if a not in names or b not in names or a == b:
            raise ValueError("unregistered or identical transition surface")
        # 0 and 15 are already represented by the base A/B surface tile.
        aliases[asset_id(a, b, 0)] = asset_id(a)
        aliases[asset_id(a, b, 15)] = asset_id(b)
        for mask in range(1, 15):
            jobs.append({"asset_id": asset_id(a, b, mask), "a": a,
                         "b": b, "mask": mask, "kind": "corner_transition"})
    ids = [x["asset_id"] for x in jobs]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate terrain tile IDs")
    return {"schema": 1, "jobs": jobs, "aliases": aliases,
            "count": len(jobs), "surface_count": len(names),
            "transition_count": len(recipes["transitions"]),
            "rights": recipes["rights"]}


def clamp(x):
    return max(0.0, min(1.0, x))


def smoothstep(a, b, x):
    t = clamp((x - a) / (b - a))
    return t * t * (3.0 - 2.0 * t)


def stable_seed(identity):
    return int.from_bytes(hashlib.sha256(identity.encode()).digest()[:4], "big")


def window(u, v):
    # Both value and slope vanish on tile boundaries.
    return math.sin(math.pi * u) ** 2 * math.sin(math.pi * v) ** 2


def phase(u, v, frequency=1):
    # Exactly periodic over one tile; independent of job seed.
    return math.sin(TAU * frequency * u) * math.cos(TAU * frequency * v)


def periodic_noise(u, v, period, seed):
    """2D smooth tileable value noise; avoids screen-direction moire stripes."""
    x, y = u * period, v * period
    ix, iy = math.floor(x), math.floor(y)
    fx, fy = smoothstep(0, 1, x - ix), smoothstep(0, 1, y - iy)

    def corner(a, b):
        z = ((a % period) * 374761393 + (b % period) * 668265263 +
             seed * 2246822519) & 0xFFFFFFFF
        z = ((z ^ (z >> 13)) * 1274126177) & 0xFFFFFFFF
        return ((z ^ (z >> 16)) & 0xFFFF) / 32767.5 - 1.0

    a = corner(ix, iy) * (1 - fx) + corner(ix + 1, iy) * fx
    b = corner(ix, iy + 1) * (1 - fx) + corner(ix + 1, iy + 1) * fx
    return a * (1 - fy) + b * fy


def coverage(mask, u, v):
    """B material fraction, with boundary determined ONLY by two shared bits."""
    nw, ne, se, sw = ((mask >> i) & 1 for i in range(4))
    top = nw * (1.0 - u) + ne * u
    bottom = sw * (1.0 - u) + se * u
    bilinear = top * (1.0 - v) + bottom * v
    # Displace the boundary inside the cell without modifying any shared edge.
    wobble = 0.085 * window(u, v) * (
        math.sin(TAU * (2 * u + v)) + .48 * math.sin(TAU * (u - 3 * v)))
    return smoothstep(.43, .57, bilinear + wobble)


def hex_rgb(value):
    return tuple(int(value[i:i + 2], 16) / 255.0 for i in (1, 3, 5))


def surface_rgb(surface, u, v, variant=0):
    """Original periodic material patterns, with interior-only controlled variation."""
    kind = surface["material"]
    broad = periodic_noise(u, v, 2, 47)
    mid = periodic_noise(u, v, 7, 83)
    micro = periodic_noise(u, v, 18, 133)
    interior = window(u, v) * .11 * math.sin(
        TAU * (u * 7 + v * 9) + (variant % 113) * .29)
    intensity = broad * .090 + mid * .038 + micro * .024 + interior
    if kind == "ground_grass":
        # Distinct patches and grouped fine cover, not a copy-pasted grass comb.
        blades = periodic_noise(u, v, 12, 233)
        intensity += .095 * blades + .045 * periodic_noise(u, v, 22, 238)
    elif kind == "asphalt":
        intensity += .042 * periodic_noise(u, v, 19, 448)
        fracture = abs(math.sin(TAU * (2*u + .17*math.sin(TAU*v))))
        intensity -= .075 * (1 - smoothstep(.015, .085, fracture))
    elif kind == "pavers":
        seam = min(abs(math.sin(math.pi * 4 * u)), abs(math.sin(math.pi * 4 * v)))
        intensity -= .23 * (1 - smoothstep(.03, .135, seam))
    elif kind == "earth":
        intensity += .10 * periodic_noise(u, v, 5, 437)
    elif kind == "gravel":
        intensity += .14 * periodic_noise(u, v, 20, 567)
    elif kind == "timber_floor":
        seam = abs(math.sin(math.pi * 4 * v))
        intensity -= .27 * (1 - smoothstep(.035, .145, seam))
        intensity += .095 * periodic_noise(u, v, 7, 773)
    elif kind == "ceramic_floor":
        seam = min(abs(math.sin(math.pi * 3 * u)), abs(math.sin(math.pi * 3 * v)))
        intensity -= .19 * (1 - smoothstep(.03, .125, seam))
    elif kind == "concrete_floor":
        intensity += .12 * periodic_noise(u, v, 3, 998)
    else:
        raise ValueError("unknown material type: " + kind)
    return tuple(clamp(c * (1 + intensity)) for c in hex_rgb(surface["base_hex"]))


def color(job, surfaces, u, v, variant=0):
    a = surface_rgb(surfaces[job["a"]], u, v, variant)
    if job["b"] is None:
        return a
    b = surface_rgb(surfaces[job["b"]], u, v, variant)
    t = coverage(job["mask"], u, v)
    return tuple(a[i] * (1 - t) + b[i] * t for i in range(3))


def height(u, v, variant=0):
    # Millimetre-scale ground relief; exact zero and flat normals at seams.
    return .004 * window(u, v) * (
        .65 * phase(u, v, 5) + .35 * math.sin(TAU * (u * 8 + v * 6) + variant * .01))


def recipe_sha():
    return hashlib.sha256(RECIPE_PATH.read_bytes()).hexdigest()
