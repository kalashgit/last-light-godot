"""Offline local VLM proposal tests: synthetic responses are NOT inference."""
from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image

from tools.recipe_architect import autonomous_job, local_vlm, sheet_crops
from tools.recipe_architect.pilot import ROOT


BATTERY = ROOT / "data/foundry_recipe_architect/vehicle_battery_recipe_v1.json"


def seed_shaped_proposal():
    """Mock output shape only, not observations inferred by a model."""
    s = json.loads(BATTERY.read_text())
    return {
        "category": s["visual_analysis"]["category"],
        "function": s["visual_analysis"]["probable_function"],
        "observations": s["visual_analysis"]["observations"],
        "assumptions": s["visual_analysis"]["assumptions"],
        "artifacts": s["visual_analysis"]["artifacts"],
        "confidence": s["visual_analysis"]["confidence"],
        "components": s["components"], "materials": s["materials"],
        "expected_silhouette": s["quality"]["expected_silhouette"],
        "footprint_m": s["gameplay"]["footprint_m"],
    }


class LocalVLMTests(unittest.TestCase):
    def source(self, path):
        Image.new("RGBA", (80, 80), (88, 70, 50, 255)).save(path)

    def test_only_explicit_loopback_endpoint_allowed(self):
        self.assertEqual(local_vlm.checked_loopback_url("http://127.0.0.1:8090/v1/chat/completions"),
                         "http://127.0.0.1:8090/v1/chat/completions")
        for url in ("https://hosted.example/v1/chat/completions",
                    "http://localhost:8090/v1/chat/completions",
                    "http://127.0.0.1:8090@external.example/v1/chat/completions",
                    "http://127.0.0.1:8090/anything", "http://127.0.0.1/v1/chat/completions"):
            with self.subTest(url=url), self.assertRaises(ValueError):
                local_vlm.checked_loopback_url(url)
        with self.assertRaisesRegex(ValueError, "redirect"):
            local_vlm.NoRedirect().redirect_request(None, None, 307, "redirect", {},
                                                     "https://external.example/infer")

    def test_host_seals_provenance_and_no_golden(self):
        with tempfile.TemporaryDirectory() as d:
            source = Path(d) / "reference.png"
            self.source(source)
            recipe = local_vlm.seal_proposal(source, seed_shaped_proposal(),
                    reference_id="LL-FGS-0042", source_rights="founder_original_pending_review",
                    model="Qwen2.5-VL-3B")
            self.assertEqual(recipe["identity"]["source_reference_id"], "LL-FGS-0042")
            self.assertEqual(recipe["identity"]["generation_method"], "vision_model_proposed")
            self.assertTrue(recipe["identity"]["source_sha256"])
            self.assertIsNone(recipe["identity"]["canonical_id"])
            self.assertFalse(recipe["quality"]["golden_approved"])
            self.assertEqual(recipe["quality"]["technical_status"], "CANDIDATE_PENDING_QA")

    def test_rejects_forged_approval_and_python_geometry(self):
        with tempfile.TemporaryDirectory() as d:
            source = Path(d) / "reference.png"
            self.source(source)
            p = seed_shaped_proposal()
            p["identity"] = {"golden_approved": True}
            with self.assertRaises(ValueError):
                local_vlm.seal_proposal(source, p, reference_id="LL-FGS-0042",
                    source_rights="founder_original_pending_review", model="local")
            p = seed_shaped_proposal()
            p["components"][0]["op"] = "python"
            with self.assertRaises(ValueError):
                local_vlm.seal_proposal(source, p, reference_id="LL-FGS-0042",
                    source_rights="founder_original_pending_review", model="local")

    def test_refuses_invented_observation_and_unapproved_rights(self):
        with tempfile.TemporaryDirectory() as d:
            source = Path(d) / "reference.png"
            self.source(source)
            p = seed_shaped_proposal()
            p["observations"][0]["component"] = "unseen_hallucination"
            with self.assertRaisesRegex(ValueError, "visible"):
                local_vlm.seal_proposal(source, p, reference_id="LL-FGS-0042",
                    source_rights="founder_original_pending_review", model="local")
            with self.assertRaisesRegex(ValueError, "source rights"):
                local_vlm.seal_proposal(source, seed_shaped_proposal(), reference_id="LL-FGS-0042",
                    source_rights="unresolved", model="local")

    def test_single_local_request_sends_actual_pixels_not_filename(self):
        with tempfile.TemporaryDirectory() as d:
            source = Path(d) / "object.png"
            self.source(source)
            p = seed_shaped_proposal()
            fake = {"choices": [{"message": {"content": json.dumps(p)}}],
                    "usage": {"prompt_tokens": 123, "completion_tokens": 45}}
            recorded = []

            class Response:
                def __enter__(self): return self
                def __exit__(self, *args): return False
                def read(self, amount): return json.dumps(fake).encode()

            class Opener:
                def open(self, req, timeout):
                    recorded.append((req, timeout))
                    return Response()

            with patch.object(local_vlm.urllib.request, "build_opener", return_value=Opener()):
                observed, audit = local_vlm.request_proposal(source,
                    endpoint="http://127.0.0.1:8090/v1/chat/completions", model="Qwen2.5-VL-3B")
            self.assertEqual(observed, p)
            self.assertTrue(audit["pixels_supplied"])
            self.assertEqual(audit["network_scope"], "loopback_only")
            self.assertEqual(audit["paid_model_calls"], 0)
            self.assertEqual(len(recorded), 1)
            self.assertEqual(recorded[0][1], local_vlm.MAX_SECONDS)
            sent = json.loads(recorded[0][0].data)
            self.assertIn("data:image/png;base64,", sent["messages"][1]["content"][1]["image_url"]["url"])

    def test_reference_sheet_crops_existing_f09_manifest(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "reference_crops"
            result = sheet_crops.extract(sheet_crops.SOURCE_DIR, start=1, count=10, out=out)
            self.assertEqual(result["extracted"], 10)
            self.assertEqual(result["crops"][0]["reference_id"], "LL-FGS-0001")
            self.assertIsNone(result["crops"][0]["canonical_asset_id"])
            self.assertFalse(result["founder_golden_approved"])
            self.assertFalse(result["original_pixels_inspected_by_vlm"])
            self.assertEqual(len(list((out / "crops").glob("*.png"))), 10)
            self.assertGreater(result["crops_with_possible_border_contamination"], 0)
            self.assertTrue(result["crops"][0]["crop_boundary_qa"]["possible_neighbor_or_truncation"])
            with self.assertRaises(FileExistsError):
                sheet_crops.extract(sheet_crops.SOURCE_DIR, start=1, count=10, out=out)

    def test_sheets_do_not_invent_missing_191_to_200(self):
        with tempfile.TemporaryDirectory() as d:
            result = sheet_crops.extract(sheet_crops.SOURCE_DIR, start=191, count=10,
                                          out=Path(d) / "gap")
            self.assertEqual([v["sheet_position"] for v in result["crops"]], list(range(201, 211)))

    def test_unattended_job_refuses_border_contaminated_real_crop(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "crops"
            sheet_crops.extract(sheet_crops.SOURCE_DIR, start=1, count=10, out=out)
            first = out / "crops/ref_0001.png"
            with patch.object(autonomous_job, "request_proposal") as request:
                with self.assertRaisesRegex(ValueError, "border-contaminated"):
                    autonomous_job.execute(first, reference_id="LL-FGS-0001",
                        rights="founder_original_pending_review", model="Qwen2.5-VL-3B",
                        endpoint="http://127.0.0.1:8090/v1/chat/completions",
                        crop_manifest=out / "crop_manifest.json", out=Path(d) / "blocked")
                request.assert_not_called()

    def test_mocked_vlm_to_blender_orchestration_is_not_live_inference(self):
        with tempfile.TemporaryDirectory() as d:
            source = Path(d) / "source.png"
            self.source(source)
            visual = {"technical_model_generated": True, "technical_qa_pass": True,
                      "initial_score": 0.45, "final_score": 0.5,
                      "accepted_corrections": 1, "stop_reason": "no_measured_improvement"}
            with patch.object(autonomous_job, "request_proposal",
                              return_value=(seed_shaped_proposal(), {"model": "mock", "paid_model_calls": 0})), \
                 patch.object(autonomous_job, "run_visual_loop", return_value=visual) as render:
                result = autonomous_job.execute(source, reference_id="LL-FGS-0042",
                    rights="founder_original_pending_review", model="Qwen2.5-VL-3B",
                    endpoint="http://127.0.0.1:8090/v1/chat/completions",
                    out=Path(d) / "job", max_iterations=2)
            self.assertEqual(result["accepted_corrections"], 1)
            self.assertFalse(result["founder_golden_approved"])
            self.assertEqual(render.call_count, 1)
            self.assertEqual(json.loads((Path(d) / "job/candidate_recipe.json").read_text())
                             ["identity"]["source_reference_id"], "LL-FGS-0042")
            self.assertTrue((Path(d) / "job/inference_receipt.json").exists())


if __name__ == "__main__":
    unittest.main()
