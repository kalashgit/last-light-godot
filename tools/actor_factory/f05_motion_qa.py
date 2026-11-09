"""Blender F05 noncanonical garment-in-motion evidence.

Opens the generated .blend and renders two poses for each provisional clip.
Checks garment transverse bounds around their shared deforming bones.
This is an automated screening gate, NOT human visual approval.
"""
import argparse
import json
import sys
from pathlib import Path
import bpy
from mathutils import Vector

parser = argparse.ArgumentParser()
parser.add_argument("--output", required=True)
args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
out = Path(args.output).resolve()
source = out / "f05_noncanonical_calibration.blend"
if not source.exists():
    raise SystemExit("F05_MOTION_QA_NO_BLEND")
bpy.ops.wm.open_mainfile(filepath=str(source))
rig = bpy.data.objects.get("F05_TEST_RIG")
if rig is None or rig.type != "ARMATURE" or not rig.animation_data:
    raise SystemExit("F05_MOTION_QA_NO_RIG")
tracks = {t.name.removeprefix("F05_CAL_"): t for t in rig.animation_data.nla_tracks}
clips = {"idle": 4, "walk": 8, "run": 8, "sneak": 8,
         "interact": 6, "attack": 6, "hurt": 3, "death": 7}
if set(tracks) != set(clips):
    raise SystemExit("F05_MOTION_QA_MISSING_NLA: " + repr(set(clips) - set(tracks)))

pairs = [("torso skin", "wearable_shirt_body", "chest")]
for side in ("L", "R"):
    pairs.extend([
        ("upper arm " + side, "wearable_shirt_sleeve_" + side, "upper_arm_" + side),
        ("thigh " + side, "wearable_pants_upper_" + side, "thigh_" + side),
        ("shin " + side, "wearable_pants_lower_" + side, "shin_" + side)
    ])
for skin_name, garment_name, bone_name in pairs:
    if any(x is None for x in (
        bpy.data.objects.get(skin_name),
        bpy.data.objects.get(garment_name),
        rig.pose.bones.get(bone_name),
    )):
        raise SystemExit("F05_MOTION_QA_MISSING_GEOMETRY: " + garment_name)

scene = bpy.context.scene
scene.render.resolution_x = 128
scene.render.resolution_y = 128
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.image_settings.color_mode = "RGBA"
frames_dir = out / "motion_frames"
frames_dir.mkdir(exist_ok=True)
defects = []
observations = []

def transverse_bounds(ob, bone_name):
    dg = bpy.context.evaluated_depsgraph_get()
    evaluated = ob.evaluated_get(dg)
    mesh = evaluated.to_mesh()
    try:
        matrix = (rig.matrix_world @ rig.pose.bones[bone_name].matrix).inverted()
        points = [matrix @ (evaluated.matrix_world @ v.co) for v in mesh.vertices]
        if not points:
            raise ValueError("No deformed vertices on " + ob.name)
        # Blender bone-local Y is longitudinal: X and Z are transverse.
        return [(min(p[i] for p in points), max(p[i] for p in points)) for i in (0, 2)]
    finally:
        evaluated.to_mesh_clear()

for clip, frame_count in clips.items():
    for name, track in tracks.items():
        track.mute = name != clip
    samples = ((2, (frame_count // 2) + 1) if clip in ("walk", "run", "sneak")
               else (1, frame_count))
    for i, frame in enumerate(samples):
        scene.frame_set(frame)
        row = {"clip": clip, "frame": frame, "envelope_margins_m": {}}
        for skin_name, garment_name, bone in pairs:
            skin = transverse_bounds(bpy.data.objects[skin_name], bone)
            garment = transverse_bounds(bpy.data.objects[garment_name], bone)
            margins = [skin[axis][0] - garment[axis][0] for axis in range(2)]
            margins.extend(garment[axis][1] - skin[axis][1] for axis in range(2))
            margin = round(min(margins), 5)
            row["envelope_margins_m"][garment_name] = margin
            if margin < -0.004:
                defects.append({
                    "clip": clip, "frame": frame, "layer": garment_name,
                    "radial_envelope_margin_m": margin
                })
        scene.render.filepath = str(frames_dir / f"{clip}_{i:02}.png")
        bpy.ops.render.render(write_still=True)
        observations.append(row)

report = {
    "status": "SCREENING_FAIL" if defects else "SCREENING_PASS",
    "scope": "bone-local transverse bounding envelopes; seams and pixel occlusion need human review",
    "physique": json.loads((out / "manifest.json").read_text()).get("physique"),
    "poses_rendered": len(observations),
    "human_visual_approved": False,
    "canonical_approved": False,
    "defects": defects,
    "observations": observations,
}
(out / "motion_qa.json").write_text(json.dumps(report, indent=2) + "\n")
print("F05_MOTION_QA", report["status"], "frames", len(observations), "defects", len(defects))
if defects:
    sys.exit(3)
