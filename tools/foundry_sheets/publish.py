"""Verify and stage bounded sheet pages on an isolated, non-Golden branch."""
from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path

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
            or len(sources) > 8 or len(frames) != 16 * len(sources)
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
    if not sources:
        return 0
    target.mkdir(parents=True)
    for page in pages:
        shutil.copyfile(source / page["file"], target / page["file"])
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
