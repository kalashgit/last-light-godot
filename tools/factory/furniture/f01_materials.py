"""Original deterministic F01 PBR shader calibration recipes; F11 review pending."""
import bpy


def wood_grain(name,light=(.39,.24,.12),dark=(.18,.095,.045),axis="Z"):
    mat=bpy.data.materials.new(name)
    mat.use_nodes=True
    nodes=mat.node_tree.nodes;nodes.clear();links=mat.node_tree.links
    output=nodes.new("ShaderNodeOutputMaterial")
    bsdf=nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Roughness"].default_value=.76
    links.new(bsdf.outputs["BSDF"],output.inputs["Surface"])
    coord=nodes.new("ShaderNodeTexCoord")
    wave=nodes.new("ShaderNodeTexWave")
    wave.wave_type="BANDS";wave.bands_direction=axis
    wave.inputs["Scale"].default_value=9
    wave.inputs["Distortion"].default_value=3.7
    wave.inputs["Detail Scale"].default_value=1.6
    wave.inputs["Detail Roughness"].default_value=.58
    links.new(coord.outputs["Generated"],wave.inputs["Vector"])
    ramp=nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position=.18
    ramp.color_ramp.elements[1].position=.80
    ramp.color_ramp.elements[0].color=(*dark,1)
    ramp.color_ramp.elements[1].color=(*light,1)
    links.new(wave.outputs["Color"],ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"],bsdf.inputs["Base Color"])
    bump=nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value=.05
    bump.inputs["Distance"].default_value=.0007
    links.new(wave.outputs["Fac"],bump.inputs["Height"])
    links.new(bump.outputs["Normal"],bsdf.inputs["Normal"])
    return mat


def enamel(name,base=(.49,.55,.53)):
    mat=bpy.data.materials.new(name);mat.use_nodes=True
    nodes=mat.node_tree.nodes;nodes.clear();links=mat.node_tree.links
    out=nodes.new("ShaderNodeOutputMaterial")
    p=nodes.new("ShaderNodeBsdfPrincipled")
    p.inputs["Metallic"].default_value=.20
    p.inputs["Coat Weight"].default_value=.28
    p.inputs["Coat Roughness"].default_value=.28
    links.new(p.outputs["BSDF"],out.inputs["Surface"])
    coords=nodes.new("ShaderNodeTexCoord")
    noise=nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value=12
    noise.inputs["Detail"].default_value=2
    links.new(coords.outputs["Generated"],noise.inputs["Vector"])
    ramp=nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color=(*(v*.84 for v in base),1)
    ramp.color_ramp.elements[1].color=(*(min(1,v*1.06) for v in base),1)
    links.new(noise.outputs["Fac"],ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"],p.inputs["Base Color"])
    range_node=nodes.new("ShaderNodeMapRange")
    range_node.inputs["From Min"].default_value=0
    range_node.inputs["From Max"].default_value=1
    range_node.inputs["To Min"].default_value=.36
    range_node.inputs["To Max"].default_value=.51
    links.new(noise.outputs["Fac"],range_node.inputs["Value"])
    links.new(range_node.outputs["Result"],p.inputs["Roughness"])
    return mat
