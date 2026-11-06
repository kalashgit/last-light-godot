#!/usr/bin/env python3
"""LAST LIGHT V4 original pixel-art benchmark (12 authored semantic recipes).

Offline-only, Pillow-based. This is a review renderer, not a production art
approval tool and not a replacement for the standalone V3 CodePad facade.
Its geometry language is data-driven; new recipes require no item-specific
Python drawing functions. Complex geometry still requires independent authoring.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import re
import tempfile
import time
import zipfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

SCHEMA = "last_light.original_component_recipe.v1"
RENDERER = "last_light.component_renderer.v4_benchmark_1"
NATIVE = 64
PALETTES = {
    # Tone 0 is an occluded crease, 5 is the narrow illuminated edge.
    "steel": ["#252e33", "#46535a", "#687a82", "#8b9ba0", "#b6c3c7", "#e2e5dc"],
    "blued_steel": ["#1d292e", "#35484e", "#50636b", "#6c8289", "#91a4a7", "#c8d1cd"],
    "aluminum": ["#3a4549", "#5d696c", "#8a9899", "#b2c0be", "#d1dad4", "#edf0e8"],
    "wood": ["#37251e", "#5a3c2b", "#805739", "#a1754d", "#bd9364", "#dfb67c"],
    "olive_canvas": ["#283129", "#3d4937", "#586b4a", "#758466", "#98a487", "#bec3a8"],
    "khaki_canvas": ["#37352c", "#5c5a46", "#80795e", "#a29a78", "#c4b997", "#e0d4b2"],
    "leather": ["#2b201b", "#493126", "#694633", "#906346", "#b18560", "#d5ab7c"],
    "rubber": ["#151d1e", "#293436", "#3f4b4c", "#596566", "#798486", "#a1aaab"],
    "paper": ["#625e4f", "#8c8570", "#b1a993", "#d0c8b2", "#e5decc", "#f6efdc"],
    "medical_blue": ["#263e49", "#3c6070", "#598092", "#7ba3b1", "#acc6cd", "#d4e3df"],
    "painted_red": ["#402a2b", "#713c3b", "#98544a", "#b8715a", "#d69b76", "#efc0a0"],
    "painted_green": ["#27362d", "#3e5240", "#557157", "#768d6d", "#9aaa8c", "#cfceb0"],
    "glass": ["#23383f", "#3e5e65", "#668388", "#91b1b3", "#b8d1cf", "#e0ede6"],
    "amber_glass": ["#392e22", "#62432b", "#8b6438", "#b38b51", "#c5a66c", "#ecce93"],
    "crystal": ["#281f37", "#473059", "#684779", "#9065a0", "#b08dbb", "#dfc7e5"],
    "stone": ["#303337", "#4c5051", "#696f6f", "#8e9290", "#b1b2a9", "#d4d2c5"],
}
GEOMETRIES = {"polygon", "ellipse", "rectangle", "line", "point", "arc"}
SURFACES = {
    "wood": {"grain"}, "leather": {"grain"},
    "olive_canvas": {"weave"}, "khaki_canvas": {"weave"},
    "steel": {"brush"}, "blued_steel": {"brush"},
    "aluminum": {"brush"}, "crystal": {"facet"},
}


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def atomic_bytes(path: Path, contents: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".ll-v4-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(contents)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def validate_recipe(recipe: dict) -> None:
    if recipe.get("schema") != SCHEMA:
        raise ValueError("Unsupported recipe schema")
    if not isinstance(recipe.get("id"), str) or not re.fullmatch(r"ll\.benchmark\.[a-z0-9_]+", recipe["id"]):
        raise ValueError("Stable benchmark item ID required")
    if recipe.get("view") != "inventory_three_quarter" or recipe.get("size") != [64, 64]:
        raise ValueError("Benchmark requires an authored 64px inventory view")
    if recipe.get("approval") != "candidate_needs_founder_review":
        raise ValueError("Benchmark cannot have an approved art state")
    if recipe.get("rights") != "original_independent_design":
        raise ValueError("Only independent original recipes are eligible")
    anchor = recipe.get("anchor")
    if not isinstance(anchor, list) or len(anchor) != 2 or not all(isinstance(a, int) and 0 <= a < 64 for a in anchor):
        raise ValueError("Inventory anchor must be explicit")
    if not recipe.get("semantic_brief") or not recipe.get("layers"):
        raise ValueError("Semantic brief and geometry are required")
    names = set()
    for layer in recipe["layers"]:
        if not isinstance(layer, dict) or not isinstance(layer.get("name"), str) or layer["name"] in names:
            raise ValueError("Every layer needs an independent unique component name")
        names.add(layer["name"])
        shape = layer.get("shape")
        if shape not in GEOMETRIES:
            raise ValueError(f"Unsupported geometry {shape}")
        if layer.get("material") not in PALETTES or type(layer.get("tone")) is not int or not 0 <= layer["tone"] <= 5:
            raise ValueError("Material and tone required on each component")
        if layer["material"] not in recipe["materials"]:
            raise ValueError("Layer material must be declared in the semantic recipe")
        if layer.get("surface") and layer["surface"] not in SURFACES.get(layer["material"], set()):
            raise ValueError("Invalid surface treatment for material")
        if layer.get("surface") and shape not in {"polygon", "rectangle", "ellipse"}:
            raise ValueError("Material surface treatment requires a closed face")
        if shape in {"polygon", "line"}:
            points = layer.get("points")
            if not isinstance(points, list) or len(points) < (3 if shape == "polygon" else 2):
                raise ValueError("Invalid component points")
            coords = (c for point in points for c in point)
        elif shape == "point":
            coords = layer.get("xy", [])
        else:
            box = layer.get("bbox")
            if not isinstance(box, list) or len(box) != 4 or box[0] > box[2] or box[1] > box[3]:
                raise ValueError("Invalid component bounding box")
            coords = box
        if any(not isinstance(c, int) or c < 0 or c >= 64 for c in coords):
            raise ValueError("All component coordinates must stay within the native pixel grid")
        if shape == "arc" and not all(isinstance(layer.get(k), int) for k in ("start", "end")):
            raise ValueError("Arc needs start/end angles")
        width = layer.get("width", 1)
        if not isinstance(width, int) or not 1 <= width <= 6:
            raise ValueError("Width outside native pixel-art constraints")


def draw_layer(target: Image.Image, layer: dict) -> None:
    draw = ImageDraw.Draw(target)
    color = PALETTES[layer["material"]][layer["tone"]]
    kind = layer["shape"]
    if kind == "polygon":
        draw.polygon([tuple(p) for p in layer["points"]], fill=color)
    elif kind == "line":
        draw.line([tuple(p) for p in layer["points"]], fill=color, width=layer.get("width", 1), joint="curve")
    elif kind == "point":
        draw.point(tuple(layer["xy"]), fill=color)
    elif kind == "rectangle":
        draw.rectangle(tuple(layer["bbox"]), fill=color, width=layer.get("width", 1)) if layer.get("outline_only") else draw.rectangle(tuple(layer["bbox"]), fill=color)
    elif kind == "ellipse":
        draw.ellipse(tuple(layer["bbox"]), outline=color, width=layer.get("width", 1)) if layer.get("outline_only") else draw.ellipse(tuple(layer["bbox"]), fill=color)
    elif kind == "arc":
        draw.arc(tuple(layer["bbox"]), layer["start"], layer["end"], fill=color, width=layer.get("width", 1))
    # Sparse deterministic, clipped material grain. This never changes the
    # silhouette and does not use random noise or source-image pixels.
    if layer.get("surface"):
        mask = Image.new("L", target.size, 0)
        md = ImageDraw.Draw(mask)
        if kind == "polygon":
            md.polygon([tuple(p) for p in layer["points"]], fill=255)
        elif kind == "rectangle":
            md.rectangle(tuple(layer["bbox"]), fill=255)
        else:
            md.ellipse(tuple(layer["bbox"]), fill=255)
        bounds = mask.getbbox()
        if not bounds:
            return
        treatment = layer["surface"]
        overlay = Image.new("RGBA", target.size)
        od = ImageDraw.Draw(overlay)
        light = PALETTES[layer["material"]][min(5, layer["tone"] + 1)]
        dark = PALETTES[layer["material"]][max(0, layer["tone"] - 1)]
        x0, y0, x1, y1 = bounds
        if treatment == "grain":
            # Parallel discontinuous strokes read as directional wood grain.
            for yy in range(y0 + 2, y1 - 1, 6):
                od.line((x0 + 3, yy, min(x1 - 2, x0 + 8), yy - 1), fill=dark, width=1)
        elif treatment == "brush":
            for yy in range(y0 + 3, y1 - 1, 7):
                od.line((x0 + 5, yy, min(x1 - 2, x0 + 12), yy - 1), fill=light, width=1)
        elif treatment == "weave":
            for yy in range(y0 + 3, y1 - 1, 7):
                for xx in range(x0 + 3 + (yy % 3), x1 - 1, 9):
                    od.line((xx, yy, xx + 1, yy), fill=dark)
        elif treatment == "facet":
            od.line((x0 + 2, y0 + 2, max(x0 + 2, x1 - 3), max(y0 + 2, y1 - 3)), fill=light)
        if overlay.getbbox():
            clipped = Image.new("RGBA", target.size)
            clipped.paste(overlay, (0, 0), mask)
            target.alpha_composite(clipped)


def render(recipe: dict) -> Image.Image:
    validate_recipe(recipe)
    image = Image.new("RGBA", (NATIVE, NATIVE), (0, 0, 0, 0))
    for layer in recipe["layers"]:
        draw_layer(image, layer)
    return image


def technical_qa(image: Image.Image) -> dict:
    if image.mode != "RGBA" or image.size != (64, 64):
        raise ValueError("Expected native 64x64 RGBA")
    alpha = image.getchannel("A")
    bbox = alpha.getbbox()
    if bbox is None:
        raise ValueError("Empty sprite")
    if any(a == 0 or b == 64 for a, b in ((bbox[0], bbox[2]), (bbox[1], bbox[3]))):
        raise ValueError("Sprite clipped at an edge")
    occupancy = sum(1 for value in alpha.get_flattened_data() if value) / 4096
    if not .03 <= occupancy <= .65:
        raise ValueError("Implausible icon occupancy")
    return {"dimensions": [64, 64], "mode": "RGBA", "alpha_bbox": bbox,
            "occupied_fraction": round(occupancy, 4), "transparent_background": True,
            "pixel_grid_clean": True, "technical_pass": True,
            "visual_review": "not_assessed", "founder_approved": False,
            "godot_integrated": False, "iphone_verified": False}


def make_sheet(records: list[tuple[dict, Image.Image]], size: int, background: str) -> Image.Image:
    # Presentation-only background and external labels; PNG source stays RGBA.
    width, height = 4 * 180, 3 * 180
    result = Image.new("RGB", (width, height), "#252b30" if background == "dark" else "#ded9ce")
    draw = ImageDraw.Draw(result)
    font = ImageFont.load_default()
    for i, (recipe, icon) in enumerate(records):
        cx, cy = (i % 4) * 180, (i // 4) * 180
        tile = "#343c42" if background == "dark" else "#eee9dc"
        ink = "#f0e9d5" if background == "dark" else "#283036"
        draw.rectangle((cx + 3, cy + 3, cx + 176, cy + 176), fill=tile)
        for yy in range(28, 151, 12):
            for xx in range(25, 155, 12):
                if (xx // 12 + yy // 12) % 2 == 0:
                    draw.rectangle((cx + xx, cy + yy, cx + xx + 11, cy + yy + 11), fill="#3e464a" if background == "dark" else "#e0dacd")
        native = icon if size == 64 else icon.resize((size, size), Image.Resampling.NEAREST)
        zoom = native.resize((size * 2, size * 2), Image.Resampling.NEAREST)
        result.paste(zoom, (cx + (180 - zoom.width)//2, cy + (174 - zoom.height)//2), zoom)
        draw.text((cx + 8, cy + 8), recipe["label"], font=font, fill=ink)
        draw.text((cx + 8, cy + 156), f"native review {size}px | NOT APPROVED", font=font, fill=ink)
    return result


def png_bytes(image: Image.Image) -> bytes:
    data = io.BytesIO()
    image.save(data, format="PNG", optimize=False)
    return data.getvalue()


def run(recipe_path: Path, output: Path) -> dict:
    start = time.perf_counter()
    payload = json.loads(recipe_path.read_text(encoding="utf-8"))
    if payload.get("schema") != SCHEMA or len(payload.get("recipes", [])) != 12:
        raise ValueError("This gated benchmark must contain exactly 12 recipes")
    records: list[tuple[dict, Image.Image]] = []
    manifest = []
    source_hash = hashlib.sha256(canonical(payload)).hexdigest()
    seen_ids = set()
    for recipe in payload["recipes"]:
        if recipe["id"] in seen_ids:
            raise ValueError("Duplicate immutable ID")
        seen_ids.add(recipe["id"])
        image = render(recipe)
        qa = technical_qa(image)
        name = recipe["id"].split(".")[-1]
        content = png_bytes(image)
        target = f"candidates/{name}.png"
        atomic_bytes(output / target, content)
        manifest.append({"asset_id": recipe["id"], "display_name": recipe["label"],
                         "semantic_brief": recipe["semantic_brief"], "materials": recipe["materials"],
                         "anchor": recipe["anchor"], "direction": recipe["view"],
                         "rights": recipe["rights"], "state": "candidate_needs_founder_review",
                         "recipe_schema": SCHEMA, "render_engine": RENDERER,
                         "filename": target, "sha256": hashlib.sha256(content).hexdigest(),
                         "technical_qa": qa})
        records.append((recipe, image))
    for size in (32, 48, 64):
        for bg in ("dark", "light"):
            atomic_bytes(output / f"reviews/benchmark_{size}_{bg}.png", png_bytes(make_sheet(records, size, bg)))
    result = {"schema": "last_light.benchmark_manifest.v1", "renderer": RENDERER,
              "source_recipe_sha256": source_hash, "count": len(manifest),
              "rights": "original_independent_design", "art_approval": "none",
              "game_integration": "none", "iphone_verification": "none",
              "reference_sheet_comparison": "blocked_founder_reference_images_not_local",
              "items": manifest}
    atomic_bytes(output / "manifest.json", canonical(result) + b"\n")
    defects = {
        "review_state": "founder_visual_review_required",
        "known_limits": [
            "Standalone authored icon geometry is not a general arbitrary-object design model.",
            "No supplied Golden 40 sheet files in the local repository for pixel-side comparison.",
            "Silhouette, material fidelity, and visual identity need manual side-by-side review.",
            "Inventory views are not valid held/world directional frames.",
            "Godot inventory integration, real mobile scale, and iPhone controls untested."
        ],
        "per_item_review_queue": [{"asset_id": r["id"], "decision": "pending_founder_review",
                                  "silhouette": "inspect", "material": "inspect",
                                  "scale_32_48_64": "inspect"} for r, _ in records]}
    atomic_bytes(output / "visual_review_queue.json", canonical(defects) + b"\n")
    archive = output / "LAST_LIGHT_V4_BENCHMARK_12_CANDIDATES.zip"
    files = sorted([p for p in output.rglob("*") if p.is_file() and p != archive])
    package = io.BytesIO()
    with zipfile.ZipFile(package, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for file in files:
            info = zipfile.ZipInfo(file.relative_to(output).as_posix(), date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, file.read_bytes())
    atomic_bytes(archive, package.getvalue())
    result["measured_seconds"] = round(time.perf_counter() - start, 3)
    result["package_sha256"] = hashlib.sha256(archive.read_bytes()).hexdigest()
    result["package_bytes"] = archive.stat().st_size
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="LAST LIGHT V4 12-item original-art benchmark")
    parser.add_argument("--recipes", type=Path, default=Path(__file__).resolve().parents[1] / "data/factory/v4_benchmark_12.json")
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parents[1] / "review/v4_benchmark_12")
    args = parser.parse_args()
    report = run(args.recipes, args.output)
    print(json.dumps({k: v for k, v in report.items() if k != "items"}, indent=2))


if __name__ == "__main__":
    main()
