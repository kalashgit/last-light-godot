#!/usr/bin/env python3
"""LAST LIGHT F12: fail-closed render-output manifest validator (stdlib only).

This validates OUTPUT metadata and PNG headers. It does not calibrate Blender's
camera, prove a sprite looks good, or certify A00 approvals/Godot compatibility.
Usage: python tools/f12/validate_render_manifest.py path/to/render_manifest.json
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import struct
import sys

ALLOWED_DIRECTIONS = {1, 2, 4, 8, 16}
PNG_SIG = b"\x89PNG\r\n\x1a\n"


class RenderValidationError(ValueError):
    pass


def require(cond: bool, message: str) -> None:
    if not cond:
        raise RenderValidationError(message)


def _finite_number(v, name: str) -> float:
    require(isinstance(v, (int, float)) and not isinstance(v, bool), f"{name}: expected number")
    require(math.isfinite(float(v)), f"{name}: nonfinite")
    return float(v)


def _point(point, name: str):
    require(isinstance(point, list) and len(point) == 2, f"{name}: expected [x, y]")
    return tuple(_finite_number(v, name) for v in point)


def validate_projection(p: dict):
    """Validate measured Godot tile projection, not a guessed camera angle."""
    require(isinstance(p, dict), "projection: missing")
    x = _point(p.get("grid_basis_x_px"), "grid_basis_x_px")
    y = _point(p.get("grid_basis_y_px"), "grid_basis_y_px")
    require("calibration_evidence" in p and bool(p["calibration_evidence"]), "calibration_evidence missing")
    cross = x[0] * y[1] - x[1] * y[0]
    require(abs(cross) > 1e-8, "projection: degenerate grid basis")
    # The game basis is the conventional 2:1 isometric 80x40 diamond:
    # x=[40,20], y=[-40,20], with sign/orientation chosen by game contract.
    # Comparison uses measured pixel vectors; signs can be mirrored by coordinate convention.
    tol = _finite_number(p.get("max_axis_error_px", 0), "max_axis_error_px")
    require(0 <= tol <= 2, "projection: max_axis_error_px exceeds 2px gate")
    for label, vec in (("x", x), ("y", y)):
        # Float/projected-coordinate rounding has sub-0.001px encoding noise.\n        require(abs(abs(vec[0]) - 40) <= tol + 0.001 and abs(abs(vec[1]) - 20) <= tol + 0.001,
                f"projection: {label} basis differs from 80x40 tile")
    return {"basis_x_px": x, "basis_y_px": y, "max_error_px": tol}


def png_info(path: Path):
    with path.open("rb") as f:
        header = f.read(33)
    require(header[:8] == PNG_SIG, f"{path}: invalid PNG signature")
    require(len(header) == 33 and header[12:16] == b"IHDR", f"{path}: missing IHDR")
    require(struct.unpack(">I", header[8:12])[0] == 13, f"{path}: invalid IHDR length")
    width, height, depth, color = struct.unpack(">IIBB", header[16:26])
    require(width > 0 and height > 0 and depth == 8 and color == 6,
            f"{path}: requires nonempty 8-bit RGBA PNG")
    return width, height


def _rect(obj, name):
    require(isinstance(obj, list) and len(obj) == 4, f"{name}: expected [x,y,w,h]")
    require(all(isinstance(v, int) and not isinstance(v, bool) for v in obj), f"{name}: integers required")
    x, y, w, h = obj
    require(x >= 0 and y >= 0 and w > 0 and h > 0, f"{name}: invalid rect")
    return x, y, w, h


def _intersect(a, b):
    return a[0] < b[0] + b[2] and b[0] < a[0] + a[2] and a[1] < b[1] + b[3] and b[1] < a[1] + a[3]


def validate_manifest(data: dict, root: Path):
    require(isinstance(data, dict), "manifest: object required")
    require(data.get("schema_version") == 1, "schema_version must be 1")
    require(data.get("production_status") in {"CALIBRATION_ONLY", "A00_VERIFIED_SOURCE"},
            "production_status must identify verification gate")
    if data["production_status"] == "A00_VERIFIED_SOURCE":
        for key in ("canonical_master_id", "a00_notion_url", "catalog_snapshot_sha", "rights_status"):
            require(isinstance(data.get(key), str) and data[key].strip(), f"{key} missing")
        require(data["rights_status"] == "CLEARED", "rights must be CLEARED")
    else:
        require(not data.get("canonical_master_id"), "calibration must not claim canonical ID")
    projection = validate_projection(data.get("projection"))
    count = data.get("direction_count")
    require(type(count) is int and count in ALLOWED_DIRECTIONS, "invalid direction_count")
    angles = data.get("heading_degrees")
    require(isinstance(angles, list) and len(angles) == count, "heading count mismatch")
    for i, angle in enumerate(angles):
        num = _finite_number(angle, "heading_degrees")
        expected = (360.0 * i / count) % 360
        require(abs((num - expected + 180) % 360 - 180) < 1e-5,
                f"heading {i}: wrong order/angle (expected {expected})")
    frames = data.get("frames")
    require(isinstance(frames, list) and len(frames) >= count, "missing frames")
    seen = set()
    by_clip = {}
    for frame in frames:
        require(isinstance(frame, dict), "invalid frame")
        clip = frame.get("clip")
        direction = frame.get("direction")
        idx = frame.get("frame")
        require(isinstance(clip, str) and clip, "frame: clip missing")
        require(type(direction) is int and 0 <= direction < count, "frame: invalid direction")
        require(type(idx) is int and idx >= 0, "frame: invalid frame index")
        key = (clip, direction, idx)
        require(key not in seen, f"duplicate frame: {key}")
        seen.add(key)
        by_clip.setdefault(clip, {}).setdefault(direction, set()).add(idx)
        duration = frame.get("duration_ms")
        require(type(duration) is int and duration > 0, f"frame {key}: invalid duration")
        _point(frame.get("ground_pivot_px"), f"frame {key} ground pivot")
        relpath = frame.get("png")
        require(isinstance(relpath, str) and relpath.endswith(".png"), f"frame {key}: png path missing")
        absolute = (root / relpath).resolve()
        require(absolute.is_relative_to(root.resolve()), f"frame {key}: path traversal")
        require(absolute.is_file(), f"frame {key}: missing PNG {relpath}")
        png_info(absolute)
    for clip, per_heading in by_clip.items():
        require(set(per_heading) == set(range(count)), f"{clip}: missing directional coverage")
        expected_indices = set(range(max(max(s) for s in per_heading.values()) + 1))
        for direction, indices in per_heading.items():
            require(indices == expected_indices, f"{clip}: missing frame index direction {direction}")
    atlases = data.get("atlases", [])
    require(isinstance(atlases, list), "atlases must be list")
    for page in atlases:
        require(isinstance(page, dict), "invalid atlas page")
        rel = page.get("png")
        require(isinstance(rel, str), "atlas PNG missing")
        path = (root / rel).resolve()
        require(path.is_relative_to(root.resolve()) and path.is_file(), "unsafe or missing atlas")
        w, h = png_info(path)
        rects = []
        for i, r in enumerate(page.get("rects", [])):
            box = _rect(r, f"atlas rect {i}")
            require(box[0] + box[2] <= w and box[1] + box[3] <= h, "atlas rect out of bounds")
            require(all(not _intersect(box, prev) for prev in rects), "atlas rects overlap")
            rects.append(box)
    return {"status": "PASS_METADATA_AND_PNG_HEADERS_ONLY",
            "direction_count": count, "frame_count": len(frames),
            "atlas_count": len(atlases), "projection": projection,
            "not_verified": ["pixel appearance", "full PNG decode", "Blender source", "A00 live status",
                             "Godot import", "real device", "founder Golden approval"]}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("manifest", type=Path)
    args = p.parse_args()
    try:
        result = validate_manifest(json.loads(args.manifest.read_text(encoding="utf-8")),
                                   args.manifest.resolve().parent)
    except (RenderValidationError, ValueError, OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "FAIL", "reason": str(exc)}))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
