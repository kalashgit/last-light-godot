import importlib.util
import hashlib
import json
import sqlite3
import tempfile
import unittest
import zipfile
import sys
from pathlib import Path

from PIL import Image, features


SCRIPT = Path(__file__).resolve().parents[1] / "tools" / "last_light_animation_auditor.py"
sys.path.insert(0, str(SCRIPT.parent))
SPEC = importlib.util.spec_from_file_location("animation_auditor", SCRIPT)
AUDITOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDITOR)


class AnimationAuditorTests(unittest.TestCase):
    def cache_row(self, path, name="walk.gif", identifier="pzwiki.file.000001"):
        data = path.read_bytes()
        return {"schema": "last_light.verified_cache_entry.v1", "source_id": identifier,
                "relative_path": name, "sha256": hashlib.sha256(data).hexdigest(),
                "byte_length": len(data), "mime": "image/gif", "category": "animation",
                "rights": "research_only", "retrieved_at": "2026-11-07T00:00:00Z",
                "verification_status": "verified"}

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

    def test_verified_cache_audit_resume_is_read_only(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            cache = root / "cache"
            cache.mkdir()
            frames = [Image.new("RGB", (9, 9), color) for color in ("red", "blue")]
            frames[0].save(cache / "walk.gif", save_all=True, append_images=frames[1:], duration=[100, 200], loop=0)
            row = self.cache_row(cache / "walk.gif")
            manifest = root / "verified.jsonl"
            manifest.write_text(json.dumps(row) + "\n")
            original_media = (cache / "walk.gif").read_bytes()
            report = AUDITOR.audit(None, root / "derived", cache_manifest=manifest, cache_root=cache)
            self.assertEqual(report["verified_cache"]["inspected"], 1)
            self.assertEqual(report["verified_cache"]["failed"], 0)
            records = [json.loads(line) for line in (root / "derived" / "animation_inventory.jsonl").read_text().splitlines()]
            self.assertEqual(records[0]["source_ids"], [row["source_id"]])
            self.assertEqual(records[0]["source_match"], "cache_verified")
            self.assertEqual(records[0]["frame_durations_ms"], [100.0, 200.0])
            self.assertEqual(len(records[0]["frame_disposal"]), 2)
            self.assertEqual((cache / "walk.gif").read_bytes(), original_media)
            second = AUDITOR.audit(None, root / "derived", cache_manifest=manifest, cache_root=cache, resume=True)
            self.assertEqual(second["verified_cache"]["reused_checkpoint"], 1)
            self.assertFalse((cache / "animation_audit_checkpoint.sqlite3").exists())

    def test_cache_rejects_traversal_symlink_and_same_size_hash_change(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            cache = root / "cache"
            cache.mkdir()
            image = cache / "test.gif"
            Image.new("RGB", (5, 5), "red").save(image)
            good = self.cache_row(image, name="test.gif")
            image.write_bytes(image.read_bytes()[:-1] + b"X")  # Same length, wrong hash.
            bad_path = dict(good, source_id="pzwiki.file.000002", relative_path="../outside.gif")
            outside = root / "outside.gif"
            outside.write_bytes(b"GIF89a")
            (cache / "alias.gif").symlink_to(outside)
            bad_link = dict(good, source_id="pzwiki.file.000003", relative_path="alias.gif")
            missing = dict(good, source_id="pzwiki.file.000004", relative_path="missing.gif")
            manifest = root / "verified.jsonl"
            manifest.write_text("\n".join(map(json.dumps, (good, bad_path, bad_link, missing))) + "\n")
            report = AUDITOR.audit(None, root / "out", cache_manifest=manifest, cache_root=cache)
            rows = list(map(json.loads, (root / "out" / "animation_inventory.jsonl").read_text().splitlines()))
            self.assertEqual(report["verified_cache"]["failed"], 4)
            self.assertEqual([r["error_code"] for r in rows],
                             ["CACHE_HASH_MISMATCH", "UNSAFE_CACHE_PATH", "CACHE_SYMLINK_REJECTED", "CACHE_FILE_MISSING"])
            with self.assertRaisesRegex(ValueError, "outside the read-only cache"):
                AUDITOR.audit(None, cache / "bad-output", cache_manifest=manifest, cache_root=cache)

    def test_sqlite_manifest_and_resource_limits(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            cache = root / "cache"
            cache.mkdir()
            first = Image.new("RGB", (8, 8), "red")
            first.save(cache / "walk.gif", save_all=True,
                       append_images=[Image.new("RGB", (8, 8), "green")], duration=[0, 200], loop=0)
            row = self.cache_row(cache / "walk.gif")
            db = root / "sources.sqlite3"
            with sqlite3.connect(db) as connection:
                connection.execute("CREATE TABLE verified_media (schema TEXT, source_id TEXT, relative_path TEXT, sha256 TEXT, byte_length INTEGER, mime TEXT, category TEXT, rights TEXT, retrieved_at TEXT, verification_status TEXT)")
                connection.execute("INSERT INTO verified_media VALUES(?,?,?,?,?,?,?,?,?,?)", tuple(row.values()))
            report = AUDITOR.audit(None, root / "out", cache_manifest=db, cache_root=cache, max_frames=1)
            self.assertEqual(report["verified_cache"]["failed"], 1)
            record = json.loads((root / "out" / "animation_inventory.jsonl").read_text().splitlines()[0])
            self.assertEqual(record["error_code"], "RESOURCE_LIMIT_FRAMES")
            AUDITOR.audit(None, root / "out", cache_manifest=db, cache_root=cache)
            record = json.loads((root / "out" / "animation_inventory.jsonl").read_text().splitlines()[0])
            self.assertTrue({"NONPOSITIVE_FRAME_DELAY", "MISSING_FRAME_DELAY"} & set(record["timing_issues"]))

    def test_apng_and_animated_webp_when_codec_supported(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            first = Image.new("RGBA", (7, 7), "red")
            second = Image.new("RGBA", (7, 7), "blue")
            first.save(root / "a.png", save_all=True, append_images=[second], duration=[100, 200], loop=0)
            apng = AUDITOR.inspect(root / "a.png", "a.png")
            self.assertEqual(apng["classification"], "animated_file")
            self.assertEqual(apng["frames"], 2)
            if features.check("webp"):
                first.save(root / "b.webp", save_all=True, append_images=[second], duration=[100, 200], loop=0)
                webp = AUDITOR.inspect(root / "b.webp", "b.webp")
                self.assertEqual(webp["classification"], "animated_file")
                self.assertEqual(webp["frames"], 2)

    def test_verified_cache_mime_and_extension_disagreement(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            cache = root / "cache"
            cache.mkdir()
            Image.new("RGBA", (9, 9), "red").save(cache / "actually.png")
            (cache / "wrong.gif").write_bytes((cache / "actually.png").read_bytes())
            row = self.cache_row(cache / "wrong.gif", name="wrong.gif")
            manifest = root / "verified.jsonl"
            manifest.write_text(json.dumps(row) + "\n")
            report = AUDITOR.audit(None, root / "out", cache_manifest=manifest, cache_root=cache)
            self.assertEqual(report["verified_cache"]["failed"], 1)
            record = json.loads((root / "out" / "animation_inventory.jsonl").read_text().splitlines()[0])
            self.assertEqual(record["error_code"], "CACHE_MIME_MISMATCH")
            self.assertIn("FORMAT_EXTENSION_MISMATCH", record["format_issues"])

    def test_cache_requires_explicit_schema_and_rejects_duplicate_ids(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            cache = root / "cache"
            cache.mkdir()
            Image.new("RGB", (4, 4)).save(cache / "one.gif")
            valid = self.cache_row(cache / "one.gif", name="one.gif")
            missing_schema = dict(valid)
            missing_schema.pop("schema")
            manifest = root / "verified.jsonl"
            manifest.write_text(json.dumps(missing_schema) + "\n" + json.dumps(valid) + "\n")
            report = AUDITOR.audit(None, root / "out", cache_manifest=manifest, cache_root=cache)
            self.assertEqual(report["verified_cache"]["failed"], 2)
            rows = list(map(json.loads, (root / "out" / "animation_inventory.jsonl").read_text().splitlines()))
            self.assertEqual([r["error_code"] for r in rows],
                             ["CACHE_SCHEMA_MISMATCH", "DUPLICATE_CACHE_SOURCE_ID"])


if __name__ == "__main__":
    unittest.main()
