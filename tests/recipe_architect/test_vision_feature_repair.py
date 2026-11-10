"""Mock-server contract tests. These do NOT prove a real VLM recognized defects."""
from __future__ import annotations

import copy
import json
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from unittest.mock import patch

from PIL import Image, ImageDraw

from tools.recipe_architect.component_geometry_optimize import recipe_digest, validate_target
from tools.recipe_architect.contract import sha256, validate
from tools.recipe_architect.seed_recipes import SEEDS
from tools.recipe_architect.vision_feature_repair import (
    inspect_and_repair, request_detection, validate_detection,
)


DEFECT = {"status": "defect", "component": "main_battery_casing",
          "source_bbox_px": [20, 20, 65, 70], "defect_type": "wrong_proportion",
          "suggested_parameter": "size_x", "suggested_direction": "decrease",
          "confidence": .92, "explanation": "Source case is visibly narrower than the Blender case."}
NONE = {"status": "no_confident_defect", "component": None,
        "source_bbox_px": None, "defect_type": None,
        "suggested_parameter": None, "suggested_direction": None,
        "confidence": .35, "explanation": "No confidently localized geometry mismatch."}


class VisionDetectionTests(unittest.TestCase):
    def fixture(self, root: Path):
        source = root / "source.png"
        image = Image.new("RGBA", (100, 100), (255, 255, 255, 255))
        ImageDraw.Draw(image).rectangle((20, 20, 65, 70), fill=(90, 60, 30, 255))
        image.save(source)
        render = root / "baseline.png"
        Image.new("RGBA", (128, 128), (0, 0, 0, 0)).save(render)
        recipe = SEEDS["vehicle_battery"]()
        recipe["identity"]["source_sha256"] = sha256(source)
        recipe["visual_analysis"]["image_dimensions"] = [100, 100]
        validate(recipe, source, full_schema=True)
        projections = {"schema": "last-light.recipe-projections.v1", "heading": 0,
                       "resolution": 128, "components": {
                           "main_battery_casing": {
                               "bbox_px": [25, 35, 115, 100],
                               "bbox_method": "actual_blender_mesh_vertices_pre_bevel",
                               "world_bbox_m": [[0, 0, 0], [1, 1, 1]]},
                           "stepped_lid_shell": {
                               "bbox_px": [30, 32, 112, 42],
                               "bbox_method": "actual_blender_mesh_vertices_pre_bevel",
                               "world_bbox_m": [[0, 0, .9], [1, 1, 1.1]]},
                       }}
        receipt = {"model": "mock-model", "source_sha256": sha256(source),
                   "recipe_sha256": recipe_digest(recipe),
                   "baseline_render_sha256": sha256(render),
                   "network_scope": "loopback_only", "pixels_supplied": True,
                   "actual_local_vision_request_completed": True}
        return source, render, recipe, projections, receipt

    def test_mock_loopback_contract_sends_source_and_real_render_without_manual_roi(self):
        with tempfile.TemporaryDirectory() as d:
            source, render, recipe, projections, _ = self.fixture(Path(d))
            seen = []

            class Handler(BaseHTTPRequestHandler):
                def do_POST(self):
                    length = int(self.headers["Content-Length"])
                    payload = json.loads(self.rfile.read(length))
                    seen.append(payload)
                    body = json.dumps({"choices": [{"message": {"content": json.dumps(DEFECT)}}],
                                       "usage": {"total_tokens": 123}}).encode()
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)

                def log_message(self, *args):
                    pass

            server = HTTPServer(("127.0.0.1", 0), Handler)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                proposal, receipt = request_detection(
                    source, render, recipe=recipe, projections=projections,
                    endpoint=f"http://127.0.0.1:{server.server_port}/v1/chat/completions",
                    model="local-mock-vlm")
            finally:
                server.shutdown()
                thread.join(timeout=2)
                server.server_close()
            self.assertEqual(proposal, DEFECT)
            self.assertEqual(receipt["source_sha256"], sha256(source))
            self.assertTrue(receipt["actual_local_vision_request_completed"])
            self.assertEqual(receipt["paid_model_calls"], 0)
            self.assertEqual(len(seen), 1)
            content = seen[0]["messages"][1]["content"]
            self.assertEqual([item["type"] for item in content], ["text", "image_url", "image_url"])
            self.assertNotIn("source_bbox_px", content[0]["text"])
            self.assertIn("main_battery_casing", content[0]["text"])
            self.assertIn("data:image/png;base64,", content[1]["image_url"]["url"])
            self.assertIn("data:image/png;base64,", content[2]["image_url"]["url"])

    def test_source_derived_target_only_for_observed_component_and_real_region(self):
        with tempfile.TemporaryDirectory() as d:
            source, _, recipe, projections, receipt = self.fixture(Path(d))
            target = validate_detection(source, recipe, projections, DEFECT, receipt)
            self.assertEqual(target["schema"], "last-light.vlm-component-geometry-target.v1")
            self.assertEqual(target["contact_neighbors"], ["stepped_lid_shell"])
            self.assertEqual(target["required_visible_components"],
                             ["main_battery_casing", "stepped_lid_shell"])
            self.assertEqual(target["suggested_parameter"], "size_x")
            self.assertFalse(target["approval"] == "GOLDEN")
            validate_target(target, recipe, source)

            for key, invalid in (("component", "invented_gear"),
                                 ("component", "brand_label"),
                                 ("suggested_parameter", "exec_python"),
                                 ("source_bbox_px", [0, 0, 10, 10]),
                                 ("source_bbox_px", [-2, 3, 20, 60])):
                with self.subTest(key=key, invalid=invalid):
                    bad = {**DEFECT, key: invalid}
                    with self.assertRaises(ValueError):
                        validate_detection(source, recipe, projections, bad, receipt)

    def test_refuses_forged_receipts_outside_hosts_and_low_confidence(self):
        with tempfile.TemporaryDirectory() as d:
            source, render, recipe, projections, receipt = self.fixture(Path(d))
            self.assertIsNone(validate_detection(source, recipe, projections, NONE, receipt))
            self.assertIsNone(validate_detection(source, recipe, projections,
                                                 {**DEFECT, "confidence": .7}, receipt))
            with self.assertRaisesRegex(ValueError, "uncertain detection"):
                validate_detection(source, recipe, projections,
                                   {**NONE, "component": "main_battery_casing"}, receipt)
            with self.assertRaisesRegex(ValueError, "unbound"):
                validate_detection(source, recipe, projections, DEFECT,
                                   {**receipt, "recipe_sha256": "0" * 64})
            for uri in ("https://127.0.0.1:1234/v1/chat/completions",
                        "http://evil.example:1234/v1/chat/completions",
                        "http://127.0.0.1:1234/redirect"):
                with self.subTest(uri=uri), self.assertRaises(ValueError):
                    request_detection(source, render, recipe=recipe, projections=projections,
                                      endpoint=uri, model="fake")

    def test_repair_runner_only_invokes_optimized_geometry_after_independent_detection(self):
        with tempfile.TemporaryDirectory() as d:
            folder = Path(d)
            source, render, recipe, projections, receipt = self.fixture(folder)
            recipe_file = folder / "recipe.json"
            recipe_file.write_text(json.dumps(recipe))
            called = []

            def fake_blender(blender, recipe_file, out, *, headings, export):
                self.assertEqual(headings, 1)
                self.assertFalse(export)
                out.mkdir(parents=True)
                Image.open(render).save(out / "heading_00.png")
                (out / "component_projections.json").write_text(json.dumps(projections))

            def fake_optimizer(recipe_path, source_path, target_path, out, *, blender):
                self.assertFalse(out.exists())
                target = json.loads(target_path.read_text())
                validate_target(target, recipe, source)
                self.assertEqual(target["component"], "main_battery_casing")
                called.append(target)
                return {"status": "HOLD_NO_BOUNDED_GEOMETRY_GAIN", "measured_feature_gain": 0,
                        "shape_changed": False, "golden_approved": False}

            with patch("tools.recipe_architect.vision_feature_repair.request_detection",
                       return_value=(copy.deepcopy(DEFECT), receipt)):
                report = inspect_and_repair(recipe_file, source, folder / "run",
                                            endpoint="http://127.0.0.1:9898/v1/chat/completions",
                                            model="mock-model", render_func=fake_blender,
                                            repair_func=fake_optimizer)
            self.assertEqual(report["status"], "HOLD_NO_BOUNDED_GEOMETRY_GAIN")
            self.assertTrue(report["geometry_optimization_run"])
            self.assertFalse(report["golden_approved"])
            self.assertEqual(len(called), 1)
            self.assertTrue((folder / "run/local_vision_inference_receipt.json").is_file())
            with patch("tools.recipe_architect.vision_feature_repair.request_detection",
                       return_value=(NONE, receipt)):
                held = inspect_and_repair(recipe_file, source, folder / "hold",
                                          endpoint="http://127.0.0.1:9898/v1/chat/completions",
                                          model="mock-model", render_func=fake_blender,
                                          repair_func=lambda *a, **kw: self.fail("should not repair"))
            self.assertEqual(held["status"], "HOLD_NO_CONFIDENT_DETECTED_COMPONENT")
            self.assertFalse(held["geometry_optimization_run"])


if __name__ == "__main__":
    unittest.main()
