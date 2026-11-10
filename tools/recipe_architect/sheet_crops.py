"""Extract bounded, SHA-verified founder sheet *references* for local VLMs.

The sheet position is a reference number, NEVER an authoritative asset ID.
Output crops are private technical inputs, not approved sprites or textures.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image

from tools.foundry_reference_sheets.build import SOURCE_DIR, build
from tools.foundry_reference_sheets.plan import plan

from .batch import fresh_output
from .pilot import dump
from .sheet_isolation import SheetIsolator


def border_risk(image: Image.Image) -> dict:
    """Conservative warning, not object segmentation or background removal.

    White JPEG sheet backgrounds may contain cropped adjacent objects at the
    grid boundary. Only warn; do not delete any uncertain reference pixels.
    """
    rgb = image.convert("RGB")
    width, height = rgb.size
    strips = {
        "left": ((x, y) for x in range(min(2, width)) for y in range(height)),
        "right": ((x, y) for x in range(max(0, width - 2), width) for y in range(height)),
        "top": ((x, y) for y in range(min(2, height)) for x in range(width)),
        "bottom": ((x, y) for y in range(max(0, height - 2), height) for x in range(width)),
    }
    counts = {edge: sum(min(rgb.getpixel(xy)) < 225 for xy in coords)
              for edge, coords in strips.items()}
    return {"nonwhite_border_pixels": counts,
            "possible_neighbor_or_truncation": any(count >= 3 for count in counts.values()),
            "interpretation": "unverified_JPEG_background_and_border_content_not_a_mask"}


def extract(source_dir: Path, *, start: int, count: int, out: Path) -> dict:
    fresh_output(out)
    # The existing F09 intake verifies all 8 original sheet files against
    # checked-in manifests, validates gaps and preserves per-slot coordinates.
    records, intake = build(source_dir)
    selected = plan(records, start, count)
    if intake["golden_3d_approved"] != 0 or selected["production_model_admitted"]:
        raise ValueError("unreviewed intake must not claim admission")
    crops = []
    isolators: dict[str, SheetIsolator] = {}
    sheet_specs = {Path(s["file"]).name: s for s in
                   json.loads((source_dir / "sheets_manifest_v1.json").read_text())["sheets"]}
    for job in selected["jobs"]:
        # The manifest's public *relative* path is not a filesystem authority.
        # Only the verified basename inside the pinned sheets/ directory is used.
        source = source_dir / "sheets" / Path(job["sheet_path"]).name
        if not source.is_file() or hashlib.sha256(source.read_bytes()).hexdigest() != job["sheet_sha256"]:
            raise ValueError("reference sheet drift")
        spec = sheet_specs[source.name]
        with Image.open(source) as sheet:
            box = job["cell_box_xyxy"]
            old_cell = sheet.crop(tuple(box))
            risk = border_risk(old_cell)
            if source.name not in isolators:
                isolators[source.name] = SheetIsolator(sheet, rows=spec["rows"],
                                                       columns=spec["columns"])
        crop, isolated_qa = isolators[source.name].isolate(job["cell_row"], job["cell_column"])
        if crop.width < 16 or crop.height < 16 or crop.width > 2048 or crop.height > 2048:
            raise ValueError("isolated crop outside bounded image dimensions")
        file_name = f"ref_{job['sheet_index']:04d}.png"
        location = out / "crops" / file_name
        location.parent.mkdir(parents=True, exist_ok=True)
        crop.save(location, format="PNG")
        crops.append({
            "reference_id": job["reference_id"],
            "sheet_position": job["sheet_index"],
            "canonical_asset_id": None,
            "source_sheet_sha256": job["sheet_sha256"],
            "crop_sha256": hashlib.sha256(location.read_bytes()).hexdigest(),
            "crop_file": f"crops/{file_name}",
            "cell_box_xyxy": job["cell_box_xyxy"],
            "working_label_unverified": job["working_label"],
            "family_suggestion_unverified": job["model_family_suggestion"],
            "source_rights": "founder_original_pending_review",
            "crop_boundary_qa": risk,
            "isolated_crop_qa": isolated_qa,
            "review_status": ("ISOLATED_PENDING_SEMANTIC_RIGHTS_AND_GEOMETRY_REVIEW"
                              if isolated_qa["safe_for_unattended_proposal"] else
                              "NEEDS_MANUAL_ISOLATION_AND_SEMANTIC_REVIEW"),
            "golden_approved": False,
        })
    result = {
        "schema": "last-light.local-vlm-sheet-crops.v1",
        "source_collection_id": intake["collection_id"],
        "input_start": start, "requested": count, "extracted": len(crops),
        "original_pixels_inspected_by_vlm": False,
        "geometry_created": False, "founder_golden_approved": False,
        "output_crops_are_private_reference_only": True,
        "crops_with_possible_border_contamination": sum(
            crop["crop_boundary_qa"]["possible_neighbor_or_truncation"] for crop in crops),
        "isolated_crops_eligible_for_local_vlm": sum(
            crop["isolated_crop_qa"]["safe_for_unattended_proposal"] for crop in crops),
        "whole_sheet_isolation_used": True,
        "crops": crops,
    }
    dump(out / "crop_manifest.json", result)
    return result


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--source-dir", type=Path, default=SOURCE_DIR)
    p.add_argument("--start", type=int, default=1)
    p.add_argument("--count", type=int, choices=(10, 20, 40, 50, 60, 100), default=10)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    result = extract(args.source_dir, start=args.start, count=args.count, out=args.out)
    print("LL_FOUNDER_SHEET_CROPS", result["extracted"], "CANDIDATES_ONLY", flush=True)


if __name__ == "__main__":
    main()
