#!/usr/bin/env python3
"""Static contracts for 20 original lab items and existing save compatibility."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = json.loads((ROOT / "assets/items/lab_items_v1.json").read_text())
LAB = json.loads((ROOT / "assets/buildings/five_building_lab_v2.json").read_text())


def check():
    assert DATA["schema_version"] == 1
    assert DATA["status"] == "five_building_lab_candidate"
    items = DATA["items"]
    assert len(items) == 20
    names = {item["id"]: item for item in items}
    assert len(names) == len(items)
    assert {"canned_food", "water_bottle", "bandage", "battery"} <= set(names)
    assert names["canned_food"]["use"] == {"hunger": 32}
    assert names["water_bottle"]["use"] == {"thirst": 42}
    assert names["bandage"]["use"] == {"health": 20}
    categories = set()
    for entry in items:
        assert entry["id"].isascii() and entry["id"].replace("_", "").isalnum()
        assert entry["name"].strip() and len(entry["name"]) <= 32
        assert entry["category"] and entry["tags"]
        categories.add(entry["category"])
        assert entry["weight_kg"] > 0 and isinstance(entry["stack_max"], int) and 1 <= entry["stack_max"] <= 99
        assert set(entry["use"]) <= {"hunger", "thirst", "health"}
        assert all(isinstance(value, (int, float)) and 0 < value <= 100 for value in entry["use"].values())
    assert len(categories) >= 7
    loot = [f["loot"] for b in LAB["buildings"] for f in b["fixtures"] if f.get("loot")]
    assert len(loot) == 10 and len(set(loot)) >= 8
    assert all(item in names for item in loot)
    assert [b["id"] for b in LAB["buildings"]] == [
        "RESIDENTIAL HOUSE", "GARAGE / WORKSHOP", "SMALL SHOP", "GAS STATION", "ABANDONED OUTPOST"]
    gd = (ROOT / "scripts/lab_survival_state.gd").read_text()
    assert 'SCHEMA_VERSION := 1' in gd and 'last_light_five_building_lab_v1.json' in gd
    assert 'ITEM_REGISTRY_PATH := "res://assets/items/lab_items_v1.json"' in gd
    assert 'item_defs.has(item_id)' in gd
    print(f"PASS: {len(items)} original items, {len(categories)} categories, "
          f"{len(loot)} loot containers / {len(set(loot))} loot types, original save schema preserved")


if __name__ == "__main__":
    check()
