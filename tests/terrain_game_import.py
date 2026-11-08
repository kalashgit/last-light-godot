"""Validate static original terrain candidates installed for Godot rendering."""
import hashlib
import json
import sys
import unittest
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools" / "terrain_factory"))
import recipe
import pixel_finish


class GodotTerrainImport(unittest.TestCase):
    def test_native_import_manifest(self):
        base = ROOT / "assets" / "last_light" / "terrain" / "v1"
        doc = json.loads((base / "manifest.json").read_text())
        self.assertEqual(doc["installed_count"], 12)
        self.assertEqual(doc["full_recipe_count"], 106)
        self.assertEqual(doc["tile_px"], [80, 40])
        self.assertEqual(doc["anchor_px"], [40, 20])
        self.assertFalse(doc["founder_golden_approved"])
        self.assertFalse(doc["iphone_verified"])
        self.assertTrue(doc["preview_scene_only"])
        self.assertEqual(doc["source_recipe_sha256"], recipe.recipe_sha())
        self.assertEqual(doc["pixel_finish_source_sha256"],
                         hashlib.sha256(Path(pixel_finish.__file__).read_bytes()).hexdigest())
        canon = {j["asset_id"] for j in recipe.plan()["jobs"]}
        self.assertEqual(len(doc["tiles"]), len({a["asset_id"] for a in doc["tiles"]}))
        for entry in doc["tiles"]:
            self.assertIn(entry["asset_id"], canon)
            self.assertEqual(entry["anchor_px"], [40, 20])
            self.assertEqual(entry["tile_px"], [80, 40])
            self.assertTrue(entry["texture"].startswith("res://assets/last_light/terrain/v1/sprites/"))
            sprite = ROOT / entry["texture"].removeprefix("res://")
            self.assertEqual(hashlib.sha256(sprite.read_bytes()).hexdigest(),
                             entry["texture_sha256"])
            with Image.open(sprite) as img:
                self.assertEqual(img.size, (80, 40))
                rgba = img.convert("RGBA")
                for y in range(40):
                    for x in range(80):
                        self.assertEqual(bool(rgba.getpixel((x, y))[3]),
                                         pixel_finish.inside(x, y))


if __name__ == "__main__":
    unittest.main(verbosity=2)
