#!/usr/bin/env python3
"""Read-only research-media animation auditor for LAST LIGHT.

Requires Pillow. Never copies source artwork to the game or approves it for use.
"""

import argparse
import csv
import hashlib
import json
import os
import re
import tempfile
import unicodedata
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

from PIL import Image, UnidentifiedImageError


EXTENSIONS = {".png", ".gif", ".webp", ".tif", ".tiff", ".bmp", ".jpg", ".jpeg", ".apng"}
FIELDS = ["path", "source_ids", "source_match", "status", "classification", "format", "width", "height", "frames", "animated", "duration_ms", "loop", "alpha", "bytes", "sha256", "sheet_candidate", "error"]
CATALOG_FIELDS = ["id", "source_filename", "category", "rights"]


def fingerprint(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def inspect_stream(stream, relative_path, size, sha256):
    entry = {name: None for name in FIELDS}
    entry.update(path=relative_path, source_ids=[], source_match="no_catalog", status="error", bytes=size,
                 sha256=sha256, animated=False, sheet_candidate=False)
    try:
        stream.seek(0)
        with Image.open(stream) as check:
            check.verify()
        stream.seek(0)
        with Image.open(stream) as img:
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


def inspect(path, relative_path):
    with path.open("rb") as stream:
        return inspect_stream(stream, relative_path, path.stat().st_size, fingerprint(path))


def file_key(name):
    """Normalize case, Unicode and MediaWiki-style underscore spacing, without guessing IDs."""
    return " ".join(unicodedata.normalize("NFC", Path(name).name).replace("_", " ").casefold().split())


def read_catalog(catalog_dirs):
    records = {}
    for folder in catalog_dirs:
        folder = Path(folder)
        if not folder.exists():
            raise ValueError(f"Catalog path does not exist: {folder}")
        paths = sorted(folder.rglob("*.jsonl")) if folder.is_dir() else [folder]
        for path in paths:
            for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                if not line.strip():
                    continue
                try:
                    row = json.loads(line)
                except ValueError as exc:
                    raise ValueError(f"Invalid catalog JSON at {path}:{line_number}: {exc}") from exc
                if not isinstance(row, dict) or not row.get("source_filename"):
                    continue  # Other JSONL record kinds are not source-media catalog entries.
                if not row.get("id") and row.get("record_type") == "external_reference" and isinstance(row.get("index"), int):
                    # Item-icon batch rows have indexed source references but no explicit IDs.
                    row["id"] = f"pzwiki.icon.{row['index']:06d}"
                if not row.get("id"):
                    continue
                if row["id"] in records and records[row["id"]] != row:
                    raise ValueError(f"Conflicting catalog source ID: {row['id']}")
                records[row["id"]] = row
    lookup = defaultdict(list)
    for record in records.values():
        lookup[file_key(record["source_filename"])].append(record["id"])
    return records, lookup


def inspect_archive(archive, max_member_bytes):
    """Stream ZIP members; never extract third-party images into the repository."""
    with zipfile.ZipFile(archive) as collection:
        for member in sorted(collection.infolist(), key=lambda i: i.filename):
            if member.is_dir() or Path(member.filename).suffix.lower() not in EXTENSIONS:
                continue
            identifier = f"{Path(archive).name}::{member.filename}"
            parts = member.filename.replace("\\", "/").split("/")
            if member.filename.startswith("/") or any(part in ("..", "") for part in parts):
                yield dict(path=identifier, status="error", classification="unsafe_zip_path",
                           error="Unsafe archive member name", source_ids=[], source_match="no_catalog")
                continue
            if member.file_size > max_member_bytes:
                yield dict(path=identifier, status="error", classification="oversize_zip_member",
                           error=f"Archive member exceeds {max_member_bytes} bytes", source_ids=[], source_match="no_catalog")
                continue
            try:
                with collection.open(member) as stream, tempfile.SpooledTemporaryFile(max_size=8 * 1024 * 1024) as spool:
                    digest = hashlib.sha256()
                    size = 0
                    while chunk := stream.read(1024 * 1024):
                        size += len(chunk)
                        if size > max_member_bytes:
                            raise ValueError("Expanded archive member exceeds size limit")
                        digest.update(chunk)
                        spool.write(chunk)
                    yield inspect_stream(spool, identifier, size, digest.hexdigest())
            except (OSError, RuntimeError, ValueError, EOFError, zipfile.BadZipFile) as exc:
                yield dict(path=identifier, status="error", classification="zip_read_error",
                           error=f"{type(exc).__name__}: {exc}", source_ids=[], source_match="no_catalog")


def frame_sequences(records):
    """Find separately stored numbered frames; candidate grouping, never approval."""
    grouped = defaultdict(list)
    for record in records:
        if record.get("status") != "ok" or record.get("animated"):
            continue
        location = record["path"]
        folder, _, filename = location.rpartition("/")
        stem = Path(filename).stem
        match = re.match(r"^(.*?)[_-](\d{1,4})$", stem)
        if not match:
            continue
        key = (folder, match.group(1).casefold(), Path(filename).suffix.lower())
        grouped[key].append((int(match.group(2)), record))
    found = []
    for (folder, label, extension), frames in sorted(grouped.items()):
        if len(frames) < 2:
            continue
        frames.sort(key=lambda value: (value[0], value[1]["path"]))
        numbers = [number for number, _ in frames]
        dimensions = {(item["width"], item["height"]) for _, item in frames}
        directional = label in {"held", "direction", "dir", "facing", "angle"}
        found.append({"family": f"{folder}/{label}".lstrip("/"), "extension": extension,
                      "frame_numbers": numbers, "files": [item["path"] for _, item in frames],
                      "missing_between": sorted(set(range(min(numbers), max(numbers) + 1)) - set(numbers)),
                      "dimensions_consistent": len(dimensions) == 1,
                      "classification": "directional_pose_set" if directional else "numbered_frame_sequence_candidate",
                      "approved_for_game": False, "fps": None, "pivot": None})
    return found


def audit(source, destination, max_files=None, archives=(), catalog_dirs=(), max_member_mb=128):
    source = Path(source).resolve() if source is not None else None
    destination = Path(destination).resolve()
    if source is not None and not source.is_dir():
        raise ValueError(f"Input directory does not exist: {source}")
    if source is not None and source == destination:
        raise ValueError("Output must be separate from input")
    if max_files is not None and max_files < 0:
        raise ValueError("--max-files must be nonnegative")
    if max_member_mb < 1:
        raise ValueError("--max-member-mb must be positive")
    archives = [Path(p).resolve() for p in archives]
    if source is None and not archives and not catalog_dirs:
        raise ValueError("Provide --input-dir, --input-zip or --catalog-dir")
    # Avoid following directory symlinks, escaping the source tree, or reading audit output.
    candidates = []
    if source is not None:
        for parent, dirs, files in os.walk(source, followlinks=False):
            dirs[:] = sorted(d for d in dirs if not (Path(parent) / d).is_symlink() and
                             not (Path(parent) / d).resolve().is_relative_to(destination))
            for name in sorted(files):
                item = Path(parent) / name
                if item.suffix.lower() in EXTENSIONS and not item.is_symlink() and not item.resolve().is_relative_to(destination):
                    candidates.append(item)
        candidates.sort(key=lambda p: p.relative_to(source).as_posix())
    catalog, lookup = read_catalog(catalog_dirs)
    # Cap applies to both directory members and ZIP members.

    records = []
    for path in candidates:
        if max_files is not None and len(records) >= max_files:
            break
        records.append(inspect(path, path.relative_to(source).as_posix()))
    for archive in sorted(archives):
        if max_files is not None and len(records) >= max_files:
            break
        if not zipfile.is_zipfile(archive):
            raise ValueError(f"Not a valid ZIP archive: {archive}")
        for entry in inspect_archive(archive, max_member_mb * 1024 * 1024):
            if max_files is not None and len(records) >= max_files:
                break
            records.append(entry)

    matched_ids = set()
    for item in records:
        names = lookup.get(file_key(item["path"].split("::")[-1]), [])
        item["source_ids"] = sorted(names)
        item["source_match"] = "unique" if len(names) == 1 else "ambiguous" if names else "unmatched" if catalog else "no_catalog"
        matched_ids.update(names)
    hashes = defaultdict(list)
    for item in records:
        if item.get("sha256"):
            hashes[item["sha256"]].append(item["path"])
    duplicates = {key: paths for key, paths in sorted(hashes.items()) if len(paths) > 1}
    counts = Counter(item["classification"] for item in records)
    sequences = frame_sequences(records)
    report = {
        "schema": "last_light.animation_audit.v2", "input": str(source) if source else None,
        "input_archives": [str(path) for path in archives],
        "scanned": len(records), "max_files": max_files, "counts": dict(sorted(counts.items())),
        "duplicates": duplicates, "error_paths": [r["path"] for r in records if r["status"] != "ok"],
        "catalog_records": len(catalog), "catalog_matched_ids": len(matched_ids),
        "catalog_unmatched_ids": len(catalog) - len(matched_ids),
        "catalog_ambiguous_filenames": sum(1 for value in lookup.values() if len(value) > 1),
        "catalog_gif_filename_hints": sum(1 for row in catalog.values() if row["source_filename"].lower().endswith(".gif")),
        "numbered_frame_sequence_candidates": sum(row["classification"] == "numbered_frame_sequence_candidate" for row in sequences),
        "directional_pose_sets": sum(row["classification"] == "directional_pose_set" for row in sequences),
        "numbered_frame_sequence_gaps": sum(bool(row["missing_between"]) for row in sequences),
        "rights": "research_only_unless_proven_otherwise", "game_art_approved": 0,
        "notes": ["Multi-frame decoding establishes animated source files, not gameplay-ready animation.",
                  "Sprite-sheet geometry is heuristic and requires human frame inspection.",
                  "Catalog GIF filenames are hints, not proof of animated frames.",
                  "No third-party images are copied or approved by this tool."],
    }
    destination.mkdir(parents=True, exist_ok=True)
    # Stable full rewrites permit safe reruns; intermediate files are atomically replaced.
    for name, content in (
        ("animation_inventory.jsonl", "".join(json.dumps(r, sort_keys=True) + "\n" for r in records)),
        ("animation_report.json", json.dumps(report, indent=2, sort_keys=True) + "\n"),
        ("numbered_frame_sequences.json", json.dumps(sequences, indent=2, sort_keys=True) + "\n"),
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
    temporary = destination / "missing_catalog_records.csv.tmp"
    with temporary.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=CATALOG_FIELDS)
        writer.writeheader()
        writer.writerows({field: catalog[ident].get(field) for field in CATALOG_FIELDS}
                         for ident in sorted(set(catalog) - matched_ids))
    temporary.replace(destination / "missing_catalog_records.csv")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, help="Local folder containing source images")
    parser.add_argument("--input-zip", type=Path, action="append", default=[], help="ZIP archive, repeatable; no extraction")
    parser.add_argument("--catalog-dir", type=Path, action="append", default=[], help="JSONL catalog directory, repeatable")
    parser.add_argument("--output-dir", type=Path, required=True, help="Separate audit-report folder")
    parser.add_argument("--max-files", type=int, help="Deterministic first N files for a benchmark")
    parser.add_argument("--max-member-mb", type=int, default=128, help="ZIP member expansion safety limit")
    args = parser.parse_args()
    report = audit(args.input_dir, args.output_dir, args.max_files,
                   archives=args.input_zip, catalog_dirs=args.catalog_dir, max_member_mb=args.max_member_mb)
    print(json.dumps({key: report[key] for key in ("scanned", "counts", "error_paths")}, indent=2))
    return 1 if report["error_paths"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
