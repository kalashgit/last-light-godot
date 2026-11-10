"""Geometry-repair test gates; synthetic coverage is not a model benchmark."""
from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageDraw

from tools.recipe_architect.component_geometry_optimize import (
    measured_contacts, normalize_rect, optimize, rect_error, validate_target, variants,
)
from tools.recipe_architect.seed_recipes import SEEDS


class ComponentGeometryMutationTests(unittest.TestCase):
    def test_box_geometry_resizes_but_source_and_other_parts_unchanged(self):
        recipe = SEEDS["vehicle_battery"]()
        original = copy.deepcopy(recipe)
        proposals = variants(recipe, "main_battery_casing")
        self.assertEqual(len(proposals), 6)
        self.assertTrue(all(p["identity"]["recipe_version"] == 2 for p, _ in proposals))
        self.assertTrue(all(not p["quality"]["golden_approved"] for p, _ in proposals))
        changed = proposals[0][0]["components"][0]["geometry"]["size"]
        self.assertGreater(changed[0], original["components"][0]["geometry"]["size"][0])
        self.assertEqual(recipe, original)

    def test_cylinder_and_lathe_are_finite_bounded_shape_changes(self):
        canteen = SEEDS["canvas_canteen"]()
        cylinder = variants(canteen, "ribbed_screw_cap")
        lathe = variants(canteen, "hollow_fabric_cover")
        self.assertEqual(len(cylinder), 4)
        self.assertEqual(len(lathe), 4)
        self.assertLess(cylinder[1][0]["components"][2]["geometry"]["radius"], .15)
        self.assertNotEqual(lathe[0][0]["components"][0]["geometry"]["profile"],
                            canteen["components"][0]["geometry"]["profile"])

    def test_polygon_and_tube_mutations_do_not_touch_non_target(self):
        skillet = SEEDS["cast_iron_skillet"]()
        polygon = variants(skillet, "tapered_handle_shank")
        self.assertEqual([m["parameter"] for _, m in polygon],
                         ["points_x", "points_x", "points_y", "points_y", "depth", "depth"])
        before = next(c for c in skillet["components"] if c["name"] == "tapered_handle_shank")
        after = next(c for c in polygon[0][0]["components"] if c["name"] == "tapered_handle_shank")
        self.assertNotEqual(before["geometry"]["points"], after["geometry"]["points"])
        canteen = SEEDS["canvas_canteen"]()
        tube = variants(canteen, "front_center_canvas_stitch")
        self.assertEqual(len(tube), 8)
        self.assertEqual(tube[-1][1]["parameter"], "points_z")

    def test_missing_or_unobserved_geometry_and_unbounded_changes_refused(self):
        recipe = SEEDS["cast_iron_skillet"]()
        with self.assertRaisesRegex(ValueError, "source-observed"):
            variants(recipe, "handle_hanging_slot")
        with self.assertRaisesRegex(ValueError, "source-observed"):
            variants(recipe, "invented_furniture_part")
        with self.assertRaisesRegex(ValueError, "bounded"):
            variants(recipe, "tapered_handle_shank", step=.99)

    def test_projected_bbox_error_rewards_measured_component_improvement(self):
        reference = [.4, .2, .6, .6]
        poor = rect_error(reference, [.25, .1, .55, .5])
        better = rect_error(reference, [.4, .22, .6, .58])
        self.assertLess(better["feature_error"], poor["feature_error"])
        self.assertGreater(better["bbox_iou"], poor["bbox_iou"])

    def test_normalization_crops_using_true_alpha(self):
        im = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
        ImageDraw.Draw(im).rectangle((20, 30, 79, 89), fill="brown")
        bbox = normalize_rect([40, 50, 60, 70], im)
        self.assertTrue(all(.3 < value < .75 for value in bbox))
        with self.assertRaisesRegex(ValueError, "inside source"):
            normalize_rect([-10, 0, 20, 30], im)

    def test_source_hash_and_observation_are_mandatory(self):
        recipe = SEEDS["vehicle_battery"]()
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "reference.png"
            Image.new("RGBA", (100, 100), "red").save(source)
            from tools.recipe_architect.contract import sha256
            target = {"schema": "last-light.manual-component-geometry-target.v1",
                      "source_sha256": sha256(source),
                      "candidate_id": recipe["identity"]["candidate_id"],
                      "component": "main_battery_casing", "confidence": .8,
                      "required_visible_components": ["main_battery_casing", "stepped_lid_shell"],
                      "source_bbox_px": [10, 10, 30, 40],
                      "provenance": "manual_source_image_estimate", "approval": "NOT_GOLDEN"}
            validate_target(target, recipe, source)
            target["source_sha256"] = "0" * 64
            with self.assertRaisesRegex(ValueError, "pinned"):
                validate_target(target, recipe, source)

    def test_physical_contact_gap_is_measured_from_blender_bounds(self):
        evidence = {"components": {
            "blade": {"world_bbox_m": [[0, 0, 0], [1, 1, 1]]},
            "socket": {"world_bbox_m": [[.9, .8, .7], [1.3, 1.1, 1.1]]},
            "loose_handle": {"world_bbox_m": [[1.3, 0, 0], [1.7, 1, 1]]}}}
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "geometry.json"
            p.write_text(json.dumps(evidence))
            gaps = measured_contacts(p, {"component": "blade",
                                         "contact_neighbors": ["socket", "loose_handle"]})
            self.assertEqual(gaps["socket"], 0)
            self.assertEqual(gaps["loose_handle"], .3)

    def test_preview_cap_checked_before_running_blender_or_creating_outputs(self):
        with self.assertRaisesRegex(ValueError, "eight real preview"):
            optimize(Path("missing_recipe"), Path("missing_source"), Path("missing_target"),
                     Path("missing_output"), max_previews=9,
                     render_func=lambda *args, **kw: self.fail("unexpected renderer"))


if __name__ == "__main__":
    unittest.main()
