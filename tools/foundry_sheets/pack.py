"""Bounded, deterministic 16-heading sprite-sheet packing for Foundry candidates.

The input is the existing F12 *technical* 4x4 atlas, never a Golden asset.
Each transparent frame is trimmed and packed without modifying pixel colors.
Animation states can be added as separate verified inputs in a later contract.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

from PIL import Image

IDENT = re.compile(r"ll_[a-z0-9_]{2,90}\Z")
RUN = re.compile(r"[0-9]{1,18}\Z")
FRAME_COUNT = 16
GAP = 2


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _read_candidate(folder: Path) -> tuple[dict, int]:
    ident = folder.name
    if not IDENT.fullmatch(ident):
        raise ValueError("Invalid canonical asset ID")
    manifest = json.loads((folder / "manifest.json").read_text())
    atlas_path = folder / "atlas_16_headings.png"
    if (manifest.get("asset_id") != ident or manifest.get("views") != FRAME_COUNT
            or manifest.get("status") != "TECHNICAL_SPRITE_CANDIDATE"
            or manifest.get("golden_approved") is not False
            or manifest.get("f12_world_scale_approved") is not False
            or manifest.get("atlas_sha256") != sha(atlas_path)):
        raise ValueError(f"Untrusted technical sprite candidate: {ident}")
    with Image.open(atlas_path) as image:
        image.verify()
    with Image.open(atlas_path) as image:
        w, h = image.size
    if w != h or (w - 20) % 4 or (w - 20) // 4 not in (128, 192, 256):
        raise ValueError(f"Invalid 4x4 technical source layout: {ident}")
    return manifest, (w - 20) // 4


def _state(state: dict | None) -> list[dict]:
    if state is None:
        return []
    if state.get("schema_version") != 1 or state.get("golden_approved") is not False:
        raise ValueError("Untrusted sprite sheet cursor")
    completed = state.get("completed")
    if (not isinstance(completed, list) or len(completed) > 20000
            or any(not isinstance(item, dict) or not IDENT.fullmatch(str(item.get("asset_id", "")))
                   or not re.fullmatch(r"[a-f0-9]{64}", str(item.get("atlas_sha256", "")))
                   for item in completed)):
        raise ValueError("Invalid sprite sheet cursor entries")
    if len({item["asset_id"] for item in completed}) != len(completed):
        raise ValueError("Duplicate sprite sheet cursor entries")
    return completed


def pack(candidate_root: Path, output: Path, state: dict | None = None,
         batch_size: int = 4, page_size: int = 1024, run_id: str = "1") -> dict:
    if not isinstance(batch_size, int) or not 1 <= batch_size <= 8:
        raise ValueError("Batch must contain between 1 and 8 assets")
    if page_size not in (1024, 2048) or not RUN.fullmatch(str(run_id)):
        raise ValueError("Unapproved page size or run ID")
    completed = _state(state)
    indexed = {entry["asset_id"]: entry["atlas_sha256"] for entry in completed}
    candidates = sorted(d for d in candidate_root.iterdir()
                        if d.is_dir() and IDENT.fullmatch(d.name))
    for folder in candidates:
        if folder.name in indexed:
            source = folder / "atlas_16_headings.png"
            if sha(source) != indexed[folder.name]:
                raise ValueError(f"Previously published source was modified: {folder.name}")
    selected = [folder for folder in candidates if folder.name not in indexed][:batch_size]
    output.mkdir(parents=True, exist_ok=True)
    pages: list[Image.Image] = []
    page_index, cursor_x, cursor_y, row_height = -1, GAP, GAP, 0
    frames = []
    inventory = []

    def new_page() -> None:
        nonlocal page_index, cursor_x, cursor_y, row_height
        if len(pages) >= 32:
            raise ValueError("Atlas pages exceed bounded batch budget")
        pages.append(Image.new("RGBA", (page_size, page_size), (0, 0, 0, 0)))
        page_index = len(pages) - 1
        cursor_x, cursor_y, row_height = GAP, GAP, 0

    for folder in selected:
        source_record, size = _read_candidate(folder)
        source_atlas = folder / "atlas_16_headings.png"
        inventory.append({"asset_id": folder.name, "atlas_sha256": sha(source_atlas),
                          "source_glb_sha256": source_record["source_glb_sha256"]})
        with Image.open(source_atlas) as opened:
            atlas = opened.convert("RGBA")
            for heading in range(FRAME_COUNT):
                col, row = heading % 4, heading // 4
                sprite = atlas.crop((4 + col * (size + 4), 4 + row * (size + 4),
                                     4 + col * (size + 4) + size, 4 + row * (size + 4) + size))
                bounds = sprite.getchannel("A").getbbox()
                if bounds is None:
                    raise ValueError(f"Empty direction {folder.name}/{heading}")
                trim = sprite.crop(bounds)
                width, height = trim.size
                if page_index < 0:
                    new_page()
                if cursor_x + width + GAP > page_size:
                    cursor_x = GAP
                    cursor_y += row_height + GAP
                    row_height = 0
                if cursor_y + height + GAP > page_size:
                    new_page()
                pages[page_index].alpha_composite(trim, (cursor_x, cursor_y))
                frames.append({"asset_id": folder.name, "state": "static", "heading": heading,
                               "direction_degrees": heading * 22.5, "frame": 0,
                               "page": page_index, "region": [cursor_x, cursor_y, width, height],
                               "source_size": [size, size], "trim_offset": [bounds[0], bounds[1]],
                               "pivot_source_px": [size // 2, size // 2],
                               "pivot_world_verified": False})
                cursor_x += width + GAP
                row_height = max(row_height, height)

    page_records = []
    for i, page in enumerate(pages):
        name = f"sheet_{i:04d}.png"
        path = output / name
        page.save(path, optimize=True)
        page_records.append({"file": name, "width": page_size, "height": page_size,
                             "sha256": sha(path)})
    manifest = {"schema_version": 1, "run_id": str(run_id), "pages": page_records,
                "frames": frames, "sources": inventory, "frames_per_asset": FRAME_COUNT,
                "coordinate_contract": "Godot AtlasTexture region [x,y,w,h] with trim_offset restored",
                "f11_material_approved": False, "f12_world_scale_approved": False,
                "gameplay_integrated": False, "iphone_verified": False,
                "golden_approved": False, "status": "TECHNICAL_SPRITE_SHEET_CANDIDATE"}
    (output / "sprite_sheet_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    new_state = {"schema_version": 1, "golden_approved": False,
                 "completed": completed + [{"asset_id": x["asset_id"],
                                            "atlas_sha256": x["atlas_sha256"]} for x in inventory],
                 "last_run_id": str(run_id)}
    (output / "next_state.json").write_text(json.dumps(new_state, indent=2) + "\n")
    report = {"schema_version": 1, "run_id": str(run_id), "batch_count": len(inventory),
              "page_count": len(pages), "frame_count": len(frames),
              "completed_total": len(new_state["completed"]),
              "unprocessed_visible": len(candidates) - len(new_state["completed"]),
              "golden_approved": False, "technical_candidate_only": True}
    (output / "batch_report.json").write_text(json.dumps(report, indent=2) + "\n")
    print("FOUNDRY_SHEETS_PACKED", len(inventory), len(frames), len(pages))
    return report


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--candidates", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    p.add_argument("--state", type=Path)
    p.add_argument("--batch-size", type=int, default=4)
    p.add_argument("--page-size", type=int, default=1024)
    p.add_argument("--run-id", default="1")
    a = p.parse_args()
    pack(a.candidates, a.output,
         json.loads(a.state.read_text()) if a.state and a.state.exists() else None,
         a.batch_size, a.page_size, a.run_id)


if __name__ == "__main__":
    main()
