"""World-space evaluated Blender BVH audit for F10 bonnet and rear liftgate.

This checks actual triangle intersections at sampled hinge poses, not a visual
render or a proxy AABB. Contacts at the shut seam are retained in the report,
but only nonzero opening-angle intersections block the experimental candidate.
"""
import argparse
import json
import math
import sys
from pathlib import Path

import bpy

sys.path.insert(0,str(Path(__file__).resolve().parent))
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"blender_factory"))
import render_v3_recovery as base
from hero_door_clearance import world_bvh
from hero_hatchback import BONNET_HINGE,HATCH_HINGE,build


PANELS={
    "bonnet":{
        "hinge":BONNET_HINGE,"kwarg":"bonnet_deg","axis_sign":-1,"max_deg":56,
        "guard_fragments":(
            "continuous sculpted side", "inset raked windshield",
            "A pillar", "windscreen lower seal", "continuous body crown"),
    },
    "rear_hatch":{
        "hinge":HATCH_HINGE,"kwarg":"rear_hatch_deg","axis_sign":1,"max_deg":70,
        "guard_fragments":(
            "continuous sculpted side", "crowned roof stamped shell",
            "C pillar", "inset rear quarter pane"),
    },
}


def audit(output:Path)->dict:
    report={"schema_version":1,"status":"NONCANONICAL_F10_PANEL_CLEARANCE",
            "method":"Blender evaluated world-mesh BVH triangle overlap",
            "panels":{},"limitations":[
                "discrete five-degree sampling, not continuous swept-volume proof",
                "selected cabin/body guard surfaces, not exhaustive vehicle physics",
                "shared closed seam contacts are recorded separately"]}
    failed=False
    for name,config in PANELS.items():
        base.setup()
        build(**{config["kwarg"]:0})
        hinge=bpy.data.objects[config["hinge"]]
        moving=[o for o in bpy.data.objects if o.type=="MESH" and o.parent==hinge]
        guards=[o for o in bpy.data.objects
                if o.type=="MESH" and o.parent is None
                and any(fragment in o.name for fragment in config["guard_fragments"])]
        assert len(moving)>=2,(name,"missing moving geometry")
        assert len(guards)>=4,(name,"missing static guard geometry")
        samples=list(range(0,config["max_deg"]+1,5))
        if samples[-1]!=config["max_deg"]:
            samples.append(config["max_deg"])
        contacts=[]
        for angle in samples:
            hinge.rotation_euler.y=math.radians(config["axis_sign"]*angle)
            bpy.context.view_layer.update()
            dg=bpy.context.evaluated_depsgraph_get()
            dynamic={o.name:world_bvh(o,dg)[0] for o in moving}
            fixed={o.name:world_bvh(o,dg)[0] for o in guards}
            for moving_name,moving_bvh in dynamic.items():
                for guard_name,fixed_bvh in fixed.items():
                    overlap=moving_bvh.overlap(fixed_bvh)
                    if overlap:
                        contacts.append({"angle_deg":angle,"moving":moving_name,
                                         "fixed":guard_name,
                                         "triangle_pairs":len(overlap),
                                         "first_triangle_pair":list(overlap[0])})
        violations=[c for c in contacts if c["angle_deg"]>0]
        verdict="CONTACT_DETECTED" if violations else "NO_SAMPLED_OPEN_POSE_CONTACT"
        failed=failed or bool(violations)
        report["panels"][name]={
            "hinge":config["hinge"],"sampled_angles_deg":samples,
            "moving_mesh_count":len(moving),"guard_mesh_count":len(guards),
            "closed_seam_contact_count":len(contacts)-len(violations),
            "opening_contact_count":len(violations),"verdict":verdict,
            "contacts":contacts}
        print("F10_PANEL_CLEARANCE",name,verdict,len(violations),flush=True)
    report["verdict"]="CONTACT_DETECTED" if failed else "NO_SAMPLED_OPEN_POSE_CONTACT"
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,indent=2)+"\n")
    return report


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",required=True,type=Path)
    args=parser.parse_args(sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else [])
    result=audit(args.output)
    if result["verdict"]!="NO_SAMPLED_OPEN_POSE_CONTACT":
        raise SystemExit(2)
