"""GM00 data contracts (no Godot needed). Run: python3 -m unittest discover -s tests/gm00/py"""
import configparser
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def load(rel):
    return json.loads((ROOT / rel).read_text())


class SpawnCatalogContract(unittest.TestCase):
    def setUp(self):
        self.cat = load("data/sandbox/spawn_catalog_v1.json")

    def test_no_fabricated_canonical_ids(self):
        for e in self.cat["entries"]:
            self.assertIsNone(e["canonical_asset_id"], e["spawn_id"])
            self.assertEqual(e["art_status"], "PROVISIONAL_PROCEDURAL")
            self.assertTrue(e["spawn_id"].startswith(("prov.", "proto.")), e["spawn_id"])

    def test_candidate_keys_trace_to_queues(self):
        keys = set()
        for q in (ROOT / "docs/production/queues").glob("F*_v1.json"):
            for wo in json.loads(q.read_text())["calibration_work_orders"]:
                keys.add(wo["candidate_key"])
        for e in self.cat["entries"]:
            if e["candidate_key"]:
                self.assertIn(e["candidate_key"], keys)

    def test_all_14_categories_present_and_ids_unique(self):
        ids = [e["spawn_id"] for e in self.cat["entries"]]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(len(self.cat["categories"]), 14)
        for c in self.cat["categories"]:
            self.assertTrue(any(e["category"] == c for e in self.cat["entries"]), c)

    def test_catalog_is_reproducible(self):
        import subprocess, sys
        before = (ROOT / "data/sandbox/spawn_catalog_v1.json").read_text()
        subprocess.run([sys.executable, str(ROOT / "tools/build_spawn_catalog.py")], check=True, capture_output=True)
        self.assertEqual(before, (ROOT / "data/sandbox/spawn_catalog_v1.json").read_text())


class WorldRecipeContract(unittest.TestCase):
    def test_recipe_uses_only_catalog_archetypes(self):
        recipe = load("data/world/gm00_world_recipe_v1.json")
        catalog = load("data/neighborhood/showcase_60_v1.json")
        ids = {b["archetype_id"] for b in catalog["buildings"]}
        groups = {b["group"] for b in catalog["buildings"]}
        covered = set()
        for d in recipe["districts"]:
            covered.update(d["groups"])
            for f in d["fillers"]:
                self.assertIn(f["archetype_id"], ids)
        self.assertEqual(covered, groups, "every catalog group must be placed by a district")
        for k in recipe["stories_override"]:
            self.assertIn(k, ids)
        self.assertNotEqual(recipe["approval"], "FOUNDER_APPROVED")

    def test_rules_reference_existing_items(self):
        rules = load("data/world/gm00_world_rules_v1.json")
        items = load("data/neighborhood/survival_pilot_v1.json")["items"]
        for pool in rules["loot_by_room"].values():
            for item in pool:
                self.assertIn(item, items)
        kits = load("data/neighborhood/modular_room_kits_v1.json")["rooms"]
        for kind in kits:
            self.assertTrue(kind in rules["loot_by_room"] or kind in ("stairs",), kind)


class ProtectedScene(unittest.TestCase):
    def test_main_scene_unchanged(self):
        text = (ROOT / "project.godot").read_text()
        self.assertIn('run/main_scene="res://main.tscn"', text)


if __name__ == "__main__":
    unittest.main()
