"""Blender-only ray-cast visibility evidence for a real editable candidate scene.

Run in Blender, not Python. Geometric visibility is necessary but not sufficient
for a visually recognizable component; human or real VLM review remains needed.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector


def component_visibility(scene, camera, obj, depsgraph):
    # Sample actual mesh surfaces, not merely the eight bounding-box corners.
    # A thin flange or surface plate may be genuinely visible even when every
    # bbox corner projects into empty space. Rays still detect a case body
    # hiding its own front-facing latch from the opposite side.
    points = [obj.matrix_world.translation.copy()]
    points.extend(obj.matrix_world @ Vector(corner) for corner in obj.bound_box)
    corners_projected = [world_to_camera_view(scene, camera, point) for point in points[1:9]]
    resolution = scene.render.resolution_x * scene.render.resolution_percentage / 100
    projected_area = (max(p.x for p in corners_projected) - min(p.x for p in corners_projected)) * (
        max(p.y for p in corners_projected) - min(p.y for p in corners_projected)) * resolution * resolution
    polygons = obj.data.polygons
    stride = max(1, math.ceil(len(polygons) / 128))
    world_normal = obj.matrix_world.to_3x3()
    for polygon_index in range(0, len(polygons), int(stride)):
        polygon = polygons[polygon_index]
        center = obj.matrix_world @ polygon.center
        normal = (world_normal @ polygon.normal).normalized()
        if normal.dot(camera.location - center) > 0:
            points.append(center)
    hits = 0
    on_screen = 0
    for point in points:
        projection = world_to_camera_view(scene, camera, point)
        if projection.z <= 0 or not (-.02 <= projection.x <= 1.02 and -.02 <= projection.y <= 1.02):
            continue
        on_screen += 1
        ray = point - camera.location
        distance = ray.length
        if distance <= 0:
            continue
        result = scene.ray_cast(depsgraph, camera.location, ray.normalized(), distance=distance + .035)
        if result[0] and result[4].name == obj.name:
            hits += 1
    origin = world_to_camera_view(scene, camera, obj.matrix_world.translation)
    return {"ray_hit_samples": hits, "on_screen_samples": on_screen,
            "total_samples": len(points), "visible": hits >= 1,
            "projected_bbox_area_px2": round(projected_area, 4),
            "projected_origin_xy": [round(origin.x, 6), round(1 - origin.y, 6)],
            "depth": round(origin.z, 6)}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--constraints", required=True, type=Path)
    p.add_argument("--out", required=True, type=Path)
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    args = p.parse_args(argv)
    document = json.loads(args.constraints.read_text())
    if document["schema"] != "last-light.component-visibility-constraints.v1":
        raise ValueError("unsupported visibility contract")
    required = document["required_visible_components"]
    if not isinstance(required, list) or not 1 <= len(required) <= 32:
        raise ValueError("1–32 required source-visible parts")
    if len(required) != len(set(required)):
        raise ValueError("duplicate required component")
    root = bpy.data.objects.get("LL_Recipe_Assembly_Root")
    camera = bpy.context.scene.camera
    if root is None or camera is None:
        raise ValueError("not a saved LAST LIGHT Blender candidate scene")
    parts = {}
    for name in required:
        if not isinstance(name, str) or not 3 <= len(name) <= 71 or not name.replace("_", "").isalnum():
            raise ValueError("invalid part name")
        obj = bpy.data.objects.get("LL_" + name)
        if obj is None or obj.type != "MESH":
            raise ValueError("required source-visible part missing from actual mesh: " + name)
        parts[name] = obj
    scene = bpy.context.scene
    orientations = []
    initial_rotation = root.rotation_euler.z
    for heading in range(16):
        root.rotation_euler.z = initial_rotation + math.radians(22.5 * heading)
        bpy.context.view_layer.update()
        depsgraph = bpy.context.evaluated_depsgraph_get()
        results = {name: component_visibility(scene, camera, obj, depsgraph) for name, obj in parts.items()}
        orientations.append({"heading": heading, "required_parts": results,
                             "all_required_visible": all(e["visible"] for e in results.values()),
                             "required_visible_count": sum(e["visible"] for e in results.values())})
    root.rotation_euler.z = initial_rotation
    bpy.context.view_layer.update()
    output = {"schema": "last-light.component-visibility-evidence.v1",
              "geometry_method": "blender_scene_ray_cast_9_samples_per_component",
              "required_visible_components": required,
              "source_sha256": document["source_sha256"],
              "candidate_id": document["candidate_id"],
              "semantic_ai_model_inference": False,
              "geometric_occlusion_only_not_semantic_recognition": True,
              "orientations": orientations}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    print("LL_COMPONENT_VISIBILITY_PROBE", document["candidate_id"],
          "ELIGIBLE_HEADINGS", [r["heading"] for r in orientations if r["all_required_visible"]])


if __name__ == "__main__":
    main()
