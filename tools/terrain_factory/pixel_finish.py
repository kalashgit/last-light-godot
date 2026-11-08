"""Deterministic, seam-conscious final pixel craft for LAST LIGHT 80x40 tiles.

This is deliberately a small finishing pass on *real Blender rendered pixels*.
It restores local contrast and a few semantic material marks lost to 4x BOX
reduction. It does not paint a replacement sprite or import reference imagery.
"""
from __future__ import annotations

import math

import recipe

W, H = 80, 40

# Grain intensity is modest (in sRGB 8-bit levels) and material-specific.
# Flat clean ceramics stay clean; aggregates are coarser than finished floors.
GRAIN = {
    "ground_grass": (7, 16, 701),
    "asphalt": (5, 20, 702),
    "pavers": (3, 23, 703),
    "earth": (6, 16, 704),
    "gravel": (9, 23, 705),
    "timber_floor": (3, 20, 706),
    "ceramic_floor": (0, 12, 707),
    "concrete_floor": (4, 22, 708),
}


def inside(x, y):
    return abs((x + .5 - 40) / 40) + abs((y + .5 - 20) / 20) < 1


def uv_from_pixel(x, y):
    """Inverse of the fixed Blender 2:1 diamond for the tile mesh axes.

    The camera is located at +world X and -world Y: increasing both X and Y
    moves right in image space, while increasing X moves down and Y moves up.
    """
    sx = (x + .5 - W / 2) / (W / 2)
    sy = (y + .5 - H / 2) / (H / 2)
    return (.5 * (1 + sx + sy), .5 * (1 + sx - sy))


def material_marks(surface, u, v):
    kind = surface["material"]
    amount, scale, seed = GRAIN[kind]
    noise = (.72 * recipe.periodic_noise(u, v, scale, seed) +
             .28 * recipe.periodic_noise(u, v, scale // 2, seed + 47))
    # The deliberately coarse three-step noise clusters pixels rather than
    # creating isolated high-frequency salt-and-pepper speckles.
    marks = amount * (round(noise * 2) / 2)
    if kind in ("pavers", "ceramic_floor", "timber_floor"):
        count = 3 if kind == "ceramic_floor" else 4
        horizontal = abs(math.sin(math.pi * count * v))
        boundary = (horizontal if kind == "timber_floor" else
                    min(horizontal, abs(math.sin(math.pi * count * u))))
        # One-pixel-readable mortar and timber joins, with a narrow shoulder.
        marks -= (17 if kind == "pavers" else 15) * (1 - recipe.smoothstep(.09, .22, boundary))
    elif kind == "asphalt":
        crack = min(recipe.segment_distance(u, v, (.17, .26), (.48, .40)),
                    recipe.segment_distance(u, v, (.48, .40), (.75, .49)))
        marks -= 13 * recipe.window(u, v) * (1 - recipe.smoothstep(.010, .045, crack))
    return marks


def contrast_weight(x, y):
    """Zero at open diamond boundary so sharpening cannot introduce seam halos."""
    depth = (1 - abs((x + .5 - 40) / 40) -
             abs((y + .5 - 20) / 20)) * 20
    return recipe.smoothstep(1.25, 3.25, depth)


def finish_tile(native, job, surfaces):
    """Return an RGBA image with stronger material-aware pixel readability.

    Does not modify the input. Alpha and source silhouette remain unchanged.
    """
    from PIL import Image

    if native.size != (W, H):
        raise ValueError("Expected native 80x40 RGBA tile")
    source = native.convert("RGBA")
    result = source.copy()
    src, dst = source.load(), result.load()
    for y in range(H):
        for x in range(W):
            if not inside(x, y):
                continue
            if src[x, y][3] == 0:
                raise ValueError("Missing alpha at native terrain interior")
            u, v = uv_from_pixel(x, y)
            a = material_marks(surfaces[job["a"]], u, v)
            if job["b"]:
                b = material_marks(surfaces[job["b"]], u, v)
                coverage = recipe.coverage(job["mask"], u, v)
                a = a * (1 - coverage) + b * coverage
            # No inventing of tile-edge shading: marks are periodic, with a
            # guarded fade to prevent boundary discontinuities after rendering.
            weight = contrast_weight(x, y)
            mean = [float(src[x, y][i]) for i in range(3)]
            if weight and all(inside(x + dx, y + dy)
                              for dx in (-1, 0, 1) for dy in (-1, 0, 1)):
                weights = ((1, 2, 1), (2, 4, 2), (1, 2, 1))
                mean = [sum(weights[dy + 1][dx + 1] * src[x + dx, y + dy][i]
                            for dy in (-1, 0, 1) for dx in (-1, 0, 1)) / 16
                        for i in range(3)]
            new_rgb = []
            for i in range(3):
                original = src[x, y][i]
                sharpen = min(15, max(-15, original - mean[i])) * 1.55 * weight
                proposed = original + sharpen + a * weight
                # 6/255-step native palette snapping groups diffuse shading into
                # intentional pixel clusters, never a noisy dither pattern.
                snapped = round(proposed / 6) * 6
                proposed = proposed * (1 - weight) + snapped * weight
                new_rgb.append(max(0, min(255, round(proposed))))
            dst[x, y] = (*new_rgb, 255)
    return result
