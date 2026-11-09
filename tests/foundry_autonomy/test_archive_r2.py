import io
import importlib.util
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("archive_r2", ROOT / "tools/foundry_autonomy/archive_r2.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
BUCKET = "last-light-foundry-sources-20261109"


class Missing(Exception):
    response = {"Error": {"Code": "404"}}


class Store:
    def __init__(self):
        self.data = {}
        self.put_count = 0

    def head_object(self, Bucket, Key):
        if (Bucket, Key) not in self.data:
            raise Missing()
        body, metadata = self.data[Bucket, Key]
        return {"ContentLength": len(body), "Metadata": metadata}

    def put_object(self, Bucket, Key, Body, Metadata, ContentType, IfNoneMatch):
        assert ContentType == "application/zip" and IfNoneMatch == "*"
        if (Bucket, Key) in self.data:
            raise RuntimeError("Overwrite attempted")
        self.put_count += 1
        self.data[Bucket, Key] = (Body.read(), Metadata)

    def get_object(self, Bucket, Key):
        return {"Body": io.BytesIO(self.data[Bucket, Key][0])}


class ArchiveTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "candidate.zip"
        with zipfile.ZipFile(self.path, "w") as z:
            z.writestr("assets/fridge/model.blend", b"BLENDER" + b"0" * 10)
            z.writestr("assets/fridge/model.glb", b"glTF" + b"0" * 10)
        self.store = Store()

    def tearDown(self):
        self.tmp.cleanup()

    def test_round_trip_and_idempotency(self):
        r = mod.archive_to_r2(self.store, self.path, BUCKET,
                              "foundry-created-42654909455", "created-candidates")
        self.assertTrue(r["remote_sha256_verified"])
        self.assertFalse(r["golden_approved"])
        self.assertEqual(r["blend_files"], 1)
        mod.archive_to_r2(self.store, self.path, BUCKET,
                          "foundry-created-42654909455", "created-candidates")
        self.assertEqual(self.store.put_count, 1)

    def test_no_unrelated_bucket_or_arbitrary_release(self):
        for bucket in ("k00-recovery-integration-20261109", "other", "../bad"):
            with self.subTest(bucket=bucket), self.assertRaises(ValueError):
                mod.archive_to_r2(self.store, self.path, bucket,
                                  "foundry-created-1", "created-candidates")
        with self.assertRaises(ValueError):
            mod.archive_to_r2(self.store, self.path, BUCKET,
                              "random-release", "created-candidates")

    def test_rejects_false_legacy_360_claim(self):
        with self.assertRaises(ValueError):
            mod.archive_to_r2(self.store, self.path, BUCKET,
                              "foundry-360-source-v1", "legacy-360")

    def test_readback_detects_object_corruption(self):
        class Corrupt(Store):
            def get_object(self, Bucket, Key):
                return {"Body": io.BytesIO(b"corrupt")}
        with self.assertRaisesRegex(ValueError, "readback"):
            mod.archive_to_r2(Corrupt(), self.path, BUCKET,
                              "foundry-created-123", "created-candidates")

    def test_rejects_path_traversal_and_duplicates(self):
        with zipfile.ZipFile(self.path, "w") as z:
            z.writestr("../model.blend", "bad")
            z.writestr("model.glb", "bad")
        with self.assertRaises(ValueError):
            mod.inspect_zip(self.path, "created-candidates")

    def test_rejects_fake_editable_sources_even_with_valid_zip_crc(self):
        for bad_member in ("model.blend", "model.glb"):
            with self.subTest(bad_member=bad_member):
                with zipfile.ZipFile(self.path, "w") as z:
                    z.writestr("assets/model.blend", b"NOTBLENDER" if bad_member.endswith(".blend") else b"BLENDER" + b"0" * 10)
                    z.writestr("assets/model.glb", b"NOTGLB" if bad_member.endswith(".glb") else b"glTF" + b"0" * 10)
                with self.assertRaisesRegex(ValueError, "signature"):
                    mod.inspect_zip(self.path, "created-candidates")

    def test_accepts_gzip_compressed_blend_source(self):
        import gzip
        with zipfile.ZipFile(self.path, "w") as z:
            z.writestr("assets/model.blend", gzip.compress(b"BLENDER" + b"0" * 10))
            z.writestr("assets/model.glb", b"glTF" + b"0" * 10)
        self.assertEqual(mod.inspect_zip(self.path, "created-candidates")["blend_files"], 1)


if __name__ == "__main__":
    unittest.main()
