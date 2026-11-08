"""Terrain families, biome rules and seam/adjacency contracts (W04-F).

Terrain is chosen by land use, elevation and moisture rather than random
scatter. Art for each family is supplied by the terrain asset worker; this
module only decides spatial selection, adjacency and transitions.
"""
from __future__ import annotations

from .core import derive_seed

# Single-character codes keep chunk rows compact and diff-friendly.
CODES = {"grass": "g", "asphalt": "a", "sidewalk": "s", "driveway": "d", "path": "p", "gravel": "r",
         "dirt": "t", "field": "f", "forest": "o", "water": "w", "floor": "b", "concrete": "c"}
FROM_CODE = {v: k for k, v in CODES.items()}
WALKABLE = set(CODES) - {"water"}
FAMILY = {"grass": "soft", "dirt": "soft", "field": "soft", "forest": "soft", "water": "water",
          "asphalt": "hard", "sidewalk": "hard", "driveway": "hard", "path": "hard", "gravel": "hard",
          "concrete": "hard", "floor": "structure"}
# Water must be banked by soft ground; structures never sit directly on water.
FORBIDDEN_ADJACENT = {frozenset({"water", "asphalt"}), frozenset({"water", "sidewalk"}), frozenset({"water", "driveway"}),
                      frozenset({"water", "floor"}), frozenset({"water", "gravel"}), frozenset({"water", "path"}),
                      frozenset({"water", "concrete"})}


def lattice(seed, x, y):
    return (derive_seed(seed, "lattice", x, y) % 10007) / 10006.0


def value_noise(seed, x, y, scale):
    gx, gy = x / scale, y / scale
    x0, y0 = int(gx // 1), int(gy // 1)
    tx, ty = gx - x0, gy - y0
    sx, sy = tx * tx * (3 - 2 * tx), ty * ty * (3 - 2 * ty)
    a, b = lattice(seed, x0, y0), lattice(seed, x0 + 1, y0)
    c, d = lattice(seed, x0, y0 + 1), lattice(seed, x0 + 1, y0 + 1)
    return (a + (b - a) * sx) + ((c + (d - c) * sx) - (a + (b - a) * sx)) * sy


def fbm(seed, x, y, scale, octaves=3):
    total, amp, norm = 0.0, 1.0, 0.0
    for o in range(octaves):
        total += value_noise(seed + o * 7919, x, y, scale / (2 ** o)) * amp
        norm += amp
        amp *= 0.5
    return total / norm


def edge_biome(kind, seed, x, y):
    """Land cover for district margins following elevation/moisture constraints."""
    elev = fbm(seed, x, y, 18.0)
    moist = fbm(seed + 101, x, y, 14.0)
    if kind == "parkland":
        return "forest" if moist > 0.66 else "grass"
    if kind == "urban_lot":
        return "dirt" if moist > 0.62 else "gravel" if elev > 0.7 else "grass"
    if kind == "farm_forest":
        if elev < 0.30 and moist > 0.45:
            return "water"
        if moist > 0.60 or elev > 0.72:
            return "forest"
        return "field" if elev < 0.58 else "grass"
    return "grass"


def bank_water(grid):
    """Replace water touching forbidden neighbours with soft dirt banks (repeat to fixpoint)."""
    changed = True
    while changed:
        changed = False
        for (x, y), t in list(grid.items()):
            if t != "water":
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                n = grid.get((x + dx, y + dy))
                if n and frozenset({t, n}) in FORBIDDEN_ADJACENT:
                    grid[(x, y)] = "dirt"
                    changed = True
                    break


def transition_mask(grid, x, y):
    """4-bit N,E,S,W mask of neighbours in a different terrain family (renderer transition key)."""
    t = grid.get((x, y))
    mask = 0
    for bit, (dx, dy) in enumerate(((0, -1), (1, 0), (0, 1), (-1, 0))):
        n = grid.get((x + dx, y + dy))
        if n is not None and FAMILY[n] != FAMILY[t]:
            mask |= 1 << bit
    return mask


def adjacency_errors(grid):
    out = []
    for (x, y), t in grid.items():
        for dx, dy in ((1, 0), (0, 1)):
            n = grid.get((x + dx, y + dy))
            if n and frozenset({t, n}) in FORBIDDEN_ADJACENT:
                out.append(f"{t}/{n} at {(x, y)}")
    return out
