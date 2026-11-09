"""Verify and stage bounded sheet pages on an isolated, non-Golden branch."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
from pathlib import Path

from PIL import Image

from pack import _state, sha


def stage(source: Path, destination: Path) -> int:
    report = json.loads((source / "batch_report.json").read_text())
    manifest = json.loads((source / "sprite_sheet_manifest.json").read_text())
    next_state = json.loads((source / "next_state.json").read_text())
    ident = report.get("run_id")
    if (not isinstance(ident, str) or not re.fullmatch(r"[0-9]{1,18}", ident)
            or manifest.get("run_id") != ident or next_state.get("last_run_id") != ident
            or report.get("golden_approved") is not False
            or manifest.get("golden_approved") is not False
            or report.get("technical_candidate_only") is not True):
        raise ValueError("Untrusted sheet production report")
    prior_path = destination / "foundry_sheets/state.json"
    prior = json.loads(prior_path.read_text()) if prior_path.exists() else None
    old = _state(prior)
    new = _state(next_state)
    sources = manifest.get("sources")
    pages = manifest.get("pages")
    frames = manifest.get("frames")
    if (not isinstance(sources, list) or not isinstance(pages, list)
            or not isinstance(frames, list) or len(sources) != report.get("batch_count")
            or len(sources) > 80 or len(frames) != 16 * len(sources)
            or new != old + [{"asset_id": x["asset_id"], "atlas_sha256": x["atlas_sha256"]}
                              for x in sources]
            or len(new) != report.get("completed_total")
            or len(pages) != report.get("page_count") or len(pages) > 32):
        raise ValueError("Stale sheet cursor or invalid production counts")
    target = destination / "foundry_sheets/batches" / ident
    if target.exists():
        raise ValueError("Never overwrite an immutable published sheet batch")
    # Verify all source page bytes and region bounds before writing anything.
    for i, page in enumerate(pages):
        name = f"sheet_{i:04d}.png"
        if page.get("file") != name or page.get("sha256") != sha(source / name):
            raise ValueError("Sprite sheet page digest mismatch")
    for entry in frames:
        page = entry.get("page")
        rect = entry.get("region")
        if (type(page) is not int or not 0 <= page < len(pages)
                or not isinstance(rect, list) or len(rect) != 4
                or any(type(v) is not int or v < 0 for v in rect)
                or rect[2] == 0 or rect[3] == 0
                or rect[0] + rect[2] > pages[page]["width"]
                or rect[1] + rect[3] > pages[page]["height"]):
            raise ValueError("Frame region outside sprite page")
    inventory = None
    if "inventory_sheet_manifest" in manifest:
        if manifest["inventory_sheet_manifest"] != "inventory_sheet_manifest.json":
            raise ValueError("Unknown inventory sheet manifest path")
        inventory = json.loads((source / "inventory_sheet_manifest.json").read_text())
        sheets = inventory.get("pages", [])
        entries = inventory.get("entries", [])
        per_page = inventory.get("items_per_page")
        if (inventory.get("run_id") != ident
                or inventory.get("schema_version") != 1
                or inventory.get("golden_approved") is not False
                or inventory.get("status") != "TECHNICAL_INVENTORY_SHEET_CANDIDATE"
                or per_page not in (40, 48, 64)
                or not isinstance(sheets, list) or not isinstance(entries, list)
                or inventory.get("entry_count") != len(sources)
                or len(entries) != len(sources)
                or len(sheets) * per_page != len(sources)
                or report.get("inventory_page_count") != len(sheets)
                or report.get("inventory_items_per_page") != per_page
                or [x.get("asset_id") for x in entries] != [x["asset_id"] for x in sources]):
            raise ValueError("Invalid 40+ inventory sheet identity or page count")
        source_hashes = {x["asset_id"]: x["atlas_sha256"] for x in sources}
        for i, sheet in enumerate(sheets):
            name = f"inventory_sheet_{i:04d}.png"
            path = source / name
            if (sheet.get("file") != name or sheet.get("asset_count") != per_page
                    or sheet.get("width") != 2048
                    or sheet.get("height") != 256 * ((per_page + 7) // 8)
                    or sheet.get("sha256") != sha(path)):
                raise ValueError("40+ inventory sheet page digest mismatch")
            with Image.open(path) as image:
                if image.format != "PNG" or image.mode != "RGBA" or image.size != (sheet["width"], sheet["height"]):
                    raise ValueError("Invalid inventory image format")
                for index, entry in enumerate(entries[i * per_page:(i + 1) * per_page]):
                    rect = entry.get("region")
                    cell = entry.get("cell_region")
                    if (entry.get("page") != i or entry.get("heading") != 2
                            or entry.get("source_atlas_sha256") != source_hashes.get(entry["asset_id"])
                            or not isinstance(rect, list) or len(rect) != 4
                            or not isinstance(cell, list) or len(cell) != 4
                            or cell != [(index % 8) * 256, (index // 8) * 256, 256, 256]
                            or any(type(x) is not int for x in rect)
                            or rect[2] <= 0 or rect[3] <= 0
                            or rect[0] < cell[0] or rect[1] < cell[1]
                            or rect[0] + rect[2] > cell[0] + cell[2]
                            or rect[1] + rect[3] > cell[1] + cell[3]):
                        raise ValueError("Inventory item region outside assigned cell")
                    cut = image.crop((rect[0], rect[1], rect[0] + rect[2], rect[1] + rect[3]))
                    if hashlib.sha256(cut.tobytes()).hexdigest() != entry.get("rgba_pixel_sha256"):
                        raise ValueError("Inventory sprite pixel digest mismatch")
    elif report.get("inventory_page_count", 0) != 0:
        raise ValueError("Missing required 40+ inventory sheet manifest")
    if not sources:
        return 0
    target.mkdir(parents=True)
    for page in pages:
        shutil.copyfile(source / page["file"], target / page["file"])
    if inventory is not None:
        for page in inventory["pages"]:
            shutil.copyfile(source / page["file"], target / page["file"])
        shutil.copyfile(source / "inventory_sheet_manifest.json", target / "inventory_sheet_manifest.json")
    for name in ("sprite_sheet_manifest.json", "batch_report.json"):
        shutil.copyfile(source / name, target / name)
    prior_path.parent.mkdir(parents=True, exist_ok=True)
    prior_path.write_text(json.dumps(next_state, indent=2) + "\n")
    print("FOUNDRY_SHEETS_STAGED", len(sources), len(new))
    return len(sources)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--source", required=True, type=Path)
    p.add_argument("--destination", required=True, type=Path)
    a = p.parse_args()
    stage(a.source, a.destination)


if __name__ == "__main__":
    main()
