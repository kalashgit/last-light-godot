"""A00/Notion/Sprite Bible V2 into provenance-safe original-art work orders.

All 21,025 PZwiki records are **research metadata**, never input image pixels.
This intake does not produce or approve any sprites; it prepares isolated,
auditable semantic/physical prompts for independent Blender authorship.
"""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re

IDENT = re.compile(r"ll_[a-z0-9_]{2,90}\Z")
SOURCE_PREFIX = "https://pzwiki.net/wiki/File:"
RESEARCH_RIGHTS = "source_research_only"
SOURCE_SEMANTIC_STATUSES = {
    "PROVISIONAL_METADATA_TRIAGE", "CANONICAL_SEMANTIC_IDENTITY_VERIFIED",
    "LINKED_TO_PREEXISTING_NOTION_MASTER", "LINKED_VERIFIED_MASTER_REFERENCE",
    "RECONCILED_CANONICAL_MASTER_SOURCE",
}
REQUIRED_RECIPE = ("proposed_brief", "geometry_and_dimensions", "materials_and_textures",
                   "animation_and_states", "render_and_pivot", "gameplay_and_physics")
PRODUCTION_STAGES = ("RECIPE_AUTHORING", "ORIGINAL_REFINEMENT_TECHNICAL_ONLY")


def digest(path: Path) -> str:
    d = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            d.update(block)
    return d.hexdigest()


def read_json(path: Path) -> dict:
    result = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(result, dict):
        raise ValueError(f"Expected JSON object: {path.name}")
    return result


def jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("".join(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n"
                            for row in rows), encoding="utf-8")


def validate_bible(bible: dict) -> None:
    if (bible.get("contract_id") != "LAST_LIGHT_MASTER_SPRITE_BIBLE_V2_ORIGINALITY_GATE"
            or bible.get("reference_policy", {}).get("original_asset_only") is not True
            or bible.get("reference_policy", {}).get("rights_evidence_or_authorship_receipt_required_before_final_art") is not True
            or bible.get("qa", {}).get("never_copy_source_pixel_data") is not True
            or bible.get("qa", {}).get("golden_requires_founder_decision") is not True
            or bible.get("production", {}).get("batch_original_items_per_inventory_sheet") != 40
            or bible.get("production", {}).get("heading_frames_per_world_source") != 16
            or bible.get("representations", {}).get("inventory_icon", {}).get("native_logical_px") != [64, 64]
            or bible.get("house_style", {}).get("key_light") != "screen_upper_left_soft_defined_10_to_11_oclock"):
        raise ValueError("Missing or weakened founder Sprite Bible V2 originality/style gate")


def validate_references(source: Path, manifest: dict) -> tuple[dict[int, dict], Counter]:
    files = manifest.get("files", [])
    if not files or len(files) != len({x["name"] for x in files}):
        raise ValueError("Missing or repeated A00 research ledger shards")
    expected = {x["name"] for x in files}
    actual = {p.name for p in source.iterdir() if p.is_file()}
    if actual != expected:
        raise ValueError(f"A00 shard set mismatch: absent={sorted(expected-actual)}, extra={sorted(actual-expected)}")
    ids: dict[int, dict] = {}
    classes: Counter = Counter()
    batches: Counter = Counter()
    for descriptor in sorted(files, key=lambda x: x["name"]):
        name = descriptor["name"]
        if not re.fullmatch(r"a00_20261108_b\d{3}_[a-z0-9_]+\.jsonl", name):
            raise ValueError(f"Untrusted ledger filename: {name}")
        path = source / name
        if path.is_symlink() or digest(path) != descriptor["sha256"]:
            raise ValueError(f"Tampered source ledger: {name}")
        with path.open(encoding="utf-8") as stream:
            for line_no, line in enumerate(stream, 1):
                record = json.loads(line)
                rid = record.get("source_page_id")
                if not isinstance(rid, int) or rid < 1 or rid in ids:
                    raise ValueError(f"Duplicate or invalid source ID {name}:{line_no}")
                if (record.get("rights") != RESEARCH_RIGHTS
                        or record.get("semantic_status") not in SOURCE_SEMANTIC_STATUSES
                        or not str(record.get("source_url", "")).startswith(SOURCE_PREFIX)):
                    raise ValueError(f"Third-party source may not be promoted {name}:{line_no}")
                if not isinstance(record.get("source_categories"), list):
                    raise ValueError(f"Untrusted source classifications {name}:{line_no}")
                ids[rid] = record
                classes[record["primary_class"]] += 1
                batches[record["batch_id"]] += 1
    if (len(ids) != manifest.get("expected_records")
            or len(ids) != manifest.get("expected_unique_ids")
            or dict(classes) != manifest.get("expected_classes")
            or dict(batches) != manifest.get("expected_batches")):
        raise ValueError("21,025 reference count/classification provenance mismatch")
    return ids, classes


