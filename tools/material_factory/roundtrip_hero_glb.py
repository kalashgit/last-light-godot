"""Reimport exported F11 hero GLBs into a clean Blender scene and audit fidelity.

This checks structural/material transport, not visual Golden approval.
"""
import json
import sys
from pathlib import Path

try:
    import ctypes
except ModuleNotFoundError:
    ext = Path(f"/usr/lib/python{sys.version_info.major}.{sys.version_info.minor}/lib-dynload")
    if ext.is_dir():
        sys.path.append(str(ext))
    import ctypes
site = Path(sys.prefix) / "lib" / f"python{sys.version_info.major}.{sys.version_info.minor}" / "site-packages"
if site.is_dir() and str(site) not in sys.path:
    sys.path.append(str(site))

import bpy

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
root = Path(args[args.index("--input") + 1]) if "--input" in args else Path("build/f11/heroes_glb")
manifest = json.loads((root / "manifest.json").read_text())
results = []
for entry in manifest["items"]:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for material in list(bpy.data.materials):
        bpy.data.materials.remove(material)
    bpy.ops.import_scene.gltf(filepath=str((root / entry["file"]).resolve()))
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    assert len(meshes) == entry["mesh_count"], (entry["name"], len(meshes))
    all_mats = {mat.name: mat for obj in meshes for mat in obj.data.materials if mat}
    textured = []
    for mat in all_mats.values():
        if not mat.use_nodes:
            continue
        images = [node.image for node in mat.node_tree.nodes
                  if node.type == "TEX_IMAGE" and node.image is not None]
        if images:
            assert all(im.size[0] > 0 and im.size[1] > 0 for im in images)
            textured.append(mat.name)
    assert textured, entry["name"]
    assert all(obj.data.uv_layers for obj in meshes if any(
        mat and mat.name in textured for mat in obj.data.materials)), entry["name"]
    results.append({"name": entry["name"], "meshes_reimported": len(meshes),
                    "materials_reimported": len(all_mats), "textured_materials": textured})
    print("LL_F11_HERO_GLB_ROUNDTRIP_PASS", entry["name"], len(meshes), len(textured), flush=True)
(root / "roundtrip-report.json").write_text(json.dumps({"schema": 1, "results": results,
    "status": "STRUCTURAL_AND_MATERIAL_TRANSPORT_ONLY_NOT_VISUAL_APPROVAL"}, indent=2) + "\n")
