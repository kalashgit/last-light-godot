"""Regression tests for the design-only catalog validator."""
import copy
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("validator", ROOT / "tools" / "validate_catalog.py")
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)
BASE = json.loads((ROOT / "data" / "catalog" / "starter_v1.json").read_text(encoding="utf-8"))

class TestCatalog(unittest.TestCase):
    def test_valid_proposed_catalog(self):
        self.assertEqual([], validator.validate(copy.deepcopy(BASE)))
    def test_duplicate_id_rejected(self):
        sample = copy.deepcopy(BASE)
        sample["items"].append(copy.deepcopy(sample["items"][0]))
        self.assertTrue(any("duplicate id" in e for e in validator.validate(sample)))
    def test_missing_loot_reference_rejected(self):
        sample = copy.deepcopy(BASE)
        sample["loot_profiles"][0]["entries"].append("item.fake.missing")
        self.assertTrue(any("unknown loot item" in e for e in validator.validate(sample)))
    def test_missing_prop_reference_rejected(self):
        sample = copy.deepcopy(BASE)
        sample["buildings"][0]["starter_props"].append("prop.fake.missing")
        self.assertTrue(any("unknown starter prop" in e for e in validator.validate(sample)))
    def test_unknown_capability_rejected(self):
        sample = copy.deepcopy(BASE)
        sample["items"][0]["capabilities"].append("teleportable")
        self.assertTrue(any("unknown capability" in e for e in validator.validate(sample)))
    def test_negative_item_weight_rejected(self):
        sample = copy.deepcopy(BASE)
        sample["items"][0]["weight_kg"] = -2
        self.assertTrue(any("invalid weight_kg" in e for e in validator.validate(sample)))
    def test_bad_id_rejected(self):
        sample = copy.deepcopy(BASE)
        sample["items"][0]["id"] = "INVALID/ID"
        self.assertTrue(any("bad id" in e for e in validator.validate(sample)))

if __name__ == "__main__":
    unittest.main()