def build(source: Path, inventory_path: Path, notion_path: Path, bible_path: Path,
          admission_path: Path, output: Path) -> dict:
    inventory = read_json(inventory_path)
    notion = read_json(notion_path)
    bible = read_json(bible_path)
    admission = read_json(admission_path)
    validate_bible(bible)
    source_by_id, classes = validate_references(source, inventory)
    masters = notion.get("production_masters", [])
    if (notion.get("source") != "NOTION_CANONICAL_ASSET_REGISTRY_READ_ONLY_EXPORT"
            or notion.get("golden_approved_by_export") is not False
            or len(masters) != notion.get("masters_total")
            or not isinstance(masters, list)):
        raise ValueError("Untrusted Notion canonical registry snapshot")
    admitted = admission.get("admitted_original_refinement_ids", [])
    if (admission.get("dispatch_total") != len(admitted)
            or len(admitted) != len(set(admitted))
            or admission.get("source_pixels_imported") is not False
            or admission.get("model_visual_verified") is not False):
        raise ValueError("Untrusted R03 admission snapshot")
    seen: set[str] = set()
    verified: list[dict] = []
    held: list[dict] = []
    for master in sorted(masters, key=lambda x: x["content_id"]):
        ident = master["content_id"]
        if ident in seen:
            raise ValueError(f"Duplicate canonical master: {ident}")
        seen.add(ident)
        if not IDENT.fullmatch(ident):
            held.append({"asset_id": ident, "reason": "UNAPPROVED_CANONICAL_ID_NAMESPACE",
                         "missing_source_page_ids": [], "notion_url": master.get("notion_url"),
                         "allowed_for_renderer": False})
            continue
        # Conflicting Notion approval claims must be held for founder evidence;
        # not silently interpreted as Golden or as authorization to render.
        if any(master.get(k) is not False for k in ("founder_visual_approved", "rights_reviewed")):
            held.append({"asset_id": ident, "reason": "FOUNDER_OR_RIGHTS_EVIDENCE_CONFLICT",
                         "missing_source_page_ids": [], "notion_url": master.get("notion_url"),
                         "allowed_for_renderer": False})
            continue
        refs = master.get("source_reference_ids", [])
        missing = [rid for rid in refs if rid not in source_by_id]
        verified_semantic = master.get("semantic_verification") == "Canonical Verified"
        complete = all(isinstance(master.get(k), str) and master[k].strip()
                       for k in REQUIRED_RECIPE)
        if not verified_semantic or not complete or missing:
            held.append({"asset_id": ident, "reason": (
                "SOURCE_PROVENANCE_RECONCILIATION" if missing else
                "SEMANTIC_VERIFICATION_REQUIRED" if not verified_semantic else "INCOMPLETE_PHYSICAL_RECIPE"),
                "missing_source_page_ids": missing, "notion_url": master.get("notion_url"),
                "allowed_for_renderer": False})
            continue
        is_admitted = ident in admitted
        # Renderer payload explicitly excludes copyrighted image links, titles,
        # source artwork and source pixel bytes. Source trace is QA-only.
        verified.append({
            "asset_id": ident,
            "owner_family": master.get("family"),
            "production_worker": master.get("production_queue"),
            "priority": master.get("production_priority"),
            "stage": PRODUCTION_STAGES[1] if is_admitted else PRODUCTION_STAGES[0],
            "automated_render_authorized": is_admitted,
            "generation_input": {
                "original_creation_only": True,
                "semantic_brief": master["proposed_brief"],
                "independent_geometry": master["geometry_and_dimensions"],
                "materials": master["materials_and_textures"],
                "construction": "Author independent usable component shapes; verify scale and physical assembly",
                "purpose": master["gameplay_and_physics"],
                "states": master["animation_and_states"],
                "representation": master["render_and_pivot"],
                "style_contract": bible["contract_id"],
                "source_image_pixels_allowed": False,
                "source_mesh_copy_allowed": False,
                "reference_silhouette_tracing_allowed": False,
            },
            "provenance_review_only": {
                "notion_url": master["notion_url"],
                "notion_work_order": master.get("source_work_order"),
                "source_page_ids": refs,
                "source_records_are_research_only": True,
            },
            "gates": {"notion_semantic_verified": True, "original_geometry_required": True,
                      "rights_reviewed": False, "f11_f12_approved": False,
                      "godot_world_tested": False, "iphone_verified": False,
                      "founder_golden_approved": False},
        })
    if len(seen) != len(masters) or not set(admitted).issubset(seen):
        raise ValueError("R03 admits missing canonical master")
    if len([x for x in masters if x["semantic_verification"] == "Canonical Verified"]) != notion["masters_semantic_verified"]:
        raise ValueError("Canonical verification status count drift")
    if any(x["asset_id"] not in admitted for x in verified if x["automated_render_authorized"]):
        raise ValueError("Refinement queue incorrectly admitted")
    source_candidates = [
        {"source_page_id": rid, "primary_class": row["primary_class"],
         "source_title": row["source_title"], "source_url": row["source_url"],
         "suggested_queue": row.get("suggested_queue"),
         "source_rights": RESEARCH_RIGHTS, "verified_original_recipe": False,
         "automated_render_authorized": False}
        for rid, row in sorted(source_by_id.items())
        if row["primary_class"] == "CANONICAL_MASTER_CANDIDATE"
    ]
    report = {
        "schema_version": 1, "source_records": len(source_by_id),
        "research_candidate_count": len(source_candidates),
        "primary_class_counts": dict(sorted(classes.items())),
        "notion_master_count": len(masters),
        "notion_semantic_verified": notion["masters_semantic_verified"],
        "reconciled_physical_recipes": len(verified),
        "provenance_hold_count": sum(bool(x["missing_source_page_ids"]) for x in held),
        "notion_hold_count": len(held),
        "refinement_admitted_valid": sum(x["automated_render_authorized"] for x in verified),
        "refinement_admitted_provenance_hold": len(admitted) - sum(x["automated_render_authorized"] for x in verified),
        "original_assets_rendered_by_this_step": 0, "founder_golden_approved": 0,
        "mass_sheet_items_required": 40,
        "ready_for_full_40_item_sheet": False,
        "status": "RESEARCH_AND_ORIGINAL_RECIPE_INTAKE_ONLY",
    }
    output.mkdir(parents=True, exist_ok=True)
    jsonl(output / "research_semantic_candidates.jsonl", source_candidates)
    jsonl(output / "original_recipe_work_orders.jsonl", verified)
    jsonl(output / "semantic_or_provenance_holds.jsonl", held)
    (output / "intake_report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print("LAST_LIGHT_ORIGINAL_INTAKE", json.dumps(report, sort_keys=True))
    return report


def main() -> None:
    root = Path(__file__).resolve().parents[2] / "data/foundry_reference_catalog"
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", type=Path, default=root / "source")
    parser.add_argument("--source-manifest", type=Path, default=root / "source_inventory_manifest_v1.json")
    parser.add_argument("--notion", type=Path, default=root / "notion_master_recipes_snapshot_v1.json")
    parser.add_argument("--bible", type=Path, default=root / "sprite_bible_contract_v2.json")
    parser.add_argument("--admission", type=Path, default=root / "r03_admitted_refinement_snapshot_v1.json")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    build(args.source_dir, args.source_manifest, args.notion, args.bible, args.admission, args.output)


if __name__ == "__main__":
    main()
