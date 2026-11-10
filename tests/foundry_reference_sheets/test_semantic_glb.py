import json
import struct
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools'))
from verify_semantic_glb import digest_glb


def synthetic_glb(height:float,mesh_bytes=b'ABCD')->bytes:
    meta={'asset':{'version':'2.0'},'meshes':[{'name':'original_mesh','extras':{'height':height}}],
          'buffers':[{'byteLength':len(mesh_bytes)}]}
    j=json.dumps(meta,separators=(',',':')).encode()
    j+=b' '*((-len(j))%4)
    b=mesh_bytes+b'\x00'*((-len(mesh_bytes))%4)
    total=12+8+len(j)+8+len(b)
    return struct.pack('<4sII',b'glTF',2,total)+struct.pack('<I4s',len(j),b'JSON')+j+struct.pack('<I4s',len(b),b'BIN\x00')+b


class PortableGLBPinTests(unittest.TestCase):
    def test_float_spelling_noise_is_ignored_but_not_mesh_content(self):
        with tempfile.TemporaryDirectory() as d:
            a,b,c=(Path(d)/str(i) for i in range(3))
            a.write_bytes(synthetic_glb(.21931712199461312))
            b.write_bytes(synthetic_glb(.2193171219946131))
            c.write_bytes(synthetic_glb(.2193171219946131,b'XBCC'))
            self.assertNotEqual(a.read_bytes(),b.read_bytes())
            self.assertEqual(digest_glb(a),digest_glb(b))
            self.assertNotEqual(digest_glb(b),digest_glb(c))

    def test_invalid_glb_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'bad.glb';p.write_bytes(b'NOT_A_GLTF')
            with self.assertRaises(ValueError):digest_glb(p)


if __name__=='__main__':unittest.main()
