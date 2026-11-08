"""Export three original V3 calibration hero meshes with F11 materials.

These are technical transport candidates, not approved A00 master assets.
"""
import importlib.util
import json
import sys
from pathlib import Path

try:
    import ctypes
except ModuleNotFoundError:
    extensions = Path(f"/usr/lib/python{sys.version_info.major}.{sys.version_info.minor}/lib-dynload")
    if extensions.is_dir():
        sys.path.append(str(extensions))
    import ctypes
site = Path(sys.prefix) / "lib" / f"python{sys.version_info.major}.{sys.version_info.minor}" / "site-packages"
if site.is_dir() and str(site) not in sys.path:
    sys.path.append(str(site))

import bpy

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
output = Path(args[args.index("--output") + 1]) if "--output" in args else Path("build/f11/heroes_glb")
output.mkdir(parents=True, exist_ok=True)
adapter = Path(__file__).with_name("render_hero_materials.py")
spec = importlib.util.spec_from_file_location("f11_render_adapter", adapter)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
v3 = module.v3

records = []
for name in ("refrigerator", "cabinet", "sofa"):
    scene = v3.setup()
    materials = v3.materials(name)
    dims = v3.BUILD[name](materials)
    bpy.context.view_layer.update()
    mesh_objects = [obj for obj in scene.objects if obj.type == "MESH"]
    if not mesh_objects:
        raise RuntimeError("No geometry for " + name)
    unwrapped = []
    for obj in mesh_objects:
        if not obj.data.uv_layers:
            bpy.ops.object.select_all(action="DESELECT")
            obj.select_set(True)
            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.select_all(action="SELECT")
            bpy.ops.uv.smart_project(island_margin=0.015)
            bpy.ops.object.mode_set(mode="OBJECT")
            if not obj.data.uv_layers:
                raise RuntimeError("UV unwrap failed: " + obj.name)
            unwrapped.append(obj.name)
    bpy.ops.object.select_all(action="DESELECT")
    for obj in mesh_objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = mesh_objects[0]
    target = (output / (name + ".glb")).resolve()
    bpy.ops.export_scene.gltf(filepath=str(target), export_format="GLB", use_selection=True,
                              export_materials="EXPORT", export_texcoords=True, export_normals=True)
    if target.stat().st_size < 10000:
        raise RuntimeError("Suspiciously small GLB: " + str(target))
    records.append({"name": name, "file": target.name, "mesh_count": len(mesh_objects),
                    "dimensions_m": list(dims), "bytes": target.stat().st_size,
                    "auto_uv_unwrapped": unwrapped,
                    "uv_note": "Smart-project fallback; physical texel-density and seam review pending",
                    "status": "UNAPPROVED_F11_TECHNICAL_EXPORT"})
    print("LL_F11_HERO_GLB_EXPORT_OK", name, len(mesh_objects), target.stat().st_size, flush=True)
(output / "manifest.json").write_text(json.dumps({"schema": 1, "items": records}, indent=2) + "\n")
