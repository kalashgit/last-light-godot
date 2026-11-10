"""Synthetic orchestration tests. Mocked runners are NOT live VLM/mesh evidence."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image

from tools.foundry_reference_sheets.build import SOURCE_DIR
from tools.recipe_architect import batch_queue, sheet_crops


ENDPOINT = "http://127.0.0.1:9898/v1/chat/completions"


class BatchQueueTests(unittest.TestCase):
    def prepared(self, root: Path, count: int = 40) -> tuple[Path, Path]:
        crops = root / "private_crops"
        sheet_crops.extract(SOURCE_DIR, start=1, count=count, out=crops)
        manifest = crops / "crop_manifest.json"
        queue = root / "queue"
        batch_queue.initialize(manifest, queue)
        return manifest, queue

    def test_100_numbered_source_mesh_slots_isolated_without_creating_models(self):
        with tempfile.TemporaryDirectory() as tmp:
            manifest, queue = self.prepared(Path(tmp), 100)
            registry = json.loads(manifest.read_text())
            data = json.loads((queue / "queue.json").read_text())
            self.assertEqual(len(registry["crops"]), 100)
            self.assertEqual(len(data["jobs"]), 100)
            self.assertEqual(data["max_builds_per_dispatch"], 3)
            self.assertEqual(sum(j["state"] == "READY" for j in data["jobs"]), 99)
            self.assertEqual(sum(j["state"] == "ISOLATION_HOLD" for j in data["jobs"]), 1)
            self.assertFalse(data["automatic_golden_approval"])
            self.assertFalse(data["production_scaling_gate_passed"])
            self.assertFalse(any((queue / "jobs").rglob("*.glb")))
            with Image.open(Path(tmp) / "private_crops/crops/ref_0001.png") as frame:
                self.assertLess(frame.width, 180)
                self.assertLess(frame.height, 240)
                # Pale background is preserved for the local vision model.
                self.assertEqual(frame.getpixel((0, 0)), (255, 255, 255))

    def test_40_50_60_and_100_contracts_and_no_overwrite(self):
        for count in (40, 50, 60, 100):
            with self.subTest(count=count), tempfile.TemporaryDirectory() as tmp:
                manifest, queue = self.prepared(Path(tmp), count)
                self.assertEqual(json.loads((queue / "queue.json").read_text())
                                 ["sheet_reference_count"], count)
                with self.assertRaises(FileExistsError):
                    batch_queue.initialize(manifest, queue)
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                sheet_crops.extract(SOURCE_DIR, start=360, count=100,
                                    out=Path(tmp) / "invalid")

    def test_three_job_wave_checkpoints_without_golden(self):
        with tempfile.TemporaryDirectory() as tmp:
            manifest, queue = self.prepared(Path(tmp))
            calls = []

            def fake_runner(source, *, reference_id, manifest, out, endpoint, model, blender, timeout):
                calls.append(reference_id)
                self.assertEqual(source.suffix, ".png")
                self.assertFalse(out.exists())
                return {"source_reference_id": reference_id,
                        "source_sha256": batch_queue.sha256(source),
                        "founder_golden_approved": False, "canonical_admitted": False,
                        "actual_local_vision_request_completed": True,
                        "blender_glb_generated": True, "technical_qa_pass": True,
                        "candidate_id": "candidate_" + reference_id[-4:],
                        "measured_visual_score_final": .53,
                        "accepted_corrections": 1}

            with patch.object(batch_queue, "_local_model_available", return_value=True), \
                 patch.object(batch_queue, "_resources_sufficient", return_value=True), \
                 patch.object(batch_queue, "_invoke_job", side_effect=fake_runner):
                one = batch_queue.dispatch(queue, manifest, endpoint=ENDPOINT,
                                           model="Qwen2.5-VL-3B", max_jobs=3)
                two = batch_queue.dispatch(queue, manifest, endpoint=ENDPOINT,
                                           model="Qwen2.5-VL-3B", max_jobs=3)
            self.assertEqual(one["attempted"], 3)
            self.assertEqual(one["technical_pass_this_dispatch"], 3)
            self.assertEqual(two["attempted"], 3)
            self.assertEqual(len(set(calls)), 6)
            self.assertEqual(one["ready_remaining"], 37)
            self.assertEqual(two["ready_remaining"], 34)
            data = json.loads((queue / "queue.json").read_text())
            self.assertTrue(all(job["golden_approved"] is False for job in data["jobs"]))
            self.assertEqual(sum(job["technical_pass"] for job in data["jobs"]), 6)
            self.assertEqual(len(list((queue / "runs").glob("*.json"))), 2)
            overview = batch_queue.status(queue)
            self.assertEqual(overview["technical_pass_visual_review_pending"], 6)
            self.assertFalse(overview["safe_to_unconditionally_build_100"])

    def test_isolation_hold_never_runs_and_missing_model_changes_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            manifest, queue = self.prepared(Path(tmp), 100)
            original = (queue / "queue.json").read_bytes()
            with patch.object(batch_queue, "_local_model_available", return_value=False):
                with self.assertRaisesRegex(ValueError, "no live local VLM"):
                    batch_queue.dispatch(queue, manifest, endpoint=ENDPOINT,
                                         model="Qwen2.5-VL-3B")
            self.assertEqual((queue / "queue.json").read_bytes(), original)
            with self.assertRaises(ValueError):
                batch_queue.dispatch(queue, manifest, endpoint=ENDPOINT,
                                     model="Qwen2.5-VL-3B", max_jobs=100)

    def test_crop_tampering_refused_before_invoking_model(self):
        with tempfile.TemporaryDirectory() as tmp:
            manifest, queue = self.prepared(Path(tmp))
            image = Path(tmp) / "private_crops/crops/ref_0001.png"
            with image.open("ab") as writer:
                writer.write(b"drift")
            with patch.object(batch_queue, "_invoke_job") as invoke:
                with self.assertRaisesRegex(ValueError, "changed reference image"):
                    batch_queue.dispatch(queue, manifest, endpoint=ENDPOINT,
                                         model="Qwen2.5-VL-3B")
                invoke.assert_not_called()

    def test_failed_attempt_needs_explicit_retry_and_keeps_attempt_number(self):
        with tempfile.TemporaryDirectory() as tmp:
            manifest, queue = self.prepared(Path(tmp))
            with patch.object(batch_queue, "_local_model_available", return_value=True), \
                 patch.object(batch_queue, "_resources_sufficient", return_value=True), \
                 patch.object(batch_queue, "_invoke_job", side_effect=RuntimeError("mock failure")):
                batch_queue.dispatch(queue, manifest, endpoint=ENDPOINT,
                                     model="Qwen2.5-VL-3B", max_jobs=1)
            data = json.loads((queue / "queue.json").read_text())
            self.assertEqual(data["jobs"][0]["state"], "JOB_FAILED")
            self.assertEqual(len(data["jobs"][0]["attempts"]), 1)
            with patch.object(batch_queue, "_local_model_available", return_value=True), \
                 patch.object(batch_queue, "_resources_sufficient", return_value=True), \
                 patch.object(batch_queue, "_invoke_job", side_effect=RuntimeError("still failing")):
                batch_queue.dispatch(queue, manifest, endpoint=ENDPOINT,
                                     model="Qwen2.5-VL-3B", max_jobs=1, retry_failed=True)
            data = json.loads((queue / "queue.json").read_text())
            self.assertEqual(len(data["jobs"][0]["attempts"]), 2)
            self.assertEqual(data["jobs"][0]["state"], "JOB_FAILED")
            self.assertFalse(data["jobs"][0]["golden_approved"])

    def test_interrupted_attempt_is_preserved_not_restarted_automatically(self):
        with tempfile.TemporaryDirectory() as tmp:
            manifest, queue = self.prepared(Path(tmp))
            receipt = queue / "queue.json"
            data = json.loads(receipt.read_text())
            data["jobs"][0]["state"] = "RUNNING"
            data["jobs"][0]["attempts"] = [{"attempt": 1, "state": "RUNNING"}]
            receipt.write_text(json.dumps(data))
            with patch.object(batch_queue, "_local_model_available", return_value=True), \
                 patch.object(batch_queue, "_resources_sufficient", return_value=False), \
                 patch.object(batch_queue, "_invoke_job") as runner:
                result = batch_queue.dispatch(queue, manifest, endpoint=ENDPOINT,
                                              model="Qwen2.5-VL-3B", max_jobs=1)
                runner.assert_not_called()
            data = json.loads(receipt.read_text())
            self.assertEqual(data["jobs"][0]["state"], "JOB_FAILED")
            self.assertIn("interrupted_dispatch", data["jobs"][0]["attempts"][0]["error"])
            self.assertEqual(result["attempted"], 0)

    def test_forged_approval_bit_refused_before_model_call(self):
        with tempfile.TemporaryDirectory() as tmp:
            manifest, queue = self.prepared(Path(tmp))
            receipt = queue / "queue.json"
            data = json.loads(receipt.read_text())
            data["jobs"][0]["golden_approved"] = True
            receipt.write_text(json.dumps(data))
            with patch.object(batch_queue, "_invoke_job") as runner:
                with self.assertRaisesRegex(ValueError, "tampering"):
                    batch_queue.dispatch(queue, manifest, endpoint=ENDPOINT,
                                         model="Qwen2.5-VL-3B", max_jobs=1)
                runner.assert_not_called()


if __name__ == "__main__":
    unittest.main()
