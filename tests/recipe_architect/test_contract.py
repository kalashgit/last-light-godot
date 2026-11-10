import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools.recipe_architect.contract import validate
from tools.recipe_architect.seed_recipes import SEEDS
from tools.recipe_architect.visual_qa import compare
from tools.recipe_architect.vision import model_inspection, pixel_report, recipe_from_analysis
from tools.recipe_architect.pilot import inspect_glb


class RecipeArchitectContractTests(unittest.TestCase):
    def setUp(self):
        self.recipe = SEEDS["vehicle_battery"]()

    def test_three_distinct_family_recipes_schema_pass(self):
        for family, factory in SEEDS.items():
            with self.subTest(family=family):
                r = validate(factory(), full_schema=True)
                self.assertGreaterEqual(len(r["components"]), 6)
                self.assertFalse(r["quality"]["golden_approved"])
                self.assertIsNone(r["identity"]["canonical_id"])

    def test_rejects_arbitrary_python_operator(self):
        r = copy.deepcopy(self.recipe)
        r["components"][0]["op"] = "python_eval"
        with self.assertRaises((ValueError, Exception)):
            validate(r, full_schema=True)

    def test_rejects_execution_in_geometry(self):
        r = copy.deepcopy(self.recipe)
        r["components"][0]["geometry"]["exec"] = "__import__('os').system('id')"
        with self.assertRaises(ValueError): validate(r, full_schema=True)

    def test_rejects_nonfinite(self):
        r = copy.deepcopy(self.recipe)
        r["components"][0]["location"][0] = float("nan")
        with self.assertRaises(Exception): validate(r, full_schema=True)

    def test_rejects_forged_founder_status(self):
        r = copy.deepcopy(self.recipe)
        r["quality"]["golden_approved"] = True
        with self.assertRaises(Exception): validate(r, full_schema=True)

    def test_rejects_parent_cycles(self):
        r = copy.deepcopy(self.recipe)
        a, b = r["components"][:2]
        a["parent"], b["parent"] = b["name"], a["name"]
        with self.assertRaises(ValueError): validate(r, full_schema=True)

    def test_rejects_wrong_image_sha(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "test.png"
            p.write_bytes(b"wrong pixels")
            with self.assertRaises(ValueError): validate(self.recipe, p, full_schema=True)

    def test_model_inference_requires_billing_permission(self):
        with self.assertRaises(PermissionError): model_inspection(Path("missing.png"))

    def test_cv_reads_real_pixels(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "image.png"
            im = Image.new("RGBA", (30, 20), (0, 0, 0, 0))
            ImageDraw.Draw(im).rectangle((8, 3, 20, 16), fill=(20, 30, 40, 255))
            im.save(p)
            report = pixel_report(p)
            self.assertEqual(report["alpha_bbox"], [8, 3, 21, 17])
            self.assertGreater(report["alpha_pixel_count"], 100)

    def test_no_generic_box_fallback_for_unknown_family(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "image.png"
            Image.new("RGBA", (8, 8), "red").save(p)
            with self.assertRaises(ValueError):
                recipe_from_analysis(p, {"analysis": {"category": "unknown_guitar"}, "method": "model_pixel_inference"})

    def test_comparison_rewards_better_silhouette(self):
        with tempfile.TemporaryDirectory() as d:
            directory = Path(d)
            source = Image.new("RGBA", (100, 100))
            ImageDraw.Draw(source).rectangle((20, 20, 80, 80), fill=(55, 55, 55, 255))
            source.save(directory / "source.png")
            close = Image.new("RGBA", (100, 100))
            ImageDraw.Draw(close).rectangle((20, 20, 80, 80), fill=(55, 55, 55, 255))
            close.save(directory / "close.png")
            wrong = Image.new("RGBA", (100, 100))
            ImageDraw.Draw(wrong).rectangle((45, 4, 55, 96), fill=(55, 55, 55, 255))
            wrong.save(directory / "wrong.png")
            good = compare(directory / "source.png", directory / "close.png")
            bad = compare(directory / "source.png", directory / "wrong.png")
            self.assertGreater(good["score"], bad["score"])

    def test_corrupt_glb_fails(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "empty.glb"
            p.write_bytes(b"glTF")
            with self.assertRaises(ValueError): inspect_glb(p)


if __name__ == "__main__": unittest.main()
