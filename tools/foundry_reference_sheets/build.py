"""Build a fail-closed, machine-readable 3D authoring intake from founder sheets.

References are design observations, never a way to copy 2D art into Godot or
automatically confer semantic, source-rights, F11/F12 or Golden admission.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image

from .labels import labels

ROOT = Path(__file__).resolve().parents[2]
SOURCE_DIR = ROOT / "data/foundry_reference_catalog/founder_sheets_001_400"
MANIFEST = SOURCE_DIR / "sheets_manifest_v1.json"

# Suggestions only. Exact A00 identity and unique physical model still require review.
NOTION_CROSSWALK_SUGGESTIONS = {
    55: "ll_household_backpack", 58: "ll_household_backpack",
    129: "ll_farming_animal_feed_sack", 135: "ll_crafting_antler_pair",
    138: "ll_food_apple", 139: "ll_food_apple", 145: "ll_clothing_leather_apron",
    179: "ll_household_bucket",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def family(label: str) -> str:
    if any(word in label for word in ("backpack", "rucksack", "daypack", "school pack", "hiking pack", "messenger bag", "field backpack")):
        return "bags_equipment"
    if any(word in label for word in ("helmet", "apron", "armor", "guard", "coveralls", "jacket", "vest", "balaclava", "mask", "gloves", "robe", "jersey", "shorts", "cap", "beret", "hat", "boots", "bandana", "swimsuit")):
        return "clothing_armor"
    if any(word in label for word in ("book", "guide", "manual", "trilogy", "journal", "notebook")):
        return "books_paper"
    if any(word in label for word in ("bone", "spear", "knife", "axe", "hatchet", "mace", "rifle", "bat ", "club", "blade", "pistol", "ammunition", "trap")):
        return "weapons_and_parts"
    if any(word in label for word in ("food", "apple", "avocado", "banana", "beans", "berries", "bread", "beef", "bacon", "fruit", "bagel", "meat", "sweets", "roll", "biscuit", "cheese", "pepper", "grapes", "strawberry")):
        return "food_organic"
    if any(word in label for word in ("box", "tin", "case", "crate", "bucket", "bottle", "can", "pan", "flask", "carton", "sack", "tray")):
        return "containers_packages"
    return "tools_props_misc"


def parts_for(kind: str) -> list[str]:
    return {
        "bags_equipment": ["independent body volume", "seams and pockets", "handles and straps", "functional buckles or zippers"],
        "clothing_armor": ["hollow wearable shell", "layering and thickness", "seams or fasteners", "body attachment pivots"],
        "books_paper": ["cover boards or paper wrapper", "page block", "spine geometry", "original LAST LIGHT cover motif"],
        "weapons_and_parts": ["structural core", "distinct working end", "fasteners or grip", "physically plausible thickness"],
        "food_organic": ["nonuniform organic silhouette", "material-specific surface", "condition variants where applicable"],
        "containers_packages": ["empty interior volume", "real wall thickness", "lid or opening mechanism", "original generic labeling"],
        "tools_props_misc": ["independent original main body", "functional subcomponents", "physically plausible material boundaries"],
    }[kind]


def build(source_dir: Path = SOURCE_DIR) -> tuple[list[dict], dict]:
    manifest_path = source_dir / "sheets_manifest_v1.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("schema_version") != 1 or manifest.get("slot_gap") != list(range(191, 201)):
        raise ValueError("Unexpected source registry or missing-slot contract")
    if len(manifest.get("sheets", [])) != 8:
        raise ValueError("Exactly eight source sheets required")

    all_labels = labels()
    records = []
    cursor = 0
    referenced_numbers: set[int] = set()
    for sheet in manifest["sheets"]:
        source_file = source_dir / sheet["file"]
        if not source_file.is_file() or digest(source_file) != sheet["sha256"]:
            raise ValueError("Missing or changed founder source sheet: " + str(source_file))
        if sheet["last"] - sheet["first"] + 1 != sheet["columns"] * sheet["rows"]:
            raise ValueError("Sheet index/grid mismatch: " + sheet["file"])
        with Image.open(source_file) as source_image:
            if source_image.size != (sheet["width"], sheet["height"]):
                raise ValueError("Wrong source sheet dimensions: " + sheet["file"])
        for offset in range(sheet["columns"] * sheet["rows"]):
            index = sheet["first"] + offset
            if index in referenced_numbers:
                raise ValueError("Duplicate pictured slot " + str(index))
            referenced_numbers.add(index)
            row, col = divmod(offset, sheet["columns"])
            x0, x1 = (col * sheet["width"]) // sheet["columns"], ((col + 1) * sheet["width"]) // sheet["columns"]
            y0, y1 = (row * sheet["height"]) // sheet["rows"], ((row + 1) * sheet["height"]) // sheet["rows"]
            label = all_labels[cursor]
            cursor += 1
            kind = family(label)
            records.append({
                "schema_version": 1, "reference_id": f"LL-FGS-{index:04d}",
                "sheet_index": index, "working_label": label,
                "label_authority": "visual_observation_requires_semantic_review",
                "sheet_path": str((Path("data/foundry_reference_catalog/founder_sheets_001_400") / sheet["file"]).as_posix()),
                "sheet_sha256": sheet["sha256"], "cell_row": row, "cell_column": col,
                "cell_box_xyxy": [x0, y0, x1, y1],
                "notion_canonical_suggestion": NOTION_CROSSWALK_SUGGESTIONS.get(index),
                "suggestion_approved": False, "variant_dedup_review_required": True,
                "model_family_suggestion": kind,
                "geometry_parts_prompt": parts_for(kind),
                "authoring_contract": {
                    "mesh": "new, independently authored editable Blender geometry; no pixel extrusion, tracing or downloaded source mesh",
                    "materials": "independent PBR slots for real construction; wear tied to material and usage",
                    "representations": ["editable_blend", "glb", "64x64_rgba_inventory", "16_heading_isometric_world_renders"],
                    "lighting": "screen upper left, grounded contact shadow, consistent 2:1 isometric projection",
                    "content_isolation": "one isolated object, no unrelated contents; sets only where explicitly named",
                    "branding": "replace all existing names, characters, labels, insignia, logos and trade dress with independent LAST LIGHT designs",
                    "reference_pixels_as_game_texture_allowed": False,
                },
                "engine_handoff": "ORIGINAL_RECIPE_AUTHORING_INPUT",
                "queue_status": "NEEDS_CANONICAL_ID_AND_ORIGINAL_PHYSICAL_RECIPE",
                "technical_preview_produced": False,
                "admission": {
                    "semantic_verified": False, "rights_reviewed": False,
                    "original_recipe_approved": False, "production_model_admitted": False,
                    "f11_approved": False, "f12_approved": False,
                    "godot_tested": False, "iphone_verified": False,
                    "founder_3d_golden_approved": False,
                },
            })

    expected = set(range(1, 401)) - set(manifest["slot_gap"])
    if cursor != len(all_labels) or referenced_numbers != expected or len(records) != 390:
        raise ValueError("Missing, extra or out-of-order pictured slots")
    return records, {
        "schema_version": 1, "collection_id": manifest["collection_id"],
        "sheet_count": 8, "pictured_reference_count": len(records),
        "unpictured_slots": manifest["slot_gap"],
        "recipe_authoring_work_orders": len(records),
        "canonical_or_production_admitted": 0,
        "actual_3d_models_generated_by_intake": 0,
        "golden_3d_approved": 0,
        "status": "REFERENCE_TRANSFERRED_AUTHORING_PENDING",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", type=Path, default=SOURCE_DIR)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--verify-pinned", action="store_true")
    args = parser.parse_args()
    records, report = build(args.source_dir)
    outputs = {
        "model_reference_queue.jsonl": "".join(json.dumps(x, sort_keys=True) + "\n" for x in records),
        "intake_report.json": json.dumps(report, indent=2, sort_keys=True) + "\n",
    }
    if args.verify_pinned:
        for name, content in outputs.items():
            if not (args.output_dir / name).exists() or (args.output_dir / name).read_text(encoding="utf-8") != content:
                raise SystemExit("STALE_FOUNDER_REFERENCE_QUEUE: " + name)
    else:
        args.output_dir.mkdir(parents=True, exist_ok=True)
        for name, content in outputs.items():
            (args.output_dir / name).write_text(content, encoding="utf-8")
    print("FOUNDER_SHEETS_INTAKE_VALID", report["pictured_reference_count"], "missing", len(report["unpictured_slots"]), "admitted", report["canonical_or_production_admitted"])


if __name__ == "__main__":
    main()
