"""Export portable UV-mapped 1m material swatches; no physical A00 asset IDs.

blender -b --factory-startup --python tools/material_factory/export_glb_swatches.py -- \
  --material-root build/material_factory/materials --output build/material_factory/swatches.glb
"""
import json
import sys
from pathlib import Path

# The hosted Blender/Python image may omit its compiled stdlib extensions.
# Append the same-ABI system directory only if ctypes is unavailable.
try:
    import ctypes
except ModuleNotFoundError:
    system_extensions = Path(f"/usr/lib/python{sys.version_info.major}.{sys.version_info.minor}/lib-dynload")
    if system_extensions.is_dir():
        sys.path.append(str(system_extensions))
    import ctypes

site_packages = Path(sys.prefix) / "lib" / f"python{sys.version_info.major}.{sys.version_info.minor}" / "site-packages"
if site_packages.is_dir() and str(site_packages) not in sys.path:
    sys.path.append(str(site_packages))

import bpy


def arg(flag, fallback):
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    return args[args.index(flag) + 1] if flag in args else fallback


root = Path(arg("--material-root", "build/material_factory/materials")).resolve()
target = Path(arg("--output", "build/material_factory/swatches.glb")).resolve()
recipes = json.loads(Path(__file__).with_name("recipes.json").read_text())
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)


def texture(nodes, links, uv, folder, key, colorspace):
    image = bpy.data.images.load(str(folder / (key + ".png")), check_existing=True)
    image.colorspace_settings.name = colorspace
    node = nodes.new("ShaderNodeTexImage")
    node.image = image
    node.label = key
    links.new(uv.outputs["UV"], node.inputs["Vector"])
    return node


for index, recipe in enumerate(recipes):
    material_id = recipe["id"]
    folder = root / material_id
    for required in ("albedo", "roughness", "metallic", "normal"):
        if not (folder / (required + ".png")).is_file():
            raise FileNotFoundError(folder / (required + ".png"))
    bpy.ops.mesh.primitive_plane_add(size=1, location=(index * 1.3, 0, 0))
    obj = bpy.context.object
    obj.name = "F11_SWATCH_" + material_id
    uv_layer = obj.data.uv_layers.active
    # 1m-wide plane, recipe-defined metres per complete texture repeat.
    repeat = 1.0 / float(recipe["uv_scale_m"])
    for polygon in obj.data.polygons:
        for loop_index in polygon.loop_indices:
            uv_layer.data[loop_index].uv *= repeat
    mat = bpy.data.materials.new(material_id)
    mat.use_nodes = True
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    shader = next(node for node in nodes if node.type == "BSDF_PRINCIPLED")
    uv = nodes.new("ShaderNodeUVMap")
    albedo = texture(nodes, links, uv, folder, "albedo", "sRGB")
    roughness = texture(nodes, links, uv, folder, "roughness", "Non-Color")
    metallic = texture(nodes, links, uv, folder, "metallic", "Non-Color")
    normal_image = texture(nodes, links, uv, folder, "normal", "Non-Color")
    normal_node = nodes.new("ShaderNodeNormalMap")
    links.new(albedo.outputs["Color"], shader.inputs["Base Color"])
    links.new(roughness.outputs["Color"], shader.inputs["Roughness"])
    links.new(metallic.outputs["Color"], shader.inputs["Metallic"])
    links.new(normal_image.outputs["Color"], normal_node.inputs["Color"])
    links.new(normal_node.outputs["Normal"], shader.inputs["Normal"])
    obj.data.materials.append(mat)

target.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.object.select_all(action="SELECT")
bpy.ops.export_scene.gltf(filepath=str(target), export_format="GLB", use_selection=True,
                          export_materials="EXPORT", export_texcoords=True, export_normals=True)
assert target.stat().st_size > 10000
print("LL_F11_GLB_SWATCH_EXPORT_PASS", len(recipes), target, target.stat().st_size, flush=True)
