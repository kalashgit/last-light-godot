from __future__ import annotations

import copy
import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("foundry_notion_catalog", ROOT / "tools/foundry_notion/catalog.py")
catalog = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = catalog
SPEC.loader.exec_module(catalog)


def sample():
    return {
        "schema_version": 1, "snapshot_date": "2026-11-09",
        "status": "NOTION_READ_ONLY_SNAPSHOT_NOT_LIVE_SYNC",
        "coverage": {"canonical_production_masters": 2, "world_specifications": 1,
                     "source_reference_records": 1, "old_editable_3d_sources": 360,
                     "old_3d_golden_approved": 0},
        "production_masters": [
            {"content_id": "ll_bookcase", "family": "prop", "stage": "Approved",
             "semantic_verification": "Canonical Verified", "priority": "P0", "queue": "F01",
             "work_order": "A00-F01-bookcase-r1", "rights_reviewed": False,
             "founder_visual_approved": False, "technical_qa_passed": False,
             "godot_tested": False, "iphone_verified": False},
            {"content_id": "ll_unknown", "family": "prop", "stage": "Backlog",
             "semantic_verification": "Unreviewed", "priority": "P3", "queue": None,
             "work_order": None, "rights_reviewed": False,
             "founder_visual_approved": False, "technical_qa_passed": False,
             "godot_tested": False, "iphone_verified": False}],
        "world_specifications": [{"world_id": "ll.archetype.house", "completion_tier": "Unresolved"}],
        "source_references": [{"reference_file_id": "9710", "production_status": "Reference",
                               "rights": "Research only"}],
    }


class CatalogTests(unittest.TestCase):
    def test_plans_only_canonical_routed_assets(self):
        result = catalog.plan(sample())
        self.assertEqual([o["content_id"] for o in result["orders"]], ["ll_bookcase"])
        self.assertEqual(result["unverified_master_count"], 1)
        self.assertEqual(result["legacy_source_models_pending_golden"], 360)
        self.assertFalse(result["golden_approved"])
        self.assertFalse(result["orders"][0]["automatic_golden_promotion_allowed"])

    def test_notion_numbered_work_order_beats_alphabetical_name(self):
        doc = sample()
        doc["production_masters"][0]["content_id"] = "ll_zz_refrigerator"
        doc["production_masters"][0]["work_order"] = "A00-B001-F01-refrigerator-r1"
        doc["production_masters"][1].update({
            "content_id": "ll_aa_firewood", "semantic_verification": "Canonical Verified",
            "priority": "P0", "queue": "F09", "work_order": "A00-B008-F09-firewood-r1",
        })
        result = catalog.plan(doc, batch_size=2)
        self.assertEqual([x["content_id"] for x in result["orders"]],
                         ["ll_zz_refrigerator", "ll_aa_firewood"])

    def test_approved_notion_stage_is_not_golden(self):
        result = catalog.plan(sample())
        self.assertTrue(result["orders"][0]["rights_review_required"])
        self.assertFalse(result["orders"][0]["founder_visual_approved"])

    def test_rejects_unsigned_approval(self):
        doc = sample()
        doc["production_masters"][0]["founder_visual_approved"] = True
        with self.assertRaises(ValueError):
            catalog.plan(doc)

    def test_rejects_invalid_source_promotion(self):
        doc = sample()
        doc["source_references"][0]["production_status"] = "Approved"
        with self.assertRaises(ValueError):
            catalog.plan(doc)

    def test_rejects_fake_world_completion(self):
        doc = sample()
        doc["world_specifications"][0]["completion_tier"] = "Gameplay complete"
        with self.assertRaises(ValueError):
            catalog.plan(doc)

    def test_rejects_missing_row(self):
        doc = sample()
        doc["production_masters"].pop()
        with self.assertRaises(ValueError):
            catalog.plan(doc)

    def test_rejects_duplicate_ids(self):
        doc = sample()
        doc["production_masters"][1]["content_id"] = "ll_bookcase"
        with self.assertRaises(ValueError):
            catalog.plan(doc)

    def test_rejects_unknown_worker(self):
        doc = sample()
        doc["production_masters"][0]["queue"] = "F99"
        with self.assertRaises(ValueError):
            catalog.plan(doc)

    def test_completion_cursor_does_not_repeat(self):
        result = catalog.plan(sample(), completed=["ll_bookcase"])
        self.assertEqual(result["orders"], [])
        self.assertEqual(result["queue_status"], "NO_ADMITTED_WORK")

    def test_deferred_candidate_is_not_falsely_completed(self):
        result = catalog.plan(sample(), deferred=["ll_bookcase"])
        self.assertEqual(result["orders"], [])
        self.assertEqual(result["deferred_not_completed"], ["ll_bookcase"])
        self.assertFalse(result["golden_approved"])
        self.assertEqual(catalog.plan(sample())["orders"][0]["content_id"], "ll_bookcase")

    def test_deferred_candidate_preserves_next_notion_priority(self):
        doc = sample()
        doc["production_masters"][1].update({
            "content_id": "ll_mattress", "semantic_verification": "Canonical Verified",
            "priority": "P0", "queue": "F01", "work_order": "A00-B002-F01-mattress-r1",
        })
        doc["production_masters"][0]["work_order"] = "A00-B001-F01-bookcase-r1"
        result = catalog.plan(doc, deferred=["ll_bookcase"])
        self.assertEqual([o["content_id"] for o in result["orders"]], ["ll_mattress"])

    def test_rejects_unknown_duplicate_or_completed_deferred(self):
        for deferred, done in [(["ll_fake"], None), (["ll_bookcase", "ll_bookcase"], None),
                               (["ll_bookcase"], ["ll_bookcase"])]:
            with self.subTest(deferred=deferred, completed=done), self.assertRaises(ValueError):
                catalog.plan(sample(), completed=done, deferred=deferred)

    def test_rejects_forged_completion(self):
        with self.assertRaises(ValueError):
            catalog.plan(sample(), completed=["ll_fake"])

    def test_rejects_unbounded_request(self):
        with self.assertRaises(ValueError):
            catalog.plan(sample(), batch_size=999)

    def test_actual_snapshot_contract_if_available(self):
        path = ROOT / "data/foundry/notion_asset_snapshot_v1.json"
        if not path.exists():
            self.skipTest("full sanitized Notion snapshot only present in repository")
        doc = json.loads(path.read_text())
        result = catalog.plan(doc)
        self.assertEqual(result["master_count"], 60)
        self.assertEqual(result["world_specifications_not_gameplay_complete"], 118)
        self.assertEqual(result["reference_records_not_assets"], 50)
        self.assertEqual(len(result["orders"]), 4)
        self.assertTrue(all(not x["founder_visual_approved"] for x in result["orders"]))


if __name__ == "__main__":
    unittest.main()
