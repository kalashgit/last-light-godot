"""Render V3 original hero meshes using Material Factory v1 PBR maps.
Designed for Blender background CPU; does not mutate the original V3 renderer.
No Project Zomboid textures or proprietary external material inputs used.
Usage:
  blender -b -t 2 --factory-startup --python tools/material_factory/render_hero_materials.py -- --material-root build/material_factory/materials --output build/material_factory/hero_raw
"""
import sys, importlib.util
from pathlib import Path
import bpy

ARGS=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
def argument(key,default):
    return ARGS[ARGS.index(key)+1] if key in ARGS else default

ROOT=Path(argument("--material-root","build/material_factory/materials")).resolve()
SCRIPT=Path(__file__).resolve().parents[1]/"blender_factory"/"render_v3_recovery.py"
spec=importlib.util.spec_from_file_location("last_light_v3_original_renderer",str(SCRIPT))
v3=importlib.util.module_from_spec(spec)
spec.loader.exec_module(v3)

BIND={
    "refrigerator":{"paint":"LL_MAT_ENAMEL_AGED_001", "steel":"LL_MAT_IRON_OXID_001"},
    "cabinet":{"wood":"LL_MAT_WOOD_WORN_001","wood_light":"LL_MAT_WOOD_WORN_001",
               "wood_dark":"LL_MAT_WOOD_WORN_001"},
    "sofa":{"cloth":"LL_MAT_FABRIC_MOSS_001","cloth_dark":"LL_MAT_FABRIC_MOSS_001",
            "wood_dark":"LL_MAT_WOOD_WORN_001"}
}

def bind_pbr(material, material_id, slot):
    folder=ROOT/material_id
    required=["albedo","roughness","metallic","normal"]
    for key in required:
        if not (folder/(key+".png")).is_file():
            raise FileNotFoundError(str(folder/(key+".png")))
    nodes=material.node_tree.nodes
    links=material.node_tree.links
    p=next((node for node in nodes if node.type=="BSDF_PRINCIPLED"),None)
    if p is None:raise ValueError("Missing Principled shader in "+material.name)
    coord=nodes.new("ShaderNodeTexCoord")
    # Object-generated positions carry semantic board-to-board grain direction.
    # Exact UV scale and orientation still needs 3D inspection and actor-relative calibration.
    mapping=nodes.new("ShaderNodeVectorMath");mapping.operation="MULTIPLY"
    mapping.inputs[1].default_value=(1.0,1.0,1.0)
    links.new(coord.outputs["Generated"],mapping.inputs[0])
    image_nodes={}
    for key in required:
        tex=nodes.new("ShaderNodeTexImage")
        tex.label="LAST LIGHT "+material_id+" / "+key
        tex.image=bpy.data.images.load(str(folder/(key+".png")),check_existing=True)
        tex.image.colorspace_settings.name="sRGB" if key=="albedo" else "Non-Color"
        tex.extension="REPEAT"
        tex.interpolation="Linear"
        links.new(mapping.outputs["Vector"],tex.inputs["Vector"])
        image_nodes[key]=tex
    base=image_nodes["albedo"].outputs["Color"]
    # Keep underlying tonal variations for separately stained wooden panels and seams.
    tint={"wood_dark":(.55,.53,.52,1),"wood_light":(1.20,1.15,1.09,1),
          "cloth_dark":(.64,.65,.65,1)}.get(slot)
    if tint:
        mix=nodes.new("ShaderNodeMixRGB");mix.blend_type="MULTIPLY"
        mix.inputs[0].default_value=1
        mix.inputs[2].default_value=tint
        links.new(base,mix.inputs[1])
        base=mix.outputs["Color"]
    links.new(base,p.inputs["Base Color"])
    links.new(image_nodes["roughness"].outputs["Color"],p.inputs["Roughness"])
    links.new(image_nodes["metallic"].outputs["Color"],p.inputs["Metallic"])
    normal=nodes.new("ShaderNodeNormalMap")
    normal.space="TANGENT"
    normal.inputs["Strength"].default_value=.38 if material_id.endswith("FABRIC_MOSS_001") else .56
    links.new(image_nodes["normal"].outputs["Color"],normal.inputs["Color"])
    links.new(normal.outputs["Normal"],p.inputs["Normal"])
    print("LL_MATERIAL_BIND_OK",material.name,material_id,slot,flush=True)

original_fidelity=v3.material_fidelity_v3
def material_fidelity(key,m):
    original_fidelity(key,m)
    for slot,material_id in BIND.get(key,{}).items():
        bind_pbr(m[slot],material_id,slot)
v3.material_fidelity_v3=material_fidelity
v3.main()
