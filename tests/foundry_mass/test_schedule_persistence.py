"""Regression: scheduled render can commit its validated candidate cursor."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
WF = ROOT / ".github/workflows/foundry-360-mass-production.yml"

class ScheduledPersistenceContract(unittest.TestCase):
    def test_dependent_contract_job_skips_scheduled_event(self):
        text = WF.read_text()
        self.assertIn("if: github.event_name != 'schedule'", text)

    def test_persist_job_explicitly_handles_skipped_prerequisites(self):
        text = WF.read_text().split("  persist-candidates:",1)[1]
        condition = text.split("    runs-on:",1)[0]
        self.assertIn("always()", condition)
        self.assertIn("needs.blender-batch.result == 'success'", condition)
        self.assertIn("github.event_name == 'schedule'", condition)
        self.assertIn("needs: [preflight, contracts, blender-batch]", condition)

    def test_only_isolated_candidate_branch_gets_written(self):
        s = WF.read_text().split("  persist-candidates:",1)[1]
        self.assertIn("foundry/technical-sprites-v1", s)
        self.assertNotIn("HEAD:refs/heads/main", s)
        self.assertIn("python tools/foundry_mass/publish.py", s)

if __name__ == '__main__':
    unittest.main()
