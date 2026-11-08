"""Regression tests for F12 render manifest gates; Python stdlib only."""
from __future__ import annotations

import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest
import zlib

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools" / "f12"))
from validate_render_manifest import RenderValidationError, validate_manifest


def png_chunk(tag, payload):
    return struct.pack(">I", len(payload)) + tag + payload + struct.pack(">I", zlib.crc32(tag + payload) & 0xffffffff)


def rgba_png(path, w=8, h=8):
    # Actual standards-compliant 8-bit RGBA PNG, not a header-only fake.
    scanline = b"\x00" + b"\x44\x88\xcc\xff" * w
    payload = b"\x89PNG\r\n\x1a\n"
    payload += png_chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
    payload += png_chunk(b"IDAT", zlib.compress(scanline * h))
    payload += png_chunk(b"IEND", b"")
    path.write_bytes(payload)


class RenderManifestTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        rgba_png(self.root / "one.png")
        rgba_png(self.root / "atlas.png", 32, 32)
        self.doc = {
            "schema_version": 1,
            "production_status": "CALIBRATION_ONLY",
            "projection": {
                "grid_basis_x_px": [40.0, 20.0],
                "grid_basis_y_px": [-40.0, 20.0],
                "max_axis_error_px": 0.5,
                "calibration_evidence": "measured Godot calibration fixture"
            },
            "direction_count": 4,
            "heading_degrees": [0.0, 90.0, 180.0, 270.0],
            "frames": [
                {"clip": "idle", "direction": d, "frame": 0, "duration_ms": 100,
                 "ground_pivot_px": [4, 7], "png": "one.png"}
                for d in range(4)
            ],
            "atlases": [{"png": "atlas.png", "rects": [[0, 0, 8, 8], [8, 0, 8, 8]]}]
        }

    def test_valid_calibration(self):
        result = validate_manifest(self.doc, self.root)
        self.assertEqual(result["status"], "PASS_METADATA_AND_PNG_HEADERS_ONLY")
        self.assertEqual(result["frame_count"], 4)

    def test_canonical_requires_real_provenance(self):
        self.doc["production_status"] = "A00_VERIFIED_SOURCE"
        with self.assertRaises(RenderValidationError):
            validate_manifest(self.doc, self.root)
        self.doc.update(canonical_master_id="not_a_real_test_id",
                        a00_notion_url="https://example.invalid",
                        catalog_snapshot_sha="test", rights_status="PENDING")
        with self.assertRaises(RenderValidationError):
            validate_manifest(self.doc, self.root)

    def test_calibration_must_not_claim_canonical_id(self):
        self.doc["canonical_master_id"] = "misleading"
        with self.assertRaises(RenderValidationError):
            validate_manifest(self.doc, self.root)

    def test_wrong_projection(self):
        self.doc["projection"]["grid_basis_x_px"] = [30, 18]
        with self.assertRaisesRegex(RenderValidationError, "basis differs"):
            validate_manifest(self.doc, self.root)

    def test_wrong_heading_order(self):
        self.doc["heading_degrees"][1] = 45
        with self.assertRaisesRegex(RenderValidationError, "wrong order"):
            validate_manifest(self.doc, self.root)

    def test_missing_direction(self):
        self.doc["frames"].pop()
        with self.assertRaises(RenderValidationError):
            validate_manifest(self.doc, self.root)

    def test_duplicate_frame(self):
        self.doc["frames"].append(dict(self.doc["frames"][0]))
        with self.assertRaisesRegex(RenderValidationError, "duplicate frame"):
            validate_manifest(self.doc, self.root)

    def test_non_rgba_png(self):
        bad = self.root / "bad.png"
        bad.write_bytes(b"not-png")
        self.doc["frames"][0]["png"] = "bad.png"
        with self.assertRaisesRegex(RenderValidationError, "invalid PNG"):
            validate_manifest(self.doc, self.root)

    def test_file_path_escape(self):
        self.doc["frames"][0]["png"] = "../outside.png"
        with self.assertRaisesRegex(RenderValidationError, "path traversal"):
            validate_manifest(self.doc, self.root)

    def test_atlas_overlap(self):
        self.doc["atlases"][0]["rects"].append([4, 4, 8, 8])
        with self.assertRaisesRegex(RenderValidationError, "overlap"):
            validate_manifest(self.doc, self.root)

    def test_atlas_out_of_bounds(self):
        self.doc["atlases"][0]["rects"].append([30, 0, 8, 8])
        with self.assertRaisesRegex(RenderValidationError, "out of bounds"):
            validate_manifest(self.doc, self.root)

    def test_full_16_heading_coverage(self):
        self.doc["direction_count"] = 16
        self.doc["heading_degrees"] = [i * 22.5 for i in range(16)]
        self.doc["frames"] = [
            {"clip": "idle", "direction": d, "frame": 0, "duration_ms": 100,
             "ground_pivot_px": [4, 7], "png": "one.png"}
            for d in range(16)
        ]
        self.assertEqual(validate_manifest(self.doc, self.root)["direction_count"], 16)


if __name__ == "__main__":
    unittest.main()
