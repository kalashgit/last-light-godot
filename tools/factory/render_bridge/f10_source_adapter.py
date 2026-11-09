"""F12 adapter for the ACTUAL F10 procedural hatchback source tree.

Source must be a read-only checkout of F10's authored branch. Does not replace
or approve F10 assets; generates a temporary .blend for cross-worker QA.
"""
import argparse
import json
import sys
from pathlib import Path
import bpy

def run(source_root, output):
    src = source_root.resolve(strict=True)
    generator = src / "tools" / "vehicle_factory" / "hero_hatchback.py"
    if not generator.is_file():
        raise FileNotFoundError("F10 hero_hatchback.py not found in source checkout")
    sys.path.insert(0, str(generator.parent))
    sys.path.insert(0, str(src / "tools" / "blender_factory"))
    import render_v3_recovery as base
    from hero_hatchback import build
    scene = base.setup()
    build()
    bpy.context.view_layer.update()
    root=bpy.data.objects.new("F12_F10_HERO_ROOT_QA_ONLY", None)
    scene.collection.objects.link(root)
    geometries=[]
    for ob in list(scene.objects):
        if ob.type not in ("MESH", "CURVE"):
            continue
        # Keep the original source geometry and all world transforms intact.
        world=ob.matrix_world.copy()
        ob.parent=root
        ob.matrix_world=world
        geometries.append(ob.name)
    if not any(bpy.data.objects[name].type=="MESH" for name in geometries):
        raise ValueError("F10 generator produced no mesh")
    if root.location.length>1e-7:
        raise AssertionError("F12 source root not grounded")
    output.parent.mkdir(parents=True,exist_ok=True)
    if output.exists():
        raise FileExistsError(str(output))
    bpy.ops.wm.save_as_mainfile(filepath=str(output))
    report={"status":"F10_PROCEDURAL_SOURCE_NOT_A00_APPROVED",
            "source_script":"tools/vehicle_factory/hero_hatchback.py",
            "blender_object_root":root.name,"geometry_count":len(geometries),
            "mesh_count":sum(bpy.data.objects[n].type=="MESH" for n in geometries),
            "source_checkout_path":str(src),
            "approval":"CALIBRATION_ONLY_NO_GOLDEN"}
    (output.parent/"f10_source_audit.json").write_text(json.dumps(report,indent=2)+"\n")
    print("F12_F10_SOURCE_ADAPTER_PASS",len(geometries),flush=True)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source-root",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    args=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    a=p.parse_args(args)
    run(a.source_root,a.output)

if __name__=="__main__":
    main()
