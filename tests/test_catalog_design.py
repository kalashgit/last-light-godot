"""Schema contract tests for the design-only LAST LIGHT content catalog.

Executed by .github/workflows/content-catalog.yml. Does not run Godot.
"""
import copy
import json
import unittest
from pathlib import Path

from tools.validate_catalog import validate


CATALOG_PATH = Path(__file__).resolve().parent.parent / "data/catalog/starter_v1.json"


class CatalogContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))

    def test_starter_catalog_valid(self):
        self.assertEqual([], validate(self.catalog))

    def test_duplicate_definition_id_rejected(self):
        bad = copy.deepcopy(self.catalog)
        bad["items"][1]["id"] = bad["items"][0]["id"]
        self.assertTrue(any("duplicate id" in e for e in validate(bad)))

    def test_missing_loot_target_rejected(self):
        bad = copy.deepcopy(self.catalog)
        bad["loot_profiles"][0]["entries"].append("item.fake.lost")
        self.assertTrue(any("unknown loot item" in e for e in validate(bad)))

    def test_missing_building_prop_rejected(self):
        bad = copy.deepcopy(self.catalog)
        bad["buildings"][0]["starter_props"].append("prop.fake.unavailable")
        self.assertTrue(any("unknown starter prop" in e for e in validate(bad)))

    def test_unknown_capability_rejected(self):
        bad = copy.deepcopy(self.catalog)
        bad["props"][0]["capabilities"].append("teleport_player")
        self.assertTrue(any("unknown capability" in e for e in validate(bad)))

    def test_negative_item_weight_rejected(self):
        bad = copy.deepcopy(self.catalog)
        bad["items"][0]["weight_kg"] = -1
        self.assertTrue(any("invalid weight_kg" in e for e in validate(bad)))


if __name__ == "__main__":
    unittest.main()
