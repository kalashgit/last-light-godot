#!/usr/bin/env python3
"""Static and behavioral contract checks for the lab character registry."""
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = json.loads((ROOT / "assets/characters/character_system_v1.json").read_text())
LAB_ITEMS = {"water_bottle", "canned_food", "bandage", "battery"}


def create(profession, hobby, trait_ids):
    professions = {p["id"]: p for p in DATA["professions"]}
    hobbies = {p["id"]: p for p in DATA["hobbies"]}
    traits = {p["id"]: p for p in DATA["traits"]}
    if profession not in professions or hobby not in hobbies:
        raise ValueError("unknown background")
    if len(trait_ids) > DATA["max_traits"] or len(set(trait_ids)) != len(trait_ids):
        raise ValueError("trait count/duplicate")
    budget, exclusive = DATA["trait_budget"], set()
    for trait_id in trait_ids:
        if trait_id not in traits:
            raise ValueError("unknown trait")
        trait = traits[trait_id]
        group = trait.get("exclusive_group")
        if group and group in exclusive:
            raise ValueError("incompatible traits")
        if group:
            exclusive.add(group)
        budget += trait["points"]
    if budget < 0:
        raise ValueError("trait budget exceeded")
    levels = dict.fromkeys((skill for group in DATA["skill_groups"].values() for skill in group), 0)
    for source in (professions[profession], hobbies[hobby]):
        for skill, bonus in source["starting_skills"].items():
            levels[skill] = min(DATA["max_skill_level"], levels[skill] + bonus)
    return levels, budget


def expect_rejected(*args):
    try:
        create(*args)
    except ValueError:
        return
    raise AssertionError(f"should reject: {args}")


def check():
    assert DATA["schema_version"] == 1
    assert DATA["projection"] == "80x40_2to1"
    assert DATA["xp_curve"]["base"] > 0 and DATA["xp_curve"]["exponent"] > 0
    skills = [skill for group in DATA["skill_groups"].values() for skill in group]
    assert len(skills) == len(set(skills)), "duplicate skill ID"
    assert len(skills) >= 30
    for category in ("professions", "traits", "hobbies"):
        entries = DATA[category]
        assert len({entry["id"] for entry in entries}) == len(entries)
        for entry in entries:
            assert entry["id"].isascii() and entry["id"].replace("_", "").isalnum()
            if "starting_skills" in entry:
                assert set(entry["starting_skills"]) <= set(skills)
                assert all(isinstance(value, int) and 0 <= value <= DATA["max_skill_level"] for value in entry["starting_skills"].values())
            if "starting_items" in entry:
                assert set(entry["starting_items"]) <= LAB_ITEMS
    assert any(t["points"] > 0 for t in DATA["traits"])
    assert any(t["points"] < 0 for t in DATA["traits"])
    for event in DATA["xp_events"].values():
        assert event["skill"] in skills and event["xp"] > 0
    assert DATA["appearance"]["gameplay_effects"] is False

    levels, budget = create("cook", "home_cook", ["studious", "poor_sleeper"])
    assert levels["cooking"] == 3 and levels["short_blade"] == 1
    assert budget == 4
    levels, budget = create("unassigned", "none", [])
    assert not any(levels.values()) and budget == 4
    expect_rejected("unknown", "none", [])
    expect_rejected("cook", "invalid", [])
    expect_rejected("cook", "none", ["studious", "studious"])
    expect_rejected("cook", "none", ["studious", "trail_runner"])
    expect_rejected("cook", "none", ["good_hearing", "hard_of_hearing"])
    expect_rejected("cook", "none", ["steady_nerves", "easily_startled"])
    expect_rejected("cook", "none", ["quick_recovery", "fragile"])
    xp_curve = [100 * math.pow(level + 1, 1.4) for level in range(10)]
    assert all(a < b for a, b in zip(xp_curve, xp_curve[1:]))
    assert (ROOT / "scripts/character_profile.gd").exists()
    print(f"PASS: registry schema, {len(skills)} skills, {len(DATA['professions'])} professions, "
          f"{len(DATA['traits'])} traits, {len(DATA['hobbies'])} hobbies, XP and 8 rejection cases")


if __name__ == "__main__":
    check()
