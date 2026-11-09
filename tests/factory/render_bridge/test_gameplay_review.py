"""F12 native-scale contact sheet regressions."""
import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from PIL import Image

module=Path(__file__).resolve().parents[3]/"tools/factory/render_bridge/gameplay_review.py"
spec=importlib.util.spec_from_file_location("f12_gameplay_review",module)
review=importlib.util.module_from_spec(spec)
spec.loader.exec_module(review)

class NativeGameplaySheetTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.source=self.root/"source"
        self.source.mkdir()
        self.frames=[]
        for i in range(16):
            image=Image.new("RGBA",(32,32),(0,0,0,0))
            for x in range(10,21):
                for y in range(8,20):
                    image.putpixel((x,y),(190,125+i,75,255))
            name="heading_%02d.png"%i
            path=self.source/name
            image.save(path)
            self.frames.append({"key":"heading_%02d"%i,"file":name,"width":32,
                                "height":32,"direction":i,
                                "world_ground_pivot_px":[16,16],
                                "source_sha256":hashlib.sha256(path.read_bytes()).hexdigest()})
        self.manifest=self.root/"manifest.json"
    def write(self):
        self.manifest.write_text(json.dumps({"frames":self.frames}))
    def test_real_pixels_and_anchor(self):
        self.write()
        result=review.build(self.manifest,self.source,self.root/"out")
        self.assertEqual(result["headings"],16)
        self.assertEqual(result["max_world_pivot_drift_px"],0)
        with Image.open(self.root/"out/f10_gameplay_16_headings_1x.png") as sheet:
            self.assertEqual(sheet.size,(1024,768))
    def test_reject_tampered_frame(self):
        self.write()
        (self.source/"heading_00.png").write_bytes(b"modified")
        with self.assertRaises(ValueError):
            review.build(self.manifest,self.source,self.root/"out")
    def test_reject_missing_world_pivot(self):
        del self.frames[4]["world_ground_pivot_px"]
        self.write()
        with self.assertRaises(ValueError):
            review.build(self.manifest,self.source,self.root/"out")
    def test_reject_incomplete_headings(self):
        self.frames.pop()
        self.write()
        with self.assertRaises(ValueError):
            review.build(self.manifest,self.source,self.root/"out")

if __name__=="__main__":
    unittest.main()
