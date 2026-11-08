"""Blender-native inspection that V2 repaired actual source PARTS.

The gate is structural and does not pretend to measure Golden40 style fidelity.
"""
import argparse
import json
import sys
from pathlib import Path
import bpy
from mathutils import Vector

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
        drawables=[o for o in objs if o.type in ("MESH","CURVE","FONT")]
        # Some real curved rods (e.g. crowbar) are intentionally editable
        # Blender curve+mesh combinations, not three independent MESH objects.
        if len(drawables)<2:raise RuntimeError("empty geometry after reopen: "+aid)
        if not any(o.data.materials for o in drawables):
            raise RuntimeError("missing source material assignments: "+aid)
        if aid.startswith("ll_master_vehicle_"):
            # Physically grounded LL-084: no vehicle side window may project
            # below ground or create a 3m tall "compact" car due to swapped axes.
            zvals=[]
            dg=bpy.context.evaluated_depsgraph_get()
            for obj in drawables:
                evaluated=obj.evaluated_get(dg)
                mesh=evaluated.to_mesh()
                if mesh is not None:
                    zvals.extend((evaluated.matrix_world @ v.co).z for v in mesh.vertices)
                evaluated.to_mesh_clear()
            if not zvals:
                raise RuntimeError("vehicle has no evaluated vertices: "+aid)
            expected=float(manifest["requested_dimensions_m"][2])
            if min(zvals)<-.10 or max(zvals)>expected*1.18:
                raise RuntimeError("vehicle has unphysical z bounds: "+aid+
                                   " [%.3f,%.3f] expected height %.3f"%(
                                       min(zvals),max(zvals),expected))
            print("LL_REFINEMENT_HEIGHT_PASS",aid,round(min(zvals),3),round(max(zvals),3))
            # Pickups preserve the distinct utility bonnet from their source
            # chassis; all other supported passenger families replace the
            # original spherical nose with a contoured pressed hood.
            pickup=aid=="ll_master_vehicle_work_pickup"
            parts=("smooth pressed roof","side left pane","side right pane",
                   "formed wheel arch lip","functional door-panel line")
            if not pickup:
                parts+=("sculpted contoured bonnet",)
            for tag in parts:
                if not any(tag in s for s in names):
                    raise RuntimeError("vehicle lacks true V2 "+tag+": "+aid)
            if not pickup and any("LL FLEET body nose" in s for s in names):
                raise RuntimeError("old spherical nose should be replaced: "+aid)
            if any("pressed separate roof" in s for s in names):
                raise RuntimeError("unrefined box roof remains: "+aid)
            if len([s for s in names if "LL FLEET tire" in s])<4:
                raise RuntimeError("actual old wheels not preserved: "+aid)
            if aid=="ll_master_vehicle_compact_hatchback":
                for tag in ("hatchback aligned windshield","hatchback aligned rear hatch glass",
                            "front dark ventilated grille","sculpted contoured bonnet hatchback hood crown"):
                    if not any(tag in name for name in names):
                        raise RuntimeError("hatchback missing real assembly "+tag)
                for obsolete in ("rear passenger volume","short hatch tail","frontal glass",
                                 "rear glass","pressed waist seam"):
                    if any(name.startswith("LL FLEET "+obsolete) for name in names):
                        raise RuntimeError("hatchback retained overlapping solid part: "+obsolete)
                panels=[o for o in meshes if "hatchback actual cutout fender side" in o.name]
                if len(panels)!=2:
                    raise RuntimeError("hatchback requires two actual cutout fender side skins")
                wheelbase=float(panels[0]["wheelbase_m"])
                for panel in panels:
                    radius=float(panel["wheel_arch_radius_m"])
                    axle_z=float(panel["wheel_axle_z_m"])
                    if len(panel.data.vertices)<40:
                        raise RuntimeError("fender is not a detailed concave opening")
                    for wheel_x in (-wheelbase*.5,wheelbase*.5):
                        arch=[v.co.z for v in panel.data.vertices if abs(v.co.x-wheel_x)<.0005]
                        if not arch or max(arch)<axle_z+radius-.01:
                            raise RuntimeError("no physical wheel clearance at "+str(wheel_x))
                print("LL_HATCHBACK_TRUE_FENDER_CUTOUT_PASS",round(wheelbase,3),flush=True)
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
