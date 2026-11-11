"""Export the A00 research ledger without promoting references into game assets.

Source JSONL stays authoritative.  This exporter makes reviewable CSV extracts
and an independently reconciled canonical-master queue for spreadsheets.
It never downloads or redistributes third-party image pixels.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter
from pathlib import Path


SOURCE_FILE = re.compile(r"a00_20261108_b00[1-8]_[0-9]+(?:_part_[a-h])?\.jsonl\Z")
REFERENCE_COLUMNS = (
    "record_number", "source_page_id", "source_title", "source_url",
    "primary_class", "source_categories", "suggested_queue", "master_id",
    "semantic_status", "visual_review", "rights", "file_page_status",
    "representation_kind", "state_key", "variant_key", "parent_source_page_id",
    "parent_source_title", "proposed_parent_stem", "family_hypothesis",
    "reason", "batch_id",
)
MASTER_COLUMNS = (
    "content_id", "family", "kind", "queue", "priority", "stage",
    "semantic_verification", "work_order", "refinement_admitted",
    "rights_reviewed", "technical_qa_passed", "founder_visual_approved",
    "godot_tested", "iphone_verified", "production_status",
)
ADMITTED_COLUMNS = (
    "master_id", "queue", "priority", "work_order_id", "notion_url",
    "source_page_url", "existing_geometry_id", "geometry_status",
    "quality_focus", "dispatch_permission", "source_rights",
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_files(source_dir: Path) -> list[Path]:
    files = sorted(p for p in source_dir.iterdir()
                   if p.is_file() and SOURCE_FILE.fullmatch(p.name))
    if not files:
        raise ValueError("No A00 source classification JSONL files found")
    return files


def load_references(source_dir: Path, expected_count: int = 21025) -> tuple[list[dict], dict]:
    records = []
    seen_ids = set()
    classes: Counter[str] = Counter()
    batches: Counter[str] = Counter()
    for file in source_files(source_dir):
        with file.open("r", encoding="utf-8") as stream:
            for line_number, line in enumerate(stream, 1):
                if not line.strip():
                    raise ValueError(f"Blank reference line in {file.name}:{line_number}")
                row = json.loads(line)
                source_id = row.get("source_page_id")
                if type(source_id) is not int or source_id in seen_ids:
                    raise ValueError(f"Missing/duplicate source ID: {source_id}")
                if not all(isinstance(row.get(key), str) and row[key]
                           for key in ("source_title", "source_url", "primary_class", "reason", "batch_id")):
                    raise ValueError(f"Incomplete source evidence: {source_id}")
                seen_ids.add(source_id)
                classes[row["primary_class"]] += 1
                batches[row["batch_id"]] += 1
                records.append({"record_number": len(records) + 1, **row})
    if len(records) != expected_count:
        raise ValueError(f"Reference coverage {len(records)} != {expected_count}")
    return records, {"count": len(records), "unique_source_ids": len(seen_ids),
                     "primary_class_counts": dict(sorted(classes.items())),
                     "batch_counts": dict(sorted(batches.items()))}


def _safe_cell(value: object) -> str | int | bool:
    if value is None:
        return ""
    if isinstance(value, list):
        value = "; ".join(str(x) for x in value)
    if isinstance(value, (int, bool)):
        return value
    string = str(value).replace("\x00", "")
    # CSV may be opened in a spreadsheet: never interpret source text as formula.
    if string.lstrip().startswith(("=", "+", "-", "@")):
        return "'" + string
    return string


def _write_csv(path: Path, columns: tuple[str, ...], rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(columns)
        writer.writerows([_safe_cell(row.get(column)) for column in columns] for row in rows)


def load_master_queue(snapshot_path: Path, admitted_path: Path | None) -> tuple[list[dict], list[dict]]:
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    masters = snapshot["production_masters"]
    admitted = json.loads(admitted_path.read_text(encoding="utf-8"))["work_orders"] if admitted_path else []
    admission_ids = {row["master_id"] for row in admitted}
    ids = [row["content_id"] for row in masters]
    if len(set(ids)) != len(ids) or len(admission_ids) != len(admitted):
        raise ValueError("Duplicate canonical master or admission IDs")
    if not admission_ids.issubset(ids):
        raise ValueError("Admitted refinement is absent from canonical Notion snapshot")
    ready = []
    for row in sorted(masters, key=lambda x: x["content_id"]):
        verified = row.get("semantic_verification") == "Canonical Verified"
        has_order = bool(row.get("work_order") and row.get("queue"))
        if row["content_id"] in admission_ids and not (verified and has_order):
            raise ValueError(f"Inadmissible refinement: {row['content_id']}")
        # Admission permits original refinement only, not automatic art release.
        status = ("ORIGINAL_REFINEMENT_ONLY" if row["content_id"] in admission_ids
                  else "RECIPE_AUTHORING_ONLY" if verified and has_order
                  else "VERIFICATION_HOLD")
        ready.append({**row, "refinement_admitted": row["content_id"] in admission_ids,
                      "production_status": status})
    return ready, sorted(admitted, key=lambda x: x["master_id"])


def export(source_dir: Path, snapshot: Path, output_dir: Path,
           admission: Path | None = None, expected_count: int = 21025) -> dict:
    references, control = load_references(source_dir, expected_count)
    masters, admitted = load_master_queue(snapshot, admission)
    output_dir.mkdir(parents=True, exist_ok=True)
    files = {
        "references": output_dir / "last_light_21025_references.csv",
        "masters": output_dir / "last_light_canonical_master_queue.csv",
        "admitted": output_dir / "last_light_admitted_refinement.csv",
    }
    _write_csv(files["references"], REFERENCE_COLUMNS, references)
    _write_csv(files["masters"], MASTER_COLUMNS, masters)
    _write_csv(files["admitted"], ADMITTED_COLUMNS, admitted)
    control.update({
        "schema_version": 1,
        "source_kind": "A00_METADATA_RESEARCH_ONLY",
        "canonical_master_rows": len(masters),
        "canonical_verified": sum(x["semantic_verification"] == "Canonical Verified" for x in masters),
        "refinement_admitted": len(admitted),
        "golden_approved_by_export": 0,
        "source_snapshot_sha256": _sha256(snapshot),
        "admission_manifest_sha256": _sha256(admission) if admission else None,
        "csv_sha256": {k: _sha256(p) for k, p in files.items()},
        "source_files": [{"name": p.name, "sha256": _sha256(p)} for p in source_files(source_dir)],
    })
    (output_dir / "last_light_catalog_integrity.json").write_text(
        json.dumps(control, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return control


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--admission", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--expected-count", type=int, default=21025)
    args = parser.parse_args()
    result = export(args.source_dir, args.snapshot, args.output_dir,
                    args.admission, args.expected_count)
    print(json.dumps({key: result[key] for key in (
        "count", "unique_source_ids", "canonical_master_rows",
        "canonical_verified", "refinement_admitted")}, sort_keys=True))


if __name__ == "__main__":
    main()
