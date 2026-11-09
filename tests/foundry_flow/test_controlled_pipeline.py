"""Synthetic offline contract tests; not substitutes for real Blender/Godot CI."""

from __future__ import annotations

import hashlib
import json
import struct
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from PIL import Image, ImageDraw

from tools.foundry_flow.plan import plan, validate_admission
from tools.foundry_flow.pixel_style import process
from tools.foundry_flow.qa import verify
from tools.foundry_flow.publish_review import stage
from tools.foundry_mass.finalize import finalize
from tools.foundry_sheets.pack import pack
from tools.foundry_sheets.sprite_gen_bridge import bridge


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class ControlledPipelineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.ids = [f"ll_test_item_{i:02d}" for i in range(15)]
        self.snapshot = {"production_masters": [{
            "content_id": ident, "semantic_verification": "Canonical Verified",
            "queue": "F09", "work_order": f"A00-B001-F09-{ident}",
            "founder_visual_approved": False, "technical_qa_passed": False,
            "godot_tested": False, "iphone_verified": False,
        } for ident in self.ids], "snapshot_date": "2026-11-09"}
        self.geometry_manifest = b'{"source": "original_geometry"}\n'
        self.glb = struct.pack("<4sII", b"glTF", 2, 20) + b"\x00" * 8
        self.admission = {
            "schema": "A00_PRODUCTION_ADMISSION_R03_V1",
            "dispatch_total": 15, "source_index_count": 21025,
            "approve_only": "Start original-asset geometry/material/refinement with explicit art QA gates. Not Golden or game-ready.",
            "work_orders": [{
                "master_id": ident, "queue": "F09", "priority": "P0",
                "notion_semantic_verification": "Canonical Verified",
                "existing_geometry_id": ident, "work_order_id": f"A00-R03-F09-{ident}-v1",
                "dispatch_permission": "ORIGINAL_REFINEMENT_AND_TECHNICAL_SOURCE_QA_ONLY",
                "machine_worker_start_allowed": True,
                "source_pixel_comparison_verified": False,
                "geometry_image_comparison_verified": False,
                "source_rights": "THE_INDIE_STONE_COPYRIGHT__RESEARCH_ONLY__NO_DIRECT_REUSE",
                "rights_reviewed": False, "founder_visual_approved": False,
                "technical_qa_passed": False, "godot_tested": False,
                "iphone_verified": False, "canonical_new_id_created": False,
                "geometry_source_manifest_sha256": digest(self.geometry_manifest),
                "notion_url": f"https://notion.so/{ident}",
                "geometry_source_bounds_m": [1., 1., 1.],
                "quality_focus": "Verify original 3D silhouette",
            } for ident in self.ids],
        }
        self.archive = self.root / "sources.zip"
        with zipfile.ZipFile(self.archive, "w", compression=zipfile.ZIP_DEFLATED) as z:
            items = []
            names = self.ids + [f"ll_test_filler_{i:03d}" for i in range(345)]
            for ident in names:
                items.append({"asset_id": ident, "glb_sha256": digest(self.glb)})
                z.writestr(f"{ident}/model.glb", self.glb)
                z.writestr(f"{ident}/model.blend", b"BLENDER-testsource")
                z.writestr(f"{ident}/geometry_manifest.json", self.geometry_manifest)
            z.writestr("batch_report.json", json.dumps({
                "schema": 1, "source_plan_unique_count": 360,
                "generated_3d_source_count": 360,
                "status": "REAL_3D_SOURCES_NOT_2_5D_OR_GOLDEN_APPROVED",
                "source_plan_sha256": "f" * 64, "items": items,
            }))

    def _pilot(self):
        with patch("tools.foundry_flow.plan.validate_snapshot"):
            return plan(self.snapshot, self.admission, self.archive, self.root / "plan")

    def test_selection_is_only_an_admitted_canonical_original(self):
        doc = self._pilot()
        self.assertEqual(len(doc["selected"]), 1)
        self.assertEqual(doc["source_count"], 15)
        self.assertFalse(doc["golden_approved"])
        self.assertTrue(Path(doc["selected"][0]["glb_path"]).exists())
        self.assertFalse(doc["selected"][0]["source_image_copy_allowed"])
        with patch("tools.foundry_flow.plan.validate_snapshot"):
            with self.assertRaisesRegex(ValueError, "not in the verified R03"):
                plan(self.snapshot, self.admission, self.archive, self.root / "unapproved",
                     asset_id="ll_unlisted_model")

    def test_reference_rights_or_geometry_hash_drift_blocks(self):
        self.admission["work_orders"][0]["rights_reviewed"] = True
        with patch("tools.foundry_flow.plan.validate_snapshot"):
            with self.assertRaisesRegex(ValueError, "Unverified or wrongly authorized"):
                validate_admission(self.snapshot, self.admission)
        self.admission["work_orders"][0]["rights_reviewed"] = False
        self.admission["work_orders"][0]["geometry_source_manifest_sha256"] = "0" * 64
        with patch("tools.foundry_flow.plan.validate_snapshot"):
            with self.assertRaisesRegex(ValueError, "manifest drift"):
                plan(self.snapshot, self.admission, self.archive, self.root / "bad")

    def test_stale_cursor_blocks_and_does_not_skip_unapproved_items(self):
        doc = self._pilot()
        stale = {"schema_version": 1, "source_plan_sha256": "0" * 64,
                 "completed": [], "golden_approved": False}
        with patch("tools.foundry_flow.plan.validate_snapshot"):
            with self.assertRaisesRegex(ValueError, "unsafe production cursor"):
                plan(self.snapshot, self.admission, self.archive,
                     self.root / "stale", stale)
        self.assertFalse(doc["gameplay_integrated"])

    def test_pixel_style_atlas_bridge_and_independent_qa(self):
        doc = self._pilot()
        asset = doc["selected"][0]
        ident = asset["asset_id"]
        raw = self.root / "raw" / ident
        raw.mkdir(parents=True)
        for heading in range(16):
            im = Image.new("RGBA", (192, 192), (0, 0, 0, 0))
            draw = ImageDraw.Draw(im)
            draw.rounded_rectangle((32 + heading, 31, 150, 152), radius=13,
                                   fill=(80 + heading, 110, 103, 255))
            im.save(raw / f"{heading:02d}.png")
        (raw / "render_metadata.json").write_text(json.dumps({
            "asset_id": ident, "source_sha256": asset["glb_sha256"],
            "engine": "CYCLES_CPU", "frames": 16,
            "resolution": 192, "samples": 4, "dimensions_m": [1, 1, 1],
            "golden_approved": False,
        }))
        styled = self.root / "styled"
        result = process(doc, self.root / "raw", styled)
        self.assertEqual(result["style_candidates"][0]["logical_canvas_px"], 64)
        self.assertFalse(result["golden_approved"])
        candidates = self.root / "candidates"
        finalize(doc, styled, candidates, "123")
        sheets = self.root / "sheets"
        packed = pack(candidates, sheets, batch_size=1, page_size=1024, run_id="123")
        self.assertEqual(packed["frame_count"], 16)
        bridge_dir = self.root / "bridge"
        bridge(styled / ident / "interchange.json", bridge_dir)
        godot = {"result": "GODOT_ATLAS_IMPORT_PASS", "frame_count": 16,
                 "instantiated_sprites": 16, "golden_approved": False,
                 "iphone_verified": False}
        review = verify(doc, styled, candidates, sheets,
                        godot,
                        self.root / "review", bridge_dir)
        self.assertEqual(review["status"], "TECHNICAL_QA_PASSED_AWAITING_FOUNDER_VISUAL_REVIEW")
        self.assertFalse(review["founder_visual_approved"])
        self.assertFalse(review["iphone_verified"])
        self.assertTrue((self.root / "review" / "founder_contact_sheet.png").exists())
        (self.root / "godot_report.json").write_text(json.dumps(godot))
        (self.root / "blender_audit.json").write_text(json.dumps({
            "objects": [{"asset_id": ident, "source_glb_sha256": asset["glb_sha256"]}],
            "golden_approved": False,
        }))
        publish_dest = self.root / "publish"
        published = stage(self.root, publish_dest)
        self.assertEqual(published["status"], "TECHNICAL_REVIEW_IMMUTABLE_NOT_GOLDEN")
        self.assertEqual(stage(self.root, publish_dest), published)
        self.assertFalse(published["golden_approved"])

        # Runtime sheet pixels must be an exact reconstructable subset of the
        # original stylized frame. A changed source must fail independent QA.
        page = sheets / "sheet_0000.png"
        with Image.open(page) as original:
            altered = original.copy()
        altered.putpixel((0, 0), (23, 45, 67, 255))
        altered.save(page)
        with self.assertRaisesRegex(ValueError, "checksum drift"):
            verify(doc, styled, candidates, sheets,
                   godot,
                   self.root / "invalid")
        with self.assertRaisesRegex(ValueError, "modified after quality assurance"):
            stage(self.root, self.root / "publish-other")


if __name__ == "__main__":
    unittest.main()
