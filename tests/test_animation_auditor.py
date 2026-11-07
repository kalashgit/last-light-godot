import importlib.util
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from PIL import Image


SCRIPT = Path(__file__).resolve().parents[1] / "tools" / "last_light_animation_auditor.py"
SPEC = importlib.util.spec_from_file_location("animation_auditor", SCRIPT)
AUDITOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDITOR)


class AnimationAuditorTests(unittest.TestCase):
    def test_multiframe_static_sheet_corrupt_and_duplicate(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            input_dir, output_dir = root / "inputs", root / "reports"
            input_dir.mkdir()
            first = Image.new("RGBA", (8, 8), "red")
            second = Image.new("RGBA", (8, 8), "blue")
            first.save(input_dir / "still.png")
            (input_dir / "copy.png").write_bytes((input_dir / "still.png").read_bytes())
            Image.new("RGBA", (32, 8), "yellow").save(input_dir / "strip.png")
            first.save(input_dir / "walk.gif", save_all=True, append_images=[second], duration=[100, 200], loop=0)
            (input_dir / "broken.gif").write_bytes(b"GIF89a damaged")

            report = AUDITOR.audit(input_dir, output_dir)
            records = {row["path"]: row for row in map(json.loads, (output_dir / "animation_inventory.jsonl").read_text().splitlines())}
            self.assertEqual(report["scanned"], 5)
            self.assertEqual(records["walk.gif"]["frames"], 2)
            self.assertEqual(records["walk.gif"]["duration_ms"], 300)
            self.assertTrue(records["walk.gif"]["animated"])
            self.assertEqual(records["strip.png"]["classification"], "possible_sprite_sheet_unverified")
            self.assertEqual(records["still.png"]["classification"], "static_image")
            self.assertEqual(records["broken.gif"]["status"], "error")
            self.assertEqual(len(report["duplicates"]), 1)
            self.assertEqual(report["game_art_approved"], 0)
            before = (output_dir / "animation_inventory.jsonl").read_bytes()
            AUDITOR.audit(input_dir, output_dir)
            self.assertEqual(before, (output_dir / "animation_inventory.jsonl").read_bytes())

    def test_deterministic_limit_and_output_exclusion(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            Image.new("RGB", (5, 5)).save(root / "a.png")
            Image.new("RGB", (6, 6)).save(root / "b.png")
            report = AUDITOR.audit(root, root / "audit", max_files=1)
            self.assertEqual(report["scanned"], 1)
            self.assertEqual(AUDITOR.audit(root, root / "audit")["scanned"], 2)

    def test_zip_streaming_catalog_reconciliation_and_missing_rows(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            img = root / "animated.gif"
            Image.new("RGB", (4, 4), "blue").save(img)
            archive = root / "research.zip"
            with zipfile.ZipFile(archive, "w") as zipped:
                zipped.write(img, arcname="images/Tree_Animation.gif")
                zipped.writestr("../invalid.gif", b"GIF89a invalid")
            catalog = root / "catalog.jsonl"
            catalog.write_text("\n".join(json.dumps(item) for item in [
                {"id": "source.1", "source_filename": "Tree Animation.gif", "category": "animated_images"},
                {"id": "source.2", "source_filename": "Tree_Animation.gif", "category": "other"},
                {"id": "source.3", "source_filename": "Absent.gif", "category": "animated_images"},
            ]), encoding="utf-8")
            report = AUDITOR.audit(None, root / "out", archives=[archive], catalog_dirs=[catalog])
            rows = [json.loads(line) for line in (root / "out" / "animation_inventory.jsonl").read_text().splitlines()]
            self.assertEqual(report["scanned"], 2)
            self.assertEqual(report["catalog_records"], 3)
            self.assertEqual(report["catalog_matched_ids"], 2)
            self.assertEqual(report["catalog_unmatched_ids"], 1)
            self.assertEqual(report["catalog_ambiguous_filenames"], 1)
            self.assertEqual(rows[1]["source_match"], "ambiguous")
            self.assertEqual(rows[1]["source_ids"], ["source.1", "source.2"])
            self.assertEqual(rows[0]["classification"], "unsafe_zip_path")
            self.assertIn("source.3", (root / "out" / "missing_catalog_records.csv").read_text())
            self.assertFalse((root / "invalid.gif").exists())

    def test_catalog_only_uses_hints_not_fake_animations(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            catalog = root / "catalog.jsonl"
            catalog.write_text(json.dumps({"id": "reference.1", "source_filename": "Walk.gif"}) + "\n")
            report = AUDITOR.audit(None, root / "out", catalog_dirs=[catalog])
            self.assertEqual(report["scanned"], 0)
            self.assertEqual(report["catalog_gif_filename_hints"], 1)
            self.assertEqual(report["counts"], {})

    def test_indexed_icon_catalog_rows_get_traceable_identifiers(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            catalog = root / "icons.jsonl"
            catalog.write_text(json.dumps({"record_type": "external_reference", "index": 3,
                                           "source_filename": "Acorn.png"}) + "\n")
            report = AUDITOR.audit(None, root / "report", catalog_dirs=[catalog])
            self.assertEqual(report["catalog_records"], 1)
            self.assertIn("pzwiki.icon.000003", (root / "report" / "missing_catalog_records.csv").read_text())

    def test_numbered_png_frames_are_candidates_with_gap_reporting(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            frame_dir = root / "frames"
            frame_dir.mkdir()
            for number in (0, 1, 3):
                Image.new("RGBA", (16, 12), "blue").save(frame_dir / f"walk_{number:02d}.png")
            report = AUDITOR.audit(frame_dir, root / "audit")
            self.assertEqual(report["numbered_frame_sequence_candidates"], 1)
            self.assertEqual(report["numbered_frame_sequence_gaps"], 1)
            sequences = json.loads((root / "audit" / "numbered_frame_sequences.json").read_text())
            self.assertEqual(sequences[0]["missing_between"], [2])
            self.assertIsNone(sequences[0]["fps"])
            self.assertFalse(sequences[0]["approved_for_game"])

    def test_held_rotation_poses_do_not_count_as_animation(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for number in range(8):
                Image.new("RGBA", (10, 10)).save(root / f"held_{number:02d}.png")
            report = AUDITOR.audit(root, root / "output")
            self.assertEqual(report["directional_pose_sets"], 1)
            self.assertEqual(report["numbered_frame_sequence_candidates"], 0)


if __name__ == "__main__":
    unittest.main()
