"""Blender geometry sanity checks for the noncanonical hatchback hero revision."""
import math
import sys
from pathlib import Path
import bpy
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"blender_factory"))
from hero_hatchback import L,W,H,WB,R,build
import render_v3_recovery as base


def main():
    base.setup()
    build()
    bpy.context.view_layer.update()
    meshes=[ob for ob in bpy.context.scene.objects if ob.type=="MESH"]
    all_objs=[ob for ob in bpy.context.scene.objects if ob.type in ("MESH","CURVE")]
    tires=[ob for ob in meshes if "HERO tire" in ob.name]
    spokes=[ob for ob in all_objs if "six-spoke" in ob.name]
    side=[ob for ob in meshes if "sculpted side" in ob.name]
    roof=[ob for ob in meshes if "crowned roof" in ob.name]
    assert len(tires)==4 and len(spokes)==24
    assert len(side)==2 and len(roof)==1
    assert all("F10_HERO_UV0" in ob.data.uv_layers for ob in side+roof)
    assert sum(len(ob.data.polygons) for ob in meshes)>700
    for ob in tires:
        center=ob.location
        assert abs(abs(center.x)-WB/2)<.01
        assert abs(center.z-R)<.01
    positions=[ob.matrix_world @ Vector(corner) for ob in meshes for corner in ob.bound_box]
    extent=[max(pt[i] for pt in positions)-min(pt[i] for pt in positions) for i in range(3)]
    assert L*.90<extent[0]<L*1.20,extent
    assert W*.90<extent[1]<W*1.38,extent
    assert H*.80<extent[2]<H*1.20,extent
    assert all(math.isfinite(x) for x in extent)
    print("F10_HERO_GEOMETRY_PASS",len(meshes),len(spokes),
          [round(v,3) for v in extent])


if __name__=="__main__":main()
