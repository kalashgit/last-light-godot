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
    broad = .5 * phase(u, v, 2) + .35 * phase(u + .17, v + .32, 5)
    micro = phase(u + .23, v + .09, 23)
    interior = window(u, v) * .11 * math.sin(
        TAU * (u * 7 + v * 9) + (variant % 113) * .29)
    intensity = broad * .075 + micro * .025 + interior
    if kind == "ground_grass":
        blades = abs(math.sin(TAU * (v * 17 + .13 * phase(u, v, 3))))
        intensity += .10 * (blades - .5) + .05 * phase(u, v, 7)
    elif kind == "asphalt":
        intensity += .028 * phase(u, v, 19) - .026 * abs(phase(u, v, 4))
    elif kind == "pavers":
        seam = min(abs(math.sin(math.pi * 4 * u)), abs(math.sin(math.pi * 4 * v)))
        intensity -= .19 * (1 - smoothstep(.018, .07, seam))
    elif kind == "earth":
        intensity += .06 * phase(u + .15, v, 9)
    elif kind == "gravel":
        intensity += .082 * phase(u + .37, v + .26, 19)
    elif kind == "timber_floor":
        seam = abs(math.sin(math.pi * 7 * v))
        intensity -= .16 * (1 - smoothstep(.016, .065, seam))
        intensity += .06 * phase(u, v, 12)
    elif kind == "ceramic_floor":
        seam = min(abs(math.sin(math.pi * 3 * u)), abs(math.sin(math.pi * 3 * v)))
        intensity -= .14 * (1 - smoothstep(.022, .065, seam))
    elif kind == "concrete_floor":
        intensity += .035 * phase(u, v, 8)
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
