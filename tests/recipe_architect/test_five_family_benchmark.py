"""Truthful benchmark orchestration tests; no model accuracy claim here."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools.foundry_reference_sheets.build import family
from tools.recipe_architect.five_family_benchmark import (
    REQUIRED_FAMILIES, bbox_iou, prepare, run, score_case,
)


class FiveFamilyBenchmarkTests(unittest.TestCase):
    def test_catalog_does_not_confuse_hatchet_with_hat_or_shelf_with_misc(self):
        self.assertEqual(family("small steel hatchet"), "weapons_and_parts")
        self.assertEqual(family("wooden wall shelf"), "furniture_fixtures")
        self.assertEqual(family("dark green avocado"), "food_organic")
        self.assertEqual(family("ice cream apron"), "clothing_armor")
        self.assertEqual(family("black daypack"), "bags_equipment")

    def test_six_privately_cropped_cases_cover_five_families_and_no_fake_inference(self):
        with tempfile.TemporaryDirectory() as temp:
            packet = Path(temp) / "packet"
            status = prepare(packet, include_human_seed_baselines=True)
            self.assertEqual({c["family"] for c in status["cases"]}, REQUIRED_FAMILIES)
            self.assertEqual(len(status["cases"]), 6)
            self.assertEqual(status["real_model_inference_count"], 0)
            self.assertFalse(status["benchmark_complete"])
            self.assertFalse(status["founder_golden_approved"])
            for case in status["cases"]:
                self.assertTrue((packet / case["source_file"]).exists())
                self.assertTrue(case["source_sha256"])
            self.assertEqual(status["ready_recipe_count"], 4)
            for case_id, required in {
                "food_avocado_0027": {"pear_shaped_fruit_body", "skin_nodule_r0_c0"},
                "furniture_shelf_0181": {"left_triangular_brace", "left_diagonal_brace_beam", "front_plank_fascia"},
                "clothing_apron_0001": {"vertical_pink_stripe_0", "vertical_pink_stripe_6", "motif_waffle_cone", "ice_cream_scoop_pink"},
                "backpack_0045": {"rounded_top_shell", "outer_front_seam_left", "front_pocket_pull_tab"},
            }.items():
                recipe = json.loads((packet / "cases" / case_id / "recipe.json").read_text())
                components = {c["name"]: c for c in recipe["components"]}
                self.assertTrue(required <= set(components), (case_id, required - set(components)))
                self.assertEqual(recipe["identity"]["generation_method"], "pixel_inspected_seed")
                self.assertEqual(recipe["identity"]["recipe_version"], 2)
                self.assertFalse(recipe["quality"]["golden_approved"])
            apron = json.loads((packet / "cases/clothing_apron_0001/recipe.json").read_text())
            self.assertEqual(apron["render"]["camera_azimuth_deg"], 275)
            self.assertEqual(sum(c["name"].startswith("vertical_pink_stripe_") for c in apron["components"]), 7)
            shelf = json.loads((packet / "cases/furniture_shelf_0181/recipe.json").read_text())
            brace = next(c for c in shelf["components"] if c["name"] == "left_triangular_brace")
            self.assertEqual(brace["rotation_deg"], [90, 0, 90])
            with self.assertRaisesRegex(ValueError, "human truth missing"):
                run(packet, Path(temp) / "results",
                    endpoint="http://127.0.0.1:8080/v1/chat/completions",
                    model="fake-local-vlm")
            self.assertFalse((Path(temp) / "results").exists())

    def test_provisional_manual_estimates_cannot_be_reported_as_model_accuracy(self):
        truth = {"schema": "last-light.held-out-manual-feature-truth.v1",
                 "review_status": "PROVISIONAL_NEEDS_INDEPENDENT_REVIEW",
                 "defect_present": True, "component": "blade",
                 "source_bbox_px": [10, 20, 40, 60]}
        proposal = {"status": "defect", "component": "blade",
                    "source_bbox_px": [20, 30, 40, 60]}
        repair = {"actual_local_vision_request_completed": True, "golden_approved": False,
                  "shape_changed": True, "measured_feature_gain": .03}
        with self.assertRaisesRegex(ValueError, "provisional"):
            score_case(truth, proposal, repair)
        truth["review_status"] = "INDEPENDENTLY_VERIFIED"
        score = score_case(truth, proposal, repair)
        self.assertTrue(score["correct_component"])
        self.assertAlmostEqual(score["source_bbox_iou"], .5)
        self.assertTrue(score["shape_changed"])
        self.assertFalse(score["golden_approved"])
        with self.assertRaises(ValueError):
            bbox_iou([0, 0, 0, 4], [1, 2, 3, 4])


if __name__ == "__main__":
    unittest.main()
