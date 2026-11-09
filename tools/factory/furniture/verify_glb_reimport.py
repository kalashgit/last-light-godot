"""Independently reopen F01 GLBs in Blender and validate real mesh dimensions.

blender -b --factory-startup --python tools/factory/furniture/verify_glb_reimport.py -- <glb> [<glb> ...]
"""
import json
import sys
from pathlib import Path

system_extensions=Path(f"/usr/lib/python{sys.version_info.major}.{sys.version_info.minor}/lib-dynload")
runtime_sites=Path(f"/opt/codex/runtimes/codex-primary-runtime/dependencies/python/lib/python{sys.version_info.major}.{sys.version_info.minor}/site-packages")
for directory in (system_extensions,runtime_sites):
    if directory.is_dir() and str(directory) not in sys.path:sys.path.append(str(directory))

import bpy


def main():
    paths=[Path(p).resolve() for p in sys.argv[sys.argv.index("--")+1:]]
    if not paths:raise SystemExit("Provide at least one GLB")
    reports=[]
    for path in paths:
        bpy.ops.object.select_all(action="SELECT")
        bpy.ops.object.delete(use_global=False)
        bpy.ops.import_scene.gltf(filepath=str(path))
        mesh=[o for o in bpy.context.scene.objects if o.type=="MESH"]
        hinges=[o for o in bpy.context.scene.objects if "hinge_local.main_door" in o.name]
        actions=list(bpy.data.actions)
        verts=sum(len(o.data.vertices) for o in mesh)
        assert mesh and verts>50,(path,verts)
        assert all(o.dimensions.length>0 for o in mesh),(path,"empty object")
        if any(tag in str(path) for tag in ("refrigerator_v6","refrigerator_v8","refrigerator_v9")):
            assert hinges,(path,"hinge pivot not imported")
            assert actions,(path,"hinge action not imported")
        crisper=[o for o in bpy.context.scene.objects if "slide_local.crisper_drawer" in o.name]
        if "refrigerator_v8" in str(path) or "refrigerator_v9" in str(path):
            assert crisper,(path,"crisper sliding origin not imported")
            assert sum(o.parent==crisper[0] and o.type=="MESH" for o in bpy.context.scene.objects)==7
        reports.append({"file":path.name,"mesh_count":len(mesh),"vertex_count":verts,
                        "hinge_pivot_count":len(hinges),"crisper_pivot_count":len(crisper),
                        "imported_action_count":len(actions),
                        "status":"GLB_REIMPORT_GEOMETRY_PASS"})
    print("F01_GLTF_REIMPORT_PASS",json.dumps(reports),flush=True)


if __name__=="__main__":main()
