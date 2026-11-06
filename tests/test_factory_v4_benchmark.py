"""Regression checks for review-only V4 component recipes (no approvals)."""
import copy
import importlib.util
import json
import pathlib
import tempfile
import unittest
import zipfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("ll_v4_benchmark", ROOT / "tools/factory_v4_benchmark.py")
factory = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(factory)
RECIPES = ROOT / "data/factory/v4_benchmark_12.json"


class V4BenchmarkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payload = json.loads(RECIPES.read_text(encoding="utf-8"))

    def test_exact_twelve_original_semantic_recipes(self):
        recipes = self.payload["recipes"]
        self.assertEqual(len(recipes), 12)
        self.assertEqual(len({r["id"] for r in recipes}), 12)
        for recipe in recipes:
            factory.validate_recipe(recipe)
            self.assertGreaterEqual(len(recipe["layers"]), 10)
            self.assertEqual(recipe["rights"], "original_independent_design")
            self.assertEqual(recipe["approval"], "candidate_needs_founder_review")
            self.assertTrue(recipe["semantic_brief"])

    def test_rendering_is_native_grid_and_transparent(self):
        fingerprints = set()
        for recipe in self.payload["recipes"]:
            image = factory.render(recipe)
            qa = factory.technical_qa(image)
            self.assertTrue(qa["technical_pass"])
            self.assertFalse(qa["founder_approved"])
            self.assertGreater(qa["occupied_fraction"], .03)
            fingerprints.add(factory.png_bytes(image))
        self.assertEqual(len(fingerprints), 12, "Distinct item identities must not share the same pixels")

    def test_invalid_rights_and_approval_are_rejected(self):
        original = self.payload["recipes"][0]
        for key, value in [("rights", "copied_source_pixels"), ("approval", "founder_approved"),
                           ("id", "ll.benchmark.../secret")]:
            recipe = copy.deepcopy(original)
            recipe[key] = value
            with self.assertRaises(ValueError):
                factory.validate_recipe(recipe)

    def test_nonsemantic_material_and_out_of_bounds_are_rejected(self):
        recipe = copy.deepcopy(self.payload["recipes"][0])
        recipe["layers"][0]["material"] = "crystal"
        with self.assertRaises(ValueError):
            factory.validate_recipe(recipe)
        recipe = copy.deepcopy(self.payload["recipes"][0])
        recipe["layers"][0]["points"][0][0] = 64
        with self.assertRaises(ValueError):
            factory.validate_recipe(recipe)

    def test_repeated_zip_is_identical_and_no_approvals_are_created(self):
        with tempfile.TemporaryDirectory() as folder:
            output = pathlib.Path(folder) / "rendered"
            first = factory.run(RECIPES, output)
            second = factory.run(RECIPES, output)
            self.assertEqual(first["package_sha256"], second["package_sha256"])
            self.assertEqual(first["source_recipe_sha256"], second["source_recipe_sha256"])
            self.assertEqual(first["count"], 12)
            self.assertEqual(first["art_approval"], "none")
            self.assertEqual(first["game_integration"], "none")
            self.assertEqual(len(list((output / "candidates").glob("*.png"))), 12)
            self.assertEqual(len(list((output / "reviews").glob("*.png"))), 6)
            self.assertFalse((output / "approved").exists())
            with zipfile.ZipFile(output / "LAST_LIGHT_V4_BENCHMARK_12_CANDIDATES.zip") as archive:
                self.assertIsNone(archive.testzip())
                self.assertEqual(len(archive.namelist()), 20)
                self.assertNotIn("approved", " ".join(archive.namelist()))


if __name__ == "__main__":
    unittest.main()
