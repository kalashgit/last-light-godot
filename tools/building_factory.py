#!/usr/bin/env python3
"""Compile original, non-playable building design scaffolds from the catalog.

The emitted room slots and asset bill are authoring aids, not finished geometry,
collision, navigation, doors, sprites, or a map expansion.
"""
from __future__ import annotations

import argparse
import json
from math import ceil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "assets/buildings/building_archetypes_v1.json"


def load_catalog() -> dict:
    return json.loads(CATALOG.read_text(encoding="utf-8"))


def archetypes(catalog: dict) -> dict[str, dict]:
    return {entry["id"]: {**entry, "family": family}
            for family, entries in catalog["archetypes"].items() for entry in entries}


def make_scaffold(catalog: dict, archetype_id: str, seed: int = 0) -> dict:
    """Pure deterministic transformation; produces no playable map objects."""
    candidates = archetypes(catalog)
    if archetype_id not in candidates:
        raise ValueError(f"Unknown archetype ID: {archetype_id}")
    archetype = candidates[archetype_id]
    kit = catalog["material_kits"][archetype["kit"]]
    modules = catalog["room_profiles"][archetype["profile"]]
    w, h = archetype["footprint_hint"]
    cols = 1 if len(modules) == 1 else 2
    rows = ceil(len(modules) / cols)
    inner_width, inner_height = w - 2, h - 2
    room_slots = []
    for index, module_id in enumerate(modules):
        module = catalog["room_modules"][module_id]
        col, row = index % cols, index // cols
        x0 = 1.0 + inner_width * col / cols
        y0 = 1.0 + inner_height * row / rows
        room_slots.append({
            "id": f"{archetype_id}/room_{index:02d}_{module_id}",
            "module": module_id,
            "approx_rect": [round(x0, 3), round(y0, 3),
                            round(inner_width / cols, 3), round(inner_height / rows, 3)],
            "prop_roles": module["props"],
            "systems": module["systems"],
        })
    props = sorted({p for room in room_slots for p in room["prop_roles"]})
    systems = sorted({s for room in room_slots for s in room["systems"]})
    return {
        "schema_version": 1,
        "status": "authored_scaffold_not_playable",
        "archetype_id": archetype_id,
        "category": archetype["family"],
        "seed": seed,
        "material_kit": archetype["kit"],
        "look_variant": abs(seed) % 4,
        "projection": catalog["projection"],
        "footprint_hint": archetype["footprint_hint"],
        "surfaces": {name: kit[name] for name in ("wall", "roof", "floor", "secondary_floor")},
        "room_slots": room_slots,
        "asset_bill": {"prop_roles": props, "system_hooks": systems,
                       "structural_parts": ["floor_center", "floor_edge", "wall_run", "wall_corner",
                                            "door_opening", "window_opening", "roof_edge", "roof_occlusion"]},
        "missing_acceptance": ["authored_doors_and_windows", "walkable_navigation",
                               "collision_and_occlusion", "rendered_art", "interactive_loot",
                               "Godot_parser_and_playtest", "iPhone_touch_playtest"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archetype", help="Stable archetype ID, e.g. hospital")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--output", type=Path, help="Optional file to write; otherwise prints JSON")
    args = parser.parse_args()
    scaffold = make_scaffold(load_catalog(), args.archetype, args.seed)
    serialized = json.dumps(scaffold, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(serialized, encoding="utf-8")
        print(f"Wrote unplayable authoring scaffold: {args.output}")
    else:
        print(serialized, end="")


if __name__ == "__main__":
    main()
