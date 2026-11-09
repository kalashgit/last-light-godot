#!/usr/bin/env python3
"""LL_ATLAS_OUTPUTS_V2: the missing `outputs` contract between F12 and W01.

F12's compose_atlas.py writes atlas.json (key/page/rect/direction/clip/duration_ms/
source_sha256). The W01 Godot fixture needs canvas size, ground pivot, frame index
and pixel-level hashes, none of which atlas.json carries. This module defines a
thin extension document (outputs_v2.json) that *references* the unmodified F12
atlas.json by hash and adds only those fields, then validates both together:

  - F12 atlas.json hash and frame-for-frame agreement (no divergent copy)
  - page PNGs: hash, PNG, RGBA, declared size
  - rects in bounds; rects + padding never overlap another rect
  - unique keys and (clip, direction, frame_index); heading coverage through
    F12's own verify_headings.verify_coverage (imported, not reimplemented)
  - pixels cut from the atlas match per-frame pixel_sha256 (raw RGBA bytes)
  - nonempty alpha, no opaque pixels on the canvas border (clipping)
  - ground pivot inside canvas, inside the alpha bbox (no floating), and
    stable within each clip+direction animation
  - straight-alpha sanity: semi-transparent edge pixels are not black-premultiplied
  - reports VRAM estimate for W08

Validation is technical only. It never grants A00, W09, founder or Godot approval.
Requires Pillow. Usage:
  python atlas_outputs_v2.py OUT_DIR/outputs_v2.json --f12-tools PATH/tools/factory/render_bridge
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

from PIL import Image

SCHEMA = "LL_ATLAS_OUTPUTS_V2"
ALLOWED_STATUS = {"CALIBRATION_ONLY", "CANDIDATE_NOT_APPROVED"}
F12_FRAME_FIELDS = ("key", "page", "rect", "direction", "clip", "duration_ms", "source_sha256")
MIN_OPAQUE_PIXELS = 16  # native-size readability floor; below this a sprite is a speck


class OutputsError(ValueError):
    pass


def require(ok, msg):
    if not ok:
        raise OutputsError(msg)


def sha_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def is_sha(s):
    return isinstance(s, str) and len(s) == 64 and all(c in "0123456789abcdef" for c in s)


def load_f12_module(f12_tools: Path, name: str):
    path = Path(f12_tools) / f"{name}.py"
    require(path.is_file(), f"F12 tool {name}.py not found at {path}")
    if str(path.parent) not in sys.path:
        sys.path.insert(0, str(path.parent))  # compose_atlas imports atlas_layout by name
    spec = importlib.util.spec_from_file_location(f"f12_{name}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def safe_child(root: Path, name: str) -> Path:
    require(isinstance(name, str) and name and Path(name).name == name, f"unsafe file name {name!r}")
    p = (root / name).resolve()
    require(p.is_relative_to(root.resolve()) and p.is_file(), f"missing file {name}")
    return p


def pixel_sha(img: Image.Image) -> str:
    return hashlib.sha256(img.convert("RGBA").tobytes()).hexdigest()


def frame_pixel_metrics(img: Image.Image) -> dict:
    """Alpha bbox, opaque count, clipping and halo metrics of one frame image."""
    alpha = img.getchannel("A")
    bbox = alpha.getbbox()
    w, h = img.size
    px = img.load()
    opaque = semi = black_semi = border_opaque = 0
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a == 0:
                continue
            if a == 255:
                opaque += 1
            else:
                semi += 1
                if r + g + b == 0:
                    black_semi += 1
            if a >= 128 and (x == 0 or y == 0 or x == w - 1 or y == h - 1):
                border_opaque += 1
    return {"alpha_bbox": list(bbox) if bbox else None, "opaque_pixels": opaque,
            "semi_pixels": semi, "black_semi_ratio": (black_semi / semi) if semi else 0.0,
            "border_opaque_pixels": border_opaque}


def overlaps(a, b):
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    return ax < bx + bw and bx < ax + aw and ay < by + bh and by < ay + ah


def validate_outputs(outputs_path: Path, f12_tools: Path, expected_directions=None,
                     pivot_tolerance_px=0.5) -> dict:
    outputs_path = Path(outputs_path).resolve()
    root = outputs_path.parent
    doc = json.loads(outputs_path.read_text())
    require(doc.get("schema") == SCHEMA and doc.get("schema_version") == 1, "not LL_ATLAS_OUTPUTS_V2 v1")
    require(doc.get("status") in ALLOWED_STATUS, "status must be CALIBRATION_ONLY or CANDIDATE_NOT_APPROVED")
    for forbidden in ("founder_approved", "golden_approved", "w09_approved"):
        require(not doc.get(forbidden), f"outputs cannot self-assert {forbidden}")
    require(doc.get("logical_tile_px") == [80, 40], "logical tile must be [80,40]")
    proj = doc.get("projection") or {}
    require(proj.get("basis_px") == [[-40, 20], [40, 20]], "projection basis must be F12 80x40 basis")
    require(isinstance(proj.get("max_residual_px"), (int, float)) and proj["max_residual_px"] <= 0.001,
            "projection residual missing or > 0.001 px")
    directions = doc.get("directions")
    require(directions in (1, 2, 4, 8, 16), "directions must be 1/2/4/8/16")
    if expected_directions is not None:
        require(directions == expected_directions, "directions disagree with package renderer")

    # F12 atlas.json is referenced, never rewritten.
    ref = doc.get("f12_atlas") or {}
    atlas_path = safe_child(root, ref.get("file", ""))
    require(sha_file(atlas_path) == ref.get("sha256"), "F12 atlas.json hash mismatch")
    f12 = json.loads(atlas_path.read_text())
    padding = f12.get("padding")
    require(isinstance(padding, int) and padding >= 1, "F12 atlas padding missing")

    pages = doc.get("pages")
    require(isinstance(pages, list) and pages, "pages required")
    require([{"file": p.get("file"), "sha256": p.get("sha256")} for p in pages] == f12.get("atlas_files"),
            "pages disagree with F12 atlas_files")
    page_images = []
    vram = 0
    for p in pages:
        path = safe_child(root, p["file"])
        require(sha_file(path) == p["sha256"], f"page hash mismatch {p['file']}")
        img = Image.open(path)
        require(img.format == "PNG" and img.mode == "RGBA", f"page not RGBA PNG {p['file']}")
        require(list(img.size) == p.get("size"), f"page size mismatch {p['file']}")
        vram += img.size[0] * img.size[1] * 4
        page_images.append(img.copy())

    clips = doc.get("clips")
    require(isinstance(clips, dict) and clips, "clips required")
    for name, c in clips.items():
        require(isinstance(c, dict) and type(c.get("fps")) is int and 1 <= c["fps"] <= 60,
                f"clip {name} fps invalid")
        require(isinstance(c.get("loop"), bool), f"clip {name} loop flag required")

    frames = doc.get("frames")
    require(isinstance(frames, list) and frames, "frames required")
    f12_frames = {f["key"]: f for f in f12.get("frames", [])}
    require(len(f12_frames) == len(f12.get("frames", [])) == len(frames), "frame count disagrees with F12 atlas")
    keys, identities, rects = set(), set(), []
    pivots = {}
    metrics = []
    for f in frames:
        key = f.get("key")
        require(isinstance(key, str) and key not in keys, f"duplicate/empty key {key!r}")
        keys.add(key)
        require(key in f12_frames, f"frame {key} not in F12 atlas")
        for field in F12_FRAME_FIELDS:
            require(f.get(field) == f12_frames[key].get(field), f"{key}: {field} differs from F12 atlas")
        require(f["clip"] in clips, f"{key}: clip not declared")
        require(type(f.get("frame_index")) is int and f["frame_index"] >= 0, f"{key}: frame_index invalid")
        ident = (f["clip"], f["direction"], f["frame_index"])
        require(ident not in identities, f"{key}: duplicate clip/direction/frame_index")
        identities.add(ident)
        require(is_sha(f.get("pixel_sha256")), f"{key}: pixel_sha256 invalid")
        page = f["page"]
        require(type(page) is int and 0 <= page < len(page_images), f"{key}: bad page")
        x, y, w, h = f["rect"]
        pw, ph = page_images[page].size
        require(x >= padding and y >= padding and x + w + padding <= pw and y + h + padding <= ph,
                f"{key}: rect+padding outside page")
        for other_page, other_key, other in rects:
            if other_page == page:
                grown = [x - padding, y - padding, w + 2 * padding, h + 2 * padding]
                require(not overlaps(grown, other), f"{key}: overlaps {other_key} (incl. padding)")
        rects.append((page, key, [x, y, w, h]))

        cw, ch = f.get("canvas_px") or (None, None)
        tx, ty = f.get("trim_offset_px") or (None, None)
        require(all(type(v) is int for v in (cw, ch, tx, ty)), f"{key}: canvas/trim ints required")
        require(tx >= 0 and ty >= 0 and tx + w <= cw and ty + h <= ch, f"{key}: crop outside canvas")
        gx, gy = f.get("ground_pivot_px") or (None, None)
        require(all(isinstance(v, (int, float)) for v in (gx, gy)), f"{key}: ground pivot required")
        require(0 <= gx <= cw and 0 <= gy <= ch, f"{key}: pivot outside canvas")

        crop = page_images[page].crop((x, y, x + w, y + h))
        require(pixel_sha(crop) == f["pixel_sha256"], f"{key}: atlas pixels differ from source frame")
        m = frame_pixel_metrics(crop)
        require(m["alpha_bbox"] is not None, f"{key}: blank alpha")
        require(m["opaque_pixels"] >= MIN_OPAQUE_PIXELS, f"{key}: fewer than {MIN_OPAQUE_PIXELS} opaque px")
        if tx == 0 and ty == 0 and (w, h) == (cw, ch):
            require(m["border_opaque_pixels"] == 0, f"{key}: opaque pixels on canvas edge (clipped)")
        require(m["black_semi_ratio"] <= 0.5, f"{key}: edge pixels look black-premultiplied (halo)")
        bx0, by0, bx1, by1 = m["alpha_bbox"]
        lx, ly = gx - tx, gy - ty
        require(bx0 <= lx <= bx1 and by0 <= ly <= by1, f"{key}: ground pivot outside alpha bbox (floating)")
        require(f.get("alpha_bbox") == m["alpha_bbox"], f"{key}: recorded alpha_bbox disagrees")
        anim = (f["clip"], f["direction"])
        if anim in pivots:
            px0, py0 = pivots[anim]
            require(abs(px0 - gx) <= pivot_tolerance_px and abs(py0 - gy) <= pivot_tolerance_px,
                    f"{key}: pivot wanders within animation {anim}")
        else:
            pivots[anim] = (gx, gy)
        metrics.append({"key": key, **m})

    verify = load_f12_module(f12_tools, "verify_headings")
    headings = directions if directions in (1, 4, 8, 16) else None
    require(headings is not None, "F12 verify_headings supports 1/4/8/16 only; 2 is NOT RUN")
    coverage = verify.verify_coverage(
        [{"clip": f["clip"], "direction": f["direction"], "frame_index": f["frame_index"]} for f in frames],
        headings)
    return {"status": "OUTPUTS_TECHNICAL_PASS_NOT_APPROVAL", "frames": len(frames), "pages": len(pages),
            "directions": directions, "vram_bytes_uncompressed": vram, "coverage": coverage["clips"],
            "min_opaque_pixels": min(m["opaque_pixels"] for m in metrics),
            "outputs_sha256": sha_file(outputs_path)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("outputs", type=Path)
    ap.add_argument("--f12-tools", type=Path, required=True)
    ap.add_argument("--directions", type=int)
    a = ap.parse_args()
    try:
        print(json.dumps(validate_outputs(a.outputs, a.f12_tools, a.directions), sort_keys=True))
        return 0
    except (OutputsError, OSError, ValueError, KeyError, TypeError) as e:
        print(json.dumps({"status": "REJECTED", "reason": str(e)}))
        return 1


if __name__ == "__main__":
    sys.exit(main())
