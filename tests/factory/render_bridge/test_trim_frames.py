"""Lossless trim and world-pivot preservation contract."""
import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from PIL import Image

path=Path(__file__).resolve().parents[3]/"tools/factory/render_bridge/trim_frames.py"
spec=importlib.util.spec_from_file_location("f12_trim",path)
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class TrimTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.src=self.root/"src"
        self.src.mkdir()
        im=Image.new("RGBA",(64,64),(0,0,0,0))
        for x in range(11,41):
            for y in range(9,42):
                im.putpixel((x,y),(177,100,45,255))
        self.path=self.src/"heading.png"
        im.save(self.path)
        self.frame={"key":"heading_00","file":"heading.png","width":64,"height":64,
                    "direction":0,"clip":"static","duration_ms":100,"frame_index":0,
                    "world_ground_pivot_px":[32,32],
                    "source_sha256":hashlib.sha256(self.path.read_bytes()).hexdigest()}
    def test_trim_preserves_pivot_and_all_opaque_pixels(self):
        report=mod.trim({"frames":[self.frame]},self.src,self.root/"out",2)
        self.assertGreater(report["pixel_reduction_fraction"],0.5)
        item=json.loads((self.root/"out/manifest.json").read_text())["frames"][0]
        self.assertEqual(item["source_crop_rect"],[9,7,43,44])
        self.assertEqual(item["anchor_local_px"],[23,25])
        with Image.open(self.path) as original,Image.open(self.root/"out/heading.png") as trimmed:
            self.assertEqual(trimmed.size,(34,37))
            self.assertEqual(trimmed.getpixel((2,2)),original.getpixel((11,9)))
            self.assertEqual(trimmed.getpixel((1,1))[3],0)
    def test_hash_tamper_rejected_without_writing(self):
        self.frame["source_sha256"]="a"*64
        with self.assertRaises(ValueError):
            mod.trim({"frames":[self.frame]},self.src,self.root/"out")
        self.assertFalse((self.root/"out").exists())
    def test_missing_pivot_rejected(self):
        del self.frame["world_ground_pivot_px"]
        with self.assertRaises(ValueError):
            mod.trim({"frames":[self.frame]},self.src,self.root/"out")
    def test_existing_output_rejected(self):
        with self.assertRaises(FileExistsError):
            mod.trim({"frames":[self.frame]},self.src,self.src)
if __name__=="__main__":
    unittest.main()
