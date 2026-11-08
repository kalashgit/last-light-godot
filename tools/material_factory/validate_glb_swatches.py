#!/usr/bin/env python3
"""Inspect GLB structure independently of Blender; technical QA only."""
import json
import struct
import sys
from pathlib import Path


def validate(path):
    data = Path(path).read_bytes()
    assert len(data) > 10000
    magic, version, total = struct.unpack_from("<III", data)
    assert magic == 0x46546C67 and version == 2 and total == len(data)
    length, chunk_type = struct.unpack_from("<II", data, 12)
    assert chunk_type == 0x4E4F534A
    gltf = json.loads(data[20:20 + length])
    recipes = json.loads(Path(__file__).with_name("recipes.json").read_text())
    expected = {r["id"] for r in recipes}
    materials = gltf["materials"]
    assert {m["name"] for m in materials} == expected
    assert len(gltf["meshes"]) == len(expected) == 5
    assert gltf.get("images") and gltf.get("textures")
    assert all(im.get("mimeType") == "image/png" for im in gltf["images"])
    tex_count = len(gltf["textures"])
    for material in materials:
        pbr = material["pbrMetallicRoughness"]
        for entry in (pbr["baseColorTexture"], pbr["metallicRoughnessTexture"], material["normalTexture"]):
            assert 0 <= entry["index"] < tex_count, material["name"]
            assert entry.get("texCoord", 0) == 0
    for mesh in gltf["meshes"]:
        for primitive in mesh["primitives"]:
            assert "TEXCOORD_0" in primitive["attributes"]
            assert "NORMAL" in primitive["attributes"]
            assert primitive["material"] < len(materials)
    print("LL_F11_GLB_STRUCTURE_PASS", len(materials), "materials", len(gltf["images"]), "embedded images")


if __name__ == "__main__":
    validate(sys.argv[1])
