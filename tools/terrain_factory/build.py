"""LAST LIGHT original Blender terrain/tile authoring and 2.5D bridge.

blender -b --factory-startup -t 2 --python tools/terrain_factory/build.py -- \
  --out build/terrain_v1 --limit 12 --samples 8

Each tile has a true editable 1m surface mesh, not an imported sprite plane.
Raster art is rendered from that mesh with the existing fixed camera/light rig.
The 80x40 tile is a candidate until founder and Godot/device gates pass.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import bpy
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "blender_factory"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import render_v3_recovery as rig
import recipe
import pixel_finish

RENDER_SIZE = 1024
MESH_STEPS = 40


def srgb_to_linear(c):
    return c / 12.92 if c <= .04045 else ((c + .055) / 1.055) ** 2.4


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def tile_mesh(job, surfaces):
    n = MESH_STEPS
    variant = recipe.stable_seed(job["asset_id"])
    relief_a = recipe.RELIEF_AMPLITUDE_M[surfaces[job["a"]]["material"]]
    relief_b = (recipe.RELIEF_AMPLITUDE_M[surfaces[job["b"]]["material"]]
                if job["b"] else relief_a)
    relief = max(relief_a, relief_b)
    verts = []
    rgba = []
    faces = []
    for j in range(n + 1):
        v = j / n
        for i in range(n + 1):
            u = i / n
            verts.append((u - .5, v - .5, recipe.height(u, v, variant, relief)))
            # Blender color attributes are linear. Feeding sRGB channel values
            # directly makes earth/wood/grass nearly white after display transform.
            rgba.append((*[srgb_to_linear(c) for c in recipe.color(
                job, surfaces, u, v, variant)], 1.0))
    for j in range(n):
        for i in range(n):
            q = j * (n + 1) + i
            faces.append((q, q + 1, q + n + 2, q + n + 1))
    mesh = bpy.data.meshes.new(job["asset_id"] + " original mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    attribute = mesh.color_attributes.new(name="LL_Terrain_Color", type="FLOAT_COLOR", domain="CORNER")
    uvmap = mesh.uv_layers.new(name="LL_Terrain_UV")
    for loop in mesh.loops:
        vid = loop.vertex_index
        attribute.data[loop.index].color = rgba[vid]
        u = (vid % (n + 1)) / n
        v = (vid // (n + 1)) / n
        uvmap.data[loop.index].uv = (u, v)
    mat = bpy.data.materials.new("LL original periodic terrain vertex colors")
    mat.diffuse_color = (0.6, .6, .6, 1)
    mat.use_nodes = True
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    nodes.clear()
    out = nodes.new("ShaderNodeOutputMaterial")
    shader = nodes.new("ShaderNodeBsdfPrincipled")
    rough_a = surfaces[job["a"]]["roughness"]
    rough_b = surfaces[job["b"]]["roughness"] if job["b"] else rough_a
    shader.inputs["Roughness"].default_value = (rough_a + rough_b) * .5
    shader.inputs["Metallic"].default_value = 0
    color = nodes.new("ShaderNodeAttribute")
    color.attribute_name = "LL_Terrain_Color"
    links.new(color.outputs["Color"], shader.inputs["Base Color"])
    links.new(shader.outputs["BSDF"], out.inputs["Surface"])
    mesh.materials.append(mat)
    obj = bpy.data.objects.new(job["asset_id"], mesh)
    bpy.context.collection.objects.link(obj)
    obj["tile_size_m"] = 1.0
    obj["logical_surface_a"] = job["a"]
    obj["logical_surface_b"] = job["b"] or ""
    obj["corner_mask"] = job["mask"]
    obj["world_origin"] = "tile_center"
    return obj


def export_glb(obj, dest):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.export_scene.gltf(filepath=str(dest.resolve()), export_format="GLB",
                              use_selection=True, export_apply=True)
    if dest.stat().st_size < 500:
        raise RuntimeError("empty 3D source export")


def finish_raw(raw, dest, origin, job, surfaces):
    from PIL import Image
    # Rig calibration: at 1024 source px one 1m diamond is 320x160.
    # Native 80x40 is 4x BOX reduction from actual Blender surface rendering.
    im = Image.open(raw).convert("RGBA")
    cx, cy = origin
    if abs(cx - 512) > 1.5 or abs(cy - 512) > 1.5:
        raise RuntimeError("camera contact pivot drift: " + str(origin))
    x0 = round(cx) - 160
    y0 = round(cy) - 80
    crop = im.crop((x0, y0, x0 + 320, y0 + 160))
    native = crop.resize((80, 40), Image.Resampling.BOX)
    # Half-open pixel-center diamond mask avoids floating antialias halos.
    pixels = native.load()
    for y in range(40):
        for x in range(80):
            inside = abs((x + .5 - 40) / 40) + abs((y + .5 - 20) / 20) < 1
            if not inside:
                pixels[x, y] = (0, 0, 0, 0)
            else:
                r, g, b, _alpha = pixels[x, y]
                pixels[x, y] = (r, g, b, 255)
    native = pixel_finish.finish_tile(native, job, surfaces)
    native.save(dest)
    return [40, 20]


def build_one(job, surfaces, out, samples, render):
    folder = out / job["asset_id"]
    folder.mkdir(parents=True, exist_ok=True)
    scene = rig.setup()  # Existing exact 30-degree camera and upper-left rig.
    scene.cycles.samples = samples
    # Cycles' spatial denoiser smears grass, gravel and joints at six samples;
    # moderate extra samples plus the native pixel finisher preserve definition.
    scene.cycles.use_denoising = False
    obj = tile_mesh(job, surfaces)
    bpy.context.view_layer.update()
    projected = world_to_camera_view(scene, scene.camera, Vector((0, 0, 0)))
    pivot = [round(projected.x * RENDER_SIZE, 4),
             round((1 - projected.y) * RENDER_SIZE, 4)]
    blend = folder / "model.blend"
    glb = folder / "model.glb"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend.resolve()), compress=False)
    export_glb(obj, glb)
    files = {"blend": "model.blend", "glb": "model.glb"}
    anchor = None
    if render:
        raw = folder / "raw.png"
        scene.render.filepath = str(raw.resolve())
        bpy.ops.render.render(write_still=True)
        anchor = finish_raw(raw, folder / "world.png", pivot, job, surfaces)
        files.update(raw="raw.png", world="world.png")
    metadata = {
        "schema": 1, "asset_id": job["asset_id"], "family": "terrain_tile",
        "kind": job["kind"], "material_a": job["a"],
        "material_b": job["b"], "corner_mask": job["mask"],
        "physical_dimensions_m": [1.0, 1.0,
            round(max(v.co.z for v in obj.data.vertices) -
                  min(v.co.z for v in obj.data.vertices), 8)],
        "world_footprint_cells": [1, 1], "tile_origin": "center",
        "source_camera": "render_v3_recovery.setup fixed 30deg", "tile_px": [80, 40],
        "render_raw_px": [RENDER_SIZE, RENDER_SIZE], "raw_center_px": pivot,
        "native_anchor_px": anchor, "source_recipe_sha256": recipe.recipe_sha(),
        "build_source_sha256": digest(__file__),
        "pixel_finish_source_sha256": digest(pixel_finish.__file__),
        "files": {k: {"path": v, "sha256": digest(folder / v)} for k, v in files.items()},
        "rights": "Original LAST LIGHT procedural meshes/patterns; no source sprites",
        "geometry_status": "SOURCE_EXPORTED_NEEDS_VISUAL_REVIEW",
        "material_status": "ORIGINAL_SHADER_CANDIDATE_NEEDS_VISUAL_REVIEW",
        "render_status": "2_5D_TECHNICAL_CANDIDATE" if render else "PENDING",
        "founder_golden_approved": False, "godot_integrated": False,
        "iphone_verified": False, "gameplay_surface_parameters": "UNASSIGNED",
    }
    (folder / "asset.json").write_text(json.dumps(metadata, indent=2) + "\n")
    print("LL_TERRAIN_TILE_EXPORTED", job["asset_id"], flush=True)
    return metadata


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=12)
    parser.add_argument("--samples", type=int, default=8)
    parser.add_argument("--no-render", action="store_true")
    parser.add_argument("--ids", default="", help="Comma-separated canonical tile IDs")
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    opt = parser.parse_args(args)
    full = recipe.plan()
    jobs = full["jobs"]
    if opt.ids:
        ids = opt.ids.split(",")
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate requested tile ID")
        matched = {j["asset_id"]: j for j in jobs}
        jobs = [matched[x] for x in ids]  # unknown ID fails intentionally
    if opt.limit <= 0:
        raise ValueError("--limit must be positive; use 106 for full current recipe")
    jobs = jobs[:opt.limit]
    surfaces = {s["id"]: s for s in recipe.catalog()["surfaces"]}
    opt.out.mkdir(parents=True, exist_ok=True)
    results = [build_one(job, surfaces, opt.out, opt.samples, not opt.no_render)
               for job in jobs]
    index = {"schema": 1, "family": "terrain_tile", "full_recipe_count": full["count"],
             "built_count": len(results), "aliases": full["aliases"],
             "assets": [r["asset_id"] for r in results],
             "founder_approved_count": 0, "godot_integrated_count": 0}
    (opt.out / "manifest.json").write_text(json.dumps(index, indent=2) + "\n")
    print("LL_TERRAIN_BATCH_PASS", len(results), full["count"], flush=True)


if __name__ == "__main__":
    main()
