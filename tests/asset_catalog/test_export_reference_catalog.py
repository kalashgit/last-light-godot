"""Safety and coverage regressions for the A00 spreadsheet export."""

import csv
import json
import tempfile
import unittest
from pathlib import Path

from tools.asset_catalog.export_reference_catalog import export, load_references


class CatalogExportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "source"
        self.source.mkdir()
        self.snapshot = self.root / "snapshot.json"
        self.admission = self.root / "admission.json"
        self.output = self.root / "out"

    def write_inputs(self, duplicate=False):
        def record(number):
            return {
                "source_page_id": 1 if duplicate else number,
                "source_title": f"File:Item{number}.png",
                "source_url": f"https://example.org/source/{number}",
                "source_categories": ["Category:Items"],
                "primary_class": "CANONICAL_MASTER_CANDIDATE" if number == 1 else "UI_ICON_ONLY",
                "reason": "=DANGEROUS()" if number == 2 else "Provisional metadata",
                "batch_id": "A00-20261108-B001",
                "rights": "source_research_only",
            }
        path = self.source / "a00_20261108_b001_2.jsonl"
        path.write_text("\n".join(json.dumps(record(n)) for n in (1, 2)) + "\n")
        self.snapshot.write_text(json.dumps({"production_masters": [
            {"content_id": "ll_item_one", "family": "prop", "queue": "F09",
             "work_order": "A00-B001-F09-ll_item_one-r1", "priority": "P1",
             "stage": "Backlog", "semantic_verification": "Canonical Verified",
             "founder_visual_approved": False},
            {"content_id": "ll_unreviewed", "family": "prop", "queue": None,
             "work_order": None, "priority": "P3", "stage": "Backlog",
             "semantic_verification": "Unreviewed", "founder_visual_approved": False},
        ]}))
        self.admission.write_text(json.dumps({"work_orders": [
            {"master_id": "ll_item_one", "queue": "F09", "priority": "P1",
             "work_order_id": "R03-F09-item-one", "dispatch_permission": "ORIGINAL_REFINEMENT_ONLY"}
        ]}))

    def test_full_export_preserves_evidence_and_admission_boundary(self):
        self.write_inputs()
        result = export(self.source, self.snapshot, self.output, self.admission, 2)
        self.assertEqual(result["count"], 2)
        self.assertEqual(result["canonical_verified"], 1)
        self.assertEqual(result["refinement_admitted"], 1)
        self.assertEqual(result["golden_approved_by_export"], 0)
        with (self.output / "last_light_21025_references.csv").open(newline="") as f:
            refs = list(csv.DictReader(f))
        self.assertEqual([int(x["source_page_id"]) for x in refs], [1, 2])
        self.assertEqual(refs[1]["reason"], "'=DANGEROUS()")
        with (self.output / "last_light_canonical_master_queue.csv").open(newline="") as f:
            masters = {x["content_id"]: x for x in csv.DictReader(f)}
        self.assertEqual(masters["ll_item_one"]["production_status"], "ORIGINAL_REFINEMENT_ONLY")
        self.assertEqual(masters["ll_unreviewed"]["production_status"], "VERIFICATION_HOLD")

    def test_duplicate_reference_is_rejected(self):
        self.write_inputs(duplicate=True)
        with self.assertRaisesRegex(ValueError, "duplicate source ID"):
            load_references(self.source, 2)

    def test_missing_references_are_rejected(self):
        self.write_inputs()
        with self.assertRaisesRegex(ValueError, "Reference coverage 2 != 3"):
            load_references(self.source, 3)

    def test_admitted_master_must_be_verified(self):
        self.write_inputs()
        data = json.loads(self.admission.read_text())
        data["work_orders"][0]["master_id"] = "ll_unreviewed"
        self.admission.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, "Inadmissible refinement"):
            export(self.source, self.snapshot, self.output, self.admission, 2)


if __name__ == "__main__":
    unittest.main()
