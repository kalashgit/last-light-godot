"""Four provisional *human-inspected* physical baselines for the VLM experiment.

They are not independent vision-model inferences, Golden meshes, or final
production geometry. Original primitives/materials are merely fair, editable
starting points for comparing real VLM defect recognition against manual truth.
"""
from __future__ import annotations

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
    mats = [mat("dark_pebbled_skin", "food", (.20, .19, .085), 0, .88, .28),
            mat("olive_skin", "food", (.25, .31, .09), 0, .92, .18),
            mat("stem_brown", "food", (.18, .13, .065), 0, .93, .24)]
    components = [
        lathe("pear_shaped_fruit_body", "dark_pebbled_skin", [
            [.001, 0], [.18, .025], [.34, .11], [.42, .27], [.39, .46], [.30, .63],
            [.20, .78], [.09, .87], [.001, .89]]),
        lathe("tapered_skin_tip", "olive_skin", [
            [.001, 0], [.08, .012], [.13, .05], [.10, .13], [.001, .15]], pos=(0, 0, .78)),
        cyl("subtle_stem_cap", "stem_brown", (0, 0, .93), .046, .045, observed=False, confidence=.3),
    ]
    obs = [note("pear_shaped_fruit_body", "Dark pebbled pear-shaped avocado, rounded wider bottom and narrow upper end", .97),
           note("tapered_skin_tip", "Visible tapered end shares uneven green-brown skin", .78)]
    return "food_organic", "Whole uncut avocado", mats, components, obs, [note("subtle_stem_cap", "Top stem uncertain in one image", .3)], "pear silhouette, closed dimpled skin", [1.1, .9]


def _shelf():
    mats = [mat("weathered_oak", "paint", (.52, .31, .15), 0, .81, .22),
            mat("end_grain", "paint", (.36, .19, .09), 0, .9, .28),
            mat("hardware", "metal", (.31, .27, .2), .55, .55, .35)]
    components = [
        box("horizontal_shelf_plank", "weathered_oak", (0, -.01, .86), (1.9, .40, .13), .015),
        box("left_wall_mount", "end_grain", (-.73, .16, .62), (.14, .085, .88), .01),
        box("right_wall_mount", "end_grain", (.73, .16, .62), (.14, .085, .88), .01),
        panel("left_triangular_brace", "weathered_oak", [[-.77, .4],[-.55, .65],[-.77, .77]],
              depth=.12, pos=(0, .07, 0)),
        panel("right_triangular_brace", "weathered_oak", [[.77, .4],[.55, .65],[.77, .77]],
              depth=.12, pos=(0, .07, 0)),
        cyl("left_mount_screw", "hardware", (-.73, -.002, .88), .025, .013, observed=True),
        cyl("right_mount_screw", "hardware", (.73, -.002, .88), .025, .013, observed=True),
    ]
    obs = [note("horizontal_shelf_plank", "Wide thick wood ledge with visible top and front edge", .98),
           note("left_wall_mount", "Left vertical wooden wall mount projects above and below shelf", .93),
           note("right_wall_mount", "Right vertical wooden wall mount projects above and below shelf", .93),
           note("left_triangular_brace", "Angular underside support below left side", .87),
           note("right_triangular_brace", "Angular underside support below right side", .87)]
    return "furniture_fixtures", "Wall-mounted wooden display shelf", mats, components, obs, [], "rectangular horizontal shelf on two uprights", [1.9, .4]


