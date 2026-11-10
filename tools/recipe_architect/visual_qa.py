"""Source-pixel / rendered-pixel visual measurements and bounded defect reporting.

The score is a measurable proxy, not a semantic/object recognition or Golden gate.
Reference pixels are used for local comparison only, never as game textures.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFont


def normalization_fit(image: Image.Image, size: int = 128):
    im = image.convert("RGBA")
    alpha = im.getchannel("A")
    bounds = alpha.point(lambda a: 255 if a >= 32 else 0).getbbox()
    if not bounds:
        raise ValueError("empty reference or render alpha")
    content = im.crop(bounds)
    scale = (size - 12) / max(content.size)
    target = tuple(max(1, round(v * scale)) for v in content.size)
    return bounds, target, ((size - target[0]) // 2, (size - target[1]) // 2)


def normalized(image: Image.Image, size: int = 128) -> Image.Image:
    im = image.convert("RGBA")
    bounds, target, origin = normalization_fit(im, size)
    content = im.crop(bounds)
    content = content.resize(target, Image.Resampling.LANCZOS)
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    out.alpha_composite(content, origin)
    return out


def fitted_point(point, original: Image.Image, size: int = 128):
    """Map a raw rendered pixel point to the same normalized image as compare()."""
    (left, top, right, bottom), (width, height), (ox, oy) = normalization_fit(original, size)
    return [(point[0] - left) * width / (right - left) / size + ox / size,
            (point[1] - top) * height / (bottom - top) / size + oy / size]


def projected_landmarks(render_image, landmarks: list, projection: dict) -> list:
    if projection.get("schema") != "last-light.recipe-projections.v1" or projection.get("heading") != 0:
        raise ValueError("missing heading-zero geometry projection evidence")
    if projection.get("resolution") != render_image.width or render_image.width != render_image.height:
        raise ValueError("render resolution and geometry projections differ")
    result = []
    for landmark in landmarks:
        name = landmark["component"]
        if name not in projection["components"]:
            raise ValueError("observed component missing from Blender projection: " + name)
        data = projection["components"][name]
        actual = fitted_point(data["origin_px"], render_image)
        xy = landmark["xy"]
        axes = []
        for axis in data["local_xy_axes_px_per_m"]:
            shifted = fitted_point([data["origin_px"][k] + axis[k] for k in range(2)], render_image)
            axes.append([shifted[k] - actual[k] for k in range(2)])
        distance = math.dist(xy, actual)
        result.append({"component": name, "observed_xy": xy,
                       "rendered_xy": [round(v, 6) for v in actual],
                       "delta_xy": [round(xy[k] - actual[k], 6) for k in range(2)],
                       "local_xy_axes": axes, "error": round(distance, 6),
                       "confidence": landmark["confidence"]})
    return result


def binary_mask(im):
    return np.asarray(im.getchannel("A"), dtype=np.uint8) > 96


def edge_mask(mask):
    # Four-neighbor erosion; relative edge overlap is stricter than raw alpha IoU.
    eroded = mask.copy()
    eroded[1:, :] &= mask[:-1, :]
    eroded[:-1, :] &= mask[1:, :]
    eroded[:, 1:] &= mask[:, :-1]
    eroded[:, :-1] &= mask[:, 1:]
    return mask & ~eroded


def compare(source: Path, render: Path, output: Path | None = None,
            landmarks: list | None = None, projection: dict | None = None) -> dict:
    with Image.open(source) as f, Image.open(render) as g:
        ref, gen = normalized(f), normalized(g)
        alignments = projected_landmarks(g, landmarks, projection) if landmarks else []
    a, b = binary_mask(ref), binary_mask(gen)
    overlap = int(np.count_nonzero(a & b))
    union = int(np.count_nonzero(a | b))
    iou = overlap / max(1, union)
    ar_ref = (np.max(np.where(a)[1]) - np.min(np.where(a)[1]) + 1) / (np.max(np.where(a)[0]) - np.min(np.where(a)[0]) + 1)
    ar_gen = (np.max(np.where(b)[1]) - np.min(np.where(b)[1]) + 1) / (np.max(np.where(b)[0]) - np.min(np.where(b)[0]) + 1)
    aspect_error = abs(np.log(ar_ref / ar_gen))
    a_edge, b_edge = edge_mask(a), edge_mask(b)
    # Dilate one pixel to accommodate antialiasing differences.
    from PIL import ImageFilter
    a_ed = np.asarray(Image.fromarray((a_edge * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(3))) > 0
    b_ed = np.asarray(Image.fromarray((b_edge * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(3))) > 0
    edge_f1 = (2 * np.count_nonzero(a_edge & b_ed) / max(1, np.count_nonzero(a_edge) + np.count_nonzero(b_edge)))
    # Brightness/color difference on opaque pixels, separately from silhouette.
    rgb_a = np.asarray(ref.convert("RGB"), dtype=np.float32) / 255
    rgb_b = np.asarray(gen.convert("RGB"), dtype=np.float32) / 255
    median_a = np.median(rgb_a[a], axis=0)
    median_b = np.median(rgb_b[b], axis=0)
    color_error = float(np.mean(np.abs(median_a - median_b)))
    aspect_score = float(np.exp(-aspect_error))
    pixel_score = float(.62 * iou + .20 * aspect_score + .10 * max(0, 1 - color_error) + .08 * min(1, edge_f1))
    landmark_error = (sum(a["error"] * a["confidence"] for a in alignments) /
                      sum(a["confidence"] for a in alignments)) if alignments else None
    landmark_score = max(0, 1 - 4 * landmark_error) if alignments else None
    score = .75 * pixel_score + .25 * landmark_score if alignments else pixel_score
    defects = []
    for item in alignments:
        if item["error"] > .015:
            defects.append({"defect": "component_landmark_displacement", "component": item["component"],
                            "importance": round(item["error"] * item["confidence"], 4)})
    if aspect_error > .11: defects.append({"defect": "proportions_width_height", "importance": round(aspect_error, 4)})
    if iou < .78: defects.append({"defect": "silhouette_component_placement", "importance": round(1 - iou, 4)})
    if color_error > .18: defects.append({"defect": "surface_palette", "importance": round(color_error, 4)})
    if edge_f1 < .38: defects.append({"defect": "edge_structure", "importance": round(1 - edge_f1, 4)})
    defects.sort(key=lambda d: -d["importance"])
    result = {
        "score": round(score, 6), "pixel_score": round(pixel_score, 6),
        "landmark_score": round(landmark_score, 6) if landmark_score is not None else None,
        "landmark_error": round(landmark_error, 6) if landmark_error is not None else None,
        "landmarks": alignments,
        "silhouette_iou": round(iou, 6), "aspect_error": round(float(aspect_error), 6),
        "reference_aspect": round(float(ar_ref), 5), "render_aspect": round(float(ar_gen), 5),
        "color_median_l1": round(color_error, 6), "edge_f1_approx": round(float(edge_f1), 6),
        "defects": defects, "interpretation": "pixel-proxy ONLY; requires human 3D/visual review",
    }
    if output is not None:
        output.mkdir(parents=True, exist_ok=True)
        overlay = Image.new("RGBA", (128, 128), (0, 0, 0, 255))
        arr = np.zeros((128, 128, 4), dtype=np.uint8)
        arr[..., 3] = 255
        arr[a & ~b, :3] = (240, 78, 72)
        arr[b & ~a, :3] = (70, 155, 243)
        arr[a & b, :3] = (91, 200, 126)
        overlay = Image.fromarray(arr, "RGBA")
        combined = Image.new("RGBA", (128 * 3, 170), "#181c20")
        for idx, im in enumerate((ref, gen, overlay)):
            combined.alpha_composite(im, (idx * 128, 22))
        draw = ImageDraw.Draw(combined)
        # Some tests use procedurally generated reference fixtures; never
        # imply that every reference is private founder-supplied artwork.
        for idx, label in enumerate(("Reference", "3D render", "green=overlap")):
            draw.text((idx * 128 + 6, 4), label, fill="#ecedef")
        combined.resize((1152, 510), Image.Resampling.NEAREST).save(output / "reference_vs_render.png")
        (output / "visual_qa.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return result


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--render", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    print("LL_VISUAL_QA", json.dumps(compare(a.source, a.render, a.out), sort_keys=True))
