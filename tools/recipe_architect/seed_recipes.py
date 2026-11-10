"""Pixel-inspected, SHA-pinned technical recipe seeds for archived founder art.

Descriptions below were made by inspecting the three actual RGBA images, not
from filenames. They are not output from an autonomous vision model.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SHA = {
    "vehicle_battery": "e69103e64deb44dcc7213ae142b9767b8f0fa2eeb44b05a2f0557025ca8c33b7",
    "canvas_canteen": "fca1136b0fdde382e83ffbe7478c93977259d021256959651d4ea14f35b0e73a",
    "cast_iron_skillet": "5b336ee3f34297afab52475de8bd21a5f956b765e5d4f719a91fa7eab03e8802",
}


def mat(name, kind, rgb, metallic=0, roughness=.7, wear=.12, texture="fine_noise"):
    return dict(name=name, **{"class": kind}, rgba=[*rgb, 1], metallic=metallic, roughness=roughness, wear=wear, texture=texture)


def part(name, op, material, location, geometry, rotation=(0, 0, 0), parent=None,
         observed=True, confidence=.85, modifiers=(), topology="closed"):
    return dict(name=name, op=op, material=material, location=list(location),
                rotation_deg=list(rotation), parent=parent, geometry=geometry,
                observed=observed, confidence=confidence, modifiers=list(modifiers), topology=topology)


def box(name, material, pos, size, bevel=.012, **kw):
    return part(name, "box", material, pos, {"size": list(size), "bevel": bevel}, **kw)


def cyl(name, material, pos, radius, depth, vertices=32, scale_xy=(1, 1), **kw):
    return part(name, "cylinder", material, pos, {"radius": radius, "depth": depth,
                 "vertices": vertices, "scale_xy": list(scale_xy)}, **kw)


def tube(name, material, points, radius=.012, closed=False, **kw):
    return part(name, "tube", material, (0, 0, 0), {"points": [list(p) for p in points],
                 "radius": radius, "closed": closed}, **kw)


def ring(name, material, radius, z, thickness, x=0, y=0, ellipse=(1, 1), **kw):
    import math
    return tube(name, material, [(x + radius * ellipse[0] * math.cos(i * math.tau / 36),
                y + radius * ellipse[1] * math.sin(i * math.tau / 36), z) for i in range(36)], thickness, True, **kw)


def note(component, detail, confidence):
    return dict(component=component, detail=detail, confidence=confidence)


def common(name, family, dims, observed, inferred, materials, components, gameplay, silhouette, scale=(1, 1, 1), ortho=2.55):
    return {
        "schema": "last-light.recipe-architect.v1",
        "identity": {"candidate_id": "pilot_" + name + "_recipe_v1", "source_reference_id": "founder_sheet_s01_slot_" +
                     {"vehicle_battery": "614", "canvas_canteen": "608", "cast_iron_skillet": "626"}[name] + "_isolated_sha_pinned",
                     "source_sha256": SHA[name], "source_rights": "founder_original_pending_review",
                     "asset_family": family, "recipe_version": 1, "generation_method": "pixel_inspected_seed", "canonical_id": None},
        "visual_analysis": {"provider": "chatgpt_visual_inspection_2026_11_10", "pixels_inspected": True,
                            "image_dimensions": dims, "probable_function": gameplay["function"], "category": family,
                            "observations": observed, "assumptions": inferred,
                            "artifacts": ["RGBA segmentation has uneven cutout edges; treat missing/white pixels as uncertain, not new geometry"],
                            "confidence": .84},
        "materials": materials, "components": components,
        "gameplay": {"collision": "box" if name != "cast_iron_skillet" else "convex",
                     "movable": True, "interactable_parts": gameplay["interactable"],
                     "container_openings": gameplay["openings"],
                     "damage_states": ["intact", "worn", "broken"],
                     "footprint_m": gameplay["footprint"], "animations": gameplay["animations"],
                     "attachment_points": gameplay["attachments"]},
        "render": {"headings": 16, "resolution": 128, "camera_azimuth_deg": 315,
                   "camera_elevation_deg": 35.264, "orthographic_scale": ortho,
                   "key_light": "upper_left", "assembly_scale": list(scale)},
        "quality": {"expected_silhouette": silhouette, "qa_checks": ["source_sha", "glb_geometry", "alpha", "16_distinct_headings", "silhouette", "color", "manual_golden"],
                    "technical_status": "CANDIDATE_PENDING_QA", "golden_approved": False, "founder_review": "NOT_GOLDEN"},
        "tuning": {"scale_step": .09, "max_corrections": 5},
    }


def battery():
    m = [mat("black_polymer", "plastic", (.055, .059, .057), roughness=.62),
         mat("edge_graphite", "plastic", (.15, .17, .17), roughness=.54),
         mat("graphite_panel", "plastic", (.095, .105, .102)),
         mat("terminal_lead", "metal", (.24, .27, .28), .67, .45),
         mat("positive_copper", "metal", (.62, .15, .065), .55, .39),
         mat("paper_label", "paper", (.83, .79, .63), roughness=.83, texture="none"),
         mat("black_ink", "paint", (.08, .076, .064), roughness=.86, texture="none"),
         mat("silver_trim", "metal", (.31, .34, .35), .52, .46)]
    c = [box("main_battery_casing", "black_polymer", (0, 0, .45), (1.48, .85, .84), .035, modifiers=("weighted_normals",)),
         box("bottom_retaining_foot", "edge_graphite", (0, 0, .085), (1.55, .90, .13), .012),
         box("lid_seam", "silver_trim", (0, 0, .83), (1.52, .89, .028), .008),
         box("stepped_lid_shell", "graphite_panel", (0, 0, .91), (1.60, .94, .14), .033),
         box("upper_recess_inset", "black_polymer", (0, .045, .985), (1.40, .78, .022), .006),
         box("left_top_service_panel", "edge_graphite", (-.25, .16, 1.012), (.43, .32, .018), .01),
         box("right_top_service_panel", "edge_graphite", (.26, .16, 1.012), (.43, .32, .018), .01),
         box("left_top_panel_etch", "black_polymer", (-.25, .15, 1.024), (.35, .20, .008), .004),
         box("right_top_panel_etch", "black_polymer", (.26, .15, 1.024), (.35, .20, .008), .004),
         cyl("negative_terminal_base", "silver_trim", (-.57, -.05, 1.035), .126, .055),
         cyl("negative_terminal_post", "terminal_lead", (-.57, -.05, 1.145), .086, .21),
         ring("negative_terminal_lip", "silver_trim", .090, 1.244, .010, -.57, -.05),
         cyl("positive_terminal_base", "silver_trim", (.57, -.05, 1.035), .124, .05),
         cyl("positive_terminal_post", "positive_copper", (.57, -.05, 1.15), .089, .20),
         ring("positive_terminal_lip", "positive_copper", .096, 1.245, .012, .57, -.05),
         box("front_label_plate", "paper_label", (0, -.44, .565), (1.09, .018, .235), .014),
         box("front_label_top_rule", "black_ink", (0, -.454, .67), (1.03, .005, .014), .001),
         box("front_label_mid_rule", "black_ink", (0, -.454, .46), (1.03, .005, .013), .001),
         part("brand_label", "text", "black_ink", (-.47, -.463, .53), {"value": "NORTHRIDGE", "size": .135, "extrude": .001}, (90, 0, 0), topology="text_mesh"),
         part("capacity_label", "text", "paper_label", (-.34, -.463, .315), {"value": "12V 60Ah", "size": .155, "extrude": .001}, (90, 0, 0), topology="text_mesh"),
         box("left_vertical_corner_reinforcement", "edge_graphite", (-.735, -.425, .47), (.035, .02, .74), .004),
         box("right_vertical_corner_reinforcement", "edge_graphite", (.735, -.425, .47), (.035, .02, .74), .004),
         box("bottom_front_rail", "silver_trim", (0, -.454, .085), (1.51, .029, .04), .005),
         box("right_side_lower_rib", "edge_graphite", (.752, 0, .26), (.025, .78, .028), .004)]
    return common("vehicle_battery", "electrical_battery", [189, 174], [
        note("main_battery_casing", "Dark almost-black rectangular enclosure; front and right faces visible", .99),
        note("stepped_lid_shell", "Flat top with raised rim and recessed rectangular service areas", .94),
        note("negative_terminal_post", "Dark lead-gray cylindrical post on upper left", .96),
        note("positive_terminal_post", "Bright red-orange cylindrical post on upper right", .99),
        note("front_label_plate", "Light tan frontal label with dark NORTHRIDGE and 12V 60Ah lettering", .98),
        note("bottom_retaining_foot", "Thin stepped lower band and corner trim", .85)], [
        note("main_battery_casing", "Back face and internal cell structure unobserved; assume sealed battery case", .53),
        note("negative_terminal_post", "Terminal metallurgy and exact height inferred from small sprite", .65)], m, c,
        {"function": "Stores electrical energy in a 12-volt vehicle system", "interactable": ["negative_terminal_post", "positive_terminal_post"],
         "openings": [], "footprint": [1.55, .90], "animations": [],
         "attachments": [{"name": "negative_cable", "position": [-.57, -.05, 1.24]}, {"name": "positive_cable", "position": [.57, -.05, 1.24]}]},
        "Low broad rectangular battery with two distinct top posts and a pale central front label", scale=(.89, 1, 1), ortho=2.35)


def canteen():
    m = [mat("olive_canvas", "fabric", (.34, .30, .18), roughness=.89, wear=.28, texture="scuffed"),
         mat("olive_dark", "fabric", (.18, .18, .105), roughness=.9),
         mat("brass_buckle", "metal", (.53, .38, .16), .64, .49),
         mat("top_cap", "plastic", (.30, .25, .15), roughness=.65),
         mat("thread", "fabric", (.48, .42, .25), roughness=.92)]
    profile = [[0, .04], [.22, .04], [.32, .11], [.34, .28], [.34, .77], [.31, .92], [.21, 1.03], [.105, 1.06],
               [.105, .99], [.20, .95], [.28, .84], [.29, .72], [.29, .18], [.17, .10], [0, .10]]
    c = [part("hollow_fabric_cover", "lathe", "olive_canvas", (0, 0, 0), {"profile": profile, "vertices": 48, "scale_xy": [1, .77]}),
         cyl("neck_socket", "olive_dark", (0, 0, 1.085), .122, .105),
         cyl("ribbed_screw_cap", "top_cap", (0, 0, 1.18), .15, .19, 36),
         ring("cap_top_ridge", "brass_buckle", .136, 1.276, .011),
         ring("cap_lower_seam", "olive_dark", .146, 1.097, .009),
         tube("right_cap_retain_loop", "brass_buckle", [[.14, 0, 1.20], [.23, -.02, 1.28], [.30, -.025, 1.24], [.30, -.025, 1.15], [.22, 0, 1.12]], .024),
         tube("left_shoulder_strap", "olive_dark", [[-.26, -.16, .96], [-.33, -.18, .79], [-.29, -.19, .66], [-.27, -.18, .39]], .045),
         tube("right_shoulder_strap", "olive_dark", [[.26, -.16, .96], [.34, -.18, .78], [.29, -.19, .62], [.26, -.18, .39]], .045),
         box("left_strap_clasp", "brass_buckle", (-.286, -.196, .67), (.13, .055, .13), .018),
         box("left_clasp_inset", "olive_canvas", (-.286, -.227, .67), (.085, .015, .087), .008),
         box("right_strap_clasp", "brass_buckle", (.286, -.196, .67), (.13, .055, .13), .018),
         box("right_clasp_inset", "olive_canvas", (.286, -.227, .67), (.085, .015, .087), .008),
         tube("front_center_canvas_stitch", "thread", [[0, -.267, .16], [0, -.265, .41], [0, -.25, .72]], .005, observed=True),
         tube("left_side_wear_seam", "thread", [[-.3, -.085, .17], [-.32, -.09, .43], [-.30, -.1, .70]], .007, confidence=.6)]
    recipe = common("canvas_canteen", "water_canteen", [170, 230], [
        note("hollow_fabric_cover", "Tall olive-brown rounded flask/canvas cover, narrower at shoulders", .95),
        note("ribbed_screw_cap", "Wide ribbed cylindrical cap and narrower neck at top", .97),
        note("right_cap_retain_loop", "Small metallic ring projecting to right of cap", .89),
        note("left_strap_clasp", "Paired vertical fabric straps with rectangular front fasteners", .92)], [
        note("hollow_fabric_cover", "Unseen back and water container wall are approximated as hollow lathed shell", .57),
        note("olive_canvas", "Exact surface pattern and seams are guessed, not source texture", .5)], m, c,
        {"function": "Portable carried vessel for drinking water", "interactable": ["ribbed_screw_cap"],
         "openings": ["neck_socket"], "footprint": [.68, .53], "animations": ["unscrew_cap"],
         "attachments": [{"name": "carry_ring", "position": [.3, 0, 1.20]}]},
        "Tall olive vessel, distinct neck/cap, flanking straps, small side ring", ortho=2.4)
    recipe["render"]["camera_azimuth_deg"] = 275
    return recipe


def skillet():
    m = [mat("cast_iron", "metal", (.13, .12, .105), .66, .83, .42, "scuffed"),
         mat("worn_rim", "metal", (.26, .23, .19), .67, .81, .38, "scuffed"),
         mat("inner_patina", "metal", (.19, .17, .135), .59, .89, .58, "scuffed")]
    # One lathed, physical hollow pan cross section (base, inner bowl and rim).
    profile = [[0, .065], [.38, .065], [.47, .086], [.52, .12], [.57, .23], [.57, .275],
               [.535, .29], [.508, .245], [.47, .16], [.38, .13], [0, .13]]
    c = [part("hollow_cast_iron_bowl", "lathe", "cast_iron", (0, 0, 0), {"profile": profile, "vertices": 64}),
         ring("rolled_metal_lip", "worn_rim", .562, .278, .018),
         cyl("interior_seasoned_surface", "inner_patina", (0, 0, .132), .38, .005, vertices=64),
         part("tapered_handle_shank", "polygon_extrude", "cast_iron", (0, .775, .245),
              {"points": [[-.21, -.115], [.18, -.09], [.42, -.065], [.42, .065], [.18, .09], [-.21, .115]], "depth": .095}, (0, 0, 90)),
         part("handle_hanging_slot", "boolean_cut", "cast_iron", (0, 1.14, .245),
              {"target": "tapered_handle_shank", "size": [.12, .075, .25], "bevel": .02}, (0, 0, 90), observed=True),
         box("opposite_pour_spout", "worn_rim", (0, -.565, .265), (.17, .10, .044), .015),
         ring("underbase_concentric_seam", "inner_patina", .39, .066, .008)]
    return common("cast_iron_skillet", "cookware_pan", [197, 187], [
        note("hollow_cast_iron_bowl", "Wide blackened shallow circular iron pan, empty concave interior", .99),
        note("rolled_metal_lip", "Raised uneven rim with brown worn edge highlights", .91),
        note("tapered_handle_shank", "Single long cast handle going toward upper right; hole near handle tip", .97),
        note("interior_seasoned_surface", "Brown/gray mottled seasoned interior surface", .92)], [
        note("hollow_cast_iron_bowl", "Hidden base and thickness inferred as cast iron; scratch texture procedural", .68),
        note("opposite_pour_spout", "Small pour lip position plausible but not distinctly resolved", .44)], m, c,
        {"function": "Open, empty frying vessel heated on a stovetop", "interactable": ["tapered_handle_shank"],
         "openings": [], "footprint": [1.15, 1.15], "animations": [],
         "attachments": [{"name": "handle_grab", "position": [0, 1.06, .245]}]},
        "Wide hollow low bowl with pronounced rim and one long perforated handle", ortho=3.05)


SEEDS = {"vehicle_battery": battery, "canvas_canteen": canteen, "cast_iron_skillet": skillet}


if __name__ == "__main__":
    from .contract import validate
    for name, factory in SEEDS.items():
        recipe = factory()
        validate(recipe, full_schema=True)
        output = ROOT / "data/foundry_recipe_architect" / f"{name}_recipe_v1.json"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(recipe, sort_keys=True, indent=2) + "\n")
        print("LL_RECIPE_SEED_VALID", name, output)
