"""Fail-closed contract checks for Foundry finite unattended self-dispatch."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2] / ".github" / "workflows"
CASES = {
    "foundry-360-mass-production.yml": ("persist-candidates:", "foundry/technical-sprites-v1", 360),
    "foundry-create-new-3d-models.yml": ("archive-and-advance:", "foundry/generated-sources-v1", 512),
}

class FiniteProductionTests(unittest.TestCase):
    def test_only_restricted_default_branch_and_owner_bot(self):
        for filename, (job, branch, total) in CASES.items():
            with self.subTest(filename=filename):
                s = (ROOT / filename).read_text()
                self.assertIn("github.ref == 'refs/heads/main'", s)
                self.assertIn("github.actor == 'kalashgit'", s)
                self.assertIn("github.actor == 'github-actions[bot]'", s)
                self.assertTrue("cancel-in-progress: false" in s or "cancel-in-progress: ${{ github.event_name == 'pull_request' }}" in s)
                self.assertIn("github.event_name == 'schedule'", s)
                self.assertIn("github.event_name == 'pull_request'", s)
    def test_no_unbounded_dispatch_and_no_schedule_chain(self):
        for filename, (job, branch, total) in CASES.items():
            with self.subTest(filename=filename):
                s = (ROOT / filename).read_text()
                self.assertIn("continuation_batches:", s)
                self.assertIn("default: '0'", s)
                self.assertTrue("options: ['0', '1', '2']" in s or "options: ['0','1','2']" in s)
                self.assertIn("if [[ \"$GITHUB_EVENT_NAME\" == 'push' ]]; then remaining=2; else remaining=\"$CHAIN_INPUT\"; fi", s)
                self.assertIn("[[ \"$remaining\" =~ ^[012]$ ]]", s)
                self.assertIn("next=$((remaining-1))", s)
                self.assertIn("if (( remaining == 0 )); then", s)
                self.assertIn("if: github.event_name == 'push' || github.event_name == 'workflow_dispatch'", s)
                self.assertIn("gh workflow run "+filename, s)
                self.assertIn("len(d['completed'])<="+str(total), s)
                self.assertIn("d['golden_approved'] is False", s)
                self.assertEqual(s.count("gh workflow run "), 1)
    def test_only_publisher_has_privileged_self_dispatch(self):
        for filename,(job, branch, total) in CASES.items():
            with self.subTest(filename=filename):
                s=(ROOT / filename).read_text()
                before, after=s.split("  "+job,1)
                self.assertNotIn("gh workflow run ", before)
                self.assertIn("actions: write", after)
                self.assertIn("contents: write", after)
                self.assertIn("GH_TOKEN: ${{ github.token }}", after)
                self.assertIn(branch, after)
                self.assertIn("github.event_name == 'schedule'", after)
                self.assertNotIn("golden_approved=true", s)
                self.assertNotIn("promote-golden", s)

    def test_original_creation_chain_preserves_bounded_owner_batch_size(self):
        s = (ROOT / "foundry-create-new-3d-models.yml").read_text()
        self.assertIn("BATCH_INPUT: ${{ inputs.batch_size || '2' }}", s)
        self.assertIn('[[ "$BATCH_INPUT" =~ ^[1-4]$ ]]', s)
        self.assertIn('-f batch_size="$BATCH_INPUT"', s)
        self.assertNotIn('-f batch_size=2 -f continuation_batches=', s)
        self.assertIn("if: github.event_name == 'push' || github.event_name == 'workflow_dispatch'", s)

if __name__ == "__main__":
    unittest.main()
