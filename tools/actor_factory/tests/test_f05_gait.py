"""F05 pure gait contract regressions independent of Blender runtime."""
import importlib.util
import math
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location("f05_gait", Path(__file__).resolve().parents[1] / "f05_gait.py")
gait = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gait)

class TestF05Gait(unittest.TestCase):
    def test_phase_loop_continuity(self):
        for clip in gait.LOCOMOTION:
            for side in (-1, 1):
                a = gait.gait_pose(clip, 0, side)
                b = gait.gait_pose(clip, 1, side)
                for axis in a:
                    self.assertAlmostEqual(a[axis], b[axis], places=9)
            a = gait.torso_pose(clip, 0)
            b = gait.torso_pose(clip, 1)
            for axis in a:
                self.assertAlmostEqual(a[axis], b[axis], places=9)

    def test_opposed_legs_and_arm_swings(self):
        for clip in gait.LOCOMOTION:
            for phase in (.125, .25, .375, .625, .75):
                left = gait.gait_pose(clip, phase, 1)
                right = gait.gait_pose(clip, phase, -1)
                self.assertAlmostEqual(left["hip_x"], -right["hip_x"])
                self.assertAlmostEqual(left["arm_x"], -right["arm_x"])
                self.assertLessEqual(left["hip_x"] * left["arm_x"], 0)

    def test_knee_bends_nonnegative_with_ankle_counterrotation(self):
        for clip in gait.LOCOMOTION:
            for side in (-1, 1):
                samples = [gait.gait_pose(clip, i / 32, side) for i in range(32)]
                self.assertGreater(max(p["knee_x"] for p in samples), 0)
                self.assertGreaterEqual(min(p["knee_x"] for p in samples), 0)
                self.assertTrue(all(abs(p["ankle_x"]) < .40 for p in samples))

    def test_distinct_gaits_with_counterrotating_torso(self):
        run = gait.gait_pose("run", .25, 1)
        walk = gait.gait_pose("walk", .25, 1)
        sneak = gait.gait_pose("sneak", .25, 1)
        self.assertGreater(run["hip_x"], walk["hip_x"])
        self.assertGreater(walk["hip_x"], sneak["hip_x"])
        for clip in gait.LOCOMOTION:
            p = gait.torso_pose(clip, .25)
            self.assertLess(p["pelvis_z"] * p["chest_z"], 0)

    def test_invalid_inputs_fail(self):
        with self.assertRaises(ValueError):
            gait.gait_pose("death", .25, 1)
        with self.assertRaises(ValueError):
            gait.gait_pose("walk", .25, 0)

if __name__ == "__main__":
    unittest.main()
