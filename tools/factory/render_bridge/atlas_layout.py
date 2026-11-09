"""F12 deterministic atlas layout and strict manifest validation (stdlib only).

Input manifest: {"frames":[{"key":"...", "width":32,"height":48,
"duration_ms":100,"direction":0,"clip":"idle","source_sha256":"<64 hex>"}]}
Keys must be unique; input order does not influence packing.
This is a layout/metadata stage, NOT a PNG compositor or Godot importer.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path

def validate(frames, page_size, padding):
    if not isinstance(frames, list) or not frames:
        raise ValueError("frames must be a nonempty list")
    if not isinstance(page_size, int) or page_size < 16 or page_size > 8192:
        raise ValueError("page_size out of bounds")
    if not isinstance(padding, int) or padding < 1 or padding > 32:
        raise ValueError("padding out of bounds")
    keys = set()
    for f in frames:
        if not isinstance(f, dict):
            raise ValueError("invalid frame")
        key = f.get("key")
        if not isinstance(key, str) or not key or key in keys:
            raise ValueError("empty or duplicate key")
        keys.add(key)
        for name in ("width", "height", "duration_ms"):
            v = f.get(name)
            if type(v) is not int or v <= 0:
                raise ValueError("invalid " + name + ": " + key)
        if type(f.get("direction")) is not int or not 0 <= f["direction"] < 16:
            raise ValueError("invalid direction: " + key)
        if not isinstance(f.get("clip"), str) or not f["clip"]:
            raise ValueError("missing clip: " + key)
        digest = f.get("source_sha256")
        if not isinstance(digest, str) or len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
            raise ValueError("invalid source hash: " + key)
        anchor = f.get("anchor_local_px")
        if anchor is not None and (not isinstance(anchor,list) or len(anchor)!=2
                or not all(type(v) in (int,float) and math.isfinite(v) for v in anchor)):
            raise ValueError("invalid ground anchor: " + key)
        original_pivot = f.get("world_ground_pivot_px")
        if original_pivot is not None and (not isinstance(original_pivot,list) or len(original_pivot)!=2
                or not all(type(v) in (int,float) and math.isfinite(v) for v in original_pivot)):
            raise ValueError("invalid original pivot: " + key)
        if f["width"] + 2 * padding > page_size or f["height"] + 2 * padding > page_size:
            raise ValueError("frame exceeds page: " + key)

def layout(frames, page_size=2048, padding=2):
    validate(frames, page_size, padding)
    # Stable shelf packing; independent of input ordering and host filesystem.
    ordered = sorted(frames, key=lambda f: (-f["height"], -f["width"], f["key"]))
    pages = [[]]
    x = y = shelf_h = 0
    for f in ordered:
        w, h = f["width"] + 2 * padding, f["height"] + 2 * padding
        if x + w > page_size:
            x, y, shelf_h = 0, y + shelf_h, 0
        if y + h > page_size:
            pages.append([])
            x = y = shelf_h = 0
        entry = {
            "key": f["key"], "page": len(pages) - 1,
            "rect": [x + padding, y + padding, f["width"], f["height"]],
            "direction": f["direction"], "clip": f["clip"],
            "duration_ms": f["duration_ms"], "source_sha256": f["source_sha256"],
        }
        if "anchor_local_px" in f:
            entry["anchor_local_px"] = f["anchor_local_px"]
        if "source_crop_rect" in f:
            entry["source_crop_rect"] = f["source_crop_rect"]
        if "world_ground_pivot_px" in f:
            entry["world_ground_pivot_px"] = f["world_ground_pivot_px"]
        pages[-1].append(entry)
        x += w
        shelf_h = max(shelf_h, h)
    result = {"schema_version": 1, "status": "LAYOUT_ONLY_NOT_GAME_READY",
              "page_size": page_size, "padding": padding,
              "pages": len(pages), "frames": sorted(
                  (entry for page in pages for entry in page), key=lambda e: e["key"])}
    canonical = json.dumps(result, sort_keys=True, separators=(",", ":")).encode()
    result["layout_sha256"] = hashlib.sha256(canonical).hexdigest()
    return result

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--page-size", type=int, default=2048)
    parser.add_argument("--padding", type=int, default=2)
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text())
    result = layout(manifest["frames"], args.page_size, args.padding)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")

if __name__ == "__main__":
    main()
