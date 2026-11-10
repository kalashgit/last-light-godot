"""Four provisional *human-inspected* physical baselines for the VLM experiment.

They are not independent vision-model inferences, Golden meshes, or final
production geometry. Original primitives/materials are merely fair, editable
starting points for comparing real VLM defect recognition against manual truth.
"""
from __future__ import annotations

import math
from pathlib import Path

from PIL import Image

from .contract import sha256, validate
from .seed_recipes import box, cyl, mat, note, part, tube


def lathe(name: str, material: str, profile: list[list[float]], *, pos=(0, 0, 0),
          observed=True, confidence=.82):
    return part(name, "lathe", material, pos,
                {"profile": profile, "vertices": 40}, observed=observed, confidence=confidence)


def panel(name: str, material: str, points: list[list[float]], *, depth=.035,
          pos=(0, 0, 0), rotation=(90, 0, 0), observed=True):
    return part(name, "polygon_extrude", material, pos,
                {"points": points, "depth": depth, "bevel": .006},
                rotation=rotation, observed=observed)


def _avocado():
    mats = [mat("dark_pebbled_skin", "food", (.18, .165, .085), 0, .88, .38, "scuffed"),
            mat("olive_skin", "food", (.24, .27, .095), 0, .92, .18, "scuffed"),
            mat("pebble_highlights", "food", (.30, .29, .145), 0, .91, .22),
            mat("stem_brown", "food", (.18, .13, .065), 0, .93, .24)]
    body = lathe("pear_shaped_fruit_body", "dark_pebbled_skin", [
        [.001, 0], [.16, .014], [.30, .065], [.40, .19], [.44, .32],
        [.43, .46], [.36, .62], [.26, .77], [.14, .87], [.055, .94],
        [.001, .97]])
    body["geometry"]["scale_xy"] = [.93, .83]
    body["rotation_deg"] = [0, 27, 0]
    components = [body,
        lathe("tapered_skin_tip", "olive_skin", [
            [.001, 0], [.08, .012], [.11, .06], [.07, .12], [.001, .15]],
            pos=(.37, 0, .70)),
        cyl("subtle_stem_cap", "stem_brown", (.42, 0, .84), .035, .032,
            observed=False, confidence=.3),
    ]
    # Small 3-D skin nodules, deterministically distributed over the visible
    # hemisphere. These are actual mesh components, not a baked source image.
    for row, (z, radius) in enumerate(((.16, .33), (.29, .41), (.42, .39),
                                      (.56, .34), (.69, .27), (.78, .19))):
        for column in range(7):
            x_fraction = (column - 3 + (row % 2) * .35) / 4.15
            x = x_fraction * radius
            y = -.82 * math.sqrt(max(.001, radius * radius - x * x))
            angle = math.radians(27)
            placed_x = x * math.cos(angle) + z * math.sin(angle)
            placed_z = -x * math.sin(angle) + z * math.cos(angle)
            components.append(cyl(
                f"skin_nodule_r{row}_c{column}", "pebble_highlights",
                (placed_x, y - .008, placed_z), .012 + .003 * ((row + column) % 3),
                .008, vertices=12, rotation=(90, 0, 0), confidence=.60))
    obs = [note("pear_shaped_fruit_body", "Dark pebbled pear-shaped avocado, rounded wider bottom and narrow upper end", .97),
           note("tapered_skin_tip", "Visible tapered end shares uneven green-brown skin", .78)]
    return "food_organic", "Whole uncut avocado", mats, components, obs, [note("subtle_stem_cap", "Top stem uncertain in one image", .3)], "pear silhouette, closed dimpled skin", [1.1, .9]


