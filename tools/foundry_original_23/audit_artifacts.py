"""Independent cross-window acceptance of *real* non-Golden Blender outputs.

This proves the 23 model/icon/16-direction artifacts exist and match source
hashes; it does not certify artistic originality, Godot or founder approval.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image

from tools.foundry_original_23.contract import DEFAULT_MANIFEST, EXPECTED_IDS, MASTER, check_manifest, checksum
from tools.foundry_original_23.postprocess import inspect_alpha, contact_sheet


def find_windows(root: Path) -> list[Path]:
    # Local extracted artifact parent or actions/download-artifact directory.
    windows = sorted([p for p in root.iterdir() if p.is_dir() and (p.name.startswith("window-") or p.name.startswith("original-23-review-window-"))])
    if len(windows) != 6:
        raise ValueError(f"Expected exactly six independently rendered windows, found {len(windows)}")
    return windows


def audit(root: Path, output: Path, manifest_path: Path = DEFAULT_MANIFEST) -> dict:
    doc = json.loads(manifest_path.read_text())
    verdict = check_manifest(doc, MASTER)
    if verdict["errors"]:
        raise ValueError("Pinned original Notion evidence is stale/untrusted")
    windows = find_windows(root)
    seen = {}
    seen_pixel = {}
    for window in windows:
        folders = [x for x in (window / "models").iterdir() if x.is_dir()]
        for folder in folders:
            ident = folder.name
            if ident not in EXPECTED_IDS or ident in seen:
                raise ValueError("Unknown or repeated canonical original asset ID: " + ident)
            source = folder / (ident + ".blend")
            glb = folder / (ident + ".glb")
            receipt = json.loads((folder / "authorship_receipt.json").read_text())
            if source.stat().st_size < 1000 or glb.stat().st_size < 1000:
                raise ValueError("Missing authored editable 3D source: " + ident)
            if receipt["asset_id"] != ident or receipt["blender_source_sha256"] != checksum(source) or receipt["glb_sha256"] != checksum(glb):
                raise ValueError("Source/GLB receipt hash mismatch: " + ident)
            if receipt.get("source_images_or_textures_imported") is not False or receipt.get("base_geometry_from_pz") is not False:
                raise ValueError("Third-party artwork or geometry forbidden: " + ident)
            for key in ("semantic_admitted", "f11_approved", "f12_approved", "godot_tested", "iphone_verified", "founder_golden_approved"):
                if receipt.get(key) is not False:
                    raise ValueError("Forged original-asset admission: " + ident + "." + key)
            image_path = window / "review" / ident / "inventory_64.png"
            with Image.open(image_path) as raw:
                if raw.size != (64, 64):
                    raise ValueError("Inventory art not 64x64: " + ident)
                icon = raw.convert("RGBA")
            inspect_alpha(icon)
            rgba = hashlib.sha256(icon.tobytes()).hexdigest()
            if rgba in seen_pixel:
                raise ValueError("Duplicate cross-ID original inventory sprite: " + ident + " and " + seen_pixel[rgba])
            seen_pixel[rgba] = ident
            rendered = window / "renders" / ident
            meta = json.loads((rendered / "render_metadata.json").read_text())
            if meta.get("frames") != 16 or meta.get("golden_approved") is not False or meta.get("source_sha256") != receipt["glb_sha256"]:
                raise ValueError("Technical directional render provenance mismatch: " + ident)
            frame_hashes = set()
            for i in range(16):
                with Image.open(rendered / f"{i:02d}.png") as heading:
                    if heading.mode != "RGBA" or heading.size != (192, 192) or not heading.getchannel("A").getbbox():
                        raise ValueError("Invalid world render pixel/alpha: " + ident + ":" + str(i))
                    frame_hashes.add(hashlib.sha256(heading.tobytes()).hexdigest())
            if len(frame_hashes) < 2:
                raise ValueError("Directional render degenerate, requires review: " + ident)
            seen[ident] = {"asset_id": ident, "blend_sha256": receipt["blender_source_sha256"],
                          "glb_sha256": receipt["glb_sha256"], "inventory_pixel_sha256": rgba,
                          "rendered_direction_count": 16, "unique_direction_count": len(frame_hashes),
                          "technical_preview_passed": True, "artistic_originality_approved": False,
                          "godot_approved": False, "founder_golden_approved": False}
    if set(seen) != set(EXPECTED_IDS) or len(seen) != 23:
        raise ValueError("All 23 canonical assets must have original Blender, GLB and sprite evidence; missing: " + str(sorted(set(EXPECTED_IDS) - set(seen))))
    output.mkdir(parents=True, exist_ok=True)
    icons = []
    for ident in EXPECTED_IDS:
        path = next(w / "review" / ident / "inventory_64.png" for w in windows if (w / "review" / ident / "inventory_64.png").exists())
        with Image.open(path) as icon:
            icons.append(icon.convert("RGBA"))
    contact_sheet(icons).save(output / "all_23_original_technical_previews.png")
    report = {"batch_id": doc["batch_id"], "original_meshes": 23,
              "verified_glbs": 23, "inventory_64_rgba": 23,
              "directional_frames": 23 * 16, "distinct_original_assets": 23,
              "production_admitted_count": 0, "forty_item_release_sheets": 0,
              "f11_f12_art_acceptance": "PENDING", "godot_iphone_tests": "PENDING",
              "founder_golden_approved_count": 0, "status": "PASS_REAL_TECHNICAL_ARTIFACTS_ONLY",
              "assets": [seen[ident] for ident in EXPECTED_IDS]}
    (output / "all_23_technical_qa_report.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--windows", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    result = audit(args.windows, args.output)
    print("LL_ALL_23_REAL_ORIGINAL_ARTIFACTS_VERIFIED", result["original_meshes"],
          "16_DIRECTION_FRAMES", result["directional_frames"], "GOLDEN=0 RELEASE=0")


if __name__ == "__main__":
    main()
