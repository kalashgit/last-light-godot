#!/usr/bin/env python3
"""Read-only research-media animation auditor for LAST LIGHT.

Requires Pillow. Never copies source artwork to the game or approves it for use.
"""

import argparse
import csv
import hashlib
import json
import os
from collections import Counter, defaultdict
from pathlib import Path

from PIL import Image, UnidentifiedImageError


EXTENSIONS = {".png", ".gif", ".webp", ".tif", ".tiff", ".bmp", ".jpg", ".jpeg", ".apng"}
FIELDS = ["path", "status", "classification", "format", "width", "height", "frames", "animated", "duration_ms", "loop", "alpha", "bytes", "sha256", "sheet_candidate", "error"]


def fingerprint(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def inspect(path, relative_path):
    entry = {name: None for name in FIELDS}
    entry.update(path=relative_path, status="error", bytes=path.stat().st_size, sha256=fingerprint(path),
                 animated=False, sheet_candidate=False)
    try:
        with Image.open(path) as check:
            check.verify()
        with Image.open(path) as img:
            frames = int(getattr(img, "n_frames", 1))
            animated = bool(getattr(img, "is_animated", False) and frames > 1)
            durations = []
            alpha = False
            # Decode every frame, rather than trusting only an image header.
            for number in range(frames):
                img.seek(number)
                img.load()
                duration = img.info.get("duration")
                if duration is not None:
                    durations.append(float(duration))
                alpha |= "A" in img.getbands() or "transparency" in img.info
            width, height = img.size
            # A wide strip is only a candidate. Geometry alone never proves animation.
            sheet = not animated and width >= 2 * height and width % height == 0 and width // height <= 64
            entry.update(status="ok", classification="animated_file" if animated else
                         "possible_sprite_sheet_unverified" if sheet else "static_image",
                         format=img.format, width=width, height=height, frames=frames,
                         animated=animated, duration_ms=sum(durations) if durations else None,
                         loop=img.info.get("loop"), alpha=alpha, sheet_candidate=sheet)
    except (UnidentifiedImageError, OSError, ValueError, EOFError, SyntaxError) as exc:
        entry["classification"] = "decode_error"
        entry["error"] = f"{type(exc).__name__}: {exc}"
    return entry


def audit(source, destination, max_files=None):
    source = Path(source).resolve()
    destination = Path(destination).resolve()
    if not source.is_dir():
        raise ValueError(f"Input directory does not exist: {source}")
    if source == destination:
        raise ValueError("Output must be separate from input")
    # Avoid following directory symlinks, escaping the source tree, or reading audit output.
    candidates = []
    for parent, dirs, files in os.walk(source, followlinks=False):
        dirs[:] = sorted(d for d in dirs if not (Path(parent) / d).is_symlink() and
                         not (Path(parent) / d).resolve().is_relative_to(destination))
        for name in sorted(files):
            item = Path(parent) / name
            if item.suffix.lower() in EXTENSIONS and not item.is_symlink() and not item.resolve().is_relative_to(destination):
                candidates.append(item)
    candidates.sort(key=lambda p: p.relative_to(source).as_posix())
    if max_files is not None:
        if max_files < 0:
            raise ValueError("--max-files must be nonnegative")
        candidates = candidates[:max_files]

    records = [inspect(p, p.relative_to(source).as_posix()) for p in candidates]
    hashes = defaultdict(list)
    for item in records:
        hashes[item["sha256"]].append(item["path"])
    duplicates = {key: paths for key, paths in sorted(hashes.items()) if len(paths) > 1}
    counts = Counter(item["classification"] for item in records)
    report = {
        "schema": "last_light.animation_audit.v1", "input": str(source),
        "scanned": len(records), "max_files": max_files, "counts": dict(sorted(counts.items())),
        "duplicates": duplicates, "error_paths": [r["path"] for r in records if r["status"] != "ok"],
        "rights": "research_only_unless_proven_otherwise", "game_art_approved": 0,
        "notes": ["Multi-frame decoding establishes animated source files, not gameplay-ready animation.",
                  "Sprite-sheet geometry is heuristic and requires human frame inspection.",
                  "No third-party images are copied or approved by this tool."],
    }
    destination.mkdir(parents=True, exist_ok=True)
    # Stable full rewrites permit safe reruns; intermediate files are atomically replaced.
    for name, content in (
        ("animation_inventory.jsonl", "".join(json.dumps(r, sort_keys=True) + "\n" for r in records)),
        ("animation_report.json", json.dumps(report, indent=2, sort_keys=True) + "\n"),
    ):
        temporary = destination / (name + ".tmp")
        temporary.write_text(content, encoding="utf-8")
        temporary.replace(destination / name)
    temporary = destination / "animation_inventory.csv.tmp"
    with temporary.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(records)
    temporary.replace(destination / "animation_inventory.csv")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, required=True, help="Local folder containing source images")
    parser.add_argument("--output-dir", type=Path, required=True, help="Separate audit-report folder")
    parser.add_argument("--max-files", type=int, help="Deterministic first N files for a benchmark")
    args = parser.parse_args()
    report = audit(args.input_dir, args.output_dir, args.max_files)
    print(json.dumps({key: report[key] for key in ("scanned", "counts", "error_paths")}, indent=2))
    return 1 if report["error_paths"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
