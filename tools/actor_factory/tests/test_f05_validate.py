"""Regression tests for F05 fail-closed artifact gate.

Run: python -m unittest discover -s tools/actor_factory/tests -p 'test_f05*.py'
"""
import hashlib
import importlib.util
import json
import struct
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "f05_validate.py"
spec = importlib.util.spec_from_file_location("f05_validate", SCRIPT)
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)


class F05ArtifactGateTests(unittest.TestCase):
    @staticmethod
    def make_glb():
        scene = json.dumps({"asset": {"version": "2.0"}, "skins": [{"joints": [0]}],
                            "animations": [{"channels": [{"sampler": 0, "target": {"node": 0, "path": "rotation"}}], "samplers": [{}]}],
                            "meshes": [{"primitives": [{"attributes": {"POSITION": 0}}]}]}).encode()
        scene += b" " * (-len(scene) % 4)
        return b"glTF" + struct.pack("<II", 2, 20 + len(scene)) + struct.pack("<I4s", len(scene), b"JSON") + scene

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name)
        self.manifest = {
            "status": "CALIBRATION_ONLY",
            "physique": "lean",
            "body_width_factor": 1.0,
            "limb_width_factor": 1.0,
            "canonical_master_id": None,
            "bones": sorted(validator.EXPECTED_BONES),
            "sockets": sorted(validator.EXPECTED_SOCKETS),
            "clips": {name: {"frames": 4, "ms_per_frame": 100,
                     "contract": "PROVISIONAL_W07_APPROVAL_REQUIRED"}
                      for name in validator.EXPECTED_CLIPS},
            "qa": {"glb_export": "PASS"},
            "sha256": {}
        }
        # Minimal integrity fixtures; tests only validate container headers,
        # not Blender geometry or successful Godot imports.
        files = {
            "calibration.png": bytes((137, 80, 78, 71, 13, 10, 26, 10)) + struct.pack(">I", 13) +
                b"IHDR" + struct.pack(">IIBBBBB", 2, 2, 8, 6, 0, 0, 0) + b"0" * 24,
            "f05_noncanonical_calibration.blend": b"BLENDER-v400" + b"0" * 32,
            "f05_noncanonical_calibration.glb": self.make_glb(),
        }
        for name, payload in files.items():
            (self.path / name).write_bytes(payload)
            self.manifest["sha256"][name] = hashlib.sha256(payload).hexdigest()
        self.save()

    def save(self):
        (self.path / "manifest.json").write_text(json.dumps(self.manifest))

    def test_valid_fixture_passes_integrity_only(self):
        self.assertEqual(validator.validate(self.path), [])

    def test_empty_glb_structures_fail(self):
        scene = json.dumps({"asset": {"version": "2.0"}, "skins": [{}],
                            "animations": [{}], "meshes": [{}]}).encode()
        scene += b" " * (-len(scene) % 4)
        payload = b"glTF" + struct.pack("<II", 2, 20 + len(scene)) + struct.pack("<I4s", len(scene), b"JSON") + scene
        (self.path / "f05_noncanonical_calibration.glb").write_bytes(payload)
        self.manifest["sha256"]["f05_noncanonical_calibration.glb"] = hashlib.sha256(payload).hexdigest()
        self.save()
        errors = validator.validate(self.path)
        self.assertIn("GLB missing skinned armature", errors)
        self.assertIn("GLB missing exported animation", errors)
        self.assertIn("GLB missing mesh geometry", errors)

    def test_broad_physique_passes(self):
        self.manifest.update(physique="broad", body_width_factor=1.18, limb_width_factor=1.12)
        self.save()
        self.assertEqual(validator.validate(self.path), [])

    def test_inconsistent_physique_fails(self):
        self.manifest["physique"] = "broad"
        self.save()
        self.assertIn("Physique dimensions do not match calibration contract", validator.validate(self.path))

    def test_missing_glb_fails(self):
        (self.path / "f05_noncanonical_calibration.glb").unlink()
        self.assertTrue(validator.validate(self.path))

    def test_hash_tampering_fails(self):
        (self.path / "calibration.png").write_bytes(b"tampered")
        self.assertTrue(validator.validate(self.path))

    def test_unapproved_canonical_id_fails(self):
        self.manifest["canonical_master_id"] = "UNVERIFIED_TEST"
        self.save()
        self.assertTrue(validator.validate(self.path))

    def test_missing_bone_fails(self):
        self.manifest["bones"].remove("pelvis")
        self.save()
        self.assertTrue(validator.validate(self.path))

    def test_unapproved_timing_fails(self):
        self.manifest["clips"]["walk"]["contract"] = "APPROVED"
        self.save()
        self.assertTrue(validator.validate(self.path))

    def test_glb_missing_skin_fails(self):
        scene = json.dumps({"asset": {"version": "2.0"}, "animations": [{}],
                            "meshes": [{}]}).encode()
        scene += b" " * (-len(scene) % 4)
        payload = b"glTF" + struct.pack("<II", 2, 20 + len(scene)) + struct.pack("<I4s", len(scene), b"JSON") + scene
        (self.path / "f05_noncanonical_calibration.glb").write_bytes(payload)
        self.manifest["sha256"]["f05_noncanonical_calibration.glb"] = hashlib.sha256(payload).hexdigest()
        self.save()
        self.assertIn("GLB missing skinned armature", validator.validate(self.path))

    def test_failed_export_fails(self):
        self.manifest["qa"]["glb_export"] = "FAIL"
        self.save()
        self.assertTrue(validator.validate(self.path))


if __name__ == "__main__":
    unittest.main()
