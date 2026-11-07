"""Master import V1 regression; validate actual manifests without pretending Golden approval."""
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools" / "unified_factory"))
import import_godot as factory


class MasterImportV1(unittest.TestCase):
    def test_reject_traversal_and_duplicate_id(self):
        for p in ("../private/data.png", "/etc/passwd", "res://external.png", "abc\\evil.png"):
            with self.assertRaises(ValueError, msg=p):
                factory.relative_file(ROOT, p)
        for key in ("../../oops", "ll asset bad", "bad:asset"):
            with self.assertRaises(ValueError):
                factory.asset_id(key)

    def test_png_header_and_strict_projection(self):
        root = ROOT / "preview" / "vehicle-factory-v1"
        image = factory.relative_file(ROOT, "preview/vehicle-factory-v1/vehicle_16_headings.png")
        width, height = factory.png_size(image)
        self.assertGreater(width, 0)
        self.assertGreater(height, 0)
        good = factory.read_manifest(ROOT, Path("preview/vehicle-factory-v1/manifest.json"))
        self.assertEqual(good["tile_px"], [80, 40])
        self.assertEqual(good["heading_count"], 16)

    def test_import_every_actual_source_once_and_cache(self):
        dest = ROOT / "assets/generated/master_import_v1"
        result = factory.build(ROOT, dest)
        expected = {"item": 300, "actor": 5, "prop": 3, "vehicle": 3}
        self.assertEqual(result["source_counts"], expected)
        self.assertEqual(result["asset_count"], sum(expected.values()))
        self.assertEqual(len({x["stable_id"] for x in result["resources"]}), sum(expected.values()))
        self.assertTrue(all(not r["visual_approved"] and not r["integrated_gameplay"]
                            for r in result["resources"]))
        for r in result["resources"]:
            self.assertTrue((ROOT / r["resource_path"][6:]).is_file())
            self.assertTrue((ROOT / r["scene_path"][6:]).is_file())
            self.assertTrue(r["spriteframes_sha256"])
        actors = [r for r in result["resources"] if r["kind"] == "actor"]
        self.assertEqual(len(actors), 5)
        for r in actors:
            self.assertTrue(all("idle_" + d in r["animation_names"] for d in factory.DIRS))
        vehicles = [r for r in result["resources"] if r["kind"] == "vehicle"]
        self.assertTrue(all(len(v["animation_names"]) == 16 for v in vehicles))
        props = [r for r in result["resources"] if r["kind"] == "prop"]
        self.assertTrue(all("open" in p["animation_names"] and "close" in p["animation_names"]
                            for p in props))
        result_again = factory.build(ROOT, dest)
        self.assertEqual(result_again["generated_files_changed"], 0)
        self.assertEqual((dest / "catalog.json").read_text(),
                         json.dumps(result_again, indent=2) + "\n")

    def test_strict_resource_generation_has_atlas_frames_and_no_double_offsets(self):
        m = factory.read_manifest(ROOT, Path("preview/actor-factory-v1/manifest.json"))
        a = m["actors"][0]
        clip = a["clips"]["idle"]
        c = factory.checked_cell(clip["cell_px"], a["render_id"])
        tex = "res://preview/actor-factory-v1/" + clip["atlas"]
        frames = [factory.frame(tex, [i * c[0], 0, c[0], c[1]])
                  for i in range(clip["frame_count_per_direction"])]
        text = factory.indent_for_resource(a["render_id"], [tex],
                         [factory.animation("idle_front", frames)])
        self.assertIn('type="SpriteFrames"', text)
        self.assertIn('type="AtlasTexture"', text)
        self.assertIn('animations = [', text)
        self.assertIn('region = Rect2(', text)


if __name__ == "__main__":
    unittest.main()
