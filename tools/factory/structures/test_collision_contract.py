"""F02 collision proposal invariants. Run with pytest or unittest discovery."""
import unittest
from collision_contract import collision_proposal
from geometry import SUBJECTS


class CollisionContractTests(unittest.TestCase):
    def test_no_runtime_approval(self):
        for subject in SUBJECTS:
            data = collision_proposal(subject)
            self.assertIsNone(data["canonical_master_id"])
            self.assertFalse(data["approved_for_runtime"])
            self.assertFalse(data["navmesh_baked"])

    def test_dynamic_objects_never_in_static_colliders(self):
        for subject in SUBJECTS:
            data = collision_proposal(subject)
            static_names = {x["part"] for x in data["static_box_colliders"]}
            dynamic_names = {x["part"] for x in data["dynamic_box_candidates"]}
            self.assertFalse(static_names & dynamic_names)
            self.assertTrue(all(x["collision_policy"] == "W05_STATE_DRIVEN_PENDING"
                                for x in data["dynamic_box_candidates"]))

    def test_portal_metadata_retained(self):
        for subject in SUBJECTS:
            data = collision_proposal(subject)
            self.assertTrue(all(p["clear_width_m"] > 0 for p in data["portals"]))
            self.assertTrue(all(p["traversal"] == "W04_PENDING" for p in data["portals"]))

    def test_garage_vehicle_aperture(self):
        garage = collision_proposal("garage")
        apertures = [p for p in garage["portals"] if p["kind"] == "garage"]
        self.assertEqual(len(apertures), 1)
        self.assertAlmostEqual(apertures[0]["clear_width_m"], 2.76)

if __name__ == "__main__":
    unittest.main()
