"""Original, parametric F01 refrigerator source and diagnostic Blender renders.

Run with:
    blender --background --factory-startup --python \
      tools/foundry_f01/generate_refrigerator.py -- \
      --output build/foundry/f01/refrigerator

Outputs are technical/artistic candidates only. This recipe does not integrate
the model into Godot or certify F11/F12, rights, iPhone, or Golden acceptance.
"""
from __future__ import annotations

import argparse
from array import array
import hashlib
import json
import math
import random
import struct
import sys
import zipfile
from pathlib import Path

import bpy
from mathutils import Vector


HERE = Path(__file__).resolve().parent
CONTRACT_PATH = HERE / "refrigerator_contract.json"
RESOLUTION = 256
HEADINGS = 16
ORTHO_SCALE = 2.35


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def material(name: str, color: tuple[float, float, float], roughness: float,
             metallic: float = 0.0) -> bpy.types.Material:
    result = bpy.data.materials.new(name)
    result.diffuse_color = (*color, 1.0)
    result.use_nodes = True
    shader = result.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (*color, 1.0)
    shader.inputs["Roughness"].default_value = roughness
    shader.inputs["Metallic"].default_value = metallic
    return result


def box(name: str, location: tuple[float, float, float],
        dimensions: tuple[float, float, float], surface: bpy.types.Material,
        bevel: float = 0.0) -> bpy.types.Object:
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(surface)
    if bevel > 0.0:
        mod = obj.modifiers.new("small_pressed_edge_radius", "BEVEL")
        mod.width = bevel
        mod.segments = 2
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=mod.name)
    return obj


def cylinder(name: str, location: tuple[float, float, float], radius: float,
             depth: float, surface: bpy.types.Material,
             rotation: tuple[float, float, float] = (0.0, 0.0, 0.0),
             vertices: int = 16) -> bpy.types.Object:
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=vertices, radius=radius, depth=depth,
        location=location, rotation=rotation,
    )
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(surface)
    return obj


