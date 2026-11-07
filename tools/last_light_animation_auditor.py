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
import sqlite3
import tempfile
import unicodedata
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

from PIL import Image, UnidentifiedImageError
from animation_cache_adapter import iter_cache_entries


EXTENSIONS = {".png", ".gif", ".webp", ".tif", ".tiff", ".bmp", ".jpg", ".jpeg", ".apng"}
FIELDS = ["path", "source_ids", "source_match", "status", "classification", "format", "width", "height", "frames", "animated", "duration_ms", "loop", "alpha", "bytes", "sha256", "expected_sha256", "sheet_candidate", "error", "error_code", "format_issues", "frame_durations_ms", "frame_disposal", "frame_blend", "frame_bbox", "duplicate_frame_indices", "timing_issues", "mime", "rights", "retrieved_at"]
CATALOG_FIELDS = ["id", "source_filename", "category", "rights"]
AUDITOR_VERSION = "last_light.animation_audit.v3"
FORMAT_EXTENSIONS = {"PNG": {".png", ".apng"}, "GIF": {".gif"}, "WEBP": {".webp"},
                     "JPEG": {".jpg", ".jpeg"}, "BMP": {".bmp"}, "TIFF": {".tif", ".tiff"}}
FORMAT_MIMES = {"PNG": {"image/png", "image/apng"}, "GIF": {"image/gif"},
                "WEBP": {"image/webp"}, "JPEG": {"image/jpeg"},
                "BMP": {"image/bmp", "image/x-ms-bmp"}, "TIFF": {"image/tiff"}}


