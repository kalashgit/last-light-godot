"""Blender-only source geometry/material evidence for one admitted original GLB.

Records actual editable-source geometry rather than guessing quality from a
contact sheet. Does NOT award F11 PBR or founder approval.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import bpy
from mathutils import Vector


def audit(plan: dict, output: Path) -> dict:
    if plan.get("schema_version") != 1 or plan.get("golden_approved") is not False:
        raise ValueError("Untrusted controlled Blender plan")
    rows = []
    for asset in plan["selected"]:
        path = Path(asset["glb_path"])
        data = path.read_bytes()
        if hashlib.sha256(data).hexdigest() != asset["glb_sha256"]:
            raise ValueError("Source changed after Notion admission")
        bpy.ops.wm.read_factory_settings(use_empty=True)
        bpy.ops.import_scene.gltf(filepath=str(path.resolve()))
        objects = [o for o in bpy.context.scene.objects if o.type == "MESH"]
        if not objects:
            raise ValueError("No editable geometry detected")
        bpy.context.view_layer.update()
        corners = [o.matrix_world @ Vector(corner) for o in objects for corner in o.bound_box]
        low = [min(v[i] for v in corners) for i in range(3)]
        high = [max(v[i] for v in corners) for i in range(3)]
        dims = [high[i] - low[i] for i in range(3)]
        material_names = sorted({mat.name for o in objects for mat in o.data.materials if mat})
        texture_nodes = sum(1 for mat in bpy.data.materials if mat and mat.use_nodes
                            for node in mat.node_tree.nodes if node.type == "TEX_IMAGE")
        rec = {
            "asset_id": asset["asset_id"], "source_glb_sha256": asset["glb_sha256"],
            "mesh_count": len(objects),
            "vertex_count": sum(len(o.data.vertices) for o in objects),
            "triangle_count": sum(sum(max(0, len(p.vertices) - 2) for p in o.data.polygons)
                                  for o in objects),
            "material_count": len(material_names),
            "material_names": material_names,
            "image_texture_nodes": texture_nodes,
            "dimensions_m": dims,
            "geometry_present": True,
            "pbr_material_quality_verified": False,
            "originality_final_review_required": True,
            "golden_approved": False,
        }
        if rec["vertex_count"] < 8 or not all(0.02 < d < 100 for d in dims):
            raise ValueError("Implausible source mesh bounds or count")
        rows.append(rec)
    report = {"schema_version": 1, "source_plan_sha256": plan["source_plan_sha256"],
              "objects": rows, "f11_material_approved": False, "golden_approved": False}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n")
    return report


def main() -> None:
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--plan", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args(argv)
    result = audit(json.loads(a.plan.read_text()), a.output)
    print("FOUNDRY_BLENDER_AUDIT", len(result["objects"]))


if __name__ == "__main__":
    main()
