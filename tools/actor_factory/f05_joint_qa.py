"""F05 exhaustive frame/subframe Blender joint and floor-contact QA.

Covers every keyed frame of eight provisional actions, plus half frames for
locomotion. Uses evaluated, weighted world-space meshes; does not infer fit from
unposed source geometry. Surface intersections are checked on specified pairs.
Adjacent sewn seams and aesthetic appearance still require visual approval.
"""
import argparse
import json
import sys
from itertools import combinations
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

p = argparse.ArgumentParser()
p.add_argument("--output", required=True)
args = p.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
out = Path(args.output).resolve()
bpy.ops.wm.open_mainfile(filepath=str(out / "f05_noncanonical_calibration.blend"))
rig = bpy.data.objects.get("F05_TEST_RIG")
if rig is None or not rig.animation_data:
    raise SystemExit("F05_JOINT_QA_MISSING_ARMATURE")
tracks = {track.name.removeprefix("F05_CAL_"): track
          for track in rig.animation_data.nla_tracks}
clips = {"idle": 4, "walk": 8, "run": 8, "sneak": 8,
         "interact": 6, "attack": 6, "hurt": 3, "death": 7}
if set(tracks) != set(clips):
    raise SystemExit("F05_JOINT_QA_MISSING_ACTIONS")

pairs = [("torso skin", "wearable_shirt_body")]
for side in ("L", "R"):
    pairs.append(("leg_skin_" + side, "wearable_pants_" + side))
    pairs.append(("arm_skin_" + side, "wearable_shirt_sleeve_" + side))
# Check nonadjacent body/garment collisions. Overlapping shoulders, cuffs and
# crotch seams are exempted explicitly, not counted as validated.
unrelated = [("hand " + side, "wearable_pants_" + side)
             for side in ("L", "R")]
unrelated += [("arm_skin_" + side, "wearable_pants_" + side)
              for side in ("L", "R")]
required = {item for pair in pairs + unrelated for item in pair}
required.update(("foot L", "foot R"))
missing = required.difference(bpy.data.objects.keys())
if missing:
    raise SystemExit("F05_JOINT_QA_MISSING_OBJECTS " + repr(sorted(missing)))

def evaluated_mesh(ob, dg):
    evaluated = ob.evaluated_get(dg)
    mesh = evaluated.to_mesh()
    try:
        world = evaluated.matrix_world
        verts = [world @ v.co for v in mesh.vertices]
        faces = [tuple(p.vertices) for p in mesh.polygons]
        return verts, faces
    finally:
        evaluated.to_mesh_clear()

def tree(points, faces):
    if not points or not faces:
        raise RuntimeError("Missing evaluated surface")
    return BVHTree.FromPolygons(points, faces, all_triangles=False)

def radial_margin(skin, shell, segments=16):
    if len(skin) < len(shell) or len(shell) % segments or len(skin) % segments:
        raise RuntimeError("Paired loft topology changed across deformation")
    # The sleeve deliberately covers only the upper four rings of the
    # continuous arm, rather than extending all the way to the wrist.
    skin = skin[-len(shell):]
    gaps = []
    for start in range(0, len(skin), segments):
        center = sum((v for v in skin[start:start + segments]), Vector()) / segments
        for index in range(start, start + segments):
            radial = skin[index] - center
            if radial.length < 1e-7:
                raise RuntimeError("Degenerate evaluated skin cross-section")
            gaps.append((shell[index] - skin[index]).dot(radial.normalized()))
    return min(gaps)

defects = []
rows = []
min_radial = 1e9
worst_floor = 1e9
max_hover = 0.0
for clip, frames in clips.items():
    for name, track in tracks.items():
        track.mute = name != clip
    samples = [(f, 0.0) for f in range(1, frames + 1)]
    if clip in ("idle", "walk", "run", "sneak"):
        samples.extend((f, .5) for f in range(1, frames))
    for frame, sub in samples:
        bpy.context.scene.frame_set(frame, subframe=sub)
        dg = bpy.context.evaluated_depsgraph_get()
        cache = {}
        def mesh(name):
            if name not in cache:
                cache[name] = evaluated_mesh(bpy.data.objects[name], dg)
            return cache[name]
        row = {"clip": clip, "frame": frame, "subframe": sub}
        for inner, outer in pairs:
            iv, ip = mesh(inner)
            ov, op = mesh(outer)
            intersections = len(tree(iv, ip).overlap(tree(ov, op)))
            if intersections:
                defects.append({"clip": clip, "frame": frame, "subframe": sub,
                                "type": "surface_intersection", "objects": [inner, outer],
                                "triangle_pairs": intersections})
            if inner == "torso skin" or inner.startswith(("leg_skin", "arm_skin")):
                margin = radial_margin(iv, ov)
                min_radial = min(min_radial, margin)
                if margin < 0.004:
                    defects.append({"clip": clip, "frame": frame, "subframe": sub,
                                    "type": "garment_skin_clearance",
                                    "objects": [inner, outer],
                                    "clearance_m": round(margin, 5)})
        for first, second in unrelated:
            av, ap = mesh(first)
            bv, bp = mesh(second)
            intersections = len(tree(av, ap).overlap(tree(bv, bp)))
            if intersections:
                defects.append({"clip": clip, "frame": frame, "subframe": sub,
                                "type": "unrelated_body_clipping",
                                "objects": [first, second],
                                "triangle_pairs": intersections})
        if clip in ("idle", "walk", "run", "sneak"):
            floor = min(min(v.z for v in mesh("foot " + side)[0])
                        for side in ("L", "R"))
            worst_floor = min(worst_floor, floor)
            max_hover = max(max_hover, floor)
            row["lowest_foot_z"] = round(floor, 5)
            if floor < -0.006 or floor > 0.025:
                defects.append({"clip": clip, "frame": frame, "subframe": sub,
                                "type": "foot_floor_contact", "sole_z_m": round(floor, 5)})
        rows.append(row)

result = {
    "status": "FAIL" if defects else "PASS",
    "physique": json.loads((out / "manifest.json").read_text())["physique"],
    "full_frames": sum(clips.values()),
    "half_frames": sum(clips[name] - 1 for name in ("idle", "walk", "run", "sneak")),
    "samples": len(rows),
    "minimum_limb_garment_radial_clearance_m": round(min_radial, 5),
    "minimum_foot_sole_z_m": round(worst_floor, 5),
    "maximum_foot_hover_z_m": round(max_hover, 5),
    "scope": "all 50 keyed and 24 intermediate poses, continuous arm/sleeve and leg/trouser surfaces, unrelated hand/arm-pants collisions, floor contact",
    "exclusions": ["shoulder sleeve and shirt seam", "two pant legs at crotch",
                   "footwear cuff to ankle seam", "physically planted-foot IK",
                   "Godot gameplay rendering", "visual approval"],
    "defects": defects[:100],
    "total_defects": len(defects),
    "sample_records": rows,
    "canonical_approved": False,
}
(out / "joint_qa.json").write_text(json.dumps(result, indent=2) + "\n")
print("F05_JOINT_QA", result["status"], "samples", len(rows),
      "defects", len(defects), "radial_min", result["minimum_limb_garment_radial_clearance_m"],
      "floor_min", result["minimum_foot_sole_z_m"],
      "floor_hover_max", result["maximum_foot_hover_z_m"])
if defects:
    from collections import Counter
    print("F05_JOINT_DEFECT_COUNTS", json.dumps(dict(Counter(item["type"] for item in defects))))
    for item in defects[:35]:
        print("F05_JOINT_DEFECT", json.dumps(item))
    sys.exit(4)
