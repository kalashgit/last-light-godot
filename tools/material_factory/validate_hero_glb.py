#!/usr/bin/env python3
"""Verify export texture/UV coverage of F11 refrigerator, cabinet, sofa heroes."""
import json
import struct
import sys
from pathlib import Path


EXPECTED = {
    "refrigerator": ("aged enamel", "worn iron"),
    "cabinet": ("aged grain", "rubbed edges", "stained endgrain"),
    "sofa": ("faded moss upholstery", "stained endgrain"),
}


def validate(root):
    manifest = json.loads((root / "manifest.json").read_text())
    assert {item["name"] for item in manifest["items"]} == set(EXPECTED)
    for entry in manifest["items"]:
        name = entry["name"]
        payload = (root / entry["file"]).read_bytes()
        magic, version, total = struct.unpack_from("<III", payload)
        assert (magic, version, total) == (0x46546C67, 2, len(payload))
        length, kind = struct.unpack_from("<II", payload, 12)
        assert kind == 0x4E4F534A
        gltf = json.loads(payload[20:20 + length])
        mats = gltf["materials"]
        assert len(gltf["meshes"]) == entry["mesh_count"]
        for required in EXPECTED[name]:
            matches = [mat for mat in mats if required in mat["name"]]
            assert len(matches) == 1, (name, required)
            mat = matches[0]
            pbr = mat["pbrMetallicRoughness"]
            assert "baseColorTexture" in pbr and "metallicRoughnessTexture" in pbr
            assert "normalTexture" in mat
        uv_covered = 0
        for mesh in gltf["meshes"]:
            for primitive in mesh["primitives"]:
                material = mats[primitive.get("material", 0)]
                textured = "baseColorTexture" in material.get("pbrMetallicRoughness", {})
                if textured:
                    assert "TEXCOORD_0" in primitive["attributes"], (name, mesh.get("name"))
                    uv_covered += 1
        assert uv_covered > 0
        print("LL_F11_HERO_GLB_QA_PASS", name, uv_covered, "textured primitives")


if __name__ == "__main__":
    validate(Path(sys.argv[1]))
