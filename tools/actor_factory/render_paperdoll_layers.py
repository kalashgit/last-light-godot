"""LAST LIGHT F05/F06 Blender-backed paperdoll source-pass pilot.

Original procedural ll_biped_v1 geometry and F05/F12 camera, not source art.
A complete bounded run emits native .blend, .glb, and per-item RGBA frames.
All appearance variants share frame timing, camera, anchor and viewport.
Intended consumer: the version-pinned offline packer from PR #103.
No image API or Golden promotion.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

import bpy
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "blender_factory"))
sys.path.insert(0, str(ROOT / "tools" / "actor_factory"))
import render_v3_recovery as hero
from actor_state import create_actor, spawn_zombie, ACTOR_RIG, appearance

WIDTH, HEIGHT = 128, 160
FPS = 8
# The headings preserve the native four cardinal orientations and add intermediates.
HEADING_ANGLES = {
    "front": 0, "front_right": 45, "right": 90, "back_right": 135,
    "back": 180, "back_left": 225, "left": 270, "front_left": 315,
}
CLIPS = {"idle": 1, "walk": 3}
LAYERS = [
    ("body", "base"), ("pants", "jeans"), ("shirt", "green_shirt"),
    ("shirt", "blue_shirt"), ("backpack", "pack"),
]


def sha(path):
    value = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            value.update(block)
    return value.hexdigest()


def material(name, rgba, rough=0.85):
    return hero.mat("LL paperdoll " + name, rgba, rough=rough, wear=0.06)


def add(obj, slot, item):
    obj["ll_layer_slot"] = slot
    obj["ll_layer_item"] = item
    obj["ll_rig"] = ACTOR_RIG["id"]
    return obj


def ellipse(name, center, dimensions, mat, slot, item):
    return add(hero.uv(name, center, dimensions, mat), slot, item)


def cube(name, center, dimensions, mat, slot, item, bevel=0.02):
    return add(hero.cube(name, center, dimensions, mat, bevel, 2), slot, item)


def limb(name, a, b, radius, mat, slot, item):
    p, q = Vector(a), Vector(b)
    direction = q - p
    if direction.length < 0.02:
        raise ValueError("degenerate original limb " + name)
    obj = hero.cyl(name, (p + q) * 0.5, radius, direction.length, mat, vertices=12)
    obj.rotation_euler = direction.to_track_quat("Z", "Y").to_euler()
    return add(obj, slot, item)


def mats(kind):
    zombie = kind == "infected"
    return {
        "skin": material("skin", (.40, .44, .34) if zombie else (.61, .46, .35)),
        "hair": material("hair", (.18, .17, .14)),
        "eyes": material("eyes", (.12, .12, .11)),
        "pants": material("denim", (.20, .27, .33)),
        "boots": material("boots", (.21, .17, .14)),
        "green": material("faded green cotton", (.28, .40, .30)),
        "blue": material("dusty blue cotton", (.23, .32, .48)),
        "pack": material("worn canvas", (.32, .27, .19)),
        "strap": material("dark webbing", (.16, .16, .13)),
    }


def build_geometry(actor, clip, frame, settings):
    """All visible meshes are real original Blender geometry, rebuilt from one pose."""
    phase = 2.0 * math.pi * frame / CLIPS[clip]
    lean = .09 if actor["kind"] == "zombie" else .0
    locomotion = .10 if clip == "walk" else 0.0
    step = math.sin(phase) * locomotion
    r = float(actor["height_m"]) / 1.76
    morph = actor.get("body_morph", appearance(actor)["body_morph"])
    broad = .94 + .15 * float(morph["muscle"])
    m = settings

    torso_z = 1.23 * r
    torso_y = .025 + lean
    ellipse("BODY torso", (0, torso_y, torso_z), (.275 * broad, .205, .40*r),
            m["skin"], "body", "base")
    ellipse("BODY pelvis", (0, .01, .92*r), (.255, .20, .23*r),
            m["skin"], "body", "base")
    ellipse("BODY neck", (0, torso_y-.02, 1.51*r), (.105, .10, .19*r),
            m["skin"], "body", "base")
    ellipse("BODY head", (0, torso_y-.02, 1.68*r), (.20*broad, .19, .24*r),
            m["skin"], "body", "base")
    ellipse("BODY hair cap", (0, torso_y+.02, 1.78*r), (.198*broad, .188, .075*r),
            m["hair"], "body", "base")
    for sign in (-1, 1):
        x = sign * .12
        gait = step * sign
        hip = (x, .018, .87*r)
        knee = (x, .03+gait*.72, .51*r)
        ankle = (x, .03+gait, .13*r)
        limb("BODY thigh " + str(sign), hip, knee, .083*broad, m["skin"], "body", "base")
        limb("BODY calf " + str(sign), knee, ankle, .066*broad, m["skin"], "body", "base")
        shoulder = (sign*.235*broad, torso_y, 1.43*r)
        elbow = (sign*.32*broad, torso_y+.03-gait*.40, 1.16*r)
        wrist = (sign*.33*broad, torso_y-.035-gait*.75, .91*r)
        limb("BODY arm " + str(sign), shoulder, elbow, .066, m["skin"], "body", "base")
        limb("BODY forearm " + str(sign), elbow, wrist, .050, m["skin"], "body", "base")
        ellipse("BODY hand " + str(sign), wrist, (.074, .068, .10*r),
                m["skin"], "body", "base")

        # The same gait and anchors drive separately rendered original garment shells.
        limb("PANTS thigh " + str(sign), hip, knee, .100*broad, m["pants"], "pants", "jeans")
        limb("PANTS shin " + str(sign), knee, ankle, .080*broad, m["pants"], "pants", "jeans")
        ellipse("PANTS boot " + str(sign), (x, -.055+gait, .083*r),
                (.14, .26, .13*r), m["boots"], "pants", "jeans")

        for item, key in (("green_shirt", "green"), ("blue_shirt", "blue")):
            limb(item + " sleeve " + str(sign), shoulder, elbow,
                 .084, m[key], "shirt", item)

    ellipse("PANTS waist shell", (0, .012, .92*r), (.285, .233, .245*r),
            m["pants"], "pants", "jeans")
    for item, key in (("green_shirt", "green"), ("blue_shirt", "blue")):
        ellipse(item + " fitted torso", (0, torso_y, torso_z),
                (.299*broad, .228, .42*r), m[key], "shirt", item)
        ellipse(item + " collar", (0, torso_y-.02, 1.48*r),
                (.113, .113, .056*r), m[key], "shirt", item)

    cube("BACKPACK canvas shell", (0, torso_y+.25, 1.25*r),
         (.34, .19, .48*r), m["pack"], "backpack", "pack", bevel=.055)
    for sign in (-1, 1):
        limb("BACKPACK shoulder strap " + str(sign),
             (sign*.12, torso_y-.07, 1.45*r),
             (sign*.12, torso_y-.11, 1.10*r),
             .022, m["strap"], "backpack", "pack")

    objects = [o for o in bpy.context.scene.objects if o.type == "MESH"
               and "ll_layer_slot" in o]
    if len(objects) < 25:
        raise RuntimeError("missing original geometry")
    root = bpy.data.objects.new("LL_BIPED_V1_SHARED_RIG_ROOT", None)
    bpy.context.collection.objects.link(root)
    for obj in objects:
        local_to_world = obj.matrix_world.copy()
        obj.parent = root
        obj.matrix_world = local_to_world
    root["ll_original_procedural"] = True
    root["ll_golden_approved"] = False
    return root, objects


def save_editable_source(scene, root, meshes, path):
    source = path / "editable"
    source.mkdir(parents=True, exist_ok=True)
    bpy.context.preferences.filepaths.save_version = 0
    blend = source / "ll_biped_layered_pilot.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend.resolve()), compress=False)
    bpy.ops.object.select_all(action="DESELECT")
    for mesh in meshes:
        mesh.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    glb = source / "ll_biped_layered_pilot.glb"
    bpy.ops.export_scene.gltf(filepath=str(glb.resolve()), export_format="GLB",
                              use_selection=True, export_yup=True)
    if blend.read_bytes()[:7] != b"BLENDER" or glb.read_bytes()[:4] != b"glTF":
        raise RuntimeError("Blender and GLB signatures missing")
    return {"blend": str(blend.relative_to(path)), "blend_sha256": sha(blend),
            "glb": str(glb.relative_to(path)), "glb_sha256": sha(glb)}


def remove_geometry(root, meshes):
    for mesh in meshes:
        bpy.data.objects.remove(mesh, do_unlink=True)
    bpy.data.objects.remove(root, do_unlink=True)


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--kind", choices=("survivor", "infected"), default="survivor")
    args = parser.parse_args(argv)
    out = args.output.resolve()
    if out.exists() and any(out.iterdir()):
        raise RuntimeError("refusing to overwrite prior source evidence")
    out.mkdir(parents=True, exist_ok=True)

    if args.kind == "survivor":
        actor = create_actor("ll_f05_layered_survivor_candidate", 117, height_m=1.76)
    else:
        actor = spawn_zombie(117, "house_1", "living_room", 0, "residential")
    if actor["kind"] != ("human" if args.kind == "survivor" else "zombie"):
        raise RuntimeError("F05/F06 actor state mismatch")

    scene = hero.setup()
    scene.camera.data.ortho_scale = 2.65
    scene.camera.location.z += .86
    scene.render.resolution_x = WIDTH
    scene.render.resolution_y = HEIGHT
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = True
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.cycles.samples = 3
    scene.cycles.use_denoising = False
    bpy.context.view_layer.update()
    center = world_to_camera_view(scene, scene.camera, Vector((0, 0, 0)))
    pivot = [round(center.x * WIDTH), round((1.0-center.y)*HEIGHT)]
    if not 0 <= pivot[0] <= WIDTH or not 0 <= pivot[1] <= HEIGHT:
        raise RuntimeError("world origin is clipped")
    style = mats(args.kind)
    frames = []
    editable = None
    for clip, count in CLIPS.items():
        for frame in range(count):
            root, meshes = build_geometry(actor, clip, frame, style)
            if editable is None:
                editable = save_editable_source(scene, root, meshes, out)
            for heading, angle in HEADING_ANGLES.items():
                root.rotation_euler.z = math.radians(angle)
                bpy.context.view_layer.update()
                for slot, item in LAYERS:
                    for mesh in meshes:
                        mesh.hide_render = not (
                            mesh["ll_layer_slot"] == slot and mesh["ll_layer_item"] == item
                        )
                    rel = f"frames/{slot}_{item}_{clip}_{heading}_{frame:02d}.png"
                    dest = out / rel
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    scene.render.filepath = str(dest)
                    bpy.ops.render.render(write_still=True)
                    if not dest.exists() or dest.stat().st_size < 64:
                        raise RuntimeError("Blender did not write RGBA frame " + rel)
                    frames.append(dict(
                        slot=slot, item_id=item, animation=clip,
                        direction=heading, frame=frame,
                        file=rel, sha256=sha(dest)
                    ))
                    print("LL_F05_LAYER_FRAME", args.kind, clip, heading,
                          frame, slot, item, flush=True)
            remove_geometry(root, meshes)
    data = dict(schema="last-light.paperdoll.frames.v1",
                asset_id="ll_" + args.kind + "_layered_candidate",
                rig="ll_biped_v1", tile_px=[80, 40],
                frame_size=[WIDTH, HEIGHT], pivot=pivot,
                golden_approved=False, directions=list(HEADING_ANGLES),
                animations={
                    clip: {"frames": count, "fps": float(FPS), "loop": True}
                    for clip, count in CLIPS.items()
                }, frames=frames,
                provenance={
                    "original_generator": "tools/actor_factory/render_paperdoll_layers.py",
                    "model_source": "F05 original procedural biped and F06 state",
                    "artist_approval": "PENDING",
                    "actual_editable_sources": editable,
                    "layer_occlusion_review": "PENDING",
                    "no_project_zomboid_assets_reused": True
                })
    (out / "manifest.json").write_text(json.dumps(data, indent=2) + "\n")
    print("LL_F05_LAYER_RENDER_COMPLETE", args.kind,
          len(frames), "frames", len(LAYERS), "independent source layers",
          "pivot", pivot, flush=True)


if __name__ == "__main__":
    main()
