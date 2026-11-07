"""Immutable LAST LIGHT retrieval-cache adapter (LL-074).

The retrieval worker owns media and the snapshot. This module never downloads,
renames, writes to, or extracts anything inside the cache root.
"""

import json
import re
import sqlite3
from pathlib import Path, PurePosixPath


SCHEMA = "last_light.verified_cache_entry.v1"
REQUIRED = ("source_id", "relative_path", "sha256", "byte_length", "mime", "category",
            "rights", "retrieved_at", "verification_status")


def load_manifest(path):
    """Read JSONL or a read-only SQLite manifest; preserve record order."""
    path = Path(path).resolve(strict=True)
    if path.suffix.lower() in (".sqlite", ".sqlite3", ".db"):
        # An immutable snapshot prevents SQLite from creating any WAL/SHM files
        # alongside the retrieval worker's database. Never read a live writer DB.
        connection = sqlite3.connect(f"file:{path.as_posix()}?mode=ro&immutable=1", uri=True)
        connection.row_factory = sqlite3.Row
        try:
            return [dict(row) for row in connection.execute("SELECT * FROM verified_media ORDER BY source_id")]
        finally:
            connection.close()
    if path.suffix.lower() != ".jsonl":
        raise ValueError("Manifest must be a .jsonl or SQLite database with verified_media table")
    rows = []
    with path.open("r", encoding="utf-8") as stream:
        for number, line in enumerate(stream, 1):
            if line.strip():
                try:
                    rows.append(json.loads(line))
                except ValueError as exc:
                    raise ValueError(f"Invalid JSONL at {path.name}:{number}") from exc
    return rows


def safe_cache_path(cache_root, relative_path):
    """Reject traversal and symlink components (including dangling links)."""
    root = Path(cache_root)
    if root.is_symlink() or not root.is_dir():
        raise ValueError("CACHE_ROOT_UNAVAILABLE")
    root = root.resolve(strict=True)
    if not isinstance(relative_path, str) or not relative_path or "\\" in relative_path:
        raise ValueError("UNSAFE_CACHE_PATH")
    pure = PurePosixPath(relative_path)
    if pure.is_absolute() or any(part in ("..", ".") for part in relative_path.split("/")):
        raise ValueError("UNSAFE_CACHE_PATH")
    if any(part == "" for part in relative_path.split("/")) or ":" in pure.parts[0]:
        raise ValueError("UNSAFE_CACHE_PATH")
    path = root
    for part in pure.parts:
        path = path / part
        if path.is_symlink():
            raise ValueError("CACHE_SYMLINK_REJECTED")
    if not path.is_file() or not path.resolve(strict=True).is_relative_to(root):
        raise ValueError("CACHE_FILE_MISSING")
    return path


def iter_cache_entries(manifest, cache_root):
    """Yields validated immutable IDs and paths, or structured errors per row."""
    seen = set()
    for index, row in enumerate(load_manifest(manifest), 1):
        record = {"source_id": None, "relative_path": None, "path": None,
                  "sha256": None, "byte_length": None, "mime": None,
                  "category": None, "rights": None, "retrieved_at": None,
                  "cache_error": None, "row_number": index}
        if not isinstance(row, dict):
            record["cache_error"] = "INVALID_CACHE_RECORD"
            yield record
            continue
        record.update({k: row.get(k) for k in REQUIRED if k in record})
        source_id = row.get("source_id")
        if not isinstance(source_id, str) or not source_id.strip():
            record["cache_error"] = "CACHE_ID_MISSING"
        elif source_id in seen:
            record["cache_error"] = "DUPLICATE_CACHE_SOURCE_ID"
        else:
            seen.add(source_id)
            if row.get("schema") != SCHEMA:
                record["cache_error"] = "CACHE_SCHEMA_MISMATCH"
            elif not all(row.get(field) is not None for field in REQUIRED):
                record["cache_error"] = "CACHE_METADATA_MISSING"
            elif row.get("verification_status") != "verified":
                record["cache_error"] = "CACHE_NOT_VERIFIED"
            elif not isinstance(row.get("byte_length"), int) or row["byte_length"] < 0:
                record["cache_error"] = "CACHE_SIZE_INVALID"
            elif not isinstance(row.get("sha256"), str) or not re.fullmatch("[a-fA-F0-9]{64}", row["sha256"]):
                record["cache_error"] = "CACHE_HASH_INVALID"
            elif not isinstance(row.get("mime"), str) or not row["mime"].startswith("image/"):
                record["cache_error"] = "CACHE_MIME_UNSUPPORTED"
            elif not all(isinstance(row.get(key), str) and row[key].strip()
                         for key in ("category", "rights", "retrieved_at")):
                record["cache_error"] = "CACHE_METADATA_INVALID"
            else:
                try:
                    record["path"] = safe_cache_path(cache_root, row["relative_path"])
                except (ValueError, OSError) as exc:
                    record["cache_error"] = str(exc)
        yield record
