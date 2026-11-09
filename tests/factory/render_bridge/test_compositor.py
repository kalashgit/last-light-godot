"""F12 atlas compositor regression suite; run with unittest discovery."""
import hashlib
import tempfile
import unittest
from pathlib import Path
from PIL import Image
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'tools/factory/render_bridge'))
from compose_atlas import compose

class CompositorTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.src=self.root/"src"
        self.src.mkdir()
        self.frames=[]
        for i in range(16):
            name=f"frame_{i}.png"
            Image.new("RGBA",(12,18),(10*i,120,200,255)).save(self.src/name)
            self.frames.append(dict(key=str(i),file=name,width=12,height=18,duration_ms=100,direction=i,clip="idle",source_sha256=hashlib.sha256((self.src/name).read_bytes()).hexdigest()))

    def test_composition_and_determinism(self):
        a=compose({"frames":self.frames},self.src,self.root/"a",64,2)
        b=compose({"frames":list(reversed(self.frames))},self.src,self.root/"b",64,2)
        self.assertEqual(a,b)
        self.assertGreater(a["pages"],1)
        for e in a["frames"]:
            x,y,w,h=e["rect"]
            with Image.open(self.root/"a"/f"atlas_{e['page']:03d}.png") as page:
                self.assertEqual(page.getpixel((x,y)),(10*int(e["key"]),120,200,255))
                self.assertEqual(page.getpixel((x-1,y)),page.getpixel((x,y)))

    def test_reject_tampered_source_before_output(self):
        (self.src/"frame_0.png").write_bytes(b"bad")
        with self.assertRaises(ValueError):
            compose({"frames":self.frames},self.src,self.root/"out",64,2)
        self.assertFalse((self.root/"out").exists())

    def test_reject_traversal(self):
        self.frames[0]["file"]="../escape.png"
        with self.assertRaises(ValueError):
            compose({"frames":self.frames},self.src,self.root/"out",64,2)

    def test_reject_existing_output(self):
        with self.assertRaises(FileExistsError):
            compose({"frames":self.frames},self.src,self.src,64,2)

if __name__=="__main__":
    unittest.main()
