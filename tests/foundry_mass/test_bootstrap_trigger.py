"""Regression: only a reviewed main-branch workflow push can bootstrap persistence.

PR test runs must never write candidate branches. No Golden approval allowed.
"""
from __future__ import annotations
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS = (
    "foundry-360-mass-production.yml",
    "foundry-create-new-3d-models.yml",
)

class BootstrapGuardTests(unittest.TestCase):
    def test_both_bootstraps_are_strictly_main_path_scoped(self):
        for file in WORKFLOWS:
            with self.subTest(workflow=file):
                s = (ROOT / ".github/workflows" / file).read_text()
                self.assertIn("  push:\n    branches: [main]\n    paths:", s)
                self.assertIn(f"'.github/workflows/{file}'", s)
                self.assertIn("github.event_name == 'push' && github.ref == 'refs/heads/main' && github.actor == 'kalashgit'", s)
                self.assertIn("github.event_name == 'schedule'", s)
                self.assertIn("github.event_name == 'workflow_dispatch'", s)
    def test_pr_runs_cannot_auto_publish(self):
        for file in WORKFLOWS:
            with self.subTest(workflow=file):
                s = (ROOT / ".github/workflows" / file).read_text()
                self.assertIn("github.event_name == 'pull_request'", s)
                self.assertIn("github.actor == 'kalashgit'", s)
                self.assertIn("always()", s)
                self.assertNotIn("github.event_name == 'pull_request' && github.ref == 'refs/heads/main'", s)
    def test_no_golden_promotion_in_workflow(self):
        for file in WORKFLOWS:
            s = (ROOT / ".github/workflows" / file).read_text()
            self.assertNotIn("golden_approved=true", s)
            self.assertNotIn("promote-golden", s)
    def test_bootstrap_does_not_run_on_candidate_branch_push(self):
        for file in WORKFLOWS:
            s = (ROOT / ".github/workflows" / file).read_text()
            self.assertIn("branches: [main]", s)
            self.assertNotIn("branches: ['**']", s)

if __name__ == "__main__":
    unittest.main()
