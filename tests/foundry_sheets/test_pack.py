import json
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/foundry_sheets"))
from pack import pack, sha
from publish import stage


def candidate(root: Path, ident: str, size: int = 128):
    folder = root / ident
    folder.mkdir(parents=True)
    image = Image.new("RGBA", (4 * size + 20, 4 * size + 20))
    for i in range(16):
        col, row = i % 4, i // 4
        x, y = 4 + col * (size + 4), 4 + row * (size + 4)
        color = ((i * 11) % 255, 30, 140, 255)
        ImageDraw.Draw(image).rectangle((x + 10, y + 15, x + 33, y + 45), fill=color)
    atlas = folder / "atlas_16_headings.png"
    image.save(atlas)
    info = {"asset_id": ident, "views": 16,
            "source_glb_sha256": "a" * 64, "atlas_sha256": sha(atlas),
            "status": "TECHNICAL_SPRITE_CANDIDATE", "golden_approved": False,
            "f12_world_scale_approved": False}
    (folder / "manifest.json").write_text(json.dumps(info))
    return folder


class SheetTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name)
        self.source = self.path / "candidates"
        self.source.mkdir()
        candidate(self.source, "ll_furniture_mattress")
        candidate(self.source, "ll_furniture_bookcase")

    def test_deterministic_pack_and_reconstruct_original_pixels(self):
        first = self.path / "a"
        second = self.path / "b"
        report = pack(self.source, first, batch_size=2, run_id="123")
        pack(self.source, second, batch_size=2, run_id="123")
        self.assertEqual(report["frame_count"], 32)
        self.assertEqual(report["batch_count"], 2)
        self.assertEqual(sha(first / "sheet_0000.png"), sha(second / "sheet_0000.png"))
        manifest = json.loads((first / "sprite_sheet_manifest.json").read_text())
        self.assertFalse(manifest["golden_approved"])
        self.assertFalse(manifest["pivot_world_verified"] if "pivot_world_verified" in manifest else False)
        for row in manifest["frames"]:
            x, y, w, h = row["region"]
            with Image.open(first / f"sheet_{row['page']:04d}.png") as page:
                packed = page.crop((x, y, x + w, y + h))
            with Image.open(self.source / row["asset_id"] / "atlas_16_headings.png") as raw:
                size = row["source_size"][0]
                col, r = row["heading"] % 4, row["heading"] // 4
                original = raw.crop((4 + col * (size + 4), 4 + r * (size + 4),
                                     4 + col * (size + 4) + size, 4 + r * (size + 4) + size))
                ox, oy = row["trim_offset"]
                self.assertEqual(packed.tobytes(), original.crop((ox, oy, ox + w, oy + h)).tobytes())

    def test_persist_cursor_and_do_not_repack(self):
        first = self.path / "first"
        dest = self.path / "persist"
        pack(self.source, first, batch_size=1, run_id="123")
        self.assertEqual(stage(first, dest), 1)
        second = self.path / "second"
        pack(self.source, second, json.loads((dest / "foundry_sheets/state.json").read_text()),
             batch_size=1, run_id="124")
        self.assertEqual(stage(second, dest), 1)
        self.assertEqual(len(json.loads((dest / "foundry_sheets/state.json").read_text())["completed"]), 2)
        with self.assertRaises(ValueError):
            stage(first, dest)
        empty = self.path / "empty"
        report = pack(self.source, empty, json.loads((dest / "foundry_sheets/state.json").read_text()), run_id="125")
        self.assertEqual(report["batch_count"], 0)
        self.assertEqual(stage(empty, dest), 0)

    def test_reject_tampering_and_false_golden(self):
        path = self.source / "ll_furniture_mattress" / "manifest.json"
        data = json.loads(path.read_text())
        data["golden_approved"] = True
        path.write_text(json.dumps(data))
        with self.assertRaises(ValueError):
            pack(self.source, self.path / "bad", run_id="1")

    def test_reject_mutated_published_source(self):
        first = self.path / "first"
        pack(self.source, first, batch_size=1, run_id="1")
        state = json.loads((first / "next_state.json").read_text())
        chosen = state["completed"][0]["asset_id"]
        atlas = self.source / chosen / "atlas_16_headings.png"
        with Image.open(atlas) as img:
            img.save(atlas, optimize=True)
        with self.assertRaisesRegex(ValueError, "modified"):
            pack(self.source, self.path / "second", state, run_id="2")

    def test_page_and_batch_limits(self):
        for size in (512, 4096):
            with self.assertRaises(ValueError):
                pack(self.source, self.path / f"bad_{size}", page_size=size)
        for count in (0, 81):
            with self.assertRaises(ValueError):
                pack(self.source, self.path / f"bad_{count}", batch_size=count)
        with self.assertRaisesRegex(ValueError, "minimum"):
            pack(self.source, self.path / "bad_min", batch_size=4, min_batch_size=40)
        with self.assertRaisesRegex(ValueError, "cannot fill"):
            pack(self.source, self.path / "bad_inventory", batch_size=8,
                 inventory_page_items=40)

    def test_mass_80_assets_produce_two_genuine_40_item_pages(self):
        for i in range(78):
            candidate(self.source, f"ll_catalog_item_{i:03d}")
        output = self.path / "mass"
        report = pack(self.source, output, batch_size=80, min_batch_size=40,
                      inventory_page_items=40, page_size=2048, run_id="333")
        self.assertEqual(report["batch_count"], 80)
        self.assertEqual(report["frame_count"], 1280)
        self.assertEqual(report["inventory_page_count"], 2)
        self.assertEqual(report["status"], "PACKED")
        manifest = json.loads((output / "inventory_sheet_manifest.json").read_text())
        self.assertEqual([p["asset_count"] for p in manifest["pages"]], [40, 40])
        self.assertEqual(len(manifest["entries"]), 80)
        self.assertEqual(len({entry["asset_id"] for entry in manifest["entries"]}), 80)
        self.assertFalse(manifest["golden_approved"])
        for entry in manifest["entries"]:
            with Image.open(output / manifest["pages"][entry["page"]]["file"]) as page:
                x, y, w, h = entry["region"]
                icon = page.crop((x, y, x + w, y + h))
            with Image.open(self.source / entry["asset_id"] / "atlas_16_headings.png") as source:
                heading = entry["heading"]
                col, row = heading % 4, heading // 4
                size = entry["source_size"][0]
                raw = source.crop((4 + col * (size + 4), 4 + row * (size + 4),
                                   4 + col * (size + 4) + size,
                                   4 + row * (size + 4) + size))
            ox, oy = entry["trim_offset"]
            self.assertEqual(icon.tobytes(), raw.crop((ox, oy, ox + w, oy + h)).tobytes())
        self.assertEqual(stage(output, self.path / "persist"), 80)
        with Image.open(output / "inventory_sheet_0000.png") as original:
            altered = original.copy()
        altered.putpixel((0, 0), (18, 91, 47, 255))
        altered.save(output / "inventory_sheet_0000.png")
        with self.assertRaisesRegex(ValueError, "digest mismatch"):
            stage(output, self.path / "tampered")

    def test_mass_waits_for_40_distinct_assets_without_advancing_cursor(self):
        for i in range(37):
            candidate(self.source, f"ll_wait_item_{i:03d}")
        output = self.path / "waiting"
        first = pack(self.source, output, batch_size=40, min_batch_size=40,
                     inventory_page_items=40, page_size=2048, run_id="101")
        self.assertEqual(first["batch_count"], 0)
        self.assertEqual(first["held_for_full_page"], 39)
        self.assertEqual(first["status"], "WAITING_FOR_COMPLETE_INVENTORY_PAGE")
        self.assertFalse((output / "inventory_sheet_0000.png").exists())
        self.assertEqual(json.loads((output / "next_state.json").read_text())["completed"], [])
        candidate(self.source, "ll_wait_item_999")
        second = pack(self.source, self.path / "ready", batch_size=40,
                      min_batch_size=40, inventory_page_items=40,
                      page_size=2048, run_id="102")
        self.assertEqual(second["batch_count"], 40)
        self.assertEqual(second["inventory_page_count"], 1)

    def test_publish_rejects_modified_sheet_bytes(self):
        first = self.path / "first"
        pack(self.source, first, batch_size=1, run_id="1")
        with Image.open(first / "sheet_0000.png") as img:
            img.save(first / "sheet_0000.png", optimize=False)
        with self.assertRaisesRegex(ValueError, "digest"):
            stage(first, self.path / "persist")

    def test_schedule_requires_explicit_opt_in(self):
        text = (ROOT / ".github/workflows/foundry-mass-sprite-sheets.yml").read_text()
        self.assertIn("vars.FOUNDRY_SPRITE_SHEETS_ENABLED == 'true'", text)
        self.assertIn("github.actor == 'kalashgit'", text)
        self.assertIn("foundry/sprite-sheets-v1", text)


if __name__ == "__main__":
    unittest.main()
