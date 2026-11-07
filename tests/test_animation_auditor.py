import importlib.util
import json
import tempfile
import unittest
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


if __name__ == "__main__":
    unittest.main()
