"""Workspace provenance and isolation tests; synthetic receipt ≠ real Blender QA."""
from __future__ import annotations

import hashlib
import json
import struct
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from tools.recipe_architect.mesh_workspace import (
    import_batch_rooms, plan_reference_rooms,
)
from tools.recipe_architect.serve_workspace import handler_for


class MeshWorkspaceTests(unittest.TestCase):
    def test_100_isolated_source_rooms_without_building_models(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / "workspace"
            receipt = plan_reference_rooms(start=1, count=100, out=root)
            self.assertEqual(receipt["room_count"], 100)
            self.assertEqual(receipt["production_build_cap_unchanged"], 3)
            self.assertEqual(len(list((root / "rooms").glob("*/room.json"))), 100)
            self.assertEqual(len({r["room_id"] for r in receipt["rooms"]}), 100)
            self.assertFalse(any(r["technical_pass"] or r["golden_approved"] for r in receipt["rooms"]))
            self.assertFalse(any((root / "rooms").rglob("*.png")))
            self.assertFalse(any((root / "rooms").rglob("*.glb")))
            self.assertEqual(json.loads((root / "manifest.json").read_text()), receipt)

    def test_gap_and_scope_do_not_fabricate_unpictured_sheet_slots(self):
        with tempfile.TemporaryDirectory() as d:
            receipt = plan_reference_rooms(start=185, count=40, out=Path(d) / "first")
            indices = [r["reference_position_not_canonical_id"] for r in receipt["rooms"]]
            self.assertEqual(indices[:6], [185, 186, 187, 188, 189, 190])
            self.assertEqual(indices[6], 201)
            with self.assertRaisesRegex(ValueError, "pictured"):
                plan_reference_rooms(start=380, count=100, out=Path(d) / "second")
            with self.assertRaises(ValueError):
                plan_reference_rooms(start=1, count=101, out=Path(d) / "third")

    def test_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / "workspace"
            plan_reference_rooms(start=1, count=10, out=root)
            with self.assertRaises(FileExistsError):
                plan_reference_rooms(start=1, count=10, out=root)

    @staticmethod
    def synthetic_receipt(folder: Path) -> Path:
        """Fake bytes test only importer integrity logic, NOT Blender output."""
        source = folder / "candidates" / "battery"
        source.mkdir(parents=True)
        assets = {}
        for key, name in {"glb": "candidate.glb", "blend": "editable_candidate.blend",
                          "contact_sheet": "contact.png", "inventory": "inventory.png",
                          "atlas": "atlas.png", "log": "blender.log"}.items():
            path = source / name
            if path.suffix == ".png":
                Image.new("RGBA", (64, 64), (70, 80, 90, 255)).save(path)
            elif key == "glb":
                # Syntactically structured dummy GLB for importer tests only.
                # This isn't meaningful geometry or an actual Blender result.
                gltf = {"asset": {"version": "2.0"},
                        "nodes": [{"mesh": n} for n in range(3)],
                        "meshes": [{"primitives": [{"attributes": {"POSITION": 0}}]} for _ in range(3)]}
                json_bytes = json.dumps(gltf).encode()
                json_bytes += b" " * (-len(json_bytes) % 4)
                path.write_bytes(b"glTF" + struct.pack("<II", 2, 20 + len(json_bytes)) +
                                 struct.pack("<I4s", len(json_bytes), b"JSON") + json_bytes)
            else:
                path.write_bytes(("synthetic " + key).encode())
            assets[key] = str(path.relative_to(folder))
        for angle in range(16):
            Image.new("RGBA", (128, 128), (angle, 80, 90, 255)).save(source / f"heading_{angle:02d}.png")
        receipt = {
            "schema": "last-light.recipe-architect-batch.v1",
            "founder_golden_approved": False, "canonical_admission": False,
            "reference_vs_render_comparison_this_run": False,
            "candidates": [{"preset": "battery", "source_reference_id": "source_614",
                "candidate_id": "pilot_battery", "source_sha256": "a" * 64,
                "asset_family": "electrical_battery", "state": "TECHNICAL_PASS_VISUAL_PENDING",
                "founder_review": "NOT_GOLDEN", "golden_approved": False,
                "distinct_headings": 16, "meshes": 24, "triangles_estimate": 22992,
                "glb_sha256": hashlib.sha256((source / "candidate.glb").read_bytes()).hexdigest(),
                "blend_sha256": hashlib.sha256((source / "editable_candidate.blend").read_bytes()).hexdigest(),
                "artifacts": assets}],
        }
        path = folder / "batch_report.json"
        path.write_text(json.dumps(receipt))
        return path

    def test_import_copies_verifiable_isolated_candidate_outputs(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            report = self.synthetic_receipt(root)
            vault = root / "vault"
            manifest = import_batch_rooms(report_path=report, out=vault)
            room = manifest["rooms"][0]
            self.assertTrue(room["technical_pass"])
            self.assertFalse(room["golden_approved"])
            self.assertFalse(room["reference_vs_render_measured_this_run"])
            self.assertEqual(len(room["headings"]), 16)
            self.assertTrue((vault / room["files"]["glb"]).read_bytes().startswith(b"glTF"))
            with Image.open(vault / room["headings"][15]) as frame:
                self.assertEqual(frame.size, (128, 128))
                self.assertEqual(frame.getpixel((0, 0))[0], 15)
            self.assertFalse((vault / "rooms" / room["room_id"] / "source.png").exists())

    def test_forged_approval_or_hash_fails_without_writing(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            path = self.synthetic_receipt(root)
            receipt = json.loads(path.read_text())
            receipt["candidates"][0]["golden_approved"] = True
            path.write_text(json.dumps(receipt))
            with self.assertRaisesRegex(ValueError, "not-Golden"):
                import_batch_rooms(report_path=path, out=root / "vault")
            self.assertFalse((root / "vault").exists())
            receipt["candidates"][0]["golden_approved"] = False
            receipt["candidates"][0]["glb_sha256"] = "0" * 64
            path.write_text(json.dumps(receipt))
            with self.assertRaisesRegex(ValueError, "GLB"):
                import_batch_rooms(report_path=path, out=root / "vault")
            self.assertFalse((root / "vault").exists())

    def test_traversal_and_outside_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            path = self.synthetic_receipt(root)
            receipt = json.loads(path.read_text())
            receipt["candidates"][0]["artifacts"]["glb"] = "../../outside.glb"
            path.write_text(json.dumps(receipt))
            with self.assertRaisesRegex(ValueError, "escaped"):
                import_batch_rooms(report_path=path, out=root / "vault")
            self.assertFalse((root / "vault").exists())

    def test_server_never_exposes_arbitrary_filenames(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            server = handler_for(root)
            obj = object.__new__(server)
            self.assertEqual(Path(obj.translate_path("/manifest.json")), root / "manifest.json")
            self.assertEqual(Path(obj.translate_path("/rooms/../../../etc/passwd")), root / "__not_served__")
            self.assertEqual(Path(obj.translate_path("/AGENTS.md")), root / "__not_served__")


if __name__ == "__main__":
    unittest.main()
