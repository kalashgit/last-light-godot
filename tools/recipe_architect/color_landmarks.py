"""Opt-in CPU pixel inspection for distinctive, color-identified components.

This is *not* a semantic vision model. It matches an already identified recipe
material to an isolated, color-distinct source region and refuses ambiguous
cases. No filename-only observation, network request, or invented hidden part.
"""
from __future__ import annotations

import colorsys
import math
from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image

from .contract import sha256
from .visual_qa import fitted_point, normalized


def material_hsv(m: dict) -> tuple[float, float, float]:
    return colorsys.rgb_to_hsv(*m["rgba"][:3])


def approximate_volume(component: dict) -> float:
    """Conservative family-free estimate for choosing one dominant material part."""
    g, op = component["geometry"], component["op"]
    if op == "box":
        return math.prod(g["size"])
    if op == "cylinder":
        return math.pi * g["radius"] ** 2 * g["depth"] * math.prod(g.get("scale_xy", [1, 1]))
    if op == "tube":
        return math.pi * g["radius"] ** 2 * sum(
            math.dist(a, b) for a, b in zip(g["points"], g["points"][1:]))
    if op == "lathe":
        return math.pi * max(p[0] for p in g["profile"]) ** 2 * (
            max(p[1] for p in g["profile"]) - min(p[1] for p in g["profile"]))
    if op == "polygon_extrude":
        p = g["points"]
        area = abs(sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(p, p[1:] + p[:1])) / 2)
        return area * g["depth"]
    return 0.


def connected_regions(mask: np.ndarray) -> list[dict]:
    """8-connected components; inspect only pixels that passed alpha/color tests."""
    height, width = mask.shape
    seen = np.zeros_like(mask, dtype=bool)
    groups = []
    for y in range(height):
        for x in range(width):
            if not mask[y, x] or seen[y, x]:
                continue
            pending = deque([(y, x)])
            seen[y, x] = True
            pixels = []
            while pending:
                row, col = pending.popleft()
                pixels.append((row, col))
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        ny, nx = row + dy, col + dx
                        if 0 <= ny < height and 0 <= nx < width and mask[ny, nx] and not seen[ny, nx]:
                            seen[ny, nx] = True
                            pending.append((ny, nx))
            if len(pixels) < 7:
                continue
            ys, xs = zip(*pixels)
            groups.append({"count": len(pixels),
                           "xy": [(sum(xs) / len(xs) + .5) / width,
                                  (sum(ys) / len(ys) + .5) / height],
                           "bbox": [min(xs), min(ys), max(xs) + 1, max(ys) + 1]})
    return groups


def discover(source: Path, recipe: dict, render: Path, projection: dict,
             max_landmarks: int = 2) -> dict:
    """Return a measured provisional landmark report; never silently approve it.

    Requires the exact source SHA and an independently constructed Blender
    projection. Refuses generic colors, multi-part ambiguity and distant blobs.
    """
    if sha256(source) != recipe["identity"]["source_sha256"]:
        raise ValueError("source image changed before landmark inspection")
    if not 0 <= max_landmarks <= 8:
        raise ValueError("invalid landmark budget")
    if projection.get("schema") != "last-light.recipe-projections.v1" or projection.get("heading") != 0:
        raise ValueError("no independent Blender projection evidence")

    with Image.open(source) as original:
        image = normalized(original)
    with Image.open(render) as rendered:
        if projection.get("resolution") != rendered.width or rendered.width != rendered.height:
            raise ValueError("render and projection mismatch")
        predicted = {name: fitted_point(p["origin_px"], rendered)
                     for name, p in projection["components"].items()}

    arr = np.asarray(image.convert("HSV"), dtype=np.float32) / 255
    alpha = np.asarray(image.getchannel("A"), dtype=np.uint8) > 96
    mats = {m["name"]: m for m in recipe["materials"]}
    by_material = {}
    for part in recipe["components"]:
        if part["op"] != "boolean_cut" and part["observed"]:
            by_material.setdefault(part["material"], []).append(part)

    accepted, decisions = [], []
    for name, material in mats.items():
        h, s, _ = material_hsv(material)
        if s < .65:
            continue  # gray / off-white / ambiguous real-world material
        other_hues = [material_hsv(other)[0] for other in mats.values()
                      if other["name"] != name and material_hsv(other)[1] >= .55]
        if any(min(abs(h - other), 1 - abs(h - other)) < .085 for other in other_hues):
            decisions.append({"material": name, "status": "skip_nonunique_hue"})
            continue
        parts = sorted(by_material.get(name, []), key=approximate_volume, reverse=True)
        if not parts or parts[0]["name"] not in predicted:
            continue
        if len(parts) > 1 and approximate_volume(parts[0]) < 4 * approximate_volume(parts[1]):
            decisions.append({"material": name, "status": "skip_ambiguous_shared_material"})
            continue
        main = parts[0]
        hue_distance = np.abs(arr[..., 0] - h)
        hue_distance = np.minimum(hue_distance, 1 - hue_distance)
        mask = alpha & (hue_distance <= .085) & (arr[..., 1] >= max(.40, s * .55)) & (arr[..., 2] >= .10)
        blobs = connected_regions(mask)
        near = sorted(((math.dist(blob["xy"], predicted[main["name"]]), blob)
                       for blob in blobs), key=lambda item: item[0])
        if not near or near[0][0] > .19:
            decisions.append({"material": name, "component": main["name"], "status": "skip_no_near_region",
                              "matching_pixels": int(mask.sum())})
            continue
        if len(near) > 1 and near[1][0] < near[0][0] + .035 and near[1][1]["count"] > .65 * near[0][1]["count"]:
            decisions.append({"material": name, "component": main["name"], "status": "skip_ambiguous_color_blobs"})
            continue
        distance, blob = near[0]
        if blob["count"] < 10 or distance > .19:
            continue
        # Heuristic confidence, not a calibrated model probability.
        confidence = round(max(.50, min(.90, .85 - distance * .9)), 3)
        accepted.append({"component": main["name"], "xy": [round(v, 6) for v in blob["xy"]],
                         "confidence": confidence})
        decisions.append({"material": name, "component": main["name"], "status": "provisional_color_match",
                          "blob_pixels": blob["count"], "blob_bbox_normalized128": blob["bbox"],
                          "distance_from_rendered_origin": round(distance, 6),
                          "confidence_is_heuristic": True})
    accepted = sorted(accepted, key=lambda x: -x["confidence"])[:max_landmarks]
    return {"schema": "last-light.color-landmark-candidates.v1", "source_sha256": sha256(source),
            "method": "cpu_hsv_connected_components_with_recipe_material_prior",
            "semantic_model_inference": False, "provisional_only": True,
            "landmarks": accepted, "decisions": decisions}
