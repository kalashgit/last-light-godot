from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("foundry_copilot_dispatch", ROOT / "tools/foundry_copilot/dispatch.py")
module = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = module
SPEC.loader.exec_module(module)


def issue():
    return {"number": 83, "state": "open", "assignees": [],
            "body": "A00-B001-F01-ll_furniture_refrigerator-r1; 0/360 Golden; No auto-merge"}


class DispatchTests(unittest.TestCase):
    def test_pilot_assignment_exact_and_default_model(self):
        p = module.prepare(issue(), 83)
        self.assertEqual(p["assignees"], ["copilot-swe-agent[bot]"])
        self.assertEqual(p["agent_assignment"]["custom_agent"], "foundry-modeler")
        self.assertEqual(p["agent_assignment"]["model"], "")

    def test_other_issue_denied(self):
        with self.assertRaises(ValueError):
            module.prepare(issue(), 84)

    def test_wrong_body_denied(self):
        i = issue()
        i["body"] = "Build a refrigerator"
        with self.assertRaises(ValueError):
            module.prepare(i, 83)

    def test_existing_assignee_denied(self):
        i = issue()
        i["assignees"] = [{"login": "copilot-swe-agent[bot]"}]
        with self.assertRaises(ValueError):
            module.prepare(i, 83)

    def test_past_assignment_denied_even_if_unassigned_now(self):
        with self.assertRaises(ValueError):
            module.reject_repeat_assignment([{
                "event": "assigned", "assignee": {"login": "copilot-swe-agent[bot]"}
            }])
        module.reject_repeat_assignment([{"event": "labeled", "label": {"name": "F01"}}])

    def test_closed_issue_denied(self):
        i = issue()
        i["state"] = "closed"
        with self.assertRaises(ValueError):
            module.prepare(i, 83)

    def test_pr_denied(self):
        i = issue()
        i["pull_request"] = {"url": "https://example.invalid"}
        with self.assertRaises(ValueError):
            module.prepare(i, 83)

    def test_requires_owner_and_main(self):
        env = {"GITHUB_EVENT_NAME": "workflow_dispatch", "GITHUB_REF": "refs/heads/main",
               "GITHUB_ACTOR": "kalashgit", "FOUNDRY_COPILOT_OWNER_BUDGET_CONFIRMED": "true",
               "FOUNDRY_COPILOT_USER_TOKEN": "redacted"}
        module.preflight(env)
        for key, value in (("GITHUB_ACTOR", "attacker"), ("GITHUB_REF", "refs/heads/pr"),
                           ("GITHUB_EVENT_NAME", "schedule"),
                           ("FOUNDRY_COPILOT_OWNER_BUDGET_CONFIRMED", "false"),
                           ("FOUNDRY_COPILOT_USER_TOKEN", "")):
            bad = dict(env)
            bad[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                module.preflight(bad)

    def test_agent_profile_restricts_tools_and_golden(self):
        profile = (ROOT / ".github/agents/foundry-modeler.agent.md").read_text()
        self.assertIn('tools: ["read", "search", "edit", "execute"]', profile)
        self.assertIn("disable-model-invocation: true", profile)
        self.assertIn("never Golden", profile)


if __name__ == "__main__":
    unittest.main()
