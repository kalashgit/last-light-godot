"""Offline bridge for sprite-gen exported PNG frames; never invokes AI providers.

Input is a small, explicit interchange contract, not a dependency on sprite-gen's
rapidly changing internal manifest format. See the production documentation.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from PIL import Image

try:
    from .pack import sha
except ImportError:
    from pack import sha


SAFE = re.compile(r"[a-z0-9][a-z0-9_-]{0,79}\Z")
MAX_FRAMES = 256
GAP = 2


def bridge(spec_path: Path, output: Path, page_size: int = 1024) -> dict:
    if page_size not in (1024, 2048):
        raise ValueError("Unsupported page size")
    spec_path = spec_path.resolve(strict=True)
    root = spec_path.parent
    spec = json.loads(spec_path.read_text())
    asset_id = spec.get("asset_id")
    if (spec.get("schema_version") != 1 or not isinstance(asset_id, str)
            or not SAFE.fullmatch(asset_id)):
        raise ValueError("Invalid sprite-gen interchange contract")
    frames = spec.get("frames")
    if not isinstance(frames, list) or not 1 <= len(frames) <= MAX_FRAMES:
        raise ValueError("Frame count must be 1–256")

    validated = []
    seen = set()
    for item in frames:
        if not isinstance(item, dict):
            raise ValueError("Frame must be an object")
        state, heading, index = item.get("state"), item.get("heading"), item.get("frame")
        fps, rel = item.get("fps"), item.get("png")
        if (not isinstance(state, str) or not SAFE.fullmatch(state)
                or type(heading) is not int or heading not in range(16)
                or type(index) is not int or not 0 <= index < MAX_FRAMES
                or type(fps) not in (int, float) or not 1 <= fps <= 60
                or not isinstance(rel, str) or not rel.endswith(".png")):
            raise ValueError("Invalid frame state, heading, index, rate or path")
        key = (state, heading, index)
        if key in seen:
            raise ValueError("Duplicate animation frame")
        seen.add(key)
        parts = Path(rel)
        if parts.is_absolute() or ".." in parts.parts or len(parts.parts) > 5:
            raise ValueError("Unsafe source path")
        source = (root / parts).resolve(strict=True)
        if not source.is_relative_to(root):
            raise ValueError("Source escapes interchange root")
        with Image.open(source) as opened:
            if opened.format != "PNG" or opened.mode != "RGBA":
                raise ValueError("Only transparent RGBA PNG frames accepted")
            if not 1 <= opened.width <= 512 or not 1 <= opened.height <= 512:
                raise ValueError("Unbounded source frame")
            rgba = opened.copy()
        bounds = rgba.getchannel("A").getbbox()
        if bounds is None:
            raise ValueError("Empty source frame")
        pivot = item.get("pivot", [rgba.width // 2, rgba.height - 1])
        if (not isinstance(pivot, list) or len(pivot) != 2
                or any(type(v) is not int for v in pivot)
                or not 0 <= pivot[0] < rgba.width or not 0 <= pivot[1] < rgba.height):
            raise ValueError("Invalid pivot")
        validated.append((item, rgba, bounds, pivot, sha(source)))

    # All validation completes before a single output is written.
    output.mkdir(parents=True, exist_ok=True)
    pages = []
    entries = []
    x = y = GAP
    row_height = 0

    for item, rgba, bounds, pivot, digest in sorted(
            validated, key=lambda record: (record[0]["state"], record[0]["heading"], record[0]["frame"])):
        crop = rgba.crop(bounds)
        w, h = crop.size
        if w + 2 * GAP > page_size or h + 2 * GAP > page_size:
            raise ValueError("Frame cannot fit page")
        if not pages:
            pages.append(Image.new("RGBA", (page_size, page_size)))
        if x + w + GAP > page_size:
            x, y, row_height = GAP, y + row_height + GAP, 0
        if y + h + GAP > page_size:
            if len(pages) == 8:
                raise ValueError("Page budget exceeded")
            pages.append(Image.new("RGBA", (page_size, page_size)))
            x = y = GAP
            row_height = 0
        pages[-1].alpha_composite(crop, (x, y))
        entries.append({"asset_id": asset_id, "state": item["state"],
                        "heading": item["heading"], "frame": item["frame"],
                        "fps": item["fps"], "loop": item.get("loop", True),
                        "page": len(pages) - 1, "region": [x, y, w, h],
                        "source_size": list(rgba.size),
                        "trim_offset": [bounds[0], bounds[1]],
                        "pivot_source_px": pivot, "pivot_world_verified": False,
                        "source_sha256": digest})
        x += w + GAP
        row_height = max(row_height, h)

    outputs = []
    for number, image in enumerate(pages):
        filename = f"sheet_{number:04d}.png"
        dest = output / filename
        image.save(dest, optimize=True)
        outputs.append({"file": filename, "sha256": sha(dest),
                        "width": page_size, "height": page_size})
    manifest = {"schema_version": 1, "origin": "sprite-gen-offline-export",
                "asset_id": asset_id, "pages": outputs, "frames": entries,
                "status": "TECHNICAL_ANIMATION_CANDIDATE", "golden_approved": False,
                "f12_world_scale_approved": False, "gameplay_integrated": False,
                "iphone_verified": False}
    (output / "sprite_sheet_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--page-size", default=1024, type=int)
    args = parser.parse_args()
    result = bridge(args.spec, args.output, args.page_size)
    print("FOUNDRY_SPRITE_GEN_BRIDGE", result["asset_id"], len(result["frames"]), len(result["pages"]))


if __name__ == "__main__":
    main()
