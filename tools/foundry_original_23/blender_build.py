"""Create independent editable Blender source models from Sprite Bible V2 briefs.

This script is a technical *geometry-authoring* pass, not final realistic art.
No source art or source geometry is imported, and no asset is Golden-approved.
Run inside Blender, e.g. blender -b -t 2 --python blender_build.py -- --output ...
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector


PALETTE = {
    "ivory_bone": (0.70, .63, .47), "weathered_bone": (.44, .32, .23),
    "russet_leather": (.36, .16, .08), "brown_leather": (.29, .15, .07),
    "dark_leather": (.14, .095, .075), "stitch": (.52, .43, .30),
    "brass": (.50, .33, .10), "olive_canvas": (.24, .29, .16),
    "navy_canvas": (.075, .12, .20), "thread": (.55, .51, .40),
    "steel": (.38, .41, .43), "forged_steel": (.28, .31, .33),
    "charcoal_plastic": (.11, .12, .13), "polymer_tie": (.18, .19, .17),
    "kraft_paper": (.52, .39, .25), "kraft_cardboard": (.56, .43, .28),
    "olive_ink": (.27, .36, .20), "ash_wood": (.46, .30, .16),
    "hickory_wood": (.42, .28, .15), "hemp_rope": (.55, .43, .26),
    "lining": (.24, .20, .16), "metal_zipper": (.42, .42, .37),
    "graphite_tape": (.17, .18, .19), "kraft_core": (.47, .34, .19),
    "amber_plastic": (.61, .31, .09), "ivory_gauze": (.83, .81, .72),
    "medical_packaging": (.68, .75, .74), "olive_fabric": (.28, .33, .22),
    "rubber": (.085, .08, .075), "laces": (.43, .39, .27),
    "black_zipper": (.045, .05, .055), "webbing": (.13, .15, .12),
    "transparent_pet": (.60, .69, .70), "blue_water": (.22, .45, .53),
    "dark_plastic": (.085, .09, .10), "dark_webbing": (.14, .16, .12),
    "aluminum_foil": (.48, .52, .55), "clear_blister": (.70, .74, .73),
    "cream_tablet": (.84, .80, .66), "teal_card": (.10, .41, .43),
    "olive_cloth": (.27, .30, .20), "tan_paper": (.66, .54, .37),
    "black_elastic": (.055, .065, .065), "oxblood_hardcase": (.35, .095, .085),
    "ivory_symbol": (.85, .81, .70), "red_skin": (.51, .11, .075),
    "green_shoulder": (.23, .40, .12), "brown_stem": (.25, .14, .065),
    "sage_label": (.38, .47, .32), "cream_ink": (.72, .67, .50),
}


def material(name):
    cached = bpy.data.materials.get("LL_ORIGINAL_" + name)
    if cached:
        return cached
    if name not in PALETTE:
        raise ValueError("Unapproved material slot: " + name)
    mat = bpy.data.materials.new("LL_ORIGINAL_" + name)
    mat.diffuse_color = (*PALETTE[name], 1.0)
    mat.use_nodes = True
    principled = mat.node_tree.nodes.get("Principled BSDF")
    principled.inputs["Base Color"].default_value = (*PALETTE[name], 1.0)
    principled.inputs["Roughness"].default_value = 0.34 if name in ("steel", "forged_steel", "aluminum_foil", "brass") else 0.77
    principled.inputs["Metallic"].default_value = 0.75 if name in ("steel", "forged_steel", "aluminum_foil", "brass", "metal_zipper") else 0.0
    return mat


def assign(obj, slot, name):
    obj.name = "LL_ORIGINAL_" + name
    obj.data.materials.append(material(slot))
    return obj


def box(name, location, size, slot, bevel=0.03):
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    obj = bpy.context.object
    obj.dimensions = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel:
        modifier = obj.modifiers.new("functional_edge_bevel", "BEVEL")
        modifier.width = min(min(size) * .45, bevel)
        modifier.segments = 2
        obj.modifiers.new("weighted_corner_normals", "WEIGHTED_NORMAL")
    return assign(obj, slot, name)


def cylinder(name, location, radius, depth, slot, axis="Z", vertices=16):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=location)
    obj = bpy.context.object
    if axis == "X":
        obj.rotation_euler[1] = math.pi / 2
    elif axis == "Y":
        obj.rotation_euler[0] = math.pi / 2
    return assign(obj, slot, name)


def sphere(name, location, size, slot):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, location=location)
    obj = bpy.context.object
    obj.dimensions = size
    return assign(obj, slot, name)


def tube(name, points, radius, slot, cyclic=False):
    curve = bpy.data.curves.new(name, "CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = 12
    curve.bevel_depth = radius
    curve.bevel_resolution = 2
    spline = curve.splines.new("POLY")
    spline.points.add(len(points) - 1)
    for point, coord in zip(spline.points, points):
        point.co = (*coord, 1)
    spline.use_cyclic_u = cyclic
    obj = bpy.data.objects.new(name, curve)
    bpy.context.scene.collection.objects.link(obj)
    return assign(obj, slot, name)


def loop(name, center, radii, slot, thickness=.025, points=20):
    cx, cy, cz = center
    rx, ry = radii
    return tube(name, [(cx + rx * math.cos(i * 2 * math.pi / points),
                        cy + ry * math.sin(i * 2 * math.pi / points), cz)
                       for i in range(points)], thickness, slot, cyclic=True)


def panel(name, points, thickness, slot):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(points, [], [list(range(len(points)))])
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    solid = obj.modifiers.new("physical_fabric_thickness", "SOLIDIFY")
    solid.thickness = thickness
    return assign(obj, slot, name)


def art(a):
    """Unique geometry constructions, never based on external sprite silhouettes."""
    ident = a["archetype"]
    m = a["material_slots"]
    primary = m[0]
    if ident == "antler_pair":
        for side in (-1, 1):
            x = side * .23
            pts = [(x, 0, .04), (x + side * .06, 0, .25),
                   (x + side * .13, -.02, .54), (x + side * .08, -.03, .84)]
            tube("original_antler_trunk", pts, .037, primary)
            cylinder("rough_coronet", pts[0], .07, .08, m[1])
            for j, t in enumerate((.25, .52, .72)):
                p = pts[min(3, j + 1)]
                tube("naturally_asymmetric_tine", [p, (p[0] + side * (.12 + j * .025),
                     p[1] + .06 * (-1) ** j, p[2] + .15 + t * .1)], .018, primary)
    elif ident in ("leather_apron", "plastic_apron"):
        panel("single_tapered_bib", [(-.29, 0, .10), (.29, 0, .10), (.22, 0, .84),
              (-.21, 0, .84)], .028 if ident == "leather_apron" else .009, primary)
        tube("neck_loop", [(-.17, 0, .78), (-.11, .02, 1.05), (.11, .02, 1.05),
             (.17, 0, .78)], .019, m[1])
        for side in (-1, 1):
            tube("waist_tie", [(side * .22, .01, .51), (side * .45, .02, .48),
                 (side * .55, .0, .42)], .012, m[1])
        if ident == "leather_apron":
            box("chest_pocket", (0, -.023, .64), (.19, .025, .16), primary, .01)
            box("original_small_buckle", (-.18, -.021, .75), (.045, .02, .04), m[2], .005)
    elif ident in ("canvas_bandolier", "leather_bandolier"):
        # A folded, empty diagonal strap, not a pre-filled copied cartridge belt.
        tube("crossbody_strap", [(-.33, -.02, .06), (-.15, -.02, .36),
             (.07, -.01, .68), (.24, .02, .83), (.36, .02, .70),
             (.17, .02, .32), (-.10, -.02, .03)], .05, primary)
        n = 8 if ident == "canvas_bandolier" else 6
        for j in range(n):
            t = j / max(1, n - 1)
            box("empty_stitched_sleeve", (-.20 + .41 * t, -.07, .23 + .36 * t),
                (.06, .045, .12), primary, .012)
        box("adjustment_buckle", (.32, -.03, .66), (.10, .032, .09), m[-1], .009)
    elif ident == "feed_sack":
        sphere("bulging_plant_feed_sack", (0, 0, .36), (.54, .39, .68), primary)
        box("folded_stitched_top", (0, 0, .74), (.50, .23, .09), primary, .022)
        panel("original_grain_emblem", [(-.1, -.199, .33), (.0, -.202, .48),
              (.1, -.199, .33)], .002, m[1])
        tube("closure_stitch", [(-.23, -.02, .78), (.23, -.02, .78)], .007, m[2])
    elif ident == "claw_hammer":
        cylinder("ash_grip", (0, 0, .32), .065, .63, primary)
        box("striking_head", (0, 0, .68), (.32, .12, .13), m[1], .025)
        for y in (-.042, .042):
            tube("split_curved_claw", [(-.14, y, .70), (-.30, y, .76),
                 (-.39, y, .67)], .027, m[1])
    elif ident == "rope_coil":
        for j in range(5):
            loop("independent_tan_rope_turn", (0, .012 * j, .04 + .013 * j),
                 (.27 - .026 * j, .19 - .017 * j), primary, .016)
        tube("loose_rope_end", [(.19, -.1, .10), (.33, -.13, .10),
             (.39, -.09, .03)], .016, primary)
    elif ident == "leather_jacket":
        box("hollow_jacket_torso_proxy", (0, 0, .47), (.51, .23, .64), primary, .05)
        for side in (-1, 1):
            cylinder("original_tapered_sleeve", (side * .37, 0, .43), .105, .55, primary)
            box("cuff", (side * .37, 0, .18), (.21, .20, .065), primary, .01)
        box("folded_collar", (0, -.09, .80), (.43, .12, .11), primary, .018)
        box("center_zipper", (0, -.126, .46), (.015, .012, .57), m[2], .002)
    elif ident == "duct_tape":
        loop("adhesive_tape_wound_roll", (0, 0, .12), (.28, .28), primary, .095)
        loop("exposed_kraft_core", (0, 0, .12), (.17, .17), m[1], .025)
        panel("attached_folding_tape_end", [(.24, 0, .11), (.43, 0, .10),
              (.43, -.09, .10), (.24, -.09, .11)], .012, primary)
    elif ident == "flat_screwdriver":
        cylinder("fluted_amber_handle", (0, 0, .20), .10, .38, primary)
        cylinder("straight_steel_shank", (0, 0, .54), .028, .34, m[1])
        box("flattened_driver_tip", (0, 0, .73), (.065, .014, .07), m[1], .002)
    elif ident == "hatchet":
        cylinder("short_hickory_handle", (0, 0, .37), .07, .73, primary)
        box("forged_hatchet_eye", (0, 0, .73), (.17, .11, .20), m[1], .026)
        panel("thinning_wide_cutting_blade", [(-.06, 0, .83), (.31, 0, .88),
              (.35, 0, .69), (-.06, 0, .64)], .075, m[1])
    elif ident == "sterile_bandage":
        for j in range(4):
            box("folded_original_gauze_layer", (0, 0, .015 + j * .012),
                (.48 - j * .018, .37 - j * .012, .011), primary, .004)
        panel("lifted_gauze_corner", [(.12, .14, .06), (.27, .15, .07),
              (.24, .29, .13)], .009, primary)
    elif ident == "hiking_boots":
        for side in (-1, 1):
            x = side * .26
            box("rubber_tread_sole", (x, -.12, .06), (.35, .53, .12), m[2], .055)
            box("original_leather_foot", (x, -.12, .19), (.31, .45, .20), primary, .055)
            box("padded_ankle_upper", (x, .03, .39), (.27, .27, .37), m[1], .06)
            for j in range(4):
                tube("boot_lace_cross", [(x-.095, -.26+j*.052, .30+j*.04),
                     (x+.095, -.26+j*.052, .30+j*.04)], .009, m[3])
    elif ident == "duffel_bag":
        cylinder("soft_horizontal_canvas_body", (0, 0, .25), .23, .76, primary, "X")
        box("continuous_top_zip", (0, -.01, .46), (.64, .022, .015), m[1], .004)
        for x in (-.23, .23):
            tube("arched_carry_handle", [(x-.08, -.06, .44), (x-.08, -.06, .60),
                 (x+.08, -.06, .60), (x+.08, -.06, .44)], .019, m[2])
        tube("detached_shoulder_webbing", [(-.35, .08, .34), (0, .14, .73),
             (.35, .08, .34)], .022, m[2])
    elif ident == "water_bottle":
        cylinder("clear_ribbed_pet_body", (0, 0, .37), .17, .63, primary)
        for j in range(4):
            loop("original_pet_grip_rib", (0, 0, .22 + j * .12), (.17, .17), primary, .009)
        cylinder("dark_screw_cap", (0, 0, .77), .11, .13, m[2])
        cylinder("water_fill_surface_proxy", (0, 0, .28), .158, .44, m[1])
    elif ident == "backpack":
        box("loaded_olive_canvas_body", (0, 0, .39), (.63, .36, .72), primary, .11)
        box("domed_roll_top_flap", (0, -.07, .81), (.59, .33, .17), primary, .08)
        box("lower_front_pocket", (0, -.21, .23), (.42, .12, .32), primary, .042)
        for side in (-1, 1):
            box("buckle", (side * .18, -.277, .42), (.075, .024, .08), m[2], .009)
            tube("backpack_shoulder_strap", [(side * .24, .18, .79),
                 (side * .27, .36, .46), (side * .22, .18, .12)], .037, m[1])
    elif ident == "antibiotic_tablets":
        box("silver_blister_foil", (0, 0, .03), (.42, .70, .036), primary, .014)
        for side in (-1, 1):
            for j in range(4):
                sphere("individual_cream_tablet_blister", (side * .11, -.23+j*.15, .065),
                       (.15, .125, .055), m[2])
        box("original_teal_card_tab", (0, .37, .029), (.40, .10, .022), m[3], .012)
    elif ident == "field_notebook":
        box("tan_page_block", (0, 0, .034), (.50, .68, .05), m[1], .017)
        box("olive_cloth_cover", (0, 0, .065), (.53, .72, .026), primary, .018)
        tube("black_elastic_closure", [(.18, -.35, .08), (.18, .35, .08)], .012, m[2])
        box("bound_stitched_spine", (-.25, 0, .045), (.034, .70, .06), primary, .008)
    elif ident == "first_aid_case":
        box("oxblood_hardcase_shell", (0, 0, .31), (.70, .33, .49), primary, .075)
        tube("integral_carry_handle", [(-.15, 0, .56), (-.15, 0, .72),
             (.15, 0, .72), (.15, 0, .56)], .027, primary)
        for x in (-.23, .23):
            box("metal_front_clasp", (x, -.18, .37), (.075, .024, .13), m[2], .009)
        box("ivory_cross_vertical", (0, -.181, .39), (.066, .008, .18), m[1], .002)
        box("ivory_cross_horizontal", (0, -.182, .39), (.16, .008, .059), m[1], .002)
    elif ident == "shoe_box":
        box("kraft_shoe_storage_carton", (0, 0, .20), (.72, .47, .35), primary, .016)
        box("overhanging_removable_lid", (0, 0, .385), (.75, .50, .055), primary, .012)
        tube("front_finger_notch_rim", [(-.065, -.251, .39), (0, -.253, .35),
             (.065, -.251, .39)], .008, primary)
    elif ident == "apple":
        sphere("asymmetric_red_fruit_body", (0, 0, .25), (.55, .53, .48), primary)
        sphere("subtle_green_shoulder", (-.08, 0, .47), (.24, .19, .06), m[1])
        tube("short_brown_stem", [(0, 0, .45), (.015, 0, .57)], .021, m[2])
    elif ident == "bean_tin":
        cylinder("original_rolled_steel_can", (0, 0, .36), .27, .61, primary)
        cylinder("separate_steel_top_lid", (0, 0, .68), .28, .035, primary)
        cylinder("generic_sage_paper_label", (0, 0, .34), .274, .43, m[1])
        box("plain_bean_emblem_panel", (0, -.279, .36), (.24, .014, .17), m[2], .009)
    else:
        raise ValueError("Unimplemented independently authored original archetype " + ident)


def hash_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def build_one(asset, output):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    art(asset)
    # Source curves are converted to editable meshes for GLB export; original
    # shape provenance remains the deterministic parametric authoring script.
    for obj in list(bpy.context.scene.objects):
        if obj.type == "CURVE":
            bpy.ops.object.select_all(action="DESELECT")
            obj.select_set(True)
            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.convert(target="MESH")
    meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    if len(meshes) < 3:
        raise ValueError("Independent original mesh needs at least 3 authored components")
    bpy.context.view_layer.update()
    corners = [o.matrix_world @ Vector(p) for o in meshes for p in o.bound_box]
    lo = [min(v[i] for v in corners) for i in range(3)]
    hi = [max(v[i] for v in corners) for i in range(3)]
    actual = [hi[i] - lo[i] for i in range(3)]
    if any(v <= .001 or v > 100 or not math.isfinite(v) for v in actual):
        raise ValueError("Source geometry invalid / degenerate")
    expected = asset["nominal_dimensions_m"]
    factors = [expected[i] / actual[i] for i in range(3)]
    origin = [(lo[i] + hi[i]) / 2 for i in range(2)] + [lo[2]]
    for obj in meshes:
        obj.location.x = (obj.location.x - origin[0]) * factors[0]
        obj.location.y = (obj.location.y - origin[1]) * factors[1]
        obj.location.z = (obj.location.z - origin[2]) * factors[2]
        for i in range(3):
            obj.scale[i] *= factors[i]
    folder = output / asset["asset_id"]
    folder.mkdir(parents=True, exist_ok=True)
    blend = folder / (asset["asset_id"] + ".blend")
    bpy.ops.wm.save_as_mainfile(filepath=str(blend.resolve()))
    bpy.ops.object.select_all(action="DESELECT")
    for obj in meshes:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    glb = folder / (asset["asset_id"] + ".glb")
    bpy.ops.export_scene.gltf(filepath=str(glb.resolve()), export_format="GLB", use_selection=True)
    evidence = {
        "asset_id": asset["asset_id"], "source": "INDEPENDENT_BLENDER_PARAMETRIC_AUTHORING",
        "source_images_or_textures_imported": False, "base_geometry_from_pz": False,
        "mesh_objects": len(meshes), "blender_source_sha256": hash_file(blend),
        "glb_sha256": hash_file(glb), "nominal_dimensions_m": expected,
        "technical_preview": True, "semantic_admitted": False,
        "f11_approved": False, "f12_approved": False, "godot_tested": False,
        "iphone_verified": False, "founder_golden_approved": False,
    }
    (folder / "authorship_receipt.json").write_text(json.dumps(evidence, indent=2) + "\n")
    print("LL_ORIGINAL_3D_CREATED", asset["asset_id"], len(meshes))
    return evidence


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--recipes", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--ids", default="", help="comma-separated explicit reviewed preview IDs")
    parser.add_argument("--max-assets", type=int, default=2)
    parser.add_argument("--start-index", type=int, default=0,
                        help="0-based bounded technical preview window over 23 original proposals")
    opts = parser.parse_args(argv)
    if not 1 <= opts.max_assets <= 4:
        raise ValueError("Max 4 previews per bounded CI run")
    if not 0 <= opts.start_index < 23:
        raise ValueError("Preview start index must lie within 23 original proposals")
    doc = json.loads(opts.recipes.read_text())
    if doc.get("count") != 23 or doc.get("source_art_pixels_imported") is not False:
        raise ValueError("Untrusted original authoring manifest")
    ids = opts.ids.split(",") if opts.ids else [a["asset_id"] for a in doc["assets"][opts.start_index:opts.start_index + opts.max_assets]]
    if len(ids) > opts.max_assets or len(set(ids)) != len(ids):
        raise ValueError("Too many/duplicate preview IDs")
    index = {a["asset_id"]: a for a in doc["assets"]}
    out = []
    for ident in ids:
        a = index.get(ident)
        if not a or a["admission"].get("production_render_admitted") is not False:
            raise ValueError("Untrusted technical-preview admission")
        out.append(build_one(a, opts.output))
    opts.output.mkdir(parents=True, exist_ok=True)
    (opts.output / "technical_preview_report.json").write_text(json.dumps({
        "source_manifest_count": 23, "generated": out, "golden_approved": False,
        "status": "ORIGINAL_GEOMETRY_TECHNICAL_PREVIEW_ONLY",
    }, indent=2) + "\n")


if __name__ == "__main__":
    main()
