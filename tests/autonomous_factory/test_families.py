import copy
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("m02_families", ROOT / "tools/autonomous_factory/families.py")
families = importlib.util.module_from_spec(spec)
spec.loader.exec_module(families)
DATA = json.loads(families.REGISTRY.read_text())


class FamilyRegistryTests(unittest.TestCase):
    def test_complete_twelve_family_census(self):
        plan = families.plan(DATA, "ALL")
        self.assertEqual(len(plan["ready"]) + len(plan["blocked"]), 12)
        self.assertEqual(plan["ready"], ["F01"])
        self.assertEqual(len(plan["golden_approved"]), 0)

    def test_missing_or_duplicate_family_rejected(self):
        for change in (lambda x: x["families"].pop(),
                       lambda x: x["families"].__setitem__(1, x["families"][0])):
            registry = copy.deepcopy(DATA)
            change(registry)
            with self.assertRaises(ValueError):
                families.validate(registry)

    def test_unverified_family_never_executes(self):
        for code in [f"F{i:02d}" for i in range(2, 13)]:
            plan = families.plan(DATA, code)
            self.assertFalse(plan["ready"])
            self.assertEqual(plan["blocked"][0]["id"], code)

    def test_fabricated_adapter_and_approval_rejected(self):
        registry = copy.deepcopy(DATA)
        registry["families"][9]["adapter"] = "f10_unverified"
        registry["families"][9]["readiness"] = "CALIBRATION_RUNNABLE"
        with self.assertRaises(ValueError):
            families.validate(registry)
        registry = copy.deepcopy(DATA)
        registry["families"][0]["canonical_promotion"] = True
        with self.assertRaises(ValueError):
            families.validate(registry)


if __name__ == "__main__":
    unittest.main()
