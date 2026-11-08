"""Geometry-first render bridge: actual 3D Blender source -> native 2.5D candidate.

Renders source .blend files from fixed 30-degree isometric camera and the
reference material/light rig. Never projects an existing sprite bitmap onto a
flat plane. Output is still a visual *candidate*, not Golden approval.

blender -b --factory-startup -t 2 --python tools/geometry_first/stage2_render.py -- \
    --sources build/geometry_first/source_models --output build/geometry_first/renders \
    --asset-ids ll_master_furniture_refrigerator,ll_master_furniture_cabinet
"""
import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

import bpy

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"tools/blender_factory"))
import render_v3_recovery as hero

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--sources",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--asset-ids",required=True)
    p.add_argument("--samples",type=int,default=12)
    p.add_argument("--vehicle-headings",type=int,choices=(4,8,16),default=16)
    args=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    a=p.parse_args(args)
    names=a.asset_ids.split(",")
    if not names or len(names)!=len(set(names)):
        raise ValueError("choose unique 3D source asset IDs")
    a.output.mkdir(parents=True,exist_ok=True)
    report=[]
    inventory_previews=[]
    for name in names:
        folder=a.sources/name
        source=folder/"model.blend"
        info=json.loads((folder/"geometry_manifest.json").read_text())
        if not source.is_file() or name!=info["asset_id"]:
            raise ValueError("missing reusable 3D source: "+name)
        bpy.ops.wm.open_mainfile(filepath=str(source.resolve()))
        scene=bpy.context.scene
        if scene.camera is None:
            raise RuntimeError("missing original isometric camera")
        scene.camera.data.ortho_scale=hero.ORTHO
        scene.render.resolution_x=1024
        scene.render.resolution_y=1024
        scene.render.resolution_percentage=100
        scene.render.image_settings.file_format="PNG"
        scene.render.image_settings.color_mode="RGBA"
        scene.render.film_transparent=True
        scene.cycles.samples=a.samples
        base=a.output/name
        base.mkdir(parents=True,exist_ok=True)
        orientations=a.vehicle_headings if name.startswith("ll_master_vehicle") else 1
        for index in range(orientations):
            # Rotate objects as a group around the original world origin and
            # restore matrices after export. No per-view recenter.
            models=[x for x in bpy.context.scene.objects if x.type in ("MESH","CURVE","FONT")]
            matrices={x.name:x.matrix_world.copy() for x in models}
            if index:
                from mathutils import Matrix
                rotation=Matrix.Rotation(math.tau*index/orientations,4,"Z")
                for ob in models:
                    ob.matrix_world=rotation @ matrices[ob.name]
            bpy.context.view_layer.update()
            dest=base/("angle_%02d.png"%index)
            scene.render.filepath=str(dest.resolve())
            bpy.ops.render.render(write_still=True)
            for ob in models:
                ob.matrix_world=matrices[ob.name]
            report.append(dict(asset_id=name,index=index,
                heading_deg=round(360*index/orientations,4),
                total_headings=orientations,
                path=str(dest.relative_to(a.output)),
                source_model_sha=info["glb_sha256"],
                source_source_sha=info["source_recipe_sha256"],
                world_projection="30deg_elevation_80x40_tile",
                stage="RENDERED_SOURCE_3D_TO_2_5D_CANDIDATE"))
            print("LL_SOURCE_TO_ISO_RENDER",name,index,flush=True)
        if not name.startswith("ll_master_vehicle"):
            # Keep the true metre-scale world sprite intact. A second close-up
            # makes a physically small tool inspectable for inventory-icon QA.
            scale=max(.34,max(info["requested_dimensions_m"])*1.6)
            scene.camera.data.ortho_scale=scale
            closeup=base/"inventory_closeup.png"
            scene.render.filepath=str(closeup.resolve())
            bpy.ops.render.render(write_still=True)
            inventory_previews.append(dict(asset_id=name,
                path=str(closeup.relative_to(a.output)),camera_scale=scale,
                stage="INVENTORY_CLOSEUP_REVIEW_NOT_WORLD_SCALE_OR_GOLDEN_APPROVED"))
            scene.camera.data.ortho_scale=hero.ORTHO
    (a.output/"render_report.json").write_text(json.dumps(dict(
       schema=1,frames=report,inventory_previews=inventory_previews,
       status="NATIVE_ISO_RENDERED_CANDIDATES_NOT_GOLDEN_APPROVED"),indent=2)+"\n")
    print("LL_SOURCE_TO_2_5D_PASS",len(report),flush=True)

if __name__=="__main__":
    main()
