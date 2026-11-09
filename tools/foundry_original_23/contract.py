"""Fail-closed contract for LAST LIGHT original-authoring batch 23–45.

The Notion record's `Stage=Approved` is NOT semantic, production, F11/F12,
Godot, or founder approval. The factory may make technical previews only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


EXPECTED_IDS = (
    "ll_crafting_antler_pair", "ll_clothing_leather_apron",
    "ll_equipment_canvas_bandolier", "ll_clothing_improvised_plastic_apron",
    "ll_equipment_leather_bandolier", "ll_farming_animal_feed_sack",
    "ll_tools_claw_hammer", "ll_crafting_rope_coil",
    "ll_clothing_leather_jacket", "ll_crafting_duct_tape",
    "ll_tools_flat_screwdriver", "ll_tools_hatchet",
    "ll_medical_sterile_bandage", "ll_clothing_hiking_boots",
    "ll_household_duffel_bag", "ll_food_water_bottle",
    "ll_household_backpack", "ll_medical_antibiotic_tablets",
    "ll_household_field_notebook", "ll_medical_first_aid_case",
    "ll_household_shoe_box", "ll_food_apple", "ll_food_bean_tin",
)

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST = ROOT / "data/foundry_reference_catalog/batch_23_45_original_recipes_v1.json"
MASTER = ROOT / "data/foundry_reference_catalog/notion_master_recipes_snapshot_v1.json"


def checksum(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_manifest(doc: dict, master_path: Path | None = None) -> dict:
    errors = []
    assets = doc.get("assets", [])
    if doc.get("count") != 23 or len(assets) != 23:
        errors.append("Exactly 23 independent original asset recipes required")
    ids = tuple(a.get("asset_id") for a in assets)
    if ids != EXPECTED_IDS:
        errors.append("Canonical ID order mismatch, duplicate, or wrong asset")
    if doc.get("source_art_pixels_imported") is not False:
        errors.append("Cannot import source artwork/pixels")
    if doc.get("inventory_sheet_min_unique") != 40:
        errors.append("Forty-distinct-asset page minimum must remain enforced")

    for a in assets:
        ident = a.get("asset_id", "<missing>")
        prefix = ident + ": "
        if not a.get("notion_url", "").startswith("https://") or not a.get("brief"):
            errors.append(prefix + "missing canonical Notion evidence or descriptive brief")
        if a.get("source_reference_ids") != []:
            errors.append(prefix + "research reference must not be fabricated")
        if a.get("source_status") != "NOTION_UNREVIEWED_ORIGINAL_DESIGN_PROPOSAL":
            errors.append(prefix + "semantic stage mismatch")
        if a.get("originality_scope") != "INDEPENDENT_GEOMETRY_MATERIALS_LABELS_NO_SOURCE_PIXELS_OR_TRADE_DRESS":
            errors.append(prefix + "originality scope weakened")
        dimensions = a.get("nominal_dimensions_m", [])
        if len(dimensions) != 3 or any(not isinstance(x, (int, float)) or x <= 0 or x > 10 for x in dimensions):
            errors.append(prefix + "invalid three-dimensional physical envelope")
        if len(a.get("material_slots", [])) < 1 or len(set(a.get("material_slots", []))) != len(a.get("material_slots", [])):
            errors.append(prefix + "missing or duplicate material identities")
        if not a.get("archetype") or not a.get("states") or not a.get("gameplay_roles"):
            errors.append(prefix + "missing original geometry/state/gameplay contract")
        if a.get("kind") in ("wearable", "weapon", "container") and not a.get("attachment_sockets"):
            errors.append(prefix + "missing equipment/interaction sockets")
        geometry = a.get("geometry_recipe", {})
        if geometry.get("mesh_strategy") != "parametric_original_parts" or geometry.get("editable_blend_required") is not True:
            errors.append(prefix + "source Blender geometry contract missing")
        inventory = a.get("inventory", {})
        if inventory.get("logical_resolution_px") != [64, 64] or inventory.get("background") != "transparent_RGBA":
            errors.append(prefix + "inventory must be 64x64 alpha sprite")
        if inventory.get("check_readability_at_px") != [32, 48, 64]:
            errors.append(prefix + "inventory readability probes missing")
        world = a.get("world", {})
        if world.get("render_headings") != 16 or world.get("heading_degrees_increment") != 22.5:
            errors.append(prefix + "F12 16-heading contract changed")
        if world.get("godot_tested") is not False or world.get("iphone_verified") is not False:
            errors.append(prefix + "untested gameplay/device falsely certified")
        qa = a.get("visual_qa", {})
        if qa.get("qa_score") is not None or qa.get("originality_provenance") != "REQUIRES_INDEPENDENT_ART_REVIEW":
            errors.append(prefix + "visual/originality review has not yet happened")
        admission = a.get("admission", {})
        if admission.get("semantic_status") != "UNREVIEWED" or admission.get("technical_preview_allowed") is not True:
            errors.append(prefix + "preview admission mismatch")
        for field in ("production_render_admitted", "rights_reviewed", "f11_approved", "f12_approved", "founder_golden_approved"):
            if admission.get(field) is not False:
                errors.append(prefix + field + " must remain false")

    if master_path is not None:
        if not master_path.is_file():
            errors.append("Pinned Notion master registry missing")
        else:
            master = json.loads(master_path.read_text(encoding="utf-8"))
            rows = master if isinstance(master, list) else next((master[k] for k in ("production_masters", "rows", "assets", "records") if isinstance(master.get(k), list)), [])
            masters = {r.get("content_id") or r.get("asset_id") or r.get("Asset ID"): r for r in rows}
            for a in assets:
                ident = a["asset_id"]
                source = masters.get(ident)
                if not source:
                    errors.append("Candidate ID missing from pinned canonical Notion snapshot: " + ident)
                    continue
                for a_key, m_key in (("notion_url", "notion_url"), ("brief", "proposed_brief"), ("notion_stage", "stage")):
                    if a[a_key] != source[m_key]:
                        errors.append("Pinned Notion provenance differs for " + ident + ": " + a_key)
                if source.get("semantic_verification") != "Unreviewed" or source.get("automation_gate") != "HOLD":
                    errors.append("Source verification/admission changed; re-author and re-audit: " + ident)

    return {
        "batch_id": doc.get("batch_id"), "asset_count": len(assets),
        "identities_reconciled": not any("ID" in x or "Canonical" in x for x in errors),
        "source_art_pixels_imported": False, "technical_preview_count": len(assets) if not errors else 0,
        "production_admitted_count": 0, "forty_item_pages_eligible": 0,
        "founder_golden_approved_count": 0, "status": "PASS_PREVIEW_ONLY" if not errors else "FAIL_CLOSED",
        "errors": errors,
    }


def build_render_plan(build_root: Path, output: Path) -> dict:
    """Only source-hashed GLB previews; never manufactures an R03 approval."""
    selected = []
    for ident in EXPECTED_IDS:
        folder = build_root / ident
        glb = folder / (ident + ".glb")
        receipt = folder / "authorship_receipt.json"
        if not glb.exists() or not receipt.exists():
            continue
        evidence = json.loads(receipt.read_text())
        if evidence.get("asset_id") != ident or evidence.get("glb_sha256") != checksum(glb):
            raise ValueError("Source provenance/hash discrepancy: " + ident)
        for flag in ("semantic_admitted", "founder_golden_approved", "f11_approved", "f12_approved"):
            if evidence.get(flag) is not False:
                raise ValueError("False source approval in receipt: " + ident)
        selected.append({"asset_id": ident, "glb_path": str(glb.resolve()), "glb_sha256": checksum(glb)})
    if not selected:
        raise ValueError("No real independently generated GLB files to render")
    plan = {"schema_version": 1, "status": "READY", "selected": selected,
            "admission": "TECHNICAL_ONLY_NOT_R03_OR_GOLDEN"}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(plan, indent=2) + "\n")
    return plan


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--build-root", type=Path)
    p.add_argument("--plan-output", type=Path)
    opt = p.parse_args()
    doc = json.loads(opt.manifest.read_text())
    report = check_manifest(doc, MASTER)
    opt.output.parent.mkdir(parents=True, exist_ok=True)
    report["manifest_sha256"] = checksum(opt.manifest)
    opt.output.write_text(json.dumps(report, indent=2) + "\n")
    if report["errors"]:
        raise SystemExit("Original-authoring admission FAIL_CLOSED: " + "; ".join(report["errors"]))
    if opt.build_root is not None:
        if opt.plan_output is None:
            raise SystemExit("--plan-output required with --build-root")
        build_render_plan(opt.build_root, opt.plan_output)
    print("LL_23_45_CONTRACT_PASS_PREVIEW_ONLY", report["asset_count"], "production=0, golden=0")


if __name__ == "__main__":
    main()
