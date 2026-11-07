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

# Make *mesh-specific* condition masks. A refrigerator door should not acquire
# the same grime pattern as a sofa cushion or an entire wooden cabinet carcass.
# This is original procedural shading, not copied reference-game pixels.
SEMANTIC_ZONES=(
    ("curved ivory enamel carcass", "bottom", (.70,.71,.69,1), .70),
    ("individual pressed convex door", "grip", (.82,.83,.82,1), .46),
    ("dark walnut solid carcass", "bottom", (.67,.66,.63,1), .65),
    ("slightly convex hand-finished inner panel", "grip", (1.21,1.19,1.17,1), .52),
    ("overstuffed curved seat", "top", (.78,.80,.78,1), .48),
    ("padded back cushion", "top", (.83,.84,.81,1), .36),
)

def semantic_surface(obj):
    """Add a restrained location/role-conditioned color variation to one mesh."""
    if obj is None or not obj.data.materials:
        return obj
    name=obj.name.lower()
    rule=next(((zone,tint,amount) for prefix,zone,tint,amount in SEMANTIC_ZONES
               if name.startswith(prefix)),None)
    if not rule:
        return obj
    zone,tint,amount=rule
    # Material copies keep existing image maps while isolating object-specific wear.
    material=obj.data.materials[0].copy()
    material.name=obj.name+" / semantic surface"
    obj.data.materials[0]=material
    nodes=material.node_tree.nodes;links=material.node_tree.links
    shader=next((n for n in nodes if n.type=="BSDF_PRINCIPLED"),None)
    if shader is None or not shader.inputs["Base Color"].is_linked:
        return obj
    original=shader.inputs["Base Color"].links[0].from_socket
    coords=nodes.new("ShaderNodeTexCoord")
    xyz=nodes.new("ShaderNodeSeparateXYZ")
    links.new(coords.outputs["Generated"],xyz.inputs["Vector"])
    region=nodes.new("ShaderNodeMapRange")
    region.clamp=True
    if zone=="bottom":
        region.inputs["From Min"].default_value=.04
        region.inputs["From Max"].default_value=.43
        region.inputs["To Min"].default_value=1.
        region.inputs["To Max"].default_value=0.
        links.new(xyz.outputs["Z"],region.inputs["Value"])
    elif zone=="grip":
        region.inputs["From Min"].default_value=.48
        region.inputs["From Max"].default_value=.95
        links.new(xyz.outputs["X"],region.inputs["Value"])
    else:
        region.inputs["From Min"].default_value=.45
        region.inputs["From Max"].default_value=.94
        links.new(xyz.outputs["Z"],region.inputs["Value"])
    noise=nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value=13.
    noise.inputs["Detail"].default_value=2.
    links.new(coords.outputs["Generated"],noise.inputs["Vector"])
    modulation=nodes.new("ShaderNodeMath");modulation.operation="MULTIPLY"
    links.new(region.outputs["Result"],modulation.inputs[0])
    links.new(noise.outputs["Fac"],modulation.inputs[1])
    strength=nodes.new("ShaderNodeMath");strength.operation="MULTIPLY"
    strength.inputs[1].default_value=amount
    links.new(modulation.outputs[0],strength.inputs[0])
    mix=nodes.new("ShaderNodeMixRGB");mix.blend_type="MULTIPLY"
    links.new(strength.outputs[0],mix.inputs[0])
    links.new(original,mix.inputs[1])
    mix.inputs[2].default_value=tint
    links.new(mix.outputs["Color"],shader.inputs["Base Color"])
    print("LL_SEMANTIC_MATERIAL",obj.name,zone,flush=True)
    return obj

original_cube=v3.cube
def cube_with_semantics(*args,**kwargs):
    return semantic_surface(original_cube(*args,**kwargs))
v3.cube=cube_with_semantics

original_pad=v3.anatomical_pad
def pad_with_semantics(*args,**kwargs):
    return semantic_surface(original_pad(*args,**kwargs))
v3.anatomical_pad=pad_with_semantics

v3.main()
