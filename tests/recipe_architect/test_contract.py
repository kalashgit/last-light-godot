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
from tools.recipe_architect.visual_qa import compare, fitted_point
from tools.recipe_architect.vision import model_inspection, pixel_report, recipe_from_analysis
from tools.recipe_architect.pilot import inspect_glb, propose_component_shift


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

    def test_landmarks_must_be_observed_and_unique(self):
        r = copy.deepcopy(self.recipe)
        r["visual_analysis"]["landmarks"] = [{"component": "positive_terminal_post", "xy": [.7, .2], "confidence": .9}]
        validate(r, full_schema=True)
        r["visual_analysis"]["landmarks"].append(copy.deepcopy(r["visual_analysis"]["landmarks"][0]))
        with self.assertRaises(ValueError): validate(r, full_schema=True)
        r["visual_analysis"]["landmarks"][1]["component"] = "unknown_part"
        with self.assertRaises(ValueError): validate(r, full_schema=True)
        r["visual_analysis"]["landmarks"].pop()
        r["visual_analysis"]["landmarks"][0]["component"] = "main_battery_casing"
        r["components"][0]["observed"] = False
        with self.assertRaises(ValueError): validate(r, full_schema=True)

    def test_component_shift_solves_projected_defect_with_bound(self):
        comparison = {"landmarks": [{"component": "positive_terminal_post", "confidence": .95,
                                    "error": .1, "delta_xy": [.1, -.05],
                                    "local_xy_axes": [[1, 0], [0, 1]]}]}
        proposal = propose_component_shift(self.recipe, comparison)
        self.assertIsNotNone(proposal)
        trial, change = proposal
        self.assertEqual(change["component"], "positive_terminal_post")
        self.assertEqual(change["change"], "component_location_xy")
        self.assertLessEqual(sum(v * v for v in change["delta_local_m"]) ** .5, .090001)
        a = next(c for c in self.recipe["components"] if c["name"] == "positive_terminal_post")
        b = next(c for c in trial["components"] if c["name"] == "positive_terminal_post")
        self.assertEqual(a["location"][2], b["location"][2])
        self.assertEqual(self.recipe, SEEDS["vehicle_battery"]())

    def test_component_shift_refuses_singular_camera_projection(self):
        comparison = {"landmarks": [{"component": "positive_terminal_post", "confidence": .95,
                                    "error": .1, "delta_xy": [.1, -.05],
                                    "local_xy_axes": [[1, 0], [2, 0]]}]}
        self.assertIsNone(propose_component_shift(self.recipe, comparison))

    def test_landmark_comparison_measures_render_position(self):
        with tempfile.TemporaryDirectory() as d:
            directory = Path(d)
            im = Image.new("RGBA", (128, 128))
            ImageDraw.Draw(im).rectangle((20, 20, 108, 108), fill="grey")
            im.save(directory / "reference.png")
            projection = {"schema": "last-light.recipe-projections.v1", "heading": 0, "resolution": 128,
                          "components": {"positive_terminal_post": {"origin_px": [64, 64],
                                            "local_xy_axes_px_per_m": [[60, 0], [0, 60]]}}}
            target = fitted_point([64, 64], im)
            aligned = compare(directory / "reference.png", directory / "reference.png",
                              landmarks=[{"component": "positive_terminal_post", "xy": target, "confidence": 1}],
                              projection=projection)
            displaced = compare(directory / "reference.png", directory / "reference.png",
                                landmarks=[{"component": "positive_terminal_post", "xy": [.8, .6], "confidence": 1}],
                                projection=projection)
            self.assertEqual(aligned["landmark_error"], 0)
            self.assertGreater(aligned["score"], displaced["score"])
            self.assertEqual(displaced["defects"][0]["component"], "positive_terminal_post")


if __name__ == "__main__": unittest.main()
