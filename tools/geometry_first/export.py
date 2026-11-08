"""LAST LIGHT original 3D master exporter from prior sprites and factory shapes.

Headless:
 blender -b --factory-startup -t 2 --python tools/geometry_first/export.py -- \
    --plan build/geometry_first/plan.json \
    --output build/geometry_first/source_models --max-jobs 60 --preview-every 1

Exports editable .blend AND interoperable .glb for every selected identity,
plus EXPLICIT geometry QA / source-recipe hashes. Preview PNGs are for review:
NOT Golden approval, not finished textured/2.5D engine imports.

For Golden40 icons the input 2D PNGs are references, not flat textured planes.
Previously unseen backs / undersides are ORIGINAL estimated construction.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import sys
import time
from pathlib import Path

import bpy
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

ROOT=Path(__file__).resolve().parents[2]
for path in ("tools/blender_factory","tools/asset_factory","tools/vehicle_factory",
             "tools/actor_factory","tools/geometry_first"):
    sys.path.insert(0,str(ROOT/path))
import render_v3_recovery as hero
import geometry as item_geometry
from catalog import registry as catalog_registry
from fleet_catalog import PROFILES,PALETTE
from fleet_render import build_vehicle
import importlib.util
# Several factories contain a file named render.py; bind the actor version explicitly.
actor_module_path=ROOT/"tools/actor_factory/render.py"
actor_spec=importlib.util.spec_from_file_location("ll_actor_source_render",actor_module_path)
actor_render=importlib.util.module_from_spec(actor_spec)
actor_spec.loader.exec_module(actor_render)
from golden40_mesh import build as build_golden
from refine_v2 import apply as apply_v2_refinement, recipe_sha256 as refine_v2_sha

MODEL_TYPES={"MESH","CURVE","FONT","SURFACE"}
HERO_FURNITURE={"refrigerator":hero.fridge_v3,
                "cabinet":hero.cabinet_v3,
                "sofa":hero.sofa_v3}

def sha(file):
    h=hashlib.sha256()
    with file.open("rb") as stream:
        for data in iter(lambda:stream.read(1048576),b""):
            h.update(data)
    return h.hexdigest()

def build_item(job):
    tag=job["category"]
    if tag=="golden40":
        build_golden(job)
    elif tag=="catalog":
        obj=next((o for o in catalog_registry() if o["id"]==job["asset_id"]),None)
        if obj is None:
            raise RuntimeError("missing original item catalog record: "+job["asset_id"])
        item_geometry.build(obj)
    elif tag=="furniture":
        name=job["name"]
        materials=hero.materials(name)
        HERO_FURNITURE[name](materials)
    elif tag=="vehicle":
        prof=PROFILES[job["name"]]
        build_vehicle({"model":job["name"],"paint_hex":PALETTE["olive_green"],
                       "condition_level":1})
    elif tag=="actor":
        pilot=next((a for name,a,_ in actor_render.pilots() if name==job["name"]),None)
        if pilot is None:
            raise RuntimeError("unknown actor variant: "+job["name"])
        actor_render.draw_actor(pilot,"idle",0.0)
    else:
        raise RuntimeError("unsupported source geometry family: "+tag)

def actual_geometry():
    return [o for o in bpy.context.scene.objects if o.type in MODEL_TYPES and
            o.name not in ("Camera",)]

def validate_bounds(objects,job):
    if not objects:
        raise RuntimeError(job["asset_id"]+" has no original 3D source objects")
    dg=bpy.context.evaluated_depsgraph_get()
    vertices=[]
    for ob in objects:
        # Evaluate exact deform + bevel + geometry for true spatial envelope.
        try:
            eval_ob=ob.evaluated_get(dg)
            mesh=eval_ob.to_mesh()
            if mesh:
                matrix=eval_ob.matrix_world
                vertices.extend(matrix @ v.co for v in mesh.vertices)
            eval_ob.to_mesh_clear()
        except (RuntimeError,TypeError):
            pass
    if not vertices:
        raise RuntimeError(job["asset_id"]+" has no evaluated 3D mesh vertices")
    mins=[min(float(v[i]) for v in vertices) for i in range(3)]
    maxs=[max(float(v[i]) for v in vertices) for i in range(3)]
    size=[round(maxs[i]-mins[i],5) for i in range(3)]
    if any(not math.isfinite(x) or x<.003 or x>22 for x in size):
        raise RuntimeError(job["asset_id"]+" bad geometry bounds "+str(size))
    requested=job["dimensions_m"]
    # Loose gate: Blender artwork often contains external handles and wheels.
    # Source proportions are flagged for later refinement rather than silently
    # asserted exact from a single icon.
    ratio=[round(a/b,3) for a,b in zip(size,requested)]
    severe_mismatch=any(x<.33 or x>3.0 for x in ratio)
    return dict(actual_bounds_m=size,requested_dimensions_m=requested,
                bounding_ratio=ratio,
                geometry_family=job["geometry_family"],
                geometry_warning=("SOURCE_PROPORTIONS_NEED_REVIEW" if severe_mismatch else None),
                nonempty_meshes=len(objects))

def glb_export(dest,objects):
    bpy.ops.object.select_all(action="DESELECT")
    selection=[]
    for o in objects:
        o.select_set(True)
        selection.append(o)
    if not selection:
        raise RuntimeError("empty Blender export selection")
    bpy.context.view_layer.objects.active=next(
        (o for o in selection if o.type=="MESH"),selection[0])
    bpy.ops.export_scene.gltf(filepath=str(dest),
                              export_format="GLB",use_selection=True,
                              export_apply=True)
    if dest.stat().st_size<500:
        raise RuntimeError("empty original 3D glb file: "+str(dest))

def preview(path,job,objects,samples=8):
    # Render for 3D source verification only. This is not world-scale 2.5D atlas.
    sc=bpy.context.scene
    length=max(job["dimensions_m"])
    sc.camera.data.ortho_scale=max(hero.ORTHO,length*1.45)
    sc.cycles.samples=samples
    sc.render.resolution_x=512
    sc.render.resolution_y=512
    sc.render.resolution_percentage=100
    sc.render.film_transparent=True
    sc.render.image_settings.file_format="PNG"
    sc.render.image_settings.color_mode="RGBA"
    sc.render.filepath=str(path.resolve())
    bpy.ops.render.render(write_still=True)

def build_one(job,out,preview_png=False,skip_existing=False,refinement_profile="v1"):
    source_id=job["asset_id"]
    dest=out/source_id
    dest.mkdir(parents=True,exist_ok=True)
    metadata=dest/"geometry_manifest.json"
    if skip_existing and metadata.exists():
        cached=json.loads(metadata.read_text())
        if (cached.get("source_recipe_sha256")==job["template_source_hash"]
            and cached.get("refinement_profile","v1")==refinement_profile
            and (refinement_profile!="v2" or cached.get("refinement_code_sha256")==refine_v2_sha())
            and (dest/"model.blend").is_file() and (dest/"model.glb").is_file()):
            print("LL_GEOMETRY_CACHE_HIT",source_id,flush=True)
            return cached
    start=time.monotonic()
    # Reference fixed camera and light for consistent shape previews.
    hero.setup()
    build_item(job)
    if refinement_profile=="v2":
        refinement=apply_v2_refinement(job)
    elif refinement_profile=="v1":
        refinement=dict(refinement_version="original_geometry_first_v1",applied=False,
                        reason="ORIGINAL_FIRST_PASS_SOURCE_UNMODIFIED")
    else:
        raise ValueError("unsupported refinement profile: "+refinement_profile)
    bpy.context.view_layer.update()
    objects=actual_geometry()
    metrics=validate_bounds(objects,job)
    blend=dest/"model.blend"
    glb=dest/"model.glb"
    # Preserve the original editable Blender procedural source with all
    # modifiers/material zones and independent part names.
    bpy.ops.wm.save_as_mainfile(filepath=str(blend.resolve()),compress=False)
    glb_export(glb,objects)
    if preview_png:
        preview(dest/"preview_source.png",job,objects)
    manifest=dict(
       schema=1,asset_id=source_id,category=job["category"],
       source_recipe_sha256=job["template_source_hash"],
       refinement_profile=refinement_profile,
       refinement_code_sha256=refine_v2_sha() if refinement_profile=="v2" else None,
       refinement=refinement,
       source_reference=job.get("source_reference"),
       source_reference_sha256=job.get("source_reference_sha256"),
       original_geometry=True,
       geometry_status="GEOMETRY_SOURCE_EXPORTED_NEEDS_VISUAL_RECONSTRUCTION_QA",
       material_status="PLACEHOLDER_OR_EXISTING_MATERIAL_PENDING_GOLDEN_REFINEMENT",
       render_2_5d_status="PENDING",
       godot_import_status="PENDING",
       founder_golden_approved=False,
       editable_blend="model.blend",editable_blend_sha256=sha(blend),
       interoperable_glb="model.glb",glb_sha256=sha(glb),
       preview="preview_source.png" if preview_png else None,
       elapsed_s=round(time.monotonic()-start,3),**metrics)
    metadata.write_text(json.dumps(manifest,indent=2)+"\n")
    print("LL_GEOMETRY_SOURCE_EXPORTED",source_id,
          len(objects),str(metrics["actual_bounds_m"]),flush=True)
    return manifest

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--plan",required=True,type=Path)
    parser.add_argument("--output",required=True,type=Path)
    parser.add_argument("--max-jobs",type=int,default=0)
    parser.add_argument("--preview-every",type=int,default=5)
    parser.add_argument("--resume",action="store_true")
    parser.add_argument("--refinement-profile",choices=("v1","v2"),default="v1")
    args=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    a=parser.parse_args(args)
    plan=json.loads(a.plan.read_text())
    if plan["schema"]!=1 or plan["status"]!="GEOMETRY_SOURCE_PLAN_NOT_RENDERED_NOT_GOLDEN_APPROVED":
        raise ValueError("unsupported reconstruction plan")
    a.output.mkdir(parents=True,exist_ok=True)
    jobs=plan["jobs"][:a.max_jobs] if a.max_jobs else plan["jobs"]
    if a.preview_every<0:raise ValueError("preview-every cannot be negative")
    built=[]
    for idx,job in enumerate(jobs):
        result=build_one(job,a.output,
                         preview_png=a.preview_every>0 and idx%a.preview_every==0,
                         skip_existing=a.resume,
                         refinement_profile=a.refinement_profile)
        built.append(dict(asset_id=result["asset_id"],
            geometry_status=result["geometry_status"],
            actual_bounds_m=result["actual_bounds_m"],
            geometry_warning=result["geometry_warning"],
            preview=result["preview"],
            recipe_hash=result["source_recipe_sha256"],
            glb_sha256=result["glb_sha256"]))
    report=dict(schema=1,source_plan_sha256=plan["plan_sha256"],
        source_plan_unique_count=plan["total_unique"],
        generated_3d_source_count=len(built),
        ungenerated_remaining=plan["total_unique"]-len(built),
        status="REAL_3D_SOURCES_NOT_2_5D_OR_GOLDEN_APPROVED",
        refinement_profile=a.refinement_profile,
        refined_sources_count=sum(bool((a.output/x["asset_id"]/"geometry_manifest.json").exists()
                and json.loads((a.output/x["asset_id"]/"geometry_manifest.json").read_text())
                    .get("refinement",{}).get("applied")) for x in built),
        items=built)
    (a.output/"batch_report.json").write_text(json.dumps(report,indent=2)+"\n")
    print("LL_GEOMETRY_BATCH_PASS",len(built),plan["total_unique"],
          "unique 3D master sources",flush=True)

if __name__=="__main__":
    main()
