"""Run with: python -m unittest discover -s tests/factory/render_bridge -v"""
import json
import os
import unittest
from pathlib import Path


class CalibrationContract(unittest.TestCase):
    def test_real_blender_report(self):
        path = os.environ.get("F12_CAL_REPORT")
        if not path:
            self.skipTest("Set F12_CAL_REPORT to a genuine Blender CAL-01 report")
        report = json.loads(Path(path).read_text())
        self.assertEqual(report["canonical_status"], "CALIBRATION_ONLY_NONCANONICAL")
        self.assertEqual(report["tile_logical_pixels"], [80, 40])
        self.assertLess(report["max_absolute_residual_px"], 0.001)
        self.assertEqual(report["world_axis_mapping"], {
            "blender_x": "godot_y", "blender_y": "godot_x"})
        self.assertEqual(len(report["source_blend_sha256"]), 64)
        self.assertEqual(len(report["render_png_sha256"]), 64)
        from PIL import Image
        image = Image.open(Path(path).parent / "CAL-01_cube_rgba.png")
        self.assertEqual(image.mode, "RGBA")
        self.assertEqual(image.size, (256, 256))
        alpha = image.getchannel("A")
        lo, hi = alpha.getextrema()
        self.assertEqual(lo, 0)
        self.assertEqual(hi, 255)


if __name__ == "__main__":
    unittest.main()
