"""Temporary glTF-safe material representation for F09 calibrated source exports.

Preserves original procedural Blender materials for editing/rendering. This
does NOT replace F11 UV/PBR baking or produce texture maps.
"""
import json
import struct
import bpy

def _simple_preview(source):
    mat=bpy.data.materials.new(source.name+" | GLB flat preview")
    mat.use_nodes=True
    nodes=mat.node_tree.nodes
    nodes.clear()
    out=nodes.new("ShaderNodeOutputMaterial")
    p=nodes.new("ShaderNodeBsdfPrincipled")
    mat.node_tree.links.new(p.outputs["BSDF"],out.inputs["Surface"])
    ramp_nodes=[n for n in source.node_tree.nodes if n.bl_idname=="ShaderNodeValToRGB"]
    if ramp_nodes:
        source_ramp=max(ramp_nodes,key=lambda n:len(n.color_ramp.elements))
        points=sorted(source_ramp.color_ramp.elements,key=lambda el:el.position)
        rgb=tuple(points[len(points)//2].color[:3])
    else:
        rgb=tuple(source.diffuse_color[:3])
    p.inputs["Base Color"].default_value=(*rgb,1)
    bsdf=[n for n in source.node_tree.nodes if n.bl_idname=="ShaderNodeBsdfPrincipled"]
    if bsdf:
        p.inputs["Metallic"].default_value=bsdf[0].inputs["Metallic"].default_value
        p.inputs["Roughness"].default_value=bsdf[0].inputs["Roughness"].default_value
    return mat

def export_with_preview(export_callable, dest, objects):
    originals=[]
    created=[]
    previews={}
    try:
        for ob in objects:
            if ob.type!="MESH":continue
            for slot in ob.material_slots:
                source=slot.material
                if source is None:continue
                if source.name not in previews:
                    previews[source.name]=_simple_preview(source)
                    created.append(previews[source.name])
                originals.append((slot,source))
                slot.material=previews[source.name]
        export_callable(dest,objects)
    finally:
        for slot,source in originals:
            slot.material=source
        for mat in created:
            if mat.users==0:
                bpy.data.materials.remove(mat)

def inspect_glb_preview(path):
    data=path.read_bytes()
    if data[:4]!=b"glTF":raise ValueError("not GLB")
    length,tag=struct.unpack_from("<II",data,12)
    if tag!=0x4e4f534a:raise ValueError("missing GLB JSON chunk")
    document=json.loads(data[20:20+length])
    materials=document.get("materials",[])
    colors=[]
    for material in materials:
        color=material.get("pbrMetallicRoughness",{}).get("baseColorFactor")
        if color is not None: colors.append(tuple(round(float(x),3) for x in color[:3]))
    if len(set(colors))<2:
        raise ValueError("GLB material colors collapsed: "+str(colors))
    return {"material_count":len(materials),"distinct_flat_colors":len(set(colors)),
            "status":"PREVIEW_ONLY_NOT_TEXTURE_BAKED"}
