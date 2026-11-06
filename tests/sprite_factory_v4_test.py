#!/usr/bin/env python3
"""Independent native-render, recovery and export-contract tests for V4.

These checks test engineering behavior. Passing them confers no visual or founder
approval, and says nothing about execution in CodePad, Xogot or on an iPhone.
"""
import copy
import argparse
import base64
import hashlib
import importlib.util
import io
import json
import tempfile
import sys
import platform
import unittest
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
FACTORY_PATH = ROOT / "LAST_LIGHT_MASTER_SPRITE_FACTORY_V4.py"
SPEC = importlib.util.spec_from_file_location("last_light_factory_v4_tested", FACTORY_PATH)
f = importlib.util.module_from_spec(SPEC)
FACTORY_SOURCE_BYTES = FACTORY_PATH.read_bytes()
sys.modules[SPEC.name] = f
exec(compile(FACTORY_SOURCE_BYTES, str(FACTORY_PATH), "exec"), f.__dict__)

EXPECTED_IDS = {
    "item.food.canned_beans", "item.food.canned_peas", "item.food.apple", "item.food.pear",
    "item.medical.first_aid_kit", "item.medical.bandage_box",
    "item.tools.claw_hammer", "item.tools.ball_peen_hammer",
    "item.tools.flathead_screwdriver", "item.tools.phillips_screwdriver",
    "item.tools.adjustable_wrench", "item.tools.pipe_wrench",
    "item.materials.wooden_plank", "item.materials.steel_bar",
    "item.materials.duct_tape", "item.materials.rope_coil",
    "item.containers.rucksack", "item.containers.tool_bag",
    "item.clothing.work_gloves", "item.clothing.winter_beanie",
    "item.electronics.handheld_radio", "item.electronics.flashlight",
    "item.survival.water_bottle", "item.survival.camping_mug",
}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def records(directory):
    path = Path(directory) / "manifest.jsonl"
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def normalized():
    return [f.normalize_recipe(copy.deepcopy(raw)) for raw in f.demo_recipes()]


class NativeRenderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.recipes = normalized()

    def test_exact_requested_twenty_four_logical_objects(self):
        self.assertEqual(len(self.recipes), 24)
        self.assertEqual({r["id"] for r in self.recipes}, EXPECTED_IDS)

    def test_all_objects_render_deterministically_at_native_resolution(self):
        hashes = []
        for recipe in self.recipes:
            with self.subTest(item=recipe["id"]):
                first = f.render_icon(recipe, variant=0)
                again = f.render_icon(copy.deepcopy(recipe), variant=0)
                self.assertEqual(first.mode, "RGBA")
                self.assertEqual(first.size, (64, 64))
                self.assertEqual(first.tobytes(), again.tobytes())
                report = f.technical_qa(first)
                self.assertTrue(report["passed"], report)
                self.assertFalse(report["errors"], report)
                hashes.append(hashlib.sha256(first.tobytes()).hexdigest())
        self.assertEqual(len(set(hashes)), 24, "Different requested objects must not have identical pixels")

    def test_seeded_variants_reproduce_without_inflating_item_count(self):
        changed = 0
        for recipe in self.recipes:
            with self.subTest(item=recipe["id"]):
                original = f.render_icon(recipe, variant=0)
                variant = f.render_icon(recipe, variant=1)
                self.assertEqual(variant.tobytes(), f.render_icon(recipe, variant=1).tobytes())
                self.assertTrue(f.technical_qa(variant)["passed"])
                changed += original.tobytes() != variant.tobytes()
        self.assertGreater(changed, 0, "A variant index must influence intentional render variation")

    def test_seed_is_part_of_deterministic_recipe(self):
        original = self.recipes[0]
        changed = copy.deepcopy(original)
        changed["seed"] += 97
        a = f.render_icon(changed, variant=1)
        self.assertEqual(a.tobytes(), f.render_icon(changed, variant=1).tobytes())
        self.assertNotEqual(hashlib.sha256(a.tobytes()).hexdigest(),
                            hashlib.sha256(f.render_icon(original, variant=1).tobytes()).hexdigest())

    def test_semantic_parts_have_materials_and_construction(self):
        for recipe in self.recipes:
            with self.subTest(item=recipe["id"]):
                self.assertTrue(recipe["parts"])
                for part in recipe["parts"]:
                    self.assertTrue(part["name"])
                    self.assertTrue(part["material"])
                    self.assertTrue(part["construction"])

    def test_all_fourteen_materials_render_without_identical_samples(self):
        required = {"bare_steel", "painted_metal", "aluminum", "plastic", "glass", "rubber", "wood",
                    "leather", "fabric", "paper", "ceramic", "organic", "stone", "liquid"}
        self.assertEqual(set(f.MATERIALS), required)
        hashes = set()
        for material in sorted(required):
            with self.subTest(material=material):
                surface = f.PixelSurface(seed=17)
                surface.ellipse((12, 10, 51, 53), material, 3, "round", texture=True)
                self.assertTrue(f.technical_qa(surface.image)["passed"])
                hashes.add(hashlib.sha256(surface.image.tobytes()).hexdigest())
        self.assertEqual(len(hashes), len(required))


