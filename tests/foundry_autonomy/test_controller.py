import copy
import hashlib
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("foundry_controller", ROOT / "tools/foundry_autonomy/controller.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
CATALOG = json.loads((ROOT / "data/foundry/notion_asset_snapshot_v1.json").read_text())
SHA = "a" * 40


def pr():
    return {"number": 85, "work_order": "A00-B001-F01-ll_furniture_refrigerator-r1",
            "asset_id": "ll_furniture_refrigerator", "draft": True, "state": "open",
            "merged": False, "repo": mod.REPOSITORY, "head_repo": mod.REPOSITORY,
            "base": "main", "head": "copilot/f01-fridge", "head_sha": SHA}


def run(result="success"):
    return {"id": 42656136172, "head_sha": SHA, "head_branch": "copilot/f01-fridge",
            "event": "pull_request", "status": "completed", "conclusion": result}


def review():
    return {"schema_version": 1, "candidate_sha": SHA, "reviewer": "F12-independent-QA",
            "golden_approved": False, "founder_visual_approved": False, "heading_count": 16,
            "contact_sheet_sha256": hashlib.sha256(b"original-sheet").hexdigest(),
            "categories": {c: "pass" for c in mod.REQUIRED_VISUAL_CATEGORIES},
            "defects": [], "gameplay_scale_checked": True,
            "f11_materials_checked": True, "f12_atlas_checked": True}


class ControllerTests(unittest.TestCase):
    def test_scheduled_audit_is_disabled_without_owner_opt_in(self):
        workflow = (ROOT / ".github/workflows/foundry-autonomous-review-audit.yml").read_text()
        guard = "vars.FOUNDRY_AUTONOMY_AUDIT_ENABLED == 'true'"
        job_condition = workflow.split("  review-audit:", 1)[1].split("    runs-on:", 1)[0]
        self.assertEqual(job_condition.count(guard), 2)
        self.assertIn("github.event_name == 'schedule'", job_condition)
        self.assertIn("github.actor == 'kalashgit'", job_condition)

    def test_technical_success_waits_for_visual(self):
        d, state = mod.assess(CATALOG, pr(), run(), None)
        self.assertEqual(d["next_action"], "AWAIT_INDEPENDENT_VISUAL_REVIEW")
        self.assertFalse(d["golden_approved"])
        self.assertEqual(len(state["events"]), 1)

    def test_independent_full_review_only_requests_founder(self):
        d, _ = mod.assess(CATALOG, pr(), run(), review())
        self.assertEqual(d["next_action"], "AWAIT_FOUNDER_GOLDEN_DECISION")
        self.assertTrue(d["founder_review_required"])
        self.assertFalse(d["automatic_merge"])
        self.assertFalse(d["automated_copilot_dispatch"])

    def test_defect_feedback_and_rework(self):
        visual = review()
        visual["categories"]["handles"] = "fail"
        visual["defects"] = ["Door handle floats away from gasket at heading 225 degrees"]
        d, _ = mod.assess(CATALOG, pr(), run(), visual)
        self.assertEqual(d["next_action"], "REQUEST_ARTISTIC_REWORK")
        self.assertIn("heading 225", d["defects"][0])

    def test_failing_run_never_promotes_even_with_visual_report(self):
        d, _ = mod.assess(CATALOG, pr(), run("failure"), review())
        self.assertEqual(d["next_action"], "REQUEST_TECHNICAL_REWORK")
        self.assertFalse(d["founder_review_required"])

    def test_idempotent_durable_cursor(self):
        one, state = mod.assess(CATALOG, pr(), run(), None)
        two, after = mod.assess(CATALOG, pr(), run(), None, state)
        self.assertEqual(state, after)
        self.assertFalse(one["already_recorded"])
        self.assertTrue(two["already_recorded"])

    def test_refuses_untrusted_or_stale_ci(self):
        for key, value in (("head_sha", "b" * 40), ("head_branch", "main"),
                           ("status", "in_progress"), ("event", "fork")):
            r = run()
            r[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                mod.assess(CATALOG, pr(), r, None)

    def test_refuses_merge_fork_and_unsigned_golden(self):
        for key, value in (("draft", False), ("merged", True),
                           ("head_repo", "untrusted/fork")):
            p = pr()
            p[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                mod.assess(CATALOG, p, run(), None)
        c = copy.deepcopy(CATALOG)
        next(r for r in c["production_masters"] if r.get("work_order") == pr()["work_order"])["founder_visual_approved"] = True
        with self.assertRaises(ValueError):
            mod.assess(c, pr(), run(), None)

    def test_review_needs_independence_and_all_headings(self):
        for key, value in (("reviewer", "Copilot"), ("heading_count", 8),
                           ("contact_sheet_sha256", "fake"), ("candidate_sha", "f" * 40)):
            v = review()
            v[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                mod.assess(CATALOG, pr(), run(), v)
        v = review()
        v["categories"].pop("sprite_readability")
        with self.assertRaises(ValueError):
            mod.assess(CATALOG, pr(), run(), v)

    def test_partial_material_or_gameplay_review_blocks_founder(self):
        v = review()
        v["f11_materials_checked"] = False
        self.assertEqual(mod.assess(CATALOG, pr(), run(), v)[0]["next_action"],
                         "AWAIT_F11_F12_ACCEPTANCE")
        v["gameplay_scale_checked"] = False
        self.assertEqual(mod.assess(CATALOG, pr(), run(), v)[0]["next_action"],
                         "AWAIT_INDEPENDENT_VISUAL_REVIEW")


if __name__ == "__main__":
    unittest.main()