def _shelf():
    mats = [mat("weathered_oak", "paint", (.52, .31, .15), 0, .81, .22, "scuffed"),
            mat("end_grain", "paint", (.34, .19, .10), 0, .9, .28, "scuffed"),
            mat("sunlit_grain", "paint", (.67, .44, .22), 0, .9, .18),
            mat("hardware", "metal", (.31, .27, .2), .55, .55, .35)]
    components = [
        box("horizontal_shelf_plank", "weathered_oak", (0, -.025, .86), (1.90, .44, .15), .014),
        box("front_plank_fascia", "end_grain", (0, -.247, .816), (1.92, .026, .105), .009),
        box("left_wall_mount", "end_grain", (-.68, .225, .67), (.17, .10, .94), .018),
        box("right_wall_mount", "end_grain", (.68, .225, .67), (.17, .10, .94), .018),
    ]
    for side, x in (("left", -.68), ("right", .68)):
        # Panels are made in the y-z plane; the previous version accidentally
        # put the triangular gussets in the x-z plane and hid them behind the shelf.
        components.append(panel(f"{side}_triangular_brace", "weathered_oak",
                                [[-.205, .39], [.215, .075], [.215, .39]],
                                depth=.13, pos=(x, 0, .405), rotation=(90, 0, 90)))
        components.append(tube(f"{side}_diagonal_brace_beam", "end_grain",
                               [(x, -.19, .78), (x, .18, .46)], .04))
        foot = x - .085 if x < 0 else x + .085
        tip = x + .16 if x < 0 else x - .16
        components.append(panel(f"{side}_visible_front_gusset", "end_grain",
                                [[foot - .045, .38], [foot + .045, .38],
                                 [tip + .045, .795], [tip - .045, .795]],
                                depth=.05, pos=(0, -.245, 0)))
        for suffix, z in (("upper", 1.06), ("lower", .34)):
            components.append(cyl(f"{side}_{suffix}_mount_screw", "hardware",
                                  (x, .163, z), .023, .012, vertices=12,
                                  rotation=(90, 0, 0)))
    for idx, y in enumerate((-.16, -.045, .075)):
        components.append(tube(f"top_plank_grain_{idx}", "sunlit_grain",
                               [(-.84, y, .939),(-.34, y + .009, .939),
                                (.16, y - .006, .939),(.81, y + .004, .939)], .006))
    obs = [note("horizontal_shelf_plank", "Wide thick wood ledge with visible top and front edge", .98),
           note("left_wall_mount", "Left vertical wooden wall mount projects above and below shelf", .93),
           note("right_wall_mount", "Right vertical wooden wall mount projects above and below shelf", .93),
           note("left_triangular_brace", "Angular underside support below left side", .87),
           note("right_triangular_brace", "Angular underside support below right side", .87)]
    return "furniture_fixtures", "Wall-mounted wooden display shelf", mats, components, obs, [], "rectangular horizontal shelf on two uprights", [1.9, .4]


def _apron():
    mats = [mat("seafoam_cotton", "fabric", (.40, .68, .62), 0, .95, .19, "scuffed"),
            mat("pink_striped_cotton", "fabric", (.88, .53, .62), 0, .93, .08),
            mat("pale_cream_trim", "fabric", (.88, .79, .68), 0, .93, .04),
            mat("coral_motif", "paint", (.84, .42, .48), 0, .86, .04),
            mat("motif_vanilla", "fabric", (.96, .77, .68), 0, .88, .04),
            mat("motif_waffle", "fabric", (.67, .43, .22), 0, .85, .10)]
    components = [
        panel("flared_lower_apron_skirt", "pale_cream_trim", [
            [-.39, -.68], [.39, -.68], [.36, -.31], [.27, -.1], [-.27, -.1], [-.36, -.31]],
            pos=(0, 0, .71)),
        panel("seafoam_upper_bib", "seafoam_cotton", [
            [-.28, -.12], [.28, -.12], [.19, .18], [.14, .63], [-.14, .63], [-.19, .18]],
            pos=(0, -.019, .71)),
        tube("neck_loop", "seafoam_cotton", [(-.14, 0, 1.31),(-.16, .01, 1.45),
                (-.18, .03, 1.53),(-.13, .05, 1.62),(-.05, .06, 1.65),
                (.05, .06, 1.65),(.13, .05, 1.62),(.18, .03, 1.54),
                (.16, .01, 1.45),(.14, 0, 1.31)], .020),
        tube("left_waist_tie", "seafoam_cotton", [(-.27, 0, .72),(-.49, -.02, .71),
                (-.59, -.05, .52),(-.55, -.08, .39)], .025),
        tube("right_waist_tie", "seafoam_cotton", [(.27, 0, .72),(.49, -.02, .71),
                (.59, -.05, .52),(.55, -.08, .39)], .025),
        panel("motif_waffle_cone", "motif_waffle", [[-.075, -.045],[.075, -.045],[0, -.24]],
              depth=.010, pos=(0, -.044, 1.14)),
        panel("upper_bib_pink_trim", "pink_striped_cotton",
              [[-.14, .58],[.14, .58],[.15, .51],[-.15, .51]],
              depth=.010, pos=(0, -.045, .71)),
    ]
    # The source has alternating pale/pink vertical stripes, not a solid pink
    # lower panel. Individual narrow cloth strips remain editable in Blender.
    for index in range(7):
        x_center = -.32 + index * .106
        components.append(panel(f"vertical_pink_stripe_{index}", "pink_striped_cotton",
                                [[x_center - .030, -.665], [x_center + .030, -.665],
                                 [x_center + .025, -.270], [x_center - .025, -.270]],
                                depth=.010, pos=(0, -.027, .71)))
    components.extend([
        tube("curved_lower_hem", "pink_striped_cotton",
             [(-.38, -.035, .04),(-.19, -.035, .035),(.03, -.035, .03),
              (.24, -.035, .035),(.38, -.035, .04)], .010),
        tube("waist_seam", "seafoam_cotton",
             [(-.33, -.043, .62),(-.12, -.045, .61),(.12, -.045, .61),(.33, -.043, .62)], .016),
        tube("left_bib_stitching", "pale_cream_trim",
             [(-.27, -.040, .61),(-.235, -.042, .77),(-.19, -.042, .90),
              (-.145, -.042, 1.10),(-.135, -.042, 1.30)], .007),
        tube("right_bib_stitching", "pale_cream_trim",
             [(.27, -.040, .61),(.235, -.042, .77),(.19, -.042, .90),
              (.145, -.042, 1.10),(.135, -.042, 1.30)], .007),
        cyl("ice_cream_scoop_pink", "coral_motif", (-.032, -.062, 1.20),
            .077, .010, scale_xy=(1, .89), rotation=(90, 0, 0)),
        cyl("ice_cream_scoop_vanilla", "motif_vanilla", (.025, -.067, 1.263),
            .061, .010, scale_xy=(1, .89), rotation=(90, 0, 0)),
        cyl("ice_cream_scoop_coral", "coral_motif", (.071, -.072, 1.19),
            .057, .009, scale_xy=(1, .89), rotation=(90, 0, 0)),
    ])
    obs = [note("flared_lower_apron_skirt", "Pink-striped flaring lower fabric panel", .97),
           note("seafoam_upper_bib", "Seafoam-green upper bib narrowing into the neck strap", .96),
           note("neck_loop", "One fabric strap arcs over the neck opening", .96),
           note("left_waist_tie", "Free hanging tie on left", .9),
           note("right_waist_tie", "Free hanging tie on right", .9),
           note("vertical_pink_stripe_0", "Alternating vertical pink-and-white lower skirt bands", .95),
           note("ice_cream_scoop_pink", "Two-color original stylized ice-cream motif on center bib", .89)]
    return "clothing_armor", "Lightweight kitchen apron", mats, components, obs, [], "flared apron and open neck loop", [.85, .15]


