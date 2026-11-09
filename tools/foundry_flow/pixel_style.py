"""Make original Blender directional renders into reviewable pixel-style frames.

This is a deterministic offline *style candidate* step, not an AI image maker
or a claim that the actual geometry/material quality meets Golden 40. The
original editable 3D source and full-resolution frames remain independent.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image


def process(plan: dict, raw_views: Path, output: Path, logical_size: int = 64) -> dict:
    if logical_size not in (48, 64):
        raise ValueError("Unsupported Golden-style logical image size")
    if plan.get("schema_version") != 1 or plan.get("golden_approved") is not False:
        raise ValueError("Untrusted Blender plan")
    outputs = []
    for item in plan["selected"]:
        ident = item["asset_id"]
        src = raw_views / ident
        metadata = json.loads((src / "render_metadata.json").read_text())
        if (metadata.get("asset_id") != ident
                or metadata.get("source_sha256") != item["glb_sha256"]
                or metadata.get("engine") != "CYCLES_CPU"
                or metadata.get("frames") != 16
                or metadata.get("golden_approved") is not False
                or metadata.get("resolution") not in (192, 256)):
            raise ValueError(f"Untrusted source render: {ident}")
        size = metadata["resolution"]
        if size % logical_size:
            raise ValueError("Native pixel scale must divide render canvas")
        out = output / ident
        out.mkdir(parents=True, exist_ok=True)
        interchange = {"schema_version": 1, "asset_id": ident, "frames": []}
        for heading in range(16):
            source = src / f"{heading:02d}.png"
            with Image.open(source) as im:
                if im.format != "PNG" or im.size != (size, size):
                    raise ValueError(f"Invalid original frame: {ident}/{heading}")
                rgba = im.convert("RGBA")
            if not rgba.getchannel("A").getbbox():
                raise ValueError(f"Empty original frame: {ident}/{heading}")
            # BOX produces a native logical image; nearest-neighbor display
            # preserves intentional pixel groups, never bicubic smoothing.
            logical = rgba.resize((logical_size, logical_size), Image.Resampling.BOX)
            styled = logical.resize((size, size), Image.Resampling.NEAREST)
            if not styled.getchannel("A").getbbox():
                raise ValueError(f"Empty pixel-style frame: {ident}/{heading}")
            filename = f"{heading:02d}.png"
            styled.save(out / filename, optimize=True)
            interchange["frames"].append({
                "state": "static", "heading": heading, "frame": 0,
                "fps": 1, "png": filename,
                "pivot": [size // 2, size // 2], "loop": True,
            })
        (out / "interchange.json").write_text(json.dumps(interchange, indent=2) + "\n")
        (out / "render_metadata.json").write_text(json.dumps({
            **metadata,
            "pixel_style_preset": "GOLDEN40_PIXEL_REALISM_CANDIDATE_V1",
            "logical_canvas_px": logical_size,
            "pixel_display_scale": size // logical_size,
            "f11_approved": False,
            "f12_world_scale_approved": False,
            "golden_approved": False,
        }, indent=2) + "\n")
        outputs.append({"asset_id": ident, "view_count": 16, "logical_canvas_px": logical_size})
    return {"style_candidates": outputs, "golden_approved": False}


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--plan", type=Path, required=True)
    p.add_argument("--raw-views", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--logical-size", type=int, default=64)
    a = p.parse_args()
    report = process(json.loads(a.plan.read_text()), a.raw_views, a.output, a.logical_size)
    print("FOUNDRY_PIXEL_STYLE", len(report["style_candidates"]))


if __name__ == "__main__":
    main()
