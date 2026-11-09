"""F02 aperture audit regression checks."""
import unittest
from audit_apertures import audit_apertures
from geometry import SUBJECTS

class ApertureAuditTests(unittest.TestCase):
    def test_walkable_portals_are_not_blocked_by_static_boxes(self):
        for subject in SUBJECTS:
            with self.subTest(subject=subject):
                report = audit_apertures(subject)
                self.assertTrue(report["passed"], report["static_blockers"])
                self.assertFalse(report["godot_physics_verified"])

    def test_garage_aperture_has_no_static_center_blocker(self):
        report = audit_apertures("garage")
        self.assertEqual(report["walkable_portals_checked"], 1)
        self.assertEqual(report["static_blockers"], [])

    def test_windows_are_not_walkable_portals(self):
        report = audit_apertures("door_window")
        self.assertEqual(report["walkable_portals_checked"], 1)

if __name__ == "__main__":
    unittest.main()
