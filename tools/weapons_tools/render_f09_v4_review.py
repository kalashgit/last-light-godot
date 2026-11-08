"""Isolated F09 V4 visual candidate renders for review, not F12 sprite production."""
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Matrix

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "weapons_tools"))
import build as factory
from f09_v4_detail import refine

TARGETS = {"ll_tools_hand_saw", "ll_tools_adjustable_wrench", "ll_tools_socket_handle"}
OUT = ROOT / "build" / "f09_v4_visual_review"

def render_png(scene, path, *, scale, samples):
    scene.camera.data.ortho_scale = scale
    scene.render.resolution_x = 384
    scene.render.resolution_y = 384
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = True
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.filepath = str(path.resolve())
    scene.cycles.samples = samples
    bpy.ops.render.render(write_still=True)
    assert path.exists() and path.stat().st_size > 1000, path

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    recipes = json.loads(factory.RECIPE_FILE.read_text())
    report = []
    for item in recipes["assets"]:
        if item["asset_id"] not in TARGETS:
            continue
        scene = factory.hero.setup()
        mats = factory.material_set()
        factory.construction(item, mats)
        refine(item["archetype"], mats, form=factory.form,
               tube=factory.tube, small_pin=factory.small_pin,
               curved_bar=factory.curved_bar)
        bpy.context.view_layer.update()
        objects = factory.models()
        transforms = {o.name: o.matrix_world.copy() for o in objects}
        folder = OUT / item["asset_id"]
        folder.mkdir(exist_ok=True)
        outputs = []
        for heading in (0, 1, 2, 3):
            rotation = Matrix.Rotation(math.tau * heading / 4, 4, "Z")
            for ob in objects:
                ob.matrix_world = rotation @ transforms[ob.name]
            bpy.context.view_layer.update()
            name = "review_heading_%02d.png" % heading
            render_png(scene, folder / name, scale=factory.hero.ORTHO, samples=4)
            outputs.append(name)
        for ob in objects:
            ob.matrix_world = transforms[ob.name]
        bpy.context.view_layer.update()
        render_png(scene, folder / "review_icon.png",
                   scale=max(.36, item["dimensions_m"][1] * 1.55), samples=4)
        outputs.append("review_icon.png")
        report.append({"source_asset_id": item["asset_id"],
                       "outputs": outputs, "resolution_px": [384, 384],
                       "status": "NON_APPROVED_VISUAL_QA_RENDER"})
        print("F09_V4_VISUAL_RENDER_PASS", item["asset_id"], len(outputs), flush=True)
    assert len(report) == 3
    (OUT / "render_review_manifest.json").write_text(
        json.dumps({"items": report, "approved": False,
                    "production_sprites": False}, indent=2) + "\n")

if __name__ == "__main__":
    main()
