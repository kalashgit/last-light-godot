"""F02 structural integration contract checks (noncanonical calibration).

Run: python -m unittest discover -s tools/factory/structures -p 'test_integration_contract.py'
"""
import unittest
from geometry import SUBJECTS, make_plan, WALL_HEIGHT

class IntegrationContractTests(unittest.TestCase):
    def test_all_calibration_plans_are_noncanonical(self):
        for subject in SUBJECTS:
            with self.subTest(subject=subject):
                m = make_plan(subject).manifest()
                self.assertIsNone(m["canonical_master_id"])
                self.assertEqual(m["status"], "NONCANONICAL_CALIBRATION_ONLY")
                self.assertEqual(m["grid_approval"], "PENDING_W01_W04")

    def test_opening_has_matching_portal_socket(self):
        for subject in SUBJECTS:
            plan = make_plan(subject)
            for opening in plan.openings:
                kind = opening["kind"]
                expected = "window_hinge" if kind == "window" else "portal_link"
                self.assertTrue(any(s["type"] == expected and s.get("opening") == kind
                                    for s in plan.sockets), (subject, kind))
                self.assertGreater(opening["void_width_m"], 0)
                self.assertLessEqual(opening["z_range_m"][1], WALL_HEIGHT)

    def test_moving_parts_are_not_static_wall_parts(self):
        for subject in SUBJECTS:
            plan = make_plan(subject)
            for part in plan.parts:
                if part.group in ("door_leaf", "window_leaf", "garage_gate"):
                    self.assertNotEqual(part.role, "wall")
                    self.assertNotEqual(part.group, "structure")

    def test_roof_cutaway_is_non_destructive(self):
        for subject in ("small_house", "garage", "shopfront", "roof_corner"):
            plan = make_plan(subject)
            self.assertTrue(plan.masks)
            for mask in plan.masks:
                self.assertTrue(mask["physics_unchanged"])
                self.assertIn("roof_cut", mask["hidden_states"])
            self.assertTrue(any(p.group == "roof" for p in plan.parts))

    def test_stair_connectors_align_with_target_floor(self):
        plan = make_plan("stairs")
        start = next(s for s in plan.sockets if s["type"] == "stairs_start")
        end = next(s for s in plan.sockets if s["type"] == "stairs_end")
        self.assertAlmostEqual(start["position_m"][2], 0)
        self.assertAlmostEqual(end["position_m"][2], WALL_HEIGHT)
        self.assertGreater(end["position_m"][0], start["position_m"][0])

if __name__ == "__main__":
    unittest.main()
