#!/usr/bin/env python3
"""LAST LIGHT deterministic offline paperdoll atlas bridge.

Inputs are ORIGINAL transparent RGBA PNG frames plus a pinned source manifest.
No network, AI API, Copilot, Blender or asset-status promotion.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
import re
import tempfile
from pathlib import Path
from PIL import Image

SOURCE_SCHEMA = "last-light.paperdoll.frames.v1"
CATALOG_SCHEMA = "last-light.paperdoll.catalog.v1"
RUNTIME_SCHEMA = "last-light.paperdoll.v1"
SLOTS = ("body", "pants", "shirt", "backpack", "effects")
ID = re.compile(r"[a-z][a-z0-9_]{0,63}\Z")
SHA = re.compile(r"[0-9a-f]{64}\Z")
MAX_ENTRIES = 4096
MAX_ATLAS_SIDE = 4096


def digest(path: Path) -> str:
    hash_obj = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            hash_obj.update(block)
    return hash_obj.hexdigest()


def _require(ok, explanation: str):
    if not ok:
        raise ValueError(explanation)


def _safe_file(root: Path, relative: str) -> Path:
    _require(isinstance(relative, str) and relative and "\\" not in relative, "invalid relative file")
    name = Path(relative)
    _require(not name.is_absolute() and all(p not in (".", "..") for p in name.parts),
             "unsafe source path")
    _require(name.suffix == ".png", "only PNG layers are supported")
    target = (root / name).resolve()
    _require(target.is_relative_to(root.resolve()) and target.is_file(), "file missing or path escapes root")
    return target


def _shape(manifest: dict) -> tuple[list, dict, list, tuple, tuple]:
    _require(isinstance(manifest, dict) and manifest.get("schema") == SOURCE_SCHEMA, "source schema")
    _require(manifest.get("rig") == "ll_biped_v1" and manifest.get("tile_px") == [80, 40], "rig/tile mismatch")
    _require(manifest.get("golden_approved", False) is False, "source cannot declare Golden")
    _require(bool(ID.fullmatch(str(manifest.get("asset_id", "")))), "bad asset_id")
    headings = manifest.get("directions")
    _require(isinstance(headings, list) and len(headings) in (4, 8, 16), "direction count")
    _require(all(isinstance(h, str) and ID.fullmatch(h) for h in headings)
             and len(set(headings)) == len(headings), "invalid/duplicate headings")
    cell, pivot = manifest.get("frame_size"), manifest.get("pivot")
    _require(isinstance(cell, list) and len(cell) == 2
             and all(type(v) is int and 1 <= v <= 256 for v in cell), "invalid cell size")
    _require(isinstance(pivot, list) and len(pivot) == 2
             and all(type(v) is int and 0 <= v <= cell[i] for i, v in enumerate(pivot)),
             "invalid shared pivot")
    clips = manifest.get("animations")
    _require(isinstance(clips, dict) and "idle" in clips and 1 <= len(clips) <= 32, "missing clips")
    for name, spec in clips.items():
        _require(isinstance(name, str) and ID.fullmatch(name) and isinstance(spec, dict), "invalid clip")
        _require(type(spec.get("frames")) is int and 1 <= spec["frames"] <= 64, "invalid frame count")
        _require(type(spec.get("fps")) in (int, float) and 0 < spec["fps"] <= 60, "invalid fps")
        _require(type(spec.get("loop")) is bool, "missing loop flag")
        _require(cell[0] * spec["frames"] <= MAX_ATLAS_SIDE
                 and cell[1] * len(headings) <= MAX_ATLAS_SIDE, "atlas too large")
    records = manifest.get("frames")
    _require(isinstance(records, list) and 1 <= len(records) <= MAX_ENTRIES, "frame limit")
    return headings, clips, records, tuple(cell), tuple(pivot)


def pack_frames(source_dir: Path, destination: Path) -> dict:
    source_dir = source_dir.resolve()
    manifest_path = source_dir / "manifest.json"
    _require(manifest_path.is_file(), "missing manifest.json")
    raw = manifest_path.read_bytes()
    manifest = json.loads(raw.decode("utf-8"))
    headings, clips, records, cell, pivot = _shape(manifest)
    _require(not destination.exists(), "refuse to replace an existing atlas package")
    index = {}
    items = set()
    for record in records:
        _require(isinstance(record, dict), "invalid frame record")
        slot, item, clip, direction = (record.get(key) for key in ("slot", "item_id", "animation", "direction"))
        frame = record.get("frame")
        _require(slot in SLOTS and isinstance(item, str) and bool(ID.fullmatch(item)), "slot/item invalid")
        _require(clip in clips and direction in headings, "unknown direction or clip")
        _require(type(frame) is int and 0 <= frame < clips[clip]["frames"], "frame index invalid")
        key = (slot, item, clip, direction, frame)
        _require(key not in index, "duplicate source frame")
        path = _safe_file(source_dir, record.get("file", ""))
        sha = record.get("sha256")
        _require(isinstance(sha, str) and bool(SHA.fullmatch(sha)) and digest(path) == sha,
                 "source frame hash mismatch")
        with Image.open(path) as im:
            _require(im.format == "PNG" and im.mode == "RGBA" and im.size == cell,
                     "source must be RGBA PNG on shared canvas")
            _require(im.getchannel("A").getbbox() is not None or slot != "body",
                     "blank base body frame")
        index[key] = path
        items.add((slot, item))
    _require(any(slot == "body" for slot, _ in items), "missing body")
    for slot, item in items:
        for clip, spec in clips.items():
            for heading in headings:
                for frame in range(spec["frames"]):
                    _require((slot, item, clip, heading, frame) in index,
                             f"incomplete layers: {slot}/{item}/{clip}/{heading}/{frame}")

    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".ll-paperdoll-", dir=destination.parent) as tmp:
        workspace = Path(tmp)
        sheets = []
        for slot, item in sorted(items, key=lambda si: (SLOTS.index(si[0]), si[1])):
            for clip, spec in sorted(clips.items()):
                cols, rows = spec["frames"], len(headings)
                atlas = Image.new("RGBA", (cols * cell[0], rows * cell[1]), (0, 0, 0, 0))
                for row, heading in enumerate(headings):
                    for frame in range(cols):
                        with Image.open(index[(slot, item, clip, heading, frame)]) as original:
                            atlas.alpha_composite(original, (frame * cell[0], row * cell[1]))
                rel = f"atlases/{slot}/{item}/{clip}.png"
                path = workspace / rel
                path.parent.mkdir(parents=True, exist_ok=True)
                atlas.save(path, format="PNG", optimize=True)
                sheets.append(dict(slot=slot, item_id=item, animation=clip, file=rel,
                                   sha256=digest(path), size_px=list(atlas.size)))
        runtime = dict(schema=RUNTIME_SCHEMA, asset_id=manifest["asset_id"],
                       directions=len(headings), direction_names=headings,
                       frame_size=list(cell), pivot=list(pivot),
                       slots=[s for s in SLOTS if any(a == s for a, _ in items)],
                       animations=clips)
        catalog = dict(schema=CATALOG_SCHEMA, status="TECHNICAL_CANDIDATE_NOT_GOLDEN",
                       source_manifest_sha256=hashlib.sha256(raw).hexdigest(),
                       source_frame_count=len(index), generated_sheet_count=len(sheets),
                       runtime=runtime, sheets=sheets)
        (workspace / "catalog.json").write_text(json.dumps(catalog, indent=2, sort_keys=True) + "\n")
        verify_package(workspace)
        workspace.rename(destination)
    return catalog


def verify_package(destination: Path) -> dict:
    catalog = json.loads((destination / "catalog.json").read_text())
    _require(catalog.get("schema") == CATALOG_SCHEMA and
             catalog.get("status") == "TECHNICAL_CANDIDATE_NOT_GOLDEN", "not a candidate catalog")
    run = catalog.get("runtime")
    _require(isinstance(run, dict) and run.get("schema") == RUNTIME_SCHEMA, "runtime schema")
    _require(run.get("directions") in (4, 8, 16)
             and len(run.get("direction_names", [])) == run["directions"], "headings mismatch")
    shapes = run.get("frame_size")
    _require(isinstance(shapes, list) and len(shapes) == 2, "missing cell")
    sheets = catalog.get("sheets")
    _require(isinstance(sheets, list) and len(sheets) == catalog.get("generated_sheet_count")
             and len(sheets) > 0, "sheet inventory mismatch")
    unique = set()
    for sheet in sheets:
        key = sheet["slot"], sheet["item_id"], sheet["animation"]
        _require(key not in unique, "duplicate sheet")
        unique.add(key)
        rel = sheet["file"]
        path = _safe_file(destination, rel)
        _require(digest(path) == sheet["sha256"], "atlas SHA mismatch")
        with Image.open(path) as im:
            _require(im.format == "PNG" and im.mode == "RGBA", "invalid atlas encoding")
            expected = (shapes[0] * run["animations"][key[2]]["frames"],
                        shapes[1] * run["directions"])
            _require(im.size == expected and list(im.size) == sheet["size_px"],
                     "atlas size mismatch")
    return dict(status="PASS", sheets=len(unique), frames=catalog["source_frame_count"],
                asset_id=run["asset_id"])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, help="Directory containing manifest.json and original PNGs")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    result = verify_package(args.output) if args.verify else pack_frames(args.source, args.output)
    print("LL_PAPERDOLL_PACKAGE_PASS", json.dumps(
        {"sheets": (len(result["sheets"]) if isinstance(result.get("sheets"), list)
                    else result.get("sheets", result.get("generated_sheet_count"))),
         "status": "TECHNICAL_CANDIDATE_NOT_GOLDEN"}, sort_keys=True))


if __name__ == "__main__":
    main()
