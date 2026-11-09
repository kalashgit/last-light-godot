"""Offline alpha cleanup, 64x64 icons and diagnostic directional atlases.

Input must be real rendered transparent PNGs from own independently authored
GLB source. Emits review-only artifacts; never feeds the R03 production queue.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image

from tools.foundry_original_23.contract import DEFAULT_MANIFEST, MASTER, check_manifest


def icon_from_frame(frame: Image.Image, size: int = 64, pad: int = 3) -> Image.Image:
    if size != 64 or pad < 3:
        raise ValueError("Golden V2 technical inventory contract must be 64px with padding")
    raw = frame.convert("RGBA")
    bbox = raw.getchannel("A").getbbox()
    if bbox is None:
        raise ValueError("Transparent render contained no mesh pixels")
    cropped = raw.crop(bbox)
    w, h = cropped.size
    # Downsample Blender antialiasing, then preserve deliberate pixel-grid shape.
    factor = min((size - 2 * pad) / w, (size - 2 * pad) / h)
    dimensions = (max(1, int(w * factor)), max(1, int(h * factor)))
    sprite = cropped.resize(dimensions, Image.Resampling.LANCZOS)
    output = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    output.alpha_composite(sprite, ((size - dimensions[0]) // 2, (size - dimensions[1]) // 2))
    return output


def inspect_alpha(img: Image.Image) -> dict:
    if img.mode != "RGBA":
        raise ValueError("PNG must be RGBA with transparent background")
    alpha = img.getchannel("A")
    bbox = alpha.getbbox()
    if not bbox:
        raise ValueError("Sprite silhouette is entirely empty")
    if bbox[0] < 2 or bbox[1] < 2 or bbox[2] > img.width - 2 or bbox[3] > img.height - 2:
        raise ValueError("Sprite silhouette touches safety padding")
    pixels = list(alpha.get_flattened_data()) if hasattr(alpha, "get_flattened_data") else list(alpha.getdata())
    return {"bbox": bbox, "opaque_or_antialiased_pixels": sum(a > 0 for a in pixels),
            "transparent_pixels": sum(a == 0 for a in pixels),
            "alpha_present": True}


def contact_sheet(icons: list[Image.Image]) -> Image.Image:
    # Review contact sheet is NOT a 40-item production atlas. Real 40-sheet
    # remains owned by tools/foundry_sheets/pack.py's admitted-only queue.
    columns = 5
    rows = (len(icons) + columns - 1) // columns
    sheet = Image.new("RGBA", (columns * 64, rows * 64), (0, 0, 0, 0))
    for j, icon in enumerate(icons):
        sheet.alpha_composite(icon, ((j % columns) * 64, (j // columns) * 64))
    return sheet


def create_previews(manifest: dict, renders: Path, output: Path) -> dict:
    verdict = check_manifest(manifest, MASTER)
    if verdict["errors"]:
        raise ValueError("Untrusted original-authoring manifest")
    output.mkdir(parents=True, exist_ok=True)
    selected = []
    icons = []
    seen_icons = {}
    for asset in manifest["assets"]:
        ident = asset["asset_id"]
        source = renders / ident
        if not source.exists():
            continue
        metadata = json.loads((source / "render_metadata.json").read_text())
        if metadata.get("asset_id") != ident or metadata.get("frames") != 16 or metadata.get("golden_approved") is not False:
            raise ValueError("Directional source missing technical/non-Golden provenance: " + ident)
        frames = []
        for heading in range(16):
            frame = source / f"{heading:02d}.png"
            if not frame.is_file():
                raise ValueError("Missing 16-direction source frame: " + str(frame))
            with Image.open(frame) as loaded:
                if loaded.mode != "RGBA" or not loaded.getchannel("A").getbbox():
                    raise ValueError("Bad transparency/empty direction: " + str(frame))
                frames.append(loaded.copy())
        dest = output / ident
        dest.mkdir(parents=True, exist_ok=True)
        icon = icon_from_frame(frames[2])
        check = inspect_alpha(icon)
        raw_pixel_sha = hashlib.sha256(icon.tobytes()).hexdigest()
        if raw_pixel_sha in seen_icons:
            raise ValueError("Cross-ID duplicate sprite artwork requires originality review: " + ident + " / " + seen_icons[raw_pixel_sha])
        seen_icons[raw_pixel_sha] = ident
        heading_pixels = {hashlib.sha256(f.tobytes()).hexdigest() for f in frames}
        if len(heading_pixels) < 2:
            raise ValueError("All 16 world headings are pixel-identical: " + ident)
        icon.save(dest / "inventory_64.png", optimize=True)
        icons.append(icon)
        # The directional page is explicit 4x4 PNG; the 16 individual source
        # frames stay in the uploaded render artifact, with independent hashes.
        tile = frames[0].size
        sheet = Image.new("RGBA", (tile[0] * 4, tile[1] * 4), (0, 0, 0, 0))
        for heading, frame in enumerate(frames):
            if frame.size != tile:
                raise ValueError("Direction resolution drift: " + ident)
            sheet.alpha_composite(frame, ((heading % 4) * tile[0], (heading // 4) * tile[1]))
        sheet.save(dest / "directions_16_technical.png", optimize=True)
        selected.append({
            "asset_id": ident, "rendered_headings": 16, "inventory_size_px": [64, 64],
            "inventory_alpha_qa": check,
            "unique_direction_frame_count": len(heading_pixels),
            "inventory_pixel_sha256": raw_pixel_sha,
            "preview_sha256": hashlib.sha256((dest / "inventory_64.png").read_bytes()).hexdigest(),
            "source_glb_sha256": metadata["source_sha256"],
            "artistic_originality_review": "PENDING_HUMAN_REVIEW",
            "f12_gameplay_scale_accepted": False, "godot_tested": False,
            "founder_golden_approved": False, "production_sheet_admitted": False,
            "visual_reviewer_scores": {
                "original_silhouette": None, "physical_materials": None,
                "upper_left_lighting": None, "pixel_treatment": None,
                "readable_at_32_48_64": None, "godot_world_consistency": None,
            },
        })
    if not selected:
        raise ValueError("No Blender-rendered original models available for preprocessing")
    contact_sheet(icons).save(output / "original_technical_review_contact.png")
    report = {"schema_version": 1, "batch_id": manifest["batch_id"],
              "asset_count": len(selected), "expected_original_assets": 23,
              "technical_previews": selected, "production_admission_count": 0,
              "forty_item_production_pages_created": 0,
              "visual_originality_qa_gate": "HUMAN_REVIEW_REQUIRED",
              "founder_golden_approved": False}
    (output / "technical_preview_qa.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    p.add_argument("--renders", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    opts = p.parse_args()
    result = create_previews(json.loads(opts.manifest.read_text()), opts.renders, opts.output)
    print("LL_TECHNICAL_PREVIEW_QA", result["asset_count"], "GOLDEN=0 PRODUCTION=0")


if __name__ == "__main__":
    main()
