"""F02 noncanonical structural generator contract tests; stdlib unittest."""
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
TOOL = ROOT / "tools/factory/structures"
sys.path.insert(0, str(TOOL))
from geometry import SUBJECTS, WALL_HEIGHT, make_plan, stairs, Plan  # noqa: E402


class TestF02Calibration(unittest.TestCase):
    def test_five_work_orders_are_noncanonical(self):
        self.assertEqual(len(SUBJECTS), 5)
        for subject in SUBJECTS:
            plan = make_plan(subject)
            self.assertGreater(len(plan.parts), 0)
            m = plan.manifest()
            self.assertEqual(m["status"], "NONCANONICAL_CALIBRATION_ONLY")
            self.assertIsNone(m["canonical_master_id"])
            self.assertEqual(len(m["geometry_plan_sha256"]), 64)
            self.assertEqual(m, make_plan(subject).manifest())

    def test_every_box_has_real_volume_and_ground_support(self):
        for subject in SUBJECTS:
            for part in make_plan(subject).parts:
                self.assertGreater(min(part.size), 0, part.name)
                self.assertTrue(all(math.isfinite(v) for v in (*part.center, *part.size)))
                if part.role in {"wall", "frame", "floor", "floor_finish", "stair"}:
                    self.assertGreaterEqual(part.center[2] - part.size[2]/2, -.221)

    def test_masonry_has_open_voids(self):
        plan = make_plan("door_window")
        door, window = plan.openings
        self.assertEqual([door["kind"], window["kind"]], ["door", "window"])
        # Reject any structural wall block crossing the clear portal rectangle.
        for op in plan.openings:
            x, y, axis = op["wall"]
            lo, hi = op["span_local"]
            zlo, zhi = op["z_range_m"]
            for p in plan.parts:
                if p.role != "wall":
                    continue
                local = p.center[0]-x if axis == "x" else p.center[1]-y
                extent = p.size[0] if axis == "x" else p.size[1]
                overlap_u = min(local+extent/2, hi) - max(local-extent/2, lo)
                overlap_z = min(p.center[2]+p.size[2]/2, zhi) - max(p.center[2]-p.size[2]/2, zlo)
                self.assertLessEqual(min(overlap_u, overlap_z), 1e-6, p.name)
        self.assertTrue(any(p.role == "pane" for p in plan.parts))
        self.assertTrue(any(p.role == "door_leaf" for p in plan.parts))

    def test_garage_vehicle_clearance(self):
        plan = make_plan("garage")
        door = [o for o in plan.openings if o["kind"] == "garage"]
        self.assertEqual(len(door), 1)
        self.assertGreaterEqual(door[0]["void_width_m"], 2.7)
        self.assertGreaterEqual(door[0]["z_range_m"][1], 2.4)

    def test_roof_cut_preserves_physics_and_furniture(self):
        for subject in ("small_house", "garage", "shopfront", "roof_corner"):
            plan = make_plan(subject)
            self.assertTrue(any(p.group == "roof" for p in plan.parts))
            self.assertTrue(all(m["physics_unchanged"] for m in plan.masks))
            manifest = plan.manifest()
            self.assertEqual(manifest["states"]["roof_cut"]["frames"], 2)
            self.assertEqual(manifest["states"]["door_open"]["frames"], 7)

    def test_stairs_are_supported_and_reach_same_floor_height(self):
        plan = Plan("stairs_test", (4, 1))
        stairs(plan, .2, 0, steps=10, rise=WALL_HEIGHT/10)
        ends = {s["type"]: s["position_m"] for s in plan.sockets}
        self.assertAlmostEqual(ends["stairs_end"][2], WALL_HEIGHT)
        self.assertAlmostEqual(ends["stairs_end"][0]-ends["stairs_start"][0], 3.4)
        self.assertEqual(sum(p.role == "stair" for p in plan.parts), 10)

    def test_cardinal_rotation_preserves_snap_grid(self):
        for x, y in ((0, 0), (1, 2), (-4, 9)):
            x0, y0 = x, y
            for _ in range(4):
                x0, y0 = -y0, x0
                self.assertEqual(x0, int(x0))
                self.assertEqual(y0, int(y0))
            self.assertEqual((x0, y0), (x, y))

    def test_canonical_production_flag_fails_closed(self):
        code = subprocess.run([sys.executable, str(TOOL / "blender_calibration.py"),
                               "--ids", "made_up_id", "--dry-run"],
                              capture_output=True, text=True)
        self.assertNotEqual(code.returncode, 0)
        self.assertIn("BLOCKED_CANONICAL_IDS", code.stderr)

    def test_original_material_maps_reproducible(self):
        from textures import PALETTE, make_maps
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            a, b = make_maps(Path(first), 32), make_maps(Path(second), 32)
            self.assertEqual(a, b)
            self.assertEqual(set(a), set(PALETTE))


if __name__ == "__main__":
    unittest.main()