def _apron():
    mats = [mat("seafoam_cotton", "fabric", (.40, .72, .65), 0, .95, .08),
            mat("pink_striped_cotton", "fabric", (.82, .45, .56), 0, .93, .08),
            mat("pale_cream_trim", "fabric", (.88, .79, .68), 0, .93, .04),
            mat("coral_motif", "paint", (.84, .42, .48), 0, .86, .04)]
    components = [
        panel("flared_lower_apron_skirt", "pink_striped_cotton", [
            [-.39, -.68], [.39, -.68], [.36, -.31], [.27, -.1], [-.27, -.1], [-.36, -.31]],
            pos=(0, 0, .71)),
        panel("seafoam_upper_bib", "seafoam_cotton", [
            [-.28, -.12], [.28, -.12], [.19, .18], [.14, .63], [-.14, .63], [-.19, .18]],
            pos=(0, -.019, .71)),
        tube("neck_loop", "seafoam_cotton", [(-.14, 0, 1.31),(-.18, .03, 1.53),
                (-.11, .06, 1.64),(.09, .06, 1.65),(.18, .03, 1.54),(.14, 0, 1.31)], .023),
        tube("left_waist_tie", "seafoam_cotton", [(-.27, 0, .72),(-.49, -.02, .71),
                (-.59, -.05, .52),(-.55, -.08, .39)], .025),
        tube("right_waist_tie", "seafoam_cotton", [(.27, 0, .72),(.49, -.02, .71),
                (.59, -.05, .52),(.55, -.08, .39)], .025),
        panel("front_pocket", "pale_cream_trim", [[-.27, -.47],[.27, -.47],[.24, -.30],[-.24, -.30]],
              depth=.011, pos=(0, -.048, .71)),
        panel("front_coral_patch", "coral_motif", [[-.095, -.02],[.095, -.02],[.045, .16],[-.045, .16]],
              depth=.008, pos=(0, -.065, 1.0)),
    ]
    obs = [note("flared_lower_apron_skirt", "Pink-striped flaring lower fabric panel", .97),
           note("seafoam_upper_bib", "Seafoam-green upper bib narrowing into the neck strap", .96),
           note("neck_loop", "One fabric strap arcs over the neck opening", .96),
           note("left_waist_tie", "Free hanging tie on left", .9),
           note("right_waist_tie", "Free hanging tie on right", .9),
           note("front_pocket", "Light trimmed lower pocket region", .63),
           note("front_coral_patch", "Small colorful central decorative motif, rendered generically", .72)]
    return "clothing_armor", "Lightweight kitchen apron", mats, components, obs, [], "flared apron and open neck loop", [.85, .15]


def _backpack():
    mats = [mat("charcoal_canvas", "fabric", (.09, .09, .095), 0, .88, .22),
            mat("aged_black_nylon", "fabric", (.16, .16, .16), 0, .74, .16),
            mat("zipper_gunmetal", "metal", (.33, .32, .30), .55, .62, .25)]
    components = [
        box("main_pack_body", "charcoal_canvas", (0, 0, .68), (.87, .43, 1.10), .055),
        box("upper_front_panel", "aged_black_nylon", (0, -.24, .93), (.74, .08, .34), .04),
        box("large_front_pocket", "aged_black_nylon", (0, -.30, .50), (.77, .18, .49), .038),
        box("small_upper_patch", "charcoal_canvas", (0, -.3, 1.06), (.48, .025, .13), .012),
        tube("top_grab_handle", "aged_black_nylon", [(-.19, 0, 1.21),(-.17, 0, 1.34),
             (-.05, 0, 1.39),(.12, 0, 1.37),(.19, 0, 1.21)], .036),
        tube("left_shoulder_strap", "charcoal_canvas", [(-.37, .20, 1.13),(-.48, .23, .91),
             (-.49, .26, .35),(-.36, .20, .12)], .053),
        tube("right_shoulder_strap", "charcoal_canvas", [(.37, .20, 1.13),(.48, .23, .91),
             (.49, .26, .35),(.36, .20, .12)], .053),
        tube("front_pocket_zipper", "zipper_gunmetal", [(-.33, -.395, .71),
             (0, -.395, .735),(.33, -.395, .71)], .009),
    ]
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
        "identity": {"candidate_id": "benchmark_" + case_id + "_v1",
                     "source_reference_id": reference_id + "_founder_sheet_pilot",
                     "source_sha256": sha256(source), "source_rights": "founder_original_pending_review",
                     "asset_family": family, "recipe_version": 1,
                     "generation_method": "pixel_inspected_seed", "canonical_id": None},
        "visual_analysis": {"provider": "human_observed_benchmark_seed_20261110",
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
    validate(recipe, source, full_schema=True)
    return recipe
