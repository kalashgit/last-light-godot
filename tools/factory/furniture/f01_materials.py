"""Original deterministic F01 PBR shader calibration recipes; F11 review pending."""
import math
from pathlib import Path
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


def _original_enamel_maps(folder,base,size=256):
    """Create 2 portable PNG channels, no external imagery or random state.

    Fine-frequency wear is intentionally quiet. Large painted panels must read
    as manufactured enamel at 128px rather than noisy stone or fabric.
    """
    folder=Path(folder)
    folder.mkdir(parents=True,exist_ok=True)
    color_pixels=[]
    rough_pixels=[]
    for y in range(size):
        for x in range(size):
            u=x/size;v=y/size
            broad=math.sin(2*math.pi*(u*3.0+v*.35))*.40 + math.cos(2*math.pi*(v*5.0-u*.22))*.24
            fine=math.sin(2*math.pi*(u*41.0+v*15.0))*.13
            edge=math.sin(2*math.pi*(u-v)*2.0)*.12
            wear=broad+fine+edge
            factor=1.0+wear*.025
            color_pixels.extend([max(0,min(1,c*factor)) for c in base]+[1.0])
            rough=.41+wear*.025
            rough_pixels.extend((rough,rough,rough,1.0))
    results={}
    for tag,pixels,is_color in (("basecolor",color_pixels,True),("roughness",rough_pixels,False)):
        image=bpy.data.images.new("F01 original enamel "+tag,width=size,height=size,alpha=True)
        # Changing color space AFTER filling image pixels silently zeroes the
        # RGB buffer in Blender 4.0. Configure it before foreach_set().
        image.colorspace_settings.name="sRGB" if is_color else "Non-Color"
        image.pixels.foreach_set(pixels)
        assert image.pixels[0]>.3, "Enamel pixels were cleared before PNG save"
        image.update()
        image.file_format="PNG"
        image.filepath_raw=str(folder/(f"f01_original_enamel_{tag}.png"))
        image.save()
        image.pack()
        results[tag]=image
    return results


def enamel(name,base=(.49,.55,.53),texture_folder=None):
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
    if texture_folder is not None:
        maps=_original_enamel_maps(texture_folder,base)
        for tag,input_name in (("basecolor","Base Color"),("roughness","Roughness")):
            image_node=nodes.new("ShaderNodeTexImage")
            image_node.label="F01 original baked "+tag
            image_node.image=maps[tag]
            links.new(image_node.outputs["Color"],p.inputs[input_name])
    return mat


def portable_finish(name,key,base,folder,roughness=.55,metallic=0.0,transmission=0.0,size=128):
    """Original image-backed F01 PBR finish for Godot/glTF interchange.

    RGB maps use subtle deterministic correlated wear; roughness is a distinct
    grayscale image. The material remains editable in Blender, not a flat image.
    F11 still owns final shared material IDs and art approval.
    """
    folder=Path(folder)
    folder.mkdir(parents=True,exist_ok=True)
    colors=[];roughs=[]
    for y in range(size):
        for x in range(size):
            u=x/size;v=y/size
            variation=(math.sin(2*math.pi*(u*4.0+v*.47))*.37+
                       math.cos(2*math.pi*(v*7.0-u*.18))*.24+
                       math.sin(2*math.pi*(u*27.0+v*23.0))*.13)
            shade=1+variation*.028
            colors.extend([max(0,min(1,c*shade)) for c in base]+[1.0])
            value=max(.08,min(.98,roughness+variation*.023))
            roughs.extend((value,value,value,1.0))
    maps={}
    for channel,pixels,space in (("basecolor",colors,"sRGB"),("roughness",roughs,"Non-Color")):
        image=bpy.data.images.new(f"F01 {key} {channel}",width=size,height=size,alpha=True)
        image.colorspace_settings.name=space
        image.pixels.foreach_set(pixels)
        assert image.pixels[0]>.03, (key,channel,"blank texture")
        image.update()
        image.filepath_raw=str(folder/f"f01_{key}_{channel}.png")
        image.file_format="PNG";image.save();image.pack()
        maps[channel]=image
    mat=bpy.data.materials.new(name);mat.use_nodes=True
    nodes=mat.node_tree.nodes;nodes.clear();links=mat.node_tree.links
    out=nodes.new("ShaderNodeOutputMaterial");bsdf=nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Metallic"].default_value=metallic
    bsdf.inputs["Roughness"].default_value=roughness
    bsdf.inputs["Transmission Weight"].default_value=transmission
    if transmission:
        bsdf.inputs["IOR"].default_value=1.46
    links.new(bsdf.outputs["BSDF"],out.inputs["Surface"])
    for channel,socket in (("basecolor","Base Color"),("roughness","Roughness")):
        tex=nodes.new("ShaderNodeTexImage");tex.image=maps[channel]
        tex.label=f"Original {key} {channel}"
        links.new(tex.outputs["Color"],bsdf.inputs[socket])
    return mat
