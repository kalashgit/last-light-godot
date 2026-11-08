"""Run: python -m unittest discover -s tests/factory/render_bridge -v"""
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
MODULE = ROOT / "tools/factory/render_bridge/atlas_layout.py"
spec = importlib.util.spec_from_file_location("f12_atlas_layout", MODULE)
atlas = importlib.util.module_from_spec(spec)
spec.loader.exec_module(atlas)
H = "a" * 64

def frame(key, w=12, h=18):
    return dict(key=key, width=w, height=h, duration_ms=100,
                direction=0, clip="idle", source_sha256=H)

class AtlasLayoutContract(unittest.TestCase):
    def test_deterministic_independent_of_order(self):
        frames = [frame(str(i), 12 + i, 18 + i) for i in range(12)]
        self.assertEqual(atlas.layout(frames, 64), atlas.layout(list(reversed(frames)), 64))
    def test_no_overlaps_or_out_of_bounds(self):
        output = atlas.layout([frame(str(i), 12, 18) for i in range(30)], 64, 2)
        self.assertGreater(output["pages"], 1)
        occupied = set()
        for f in output["frames"]:
            x, y, w, h = f["rect"]
            self.assertGreaterEqual(min(x, y), 2)
            self.assertLessEqual(max(x + w, y + h), 62)
            for px in range(x - 2, x + w + 2):
                for py in range(y - 2, y + h + 2):
                    cell = (f["page"], px, py)
                    self.assertNotIn(cell, occupied)
                    occupied.add(cell)
    def test_duplicate_rejected(self):
        with self.assertRaises(ValueError):
            atlas.layout([frame("a"), frame("a")])
    def test_bad_hash_rejected(self):
        bad = frame("bad")
        bad["source_sha256"] = "not a hash"
        with self.assertRaises(ValueError):
            atlas.layout([bad])
    def test_oversize_rejected(self):
        with self.assertRaises(ValueError):
            atlas.layout([frame("big", 100, 100)], 64)
    def test_invalid_duration_rejected(self):
        bad = frame("bad")
        bad["duration_ms"] = 0
        with self.assertRaises(ValueError):
            atlas.layout([bad])
    def test_invalid_direction_rejected(self):
        bad = frame("bad")
        bad["direction"] = 16
        with self.assertRaises(ValueError):
            atlas.layout([bad])

if __name__ == "__main__":
    unittest.main()
