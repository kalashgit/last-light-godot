import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("m02_factory", ROOT / "tools/autonomous_factory/v1.py")
factory = importlib.util.module_from_spec(spec)
spec.loader.exec_module(factory)


class ContractTests(unittest.TestCase):
    def test_missing_candidate_blocks_all_stages(self):
        with tempfile.TemporaryDirectory() as root:
            report = factory.inspect(root)
            self.assertEqual(report["status"], "BLOCKED")
            self.assertFalse(report["founder_approved"])
            self.assertFalse(report["engine_import_validated"])
            self.assertIn("BLEND_SOURCE", [d["code"] for d in report["defects"]])

    def test_repair_limit_invalid_rejected_before_execution(self):
        with tempfile.TemporaryDirectory() as root:
            for attempts in (0, 4, 999):
                with self.assertRaises(ValueError):
                    factory.execute("blender", root, attempts, 2)

    def test_failed_blender_does_not_retry_nonruntime_defect(self):
        with tempfile.TemporaryDirectory() as root:
            code = factory.execute("missing-blender-binary", root, 3, 2)
            self.assertEqual(code, 1)
            summary = json.loads((Path(root) / "summary.json").read_text())
            self.assertEqual(summary["iterations_used"], 1)
            self.assertEqual(summary["total_ai_calls"], 0)
            self.assertFalse(summary["canonical_promoted"])
            feedback = json.loads((Path(root) / "ai_feedback.json").read_text())
            self.assertTrue(feedback["defects"])

    def test_feedback_metadata_never_authorizes_promotion(self):
        with tempfile.TemporaryDirectory() as root:
            factory.execute("missing-blender-binary", root, 1, 2)
            candidate = json.loads((Path(root) / "attempt_1/candidate.json").read_text())
            self.assertEqual(candidate["status"], "BLOCKED")
            self.assertFalse(candidate["canonical_promoted"])
            self.assertFalse(candidate["gameplay_integrated"])


if __name__ == "__main__":
    unittest.main()
