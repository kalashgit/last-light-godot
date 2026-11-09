"""Headless F09 source geometry QA only: no sprite/render/approval."""
import hashlib
import json
import sys
from pathlib import Path

import bpy
import bmesh

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "weapons_tools"))
import build as factory
from f09_v4_detail import refine

TARGETS = {
    "ll_tools_hand_saw": ("saw", ("integral teeth", "shaped hardwood cheek")),
    "ll_tools_adjustable_wrench": ("wrench", ("worm-wheel steel knurled barrel", "translating lower jaw")),
    "ll_tools_socket_handle": ("ratchet", ("reversing lever", "quick release")),
}

def check(item, directory):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    mats = factory.material_set()
    from f09_v6_materials import refine_materials
    refine_materials(mats)
    from f09_v5_models import build as build_v5
    build_v5(item["archetype"], mats, form=factory.form, tube=factory.tube,
             grip=factory.grip, closed_sweep=factory.closed_sweep,
             small_pin=factory.small_pin, hoop=factory.hoop)
    bpy.context.view_layer.update()
    objects = factory.models()
    names = [ob.name.lower() for ob in objects]
    for required in TARGETS[item["asset_id"]][1]:
        assert any(required in name for name in names), (item["asset_id"], required)
    assert len(objects) >= 7, (item["asset_id"], len(objects))
    bounds = factory.measured_bounds(objects)
    for measured, specified in zip(bounds, item["dimensions_m"]):
        assert .005 <= measured <= specified * 1.55, (item["asset_id"], bounds)
    assert all(ob.data.materials for ob in objects if ob.type == "MESH"), item["asset_id"]
    assert all(ob.type != "MESH" or len(ob.data.polygons) > 0 for ob in objects)
    if item["archetype"] == "saw":
        handles=[o for o in objects if "V9 solid wooden D grip" in o.name]
        assert len(handles)==1, "missing actual solid through-cut grip"
        assert len(handles[0].data.vertices) == 160, "saw grip was not profile-smoothed"
        bm=bmesh.new()
        bm.from_mesh(handles[0].data)
        assert bm.verts and all(edge.is_manifold for edge in bm.edges), "grip non-manifold"
        # Closed ring with one through-aperture has genus 1 / Euler characteristic 0.
        assert len(bm.verts)-len(bm.edges)+len(bm.faces)==0, "grip opening not real"
        bm.free()
    elif item["archetype"]=="wrench":
        assert any("v15 fixed crescent upper jaw" in n for n in names) and any(
            "v15 translating lower jaw" in n for n in names), "wrench lost separate jaws"
        fixed=[o for o in objects if "v11 fixed upper polished jaw flat" in o.name.lower()]
        moving=[o for o in objects if "v11 moving lower polished jaw flat" in o.name.lower()]
        assert len(fixed)==len(moving)==1, "opposing machined flats missing"
        # In the head XY plane, jaw opening must be physically clear rather
        # than two coincident/crossed shapes that only look separate in renders.
        upper_min=min(v.co.y for v in fixed[0].data.vertices)
        lower_max=max(v.co.y for v in moving[0].data.vertices)
        jaw_gap_m=upper_min-lower_max
        assert .014 <= jaw_gap_m <= .040, ("invalid wrench jaw aperture",jaw_gap_m)
        fixed_jaw=[o for o in objects if "v15 fixed crescent upper jaw" in o.name.lower()][0]
        # Slimmer forge must not turn the stationary head into a bulky 100 mm casting.
        assert max(v.co.y for v in fixed_jaw.data.vertices) <= .173, "fixed jaw grew oversized"
        tapered=[o for o in objects if o.get("F09_VARIABLE_JAW_THICKNESS") is True]
        assert len(tapered)==2, "both jaws must be authored as 3D forging lofts"
        for jaw in tapered:
            thickness=jaw.get("F09_THICKNESS_RANGE_M")
            assert thickness and thickness[1]-thickness[0] >= .005, (
                "fake slab instead of tapered jaw",jaw.name,thickness)
            mesh=jaw.data
            bm=bmesh.new()
            bm.from_mesh(mesh)
            assert all(edge.is_manifold for edge in bm.edges), "nonmanifold jaw"
            bm.free()
        handles=[ob for ob in objects if ob.get("F09_TRUE_THROUGH_HOLE") is True]
        assert len(handles)==1, "missing editable wrench through-drilled handle"
        # An actual drilled hole must transmit a ray, while adjacent handle
        # steel still blocks it. This rejects a painted or torus-only fake.
        hole_mesh=handles[0]
        empty=hole_mesh.ray_cast((0,-.117,.10),(0,0,-1))[0]
        solid=hole_mesh.ray_cast((.008,-.117,.10),(0,0,-1))[0]
        assert not empty and solid, "wrench hanging eye is not a real cutout"
    out = directory / item["asset_id"]
    out.mkdir(parents=True, exist_ok=True)
    blend_path = out / "source_geometry.blend"
    glb_path = out / "source_geometry.glb"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path.resolve()))
    from f09_glb_material_bridge import export_with_preview, inspect_glb_preview
    export_with_preview(factory.glb, glb_path, objects)
    preview_materials = inspect_glb_preview(glb_path)
    assert blend_path.read_bytes()[:7] == b"BLENDER"
    assert glb_path.read_bytes()[:4] == b"glTF"
    result = {"source_asset_id": item["asset_id"], "parts": len(objects),
              "measured_bounds_m": bounds,
              "blend_sha256": hashlib.sha256(blend_path.read_bytes()).hexdigest(),
              "glb_sha256": hashlib.sha256(glb_path.read_bytes()).hexdigest(),
              "status": "GEOMETRY_EXPORT_SMOKE_TEST_ONLY",
              "material_preview": preview_materials}
    (out / "geometry_qa.json").write_text(json.dumps(result, indent=2) + "\n")
    print("F09_V4_GEOMETRY_QA_PASS", result, flush=True)

def main():
    recipes = json.loads(factory.RECIPE_FILE.read_text())
    directory = ROOT / "build" / "f09_v4_geometry_smoke"
    for item in recipes["assets"]:
        if item["asset_id"] in TARGETS:
            assert item["archetype"] == TARGETS[item["asset_id"]][0]
            check(item, directory)

if __name__ == "__main__":
    main()
