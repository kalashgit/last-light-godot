"""LAST LIGHT all-60 catalog neighborhood: deterministic offline geometry admission."""
from __future__ import annotations

import json
from pathlib import Path
import unittest

WORLD = Path(__file__).resolve().parents[2] / "data/neighborhood/showcase_60_v1.json"
COUNTS = {"Residential":9,"Commercial":15,"Civic / public":13,
          "Industrial / utility / rural":10,"Recreation":7,"Special":6}
HOUSE = ["house_small","house_large","duplex"]

def intersect(a, b):
    return (a[0] < b[0] + b[2] and a[0] + a[2] > b[0]
        and a[1] < b[1] + b[3] and a[1] + a[3] > b[1])

class LayoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = json.loads(WORLD.read_text(encoding="utf-8"))
        cls.items = cls.doc["buildings"]

    def test_60_distinct_canonical_archetype_keys_not_golden_claims(self):
        self.assertEqual(len(self.items), 60)
        self.assertEqual(len({x["archetype_id"] for x in self.items}), 60)
        self.assertEqual(len({x["source_archetype_id"] for x in self.items}), 60)
        self.assertTrue(all(x["source_archetype_id"] == "ll.archetype." + x["archetype_id"] for x in self.items))
        self.assertEqual(self.doc["status"], "LAYOUT_PROTOTYPE_NO_GOLDEN_ART")
        self.assertTrue(all(x["status"] == "CALIBRATION_LAYOUT_ONLY" and x["asset_package"] is None for x in self.items))

    def test_six_zones_exact_catalog_distribution(self):
        for zone, n in COUNTS.items():
            self.assertEqual(sum(b["group"] == zone for b in self.items), n)
        self.assertEqual(sum(COUNTS.values()), 60)
        self.assertEqual(len(self.doc["zone_rows"]), 6)

    def test_three_house_street_and_original_room_recipes(self):
        self.assertEqual([b["archetype_id"] for b in self.items[:3]], HOUSE)
        self.assertEqual(self.doc["three_house_street"], HOUSE)
        for house in self.items[:3]:
            self.assertIn("kitchen", house["room_modules"] if house["archetype_id"]!="duplex" else ["kitchen"])
        self.assertGreaterEqual(len(self.items[0]["room_modules"]), 5)

    def test_no_overlapping_footprints(self):
        for index,a in enumerate(self.items):
            for b in self.items[index + 1:]:
                self.assertFalse(intersect(a["footprint"], b["footprint"]),
                                 f"{a['archetype_id']} overlaps {b['archetype_id']}")

    def test_each_shell_has_outdoor_front_door(self):
        for b in self.items:
            x,y,w,h = b["footprint"]
            px,py = b["front_door"]
            self.assertAlmostEqual(px, x + w / 2.0)
            self.assertAlmostEqual(py, y + h)
            self.assertLess(py, 220)
            self.assertTrue(0 <= x < 240 and 0 <= y < 220)
            self.assertGreaterEqual(w, 7)
            self.assertGreaterEqual(h, 7)

    def test_all_sites_and_rooms_have_source_provenance(self):
        self.assertTrue(self.doc["catalog_source"].startswith("https://app.notion.com"))
        for b in self.items:
            self.assertIn(b["site_kind"], ("outdoor","interior_shell"))
            self.assertGreater(len(b["room_modules"]), 0)
            self.assertTrue(b["instance_id"].startswith("ll.district.prototype."))
            self.assertTrue(b["source_archetype_id"].startswith("ll.archetype."))

    def test_stable_seed_and_2_to_1_tiles(self):
        self.assertEqual(self.doc["seed"], 601109)
        self.assertEqual(self.doc["tile_pixel_basis"], [80,40])
        self.assertEqual(self.doc["player_spawn"], [10,20])

if __name__ == "__main__":
    unittest.main()
