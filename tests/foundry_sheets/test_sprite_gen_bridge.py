import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from tools.foundry_sheets.sprite_gen_bridge import bridge


class OfflineSpriteGenBridgeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / "frames").mkdir()
        self.records = []
        for state in ("idle", "walk"):
            for frame in range(2):
                filename = f"frames/{state}_{frame}.png"
                image = Image.new("RGBA", (16, 16))
                image.putpixel((frame + 1, 14), (255, 20, 10, 255))
                image.save(self.root / filename)
                self.records.append({"state": state, "heading": 0, "frame": frame,
                                     "fps": 8, "png": filename, "pivot": [8, 15]})
        self.spec = self.root / "interchange.json"

    def write(self):
        self.spec.write_text(json.dumps({"schema_version": 1, "asset_id": "ll_zombie_a",
                                         "frames": self.records}))

    def test_two_states_deterministic_and_alpha_exact(self):
        self.write()
        first = bridge(self.spec, self.root / "out")
        second = bridge(self.spec, self.root / "out2")
        self.assertEqual(first, second)
        self.assertEqual(len(first["frames"]), 4)
        self.assertEqual({f["state"] for f in first["frames"]}, {"idle", "walk"})
        self.assertFalse(first["golden_approved"])
        with Image.open(self.root / "out" / "sheet_0000.png") as atlas:
            for frame in first["frames"]:
                x, y, w, h = frame["region"]
                self.assertEqual((w, h), (1, 1))
                self.assertEqual(atlas.getpixel((x, y)), (255, 20, 10, 255))

    def test_traversal_rejected_without_output(self):
        self.records[0]["png"] = "../outside.png"
        self.write()
        with self.assertRaises(ValueError):
            bridge(self.spec, self.root / "out")
        self.assertFalse((self.root / "out").exists())

    def test_duplicate_rejected(self):
        self.records.append(dict(self.records[0]))
        self.write()
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            bridge(self.spec, self.root / "out")

    def test_invalid_rate_rejected(self):
        self.records[0]["fps"] = 0
        self.write()
        with self.assertRaises(ValueError):
            bridge(self.spec, self.root / "out")


if __name__ == "__main__":
    unittest.main()
