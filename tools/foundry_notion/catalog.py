"""Validate a frozen public-safe Notion snapshot and plan original-asset work orders.

This deliberately does not fetch private Notion content, execute AI agents, copy
reference imagery, or confer artistic approval.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

VALID_FAMILIES = frozenset({"prop", "tile", "vehicle", "animal", "animation", "character", "building", "ui", "mechanic"})
VALID_WORKERS = frozenset(f"F{i:02}" for i in range(1, 13))
VALID_PRIORITY = frozenset({"P0", "P1", "P2", "P3"})
VALID_STAGE = frozenset({"Backlog", "Original Design", "Generating", "QA Review", "Approved", "Blocked"})
IDENTITY = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{1,127}\Z")
PRIORITY = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
ORDER_SEQUENCE = re.compile(r"\AA00-B([0-9]{3})-")


def _distinct(rows: list[dict], field: str) -> None:
    values = [r.get(field) for r in rows]
    if any(not isinstance(v, str) or not IDENTITY.fullmatch(v) for v in values):
        raise ValueError(f"Invalid {field}")
    if len(values) != len(set(values)):
        raise ValueError(f"Duplicate {field}")


def validate(catalog: dict) -> None:
    if catalog.get("schema_version") != 1 or catalog.get("status") != "NOTION_READ_ONLY_SNAPSHOT_NOT_LIVE_SYNC":
        raise ValueError("Wrong source snapshot contract")
    coverage = catalog["coverage"]
    groups = (
        ("production_masters", "canonical_production_masters", "content_id"),
        ("world_specifications", "world_specifications", "world_id"),
        ("source_references", "source_reference_records", "reference_file_id"),
    )
    for group, count, ident in groups:
        rows = catalog[group]
        if not isinstance(rows, list) or len(rows) != coverage[count]:
            raise ValueError(f"Incomplete {group} snapshot")
        _distinct(rows, ident)
    if coverage["old_editable_3d_sources"] != 360 or coverage["old_3d_golden_approved"] != 0:
        raise ValueError("Original 360 must remain unapproved candidates")
    for record in catalog["production_masters"]:
        if record["family"] not in VALID_FAMILIES or record["stage"] not in VALID_STAGE:
            raise ValueError("Unknown asset family or stage")
        if record["priority"] not in VALID_PRIORITY:
            raise ValueError("Unknown priority")
        if record["queue"] is not None and record["queue"] not in VALID_WORKERS:
            raise ValueError("Unknown F01–F12 worker")
        for name in ("rights_reviewed", "founder_visual_approved", "technical_qa_passed", "godot_tested", "iphone_verified"):
            if type(record.get(name)) is not bool:
                raise ValueError(f"Missing boolean provenance field: {name}")
        # A sanitized GitHub snapshot has no signed human approval evidence.
        # A Notion 'Approved' stage must never be enough to bypass this.
        if record["founder_visual_approved"]:
            raise ValueError("Cannot certify Golden from an unsigned Notion snapshot")
    for record in catalog["source_references"]:
        if record["production_status"] != "Reference" or record["rights"] != "Research only":
            raise ValueError("Source research cannot be admitted as original game art")
    for record in catalog["world_specifications"]:
        if record["completion_tier"] != "Unresolved":
            raise ValueError("Unreviewed world research may not become gameplay-complete")


def plan(catalog: dict, completed: list[str] | None = None, batch_size: int = 4) -> dict:
    validate(catalog)
    if not isinstance(batch_size, int) or not 1 <= batch_size <= 10:
        raise ValueError("Work-order batch must contain 1 to 10 masters")
    done = completed or []
    masters = catalog["production_masters"]
    identities = {r["content_id"] for r in masters}
    if len(done) != len(set(done)) or not set(done).issubset(identities):
        raise ValueError("Unknown or duplicate completed work order")
    ready = [r for r in masters if r["semantic_verification"] == "Canonical Verified"
             and r["queue"] and r["work_order"] and r["stage"] != "Blocked"
             and r["content_id"] not in done]
    # Preserve Notion's A00-B001, B002, ... deliberately curated sequence
    # within a priority tier. In particular, F01's refrigerator Golden
    # calibration precedes less critical P0 small props.
    def _order_key(r: dict) -> tuple[int, int, str]:
        match = ORDER_SEQUENCE.match(r["work_order"])
        return (PRIORITY[r["priority"]], int(match.group(1)) if match else 999, r["content_id"])

    ready.sort(key=_order_key)
    payload = json.dumps(catalog, sort_keys=True, separators=(",", ":")).encode()
    orders = [{
        "content_id": r["content_id"], "family": r["family"], "worker": r["queue"],
        "priority": r["priority"], "canonical_work_order": r["work_order"],
        "task": "Author and test an independent original Blender recipe and candidate geometry",
        "mode": "RECIPE_AUTHORING_REVIEW_ONLY",
        "source_image_copy_allowed": False,
        "automatic_golden_promotion_allowed": False,
        "rights_review_required": not r["rights_reviewed"],
        "founder_visual_approved": False,
        "requires_f11_f12_and_godot_qa": True,
    } for r in ready[:batch_size]]
    return {
        "schema_version": 1, "catalog_sha256": hashlib.sha256(payload).hexdigest(),
        "snapshot_date": catalog["snapshot_date"], "queue_status": "READY" if orders else "NO_ADMITTED_WORK",
        "orders": orders, "eligible_remaining": len(ready)-len(orders),
        "master_count": len(masters), "legacy_source_models_pending_golden": 360,
        "unverified_master_count": sum(r["semantic_verification"] != "Canonical Verified" for r in masters),
        "reference_records_not_assets": len(catalog["source_references"]),
        "world_specifications_not_gameplay_complete": len(catalog["world_specifications"]),
        "golden_approved": False, "ai_execution_authorized": False,
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--catalog", type=Path, required=True)
    p.add_argument("--completed", type=Path)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--batch-size", type=int, default=4)
    a = p.parse_args()
    completed = json.loads(a.completed.read_text()) if a.completed and a.completed.exists() else []
    doc = plan(json.loads(a.catalog.read_text()), completed, a.batch_size)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(doc, indent=2) + "\n")
    print(f"FOUNDRY_NOTION_PLAN orders={len(doc['orders'])} remaining={doc['eligible_remaining']}")


if __name__ == "__main__":
    main()
