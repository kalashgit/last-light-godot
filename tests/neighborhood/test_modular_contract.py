"""Independent source-data checks for opt-in modular interiors and F01-F12 gating."""
from __future__ import annotations

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
KITS = json.loads((ROOT / "data/neighborhood/modular_room_kits_v1.json").read_text())
BINDINGS = json.loads((ROOT / "data/neighborhood/approved_asset_bindings_v1.json").read_text())
LEDGER = json.loads((ROOT / "docs/production/integration_v2/approval_ledger.json").read_text())
LAB = json.loads((ROOT / "data/neighborhood/house_lab_h01_h02_h03_v1.json").read_text())
CITY = json.loads((ROOT / "data/neighborhood/showcase_60_v1.json").read_text())


class ModularAssetContractTests(unittest.TestCase):
    def test_explicit_empty_approval_gate(self):
        self.assertEqual(BINDINGS["schema"], "last_light.neighborhood_asset_bindings.v1")
        self.assertEqual(BINDINGS["bindings"], [])
        self.assertEqual(LEDGER["schema_version"], 2)
        self.assertEqual(LEDGER["asset_approvals"], [])

    def test_room_kits_have_real_geometry_and_family_tags(self):
        self.assertEqual(KITS["schema"], "last_light.modular_room_kits.v1")
        self.assertGreaterEqual(len(KITS["rooms"]), 18)
        valid = {f"F{i:02}" for i in range(1, 13)}
        for room, fixtures in KITS["rooms"].items():
            self.assertGreaterEqual(len(fixtures), 1, room)
            for f in fixtures:
                self.assertIn(f["family"], valid)
                self.assertTrue(f["role"])
                self.assertEqual(len(f["at"]), 2)
                self.assertEqual(len(f["size"]), 2)
                self.assertTrue(all(0 < k < 1 for k in f["at"]), f)
                self.assertTrue(all(k > 0 for k in f["size"]), f)

    def test_all_authored_room_types_can_resolve(self):
        kinds = {str(r["type"]) for h in LAB["houses"] for r in h["rooms"] + h["upper_rooms"]}
        for kind in kinds:
            self.assertIn(kind, KITS["rooms"] | {k: None for k in KITS["aliases"]})

    def test_all_sixty_sites_have_blueprint_modules(self):
        for building in CITY["buildings"]:
            self.assertTrue(building["room_modules"], building["archetype_id"])
            self.assertIn(building["site_kind"], {"interior_shell", "outdoor"})


if __name__ == "__main__":
    unittest.main()
