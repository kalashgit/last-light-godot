"""Guard the deliberately noncanonical survival pilot against accidental promotion."""

import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]


class SurvivalPilotContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules = json.loads((ROOT / "data/neighborhood/survival_pilot_v1.json").read_text())

    def test_separate_scene_and_save_slot(self):
        scene = (ROOT / "scenes/neighborhood_survival_v1.tscn").read_text()
        script = (ROOT / "scripts/neighborhood_survival_v1.gd").read_text()
        self.assertIn('res://scripts/neighborhood_survival_v1.gd', scene)
        self.assertIn('user://last_light_neighborhood_survival_pilot_v1.json', script)
        self.assertIn('run/main_scene="res://main.tscn"', (ROOT / "project.godot").read_text())

    def test_loot_is_prototype_only_and_deterministic(self):
        rules = self.rules
        self.assertEqual(rules["schema"], "last_light.neighborhood_survival_pilot.v1")
        self.assertIn("NONCANONICAL", rules["status"])
        self.assertEqual(len(rules["items"]), 4)
        for key, value in rules["items"].items():
            self.assertTrue(key.startswith("proto."))
            self.assertTrue(value["name"])
        for pool in rules["loot_by_room"].values():
            self.assertTrue(pool)
            self.assertTrue(all(item in rules["items"] for item in pool))
        script = (ROOT / "scripts/neighborhood_survival_v1.gd").read_text()
        self.assertIn("looted_objects[key] = item_id", script)
        self.assertIn('fixture_states[key] = true', script)
        self.assertNotIn("randi()", script)

    def test_zombie_ids_and_save_boundaries(self):
        ids = [z["id"] for z in self.rules["zombies"]]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(len(ids), 4)
        self.assertEqual(self.rules["zombies"][-1]["building_id"], "LAB-H01")
        script = (ROOT / "scripts/neighborhood_survival_v1.gd").read_text()
        self.assertIn("_line_clear", script)
        self.assertIn("_restore_snapshot", script)
        self.assertIn("DirAccess.rename_absolute", script)


if __name__ == "__main__":
    unittest.main()
