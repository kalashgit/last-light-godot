"""F02 candidate portable PBR channel integrity, pending F11 signoff."""
import hashlib
from pathlib import Path
import sys
import tempfile
import unittest
from PIL import Image
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tools/factory/structures"))
from textures import PALETTE, make_maps

class F02CandidatePBRTests(unittest.TestCase):
    def test_all_materials_emit_portable_channels_and_hashes(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            generated = make_maps(root, 32)
            self.assertEqual(set(generated), set(PALETTE))
            for name, record in generated.items():
                self.assertEqual(set(record["channels"]),
                                 {"basecolor", "roughness", "metallic", "normal"})
                self.assertEqual(record["normal_convention"], "OPENGL_POSITIVE_Y")
                for channel, properties in record["channels"].items():
                    path = root / properties["file"]
                    self.assertTrue(path.is_file())
                    self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),
                                     properties["sha256"])
                    with Image.open(path) as img:
                        self.assertEqual(img.size, (32, 32))
                        self.assertEqual(img.mode, "RGB" if channel in ("basecolor", "normal") else "L")
                self.assertEqual(record["channels"]["basecolor"]["color_space"], "sRGB")
                self.assertTrue(all(record["channels"][n]["color_space"] == "Non-Color"
                                    for n in ("roughness", "metallic", "normal")))

if __name__ == "__main__":
    unittest.main()
