"""Offline package validation, hostile input and deterministic reuse tests."""
import copy
import hashlib
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools" / "paperdoll_pack"))
from pack import pack_frames, verify_package


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def make_source(root, directions=4):
    root.mkdir(parents=True, exist_ok=True)
    headings = ["front", "right", "back", "left"] if directions == 4 else [
        "north", "northeast", "east", "southeast",
        "south", "southwest", "west", "northwest"
    ]
    animations = {
        "idle": {"frames": 1, "fps": 4.0, "loop": True},
        "walk": {"frames": 3, "fps": 8.0, "loop": True},
    }
    spec = dict(schema="last-light.paperdoll.frames.v1", asset_id="ll_zombie_layer_candidate",
                rig="ll_biped_v1", tile_px=[80, 40],
                frame_size=[32, 48], pivot=[16, 44],
                golden_approved=False, directions=headings,
                animations=animations, frames=[])
    for slot, item in [("body", "base"), ("pants", "jeans"),
                       ("shirt", "green_shirt"), ("shirt", "blue_shirt"),
                       ("backpack", "pack")]:
        for clip, detail in animations.items():
            for direction in headings:
                for frame in range(detail["frames"]):
                    image = Image.new("RGBA", (32, 48), (0, 0, 0, 0))
                    color = {
                        "body": (174, 125, 97, 255),
                        "pants": (43, 57, 66, 255),
                        "shirt": ((64, 105, 68, 255) if item == "green_shirt" else (54, 70, 113, 255)),
                        "backpack": (91, 67, 44, 255),
                    }[slot]
                    from PIL import ImageDraw
                    draw = ImageDraw.Draw(image)
                    dx = frame % 2
                    if slot == "body":
                        draw.ellipse((12 + dx, 4, 21 + dx, 16), fill=color)
                        draw.rectangle((13 + dx, 16, 20 + dx, 40), fill=color)
                    elif slot == "pants":
                        draw.rectangle((13 + dx, 27, 16 + dx, 43), fill=color)
                        draw.rectangle((18 + dx, 27, 21 + dx, 43), fill=color)
                    elif slot == "shirt":
                        draw.rectangle((9 + dx, 17, 23 + dx, 29), fill=color)
                    else:
                        draw.rectangle((21 + dx, 19, 28 + dx, 31), fill=color)
                    rel = f"frames/{slot}_{item}_{clip}_{direction}_{frame:02d}.png"
                    path = root / rel
                    path.parent.mkdir(parents=True, exist_ok=True)
                    image.save(path)
                    spec["frames"].append({
                        "slot": slot, "item_id": item, "animation": clip,
                        "direction": direction, "frame": frame,
                        "file": rel, "sha256": sha(path)
                    })
    (root / "manifest.json").write_text(json.dumps(spec, indent=2) + "\n")
    return spec


class PackageTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.input = self.root / "input"
        self.output = self.root / "out"
        self.manifest = make_source(self.input)

    def write(self):
        (self.input / "manifest.json").write_text(json.dumps(self.manifest))

    def test_01_real_pack_and_independent_sha(self):
        manifest = pack_frames(self.input, self.output)
        self.assertEqual(manifest["generated_sheet_count"], 10)
        self.assertEqual(verify_package(self.output)["sheets"], 10)
        self.assertEqual(manifest["status"], "TECHNICAL_CANDIDATE_NOT_GOLDEN")
        self.assertEqual(manifest["runtime"]["pivot"], [16, 44])

    def test_02_determinism(self):
        pack_frames(self.input, self.output)
        out2 = self.root / "out2"
        pack_frames(self.input, out2)
        first = sorted(p.relative_to(self.output) for p in self.output.rglob("*.png"))
        second = sorted(p.relative_to(out2) for p in out2.rglob("*.png"))
        self.assertEqual(first, second)
        for rel in first:
            self.assertEqual(sha(self.output / rel), sha(out2 / rel))

    def test_03_reject_tampered_source_sha(self):
        target = self.input / self.manifest["frames"][0]["file"]
        with target.open("ab") as out:
            out.write(b"changed")
        with self.assertRaisesRegex(ValueError, "hash mismatch"):
            pack_frames(self.input, self.output)

    def test_04_reject_missing_frame(self):
        self.manifest["frames"].pop()
        self.write()
        with self.assertRaisesRegex(ValueError, "incomplete"):
            pack_frames(self.input, self.output)

    def test_05_reject_duplicate_frame(self):
        self.manifest["frames"].append(self.manifest["frames"][0])
        self.write()
        with self.assertRaisesRegex(ValueError, "duplicate"):
            pack_frames(self.input, self.output)

    def test_06_reject_path_escape(self):
        self.manifest["frames"][0]["file"] = "../secret.png"
        self.write()
        with self.assertRaisesRegex(ValueError, "unsafe"):
            pack_frames(self.input, self.output)

    def test_07_reject_golden_or_bad_pivot(self):
        self.manifest["golden_approved"] = True
        self.write()
        with self.assertRaisesRegex(ValueError, "Golden"):
            pack_frames(self.input, self.output)
        self.manifest["golden_approved"] = False
        self.manifest["pivot"] = [20, 90]
        self.write()
        with self.assertRaisesRegex(ValueError, "pivot"):
            pack_frames(self.input, self.output)

    def test_08_detect_tampered_output_and_no_overwrite(self):
        pack_frames(self.input, self.output)
        with self.assertRaisesRegex(ValueError, "replace"):
            pack_frames(self.input, self.output)
        target = next(self.output.glob("atlases/**/*.png"))
        with target.open("ab") as out:
            out.write(b"changed")
        with self.assertRaisesRegex(ValueError, "SHA mismatch"):
            verify_package(self.output)

    def test_09_reject_missing_body(self):
        self.manifest["frames"] = [v for v in self.manifest["frames"] if v["slot"] != "body"]
        self.write()
        with self.assertRaisesRegex(ValueError, "body"):
            pack_frames(self.input, self.output)

    def test_10_eight_direction_candidate(self):
        shutil.rmtree(self.input)
        make_source(self.input, directions=8)
        built = pack_frames(self.input, self.output)
        self.assertEqual(built["runtime"]["directions"], 8)
        self.assertEqual(verify_package(self.output)["sheets"], 10)

    def test_11_all_source_pixels_preserved_without_alpha_bleed(self):
        pack_frames(self.input, self.output)
        headings = self.manifest["directions"]
        for record in self.manifest["frames"]:
            original_path = self.input / record["file"]
            atlas_path = self.output / "atlases" / record["slot"] / record["item_id"] / (record["animation"] + ".png")
            row = headings.index(record["direction"])
            col = record["frame"]
            with Image.open(original_path) as src, Image.open(atlas_path) as atlas:
                crop = atlas.crop((col * 32, row * 48, col * 32 + 32, row * 48 + 48))
                self.assertEqual(crop.mode, "RGBA")
                self.assertEqual(crop.tobytes(), src.tobytes(),
                                 f"pixel drift in {record['slot']}/{record['item_id']}")

    def test_12_reject_symlink_escape(self):
        external = self.root / "external.png"
        Image.new("RGBA", (32, 48), (255, 255, 255, 255)).save(external)
        alias = self.input / "frames" / "alias.png"
        alias.symlink_to(external)
        self.manifest["frames"][0]["file"] = "frames/alias.png"
        self.manifest["frames"][0]["sha256"] = sha(external)
        self.write()
        with self.assertRaisesRegex(ValueError, "escapes root"):
            pack_frames(self.input, self.output)


def emit_fixture(root=ROOT):
    source = root / "build" / "paperdoll_source"
    target = root / "build" / "paperdoll_package"
    if source.exists():
        shutil.rmtree(source)
    if target.exists():
        shutil.rmtree(target)
    make_source(source, directions=8)
    result = pack_frames(source, target)
    print("LL_PAPERDOLL_FIXTURE_PASS", json.dumps({
        "source_frames": result["source_frame_count"],
        "sheets": result["generated_sheet_count"],
        "directions": result["runtime"]["directions"],
        "catalog": str(target / "catalog.json")
    }))


if __name__ == "__main__":
    if "--emit-fixture" in sys.argv:
        emit_fixture()
    else:
        unittest.main()