class RecipeValidationTests(unittest.TestCase):
    def reject(self, **fields):
        recipe = copy.deepcopy(f.demo_recipes()[0])
        recipe.update(fields)
        with self.assertRaises((ValueError, TypeError, KeyError)):
            f.normalize_recipe(recipe)

    def test_unsafe_logical_ids_rejected(self):
        for value in ("../escape", "/absolute", "item.food/escape", "item.food..escape", "", "item.food.a\\b"):
            with self.subTest(value=value):
                self.reject(id=value)

    def test_unsafe_family_rejected(self):
        for value in ("../escape", "/escape", "food/../../escape", ""):
            with self.subTest(value=value):
                self.reject(family=value)

    def test_unknown_archetype_and_incompatible_design_rejected(self):
        self.reject(archetype="teleporting_sphere")
        self.reject(design="not_a_known_original_recipe")
        self.reject(archetype="hammer", design="canned_beans")

    def test_unknown_materials_rejected(self):
        self.reject(materials=["unobtainium"])
        self.reject(parts=[{"name": "body", "material": "unobtainium", "construction": "folded shell"}])

    def test_malformed_parts_rejected(self):
        for value in ([], "body", [{}], [{"name": "body"}]):
            with self.subTest(value=value):
                self.reject(parts=value)

    def test_unsupported_camera_dimensions_seed_rejected(self):
        self.reject(camera="perspective_front")
        self.reject(size=[256, 256])
        self.reject(size=[64, 48])
        self.reject(seed=-1)
        self.reject(seed="not-an-integer")

    def test_unsupported_views_states_are_not_silently_faked(self):
        self.reject(view="world")
        self.reject(state="empty")
        self.reject(required_views=["inventory_icon", "world"])
        self.reject(required_states=["intact", "broken"])


class AuthoredLayerExtensionTests(unittest.TestCase):
    def recipe(self):
        recipe = copy.deepcopy(f.demo_recipes()[0])
        recipe.update({
            "id": "item.tools.test_authored_file", "family": "tools", "archetype": "layered",
            "design": "test_authored_file", "render_mode": "procedural", "materials": ["bare_steel", "wood"],
            "parts": [{"name": "blade", "material": "bare_steel", "construction": "Original test fixture tapered file"},
                      {"name": "handle", "material": "wood", "construction": "Original test fixture short wooden grip"}],
            "originality_provenance": "Independently authored unit-test coordinates; no external source pixels",
            "layers": [
                {"op": "polygon", "points": [[11, 44], [43, 12], [49, 17], [17, 50]], "material": "bare_steel", "tone": 3},
                {"op": "polygon", "points": [[12, 43], [17, 47], [11, 54], [7, 50]], "material": "wood", "tone": 3, "form": "cylinder"},
                {"op": "line", "points": [[16, 43], [45, 15]], "material": "bare_steel", "tone": 5, "width": 1},
                {"op": "ellipse", "box": [7, 46, 12, 51], "material": "wood", "tone": 2},
            ],
        })
        return recipe

    def test_new_original_object_can_render_without_a_builtin_design(self):
        recipe = f.normalize_recipe(self.recipe())
        image = f.render_icon(recipe)
        self.assertTrue(f.technical_qa(image)["passed"])
        self.assertEqual(image.tobytes(), f.render_icon(recipe).tobytes())
        actual_hash = hashlib.sha256(image.tobytes()).hexdigest()
        self.assertNotIn(actual_hash, {hashlib.sha256(f.render_icon(r).tobytes()).hexdigest() for r in normalized()})

    def test_layers_require_originality_provenance(self):
        recipe = self.recipe()
        recipe.pop("originality_provenance")
        with self.assertRaises(ValueError):
            f.normalize_recipe(recipe)

    def test_layer_count_is_bounded(self):
        for count in (0, 129):
            recipe = self.recipe()
            recipe["layers"] = [copy.deepcopy(recipe["layers"][0]) for _ in range(count)]
            with self.subTest(count=count), self.assertRaises(ValueError):
                f.normalize_recipe(recipe)

    def test_out_of_canvas_layer_coordinates_rejected(self):
        for coordinate in (-1, 64):
            recipe = self.recipe()
            recipe["layers"][0]["points"][0][0] = coordinate
            with self.subTest(coordinate=coordinate), self.assertRaises(ValueError):
                f.normalize_recipe(recipe)

    def test_invalid_layer_geometry_is_rejected_before_render(self):
        malformed = [
            {"op": "polygon", "points": [[10, 10], [20, 20]]},
            {"op": "polygon", "points": [[10, 10, 12], [20, 20, 22], [30, 30, 32]]},
            {"op": "line", "points": [[10, 10]]},
            {"op": "line", "points": [[10, 10], [30, 30]], "width": 0},
            {"op": "ellipse", "box": [20, 20]},
            {"op": "ellipse", "box": [30, 30, 20, 20]},
        ]
        for bad_layer in malformed:
            recipe = self.recipe()
            layer = {"material": "bare_steel", "tone": 3, **bad_layer}
            recipe["layers"] = [layer]
            with self.subTest(layer=bad_layer), self.assertRaises((ValueError, TypeError)):
                f.normalize_recipe(recipe)

    def test_declared_material_override_changes_render_and_unknown_override_fails(self):
        original = self.recipe()
        changed = self.recipe()
        changed["material_overrides"] = {"bare_steel": "painted_metal"}
        self.assertNotEqual(hashlib.sha256(f.render_icon(original).tobytes()).hexdigest(),
                            hashlib.sha256(f.render_icon(changed).tobytes()).hexdigest())
        changed["material_overrides"] = {"bare_steel": "unknown_material"}
        with self.assertRaises(ValueError):
            f.normalize_recipe(changed)


