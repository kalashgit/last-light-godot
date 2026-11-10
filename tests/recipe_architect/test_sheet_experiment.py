"""Actual founder-sheet seed recipes; tests do not claim a vision-model run."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageDraw

from tools.foundry_reference_sheets.build import SOURCE_DIR
from tools.recipe_architect.contract import sha256, validate
from tools.recipe_architect.sheet_crops import extract
from tools.recipe_architect.sheet_experiment import alpha_isolate_paper, prepare


class SheetExperimentTests(unittest.TestCase):
    def test_three_source_pinned_distinct_editable_recipes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            crops = root / "crops"
            extract(SOURCE_DIR, start=1, count=50, out=crops)
            jobs = prepare(crops / "crop_manifest.json", root / "experiment")
            self.assertEqual([j["position"] for j in jobs], [5, 35, 44])
            for job in jobs:
                with self.subTest(position=job["position"]):
                    scoring = Path(job["scoring_source"])
                    recipe = json.loads(Path(job["recipe_file"]).read_text())
                    validate(recipe, scoring, full_schema=True)
                    self.assertEqual(recipe["identity"]["source_sha256"], sha256(scoring))
                    self.assertEqual(job["source_masking"]["source_crop_sha256"],
                                     sha256(Path(job["source_crop"])))
                    self.assertGreaterEqual(len(recipe["components"]), 7)
                    self.assertFalse(recipe["quality"]["golden_approved"])
                    self.assertEqual(recipe["identity"]["generation_method"], "pixel_inspected_seed")
                    self.assertNotIn("vision_model", recipe["visual_analysis"]["provider"])
                    self.assertTrue(all(c["op"] != "boolean_cut" or
                                        c["topology"] == "cutter" for c in recipe["components"]))
                    with Image.open(scoring) as im:
                        self.assertEqual(im.mode, "RGBA")
                        self.assertEqual(im.getpixel((0, 0))[3], 0)
                        self.assertGreater(im.getchannel("A").getbbox()[2], 20)
            report = json.loads((root / "experiment/recipe_experiment_manifest.json").read_text())
            self.assertFalse(report["autonomous_vision_model_invoked"])
            self.assertEqual(report["unselected_sheet_slots"], 47)
            self.assertEqual(report["models_prepared"], 3)

    def test_background_only_edge_connected_bright_paper(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "source.png"
            score = Path(tmp) / "scoring.png"
            image = Image.new("RGB", (60, 60), "white")
            draw = ImageDraw.Draw(image)
            draw.rectangle((14, 14, 45, 45), fill=(25, 30, 35))
            draw.rectangle((20, 20, 38, 38), fill="white")
            image.save(source)
            report = alpha_isolate_paper(source, score)
            with Image.open(score) as rgba:
                self.assertEqual(rgba.getpixel((0, 0))[3], 0)
                self.assertEqual(rgba.getpixel((15, 15))[3], 255)
                # White detail inside a dark shape is not mistaken for paper.
                self.assertEqual(rgba.getpixel((28, 28))[3], 255)
            self.assertEqual(report["masked_source_sha256"], sha256(score))

    def test_rejects_changed_crop_before_recipe_creation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            crops = root / "crops"
            extract(SOURCE_DIR, start=1, count=50, out=crops)
            original = crops / "crops/ref_0035.png"
            with original.open("ab") as f:
                f.write(b"tampering")
            with self.assertRaisesRegex(ValueError, "provenance changed"):
                prepare(crops / "crop_manifest.json", root / "experiment")


if __name__ == "__main__":
    unittest.main()