def build_refrigerator(contract: dict) -> bpy.types.Object:
    """Build the sage enamel top-freezer model, with the ground anchor at 0."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 1.0
    scene["ll_asset_id"] = contract["asset_id"]
    scene["ll_work_order"] = contract["work_order"]
    scene["ll_world_placement_id"] = contract["world_placement_id"]
    scene["ll_candidate_only"] = True

    root = bpy.data.objects.new("LL_ASSET_ROOT_BOTTOM_CENTER", None)
    scene.collection.objects.link(root)
    root.location = (0.0, 0.0, 0.0)
    root["asset_id"] = contract["asset_id"]
    root["world_placement_id"] = contract["world_placement_id"]
    root["front_axis"] = "-Y"
    root["candidate_only"] = True

    enamel = material("Candidate_Sage_Worn_Enamel", (0.31, 0.39, 0.35), 0.57, 0.12)
    door_enamel = material("Candidate_Sage_Door_Enamel", (0.37, 0.44, 0.39), 0.52, 0.10)
    gasket = material("Candidate_Dark_Gasket", (0.075, 0.085, 0.078), 0.88)
    brushed = material("Candidate_Brushed_Handle_Metal", (0.43, 0.46, 0.42), 0.36, 0.72)
    foot_rubber = material("Candidate_Foot_Rubber", (0.045, 0.052, 0.048), 0.92)
    oxidation = material("Candidate_Sparse_Paint_Chips", (0.21, 0.16, 0.11), 0.84, 0.04)
    label = material("Candidate_Unmarked_Service_Plate", (0.65, 0.65, 0.57), 0.68, 0.05)

    # Cabinet envelope: 0.70 x 0.66 x 1.72, with discreet feet/trim staying
    # inside the candidate 0.72 x 0.68 x 1.78 design envelope.
    box("cabinet_shell", (0.0, 0.0, 0.92), (0.70, 0.66, 1.70), enamel, 0.025)
    box("top_cap", (0.0, 0.0, 1.775), (0.72, 0.68, 0.045), door_enamel, 0.018)
    box("bottom_plinth", (0.0, 0.0, 0.105), (0.67, 0.63, 0.12), gasket, 0.012)

    # Front is -Y. Dark seals remain visible as a narrow border around each door.
    front_y = -0.339
    box("upper_door_seal", (0.0, front_y, 1.445), (0.666, 0.026, 0.59), gasket, 0.015)
    box("lower_door_seal", (0.0, front_y, 0.745), (0.666, 0.026, 0.79), gasket, 0.015)
    box("upper_freezer_door", (0.0, -0.358, 1.445), (0.632, 0.035, 0.555), door_enamel, 0.022)
    box("lower_refrigerator_door", (0.0, -0.358, 0.745), (0.632, 0.035, 0.755), door_enamel, 0.022)
    box("door_divider", (0.0, -0.381, 1.135), (0.645, 0.012, 0.025), brushed, 0.004)

    # Small vertical pulls on the opening edge, each on simple round mounts.
    for z, length, suffix in ((1.46, 0.26, "freezer"), (0.755, 0.43, "fresh_food")):
        x = 0.255
        for mount_z in (z - length * 0.38, z + length * 0.38):
            cylinder(f"{suffix}_handle_mount_{mount_z:.3f}",
                     (x, -0.394, mount_z), 0.024, 0.026, brushed,
                     rotation=(math.pi / 2.0, 0.0, 0.0), vertices=12)
        box(f"{suffix}_vertical_pull", (x, -0.412, z),
            (0.026, 0.034, length), brushed, 0.009)

    # Unbranded small service plate and restrained vents establish appliance
    # reading without copied labels, logos, or reference typography.
    box("plain_service_badge", (-0.205, -0.381, 1.645),
        (0.115, 0.012, 0.055), label, 0.006)
    box("badge_rule_top", (-0.205, -0.389, 1.655),
        (0.065, 0.004, 0.004), gasket)
    box("badge_rule_bottom", (-0.205, -0.389, 1.638),
        (0.043, 0.004, 0.004), gasket)

    for x in (-0.235, 0.235):
        for y in (-0.22, 0.22):
            cylinder(f"rubber_leveling_foot_{x:+.3f}_{y:+.3f}",
                     (x, y, 0.035), 0.038, 0.07, foot_rubber, vertices=12)
    for z in (0.125, 0.155, 0.185, 0.215, 0.245):
        box(f"front_toe_vent_{z:.3f}", (0.0, -0.326, z),
            (0.24, 0.008, 0.009), brushed, 0.002)

    # Side pressing and rear condenser: directional details also make rear and
    # three-quarter views purposeful rather than empty boxes.
    for side in (-1.0, 1.0):
        for z in (0.43, 0.83, 1.23, 1.63):
            box(f"side_pressing_{side:+.0f}_{z:.2f}",
                (side * 0.353, 0.0, z), (0.012, 0.47, 0.018), door_enamel, 0.004)
    box("rear_service_inset", (0.0, 0.334, 0.88),
        (0.47, 0.012, 1.20), gasket, 0.01)
    for z in (0.42, 0.53, 0.64, 0.75, 0.86, 0.97, 1.08, 1.19, 1.30):
        box(f"rear_condenser_rail_{z:.2f}", (0.0, 0.347, z),
            (0.39, 0.018, 0.018), brushed, 0.006)
    for x in (-0.19, 0.19):
        box(f"rear_coil_return_{x:+.2f}", (x, 0.347, 0.86),
            (0.018, 0.018, 0.86), brushed, 0.006)

    # A stable seed gives restrained, localized paint chips (not uniform noise).
    rng = random.Random(contract["recipe"]["seed"])
    for index in range(7):
        side = -1.0 if index % 2 == 0 else 1.0
        z = rng.choice((0.31, 0.38, 0.97, 1.06, 1.56, 1.66))
        x = side * rng.uniform(0.275, 0.297)
        box(f"front_edge_wear_{index:02d}", (x, -0.380, z),
            (rng.uniform(0.009, 0.016), 0.004, rng.uniform(0.012, 0.025)),
            oxidation, 0.001)
    for index in range(4):
        z = rng.uniform(0.50, 1.45)
        box(f"right_side_wear_{index:02d}", (0.361, rng.uniform(-0.20, 0.20), z),
            (0.004, rng.uniform(0.018, 0.032), 0.007), oxidation)

    meshes = [obj for obj in scene.objects if obj.type == "MESH"]
    if len(meshes) < 25:
        raise RuntimeError(f"Geometry unexpectedly sparse: {len(meshes)} meshes")
    for obj in meshes:
        obj.parent = root
    bpy.context.view_layer.update()
    return root


def mesh_bounds_and_fingerprint(root: bpy.types.Object) -> tuple[list[float], list[float], str]:
    objects = sorted(
        (obj for obj in root.children_recursive if obj.type == "MESH"),
        key=lambda obj: obj.name,
    )
    points = []
    fingerprint = hashlib.sha256()
    for obj in objects:
        fingerprint.update(obj.name.encode("utf-8") + b"\0")
        for vertex in obj.data.vertices:
            point = obj.matrix_world @ vertex.co
            coords = tuple(round(float(value), 6) for value in point)
            points.append(coords)
            fingerprint.update((",".join(f"{value:.6f}" for value in coords) + ";").encode("ascii"))
    if not points:
        raise RuntimeError("No mesh vertices found")
    minimum = [min(point[i] for point in points) for i in range(3)]
    maximum = [max(point[i] for point in points) for i in range(3)]
    return minimum, maximum, fingerprint.hexdigest()


def validate_geometry(contract: dict, root: bpy.types.Object) -> dict:
    minimum, maximum, fingerprint = mesh_bounds_and_fingerprint(root)
    dimensions = [maximum[i] - minimum[i] for i in range(3)]
    if root.location.length > 1e-8:
        raise RuntimeError(f"Anchor root moved from origin: {tuple(root.location)}")
    if minimum[2] < -1e-5:
        raise RuntimeError(f"Geometry crosses floor anchor: minimum Z={minimum[2]}")
    if maximum[2] > 1.80:
        raise RuntimeError(f"Unexpected refrigerator height: {maximum[2]}")
    # Doors/handles may reach a little beyond the cabinet's nominal envelope.
    if not (0.68 <= dimensions[0] <= 0.76 and
            0.65 <= dimensions[1] <= 0.82 and
            1.72 <= dimensions[2] <= 1.80):
        raise RuntimeError(f"Geometry dimensions outside candidate envelope: {dimensions}")
    mats = {slot.material.name for obj in root.children_recursive
            if obj.type == "MESH" for slot in obj.material_slots}
    if len(mats) < 5:
        raise RuntimeError(f"Insufficient material distinction: {len(mats)}")
    return {
        "mesh_object_count": sum(obj.type == "MESH" for obj in root.children_recursive),
        "material_names": sorted(mats),
        "bounds_min": [round(value, 6) for value in minimum],
        "bounds_max": [round(value, 6) for value in maximum],
        "dimensions": [round(value, 6) for value in dimensions],
        "anchor_root_location": [round(float(value), 6) for value in root.location],
        "mesh_fingerprint_sha256": fingerprint,
    }


def configure_render() -> tuple[bpy.types.Scene, bpy.types.Object, bpy.types.Object]:
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 16
    scene.render.resolution_x = RESOLUTION
    scene.render.resolution_y = RESOLUTION
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = True
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.image_settings.color_depth = "8"
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "Medium High Contrast"
    scene.render.image_settings.color_mode = "RGBA"

    world = bpy.data.worlds.new("LL_Candidate_Neutral_Studio")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.24, 0.26, 0.25, 1.0)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.45
    scene.world = world

    camera_data = bpy.data.cameras.new("LL_F12_Diagnostic_Orthographic")
    camera = bpy.data.objects.new("LL_F12_Diagnostic_Orthographic", camera_data)
    scene.collection.objects.link(camera)
    camera_data.type = "ORTHO"
    camera_data.ortho_scale = ORTHO_SCALE
    camera_data.clip_end = 100.0
    target = Vector((0.0, 0.0, 0.89))
    elevation = math.radians(30.0)
    forward = Vector((1.0, 0.0, 0.0))
    camera.location = target + forward * 6.0 * math.cos(elevation) + Vector(
        (0.0, 0.0, 6.0 * math.sin(elevation))
    )
    camera.rotation_euler = (target - camera.location).to_track_quat("-Z", "Y").to_euler()
    scene.camera = camera

    light_data = bpy.data.lights.new("LL_Softbox_Key", "AREA")
    light = bpy.data.objects.new("LL_Softbox_Key", light_data)
    scene.collection.objects.link(light)
    light_data.energy = 420.0
    light_data.shape = "DISK"
    light_data.size = 3.2
    light.location = target + Vector((3.5, -2.5, 5.0))
    light.rotation_euler = (target - light.location).to_track_quat("-Z", "Y").to_euler()
    return scene, camera, light


def render_headings(contract: dict, output: Path, scene: bpy.types.Scene,
                    camera: bpy.types.Object, light: bpy.types.Object) -> list[dict]:
    render_dir = output / "headings"
    render_dir.mkdir()
    target = Vector((0.0, 0.0, 0.89))
    elevation = math.radians(30.0)
    results = []
    for heading in range(HEADINGS):
        angle = math.tau * heading / HEADINGS
        forward = Vector((math.cos(angle), math.sin(angle), 0.0))
        right = Vector((-math.sin(angle), math.cos(angle), 0.0))
        camera.location = target + forward * 6.0 * math.cos(elevation) + Vector(
            (0.0, 0.0, 6.0 * math.sin(elevation))
        )
        camera.rotation_euler = (target - camera.location).to_track_quat("-Z", "Y").to_euler()
        light.location = target + forward * 3.5 - right * 2.5 + Vector((0.0, 0.0, 5.0))
        light.rotation_euler = (target - light.location).to_track_quat("-Z", "Y").to_euler()
        path = render_dir / f"{heading:02d}.png"
        scene.render.filepath = str(path.resolve())
        bpy.ops.render.render(write_still=True)
        image = bpy.data.images.load(str(path.resolve()), check_existing=False)
        if tuple(image.size) != (RESOLUTION, RESOLUTION):
            raise RuntimeError(f"Wrong render dimensions: {path.name} {tuple(image.size)}")
        pixels = image.pixels[:]
        occupied = []
        transparent_count = 0
        maximum_alpha = 0.0
        for y in range(RESOLUTION):
            for x in range(RESOLUTION):
                alpha = pixels[(y * RESOLUTION + x) * 4 + 3]
                maximum_alpha = max(maximum_alpha, alpha)
                if alpha > contract["diagnostic_render"]["alpha_coverage_threshold"]:
                    occupied.append((x, y))
                else:
                    transparent_count += 1
        bpy.data.images.remove(image)
        if not occupied or transparent_count == 0 or maximum_alpha < 0.98:
            raise RuntimeError(f"Alpha QA failed for heading render: {path.name}")
        x_values = [point[0] for point in occupied]
        y_values = [point[1] for point in occupied]
        bbox = [min(x_values), min(y_values), max(x_values), max(y_values)]
        fractions = [(bbox[2] - bbox[0] + 1) / RESOLUTION,
                     (bbox[3] - bbox[1] + 1) / RESOLUTION]
        for fraction in fractions:
            if not (contract["diagnostic_render"]["framing_bbox_fraction_min"]
                    <= fraction
                    <= contract["diagnostic_render"]["framing_bbox_fraction_max"]):
                raise RuntimeError(f"Heading {heading} has bad pixel framing {fractions}")
        if min(bbox[0], bbox[1]) < 4 or max(bbox[2], bbox[3]) >= RESOLUTION - 4:
            raise RuntimeError(f"Heading {heading} clips against the image edge: {bbox}")
        results.append({
            "heading_index": heading,
            "heading_degrees": heading * 22.5,
            "file": path.name,
            "sha256": sha256(path),
            "alpha_nonzero_pixel_count": len(occupied),
            "alpha_transparent_pixel_count": transparent_count,
            "alpha_max": round(float(maximum_alpha), 6),
            "alpha_bbox_xyxy": bbox,
            "bbox_fraction_xy": [round(value, 6) for value in fractions],
        })
        print(f"F01_HEADING_PASS {heading:02d} {heading * 22.5:.1f}deg {path}", flush=True)
    return results


def create_contact_sheet(output: Path) -> Path:
    source_images = []
    for heading in range(HEADINGS):
        image = bpy.data.images.load(str((output / "headings" / f"{heading:02d}.png").resolve()),
                                     check_existing=False)
        source_images.append(array("f", image.pixels[:]))
        bpy.data.images.remove(image)

    atlas_width = RESOLUTION * 4
    atlas_pixels = array("f", [0.0]) * (atlas_width * atlas_width * 4)
    row_floats = RESOLUTION * 4
    for heading, source in enumerate(source_images):
        tile_x = heading % 4
        tile_y = heading // 4
        for y in range(RESOLUTION):
            src_start = y * row_floats
            dst_start = ((tile_y * RESOLUTION + y) * atlas_width + tile_x * RESOLUTION) * 4
            atlas_pixels[dst_start:dst_start + row_floats] = source[src_start:src_start + row_floats]
    atlas = bpy.data.images.new("LL_F01_Refrigerator_16_Heading_Contact_Sheet",
                                width=atlas_width, height=atlas_width, alpha=True)
    atlas.pixels[:] = atlas_pixels
    path = output / "contact_sheet_16_headings.png"
    atlas.filepath_raw = str(path.resolve())
    atlas.file_format = "PNG"
    atlas.save()
    bpy.data.images.remove(atlas)
    return path


def export_source(root: bpy.types.Object, output: Path) -> tuple[Path, Path]:
    blend_path = output / "model.blend"
    glb_path = output / "model.glb"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path.resolve()))
    bpy.ops.object.select_all(action="DESELECT")
    root.select_set(True)
    for child in root.children_recursive:
        child.select_set(True)
    bpy.context.view_layer.objects.active = root
    bpy.ops.export_scene.gltf(
        filepath=str(glb_path.resolve()),
        export_format="GLB",
        use_selection=True,
        export_apply=True,
        export_materials="EXPORT",
    )
    glb = glb_path.read_bytes()
    if len(glb) < 1000 or glb[:4] != b"glTF" or struct.unpack_from("<I", glb, 8)[0] != len(glb):
        raise RuntimeError("GLB header/length verification failed")
    blend = blend_path.read_bytes()
    if len(blend) < 1000 or blend[:7] != b"BLENDER":
        raise RuntimeError("Editable Blender source signature verification failed")
    return blend_path, glb_path


def create_candidate_archive(output: Path, contract_path: Path) -> tuple[Path, str]:
    archive_path = output / "source_archive_candidate.zip"
    recipe_path = Path(__file__).resolve()
    members = [
        (recipe_path, "recipe/generate_refrigerator.py"),
        (contract_path, "recipe/refrigerator_contract.json"),
        (output / "model.blend", "source/model.blend"),
        (output / "model.glb", "source/model.glb"),
        (output / "manifest.json", "source/manifest.json"),
        (output / "contact_sheet_16_headings.png", "diagnostics/contact_sheet_16_headings.png"),
    ]
    members.extend(
        (output / "headings" / f"{heading:02d}.png",
         f"diagnostics/headings/{heading:02d}.png")
        for heading in range(HEADINGS)
    )
    for source, _ in members:
        if not source.is_file():
            raise RuntimeError(f"Refusing incomplete source archive; missing {source}")
    with zipfile.ZipFile(archive_path, "x", compression=zipfile.ZIP_DEFLATED,
                         compresslevel=6) as archive:
        for source, member_name in members:
            archive.write(source, member_name)
    with zipfile.ZipFile(archive_path) as archive:
        bad_member = archive.testzip()
        if bad_member:
            raise RuntimeError(f"Source archive integrity failure: {bad_member}")
    return archive_path, sha256(archive_path)


def run(output: Path, contract_path: Path) -> dict:
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    if (contract.get("work_order") != "A00-B001-F01-ll_furniture_refrigerator-r1"
            or contract.get("asset_id") != "ll_furniture_refrigerator"
            or contract.get("approval", {}).get("golden_approved") is not False
            or contract.get("approval", {}).get("gameplay_integrated") is not False):
        raise RuntimeError("Unexpected identity or candidate approval contract")
    candidate_root = (HERE.parents[1] / "build" / "foundry" / "f01").resolve()
    try:
        output.relative_to(candidate_root)
    except ValueError as exc:
        raise ValueError(
            f"Refusing to write outside candidate-only build tree {candidate_root}: {output}"
        ) from exc
    output.mkdir(parents=True, exist_ok=True)
    if any(output.iterdir()):
        raise FileExistsError(f"Refusing to overwrite candidate output directory: {output}")

    root = build_refrigerator(contract)
    geometry = validate_geometry(contract, root)
    scene, camera, light = configure_render()
    blend_path, glb_path = export_source(root, output)
    headings = render_headings(contract, output, scene, camera, light)
    contact_sheet = create_contact_sheet(output)
    recipe_path = Path(__file__).resolve()
    report = {
        "schema_version": 1,
        "work_order": contract["work_order"],
        "asset_id": contract["asset_id"],
        "world_placement_id": contract["world_placement_id"],
        "status": "TECHNICAL_ARTISTIC_CANDIDATE",
        "technical_artistic_candidate_only": True,
        "golden_approved": False,
        "canonical_promoted": False,
        "gameplay_integrated": False,
        "f11_materials_approved": False,
        "f12_world_scale_approved": False,
        "godot_tested": False,
        "iphone_verified": False,
        "founder_visual_approved": False,
        "rights_reviewed": False,
        "blender_version": bpy.app.version_string,
        "recipe_sha256": sha256(recipe_path),
        "contract_sha256": sha256(contract_path),
        "blend_sha256": sha256(blend_path),
        "glb_sha256": sha256(glb_path),
        "geometry_qa": geometry,
        "collision_candidate": {
            "shape": "axis_aligned_box",
            "min": contract["placement"]["collision_min_candidate_units"],
            "max": contract["placement"]["collision_max_candidate_units"],
            "godot_interaction_tested": False,
        },
        "diagnostic_render": {
            "engine": "CYCLES_CPU",
            "resolution_px": [RESOLUTION, RESOLUTION],
            "samples": 16,
            "heading_count": len(headings),
            "headings": headings,
            "contact_sheet_sha256": sha256(contact_sheet),
            "f11_f12_certified": False,
        },
        "source_archive": {
            "file": "source_archive_candidate.zip",
            "sha256": None,
            "candidate_only": True,
        },
        "rights": contract["rights"],
        "unresolved_gates": contract["required_later_gates"],
    }
    manifest_path = output / "manifest.json"
    manifest_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    archive_path, archive_hash = create_candidate_archive(output, contract_path)
    # A ZIP cannot contain its own SHA-256 in an embedded manifest without
    # changing its digest. Keep manifest.json byte-identical on disk and inside
    # the ZIP; persist the outer archive checksum in a separate receipt.
    receipt = {
        "schema_version": 1,
        "asset_id": contract["asset_id"],
        "candidate_only": True,
        "golden_approved": False,
        "archive": archive_path.name,
        "archive_sha256": archive_hash,
        "embedded_manifest_sha256": sha256(manifest_path),
    }
    (output / "archive_receipt.json").write_text(
        json.dumps(receipt, indent=2) + "\n", encoding="utf-8"
    )
    report["archive_receipt"] = receipt
    print(f"F01_REFRIGERATOR_CANDIDATE_PASS {contract['asset_id']}", flush=True)
    print(f"F01_BLEND_SHA256 {report['blend_sha256']}", flush=True)
    print(f"F01_GLB_SHA256 {report['glb_sha256']}", flush=True)
    print(f"F01_ARCHIVE_SHA256 {archive_hash}", flush=True)
    print(f"F01_CONTACT_SHEET {contact_sheet}", flush=True)
    return report


def main() -> None:
    args_from_blender = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--contract", type=Path, default=CONTRACT_PATH)
    args = parser.parse_args(args_from_blender)
    run(args.output.resolve(), args.contract.resolve())


if __name__ == "__main__":
    main()
