#!/usr/bin/env python3
"""Read-only audit of the checked-in Notion research mirror.

Creates a reproducible human-review queue. It never changes the original
import, production DB, reference files, or an approval flag.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

from factory_v4_benchmark import atomic_bytes, canonical


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def audit(source: Path, output: Path) -> dict:
    icons = sorted((source / "notion_item_icon_batches").glob("*.jsonl"))
    classifications = sorted((source / "notion_classification_batches").glob("*.jsonl"))
    media = sorted((source / "notion_media_shards").glob("*.jsonl"))
    if not icons or not classifications or not media:
        raise ValueError("Incomplete research mirror; refusing partial coverage claims")
    files = icons + classifications + media
    fingerprints = {p.relative_to(source).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    all_icons = [row for path in icons for row in load_jsonl(path)]
    all_classes = [row for path in classifications for row in load_jsonl(path)]
    all_media = [row for path in media for row in load_jsonl(path)]
    if len({r.get("index") for r in all_icons}) != len(all_icons):
        raise ValueError("Duplicate icon source index; do not silently overwrite")
    if len({r.get("index") for r in all_classes}) != len(all_classes):
        raise ValueError("Duplicate classification source index; do not silently overwrite")
    index = {r["index"]: r for r in all_icons}
    classifications_by_id = {r["index"]: r for r in all_classes}
    queues = []
    conflicts = []
    filenames = defaultdict(list)
    for row in all_icons:
        filenames[row.get("source_filename", "").casefold()].append(row["index"])
    for index_id in sorted(set(index) | set(classifications_by_id)):
        raw, candidate = index.get(index_id), classifications_by_id.get(index_id)
        reasons = []
        if raw is None:
            reasons.append("missing_source_record")
        if candidate is None:
            reasons.append("missing_classification")
        if raw and candidate:
            if raw.get("source_filename") != candidate.get("source_filename"):
                reasons.append("source_filename_mismatch")
            if raw.get("source_file_page") != candidate.get("source_file_page"):
                reasons.append("source_page_mismatch")
            if candidate.get("proposed_category", "").lower().startswith("needs review"):
                reasons.append("provisional_unclassified")
            if candidate.get("classification_status") != "human_reviewed":
                reasons.append("not_human_verified")
            if len(filenames[raw["source_filename"].casefold()]) > 1:
                reasons.append("duplicate_filename_needs_identity_review")
        if reasons:
            queues.append({"source_id": f"pzwiki.icon.{index_id:06d}",
                           "source_index": index_id,
                           "filename": raw.get("source_filename") if raw else None,
                           "source_page": raw.get("source_file_page") if raw else None,
                           "rights": raw.get("rights") if raw else "unknown",
                           "proposed_category": candidate.get("proposed_category") if candidate else None,
                           "proposed_family": candidate.get("family_candidate") if candidate else None,
                           "review_state": "needs_evidence_not_auto_approved",
                           "reasons": reasons})
        if any(s in reasons for s in ("missing_source_record", "missing_classification", "source_filename_mismatch", "source_page_mismatch")):
            conflicts.append(queues[-1])
    raw_unclassified = [r for r in all_classes if r.get("proposed_category", "").lower().startswith("needs review")]
    # The prior 690 figure is a different on-device source-disposition count.
    # It must NOT be substituted for the mirrored provisional-classification count.
    summary = {
        "schema": "last_light.reference_audit.v4",
        "source": "checked_in_notion_research_mirror_read_only",
        "input_fingerprints": fingerprints,
        "item_reference_rows": len(all_icons),
        "classification_rows": len(all_classes),
        "provisional_unclassified_in_mirror": len(raw_unclassified),
        "historical_phone_source_status_needs_classification": 690,
        "phone_status_reverified_here": False,
        "human_verified_classification_rows": sum(r.get("classification_status") == "human_reviewed" for r in all_classes),
        "reference_rights": dict(sorted(Counter(r.get("rights", "unknown") for r in all_icons).items())),
        "media_rows_including_possible_category_memberships": len(all_media),
        "media_shards": len(media),
        "identity_conflicts": len(conflicts),
        "human_review_queue_rows": len(queues),
        "approval_state_changed": False,
        "limitations": [
            "Mirror classifications are provisional; a filename alone is not visual/object identity evidence.",
            "The historical 690 phone DB count and mirrored unclassified count describe different ledgers.",
            "Media gallery membership can duplicate underlying files and is not unique asset coverage.",
            "Real iPhone production.sqlite3 is not available to independently verify its dispositions."
        ]
    }
    atomic_bytes(output / "audit_summary.json", canonical(summary) + b"\n")
    atomic_bytes(output / "human_review_queue.jsonl", b"".join(canonical(row) + b"\n" for row in queues))
    atomic_bytes(output / "identity_conflicts.jsonl", b"".join(canonical(row) + b"\n" for row in conflicts))
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Read-only Notion research mirror audit")
    parser.add_argument("--source", type=Path, default=Path(__file__).resolve().parents[1] / "data/research")
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parents[1] / "review/v4_catalog_audit")
    args = parser.parse_args()
    print(json.dumps({k: v for k, v in audit(args.source, args.output).items() if k != "input_fingerprints"}, indent=2))


if __name__ == "__main__":
    main()
