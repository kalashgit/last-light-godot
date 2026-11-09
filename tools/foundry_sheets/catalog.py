"""Lossless 40-item inventory sprite pages from admitted technical 3D renders.

These sheets contain one 45-degree thumbnail for each DISTINCT original asset.
The separate runtime sheets still contain all sixteen headings for each asset.
No page is padded with invented items or represented as Golden-approved.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from PIL import Image


CELL = 256
COLUMNS = 8
HEADING = 2
PAGE_ITEMS = 40


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def build(folders: list[tuple[Path, int, str]], output: Path,
          run_id: str, items_per_page: int = PAGE_ITEMS) -> dict:
    """Build complete pages only; ``size`` is the original 4x4 cell width."""
    if items_per_page not in (40, 48, 64):
        raise ValueError("Inventory pages must contain 40, 48 or 64 distinct assets")
    if len(folders) % items_per_page:
        raise ValueError("Partial inventory page would misrepresent the 40+ goal")
    if len({folder.name for folder, _, _ in folders}) != len(folders):
        raise ValueError("Duplicate inventory asset")
    output.mkdir(parents=True, exist_ok=True)
    pages: list[dict] = []
    entries: list[dict] = []
    seen_pixels: dict[tuple[int, int, str], str] = {}
    rows = (items_per_page + COLUMNS - 1) // COLUMNS
    for page_index, start in enumerate(range(0, len(folders), items_per_page)):
        page = Image.new("RGBA", (CELL * COLUMNS, CELL * rows), (0, 0, 0, 0))
        chunk = folders[start:start + items_per_page]
        for local_index, (folder, size, source_sha) in enumerate(chunk):
            if size not in (128, 192, 256):
                raise ValueError("Unapproved original frame resolution")
            col, row = HEADING % 4, HEADING // 4
            with Image.open(folder / "atlas_16_headings.png") as source:
                raw = source.convert("RGBA")
                frame = raw.crop((4 + col * (size + 4), 4 + row * (size + 4),
                                  4 + col * (size + 4) + size,
                                  4 + row * (size + 4) + size))
            bounds = frame.getchannel("A").getbbox()
            if bounds is None:
                raise ValueError(f"Empty 45-degree inventory view: {folder.name}")
            cut = frame.crop(bounds)
            pixel_sha = hashlib.sha256(cut.tobytes()).hexdigest()
            visual_key = (cut.width, cut.height, pixel_sha)
            if visual_key in seen_pixels:
                raise ValueError(
                    f"Duplicate visual sprite: {folder.name} matches {seen_pixels[visual_key]}; "
                    "semantic review is required before counting it as a distinct item"
                )
            seen_pixels[visual_key] = folder.name
            x = (local_index % COLUMNS) * CELL + (CELL - size) // 2 + bounds[0]
            y = (local_index // COLUMNS) * CELL + (CELL - size) // 2 + bounds[1]
            page.alpha_composite(cut, (x, y))
            entries.append({
                "asset_id": folder.name,
                "page": page_index,
                "heading": HEADING,
                "direction_degrees": 45.0,
                "cell": [local_index % COLUMNS, local_index // COLUMNS],
                "cell_region": [(local_index % COLUMNS) * CELL,
                                (local_index // COLUMNS) * CELL, CELL, CELL],
                "region": [x, y, cut.width, cut.height],
                "source_size": [size, size],
                "trim_offset": [bounds[0], bounds[1]],
                "source_atlas_sha256": source_sha,
                "rgba_pixel_sha256": pixel_sha,
                "pivot_world_verified": False,
            })
        filename = f"inventory_sheet_{page_index:04d}.png"
        file_path = output / filename
        page.save(file_path, optimize=True)
        pages.append({"file": filename, "width": page.width, "height": page.height,
                      "asset_count": len(chunk), "sha256": _sha(file_path)})
    manifest = {
        "schema_version": 1, "run_id": str(run_id), "pages": pages,
        "entries": entries, "items_per_page": items_per_page,
        "entry_count": len(entries), "columns": COLUMNS, "cell_px": CELL,
        "status": "TECHNICAL_INVENTORY_SHEET_CANDIDATE",
        "f11_material_approved": False, "f12_world_scale_approved": False,
        "golden_approved": False, "gameplay_integrated": False,
    }
    (output / "inventory_sheet_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest
