import copy
import importlib.util
import pathlib
import sys
import unittest

P = pathlib.Path(__file__).resolve().parents[2] / "tools" / "autonomous_factory" / "foundry_ai_worker.py"
spec = importlib.util.spec_from_file_location("foundry_ai_worker", P)
worker = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = worker
spec.loader.exec_module(worker)

RUN = {
    "id": 123, "name": "M02 Pinned F02 F03 F10 F11 F12 Engine Calibration",
    "status": "completed", "conclusion": "failure", "event": "pull_request",
    "head_sha": "a" * 40, "head_branch": "codex/m02-autonomous-asset-factory-v1",
    "repository": {"full_name": "kalashgit/last-light-godot"},
    "head_repository": {"full_name": "kalashgit/last-light-godot"},
}
JOBS = [{"id": 789, "name": "F10 `crash`\nmalicious", "conclusion": "failure"}]

class TestFoundryCorrection(unittest.TestCase):
    def test_valid_failure(self):
        self.assertTrue(worker.eligible(RUN).allowed)
        title, body = worker.failure_issue(RUN, JOBS)
        self.assertIn("foundry-correction-run:123", body)
        self.assertIn("job/789", body)
        self.assertIn("Do not merge", body)
        self.assertNotIn("`crash`", body)
        self.assertNotIn("malicious\n", body)
        self.assertLess(len(title), 160)

    def test_only_allowlisted_workflows(self):
        run = copy.deepcopy(RUN)
        run["name"] = "Other workflow"
        self.assertFalse(worker.eligible(run).allowed)

    def test_no_foreign_repositories(self):
        for field in ("repository", "head_repository"):
            run = copy.deepcopy(RUN)
            run[field]["full_name"] = "someone/untrusted"
            self.assertFalse(worker.eligible(run).allowed)

    def test_missing_head_repository_fails_closed(self):
        run = copy.deepcopy(RUN)
        run.pop("head_repository", None)
        self.assertFalse(worker.eligible(run).allowed)

    def test_no_untrusted_branches(self):
        run = copy.deepcopy(RUN)
        run["head_branch"] = "main"
        self.assertFalse(worker.eligible(run).allowed)

    def test_no_untrusted_events(self):
        run = copy.deepcopy(RUN)
        run["event"] = "fork"
        self.assertFalse(worker.eligible(run).allowed)

    def test_no_successful_jobs(self):
        run = copy.deepcopy(RUN)
        run["conclusion"] = "success"
        self.assertFalse(worker.eligible(run).allowed)

    def test_no_in_progress_jobs(self):
        run = copy.deepcopy(RUN)
        run["status"] = "in_progress"
        self.assertFalse(worker.eligible(run).allowed)

    def test_no_improper_sha(self):
        run = copy.deepcopy(RUN)
        run["head_sha"] = "not-a-sha"
        self.assertFalse(worker.eligible(run).allowed)

    def test_no_failure_job_available(self):
        _, body = worker.failure_issue(RUN, [])
        self.assertIn("No failed job metadata", body)

    def test_api_path_restriction(self):
        gh = worker.GitHub("test")
        with self.assertRaises(ValueError):
            gh.request("https://evil.example/")
        with self.assertRaises(ValueError):
            gh.request("//evil.example/")

    def test_does_not_leak_token_in_repr(self):
        gh = worker.GitHub("secret")
        self.assertNotIn("secret", repr(gh))

    def test_issue_deduplication(self):
        class MockGitHub(worker.GitHub):
            def request(self, path, method="GET", body=None, token=None):
                return [{"number": 20, "body": "<!-- foundry-correction-run:123 -->"}]
        self.assertEqual(MockGitHub("test").issue_for_run(123), 20)

    def test_issue_deduplication_fails_closed(self):
        class MockGitHub(worker.GitHub):
            def request(self, path, method="GET", body=None, token=None):
                return [{"number": i, "body": "unrelated"} for i in range(100)]
        with self.assertRaises(RuntimeError):
            MockGitHub("test").issue_for_run(123)

    def test_daily_issue_cap(self):
        now = worker.dt.datetime.now(worker.dt.timezone.utc).isoformat()
        class MockGitHub(worker.GitHub):
            def request(self, path, method="GET", body=None, token=None):
                return [
                    {"number": i, "created_at": now,
                     "body": "<!-- foundry-correction-run:%d -->" % i}
                    for i in range(6)
                ]
        self.assertEqual(MockGitHub("test").correction_issues_last_day(), 6)

    def test_issue_cap_ignores_unmanaged_issues(self):
        now = worker.dt.datetime.now(worker.dt.timezone.utc).isoformat()
        class MockGitHub(worker.GitHub):
            def request(self, path, method="GET", body=None, token=None):
                return [{"created_at": now, "body": "unrelated manual task"}]
        self.assertEqual(MockGitHub("test").correction_issues_last_day(), 0)

    def test_daily_cap_fails_closed_when_unbounded(self):
        now = worker.dt.datetime.now(worker.dt.timezone.utc).isoformat()
        class MockGitHub(worker.GitHub):
            def request(self, path, method="GET", body=None, token=None):
                return [{"created_at": now, "body": "not found"} for _ in range(100)]
        with self.assertRaises(RuntimeError):
            MockGitHub("test").correction_issues_last_day()

if __name__ == "__main__":
    unittest.main()
