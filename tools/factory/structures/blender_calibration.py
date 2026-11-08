"""F02 noncanonical building calibration generator; Blender 4.0+ compatible.

Pure validation / plan dry-run:
  python tools/factory/structures/blender_calibration.py --dry-run --subject all

Actual creation:
  python tools/factory/structures/textures.py --output-dir build/f02/textures
  blender -b --factory-startup -t 2 --python \
      tools/factory/structures/blender_calibration.py -- \
      --subject all --output-dir build/f02

Never consume candidate IDs as canonical asset IDs. Requires A00 handoff before
production promotion; no Godot integration is performed here.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import hashlib
import json
import math
import sys

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from geometry import SUBJECTS, make_plan  # noqa: E402


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--subject", choices=(*SUBJECTS, "all"), default="all")
    p.add_argument("--output-dir", type=Path, default=Path("build/f02_calibration"))
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--resume", action="store_true")
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--ids", help="Canonical ID list: blocked until A00 verified snapshot")
    p.add_argument("--batch-manifest", type=Path,
                   help="Canonical work orders: blocked until A00 verified snapshot")
    a = p.parse_args(argv)
    if a.ids or a.batch_manifest:
        p.error("BLOCKED_CANONICAL_IDS: production requires verified A00 snapshot")
    return a


def build_materials(bpy, texture_dir: Path):
    from textures import PALETTE
    mats = {}
    for name, (color, roughness, metallic) in PALETTE.items():
        mat = bpy.data.materials.new(name=f"F02_CAL_{name}")
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        shader = nodes.get("Principled BSDF")
        shader.inputs["Roughness"].default_value = roughness
        shader.inputs["Metallic"].default_value = metallic
        shader.inputs["Base Color"].default_value = (*(c / 255 for c in color), 1)
        if name == "glass":
            if "Transmission Weight" in shader.inputs:
                shader.inputs["Transmission Weight"].default_value = .48
            elif "Transmission" in shader.inputs:
                shader.inputs["Transmission"].default_value = .48
            shader.inputs["Alpha"].default_value = .75
            mat.blend_method = "BLEND"
        path = texture_dir / f"{name}_basecolor.png"
        if path.is_file():
            tex = nodes.new("ShaderNodeTexImage")
            tex.image = bpy.data.images.load(str(path.resolve()), check_existing=True)
            mat.node_tree.links.new(tex.outputs["Color"], shader.inputs["Base Color"])
        mats[name] = mat
    return mats


def make_scene(bpy, plan, texture_dir):
    from mathutils import Vector
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    bpy.context.scene.frame_set(1)
    mats = build_materials(bpy, texture_dir)
    groups = {"roof": [], "door_leaf": [], "window_leaf": [], "garage_gate": []}
    for part in plan.parts:
        bpy.ops.mesh.primitive_cube_add(size=1, location=part.center)
        obj = bpy.context.object
        obj.name = part.name
        obj.dimensions = part.size
        obj.rotation_euler = part.rotation
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        obj.data.materials.append(mats[part.material])
        obj["f02_role"] = part.role
        obj["f02_group"] = part.group
        obj["f02_status"] = "NONCANONICAL_CALIBRATION_ONLY"
        if part.group in groups:
            groups[part.group].append((obj, part))
    for group in ("door_leaf", "window_leaf"):
        transformed = []
        for obj, part in groups[group]:
            axis = "y" if "_y_" in part.name else "x"
            cx, cy, _ = part.center
            offset = (part.size[1] if axis == "y" else part.size[0]) / 2
            pivot_at = (cx, cy - offset, 0) if axis == "y" else (cx - offset, cy, 0)
            pivot = bpy.data.objects.new(f"{part.name}_HINGE", None)
            bpy.context.collection.objects.link(pivot)
            pivot.location = pivot_at
            bpy.context.view_layer.update()
            world = obj.matrix_world.copy()
            obj.parent = pivot
            obj.matrix_world = world
            transformed.append((pivot, obj))
        groups[group] = transformed

    w, h = plan.footprint
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE" if bpy.app.version < (4, 2, 0) else "BLENDER_EEVEE_NEXT"
    scene.render.resolution_x = 640
    scene.render.resolution_y = 512
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = True
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "Medium High Contrast"
    scene.world.color = (.23, .25, .26)
    bpy.ops.object.camera_add()
    camera = bpy.context.object
    camera.name = "F02_F12_CAL_ORTHO_2TO1"
    camera.data.type = "ORTHO"
    # 56.5685 logical px/m yields (40,20) axis projected deltas at 30° elevation.
    camera.data.ortho_scale = 512 / math.sqrt(3200)
    target = Vector((w/2, h/2, 1.35))
    camera.location = target + Vector((9, -9, 12.727922 * math.tan(math.pi/6)))
    camera.rotation_euler = (target - camera.location).to_track_quat("-Z", "Y").to_euler()
    scene.camera = camera
    bpy.ops.object.light_add(type="AREA", location=(w/2-4, h/2-5, 8))
    light = bpy.context.object
    light.name = "F02_KEY_SCREEN_UPPER_LEFT"
    light.data.energy = 650
    light.data.shape = "DISK"
    light.data.size = 5
    light.rotation_euler = (target - light.location).to_track_quat("-Z", "Y").to_euler()
    return groups


def sha(path: Path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def render_frames(bpy, plan, groups, directory):
    from mathutils import Vector
    from bpy_extras.object_utils import world_to_camera_view
    scene = bpy.context.scene
    recorded = []
    def render(name, duration_ms=None):
        path = directory / f"{name}.png"
        scene.render.filepath = str(path.resolve())
        bpy.ops.render.render(write_still=True)
        pivot = world_to_camera_view(scene, scene.camera, Vector((0, 0, 0)))
        recorded.append({"file": path.name, "sha256": sha(path),
                         "size_px": [640, 512],
                         "ground_origin_anchor_px": [round(pivot.x*640, 3),
                                                      round((1-pivot.y)*512, 3)],
                         "duration_ms": duration_ms})
    render("roof_on")
    for obj, _ in groups["roof"]:
        obj.hide_render = True
    render("roof_cut")
    # Opening clips are candidate VISUAL ONLY: W05/W07 own collision/LOS events.
    if plan.subject == "door_window":
        for idx in range(7):
            for rig, _ in groups["door_leaf"]:
                rig.rotation_euler.z = -math.pi/2 * (idx/6)
            render(f"door_open_{idx:02}", 75)
        for rig, _ in groups["door_leaf"]:
            rig.rotation_euler.z = 0
        for idx in range(5):
            for rig, _ in groups["window_leaf"]:
                rig.rotation_euler.z = -math.pi/2 * (idx/4)
            render(f"window_open_{idx:02}", 80)
    return recorded


def produce_one(bpy, subject, output_dir):
    plan = make_plan(subject)
    target = output_dir / subject
    target.mkdir(parents=True, exist_ok=True)
    groups = make_scene(bpy, plan, output_dir / "textures")
    source = target / f"{subject}_calibration.blend"
    # Save editable source BEFORE render-only cutaway and animation states.
    bpy.ops.wm.save_as_mainfile(filepath=str(source.resolve()))
    interchange = target / f"{subject}_calibration.glb"
    bpy.ops.export_scene.gltf(filepath=str(interchange.resolve()),
                              export_format="GLB", export_cameras=False,
                              export_lights=False)
    rendered = render_frames(bpy, plan, groups, target)
    manifest = plan.manifest()
    manifest["blender_version"] = bpy.app.version_string
    manifest["sources"] = {"blend": {"file": source.name, "sha256": sha(source)},
                           "glb": {"file": interchange.name, "sha256": sha(interchange)}}
    manifest["frames"] = rendered
    manifest["generator_sha256"] = sha(Path(__file__))
    (target / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"F02_CALIBRATION_GENERATED {subject} {len(plan.parts)} parts {len(rendered)} frames", flush=True)
    return manifest


def main():
    a = parse_args()
    subjects = SUBJECTS if a.subject == "all" else (a.subject,)
    plans = [make_plan(subject).manifest() for subject in subjects]
    if a.dry_run:
        for m in plans:
            print(json.dumps({"subject": m["subject"],
                              "status": m["status"],
                              "part_count": len(m["parts"]),
                              "plan_sha256": m["geometry_plan_sha256"],
                              "opening_count": len(m["openings"])}, sort_keys=True))
        print("F02_CALIBRATION_DRY_RUN_PASS", len(subjects))
        return
    try:
        import bpy
    except ImportError as exc:
        raise RuntimeError("BLENDER_RUNTIME_REQUIRED; only --dry-run works outside Blender") from exc
    a.output_dir.mkdir(parents=True, exist_ok=True)
    reports = []
    for subject in subjects:
        if a.resume and (a.output_dir / subject / "manifest.json").is_file():
            reports.append(json.loads((a.output_dir / subject / "manifest.json").read_text()))
            continue
        reports.append(produce_one(bpy, subject, a.output_dir))
    summary = {"status": "NONCANONICAL_CALIBRATION_ONLY",
               "canonical_master_ids": [], "blender_version": bpy.app.version_string,
               "subjects": [{"name": m["subject"], "sha": m["geometry_plan_sha256"],
                             "frame_count": len(m["frames"])} for m in reports]}
    (a.output_dir / "run_report.json").write_text(json.dumps(summary, indent=2)+"\n")
    print("F02_BLENDER_CALIBRATION_PASS", len(reports), flush=True)


if __name__ == "__main__":
    main()
