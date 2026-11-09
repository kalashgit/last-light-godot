import copy
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from foundry_reference_intake.build import build, validate_bible, validate_references


class IntakeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.source = self.root / "source"
        self.source.mkdir()
        self.rows = [
            {"source_page_id": 10, "source_title": "File:Bucket.png",
             "source_url": "https://pzwiki.net/wiki/File:Bucket.png",
             "source_categories": ["Category:Item icons"], "primary_class": "CANONICAL_MASTER_CANDIDATE",
             "rights": "source_research_only", "semantic_status": "PROVISIONAL_METADATA_TRIAGE",
             "batch_id": "A00-20261108-B001", "suggested_queue": "F09"},
            {"source_page_id": 11, "source_title": "File:Other.png",
             "source_url": "https://pzwiki.net/wiki/File:Other.png",
             "source_categories": [], "primary_class": "COMPOSITION_REFERENCE",
             "rights": "source_research_only", "semantic_status": "PROVISIONAL_METADATA_TRIAGE",
             "batch_id": "A00-20261108-B001", "suggested_queue": None},
        ]
        self.filename = "a00_20261108_b001_2.jsonl"
        self.inventory = {"files": [], "expected_records": 2, "expected_unique_ids": 2,
                          "expected_classes": {"CANONICAL_MASTER_CANDIDATE": 1, "COMPOSITION_REFERENCE": 1},
                          "expected_batches": {"A00-20261108-B001": 2}}
        self.bible = json.loads((ROOT / "data/foundry_reference_catalog/sprite_bible_contract_v2.json").read_text())
        self.notion = {"source": "NOTION_CANONICAL_ASSET_REGISTRY_READ_ONLY_EXPORT",
                       "golden_approved_by_export": False, "masters_total": 1,
                       "masters_semantic_verified": 1, "production_masters": [self.master()]}
        self.admission = {"dispatch_total": 1, "model_visual_verified": False,
                          "source_pixels_imported": False,
                          "admitted_original_refinement_ids": ["ll_household_bucket"]}
        self.refresh()

    def master(self):
        d = {"content_id": "ll_household_bucket", "semantic_verification": "Canonical Verified",
             "notion_url": "https://app.notion.com/p/example", "source_reference_ids": [10],
             "family": "prop", "production_queue": "F09", "production_priority": "P0",
             "source_work_order": "TEST-F09", "founder_visual_approved": False,
             "rights_reviewed": False}
        for k in ("proposed_brief", "geometry_and_dimensions", "materials_and_textures",
                  "animation_and_states", "render_and_pivot", "gameplay_and_physics"):
            d[k] = "Independent original physical " + k
        return d

    def refresh(self):
        path = self.source / self.filename
        path.write_text("".join(json.dumps(r) + "\n" for r in self.rows))
        self.inventory["files"] = [{"name": self.filename, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}]

    def write(self, name, data):
        p = self.root / name
        p.write_text(json.dumps(data))
        return p

    def run_build(self):
        return build(self.source, self.write("manifest.json", self.inventory),
                     self.write("notion.json", self.notion),
                     self.write("bible.json", self.bible),
                     self.write("admission.json", self.admission), self.root / "build")

    def test_valid_source_packs_semantic_recipes_without_source_image_pixels(self):
        report = self.run_build()
        self.assertEqual(report["source_records"], 2)
        self.assertEqual(report["reconciled_physical_recipes"], 1)
        self.assertEqual(report["refinement_admitted_valid"], 1)
        self.assertEqual(report["founder_golden_approved"], 0)
        record = json.loads((self.root / "build/original_recipe_work_orders.jsonl").read_text())
        payload = record["generation_input"]
        self.assertFalse(any("pzwiki.net" in json.dumps(v) for v in payload.values()))
        self.assertTrue(payload["original_creation_only"])
        self.assertFalse(payload["source_image_pixels_allowed"])
        self.assertFalse(record["gates"]["founder_golden_approved"])

    def test_changed_source_without_hash_change_rejected(self):
        self.rows[0]["source_title"] = "altered"
        (self.source / self.filename).write_text("".join(json.dumps(r) + "\n" for r in self.rows))
        with self.assertRaisesRegex(ValueError, "Tampered"):
            self.run_build()

    def test_rights_escalation_rejected_even_with_recomputed_hash(self):
        self.rows[0]["rights"] = "approved_for_reuse"
        self.refresh()
        with self.assertRaisesRegex(ValueError, "may not be promoted"):
            self.run_build()

    def test_duplicate_source_id_rejected(self):
        self.rows[1]["source_page_id"] = 10
        self.refresh()
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            self.run_build()

    def test_source_id_provenance_hold(self):
        self.notion["production_masters"][0]["source_reference_ids"] = [10, 2026]
        report = self.run_build()
        self.assertEqual(report["reconciled_physical_recipes"], 0)
        self.assertEqual(report["provenance_hold_count"], 1)
        self.assertEqual(report["refinement_admitted_valid"], 0)

    def test_forged_founder_flag_quarantined(self):
        self.notion["production_masters"][0]["founder_visual_approved"] = True
        report = self.run_build()
        self.assertEqual(report["reconciled_physical_recipes"], 0)
        self.assertEqual(report["founder_golden_approved"], 0)

    def test_missing_recipe_quarantined(self):
        self.notion["production_masters"][0]["materials_and_textures"] = ""
        self.assertEqual(self.run_build()["reconciled_physical_recipes"], 0)

    def test_weakened_bible_rejected(self):
        mutated = copy.deepcopy(self.bible)
        mutated["reference_policy"]["original_asset_only"] = False
        with self.assertRaisesRegex(ValueError, "weakened"):
            validate_bible(mutated)

    def test_unexpected_source_shard_rejected(self):
        (self.source / "untracked.jsonl").write_text("{}\n")
        with self.assertRaisesRegex(ValueError, "shard set mismatch"):
            validate_references(self.source, self.inventory)


if __name__ == "__main__":
    unittest.main()
