"""Read-only reconciliation coverage tests against the checked-in research mirror."""
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
AUDIT = ROOT / "tools/factory_v4_catalog_audit.py"


class CatalogAuditTests(unittest.TestCase):
    def test_repository_mirror_reconciles_without_approvals(self):
        with tempfile.TemporaryDirectory() as work:
            dest = pathlib.Path(work) / "audit"
            result = subprocess.run([sys.executable, str(AUDIT), "--source", str(ROOT / "data/research"),
                                     "--output", str(dest)], capture_output=True, text=True, check=True)
            summary = json.loads(result.stdout)
            self.assertEqual(summary["item_reference_rows"], 4347)
            self.assertEqual(summary["classification_rows"], 4347)
            self.assertEqual(summary["provisional_unclassified_in_mirror"], 1379)
            self.assertEqual(summary["media_rows_including_possible_category_memberships"], 1640)
            self.assertEqual(summary["human_verified_classification_rows"], 0)
            self.assertEqual(summary["human_review_queue_rows"], 4347)
            self.assertFalse(summary["approval_state_changed"])
            self.assertFalse(summary["phone_status_reverified_here"])
            queue = (dest / "human_review_queue.jsonl").read_text().splitlines()
            self.assertEqual(len(queue), 4347)
            self.assertEqual(json.loads(queue[0])["source_id"], "pzwiki.icon.000001")
            self.assertEqual(json.loads(queue[-1])["source_id"], "pzwiki.icon.004347")
            self.assertTrue(all(json.loads(row)["rights"] == "research_only" for row in queue))
            self.assertEqual((dest / "identity_conflicts.jsonl").read_bytes(), b"")


if __name__ == "__main__":
    unittest.main()