def _backpack():
    mats = [mat("charcoal_canvas", "fabric", (.065, .065, .07), 0, .88, .35, "scuffed"),
            mat("aged_black_nylon", "fabric", (.14, .14, .145), 0, .84, .32, "scuffed"),
            mat("seam_webbing", "fabric", (.21, .20, .20), 0, .92, .30),
            mat("zipper_gunmetal", "metal", (.40, .38, .34), .55, .62, .25)]
    components = [
        box("main_pack_body", "charcoal_canvas", (0, 0, .69), (.91, .46, 1.15), .135),
        box("rounded_top_shell", "charcoal_canvas", (0, 0, 1.20), (.84, .43, .24), .09),
        box("upper_front_panel", "aged_black_nylon", (0, -.247, .99), (.79, .065, .39), .075),
        box("large_front_pocket", "aged_black_nylon", (0, -.317, .48), (.79, .20, .52), .082),
        box("small_upper_patch", "charcoal_canvas", (0, -.294, 1.08), (.48, .026, .14), .035),
        tube("top_grab_handle", "aged_black_nylon", [(-.19, 0, 1.21),(-.17, 0, 1.34),
             (-.05, 0, 1.39),(.12, 0, 1.37),(.19, 0, 1.21)], .036),
        tube("left_shoulder_strap", "charcoal_canvas", [(-.37, .20, 1.13),(-.48, .23, .91),
             (-.49, .26, .35),(-.36, .20, .12)], .053),
        tube("right_shoulder_strap", "charcoal_canvas", [(.37, .20, 1.13),(.48, .23, .91),
             (.49, .26, .35),(.36, .20, .12)], .053),
        tube("front_pocket_zipper", "zipper_gunmetal", [(-.33, -.395, .71),
             (0, -.395, .735),(.33, -.395, .71)], .009),
    ]
    components.extend([
        tube("outer_front_seam_left", "seam_webbing",
             [(-.40, -.263, 1.12),(-.43, -.269, .97),(-.43, -.280, .76),
              (-.42, -.285, .40),(-.37, -.275, .24)], .009),
        tube("outer_front_seam_right", "seam_webbing",
             [(.40, -.263, 1.12),(.43, -.269, .97),(.43, -.280, .76),
              (.42, -.285, .40),(.37, -.275, .24)], .009),
        tube("upper_pocket_piping", "seam_webbing",
             [(-.36, -.287, .87),(-.28, -.29, .81),(0, -.29, .81),
              (.28, -.29, .81),(.36, -.287, .87)], .010),
        tube("lower_pocket_lower_piping", "seam_webbing",
             [(-.32, -.427, .25),(0, -.427, .22),(.32, -.427, .25)], .010),
        tube("front_pocket_pull_tab", "zipper_gunmetal",
             [(.27, -.425, .73),(.27, -.442, .675)], .014),
        box("left_side_compression_webbing", "seam_webbing",
            (-.459, 0, .56), (.028, .46, .042), .010),
        box("right_side_compression_webbing", "seam_webbing",
            (.459, 0, .56), (.028, .46, .042), .010),
    ])
    obs = [note("main_pack_body", "Tall black rectangular canvas daypack with rounded volume", .97),
           note("upper_front_panel", "Top exterior rounded front section", .88),
           note("large_front_pocket", "One broad outward front pocket", .95),
           note("small_upper_patch", "Small dark rectangular patch above front pouch", .86),
           note("top_grab_handle", "One clearly visible loop handle above main shell", .98),
           note("left_shoulder_strap", "Dark side strap visible left of shell", .89),
           note("front_pocket_zipper", "Narrow horizontal zipper on pocket face", .81)]
    return ("bags_equipment", "Empty small everyday daypack", mats, components, obs, [
        note("right_shoulder_strap", "Opposite back strap inferred from ordinary bag construction", .52)],
        "rounded dark backpack with forward rectangular pocket and top handle", [.95, .55])


