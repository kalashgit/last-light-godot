"""Adversarial admission and originality regression tests for batch 23–45."""
import copy
import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageDraw

from tools.foundry_original_23.contract import (
    DEFAULT_MANIFEST, EXPECTED_IDS, MASTER, build_render_plan, check_manifest,
)
from tools.foundry_original_23.gameplay import build_gameplay
from tools.foundry_original_23.audit_artifacts import find_windows
from tools.foundry_original_23.postprocess import (
    create_previews, icon_from_frame, inspect_alpha,
)


class OriginalBatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = json.loads(DEFAULT_MANIFEST.read_text())

    def test_exact_23_unique_canonical_ids(self):
        self.assertEqual(tuple(a["asset_id"] for a in self.doc["assets"]), EXPECTED_IDS)
        self.assertEqual(len(set(EXPECTED_IDS)), 23)

    def test_pinned_notion_records_match_and_are_all_unreviewed(self):
        report = check_manifest(self.doc, MASTER)
        self.assertEqual(report["status"], "PASS_PREVIEW_ONLY", report["errors"])
        self.assertTrue(report["identities_reconciled"])
        self.assertEqual(report["production_admitted_count"], 0)
        self.assertEqual(report["founder_golden_approved_count"], 0)

    def test_40_item_pack_cannot_accept_only_23_held(self):
        report = check_manifest(self.doc, MASTER)
        self.assertEqual(report["forty_item_pages_eligible"], 0)
        self.assertLess(report["asset_count"], self.doc["inventory_sheet_min_unique"])
        self.assertTrue(all(a["admission"]["production_render_admitted"] is False for a in self.doc["assets"]))

    def test_originality_constraints_no_reference_import(self):
        self.assertFalse(self.doc["source_art_pixels_imported"])
        for a in self.doc["assets"]:
            self.assertEqual(a["source_reference_ids"], [])
            self.assertTrue(a["geometry_recipe"]["editable_blend_required"])
            self.assertTrue(a["visual_qa"]["originality_provenance"].startswith("REQUIRES"))

    def test_forged_semantic_and_golden_flags_rejected(self):
        fake = copy.deepcopy(self.doc)
        fake["assets"][0]["admission"]["founder_golden_approved"] = True
        fake["assets"][1]["admission"]["semantic_status"] = "VERIFIED"
        self.assertEqual(check_manifest(fake, MASTER)["status"], "FAIL_CLOSED")

    def test_swapped_id_duplicate_and_modified_brief_rejected(self):
        fake = copy.deepcopy(self.doc)
        fake["assets"][0]["asset_id"] = fake["assets"][1]["asset_id"]
        self.assertEqual(check_manifest(fake, MASTER)["status"], "FAIL_CLOSED")
        fake = copy.deepcopy(self.doc)
        fake["assets"][0]["brief"] = "copied marketplace artwork"
        self.assertIn("Pinned Notion provenance differs", str(check_manifest(fake, MASTER)["errors"]))

    def test_gameplay_states_and_sockets_for_all_23(self):
        result = build_gameplay(self.doc)
        self.assertEqual(len(result["assets"]), 23)
        for a in result["assets"]:
            self.assertGreater(len(a["state_machine"]), 1)
            self.assertFalse(a["founder_golden_approved"])
            self.assertTrue(all(not x["godot_binding_implemented"] for x in a["state_machine"]))
            self.assertTrue(all(x["pivot_and_animation_status"].startswith("REQUIRES") for x in a["attachment_sockets"]))

    def test_empty_source_selection_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            with self.assertRaisesRegex(ValueError, "No real independently generated GLB"):
                build_render_plan(Path(t), Path(t)/"render_plan.json")

    def test_aggregate_fail_closed_without_six_independent_windows(self):
        with tempfile.TemporaryDirectory() as t:
            with self.assertRaisesRegex(ValueError, "exactly six"):
                find_windows(Path(t))

    def test_transparent_64px_icon_and_alpha_border(self):
        image = Image.new("RGBA", (192, 192), (0, 0, 0, 0))
        ImageDraw.Draw(image).ellipse((64, 24, 124, 164), fill=(120, 55, 20, 255))
        icon = icon_from_frame(image)
        self.assertEqual(icon.size, (64, 64))
        audit = inspect_alpha(icon)
        self.assertGreater(audit["transparent_pixels"], 0)
        self.assertGreater(audit["opaque_or_antialiased_pixels"], 0)

    def test_empty_or_cut_off_art_rejected(self):
        with self.assertRaisesRegex(ValueError, "no mesh pixels"):
            icon_from_frame(Image.new("RGBA", (192, 192), (0, 0, 0, 0)))
        with self.assertRaisesRegex(ValueError, "safety padding"):
            inspect_alpha(Image.new("RGBA", (64, 64), (10, 20, 30, 255)))

    def test_offline_postprocess_requires_16_real_frames(self):
        with tempfile.TemporaryDirectory() as t:
            folder = Path(t)/"render"/EXPECTED_IDS[0]
            folder.mkdir(parents=True)
            (folder/"render_metadata.json").write_text(json.dumps({
                "asset_id": EXPECTED_IDS[0], "frames": 16, "golden_approved": False,
                "source_sha256": "0"*64,
            }))
            for i in range(15):
                frame = Image.new("RGBA", (192, 192), (0, 0, 0, 0))
                ImageDraw.Draw(frame).rectangle((50, 30, 120, 130), fill=(40, 80, 120, 255))
                frame.save(folder/f"{i:02d}.png")
            with self.assertRaisesRegex(ValueError, "Missing 16-direction"):
                create_previews(self.doc, Path(t)/"render", Path(t)/"output")

    def test_cross_asset_identical_original_art_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t)/"render"
            for ident in EXPECTED_IDS[:2]:
                folder = root/ident
                folder.mkdir(parents=True)
                (folder/"render_metadata.json").write_text(json.dumps({
                    "asset_id": ident, "frames": 16, "golden_approved": False,
                    "source_sha256": "0"*64,
                }))
                for i in range(16):
                    frame = Image.new("RGBA", (192, 192), (0, 0, 0, 0))
                    ImageDraw.Draw(frame).rectangle((50+i%4, 30, 120, 130), fill=(40, 80, 120, 255))
                    frame.save(folder/f"{i:02d}.png")
            with self.assertRaisesRegex(ValueError, "Cross-ID duplicate"):
                create_previews(self.doc, root, Path(t)/"output")


if __name__ == "__main__":
    unittest.main()
