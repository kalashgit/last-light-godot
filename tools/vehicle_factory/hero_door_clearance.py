"""Blender mesh-intersection audit for F10's noncanonical front door.

Samples the *actual posed evaluated triangles*, not just object origins or
axis-aligned boxes. A positive result is contact evidence, not a full swept
collision or vehicle-physics certification.
"""
import argparse
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils.bvhtree import BVHTree

sys.path.insert(0,str(Path(__file__).resolve().parent))
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"blender_factory"))
import render_v3_recovery as base
from hero_hatchback import build


MOVING = {
    "door_skin": "F10 HERO connected left front door exterior",
    "door_inner_card": "LL FLEET F10 HERO driver door inner padded card",
    "door_front_edge": "LL FLEET F10 HERO driver door front edge thickness",
    "door_window": "F10 HERO inset front door pane",
}
GUARDS = {
    "left_front_fender": "F10 HERO continuous sculpted side",
    "front_left_tire": "F10 HERO tire.002",
    "front_aperture_jamb": "LL FLEET F10 HERO cabin aperture jamb.001",
    "rear_aperture_jamb": "LL FLEET F10 HERO cabin aperture jamb",
}


def world_bvh(ob, depsgraph):
    evaluated=ob.evaluated_get(depsgraph)
    mesh=evaluated.to_mesh()
    try:
        transform=evaluated.matrix_world
        vertices=[tuple(transform@v.co) for v in mesh.vertices]
        polygons=[tuple(p.vertices) for p in mesh.polygons if len(p.vertices)>=3]
        assert polygons,ob.name
        return BVHTree.FromPolygons(vertices,polygons,all_triangles=False,epsilon=0.00001)
    finally:
        evaluated.to_mesh_clear()


def audit(output):
    base.setup()
    build(driver_door_deg=0)
    hinge=bpy.data.objects["F10 HERO driver door vertical hinge PROTOTYPE"]
    moving={k:bpy.data.objects[v] for k,v in MOVING.items()}
    guards={k:bpy.data.objects[v] for k,v in GUARDS.items()}
    assert all(ob.parent==hinge for ob in moving.values())
    angles=list(range(0,66,5))+[66]
    contact=[]
    for angle in angles:
        hinge.rotation_euler.z=math.radians(angle)
        bpy.context.view_layer.update()
        depsgraph=bpy.context.evaluated_depsgraph_get()
        dynamic={k:world_bvh(ob,depsgraph) for k,ob in moving.items()}
        stationary={k:world_bvh(ob,depsgraph) for k,ob in guards.items()}
        for part,dyn in dynamic.items():
            for obstacle,static in stationary.items():
                overlaps=dyn.overlap(static)
                if overlaps:
                    contact.append({"angle_deg":angle,"moving_part":part,
                                    "fixed_part":obstacle,"triangle_pairs":len(overlaps)})
    output.parent.mkdir(parents=True,exist_ok=True)
    verdict="CONTACT_DETECTED" if any(c["angle_deg"]>0 for c in contact) else "NO_SAMPLED_TRIANGLE_CONTACT"
    report={"schema_version":1,"status":"NONCANONICAL_F10_HERO_DOOR_CLEARANCE_AUDIT",
            "method":"evaluated_world_mesh_BVH_triangle_overlap",
            "sampled_angles_deg":angles,"moving_parts":list(MOVING),
            "fixed_parts":list(GUARDS),"contact_count":len(contact),
            "verdict":verdict,"contacts":contact,
            "limitations":["discrete angular samples only",
                           "no toleranced swept-volume clearance certification",
                           "not an engine collision test"]}
    output.write_text(json.dumps(report,indent=2)+"\n")
    print("F10_DOOR_CLEARANCE_AUDIT",verdict,len(contact),flush=True)
    return report


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",type=Path,required=True)
    argv=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    args=parser.parse_args(argv)
    audit(args.output)
