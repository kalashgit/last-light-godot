"""Render V3 original hero meshes using Material Factory PBR maps.
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
CONDITION=int(argument("--condition","1"))
if CONDITION not in range(4):
    raise ValueError("--condition must be 0, 1, 2 or 3")
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
    required=["albedo","roughness","metallic","normal","height"]
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
    # Geometry-derived short-range contact occlusion (not random dark flecks).
    # Areas in a joint/under fabric piping get deeper shading, but exposed faces
    # remain relatively fresh at the default condition level.
    if slot in ("cloth","cloth_dark","wood","wood_dark","wood_light"):
        ao=nodes.new("ShaderNodeAmbientOcclusion")
        ao.inputs["Distance"].default_value=.12 if "cloth" in slot else .065
        darken=nodes.new("ShaderNodeMixRGB")
        darken.blend_type="MULTIPLY"
        darken.inputs[0].default_value=.29 if "cloth" in slot else .24
        links.new(base,darken.inputs[1])
        links.new(ao.outputs["Color"],darken.inputs[2])
        base=darken.outputs["Color"]
    links.new(base,p.inputs["Base Color"])
    links.new(image_nodes["roughness"].outputs["Color"],p.inputs["Roughness"])
    links.new(image_nodes["metallic"].outputs["Color"],p.inputs["Metallic"])
    # Generated 3D furniture meshes do not all have UV tangents. Tangent normal
    # maps on non-UV anatomical cushions silently flatten or mis-shade. A height
    # driven geometric bump works on both the procedural upholstery and boards.
    bump=nodes.new("ShaderNodeBump")
    family="fabric" if "FABRIC" in material_id else "wood" if "WOOD" in material_id else "metal"
    bump.inputs["Strength"].default_value={"fabric":.24,"wood":.28,"metal":.17}[family]
    bump.inputs["Distance"].default_value={"fabric":.004,"wood":.008,"metal":.003}[family]
    links.new(image_nodes["height"].outputs["Color"],bump.inputs["Height"])
    links.new(bump.outputs["Normal"],p.inputs["Normal"])
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

def directionally_grained(obj):
    """Orient grown wood grain longitudinally on each object-facing surface.

    Mapping X/Z is for tall front panels; Y/X is for horizontal top boards.
    Without this, image textures were sampled on a very thin Y front face and
    most cabinet grain vanished even though the swatch looked detailed.
    """
    name=obj.name.lower()
    if not obj.data.materials or not any(
        n.type=="TEX_IMAGE" and n.label.startswith("LAST LIGHT LL_MAT_WOOD")
        for n in obj.data.materials[0].node_tree.nodes
    ):
        return obj
    material=obj.data.materials[0].copy()
    material.name=obj.name+" / aligned directional fibres"
    obj.data.materials[0]=material
    nodes=material.node_tree.nodes;links=material.node_tree.links
    tex=next((n for n in nodes if n.type=="TEX_COORD"),None)
    if tex is None: return obj
    split=nodes.new("ShaderNodeSeparateXYZ")
    combine=nodes.new("ShaderNodeCombineXYZ")
    links.new(tex.outputs["Generated"],split.inputs["Vector"])
    if "top board" in name or "front rail" in name:
        # horizontal-length grain, across width/depth
        links.new(split.outputs["Y"],combine.inputs["X"])
        links.new(split.outputs["X"],combine.inputs["Y"])
    else:
        links.new(split.outputs["X"],combine.inputs["X"])
        links.new(split.outputs["Z"],combine.inputs["Y"])
    links.new(split.outputs["Y"],combine.inputs["Z"])
    for node in nodes:
        if node.type=="TEX_IMAGE" and node.label.startswith("LAST LIGHT LL_MAT_WOOD"):
            links.new(combine.outputs["Vector"],node.inputs["Vector"])
    print("LL_ALIGNED_WOOD_GRAIN",obj.name,flush=True)
    return obj

def semantic_surface(obj):
    """Add a restrained location/role-conditioned color variation to one mesh."""
    if obj is None or not obj.data.materials:
        return obj
    name=obj.name.lower()
    rule=next(((zone,tint,amount) for prefix,zone,tint,amount in SEMANTIC_ZONES
               if name.startswith(prefix)),None)
    if not rule:
        return directionally_grained(obj)
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
    # Even pristine/maintained furniture retains physical seams; its patina is
    # much lighter. Severe decay is an explicit environmental override.
    strength.inputs[1].default_value=amount*(.08,.63,1.15,1.65)[CONDITION]
    links.new(modulation.outputs[0],strength.inputs[0])
    mix=nodes.new("ShaderNodeMixRGB");mix.blend_type="MULTIPLY"
    links.new(strength.outputs[0],mix.inputs[0])
    links.new(original,mix.inputs[1])
    mix.inputs[2].default_value=tint
    links.new(mix.outputs["Color"],shader.inputs["Base Color"])
    print("LL_SEMANTIC_MATERIAL",obj.name,zone,flush=True)
    return directionally_grained(obj)

original_cube=v3.cube
def cube_with_semantics(*args,**kwargs):
    return semantic_surface(original_cube(*args,**kwargs))
v3.cube=cube_with_semantics

original_pad=v3.anatomical_pad
def pad_with_semantics(*args,**kwargs):
    return semantic_surface(original_pad(*args,**kwargs))
v3.anatomical_pad=pad_with_semantics

def refrigerator_detail(materials):
    """Embossed fabrication + small grip-specific marks, not universal ruin."""
    dims=v3.fridge_v3(materials)
    # Door division has two independently pressed metal rims, not just a dark
    # line pasted onto a plane. This catches the consistent upper-left light.
    v3.pipe("Upper door folded lower lip", [(-.31,-.420,1.067),(.31,-.420,1.067)],
            .0035,materials["paint"])
    v3.pipe("Lower door rolled upper lip", [(-.31,-.420,1.031),(.31,-.420,1.031)],
            .0035,materials["paint"])
    if CONDITION>=1:
        # Scuff placement comes from human contact: only near the lower grip
        # and the bottom corner. Deliberately avoid full-surface random dirt.
        v3.pipe("Finger contact micro scuff",[(.25,-.413,.642),(.257,-.416,.639),(.271,-.417,.644)],
                .0036,materials["steel"])
    if CONDITION>=2:
        v3.pipe("Low door wear streak", [(.29,-.413,.27),(.293,-.415,.31)],
                .0045,materials["steel"])
    return dims

def cabinet_detail(materials):
    """Joinery and hand-worn hardware at actual furniture contact points."""
    dims=v3.cabinet_v3(materials)
    for x in (-.48,.48):
        # Thin metal hinge plates add legible mounting thickness at 2.5D scale.
        for z in (.27,1.17):
            v3.cube("Inset hinge mounting plate",(x,-.352,z),(.025,.015,.090),
                    materials["steel"],.003)
    # End-grain joints appear as physically recessed seams at the top corners.
    for x in (-.48,.48):
        v3.pipe("Top mortise join line",[(x,-.309,1.48),(x,-.309,1.455)],
                .0035,materials["wood_dark"])
    if CONDITION>=1:
        # Finger-oil darkens the varnish at the pull; no arbitrary face grime.
        for x in (-.088,.088):
            v3.pipe("Pull-side varnish rub",[(x,-.381,.78),(x,-.380,.82)],
                    .003,materials["wood_dark"])
    if CONDITION>=3:
        v3.pipe("Failed lower varnish edge",[(.27,-.377,.27),(.32,-.376,.275)],
                .004,materials["wood_dark"])
    return dims

def sofa_detail(materials):
    """Follow compression and upholstery seams, preserving the V3 soft shape."""
    dims=v3.sofa_v3(materials)
    for x in (-.455,.455):
        # A short compression arc follows the actual rounded pillow top. It is
        # seam geometry, not a generic distressed-texture overlay.
        v3.pipe("Back pillow compressed outer piping",[
            (x-.345,.084,.962),(x-.365,.084,.93),(x-.366,.084,.875)],
            .0045,materials["cloth_dark"])
        v3.pipe("Back pillow opposite seam",[
            (x+.345,.084,.962),(x+.363,.084,.933)],
            .0038,materials["cloth_dark"])
    if CONDITION>=2:
        v3.pipe("Seat corner use crease",[(.71,-.42,.681),(.74,-.38,.682),(.77,-.34,.68)],
                .0038,materials["cloth_dark"])
    return dims

v3.BUILD.update({"refrigerator":refrigerator_detail,
                 "cabinet":cabinet_detail,"sofa":sofa_detail})
print("LL_DETAIL_PROFILE",{"level":CONDITION,"wood":"directional",
                          "occlusion":"contact","surface":"object_specific"},flush=True)

v3.main()
