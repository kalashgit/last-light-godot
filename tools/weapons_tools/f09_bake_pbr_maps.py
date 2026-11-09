"""Isolated F09/F11-compatible candidate PBR texture bake from real Blender shaders.

Bakes per-mesh UV atlas roughness, metallic, tangent-space normal, and packs ORM
in glTF channel order. No F11 approval or irreversible master-material mutation.
"""
import bpy
import numpy as np

def _scalar_bake(mesh, directory, label, source_name):
    scene=bpy.context.scene
    image=bpy.data.images.new(label,width=512,height=512,alpha=True)
    image.colorspace_settings.name="Non-Color"
    image.generated_color=(0.0,0.0,0.0,1.0)
    saved=[]
    try:
        for material in mesh.data.materials:
            if material is None:continue
            nodes=material.node_tree.nodes
            links=material.node_tree.links
            out=next(node for node in nodes if node.bl_idname=="ShaderNodeOutputMaterial")
            bsdf=next(node for node in nodes if node.bl_idname=="ShaderNodeBsdfPrincipled")
            previous=[link.from_socket for link in out.inputs["Surface"].links]
            assert len(previous)==1,"material lacks surface"
            source=bsdf.inputs[source_name]
            source_link=source.links[0].from_socket if source.links else None
            emission=nodes.new("ShaderNodeEmission")
            if source_link is not None:
                links.new(source_link,emission.inputs["Color"])
            else:
                v=float(source.default_value)
                emission.inputs["Color"].default_value=(v,v,v,1.0)
            links.new(emission.outputs["Emission"],out.inputs["Surface"])
            target=nodes.new("ShaderNodeTexImage")
            target.name="F09_TMP_BAKE_"+source_name
            target.image=image
            nodes.active=target
            saved.append((material,out,previous[0],emission,target))
        bpy.ops.object.bake(type="EMIT")
        image.filepath_raw=str((directory/(label+".png")).resolve())
        image.file_format="PNG"
        image.save()
        assert (directory/(label+".png")).stat().st_size>3000
    finally:
        for material,out,previous,emission,target in saved:
            links=material.node_tree.links
            links.new(previous,out.inputs["Surface"])
            material.node_tree.nodes.remove(emission)
            material.node_tree.nodes.remove(target)
    return image

def _normal_bake(mesh, directory):
    image=bpy.data.images.new("normal_tangent_baked",width=512,height=512,alpha=False)
    image.colorspace_settings.name="Non-Color"
    saved=[]
    try:
        for material in mesh.data.materials:
            if not material:continue
            nodes=material.node_tree.nodes
            tex=nodes.new("ShaderNodeTexImage")
            tex.name="F09_TEMP_NORMAL_BAKE"
            tex.image=image
            nodes.active=tex
            saved.append((material,tex))
        bpy.context.scene.render.bake.normal_space="TANGENT"
        bpy.ops.object.bake(type="NORMAL")
        image.filepath_raw=str((directory/"normal_tangent_baked.png").resolve())
        image.file_format="PNG"
        image.save()
        assert (directory/"normal_tangent_baked.png").stat().st_size>3000
    finally:
        for material,target in saved:
            material.node_tree.nodes.remove(target)
    return image

def _ambient_occlusion_bake(mesh,directory):
    """Real Cycles ambient-occlusion bake on the same packed UV islands."""
    scene=bpy.context.scene
    image=bpy.data.images.new("ambient_occlusion_baked",width=512,height=512,alpha=False)
    image.colorspace_settings.name="Non-Color"
    image.generated_color=(1.0,1.0,1.0,1.0)
    nodes_created=[]
    try:
        for material in mesh.data.materials:
            if material is None:continue
            nodes=material.node_tree.nodes
            target=nodes.new("ShaderNodeTexImage")
            target.name="F09_REAL_AO_BAKE_TARGET"
            target.image=image
            nodes.active=target
            nodes_created.append((material,target))
        assert nodes_created
        scene.render.bake.use_clear=True
        bpy.ops.object.bake(type="AO")
        image.filepath_raw=str((directory/"ambient_occlusion_baked.png").resolve())
        image.file_format="PNG"
        image.save()
        assert (directory/"ambient_occlusion_baked.png").stat().st_size>3000
    finally:
        for material,target in nodes_created:
            material.node_tree.nodes.remove(target)
    return image


def bake_auxiliary(mesh,folder):
    rough=_scalar_bake(mesh,folder,"roughness_baked","Roughness")
    metal=_scalar_bake(mesh,folder,"metallic_baked","Metallic")
    normal=_normal_bake(mesh,folder)
    ao=_ambient_occlusion_bake(mesh,folder)
    r=np.array(rough.pixels[:],dtype=np.float32).reshape(512,512,4)
    m=np.array(metal.pixels[:],dtype=np.float32).reshape(512,512,4)
    a=np.array(ao.pixels[:],dtype=np.float32).reshape(512,512,4)
    packed=np.ones_like(r)
    packed[:,:,0]=a[:,:,0]
    packed[:,:,1]=r[:,:,0]
    packed[:,:,2]=m[:,:,0]
    img=bpy.data.images.new("f09_preview_orm",width=512,height=512,alpha=False)
    img.colorspace_settings.name="Non-Color"
    img.pixels.foreach_set(packed.ravel())
    img.update()
    img.filepath_raw=str((folder/"occlusion_roughness_metallic.png").resolve())
    img.file_format="PNG"
    img.save()
    assert (folder/"occlusion_roughness_metallic.png").stat().st_size>3000
    # Source images remain separately inspectable. Exporter gets the expected
    # glTF PBR green roughness / blue metallic channels via SeparateColor.
    for material in mesh.data.materials:
        if not material:continue
        nodes=material.node_tree.nodes
        links=material.node_tree.links
        bsdf=next(node for node in nodes if node.bl_idname=="ShaderNodeBsdfPrincipled")
        tex=nodes.new("ShaderNodeTexImage")
        tex.name="F09_PREVIEW_ORM"
        tex.image=img
        separate=nodes.new("ShaderNodeSeparateColor")
        separate.mode="RGB"
        links.new(tex.outputs["Color"],separate.inputs["Color"])
        links.new(separate.outputs["Green"],bsdf.inputs["Roughness"])
        links.new(separate.outputs["Blue"],bsdf.inputs["Metallic"])
        normal_tex=nodes.new("ShaderNodeTexImage")
        normal_tex.image=normal
        # glTF exporter recognizes this named node-group input as AO.\n        group=bpy.data.node_groups.get("glTF Settings")\n        if group is None:\n            group=bpy.data.node_groups.new("glTF Settings","ShaderNodeTree")\n            group.inputs.new("NodeSocketFloat","Occlusion")\n        settings=nodes.new("ShaderNodeGroup")\n        settings.node_tree=group\n        links.new(separate.outputs["Red"],settings.inputs["Occlusion"])\n        normal_node=nodes.new("ShaderNodeNormalMap")
        links.new(normal_tex.outputs["Color"],normal_node.inputs["Color"])
        links.new(normal_node.outputs["Normal"],bsdf.inputs["Normal"])
    return {"ambient_occlusion":"ambient_occlusion_baked.png",\n            "ao_channel":"REAL_CYCLES_AO_BAKE",\n            "roughness":"roughness_baked.png","metallic":"metallic_baked.png",
            "orm":"occlusion_roughness_metallic.png",
            "normal":"normal_tangent_baked.png",
            "pbr_map_resolution":[512,512],
            "pbr_map_status":"ISOLATED_REAL_BAKES_NOT_F11_APPROVED"}
