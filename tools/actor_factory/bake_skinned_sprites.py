"""LAST LIGHT F05: bake *existing skinned Blender armature* into 2D layers.

This is intentionally NOT a separate procedural per-frame modeler. It loads
the F05 .blend master, samples its NLA clips on one skeleton, renders body and
each skinned clothing mesh independently from eight locked camera headings,
and emits the PR103 offline atlas bridge's exact source contract.

blender -b --factory-startup -t 2 --python tools/actor_factory/bake_skinned_sprites.py -- \
  --source build/f05-cal/f05_noncanonical_calibration.blend \
  --source-glb build/f05-cal/f05_noncanonical_calibration.glb \
  --output build/f05-skinned-bake

All assets remain non-Golden and calibration-only. No paid model calls.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import shutil
import sys

import bpy
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

CANVAS = (128, 160)
DIRECTIONS = ("front", "front_right", "right", "back_right", "back",
              "back_left", "left", "front_left")
# These are stable cardinal/diagonal views of the SAME rig and garment meshes.
ANGLES = (0, 45, 90, 135, 180, 225, 270, 315)
SAMPLES = {"idle": (1, 3), "walk": (1, 3, 5, 7)}
FPS = {"idle": 6.0, "walk": 8.0}
# Each entry is one separately swappable, original, armature-skinned layer.
GROUPS = {
    ("body", "base"): (
        "torso skin", "underwear actual geometry", "head", "hair cap test",
        "arm_skin_L", "arm_skin_R", "leg_skin_L", "leg_skin_R",
        "hand L", "hand R", "foot L", "foot R",
    ),
    ("pants", "calibration_pants"): (
        "wearable_pants_L", "wearable_pants_R", "wearable_waist_band",
    ),
    ("shirt", "calibration_shirt"): (
        "wearable_shirt_body", "wearable_shirt_collar",
        "wearable_shirt_sleeve_L", "wearable_shirt_sleeve_R",
    ),
    ("backpack", "calibration_pack"): ("backpack test",),
    ("effects", "calibration_tool"): ("held tool proxy",),
}


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def check_source(rig):
    if rig is None or rig.type != "ARMATURE":
        raise ValueError("F05 must load a real Blender Armature")
    names = set(rig.data.bones.keys())
    necessary = {"root", "pelvis", "chest", "head",
                 "upper_arm_L", "forearm_L", "thigh_L", "shin_L",
                 "upper_arm_R", "forearm_R", "thigh_R", "shin_R"}
    if not necessary.issubset(names):
        raise ValueError("missing canonical calibration skeleton bones")
    tracks = {track.name: track for track in rig.animation_data.nla_tracks}
    for clip in SAMPLES:
        if "F05_CAL_" + clip not in tracks:
            raise ValueError("missing F05 NLA source action " + clip)
    members = {}
    for key, names in GROUPS.items():
        for name in names:
            ob = bpy.data.objects.get(name)
            if ob is None or ob.type != "MESH":
                raise ValueError("missing actual original garment/body mesh: " + name)
            if ob.parent != rig:
                raise ValueError("mesh not parented to shared rig: " + name)
            arm_mods = [m for m in ob.modifiers if m.type == "ARMATURE" and m.object == rig]
            if not arm_mods:
                raise ValueError("mesh not skinned to rig: " + name)
            if not ob.vertex_groups:
                raise ValueError("mesh has no bone weights: " + name)
            if any(name in group for group in members.values()):
                raise ValueError("mesh belongs to two independent sprite layers")
        members[key] = list(names)
    return tracks, members


def set_clip(tracks, clip):
    name = "F05_CAL_" + clip
    for track_name, track in tracks.items():
        track.mute = track_name != name


def prepare_camera(scene):
    # Camera orbits around the skeleton, never rotating or rebuilding the rig.
    cam = scene.camera
    if cam is None or cam.type != "CAMERA":
        raise ValueError("Blender rig source needs a real camera")
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = 2.75
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x, scene.render.resolution_y = CANVAS
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = True
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.image_settings.color_depth = "8"
    scene.view_settings.view_transform = "Standard"
    scene.render.image_settings.compression = 15
    return cam


def point_camera(cam, heading):
    target = Vector((0.0, 0.0, 0.90))
    theta = math.radians(heading - 90)
    radius = 4.0
    cam.location = Vector((radius * math.cos(theta),
                           radius * math.sin(theta),
                           target.z + radius * math.tan(math.radians(30))))
    cam.rotation_euler = (target - cam.location).to_track_quat("-Z", "Y").to_euler()


def verify_deformation(scene, tracks):
    # Show that the very SAME mesh changes with NLA pose, not regenerated mesh.
    ob = bpy.data.objects["arm_skin_L"]
    set_clip(tracks, "walk")
    samples = []
    for frame in (1, 3):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        dg = bpy.context.evaluated_depsgraph_get()
        evaluated = ob.evaluated_get(dg)
        mesh = evaluated.to_mesh()
        try:
            samples.append(tuple(round((evaluated.matrix_world @ mesh.vertices[i].co)[j], 5)
                                 for i in range(min(12, len(mesh.vertices))) for j in range(3)))
        finally:
            evaluated.to_mesh_clear()
    if samples[0] == samples[1]:
        raise ValueError("NLA did not actually deform the shared weighted mesh")
    return True


def main():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--source-glb", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    a = parser.parse_args(args)
    source, glb, output = a.source.resolve(), a.source_glb.resolve(), a.output.resolve()
    if not source.is_file() or not glb.is_file():
        raise ValueError("source .blend and original skinned .glb required")
    if output.exists() and any(output.iterdir()):
        raise ValueError("refusing to overwrite previously generated assets")
    output.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.open_mainfile(filepath=str(source))
    rig = bpy.data.objects.get("F05_TEST_RIG")
    tracks, members = check_source(rig)
    scene = bpy.context.scene
    cam = prepare_camera(scene)
    verify_deformation(scene, tracks)
    source_dir = output / "editable"
    source_dir.mkdir()
    shutil.copyfile(source, source_dir / "skinned_master.blend")
    shutil.copyfile(glb, source_dir / "skinned_master.glb")
    source_hash = digest(source_dir / "skinned_master.blend")
    glb_hash = digest(source_dir / "skinned_master.glb")

    meshes = {ob.name: ob for ob in bpy.data.objects if ob.type == "MESH"}
    records = []
    for clip, frames in SAMPLES.items():
        set_clip(tracks, clip)
        for idx, pose_frame in enumerate(frames):
            scene.frame_set(pose_frame)
            for name, degrees in zip(DIRECTIONS, ANGLES):
                point_camera(cam, degrees)
                bpy.context.view_layer.update()
                for (slot, item), names in members.items():
                    visible = set(names)
                    for obj_name, ob in meshes.items():
                        ob.hide_render = obj_name not in visible
                    relative = f"frames/{slot}_{item}_{clip}_{name}_{idx:02}.png"
                    file = output / relative
                    file.parent.mkdir(exist_ok=True)
                    scene.render.filepath = str(file)
                    bpy.ops.render.render(write_still=True)
                    if not file.is_file() or file.stat().st_size < 64:
                        raise RuntimeError("Blender render missing " + relative)
                    records.append({"slot": slot, "item_id": item,
                                    "animation": clip, "direction": name, "frame": idx,
                                    "file": relative, "sha256": digest(file)})
        print("LL_SKINNED_NLA_BAKED", clip, len(frames), flush=True)
    point_camera(cam, 0)
    bpy.context.view_layer.update()
    pivot_ndc = world_to_camera_view(scene, cam, Vector((0, 0, 0)))
    pivot = [round(CANVAS[0] * pivot_ndc.x),
             round(CANVAS[1] * (1-pivot_ndc.y))]
    if not 0 <= pivot[0] <= CANVAS[0] or not 0 <= pivot[1] <= CANVAS[1]:
        raise ValueError("shared world-foot pivot outside frame")
    manifest = {
        "schema": "last-light.paperdoll.frames.v1",
        "asset_id": "ll_f05_skinned_calibration_candidate",
        "rig": "ll_biped_v1",
        "tile_px": [80, 40],
        "frame_size": list(CANVAS),
        "pivot": pivot,
        "golden_approved": False,
        "directions": list(DIRECTIONS),
        "animations": {clip: {"frames": len(frames), "fps": FPS[clip], "loop": True}
                       for clip, frames in SAMPLES.items()},
        "frames": records,
        "provenance": {
            "source_system": "single_shared_blender_armature_nla",
            "source_blend": "editable/skinned_master.blend",
            "source_blend_sha256": source_hash,
            "source_glb": "editable/skinned_master.glb",
            "source_glb_sha256": glb_hash,
            "armature_object": rig.name,
            "armature_bones": len(rig.data.bones),
            "source_meshes": {slot + "/" + item: names
                              for (slot, item), names in members.items()},
            "sampled_nla_frames": {clip: list(frames) for clip, frames in SAMPLES.items()},
            "confirmed_live_skin_deformation": True,
            "status": "CALIBRATION_ONLY_NOT_GOLDEN",
            "source_rights": "original_procedural_F05"
        }
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print("LL_SKINNED_SOURCE_BAKE_COMPLETE", len(records), "RGBA frames",
          len(members), "skinned layers", "bones", len(rig.data.bones),
          "pivot", pivot, flush=True)


if __name__ == "__main__":
    main()
