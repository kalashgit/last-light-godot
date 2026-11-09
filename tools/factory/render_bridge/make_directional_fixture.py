"""Create a small NONCANONICAL vehicle-like CAL-02 fixture in Blender.

This is a render-pipeline smoke test, NOT the F10 hatchback or a catalog asset.
Run: blender -b --factory-startup --python make_directional_fixture.py -- --output /tmp/fixture.blend
"""
import argparse
import sys
from pathlib import Path
import bpy

def block(name, location, scale, material, parent):
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    obj=bpy.context.object
    obj.name=name
    obj.dimensions=scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(material)
    obj.parent=parent
    obj.matrix_parent_inverse=parent.matrix_world.inverted()
    return obj

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--output",required=True,type=Path)
    args=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    opts=p.parse_args(args)
    out=opts.output.resolve()
    if not out.parent.exists() or out.exists():
        raise ValueError("output parent must exist and file must be new")
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    root=bpy.data.objects.new("CAL02_ONLY_Root",None)
    bpy.context.scene.collection.objects.link(root)
    def mat(name,rgb):
        m=bpy.data.materials.new(name)
        m.diffuse_color=(*rgb,1)
        m.use_nodes=True
        m.node_tree.nodes.get("Principled BSDF").inputs["Base Color"].default_value=(*rgb,1)
        return m
    body=mat("CAL_ONLY_orange",(0.72,0.22,0.07))
    roof=mat("CAL_ONLY_dark_roof",(0.1,0.16,0.20))
    marker=mat("CAL_ONLY_orientation_marker",(0.92,0.85,0.09))
    # Asymmetric fixture lets QA visually distinguish front/rear, not production car art.
    block("CAL02_body",(0,0,0.46),(2.0,1.05,0.52),body,root)
    block("CAL02_roof",(-0.16,0,0.85),(0.9,0.84,0.3),roof,root)
    block("CAL02_front_marker",(0.83,-0.28,0.77),(0.18,0.26,0.10),marker,root)
    lamp=bpy.data.lights.new("CAL02_fixed_upper_left_key","AREA")
    lamp.energy=650
    lamp.shape="DISK"
    lamp.size=4
    obj=bpy.data.objects.new(lamp.name,lamp)
    bpy.context.scene.collection.objects.link(obj)
    obj.location=(-3,2,7)
    bpy.context.scene.world.color=(0.20,0.20,0.20)
    bpy.ops.wm.save_as_mainfile(filepath=str(out))
    print("F12_NONCANONICAL_DIRECTIONAL_FIXTURE_SAVED",str(out),flush=True)

if __name__=="__main__":
    main()
