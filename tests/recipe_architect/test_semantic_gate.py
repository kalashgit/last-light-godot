"""Controlled geometry-visible checks; synthetic tests are not VLM evidence."""
from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from tools.recipe_architect.contract import validate
from tools.recipe_architect.seed_recipes import SEEDS
from tools.recipe_architect.semantic_gate import correct_camera, select_heading
from tools.recipe_architect.semantic_repair import repair


def fixture(*, visible_headings: set[int], best: int = 12):
    pixels = [{"heading": h, "pixel_score": .93 if h == best else .71 - h * .002}
              for h in range(16)]
    evidence = {"schema": "last-light.component-visibility-evidence.v1",
                "required_visible_components": ["latch", "case_body"],
                "orientations": [{"heading": h, "required_parts": {
                    "latch": {"ray_hit_samples": 3 if h in visible_headings else 0,
                              "on_screen_samples": 12},
                    "case_body": {"ray_hit_samples": 7, "on_screen_samples": 12}}}
                                 for h in range(16)]}
    return pixels, evidence


class SemanticGateTests(unittest.TestCase):
    def test_occluded_pixel_winner_is_vetoed(self):
        pixels, evidence = fixture(visible_headings={0, 1, 2, 3, 4}, best=12)
        result = select_heading(pixels, evidence)
        self.assertTrue(result["pixel_winner_vetoed"])
        self.assertEqual(result["unrestricted_pixel_winner"]["heading"], 12)
        self.assertEqual(result["approved_candidate"]["heading"], 0)
        self.assertFalse(result["human_approval"])
        self.assertFalse(result["autonomous_semantic_vision_run"])

    def test_all_occluded_results_in_hold_not_fake_approval(self):
        pixels, evidence = fixture(visible_headings=set())
        result = select_heading(pixels, evidence)
        self.assertEqual(result["status"], "HOLD_ALL_ANGLES_OCCLUDED")
        self.assertIsNone(result["approved_candidate"])

    def test_missing_component_evidence_rejected(self):
        pixels, evidence = fixture(visible_headings={0})
        del evidence["orientations"][0]["required_parts"]["latch"]
        with self.assertRaisesRegex(ValueError, "missing source-visible"):
            select_heading(pixels, evidence)
        pixels, evidence = fixture(visible_headings={0})
        with self.assertRaisesRegex(ValueError, "16 real"):
            select_heading(pixels[:-1], evidence)

    def test_camera_only_bounded_correction_preserves_not_golden(self):
        starting = SEEDS["vehicle_battery"]()
        saved = copy.deepcopy(starting)
        repaired = correct_camera(starting, 4)
        self.assertEqual(repaired["render"]["camera_azimuth_deg"],
                         (saved["render"]["camera_azimuth_deg"] - 90) % 360)
        self.assertEqual(repaired["identity"]["generation_method"], "reviewed_revision")
        self.assertEqual(repaired["identity"]["recipe_version"],
                         saved["identity"]["recipe_version"] + 1)
        self.assertEqual(starting, saved)
        self.assertFalse(validate(repaired, full_schema=True)["quality"]["golden_approved"])
        with self.assertRaises(ValueError):
            correct_camera(starting, 16)

    def test_actual_build_cap_checked_before_any_mutation(self):
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            baseline = {"schema": "last-light.manual-sheet-3d-review.v1",
                        "results": [{"position": 44, "original_view_score": .59}]}
            gate = {"schema": "last-light.source-visible-gate-run.v1", "golden_approved": False,
                    "models": [{"position": 44, "candidate_id": "candidate_test",
                                "correction_recipe_path": "absent.json", "source_sha256": "0" * 64,
                                "selection": {"unrestricted_pixel_winner": {"heading": 12},
                                              "approved_candidate": {"heading": 4,
                                                                     "semantic_geometry_gate_pass": True}}}]}
            (work / "baseline.json").write_text(json.dumps(baseline))
            (work / "gate.json").write_text(json.dumps(gate))
            with self.assertRaisesRegex(ValueError, "bounded real Blender"):
                repair(work / "gate.json", work / "baseline.json", work,
                       work / "output", max_real_builds=0)
            self.assertFalse((work / "output").exists())

    def test_no_candidate_means_no_inference_or_blender_work(self):
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            baseline = {"schema": "last-light.manual-sheet-3d-review.v1",
                        "results": [{"position": 5, "original_view_score": .91}]}
            gate = {"schema": "last-light.source-visible-gate-run.v1", "golden_approved": False,
                    "models": [{"position": 5, "candidate_id": "candidate_test",
                                "correction_recipe_path": None, "source_sha256": "0" * 64,
                                "selection": {"unrestricted_pixel_winner": {"heading": 0},
                                              "approved_candidate": None}}]}
            (work / "baseline.json").write_text(json.dumps(baseline))
            (work / "gate.json").write_text(json.dumps(gate))
            report = repair(work / "gate.json", work / "baseline.json", work,
                            work / "output", run=lambda *args, **kwargs: self.fail("unexpected Blender"))
            self.assertEqual(report["real_builds_executed"], 0)
            self.assertEqual(report["changes"][0]["status"], "HOLD_OCCLUSION")
            self.assertFalse(report["golden_approved"])


if __name__ == "__main__":
    unittest.main()
