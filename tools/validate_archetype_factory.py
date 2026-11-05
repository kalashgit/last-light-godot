#!/usr/bin/env python3
"""Validate the 60-building catalog, factory and five existing lab bindings."""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from building_factory import load_catalog, archetypes, make_scaffold  # noqa: E402
from PIL import Image  # noqa: E402

FLOORS = {"wood_oak", "tile_ceramic", "concrete_stained", "vinyl_check", "asphalt_worn", "grass_sparse", "paver_gray"}
WALLS = {"plaster_cream", "concrete_block", "brick_aged", "metal_panel"}
ROOFS = {"shingle_asphalt", "standing_seam_metal", "flat_membrane"}
EXPECTED_FAMILIES = {"residential": 9, "commercial": 15, "civic": 13, "industrial": 10, "recreation": 7, "special": 6}


def check() -> None:
    catalog = load_catalog()
    assert catalog["schema_version"] == 1
    assert catalog["projection"] == "80x40_2to1"
    assert catalog["live_lab_building_limit"] == 5
    assert {family: len(entries) for family, entries in catalog["archetypes"].items()} == EXPECTED_FAMILIES
    entries = [a for group in catalog["archetypes"].values() for a in group]
    ids = [e["id"] for e in entries]
    assert len(ids) == len(set(ids)) == 60
    assert len(catalog["material_kits"]) == 8
    for kit in catalog["material_kits"].values():
        assert kit["wall"] in WALLS and kit["roof"] in ROOFS
        assert kit["floor"] in FLOORS and kit["secondary_floor"] in FLOORS
        assert kit["weathering"] in {"light", "medium", "heavy"}
    for profile_id, modules in catalog["room_profiles"].items():
        assert modules, f"empty profile: {profile_id}"
        assert all(module in catalog["room_modules"] for module in modules), profile_id
    for e in entries:
        assert e["kit"] in catalog["material_kits"] and e["profile"] in catalog["room_profiles"]
        assert all(isinstance(n, int) and n >= 4 for n in e["footprint_hint"])
        scaffold = make_scaffold(catalog, e["id"], 7)
        assert scaffold == make_scaffold(catalog, e["id"], 7), "nondeterministic scaffold"
        assert scaffold["status"] == "authored_scaffold_not_playable"
        assert all(room["approx_rect"][2] > 0 and room["approx_rect"][3] > 0 for room in scaffold["room_slots"])
        assert len(set(r["id"] for r in scaffold["room_slots"])) == len(scaffold["room_slots"])
        assert scaffold["asset_bill"]["prop_roles"] and scaffold["asset_bill"]["structural_parts"]
    lab = json.loads((ROOT / "assets/buildings/five_building_lab_v2.json").read_text())
    live = lab["buildings"]
    assert len(live) == catalog["live_lab_building_limit"] == len(catalog["lab_bindings"])
    seen = set()
    lookup = archetypes(catalog)
    for b in live:
        assert b["id"] in catalog["lab_bindings"]
        expected_id = catalog["lab_bindings"][b["id"]]
        assert b["archetype_id"] == expected_id and expected_id in lookup
        assert b["kit_id"] == lookup[expected_id]["kit"]
        assert expected_id not in seen
        seen.add(expected_id)
    assert len(seen) == 5
    try:
        make_scaffold(catalog, "not_a_real_location")
    except ValueError:
        pass
    else:
        raise AssertionError("unknown archetype must be rejected")
    preview_dir = ROOT / "assets/generated/architecture"
    manifest = json.loads((preview_dir / "manifest.json").read_text())
    image_path = preview_dir / manifest["asset"]
    assert hashlib.sha256(image_path.read_bytes()).hexdigest() == manifest["sha256"]
    with Image.open(image_path) as image:
        assert image.size == tuple(manifest["size_px"])
        assert image.format == "PNG"
    assert manifest["kit_ids"] == list(catalog["material_kits"])
    assert "not_runtime_art" in manifest["status"]
    print(f"PASS: {len(ids)} archetypes, {len(catalog['material_kits'])} kits, "
          f"{len(catalog['room_modules'])} room modules, {len(catalog['room_profiles'])} profiles, "
          f"5 unchanged lab footprints/bindings, deterministic scaffolds, original preview manifest")


if __name__ == "__main__":
    check()
