"""F12 image QA tests."""
import importlib.util
import tempfile
import unittest
from pathlib import Path
from PIL import Image

path=Path(__file__).resolve().parents[3]/"tools/factory/render_bridge/inspect_pngs.py"
spec=importlib.util.spec_from_file_location("f12_inspect",path)
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class PNGQualityTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.frame={"key":"f0","file":"f0.png","width":32,"height":32}
    def write(self,rect=None):
        im=Image.new("RGBA",(32,32),(0,0,0,0))
        if rect:
            for y in range(rect[1],rect[3]):
                for x in range(rect[0],rect[2]):
                    im.putpixel((x,y),(200,100,50,255))
        im.save(self.root/"f0.png")
    def test_valid_centered_alpha(self):
        self.write((8,8,24,24))
        result=mod.inspect({"frames":[self.frame]},self.root)
        self.assertEqual(result["status"],"PNG_QA_PASS")
        self.assertFalse(result["alpha_centroid_warning"])
    def test_empty_sprite_rejected(self):
        self.write()
        result=mod.inspect({"frames":[self.frame]},self.root)
        self.assertEqual(result["findings"][0]["code"],"EMPTY_ALPHA")
    def test_clipped_alpha_rejected(self):
        self.write((0,8,24,24))
        result=mod.inspect({"frames":[self.frame]},self.root)
        self.assertEqual(result["findings"][0]["code"],"ALPHA_TOUCHES_SAFE_MARGIN")
    def test_traversal_rejected(self):
        self.frame["file"]="../other.png"
        with self.assertRaises(ValueError):
            mod.inspect({"frames":[self.frame]},self.root)
    def test_bad_dimensions_rejected(self):
        self.write((8,8,24,24))
        self.frame["width"]=33
        with self.assertRaises(ValueError):
            mod.inspect({"frames":[self.frame]},self.root)

if __name__=="__main__":
    unittest.main()
