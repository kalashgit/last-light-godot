"""Blender-native validation of EVERY fleet geometry archetype before expensive rendering.

Proves ten distinct source builders can run, components are physically sized,
and each shares the required independently visible tires, glass and exterior.
Does NOT assert Golden visual quality.
"""
import math
import sys
from pathlib import Path
import bpy
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"tools"/"blender_factory"))
sys.path.insert(0,str(ROOT/"tools"/"vehicle_factory"))
import render_v3_recovery as base
from fleet_render import build_vehicle
from fleet_catalog import PROFILES, PALETTE

def run():
    passed=0
    signatures={}
    for model,profile in PROFILES.items():
        base.setup()
        job=dict(model=model,paint_hex=PALETTE["olive_green"],condition_level=1)
        L,W,H=build_vehicle(job)
        bpy.context.view_layer.update()
        mesh=[o for o in bpy.context.scene.objects if o.type=="MESH"]
        curve=[o for o in bpy.context.scene.objects if o.type=="CURVE"]
        all_objs=mesh+curve
        if len(mesh)<22:
            raise RuntimeError(f"{model} has insufficient distinct original geometry: {len(mesh)}")
        wheels=[o for o in mesh if "tire" in o.name.lower()]
        if len(wheels)<4:
            raise RuntimeError(f"{model} has fewer than four built tires")
        glass=[o for o in all_objs if "glass" in o.name.lower() or "window" in o.name.lower()]
        if len(glass)<2:
            raise RuntimeError(f"{model} has inadequate glass/window source elements")
        positions=[]
        for obj in mesh:
            for v in obj.bound_box:
                pt=obj.matrix_world @ Vector(v)
                if not all(math.isfinite(float(x)) for x in pt):
                    raise RuntimeError(f"{model}: invalid mesh coordinates")
                positions.append(pt)
        ranges=[max(p[axis] for p in positions)-min(p[axis] for p in positions) for axis in range(3)]
        # Shapes must fit within plausible +/- 40% of their original real size.
        # Excessive protrusions, camera/framing bugs and accidental 100x scaling fail.
        for got,want in zip(ranges,(L,W,H)):
            if not .55*want<=got<=1.40*want:
                raise RuntimeError(f"{model}: source bounding dimensions {ranges} vs {(L,W,H)}")
        signature=(profile["geometry"],round(L,2),round(W,2),round(H,2),
                   len(mesh),len(curve))
        signatures[model]=signature
        passed+=1
        print("LL_FLEET_GEOMETRY_PASS",model,len(mesh),len(curve),
              [round(v,3) for v in ranges],flush=True)
    if len({x[0] for x in signatures.values()})!=10:
        raise RuntimeError("distinct ten archetype family set missing")
    print("LL_FLEET_GEOMETRY_ALL_PASS",passed,flush=True)

if __name__=="__main__":run()
