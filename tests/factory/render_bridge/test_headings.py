"""F12 directional coverage regression tests."""
import importlib.util
import unittest
from pathlib import Path

module_path=Path(__file__).resolve().parents[3]/"tools/factory/render_bridge/verify_headings.py"
spec=importlib.util.spec_from_file_location("f12_verify_headings",module_path)
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

def frames(headings=16, count=3):
    return [dict(clip="idle",direction=d,frame_index=i) for d in range(headings) for i in range(count)]

class HeadingCoverageTests(unittest.TestCase):
    def test_complete_16_heading_animation(self):
        result=mod.verify_coverage(frames())
        self.assertEqual(result["clips"]["idle"]["total_frames"],48)
    def test_supported_8_heading_animation(self):
        self.assertEqual(mod.verify_coverage(frames(8),8)["clips"]["idle"]["headings"],8)
    def test_missing_heading_rejected(self):
        with self.assertRaises(ValueError):
            mod.verify_coverage(frames()[:-3])
    def test_duplicate_frame_rejected(self):
        f=frames()
        with self.assertRaises(ValueError):
            mod.verify_coverage(f+[f[0]])
    def test_missing_timeline_frame_rejected(self):
        f=[v for v in frames() if not (v["direction"]==3 and v["frame_index"]==1)]
        with self.assertRaises(ValueError):
            mod.verify_coverage(f)
    def test_noncontiguous_indices_rejected(self):
        f=frames()
        for v in f:
            v["frame_index"]+=1
        with self.assertRaises(ValueError):
            mod.verify_coverage(f)
    def test_unsupported_heading_count_rejected(self):
        with self.assertRaises(ValueError):
            mod.verify_coverage(frames(),12)

if __name__=="__main__":
    unittest.main()
