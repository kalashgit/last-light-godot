"""F09 cross-family *candidate fixture*: texture bake + 16 true-scale sprite headings.

Never feeds canonical F11/F12 queues. Requires Blender 4.0+ and cycles CPU.
Run: blender -b --factory-startup -t 2 --python-exit-code 1 --python
     tools/weapons_tools/f09_integration_fixture.py
"""
import hashlib
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Matrix

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"tools"/"weapons_tools"))
import build as factory
from f09_v5_models import build as build_tool
from f09_v6_materials import refine_materials

DEST=ROOT/"build"/"f09_integration_fixture"
SELECT={"ll_tools_hand_saw","ll_tools_adjustable_wrench","ll_tools_socket_handle"}

def configure(scene):
    scene.render.engine="CYCLES"
    scene.cycles.samples=4
    scene.cycles.use_denoising=False
    for layer in scene.view_layers:
        if hasattr(layer,"cycles"):
            layer.cycles.use_denoising=False
    scene.render.film_transparent=True
    scene.render.image_settings.file_format="PNG"
    scene.render.image_settings.color_mode="RGBA"

def bake_atlas(objects, folder, item):
    # The source .blend is saved *before* the fixture modifies any geometry.
    scene=bpy.context.scene
    configure(scene)
    scene.render.bake.use_pass_direct=False
    scene.render.bake.use_pass_indirect=False
    scene.render.bake.use_pass_color=True
    scene.render.bake.margin=8
    bpy.ops.object.select_all(action="DESELECT")
    meshes=[o for o in objects if o.type=="MESH"]
    assert meshes and len(meshes)==len(objects),"fixture handles mesh-only models"
    # The material factory produces modifiers; evaluate and apply before
    # joining into a single editable UV-atlas candidate.
    for ob in meshes:
        bpy.ops.object.select_all(action="DESELECT")
        ob.select_set(True)
        bpy.context.view_layer.objects.active=ob
        for mod in list(ob.modifiers):
            bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.ops.object.select_all(action="DESELECT")
    for ob in meshes:ob.select_set(True)
    bpy.context.view_layer.objects.active=meshes[0]
    bpy.ops.object.join()
    ob=bpy.context.object
    assert ob.type=="MESH"
    # Preserve original semantic material slots; allocate non-overlapping UVs.
    if ob.data.uv_layers:ob.data.uv_layers.remove(ob.data.uv_layers.active)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(island_margin=.022)
    bpy.ops.object.mode_set(mode="OBJECT")
    assert ob.data.uv_layers.active is not None
    image=bpy.data.images.new(item["asset_id"]+"_F11_PREVIEW_ALBEDO",
                              width=512,height=512,alpha=True)
    image.generated_color=(0.01,0.01,0.01,1)
    for mat in ob.data.materials:
        if not mat:continue
        mat.use_nodes=True
        tex=mat.node_tree.nodes.new("ShaderNodeTexImage")
        tex.name="F09_PREVIEW_BAKE_TARGET"
        tex.image=image
        mat.node_tree.nodes.active=tex
    bpy.ops.object.bake(type="DIFFUSE",pass_filter={"COLOR"})
    image.filepath_raw=str((folder/"albedo_baked.png").resolve())
    image.file_format="PNG"
    image.save()
    assert (folder/"albedo_baked.png").stat().st_size>4000
    # As a candidate, attach baked albedo to a simple Principled GLB shader.
    # Metallic and roughness remain per-material factors; NOT full F11 PBR.
    for mat in ob.data.materials:
        if not mat:continue
        bsdfs=[node for node in mat.node_tree.nodes
               if node.bl_idname=="ShaderNodeBsdfPrincipled"]
        assert bsdfs
        tex=mat.node_tree.nodes.get("F09_PREVIEW_BAKE_TARGET")
        mat.node_tree.links.new(tex.outputs["Color"],bsdfs[0].inputs["Base Color"])
    glb=folder/"preview_albedo_baked.glb"
    factory.glb(glb,[ob])
    assert glb.stat().st_size>4000
    return {"albedo_png":"albedo_baked.png","glb":"preview_albedo_baked.glb",
            "uv_atlas_px":[512,512],"material_mode":"CANDIDATE_BAKED_ALBEDO_AND_PBR_FACTORS",
            "pbr_maps_complete":False}

def world_sprites(scene, objects, folder):
    # Explicit source-canonical camera scale: no per-object auto-fit.
    matrices={o.name:o.matrix_world.copy() for o in objects}
    scene.camera.data.ortho_scale=factory.hero.ORTHO
    scene.render.resolution_x=384
    scene.render.resolution_y=384
    scene.render.resolution_percentage=100
    configure(scene)
    world=folder/"world_16_heading_raw"
    world.mkdir(exist_ok=True)
    for heading in range(16):
        rot=Matrix.Rotation(math.tau*heading/16,4,"Z")
        for ob in objects:ob.matrix_world=rot@matrices[ob.name]
        bpy.context.view_layer.update()
        path=world/("h%02d.png"%heading)
        scene.render.filepath=str(path.resolve())
        bpy.ops.render.render(write_still=True)
        assert path.stat().st_size>300
    for ob in objects:ob.matrix_world=matrices[ob.name]
    return world

def main():
    DEST.mkdir(parents=True,exist_ok=True)
    recipes=json.loads(factory.RECIPE_FILE.read_text())
    report=[]
    for item in recipes["assets"]:
        if item["asset_id"] not in SELECT:continue
        folder=DEST/item["asset_id"]
        folder.mkdir(exist_ok=True)
        scene=factory.hero.setup()
        mats=refine_materials(factory.material_set())
        build_tool(item["archetype"],mats,form=factory.form,tube=factory.tube,
                   grip=factory.grip,closed_sweep=factory.closed_sweep,
                   small_pin=factory.small_pin,hoop=factory.hoop)
        bpy.context.view_layer.update()
        objects=factory.models()
        assert objects
        # Raw world sprites rendered before atlas modifications.
        world_sprites(scene,objects,folder)
        source=folder/"editable_source.blend"
        bpy.ops.wm.save_as_mainfile(filepath=str(source.resolve()))
        maps=bake_atlas(objects,folder,item)
        report.append({"asset_id":item["asset_id"],
                       "canonical_id_verified":False,
                       "golden_approved":False,
                       "f11_approved":False,"f12_approved":False,
                       "godot_approved":False,"iphone_approved":False,
                       "source_blend":"editable_source.blend",
                       "headings":16,"world_ortho":factory.hero.ORTHO,
                       "world_resolution_px":[384,384],
                       "raw_path":"world_16_heading_raw",**maps})
        print("F09_INTEGRATION_FIXTURE_SOURCE_PASS",item["asset_id"],flush=True)
    assert len(report)==3
    (DEST/"integration_source_manifest.json").write_text(json.dumps({
        "schema":1,"stage":"UNAPPROVED_CROSS_FAMILY_VALIDATION_ONLY",
        "model_count":3,"records":report},indent=2)+"\n")

if __name__=="__main__":
    main()
