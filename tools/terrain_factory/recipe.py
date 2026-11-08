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


def segment_distance(u, v, a, b):
    """Distance to a short natural surface fracture (not a traced image)."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    t = clamp(((u - a[0]) * dx + (v - a[1]) * dy) / (dx * dx + dy * dy))
    return math.hypot(u - a[0] - t * dx, v - a[1] - t * dy)


def surface_rgb(surface, u, v, variant=0):
    """Original periodic material patterns, with interior-only controlled variation."""
    kind = surface["material"]
    broad = periodic_noise(u, v, 2, 47)
    mid = periodic_noise(u, v, 7, 83)
    micro = periodic_noise(u, v, 18, 133)
    # Seed-dependent patches vanish at cell borders; shared outer pigment remains
    # phase-aligned across arbitrary neighbours (no visible per-tile border line).
    interior = window(u, v) * (
        .20 * periodic_noise(u, v, 4, (variant % 997) + 101) +
        .065 * periodic_noise(u, v, 11, (variant % 919) + 307))
    intensity = broad * .077 + mid * .034 + micro * .016 + interior
    tint = (0.0, 0.0, 0.0)
    if kind == "ground_grass":
        # Masses of sparse low ground-cover with occasional dry/thin patches.
        tufts = periodic_noise(u, v, 12, 233)
        dry = smoothstep(.14, .64, periodic_noise(u, v, 3, 411))
        intensity += .095 * tufts + .034 * periodic_noise(u, v, 23, 238)
        tint = (.030 * dry, -.018 * dry, -.013 * dry)
    elif kind == "asphalt":
        # Fine embedded aggregate and a limited, discontinuous original crack.
        intensity += .068 * periodic_noise(u, v, 19, 448)
        offset = .08 * math.sin((variant % 63) * .103)
        fracture = min(
            segment_distance(u, v, (.17, .26 + offset), (.48, .40 + offset)),
            segment_distance(u, v, (.48, .40 + offset), (.75, .49 + offset)))
        intensity -= .19 * window(u, v) * (1 - smoothstep(.015, .055, fracture))
    elif kind == "pavers":
        seam = min(abs(math.sin(math.pi * 4 * u)), abs(math.sin(math.pi * 4 * v)))
        intensity -= .21 * (1 - smoothstep(.03, .135, seam))
        intensity += .040 * periodic_noise(u, v, 8, 719)
    elif kind == "earth":
        intensity += .125 * periodic_noise(u, v, 5, 437)
        intensity -= .042 * smoothstep(.23, .62, periodic_noise(u, v, 12, 709))
    elif kind == "gravel":
        intensity += .17 * periodic_noise(u, v, 18, 567)
        tint = (.018 * periodic_noise(u, v, 13, 682), 0, -.008 * micro)
    elif kind == "timber_floor":
        seam = abs(math.sin(math.pi * 4 * v))
        intensity -= .24 * (1 - smoothstep(.035, .145, seam))
        intensity += .085 * periodic_noise(u, v, 7, 773)
        knot = math.exp(-((u-.64)/.075)**2 - ((v-.39)/.035)**2)
        intensity -= .14 * window(u, v) * knot
    elif kind == "ceramic_floor":
        seam = min(abs(math.sin(math.pi * 3 * u)), abs(math.sin(math.pi * 3 * v)))
        intensity -= .21 * (1 - smoothstep(.035, .125, seam))
        intensity += .019 * periodic_noise(u, v, 6, 981)
    elif kind == "concrete_floor":
        stain = smoothstep(.05, .6, periodic_noise(u, v, 3, 998))
        intensity -= .21 * stain
        intensity += .027 * periodic_noise(u, v, 16, 999)
    else:
        raise ValueError("unknown material type: " + kind)
    return tuple(clamp(c * (1 + intensity) + tint[i])
                 for i, c in enumerate(hex_rgb(surface["base_hex"])))


def color(job, surfaces, u, v, variant=0):
    a = surface_rgb(surfaces[job["a"]], u, v, variant)
    if job["b"] is None:
        return a
    b = surface_rgb(surfaces[job["b"]], u, v, variant)
    t = coverage(job["mask"], u, v)
    return tuple(a[i] * (1 - t) + b[i] * t for i in range(3))


RELIEF_AMPLITUDE_M = {
    "ground_grass": .0022, "earth": .0017, "gravel": .0030,
    "asphalt": .0007, "pavers": .0011, "timber_floor": .00035,
    "ceramic_floor": .0002, "concrete_floor": .00075,
}


def height(u, v, variant=0, amplitude_m=.002):
    # Non-directional, bounded sub-centimetre 3D relief with ZERO edge slopes.
    # Replaces the old aligned 5/8-cycle waves that striped every material.
    return amplitude_m * window(u, v) * (
        .76 * periodic_noise(u, v, 5, 751) +
        .34 * periodic_noise(u, v, 11, (variant % 299) + 43))


def recipe_sha():
    return hashlib.sha256(RECIPE_PATH.read_bytes()).hexdigest()
