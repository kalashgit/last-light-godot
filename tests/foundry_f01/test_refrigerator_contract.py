"""Focused F01 refrigerator contract tests; Blender is an explicit separate gate."""
from __future__ import annotations

import json
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = ROOT / "tools/foundry_f01/refrigerator_contract.json"
RECIPE_PATH = ROOT / "tools/foundry_f01/generate_refrigerator.py"
SNAPSHOT_PATH = ROOT / "data/foundry/notion_asset_snapshot_v1.json"


class RefrigeratorContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
        cls.snapshot = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
        cls.recipe = RECIPE_PATH.read_text(encoding="utf-8")

    def test_exact_canonical_work_order_and_asset_identity(self):
        self.assertEqual(
            self.contract["work_order"],
            "A00-B001-F01-ll_furniture_refrigerator-r1",
        )
        self.assertEqual(self.contract["asset_id"], "ll_furniture_refrigerator")
        record = next(
            row for row in self.snapshot["production_masters"]
            if row["content_id"] == self.contract["asset_id"]
        )
        self.assertEqual(record["work_order"], self.contract["work_order"])
        self.assertEqual(record["queue"], "F01")
        self.assertEqual(record["semantic_verification"], "Canonical Verified")
        for field in (
            "rights_reviewed", "founder_visual_approved", "technical_qa_passed",
            "godot_tested", "iphone_verified",
        ):
            self.assertIs(record[field], False, field)

    def test_candidate_state_never_claims_any_acceptance_gate(self):
        approval = self.contract["approval"]
        self.assertTrue(approval["technical_artistic_candidate_only"])
        for gate in (
            "golden_approved", "canonical_promoted", "gameplay_integrated",
            "rights_reviewed", "f11_materials_approved", "f12_world_scale_approved",
            "godot_tested", "iphone_verified", "founder_visual_approved",
        ):
            self.assertIs(approval[gate], False, gate)

    def test_stable_proposed_world_id_and_ground_center_collision(self):
        self.assertEqual(
            self.contract["world_placement_id"],
            "ll_world_home_001_kitchen_refrigerator_01",
        )
        placement = self.contract["placement"]
        self.assertEqual(placement["anchor"], "bottom_center")
        self.assertEqual(placement["collision_min_candidate_units"], [-0.36, -0.34, 0.0])
        self.assertEqual(placement["collision_max_candidate_units"], [0.36, 0.34, 1.78])
        self.assertIn("not_a_canonical", self.contract["world_placement_id_status"])

    def test_candidate_proportions_and_transparent_diagnostic_contract(self):
        recipe = self.contract["recipe"]
        self.assertEqual(recipe["front_axis"], "-Y")
        self.assertEqual(recipe["origin"], "center of cabinet footprint at floor level; Blender Z-up")
        self.assertEqual(
            recipe["target_dimensions_candidate_units"],
            {"width_x": 0.72, "depth_y": 0.68, "height_z": 1.78},
        )
        render = self.contract["diagnostic_render"]
        self.assertEqual(render["headings"], 16)
        self.assertEqual(render["heading_step_degrees"], 22.5)
        self.assertEqual(render["resolution_px"], [256, 256])
        self.assertTrue(render["transparent_background"])
        self.assertEqual(render["contact_sheet_layout"], [4, 4])

    def test_recipe_generates_meshes_glb_and_actual_cycles_headings(self):
        self.assertIn("import bpy", self.recipe)
        self.assertIn('scene.render.engine = "CYCLES"', self.recipe)
        self.assertIn("bpy.ops.render.render(write_still=True)", self.recipe)
        self.assertIn("range(HEADINGS)", self.recipe)
        self.assertIn('export_format="GLB"', self.recipe)
        self.assertIn("save_as_mainfile", self.recipe)
        self.assertIn("contact_sheet_16_headings.png", self.recipe)
        self.assertIn("source_archive_candidate.zip", self.recipe)
        self.assertIn("Refusing to overwrite candidate output directory", self.recipe)

    def test_recipe_runs_objective_mesh_anchor_alpha_and_framing_qa(self):
        for evidence in (
            "mesh_bounds_and_fingerprint",
            "validate_geometry",
            "anchor_root_location",
            "alpha_nonzero_pixel_count",
            "alpha_transparent_pixel_count",
            "alpha_bbox_xyxy",
            "framing_bbox_fraction_min",
            "struct.unpack_from",
            "archive.testzip()",
        ):
            self.assertIn(evidence, self.recipe)
        self.assertRegex(self.recipe, re.compile(r"heading \* 22\.5"))

    def test_seeded_geometry_hash_supports_repeatability_comparison(self):
        self.assertEqual(self.contract["recipe"]["seed"], 1041)
        self.assertIn('random.Random(contract["recipe"]["seed"])', self.recipe)
        self.assertIn('"mesh_fingerprint_sha256": fingerprint', self.recipe)
        self.assertIn('"sha256": sha256(path)', self.recipe)

    def test_candidate_is_not_placed_in_gameplay_or_asset_import_folder(self):
        godot_script = (ROOT / "scripts/house.gd").read_text(encoding="utf-8")
        main_scene = (ROOT / "main.tscn").read_text(encoding="utf-8")
        self.assertNotIn("ll_furniture_refrigerator", godot_script)
        self.assertNotIn("ll_furniture_refrigerator", main_scene)
        self.assertFalse((ROOT / "assets/ll_furniture_refrigerator").exists())

    def test_recipe_has_no_external_reference_asset_inputs(self):
        rights = self.contract["rights"]
        self.assertEqual(rights["third_party_asset_inputs"], [])
        self.assertIn("No external meshes", self.contract["recipe"]["source_inputs"])
        self.assertIn("founder/legal rights review remains unresolved",
                      rights["license_status"].lower())
        self.assertIn("Refusing to write outside candidate-only build tree", self.recipe)


if __name__ == "__main__":
    unittest.main()
