"""Headless F09 source geometry QA only: no sprite/render/approval."""
import hashlib
import json
import sys
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "weapons_tools"))
import build as factory
from f09_v4_detail import refine

TARGETS = {
    "ll_tools_hand_saw": ("saw", ("integral teeth", "wooden thumb cheek")),
    "ll_tools_adjustable_wrench": ("wrench", ("worm adjustment", "adjustable sliding jaw")),
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
    out = directory / item["asset_id"]
    out.mkdir(parents=True, exist_ok=True)
    blend_path = out / "source_geometry.blend"
    glb_path = out / "source_geometry.glb"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path.resolve()))
    factory.glb(glb_path, objects)
    assert blend_path.read_bytes()[:7] == b"BLENDER"
    assert glb_path.read_bytes()[:4] == b"glTF"
    result = {"source_asset_id": item["asset_id"], "parts": len(objects),
              "measured_bounds_m": bounds,
              "blend_sha256": hashlib.sha256(blend_path.read_bytes()).hexdigest(),
              "glb_sha256": hashlib.sha256(glb_path.read_bytes()).hexdigest(),
              "status": "GEOMETRY_EXPORT_SMOKE_TEST_ONLY"}
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