class StandaloneLauncherTests(unittest.TestCase):
    def test_nondemo_mode_reports_missing_recipe_file_actionably(self):
        with tempfile.TemporaryDirectory(prefix="ll-v4-launcher-") as directory:
            with mock.patch.object(f, "DEMO_MODE", False), self.assertRaisesRegex(ValueError, "recipes.jsonl"):
                f.main(["--output", directory])
            self.assertFalse(list(Path(directory).rglob("*.png")))

    def test_nondemo_first_run_reads_custom_recipes_without_consuming_stream(self):
        with tempfile.TemporaryDirectory(prefix="ll-v4-launcher-") as directory:
            path = Path(directory) / "recipes.jsonl"
            path.write_text(json.dumps(f.demo_recipes()[0]) + "\n")
            with mock.patch.object(f, "DEMO_MODE", False):
                result = f.main(["--output", directory, "--limit", "1"])
            self.assertEqual(result["requested"], 1)
            self.assertEqual(result["png_files"], 1)
            self.assertEqual(records(directory)[0]["recipe_id"], f.demo_recipes()[0]["id"])


class EmbeddedOriginalTemplateTests(unittest.TestCase):
    def test_all_twenty_four_embedded_pngs_have_verified_native_masters(self):
        expected = {recipe["design"] for recipe in f.demo_recipes()}
        self.assertEqual(set(f.AUTHORED_TEMPLATES), expected)
        self.assertEqual(set(f.AUTHORED_TEMPLATE_HASHES), expected)
        provenance = json.loads((ROOT / "production/sprite_factory_v4/hybrid_source/provenance.json").read_text())
        self.assertEqual(provenance["source_sha256"], f.AUTHORED_TEMPLATE_SOURCE_SHA256)
        self.assertEqual(digest(ROOT / "production/sprite_factory_v4/hybrid_source/original_generated_sheet.png"),
                         f.AUTHORED_TEMPLATE_SOURCE_SHA256)
        rows = {record["design"]: record for record in provenance["records"]}
        self.assertEqual(set(rows), expected)
        for design in sorted(expected):
            with self.subTest(design=design):
                data = base64.b64decode(f.AUTHORED_TEMPLATES[design], validate=True)
                self.assertEqual(hashlib.sha256(data).hexdigest(), f.AUTHORED_TEMPLATE_HASHES[design])
                self.assertEqual(rows[design]["sha256"], f.AUTHORED_TEMPLATE_HASHES[design])
                self.assertEqual((ROOT / rows[design]["native_png"]).read_bytes(), data)
                with Image.open(io.BytesIO(data)) as image:
                    image.load()
                    self.assertEqual((image.format, image.mode, image.size), ("PNG", "RGBA", (64, 64)))
                    self.assertTrue(f.technical_qa(image)["passed"])

    def test_default_offline_render_matches_each_original_native_master(self):
        for recipe in f.demo_recipes():
            with self.subTest(item=recipe["id"]):
                self.assertEqual(recipe["render_mode"], "authored_template")
                with Image.open(io.BytesIO(base64.b64decode(f.AUTHORED_TEMPLATES[recipe["design"]]))) as master:
                    self.assertEqual(f.render_icon(recipe).tobytes(), master.tobytes())

    def test_authored_pixels_reject_material_relabeling_and_procedural_mode_changes_material(self):
        original = copy.deepcopy(f.demo_recipes()[0])
        original["material_overrides"] = {"bare_steel": "painted_metal"}
        with self.assertRaises(ValueError):
            f.normalize_recipe(original)
        original["render_mode"] = "procedural"
        changed = copy.deepcopy(original)
        changed["material_overrides"] = {"bare_steel": "wood"}
        self.assertNotEqual(hashlib.sha256(f.render_icon(original).tobytes()).hexdigest(),
                            hashlib.sha256(f.render_icon(changed).tobytes()).hexdigest())

    def test_export_provenance_distinguishes_ai_assisted_templates_from_procedural_layers(self):
        with tempfile.TemporaryDirectory(prefix="ll-v4-template-provenance-") as directory:
            f.run_batch(f.demo_recipes()[:1], directory, limit=1)
            row = records(directory)[0]
            self.assertEqual(row["provenance"]["authoring_method"],
                             "original_AI_assisted_native_pixel_template_with_procedural_variant_cleanup")
            self.assertEqual(row["provenance"]["source_artwork"], "embedded_original_native64_template")
            self.assertEqual(row["provenance"]["template_source_sha256"], f.AUTHORED_TEMPLATE_SOURCE_SHA256)
            self.assertIs(row["provenance"]["external_reference_pixels_used"], False)


