"""Blender-native inspection that V2 repaired actual source PARTS.

The gate is structural and does not pretend to measure Golden40 style fidelity.
"""
import argparse
import json
import sys
from pathlib import Path
import bpy

ROOT=Path(__file__).resolve().parents[2]

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--sources",type=Path,required=True)
    parser.add_argument("--asset-ids",required=True)
    args=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    a=parser.parse_args(args)
    ids=a.asset_ids.split(",")
    passed=0
    for aid in ids:
        source=a.sources/aid
        manifest=json.loads((source/"geometry_manifest.json").read_text())
        if manifest.get("refinement_profile")!="v2" or not manifest["refinement"]["applied"]:
            raise RuntimeError("Geometry not refined: "+aid)
        bpy.ops.wm.open_mainfile(filepath=str((source/"model.blend").resolve()))
        objs=list(bpy.context.scene.objects)
        meshes=[o for o in objs if o.type=="MESH"]
        names=[o.name for o in objs]
        if len(meshes)<3:raise RuntimeError("empty geometry after reopen: "+aid)
        if not any(o.data.materials for o in meshes):
            raise RuntimeError("missing source material assignments: "+aid)
        if aid.startswith("ll_master_vehicle_"):
            for tag in ("smooth pressed roof","side left pane","side right pane",
                        "formed wheel arch lip","functional door-panel line"):
                if not any(tag in s for s in names):
                    raise RuntimeError("vehicle lacks true V2 "+tag+": "+aid)
            if any("pressed separate roof" in s for s in names):
                raise RuntimeError("unrefined box roof remains: "+aid)
            if len([s for s in names if "LL FLEET tire" in s])<4:
                raise RuntimeError("actual old wheels not preserved: "+aid)
        else:
            for tag in ("functional steel shaft","reusable ergonomic molded handle"):
                if aid != "ll_tools_crowbar" and not any(tag in s for s in names):
                    raise RuntimeError("hand-tool stage missing "+tag+": "+aid)
            if aid=="ll_tools_crowbar" and not any("curved forged crowbar" in s for s in names):
                raise RuntimeError("wrong crowbar geometry "+aid)
            if aid=="ll_tools_awl" and not any("awl genuine piercing tip" in s for s in names):
                raise RuntimeError("no actual tapered tip "+aid)
        bpy.context.view_layer.update()
        if bpy.context.scene.camera is None or bpy.context.scene.camera.data.type!="ORTHO":
            raise RuntimeError("lost fixed orthographic camera "+aid)
        passed+=1
        print("LL_REFINEMENT_BLENDER_GEOMETRY_PASS",aid,len(meshes),flush=True)
    print("LL_REFINEMENT_BLENDER_ALL_PASS",passed,flush=True)

if __name__=="__main__":
    main()