FACTORIES = {
    "food_avocado_0027": _avocado,
    "furniture_shelf_0181": _shelf,
    "clothing_apron_0001": _apron,
    "backpack_0045": _backpack,
}


def build_seed(case_id: str, source: Path, *, reference_id: str) -> dict:
    if case_id not in FACTORIES:
        raise ValueError("no human-inspected physical baseline for this case")
    family, purpose, materials, components, observed, assumptions, silhouette, footprint = FACTORIES[case_id]()
    with Image.open(source) as image:
        size = list(image.size)
    recipe = {
        "schema": "last-light.recipe-architect.v1",
        "identity": {"candidate_id": "benchmark_" + case_id + "_v2",
                     "source_reference_id": reference_id + "_founder_sheet_pilot",
                     "source_sha256": sha256(source), "source_rights": "founder_original_pending_review",
                     "asset_family": family, "recipe_version": 2,
                     "generation_method": "pixel_inspected_seed", "canonical_id": None},
        "visual_analysis": {"provider": "human_observed_quality_refinement_20261110",
                            "pixels_inspected": True, "image_dimensions": size,
                            "probable_function": purpose, "category": family,
                            "observations": observed, "assumptions": assumptions,
                            "artifacts": ["Single-view source with white background; unseen back and functional internals uncertain"],
                            "confidence": .78},
        "components": components, "materials": materials,
        "gameplay": {"collision": "box", "movable": True, "interactable_parts": [],
                     "container_openings": [], "damage_states": ["intact", "worn"],
                     "footprint_m": footprint, "animations": [], "attachment_points": []},
        "render": {"headings": 16, "resolution": 128, "camera_azimuth_deg": 315,
                   "camera_elevation_deg": 35.264, "orthographic_scale": 2.45,
                   "key_light": "upper_left", "assembly_scale": [1, 1, 1]},
        "quality": {"expected_silhouette": silhouette,
                    "qa_checks": ["source_sha", "editable_blend", "glb_mesh_count", "render_comparison", "founder_review"],
                    "technical_status": "CANDIDATE_PENDING_QA", "golden_approved": False,
                    "founder_review": "NOT_GOLDEN"},
        "tuning": {"scale_step": .08, "max_corrections": 2},
    }
    if case_id == "clothing_apron_0001":
        recipe["render"]["camera_azimuth_deg"] = 275
        recipe["render"]["orthographic_scale"] = 2.15
    elif case_id == "furniture_shelf_0181":
        recipe["render"]["camera_azimuth_deg"] = 275
        recipe["render"]["orthographic_scale"] = 2.35
    elif case_id == "backpack_0045":
        recipe["render"]["camera_azimuth_deg"] = 290
        recipe["render"]["orthographic_scale"] = 2.20
    elif case_id == "food_avocado_0027":
        recipe["render"]["camera_azimuth_deg"] = 275
        recipe["render"]["orthographic_scale"] = 2.10
    validate(recipe, source, full_schema=True)
    return recipe
