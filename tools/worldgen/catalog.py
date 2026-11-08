"""Load and cross-validate the data-driven definitions the generator consumes."""
from __future__ import annotations

from functools import lru_cache

from .core import DATA, ROOT, GenerationError, load_json


@lru_cache(maxsize=1)
def catalog() -> dict:
    c = {
        "archetypes": {r["archetype_id"]: r for r in load_json(DATA / "archetypes_60.json")["records"]},
        "programs": load_json(DATA / "building_programs.json")["programs"],
        "furniture": load_json(DATA / "furniture_catalog.json")["types"],
        "rules": load_json(DATA / "room_rules.json"),
        "loot": load_json(DATA / "loot_profiles.json")["profiles"],
        "styles": load_json(DATA / "district_styles.json"),
        "lab_a": load_json(DATA / "lab_a_v1.json"),
    }
    validate_catalog(c)
    return c


def asset_ids() -> set:
    manifest = ROOT / "assets" / "generated" / "factory" / "manifest.json"
    return {o["id"] for o in load_json(manifest)["objects"]} if manifest.exists() else set()


def item_ids() -> set:
    return {i["id"] for i in load_json(ROOT / "data" / "survival_items.json")["items"]}


def validate_catalog(c: dict) -> None:
    """Fail loudly on missing archetypes, unknown assets, loot items or furniture types."""
    if len(c["archetypes"]) != 60:
        raise GenerationError("E_ARCHETYPE_COUNT", str(len(c["archetypes"])))
    for pid, program in c["programs"].items():
        for key in ("archetype_id", "secondary_archetype_id"):
            if key in program and program[key] not in c["archetypes"]:
                raise GenerationError("E_MISSING_ARCHETYPE", f"{pid}:{program[key]}")
    assets = asset_ids()
    for fid, f in c["furniture"].items():
        if f.get("asset_id") is None:
            if f.get("art") != "placeholder_procedural":
                raise GenerationError("E_FURNITURE_ART", fid)
        elif assets and f["asset_id"] not in assets:
            raise GenerationError("E_UNKNOWN_ASSET", f"{fid}:{f['asset_id']}")
        if f.get("container") and f.get("loot_profile") not in c["loot"]:
            raise GenerationError("E_UNKNOWN_LOOT_PROFILE", fid)
    items = item_ids()
    for pid, entries in c["loot"].items():
        for entry in entries:
            if entry[0] not in items:
                raise GenerationError("E_UNKNOWN_ITEM", f"{pid}:{entry[0]}")
    for room, rules in c["rules"]["rooms"].items():
        for rule in rules:
            for t in rule.get("any_of", [rule.get("type")]):
                if t not in c["furniture"]:
                    raise GenerationError("E_UNKNOWN_FURNITURE", f"{room}:{t}")
    for sid, style in c["styles"]["styles"].items():
        for table in ("zoning", "corner_zoning"):
            for pid in style[table]:
                if pid not in c["programs"]:
                    raise GenerationError("E_UNKNOWN_PROGRAM", f"{sid}:{pid}")
