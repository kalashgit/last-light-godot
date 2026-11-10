"""Allowlisted Blender recipe interpreter. Run with Blender -b --python ... -- --recipe ...

No arbitrary Python/text supplied by a recipe is evaluated or executed. Source
art is never imported as a texture. This is a candidate-only renderer.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from recipe_architect.contract import validate


def make_material(m):
    mat = bpy.data.materials.new("LL_" + m["name"])
    mat.diffuse_color = m["rgba"]
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = m["rgba"]
    bsdf.inputs["Metallic"].default_value = m["metallic"]
    bsdf.inputs["Roughness"].default_value = m["roughness"]
    if m["texture"] != "none":
        nodes, links = mat.node_tree.nodes, mat.node_tree.links
        noise = nodes.new("ShaderNodeTexNoise")
        noise.inputs["Scale"].default_value = 120 if m["texture"] == "fine_noise" else 38
        noise.inputs["Detail"].default_value = 2
        bump = nodes.new("ShaderNodeBump")
        bump.inputs["Strength"].default_value = 0.08 + 0.12 * m["wear"]
        bump.inputs["Distance"].default_value = .012
        links.new(noise.outputs["Fac"], bump.inputs["Height"])
        links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
        if m["texture"] == "scuffed":
            ramp = nodes.new("ShaderNodeValToRGB")
            base = m["rgba"][:3]
            ramp.color_ramp.elements[0].position = .28
            ramp.color_ramp.elements[0].color = (*[max(.0, c * .60) for c in base], 1)
            ramp.color_ramp.elements[1].position = .75
            ramp.color_ramp.elements[1].color = (*[min(1.0, c * 1.55) for c in base], 1)
            links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
            links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    return mat


def mesh_object(name, verts, faces):
    mesh = bpy.data.meshes.new(name + "_mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return obj


def lathe(name, g):
    count = g.get("vertices", 48)
    rings, verts, faces = [], [], []
    sx, sy = g.get("scale_xy", [1, 1])
    for r, z in g["profile"]:
        ids = []
        for j in range(1 if r == 0 else count):
            t = 2 * math.pi * j / count
            ids.append(len(verts))
            verts.append((r * math.cos(t) * sx, r * math.sin(t) * sy, z))
        rings.append(ids)
    for first, second in zip(rings, rings[1:]):
        if len(first) == 1 and len(second) == 1:
            continue
        for j in range(count):
            if len(first) == 1:
                faces.append((first[0], second[j], second[(j + 1) % count]))
            elif len(second) == 1:
                faces.append((first[j], second[0], first[(j + 1) % count]))
            else:
                k = (j + 1) % count
                faces.append((first[j], second[j], second[k], first[k]))
    return mesh_object(name, verts, faces)


def polygon_extrude(name, g):
    pts, depth = g["points"], g["depth"]
    n = len(pts)
    verts = [(x, y, z) for z in (-depth / 2, depth / 2) for x, y in pts]
    faces = [tuple(reversed(range(n))), tuple(range(n, 2 * n))]
    for i in range(n):
        j = (i + 1) % n
        faces.append((i, j, j + n, i + n))
    return mesh_object(name, verts, faces)


def create(c, materials):
    name, g, op = c["name"], c["geometry"], c["op"]
    if op in ("box", "boolean_cut"):
        bpy.ops.mesh.primitive_cube_add(size=1)
        obj = bpy.context.object
        obj.dimensions = g["size"]
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    elif op == "cylinder":
        bpy.ops.mesh.primitive_cylinder_add(vertices=g.get("vertices", 32), radius=g["radius"], depth=g["depth"])
        obj = bpy.context.object
        obj.scale.x, obj.scale.y = g.get("scale_xy", [1, 1])
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    elif op == "lathe":
        obj = lathe(name, g)
    elif op == "polygon_extrude":
        obj = polygon_extrude(name, g)
    elif op == "tube":
        curve = bpy.data.curves.new(name + "_curve", "CURVE")
        curve.dimensions = "3D"
        curve.resolution_u = 16
        curve.bevel_resolution = 3
        curve.bevel_depth = g["radius"]
        curve.use_fill_caps = True
        poly = curve.splines.new("POLY")
        poly.points.add(len(g["points"]) - 1)
        for point, xyz in zip(poly.points, g["points"]):
            point.co = (*xyz, 1)
        poly.use_cyclic_u = g.get("closed", False)
        obj = bpy.data.objects.new(name, curve)
        bpy.context.collection.objects.link(obj)
    elif op == "text":
        data = bpy.data.curves.new(name + "_text", "FONT")
        data.body = g["value"]
        data.size = g["size"]
        data.extrude = g.get("extrude", .002)
        data.bevel_depth = .0005
        obj = bpy.data.objects.new(name, data)
        bpy.context.collection.objects.link(obj)
    else:
        raise ValueError("unsupported operation: " + op)
    obj.name = "LL_" + name
    obj.location = c["location"]
    obj.rotation_euler = [math.radians(v) for v in c["rotation_deg"]]
    obj.data.materials.append(materials[c["material"]])
    if g.get("bevel") and op in ("box", "cylinder", "polygon_extrude"):
        modifier = obj.modifiers.new("edge_relief", "BEVEL")
        modifier.width = g["bevel"]
        modifier.segments = 2
    if "subdivide_1" in c["modifiers"]:
        subdiv = obj.modifiers.new("subdivide_1", "SUBSURF")
        subdiv.levels = 1
    if "weighted_normals" in c["modifiers"] and obj.type == "MESH":
        obj.modifiers.new("weighted_corner_normals", "WEIGHTED_NORMAL")
    return obj


def to_mesh(obj):
    if obj.type in ("CURVE", "FONT"):
        bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.convert(target="MESH")
        return bpy.context.object
    return obj


def setup_scene(r):
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE_NEXT"
    scene.render.film_transparent = True
    if hasattr(scene, "eevee") and hasattr(scene.eevee, "taa_render_samples"):
        scene.eevee.taa_render_samples = 16
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.resolution_x = scene.render.resolution_y = r["resolution"]
    scene.render.resolution_percentage = 100
    scene.render.image_settings.color_depth = "8"
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "Medium High Contrast"
    scene.render.film_transparent = True
    scene.camera = None
    world = bpy.data.worlds.new("LL_Neutral_World")
    scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    bg.inputs[0].default_value = (.21, .23, .25, 1)
    bg.inputs[1].default_value = .7
    cam_data = bpy.data.cameras.new("LL_2to1_Orthographic")
    camera = bpy.data.objects.new("LL_2to1_Orthographic", cam_data)
    bpy.context.collection.objects.link(camera)
    cam_data.type = "ORTHO"
    cam_data.ortho_scale = r["orthographic_scale"]
    scene.camera = camera
    light_data = bpy.data.lights.new("LL_Upper_Left_Key", "AREA")
    light = bpy.data.objects.new("LL_Upper_Left_Key", light_data)
    bpy.context.collection.objects.link(light)
    light.location = (-3.5, -4.0, 6.0)
    light_data.energy = 500
    light_data.shape = "DISK"
    light_data.size = 4.0
    light.rotation_euler = (Vector((0, 0, .5)) - light.location).to_track_quat("-Z", "Y").to_euler()
    return camera


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--recipe", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--headings", type=int, choices=[1, 16], default=16)
    parser.add_argument("--no-export", action="store_true")
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    args = parser.parse_args(argv)
    recipe = validate(json.loads(args.recipe.read_text()))
    args.output.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    materials = {m["name"]: make_material(m) for m in recipe["materials"]}
    components, cutters = {}, []
    for c in recipe["components"]:
        obj = create(c, materials)
        if c["op"] == "boolean_cut": cutters.append((c, obj))
        else: components[c["name"]] = obj
    for c, cutter in cutters:
        target = components[c["geometry"]["target"]]
        if target.type != "MESH": raise ValueError("boolean target must be a mesh")
        modifier = target.modifiers.new("allowed_boolean_cut", "BOOLEAN")
        modifier.operation = "DIFFERENCE"
        modifier.object = cutter
        bpy.context.view_layer.objects.active = target
        bpy.ops.object.modifier_apply(modifier=modifier.name)
        bpy.data.objects.remove(cutter, do_unlink=True)
    for name, obj in list(components.items()):
        components[name] = to_mesh(obj)
    bpy.context.view_layer.update()
    # A shared assembly root keeps local transforms and inherited scaling editable.
    root = bpy.data.objects.new("LL_Recipe_Assembly_Root", None)
    bpy.context.collection.objects.link(root)
    root.scale = recipe["render"]["assembly_scale"]
    for c in recipe["components"]:
        if c["op"] == "boolean_cut": continue
        parent = components[c["parent"]] if c["parent"] is not None else root
        obj = components[c["name"]]
        original = obj.matrix_world.copy()
        obj.parent = parent
        obj.matrix_world = original
    bpy.context.view_layer.update()
    meshes = list(components.values())
    vertices = sum(len(o.data.vertices) for o in meshes)
    polygons = sum(len(o.data.polygons) for o in meshes)
    triangles = sum(max(1, len(p.vertices) - 2) for o in meshes for p in o.data.polygons)
    if len(meshes) < 3 or vertices < 100 or polygons < 30:
        raise ValueError("not a substantive editable mesh construction")
    coords = [o.matrix_world @ Vector(v) for o in meshes for v in o.bound_box]
    lo = [min(v[i] for v in coords) for i in range(3)]
    hi = [max(v[i] for v in coords) for i in range(3)]
    bounds = [round(hi[i] - lo[i], 5) for i in range(3)]
    if min(bounds) <= .05: raise ValueError("degenerate physical geometry")
    camera = setup_scene(recipe["render"])
    azimuth = math.radians(recipe["render"]["camera_azimuth_deg"])
    elev = math.radians(recipe["render"]["camera_elevation_deg"])
    target = Vector((0, 0, bounds[2] * .55))
    distance = 6
    camera.location = (distance * math.cos(elev) * math.cos(azimuth),
                       distance * math.cos(elev) * math.sin(azimuth),
                       target.z + distance * math.sin(elev))
    camera.rotation_euler = (target - camera.location).to_track_quat("-Z", "Y").to_euler()
    if not args.no_export:
        bpy.ops.wm.save_as_mainfile(filepath=str((args.output / "editable_candidate.blend").resolve()), compress=True)
        bpy.ops.object.select_all(action="DESELECT")
        for obj in meshes: obj.select_set(True)
        bpy.context.view_layer.objects.active = meshes[0]
        bpy.ops.export_scene.gltf(filepath=str((args.output / "candidate.glb").resolve()), export_format="GLB", use_selection=True)
    # Actual Blender projection evidence. Recipe-provided 2D landmarks are
    # observations; these values are measured from generated geometry/camera.
    # Capture at heading zero, before applying any directional rotation.
    scene = bpy.context.scene
    bpy.context.view_layer.update()
    projected = {}
    for name, obj in components.items():
        origin = obj.matrix_world.translation.copy()
        parent_to_world = (obj.parent.matrix_world @ obj.matrix_parent_inverse).to_3x3() if obj.parent else None

        def screen(point):
            p = world_to_camera_view(scene, camera, point)
            return [round(p.x * recipe["render"]["resolution"], 6),
                    round((1 - p.y) * recipe["render"]["resolution"], 6)]

        pixel = screen(origin)
        # The visual optimizer needs measured physical component extents, not
        # estimates copied from the untrusted recipe. Sample actual Blender
        # mesh vertices after parenting/booleans; bevel modifiers may extend
        # these bounds slightly, which the optimizer treats as uncertainty.
        vertices_world = [obj.matrix_world @ vertex.co for vertex in obj.data.vertices]
        vertices_px = [screen(point) for point in vertices_world]
        component_bbox = [round(min(point[0] for point in vertices_px), 6),
                          round(min(point[1] for point in vertices_px), 6),
                          round(max(point[0] for point in vertices_px), 6),
                          round(max(point[1] for point in vertices_px), 6)]
        world_bbox = [[round(min(v[axis] for v in vertices_world), 6) for axis in range(3)],
                      [round(max(v[axis] for v in vertices_world), 6) for axis in range(3)]]
        axes = []
        for axis in (Vector((1, 0, 0)), Vector((0, 1, 0))):
            delta = parent_to_world @ axis if parent_to_world else axis
            shifted = screen(origin + delta)
            axes.append([round(shifted[k] - pixel[k], 6) for k in range(2)])
        projected[name] = {"origin_px": pixel, "bbox_px": component_bbox,
                           "world_bbox_m": world_bbox,
                           "bbox_method": "actual_blender_mesh_vertices_pre_bevel",
                           "local_xy_axes_px_per_m": axes,
                           "depth": round(world_to_camera_view(scene, camera, origin).z, 5)}
    (args.output / "component_projections.json").write_text(json.dumps({
        "schema": "last-light.recipe-projections.v1", "heading": 0,
        "resolution": recipe["render"]["resolution"], "components": projected}, indent=2, sort_keys=True) + "\n")
    for heading in range(args.headings):
        # Keep the light fixed in screen/world space while rotating the object.
        root.rotation_euler.z = math.radians(22.5 * heading)
        scene = bpy.context.scene
        scene.render.filepath = str((args.output / f"heading_{heading:02d}.png").resolve())
        bpy.ops.render.render(write_still=True)
    record = {
        "candidate_id": recipe["identity"]["candidate_id"], "source_sha256": recipe["identity"]["source_sha256"],
        "mesh_objects": len(meshes), "vertices": vertices, "polygons": polygons,
        "triangles_estimate": triangles, "bounds_m": bounds,
        "materials": sorted(materials), "component_names": sorted(components),
        "rendered_headings": args.headings, "golden_approved": False,
        "blender_version": bpy.app.version_string,
    }
    if not args.no_export:
        for name in ("candidate.glb", "editable_candidate.blend"):
            record[name + "_sha256"] = hashlib.sha256((args.output / name).read_bytes()).hexdigest()
    (args.output / "geometry_qa.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print("LL_RECIPE_BLENDER_PASS", json.dumps({"meshes": len(meshes), "triangles": triangles, "headings": args.headings}), flush=True)


if __name__ == "__main__":
    main()