def fingerprint(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def inspect_stream(stream, relative_path, size, sha256, max_frames=512, max_canvas_pixels=16_000_000,
                   max_total_pixels=64_000_000):
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
            width, height = img.size
            if not width or not height or width * height > max_canvas_pixels:
                raise ValueError("RESOURCE_LIMIT_CANVAS")
            if frames > max_frames or frames * width * height > max_total_pixels:
                raise ValueError("RESOURCE_LIMIT_FRAMES")
            animated = bool(getattr(img, "is_animated", False) and frames > 1)
            durations = []
            disposals = []
            blends = []
            bboxes = []
            frame_hashes = []
            alpha = False
            loop = img.info.get("loop")
            image_format = img.format
            # Decode every frame, rather than trusting only an image header.
            for number in range(frames):
                img.seek(number)
                img.load()
                duration = img.info.get("duration")
                if duration is not None:
                    durations.append(float(duration))
                else:
                    durations.append(None)
                disposals.append(getattr(img, "disposal_method", img.info.get("disposal")))
                blends.append(img.info.get("blend_op", img.info.get("blend")))
                alpha |= "A" in img.getbands() or "transparency" in img.info
                rgba = img.convert("RGBA")
                bboxes.append(rgba.getchannel("A").getbbox())
                frame_hashes.append(hashlib.sha256(rgba.tobytes()).hexdigest())
            timing_issues = []
            if animated:
                if any(d is None for d in durations):
                    timing_issues.append("MISSING_FRAME_DELAY")
                if any(d is not None and d <= 0 for d in durations):
                    timing_issues.append("NONPOSITIVE_FRAME_DELAY")
                if len({d for d in durations if d is not None}) > 1:
                    positive = [d for d in durations if d is not None and d > 0]
                    if positive and max(positive) / min(positive) >= 5:
                        timing_issues.append("HIGH_FRAME_DELAY_VARIANCE_REVIEW")
            duplicates = [i for i, frame_hash in enumerate(frame_hashes)
                          if frame_hash in frame_hashes[:i]]
            ext = Path(relative_path.split("::")[-1]).suffix.lower()
            format_issues = []
            if image_format in FORMAT_EXTENSIONS and ext not in FORMAT_EXTENSIONS[image_format]:
                format_issues.append("FORMAT_EXTENSION_MISMATCH")
            if any(bbox is None for bbox in bboxes):
                format_issues.append("EMPTY_ALPHA_FRAME_REVIEW")
            # A wide strip is only a candidate. Geometry alone never proves animation.
            sheet = not animated and width >= 2 * height and width % height == 0 and width // height <= 64
            entry.update(status="ok", classification="animated_file" if animated else
                         "possible_sprite_sheet_unverified" if sheet else "static_image",
                         format=image_format, width=width, height=height, frames=frames,
                         animated=animated, duration_ms=sum(d for d in durations if d is not None) if any(d is not None for d in durations) else None,
                         loop=loop, alpha=alpha, sheet_candidate=sheet,
                         frame_durations_ms=durations, frame_disposal=disposals,
                         frame_blend=blends, frame_bbox=bboxes,
                         duplicate_frame_indices=duplicates, timing_issues=timing_issues,
                         format_issues=format_issues)
    except (UnidentifiedImageError, OSError, ValueError, EOFError, SyntaxError, Image.DecompressionBombError) as exc:
        entry["classification"] = "decode_error"
        entry["error"] = f"{type(exc).__name__}: {exc}"
        entry["error_code"] = str(exc) if str(exc).startswith("RESOURCE_LIMIT_") else "DECODE_ERROR"
    return entry


def inspect(path, relative_path, **kwargs):
    with path.open("rb") as stream:
        return inspect_stream(stream, relative_path, path.stat().st_size, fingerprint(path), **kwargs)


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


def inspect_archive(archive, max_member_bytes, **limits):
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
                    yield inspect_stream(spool, identifier, size, digest.hexdigest(), **limits)
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


def open_checkpoint(destination):
    """The writable checkpoint is *only* in the isolated audit-output directory."""
    db = sqlite3.connect(destination / "animation_audit_checkpoint.sqlite3")
    db.execute("""CREATE TABLE IF NOT EXISTS inspected (
        source_id TEXT NOT NULL, sha256 TEXT NOT NULL, auditor_version TEXT NOT NULL,
        record_json TEXT NOT NULL, PRIMARY KEY(source_id, sha256, auditor_version))""")
    db.commit()
    return db


def inspect_cache_record(row, checkpoint, resume, **limits):
    path_label = row.get("relative_path") or f"row:{row['row_number']}"
    entry = {field: None for field in FIELDS}
    entry.update(path=path_label, source_ids=[row["source_id"]] if row["source_id"] else [],
                 source_match="cache_rejected", status="error", classification="cache_validation_error",
                 error_code=row["cache_error"], error=row["cache_error"],
                 expected_sha256=row.get("sha256"), mime=row.get("mime"), rights=row.get("rights"),
                 retrieved_at=row.get("retrieved_at"))
    if row["cache_error"]:
        return entry, False
    path = row["path"]
    try:
        actual_size = path.stat().st_size
        if actual_size != row["byte_length"]:
            entry.update(error_code="CACHE_SIZE_MISMATCH", error="Cache byte length differs from verified manifest")
            return entry, False
        actual_sha = fingerprint(path)
        entry["sha256"] = actual_sha
        if actual_sha.lower() != row["sha256"].lower():
            entry.update(error_code="CACHE_HASH_MISMATCH", error="Cache SHA-256 differs from verified manifest")
            return entry, False
        if resume:
            existing = checkpoint.execute("SELECT record_json FROM inspected WHERE source_id=? AND sha256=? AND auditor_version=?",
                                          (row["source_id"], actual_sha, AUDITOR_VERSION)).fetchone()
            if existing:
                cached = json.loads(existing[0])
                if cached.get("path") == path_label and cached.get("status") == "ok":
                    return cached, True
        with path.open("rb") as stream:
            inspected = inspect_stream(stream, path_label, actual_size, actual_sha, **limits)
        inspected.update(source_ids=[row["source_id"]], source_match="cache_verified",
                         expected_sha256=row["sha256"].lower(), mime=row["mime"], rights=row["rights"],
                         retrieved_at=row["retrieved_at"])
        if inspected["status"] == "ok" and inspected["format"] in FORMAT_MIMES and row["mime"].lower() not in FORMAT_MIMES[inspected["format"]]:
            inspected.update(status="error", classification="cache_validation_error",
                             error_code="CACHE_MIME_MISMATCH", error="Declared MIME disagrees with decoded image signature")
        if inspected["status"] == "ok":
            checkpoint.execute("INSERT OR REPLACE INTO inspected VALUES(?,?,?,?)",
                               (row["source_id"], actual_sha, AUDITOR_VERSION, json.dumps(inspected, sort_keys=True)))
            checkpoint.commit()
        return inspected, False
    except (OSError, ValueError) as exc:
        entry.update(error_code="CACHE_READ_ERROR", error=f"{type(exc).__name__}: {exc}")
        return entry, False


def audit(source, destination, max_files=None, archives=(), catalog_dirs=(), max_member_mb=128,
          cache_manifest=None, cache_root=None, resume=False, max_frames=512,
          max_canvas_pixels=16_000_000, max_total_pixels=64_000_000):
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
    if bool(cache_manifest) != bool(cache_root):
        raise ValueError("Provide --cache-manifest and --cache-root together")
    if cache_root is not None and (destination == Path(cache_root).resolve() or destination.is_relative_to(Path(cache_root).resolve())):
        raise ValueError("Audit output must be outside the read-only cache root")
    if source is None and not archives and not catalog_dirs and not cache_manifest:
        raise ValueError("Provide --input-dir, --input-zip, --catalog-dir or --cache-manifest with --cache-root")
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
        records.append(inspect(path, path.relative_to(source).as_posix(),
                               max_frames=max_frames, max_canvas_pixels=max_canvas_pixels,
                               max_total_pixels=max_total_pixels))
    for archive in sorted(archives):
        if max_files is not None and len(records) >= max_files:
            break
        if not zipfile.is_zipfile(archive):
            raise ValueError(f"Not a valid ZIP archive: {archive}")
        for entry in inspect_archive(archive, max_member_mb * 1024 * 1024,
                                     max_frames=max_frames, max_canvas_pixels=max_canvas_pixels,
                                     max_total_pixels=max_total_pixels):
            if max_files is not None and len(records) >= max_files:
                break
            records.append(entry)

    cache_summary = {"provided": bool(cache_manifest), "inspected": 0, "reused_checkpoint": 0, "failed": 0}
    if cache_manifest:
        destination.mkdir(parents=True, exist_ok=True)
        db = open_checkpoint(destination)
        try:
            for row in iter_cache_entries(cache_manifest, cache_root):
                if max_files is not None and len(records) >= max_files:
                    break
                record, reused = inspect_cache_record(row, db, resume, max_frames=max_frames,
                                                      max_canvas_pixels=max_canvas_pixels,
                                                      max_total_pixels=max_total_pixels)
                records.append(record)
                cache_summary["inspected"] += 1
                cache_summary["reused_checkpoint"] += bool(reused)
                cache_summary["failed"] += record["status"] != "ok"
        finally:
            db.close()

    matched_ids = set()
    for item in records:
        if item.get("source_match") in ("cache_verified", "cache_rejected"):
            if item.get("source_match") == "cache_verified" and item.get("status") == "ok":
                matched_ids.update(item.get("source_ids") or [])
            continue
        names = lookup.get(file_key(item["path"].split("::")[-1]), [])
        item["source_ids"] = sorted(names)
        item["source_match"] = "unique" if len(names) == 1 else "ambiguous" if names else "unmatched" if catalog else "no_catalog"
        matched_ids.update(names)
    matched_ids.intersection_update(catalog)
    hashes = defaultdict(list)
    for item in records:
        if item.get("sha256"):
            hashes[item["sha256"]].append(item["path"])
    duplicates = {key: paths for key, paths in sorted(hashes.items()) if len(paths) > 1}
    counts = Counter(item.get("classification") for item in records)
    sequences = frame_sequences(records)
    report = {
        "schema": AUDITOR_VERSION, "input": str(source) if source else None,
        "input_archives": [str(path) for path in archives],
        "verified_cache": cache_summary,
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
    parser.add_argument("--cache-manifest", type=Path, help="Read-only verified-cache JSONL or SQLite manifest")
    parser.add_argument("--cache-root", type=Path, help="Read-only root of externally retrieved media")
    parser.add_argument("--resume", action="store_true", help="Reuse SHA-verified results from output SQLite checkpoint")
    parser.add_argument("--max-frames", type=int, default=512)
    parser.add_argument("--max-canvas-pixels", type=int, default=16_000_000)
    parser.add_argument("--max-total-pixels", type=int, default=64_000_000)
    args = parser.parse_args()
    report = audit(args.input_dir, args.output_dir, args.max_files,
                   archives=args.input_zip, catalog_dirs=args.catalog_dir, max_member_mb=args.max_member_mb,
                   cache_manifest=args.cache_manifest, cache_root=args.cache_root, resume=args.resume,
                   max_frames=args.max_frames, max_canvas_pixels=args.max_canvas_pixels,
                   max_total_pixels=args.max_total_pixels)
    print(json.dumps({key: report[key] for key in ("scanned", "counts", "error_paths")}, indent=2))
    return 1 if report["error_paths"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