class TechnicalQATests(unittest.TestCase):
    def fail_image(self, image):
        report = f.technical_qa(image)
        self.assertFalse(report["passed"], report)
        self.assertTrue(report["errors"], report)

    def test_empty_and_nearly_empty_fail(self):
        self.fail_image(Image.new("RGBA", (64, 64)))
        tiny = Image.new("RGBA", (64, 64))
        tiny.putpixel((30, 30), (100, 90, 80, 255))
        self.fail_image(tiny)

    def test_wrong_size_and_missing_alpha_fail(self):
        self.fail_image(Image.new("RGBA", (48, 64), (100, 90, 80, 255)))
        self.fail_image(Image.new("RGB", (64, 64), (100, 90, 80)))

    def test_opaque_background_fails(self):
        self.fail_image(Image.new("RGBA", (64, 64), (100, 90, 80, 255)))

    def test_clipping_fails(self):
        clipped = Image.new("RGBA", (64, 64))
        ImageDraw.Draw(clipped).rectangle((0, 12, 38, 48), fill=(120, 100, 80, 255))
        self.fail_image(clipped)

    def test_excessive_partial_alpha_fails(self):
        halo = Image.new("RGBA", (64, 64))
        ImageDraw.Draw(halo).rectangle((10, 10, 53, 53), fill=(120, 100, 80, 50))
        self.fail_image(halo)

    def test_uncontrolled_high_color_palette_fails(self):
        noisy = Image.new("RGBA", (64, 64))
        for y in range(12, 52):
            for x in range(12, 52):
                noisy.putpixel((x, y), ((x * 4) % 256, (y * 4) % 256, (x + y) % 256, 255))
        self.fail_image(noisy)


class BatchExportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix="ll-v4-contract-")
        cls.directory = Path(cls.temp.name)
        cls.summary = f.run_batch(normalized(), cls.directory, limit=24, chunk_size=7)
        cls.rows = records(cls.directory)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_twenty_four_real_individual_exports_and_accounting(self):
        self.assertEqual(len(self.rows), 24)
        self.assertEqual(self.summary["requested"], 24)
        self.assertEqual(self.summary["png_files"], 24)
        self.assertEqual(self.summary["unique_logical_objects"], 24)
        self.assertEqual(self.summary["technical_qa_passes"], 24)
        self.assertEqual({row["recipe_id"] for row in self.rows}, EXPECTED_IDS)
        self.assertEqual(len({row["relative_path"] for row in self.rows}), 24)
        self.assertEqual(len({row["asset_id"] for row in self.rows}), 24)
        for row in self.rows:
            with self.subTest(item=row["logical_item_id"]):
                path = self.directory / row["relative_path"]
                self.assertTrue(path.is_file())
                self.assertEqual(digest(path), row["sha256"])
                with Image.open(path) as image:
                    image.load()
                    self.assertEqual(image.format, "PNG")
                    self.assertTrue(f.technical_qa(image)["passed"])
                self.assertEqual((row["width"], row["height"]), (64, 64))
                self.assertEqual(row["view"], "inventory_icon")
                self.assertEqual(row["state"], "intact")
                self.assertTrue(row["recipe_fingerprint"])
                self.assertTrue(row["provenance"])
                self.assertEqual(row["generator_version"], f.GENERATOR_VERSION)
                self.assertEqual(row["recipe_version"], f.RECIPE_VERSION)

    def test_no_automatic_visual_founder_engine_or_device_approval(self):
        for key in ("visual_qa_passes", "founder_approvals", "godot_integrations"):
            self.assertEqual(self.summary[key], 0)
        for row in self.rows:
            self.assertEqual(row["qa_status"], "technical_qa_passed")
            self.assertEqual(row["production_status"], "visual_review_required")
            self.assertIs(row["founder_approved"], False)
            self.assertEqual(row["godot_import_status"], "not_tested")
            self.assertEqual(row["device_verification_status"], "not_tested")

    def test_chunked_zip_crc_and_manifest_hashes(self):
        archived = set()
        paths = self.summary["zip_paths"]
        self.assertEqual(len(paths), 4)
        for value in paths:
            archive_path = Path(value)
            if not archive_path.is_absolute():
                archive_path = self.directory / archive_path
            with zipfile.ZipFile(archive_path) as archive:
                self.assertIsNone(archive.testzip())
                names = archive.namelist()
                self.assertEqual(len(names), len(set(names)))
                self.assertTrue(all(not name.startswith("/") and ".." not in Path(name).parts for name in names))
                rows = [json.loads(line) for line in archive.read("manifest.jsonl").splitlines() if line.strip()]
                self.assertLessEqual(len(rows), 7)
                for row in rows:
                    self.assertEqual(hashlib.sha256(archive.read(row["relative_path"])).hexdigest(), row["sha256"])
                    self.assertNotIn(row["asset_id"], archived)
                    archived.add(row["asset_id"])
        self.assertEqual(archived, {row["asset_id"] for row in self.rows})

    def test_successful_writes_leave_no_temporary_exports(self):
        leftovers = [str(path) for path in self.directory.rglob("*")
                     if path.name.endswith((".tmp", ".partial", ".pending")) or ".tmp." in path.name]
        self.assertFalse(leftovers, leftovers)

    def test_review_sheets_exist_at_native_enlarged_and_gameplay_sizes(self):
        paths = [Path(value) for value in self.summary["review_sheet_paths"]]
        self.assertEqual(len(paths), 6)
        for label in ("native_64", "pixel_3x", "dark", "light", "readability_32", "readability_48"):
            matches = [path for path in paths if path.stem.endswith("_" + label)]
            self.assertEqual(len(matches), 1, label)
            with Image.open(matches[0]) as sheet:
                sheet.load()
                self.assertGreater(sheet.width, 0)
                self.assertGreater(sheet.height, 0)


class RecoveryAndIsolationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="ll-v4-recovery-")
        self.directory = Path(self.temp.name)
        self.recipes = normalized()

    def tearDown(self):
        self.temp.cleanup()

    def scaling_receipt_fixture(self, **changes):
        recipe = f.normalize_recipe(self.recipes[0])
        fingerprint = hashlib.sha256(json.dumps(recipe, sort_keys=True, separators=(",", ":"),
                                                ensure_ascii=False, allow_nan=False).encode()).hexdigest()
        receipt = {
            "scope": "LAST_LIGHT_V4_SCALING", "founder": "UNIT_TEST_FIXTURE_NOT_REAL_APPROVAL",
            "approval_evidence": "Temporary unit-test fixture only; no real founder approval",
            "generator_version": f.GENERATOR_VERSION, "max_outputs": 25,
            "approved_recipe_fingerprints": {recipe["id"]: fingerprint},
            **changes,
        }
        path = self.directory / "fixture_approval.json"
        path.write_text(json.dumps(receipt))
        return path

    def test_duplicate_ids_rejected_before_render(self):
        with self.assertRaises(ValueError):
            f.run_batch([self.recipes[0], copy.deepcopy(self.recipes[0])], self.directory)
        self.assertFalse(list(self.directory.rglob("*.png")))

    def test_colliding_paths_rejected_before_render(self):
        other = copy.deepcopy(self.recipes[0])
        other["id"] = "item.other." + self.recipes[0]["id"].split(".")[-1]
        with self.assertRaises(ValueError):
            f.run_batch([self.recipes[0], other], self.directory)
        self.assertFalse(list(self.directory.rglob("*.png")))

    def test_interrupted_run_resumes_without_duplicate_or_lost_exports(self):
        first = f.run_batch(self.recipes[:8], self.directory, limit=8, stop_after=3)
        self.assertTrue(first["interrupted"])
        self.assertEqual(len(records(self.directory)), 3)
        accepted = {row["relative_path"]: digest(self.directory / row["relative_path"]) for row in records(self.directory)}
        final = f.run_batch(self.recipes[:8], self.directory, limit=8)
        self.assertFalse(final["interrupted"])
        self.assertEqual(final["resumed"], 3)
        self.assertEqual(len(records(self.directory)), 8)
        self.assertEqual(len(list((self.directory / "art").rglob("*.png"))), 8)
        for relative_path, expected in accepted.items():
            self.assertEqual(digest(self.directory / relative_path), expected)

    def test_corrupted_export_is_rebuilt_instead_of_resumed(self):
        f.run_batch(self.recipes[:3], self.directory, limit=3)
        row = records(self.directory)[1]
        path = self.directory / row["relative_path"]
        path.write_bytes(b"intentionally corrupted PNG test fixture")
        result = f.run_batch(self.recipes[:3], self.directory, limit=3)
        self.assertEqual(result["resumed"], 2)
        self.assertEqual(result["rebuilt"], 1)
        self.assertEqual(digest(path), row["sha256"])
        with Image.open(path) as image:
            image.load()
            self.assertTrue(f.technical_qa(image)["passed"])

    def test_missing_sidecar_is_repaired_without_regenerating_pixels(self):
        f.run_batch(self.recipes[:1], self.directory, limit=1)
        row = records(self.directory)[0]
        path = self.directory / row["relative_path"]
        sidecar = path.with_name("asset.json")
        sidecar.unlink()
        with mock.patch.object(f, "render_icon", side_effect=AssertionError("Valid pixels must resume")):
            result = f.run_batch(self.recipes[:1], self.directory, limit=1)
        self.assertEqual((result["generated"], result["resumed"], result["metadata_repaired"]), (0, 1, 1))
        self.assertEqual(digest(path), row["sha256"])
        repaired = json.loads(sidecar.read_text())
        self.assertEqual(repaired["asset_id"], row["asset_id"])
        self.assertEqual(repaired["sha256"], row["sha256"])

    def test_corrupted_sidecar_is_preserved_and_repaired_on_resume(self):
        f.run_batch(self.recipes[:1], self.directory, limit=1)
        row = records(self.directory)[0]
        path = self.directory / row["relative_path"]
        sidecar = path.with_name("asset.json")
        original_bytes = b"{ intentionally corrupted metadata test fixture"
        sidecar.write_bytes(original_bytes)
        result = f.run_batch(self.recipes[:1], self.directory, limit=1)
        self.assertEqual((result["generated"], result["resumed"], result["metadata_repaired"]), (0, 1, 1))
        self.assertEqual(digest(path), row["sha256"])
        self.assertEqual(json.loads(sidecar.read_text())["sha256"], row["sha256"])
        archived = list((self.directory / "history").rglob("asset.json.original"))
        self.assertEqual(len(archived), 1)
        self.assertEqual(archived[0].read_bytes(), original_bytes)

    def test_resuming_preserves_matching_independent_review_metadata(self):
        f.run_batch(self.recipes[:1], self.directory, limit=1)
        row = records(self.directory)[0]
        sidecar = (self.directory / row["relative_path"]).with_name("asset.json")
        fixture = json.loads(sidecar.read_text())
        fixture["visual_qa"] = {"status": "fixture_review_only", "reviewer": "unit-test fixture"}
        sidecar.write_text(json.dumps(fixture))
        result = f.run_batch(self.recipes[:1], self.directory, limit=1)
        self.assertEqual(result["resumed"], 1)
        self.assertEqual(json.loads(sidecar.read_text())["visual_qa"], fixture["visual_qa"])

    def test_mismatching_approved_sidecar_is_never_repaired_over(self):
        f.run_batch(self.recipes[:1], self.directory, limit=1)
        row = records(self.directory)[0]
        path = self.directory / row["relative_path"]
        sidecar = path.with_name("asset.json")
        fixture = json.loads(sidecar.read_text())
        fixture["founder_approved"] = True
        fixture["sha256"] = "0" * 64
        fixture["approval_fixture_note"] = "Temporary test fixture, not real approval"
        sidecar.write_text(json.dumps(fixture))
        with self.assertRaises(PermissionError):
            f.run_batch(self.recipes[:1], self.directory, limit=1)
        self.assertEqual(json.loads(sidecar.read_text()), fixture)
        self.assertEqual(digest(path), row["sha256"])

    def test_recipe_change_invalidates_only_changed_candidate(self):
        f.run_batch(self.recipes[:3], self.directory, limit=3)
        before = {row["recipe_id"]: row for row in records(self.directory)}
        changed = copy.deepcopy(self.recipes[:3])
        changed[0]["seed"] += 13
        result = f.run_batch(changed, self.directory, limit=3)
        after = {row["recipe_id"]: row for row in records(self.directory)}
        self.assertEqual(result["resumed"], 2)
        self.assertEqual(result["rebuilt"], 1)
        changed_id = changed[0]["id"]
        self.assertNotEqual(before[changed_id]["recipe_fingerprint"], after[changed_id]["recipe_fingerprint"])
        # Some canonical designs intentionally have no seed-dependent wear.
        # A semantic change must invalidate cached provenance even when those
        # particular canonical pixels remain the same.
        for unchanged in changed[1:]:
            self.assertEqual(before[unchanged["id"]]["sha256"], after[unchanged["id"]]["sha256"])

    def test_generator_version_change_invalidates_cache(self):
        f.run_batch(self.recipes[:1], self.directory, limit=1)
        before = records(self.directory)[0]
        with mock.patch.object(f, "GENERATOR_VERSION", str(f.GENERATOR_VERSION) + "-unit-test"):
            result = f.run_batch(self.recipes[:1], self.directory, limit=1)
        after = records(self.directory)[0]
        self.assertEqual(result["resumed"], 0)
        self.assertEqual(result["rebuilt"], 1)
        self.assertEqual(before["recipe_fingerprint"], after["recipe_fingerprint"])
        self.assertNotEqual(before["render_fingerprint"], after["render_fingerprint"])

    def test_render_failure_is_isolated_and_resumable(self):
        actual_render = f.render_icon
        failed_id = self.recipes[1]["id"]

        def fail_one(recipe, variant=0):
            if recipe["id"] == failed_id:
                raise RuntimeError("deliberate unit-test renderer interruption")
            return actual_render(recipe, variant=variant)

        with mock.patch.object(f, "render_icon", side_effect=fail_one):
            result = f.run_batch(self.recipes[:3], self.directory, limit=3)
        self.assertEqual(result["failed"], 1)
        self.assertEqual(len(records(self.directory)), 2)
        self.assertFalse(any(path.name.endswith(".tmp") for path in self.directory.rglob("*")))
        recovered = f.run_batch(self.recipes[:3], self.directory, limit=3)
        self.assertEqual(recovered["resumed"], 2)
        self.assertEqual(recovered["failed"], 0)
        self.assertEqual(len(records(self.directory)), 3)

    def test_interrupted_png_write_never_publishes_partial_export(self):
        def interrupted_save(image, file, *args, **kwargs):
            file.write(b"partial PNG test fixture")
            raise OSError("deliberate interrupted PNG write")

        with mock.patch.object(Image.Image, "save", new=interrupted_save):
            result = f.run_batch(self.recipes[:1], self.directory, limit=1)
        self.assertEqual(result["failed"], 1)
        self.assertEqual(len(records(self.directory)), 0)
        self.assertFalse(list((self.directory / "art").rglob("*.png")))
        recovered = f.run_batch(self.recipes[:1], self.directory, limit=1)
        self.assertEqual(recovered["failed"], 0)
        self.assertEqual(len(records(self.directory)), 1)
        self.assertFalse(list(self.directory.rglob("*.pending")))

    def test_mass_generation_requires_explicit_synthetic_benchmark_mode(self):
        with self.assertRaises((ValueError, PermissionError)):
            f.run_batch(self.recipes, self.directory, variants=2, limit=25)
        self.assertFalse(list(self.directory.rglob("*.png")))

    def test_cumulative_output_gate_cannot_be_bypassed_with_small_ranges(self):
        f.run_batch(self.recipes, self.directory, limit=24)
        before_manifest = digest(self.directory / "manifest.jsonl")
        # Recipe-major order selects twelve existing canonical assets plus
        # twelve new variant files here. A per-call count of 24 is insufficient.
        with self.assertRaises(PermissionError):
            f.run_batch(self.recipes, self.directory, variants=2, start=24, limit=24)
        self.assertEqual(digest(self.directory / "manifest.jsonl"), before_manifest)
        self.assertEqual(len(list((self.directory / "art").rglob("*.png"))), 24)

    def test_scoped_scaling_receipt_fixture_persists_and_enforces_cumulative_limit(self):
        # This temporary fixture exercises authorization parsing. Every export
        # remains visual_review_required with founder_approved=False.
        receipt = self.scaling_receipt_fixture()
        first = f.run_batch(self.recipes[:1], self.directory, variants=25, limit=25, approval_path=receipt)
        self.assertEqual(first["png_files"], 25)
        self.assertEqual(first["founder_approvals"], 0)
        self.assertTrue((self.directory / "scaling_authorization.json").exists())
        resumed = f.run_batch(self.recipes[:1], self.directory, variants=25, start=24, limit=1)
        self.assertEqual(resumed["resumed"], 1)
        with self.assertRaises(PermissionError):
            f.run_batch(self.recipes[:1], self.directory, variants=26, start=25, limit=1)
        self.assertEqual(len(list((self.directory / "art").rglob("*.png"))), 25)

    def test_scaling_receipt_missing_evidence_wrong_version_or_recipe_is_rejected(self):
        cases = [{"approval_evidence": ""}, {"generator_version": "unrelated_version"},
                 {"max_outputs": 24}, {"approved_recipe_fingerprints": {self.recipes[0]["id"]: "0" * 64}}]
        for index, changes in enumerate(cases):
            receipt = self.scaling_receipt_fixture(**changes)
            with self.subTest(changes=changes), self.assertRaises(PermissionError):
                f.run_batch(self.recipes[:1], self.directory / ("case_%d" % index),
                            variants=25, limit=25, approval_path=receipt)
        self.assertFalse(list(self.directory.rglob("*.png")))

    def test_benchmark_outputs_cannot_be_mixed_with_review_candidates(self):
        f.run_batch(self.recipes[:1], self.directory, limit=1, benchmark=True)
        with self.assertRaises(ValueError):
            f.run_batch(self.recipes[:1], self.directory, limit=1, benchmark=False)

    def test_approved_master_cannot_be_overwritten_by_changed_recipe(self):
        f.run_batch(self.recipes[:1], self.directory, limit=1)
        row = records(self.directory)[0]
        path = self.directory / row["relative_path"]
        sidecar = path.with_name("asset.json")
        fixture = json.loads(sidecar.read_text())
        fixture["founder_approved"] = True
        fixture["approval_fixture_note"] = "Temporary unit-test fixture; not actual founder approval"
        sidecar.write_text(json.dumps(fixture))
        changed = copy.deepcopy(self.recipes[:1])
        changed[0]["seed"] += 29
        with self.assertRaises(PermissionError):
            f.run_batch(changed, self.directory, limit=1)
        self.assertEqual(digest(path), row["sha256"])
        self.assertEqual(json.loads(sidecar.read_text()), fixture)

    def test_unmanaged_existing_image_is_never_silently_overwritten(self):
        recipe = self.recipes[0]
        path = self.directory / "art" / "items" / recipe["family"] / recipe["id"].split(".")[-1] / "icon.png"
        path.parent.mkdir(parents=True)
        path.write_bytes(b"existing external image fixture must stay unchanged")
        before = digest(path)
        with self.assertRaises(FileExistsError):
            f.run_batch(self.recipes[:1], self.directory, limit=1)
        self.assertEqual(digest(path), before)

    def test_identical_physical_objects_are_rejected_outside_candidate_exports(self):
        image = f.render_icon(self.recipes[0])
        with mock.patch.object(f, "render_icon", side_effect=lambda recipe, variant=0: image.copy()):
            result = f.run_batch(self.recipes[:2], self.directory, limit=2, workers=1)
        image.close()
        self.assertEqual(result["failed"], 1)
        self.assertEqual(len(records(self.directory)), 1)
        self.assertEqual(len(list((self.directory / "art").rglob("*.png"))), 1,
                         "Failed duplicate must be retained outside candidate export paths")

    def test_multiple_workers_match_serial_pixels(self):
        serial = self.directory / "serial"
        parallel = self.directory / "parallel"
        f.run_batch(self.recipes[:4], serial, limit=4, workers=1)
        f.run_batch(self.recipes[:4], parallel, limit=4, workers=2)
        self.assertEqual({row["logical_item_id"]: row["sha256"] for row in records(serial)},
                         {row["logical_item_id"]: row["sha256"] for row in records(parallel)})


