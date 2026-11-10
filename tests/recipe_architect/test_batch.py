"""Nonbillable bounded owner-dispatch work-order contract tests."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.recipe_architect import batch


class BatchContractTests(unittest.TestCase):
    def test_three_pinned_recipes_plan_without_source_fabrication(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "run"
            report = batch.execute("all", 3, out, mode="plan", run_id="test_123")
            self.assertEqual(report["candidate_count"], 3)
            self.assertEqual([r["preset"] for r in report["candidates"]], ["battery", "canteen", "skillet"])
            self.assertEqual(report["status"], "PLAN_ONLY")
            self.assertFalse(report["image_source_pixels_inspected_this_run"])
            self.assertFalse(report["reference_vs_render_comparison_this_run"])
            self.assertFalse(report["autonomous_vision_inference_run"])
            self.assertFalse(report["founder_golden_approved"])
            self.assertTrue(all(r["state"] == "PLANNED" and r["golden_approved"] is False
                                for r in report["candidates"]))
            self.assertEqual(json.loads((out / "batch_report.json").read_text()), report)
            with tempfile.TemporaryDirectory() as e:
                same = batch.execute("all", 3, Path(e) / "another", mode="plan")
                self.assertEqual(report["job_fingerprint"], same["job_fingerprint"])

    def test_rejects_unbounded_or_unknown_inputs(self):
        for name, count in (("all", 0), ("all", 4), ("battery", 2),
                            ("../../private", 1), ("skillet", -1)):
            with self.subTest(name=name, count=count):
                with self.assertRaises(ValueError): batch.selected(name, count)

    def test_rejects_preset_recipe_change_without_review(self):
        with patch.dict(batch.APPROVED_RECIPE_SHA256, {"battery": "0" * 64}):
            with self.assertRaisesRegex(ValueError, "differs from reviewed recipe"):
                batch.recipes("battery", 1)

    def test_existing_output_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "same"
            batch.execute("battery", 1, out, mode="plan")
            before = (out / "batch_report.json").read_bytes()
            with self.assertRaises(FileExistsError): batch.execute("battery", 1, out, mode="plan")
            self.assertEqual(before, (out / "batch_report.json").read_bytes())

    def test_rejects_untrusted_run_id(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):
                batch.execute("battery", 1, Path(d) / "run", run_id="../../escape")

    def test_build_failure_produces_auditable_non_golden_report(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "failed"
            with patch.object(batch, "run_blender", side_effect=RuntimeError("simulated Blender failure")):
                report = batch.execute("battery", 1, out, mode="build")
            self.assertEqual(report["status"], "TECHNICAL_FAIL")
            self.assertEqual(report["technical_pass_count"], 0)
            self.assertEqual(report["candidates"][0]["state"], "TECHNICAL_FAIL")
            self.assertIn("simulated Blender failure", report["errors"][0]["reason"])
            self.assertFalse(report["founder_golden_approved"])
            self.assertFalse(report["canonical_admission"])


if __name__ == "__main__":
    unittest.main()
