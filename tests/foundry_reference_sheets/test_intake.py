import json
import tempfile
import unittest
from pathlib import Path

from tools.foundry_reference_sheets.build import SOURCE_DIR, build
from tools.foundry_reference_sheets.labels import ROWS, labels
from tools.foundry_reference_sheets.plan import plan


class FounderReferenceIntakeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records, cls.report = build()

    def test_exact_counts_and_explicit_gap(self):
        ids = {r["sheet_index"] for r in self.records}
        self.assertEqual(len(self.records), 390)
        self.assertEqual(ids, set(range(1, 401)) - set(range(191, 201)))
        self.assertEqual(self.report["unpictured_slots"], list(range(191, 201)))

    def test_labels_and_sheet_geometry(self):
        self.assertEqual(len(ROWS), 40)
        self.assertEqual(len(labels()), 390)
        self.assertEqual(self.records[150]["working_label"], "kerosene camping lantern")
        self.assertEqual(self.records[189]["sheet_index"], 190)
        self.assertEqual(self.records[190]["sheet_index"], 201)
        self.assertEqual(self.records[190]["working_label"], "purple university cap")
        r = self.records[189]
        self.assertEqual([r["cell_row"], r["cell_column"]], [4, 7])
        self.assertEqual(r["cell_box_xyxy"], [1344, 768, 1536, 961])

    def test_no_reference_becomes_3d_or_golden_automatically(self):
        self.assertTrue(all(r["queue_status"].startswith("NEEDS_") for r in self.records))
        for item in self.records:
            self.assertFalse(any(item["admission"].values()))
            self.assertFalse(item["technical_preview_produced"])
            self.assertFalse(item["suggestion_approved"])
            self.assertFalse(item["authoring_contract"]["reference_pixels_as_game_texture_allowed"])

    def test_curated_crosswalk_is_suggestion_only(self):
        candidate = self.records[134]
        self.assertEqual(candidate["reference_id"], "LL-FGS-0135")
        self.assertEqual(candidate["notion_canonical_suggestion"], "ll_crafting_antler_pair")
        self.assertFalse(candidate["admission"]["semantic_verified"])

    def test_source_digest_is_enforced(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest = json.loads((SOURCE_DIR / "sheets_manifest_v1.json").read_text())
            manifest["sheets"][0]["sha256"] = "0" * 64
            (root / "sheets_manifest_v1.json").write_text(json.dumps(manifest))
            for image in (SOURCE_DIR / "sheets").iterdir():
                (root / "sheets").mkdir(exist_ok=True)
                (root / "sheets" / image.name).symlink_to(image)
            with self.assertRaisesRegex(ValueError, "changed founder source sheet"):
                build(root)

    def test_selected_authoring_jobs_are_bounded_and_unapproved(self):
        job = plan(self.records, 185, 20)
        self.assertEqual(len(job["jobs"]), 20)
        self.assertEqual(job["selected_reference_ids"][0], "LL-FGS-0185")
        self.assertEqual(job["selected_reference_ids"][6], "LL-FGS-0201")
        self.assertFalse(job["production_model_admitted"])
        self.assertFalse(job["source_pixels_to_mesh_or_texture"])
        with self.assertRaises(ValueError):
            plan(self.records, 1, 400)


if __name__ == "__main__":
    unittest.main()