if __name__ == "__main__":
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--report-json", type=Path)
    options, unittest_arguments = parser.parse_known_args()
    program = unittest.main(argv=[sys.argv[0]] + unittest_arguments, verbosity=2, exit=False)
    if options.report_json:
        result = program.result
        report = {
            "purpose": "Independent engineering checks; no artistic, founder, engine or device approval",
            "executed_utc": datetime.now(timezone.utc).isoformat(),
            "command_argv": [sys.executable] + sys.argv,
            "factory_sha256": hashlib.sha256(FACTORY_SOURCE_BYTES).hexdigest(),
            "generator_version": f.GENERATOR_VERSION,
            "recipe_version": f.RECIPE_VERSION,
            "python_version": platform.python_version(),
            "platform": platform.platform(),
            "tests_run": result.testsRun,
            "failures": [{"test": str(test), "traceback": traceback} for test, traceback in result.failures],
            "errors": [{"test": str(test), "traceback": traceback} for test, traceback in result.errors],
            "skipped": [{"test": str(test), "reason": reason} for test, reason in result.skipped],
            "passed": result.wasSuccessful(),
            "iPhone_CodePad_execution_verified": False,
            "founder_approval_granted": False,
        }
        options.report_json.parent.mkdir(parents=True, exist_ok=True)
        options.report_json.write_text(json.dumps(report, indent=2) + "\n")
    raise SystemExit(not program.result.wasSuccessful())
