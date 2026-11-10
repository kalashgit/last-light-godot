"""Three source-pinned, manually image-inspected mesh experiments from sheet 001–050.

These are original procedural reconstructions, NOT VLM inference or Golden art.
Every recipe reads a verified isolated source crop and preserves its exact hash.
Only positions 5, 35 and 44 were visually inspected and designed here. Never
extrapolate this manually authored sample to an unattended 50-model claim.
"""
from __future__ import annotations

import argparse
from collections import deque
import json
from pathlib import Path

from PIL import Image

from .contract import sha256, validate
from .pilot import dump
from .seed_recipes import box, cyl, mat, note, part, ring, tube

CHOICES = {5: "thread_spool", 35: "wood_handle_hatchet", 44: "wooden_tool_case"}


def spool():
    materials = [
        mat("golden_thread", "fabric", (.88, .45, .058), roughness=.85, wear=.05, texture="fine_noise"),
        mat("thread_highlight", "fabric", (1., .65, .12), roughness=.8, wear=.04),
        mat("thread_shadow", "fabric", (.56, .26, .035), roughness=.83, wear=.11),
        mat("flange_dark", "plastic", (.105, .11, .12), roughness=.7, wear=.16),
        mat("flange_highlight", "plastic", (.235, .24, .245), roughness=.62, wear=.19),
        mat("spool_hole", "plastic", (.032, .036, .04), roughness=.81),
    ]
    components = [
        cyl("thread_core", "golden_thread", (0, 0, .735), .415, 1.15, 64),
        cyl("bottom_flange", "flange_dark", (0, 0, .115), .55, .17, 64),
        cyl("bottom_flange_face", "flange_highlight", (0, 0, .06), .53, .033, 64),
        cyl("upper_flange", "flange_dark", (0, 0, 1.37), .57, .15, 64),
        cyl("upper_flange_highlight", "flange_highlight", (0, 0, 1.442), .542, .025, 64),
        cyl("upper_hole_shadow", "spool_hole", (0, 0, 1.462), .204, .018, 48),
        cyl("upper_hole_inner", "flange_dark", (0, 0, 1.473), .128, .008, 48),
        ring("bottom_flange_rim", "flange_highlight", .527, .14, .024),
        ring("top_flange_rim", "flange_dark", .541, 1.418, .027),
    ]
    for n in range(22):
        z = .19 + n * .049
        components.append(ring(f"winding_ridge_{n+1:02d}",
                               "thread_highlight" if n % 3 == 0 else "thread_shadow",
                               .419 if n % 2 == 0 else .421, z, .0105,
                               confidence=.69))
    observations = [
        note("thread_core", "Tall cylindrical tightly wound golden thread, nearly constant width", .97),
        note("upper_flange", "Dark charcoal circular top disk wider than the thread body", .97),
        note("upper_hole_shadow", "Concentric dark hole visible at top center", .96),
        note("bottom_flange", "Wider black lower bobbin lip and distinct base silhouette", .95),
    ]
    assumptions = [note("thread_core", "Thread spirals are approximated by separate circumferential rings", .48)]
    return materials, components, observations, assumptions, {
        "family": "crafting_thread_spool", "function": "Thread supply on a plastic bobbin",
        "silhouette": "Tall amber cylinder with two black flanges and top concentric hole",
        "footprint": [1.13, 1.13], "collision": "convex", "interact": [],
        "openings": [], "attachments": [], "camera": 315, "ortho": 2.15,
    }


def hatchet():
    materials = [
        mat("warm_wood", "paint", (.52, .29, .12), roughness=.86, wear=.23, texture="scuffed"),
        mat("wood_highlight", "paint", (.66, .42, .21), roughness=.85, wear=.20),
        mat("wood_shadow", "paint", (.26, .14, .07), roughness=.93, wear=.31),
        mat("axe_steel", "metal", (.31, .33, .34), metallic=.77, roughness=.7, wear=.38, texture="scuffed"),
        mat("blade_edge", "metal", (.52, .52, .52), metallic=.74, roughness=.58, wear=.26),
        mat("blade_dark", "metal", (.19, .19, .2), metallic=.7, roughness=.72, wear=.38),
    ]
    components = [
        # Long handle runs from lower left to upper right when seen from the source angle.
        cyl("wood_handle", "warm_wood", (-.05, 0, .73), .080, 1.60, 32,
            rotation=(0, 37, 0)),
        cyl("handle_lower_grip", "wood_highlight", (-.53, 0, .085), .091, .23, 32,
            rotation=(0, 37, 0), confidence=.66),
        cyl("handle_taper_upper", "wood_shadow", (.41, 0, 1.34), .081, .28, 32,
            rotation=(0, 37, 0), confidence=.7),
        cyl("head_socket", "axe_steel", (.42, 0, 1.33), .15, .32, 32,
            rotation=(0, 37, 0)),
        cyl("head_socket_back", "blade_dark", (.35, 0, 1.41), .155, .035, 32,
            rotation=(0, 37, 0), confidence=.62),
        part("steel_blade_wedge", "polygon_extrude", "axe_steel", (.53, 0, 1.35),
             {"points": [[-.08, -.15], [.20, -.20], [.48, -.31], [.58, .19],
                         [.27, .16], [-.10, .12]], "depth": .17, "bevel": .017},
             rotation=(90, 0, 0)),
        part("cutting_edge", "polygon_extrude", "blade_edge", (.53, -.091, 1.35),
             {"points": [[.47, -.30], [.58, .19], [.52, .18], [.42, -.28]],
              "depth": .012, "bevel": .005}, rotation=(90, 0, 0), confidence=.76),
        tube("wood_length_grain", "wood_highlight",
             [[-.55, -.073, .16], [-.35, -.073, .40], [-.10, -.074, .78],
              [.17, -.074, 1.06], [.37, -.07, 1.33]], .009, confidence=.62),
    ]
    observations = [
        note("wood_handle", "Single long honey-brown wooden shaft slopes diagonally toward head", .95),
        note("head_socket", "Dark iron socket wraps around wood near upper end", .94),
        note("steel_blade_wedge", "Broad silver-gray wedge projects rightward with wide cutting edge", .94),
    ]
    assumptions = [
        note("head_socket_back", "Unseen opposite side of socket approximated symmetrically", .52),
        note("steel_blade_wedge", "Blade bevel thickness and back-edge contours inferred", .59),
    ]
    return materials, components, observations, assumptions, {
        "family": "melee_hand_tool", "function": "Compact wood-handled chopping hatchet",
        "silhouette": "Long diagonal handle with broad flat steel blade on upper end",
        "footprint": [1.45, .4], "collision": "convex", "interact": ["wood_handle"],
        "openings": [], "attachments": [{"name": "grip", "position": [-.5, 0, .22]}],
        "camera": 305, "ortho": 2.72,
    }


def case():
    materials = [
        mat("dark_walnut", "paint", (.245, .105, .042), roughness=.87, wear=.24, texture="scuffed"),
        mat("lid_walnut", "paint", (.37, .18, .08), roughness=.86, wear=.16, texture="scuffed"),
        mat("wood_plank", "paint", (.57, .30, .14), roughness=.88, wear=.13, texture="fine_noise"),
        mat("wood_dark_grain", "paint", (.26, .12, .05), roughness=.89, wear=.23),
        mat("hinge_brass", "metal", (.58, .4, .15), metallic=.69, roughness=.51, wear=.3),
        mat("metal_shadow", "metal", (.25, .17, .05), metallic=.6, roughness=.7, wear=.32),
    ]
    components = [
        box("case_base", "dark_walnut", (0, 0, .19), (1.73, .77, .34), .024),
        box("case_lid_rim", "lid_walnut", (0, 0, .397), (1.78, .79, .105), .017),
        box("top_sunken_panel", "dark_walnut", (0, 0, .461), (1.55, .575, .03), .008),
        box("left_lid_rail", "lid_walnut", (-.805, 0, .475), (.10, .735, .04), .006),
        box("right_lid_rail", "lid_walnut", (.805, 0, .475), (.10, .735, .04), .006),
        box("front_lid_rail", "lid_walnut", (0, -.357, .478), (1.62, .075, .047), .004),
        box("back_lid_rail", "lid_walnut", (0, .357, .478), (1.62, .075, .047), .004),
        box("lid_front_seam", "wood_dark_grain", (0, -.395, .356), (1.71, .018, .026), .004),
        box("front_lower_horizontal_grain", "lid_walnut", (0, -.39, .15), (1.65, .013, .016), .002),
        box("brass_latch_upper", "hinge_brass", (.37, -.411, .405), (.12, .029, .16), .007),
        box("brass_latch_lower", "hinge_brass", (.37, -.412, .284), (.095, .04, .09), .006),
        box("latch_keyhole", "metal_shadow", (.37, -.446, .286), (.028, .006, .045), .002),
    ]
    for i in range(9):
        x = -.685 + .171 * i
        components.append(box(f"top_lid_plank_{i+1:02d}",
                              "wood_plank" if i % 3 else "lid_walnut",
                              (x, 0, .48), (.153, .54, .018), .003, confidence=.87))
        components.append(box(f"plank_grain_{i+1:02d}", "wood_dark_grain",
                              (x + .036, -.03, .492), (.006, .45, .004), .0005,
                              confidence=.55))
    observations = [
        note("case_base", "Low dark-brown rectangular wooden box with closed straight sides", .98),
        note("case_lid_rim", "Raised perimeter lid frame encloses inset wood strips", .94),
        note("top_lid_plank_01", "Parallel lighter wooden planks run across inset top surface", .92),
        note("brass_latch_upper", "Small gold/brass latch on the visible front-right edge", .91),
    ]
    assumptions = [
        note("case_base", "Inside contents, bottom joinery, and unseen back not reconstructed", .64),
        note("brass_latch_lower", "Exact latch mechanical details inferred", .52),
    ]
    return materials, components, observations, assumptions, {
        "family": "wooden_storage_case", "function": "Small latching wooden storage case",
        "silhouette": "Low wide rectangular hinged wooden case, inset slatted lid, front brass clasp",
        "footprint": [1.78, .8], "collision": "box", "interact": ["brass_latch_upper"],
        "openings": [], "attachments": [], "camera": 315, "ortho": 2.64,
    }


BUILDERS = {5: spool, 35: hatchet, 44: case}


def alpha_isolate_paper(source: Path, output: Path) -> dict:
    """Remove *only edge-connected near-white JPEG paper*, not interior pixels.

    This is a scoring reference, never a texture exported into the game. More
    complicated/white sprites require manual masks and are out of this pilot.
    """
    with Image.open(source) as im:
        rgb = im.convert("RGB")
    w, h = rgb.size
    pixels = rgb.load()
    paper = lambda x, y: (min(pixels[x, y]) >= 230 and
                          max(pixels[x, y]) - min(pixels[x, y]) <= 18)
    visited = bytearray(w * h)
    todo = deque()
    for x in range(w):
        todo.append((x, 0))
        todo.append((x, h - 1))
    for y in range(h):
        todo.append((0, y))
        todo.append((w - 1, y))
    background_count = 0
    while todo:
        x, y = todo.popleft()
        index = y * w + x
        if visited[index] or not paper(x, y):
            continue
        visited[index] = 1
        background_count += 1
        if x: todo.append((x - 1, y))
        if x + 1 < w: todo.append((x + 1, y))
        if y: todo.append((x, y - 1))
        if y + 1 < h: todo.append((x, y + 1))
    if not .15 < background_count / (w * h) < .95:
        raise ValueError("background mask ambiguous; human review required")
    out = rgb.convert("RGBA")
    alpha = Image.new("L", (w, h), 255)
    alpha.putdata([0 if visited[i] else 255 for i in range(w * h)])
    out.putalpha(alpha)
    output.parent.mkdir(parents=True, exist_ok=True)
    out.save(output)
    return {"source_crop_sha256": sha256(source), "masked_source_sha256": sha256(output),
            "background_pixels": background_count, "pixels_total": w * h,
            "method": "edge_connected_neutral_nearwhite_flood_fill",
            "use": "technical_scoring_reference_only"}


def prepare(manifest_file: Path, output: Path) -> list[dict]:
    manifest_file = manifest_file.resolve()
    data = json.loads(manifest_file.read_text())
    if data["schema"] != "last-light.local-vlm-sheet-crops.v1" or data["input_start"] != 1:
        raise ValueError("expected verified first founder sheet crop manifest")
    source_dir = manifest_file.parent
    by_pos = {r["sheet_position"]: r for r in data["crops"]}
    reports = []
    for position, builder in BUILDERS.items():
        ref = by_pos[position]
        if not ref["isolated_crop_qa"]["safe_for_unattended_proposal"]:
            raise ValueError(f"reference {position} requires manual isolation")
        if ref["source_rights"] != "founder_original_pending_review" or ref["golden_approved"]:
            raise ValueError("unexpected source rights / Golden status")
        source = (source_dir / ref["crop_file"]).resolve()
        if not source.is_relative_to(source_dir) or sha256(source) != ref["crop_sha256"]:
            raise ValueError("source crop provenance changed")
        with Image.open(source) as im:
            dimensions = list(im.size)
        masked_source = output / "scoring_sources" / f"ref_{position:04d}.png"
        masking = alpha_isolate_paper(source, masked_source)
        materials, components, observations, assumptions, info = builder()
        name = CHOICES[position]
        recipe = {
            "schema": "last-light.recipe-architect.v1",
            "identity": {
                "candidate_id": f"sheet_001_050_{position:02d}_{name}_v1",
                "source_reference_id": ref["reference_id"],
                "source_sha256": sha256(masked_source),
                "source_rights": ref["source_rights"],
                "asset_family": info["family"], "recipe_version": 1,
                "generation_method": "pixel_inspected_seed", "canonical_id": None,
            },
            "visual_analysis": {
                "provider": "chatgpt_manual_visual_inspection_2026_11_10",
                "pixels_inspected": True, "image_dimensions": dimensions,
                "probable_function": info["function"], "category": info["family"],
                "observations": observations, "assumptions": assumptions,
                "artifacts": ["Original JPEG artwork isolated from 50-cell sheet; scoring source has edge-connected white background removed",
                              "Single view cannot establish unseen depth; derived 3D volumes are approximate"],
                "confidence": .82,
            },
            "materials": materials, "components": components,
            "gameplay": {
                "collision": info["collision"], "movable": True,
                "interactable_parts": info["interact"], "container_openings": info["openings"],
                "damage_states": ["intact", "worn", "broken"], "footprint_m": info["footprint"],
                "animations": [], "attachment_points": info["attachments"],
            },
            "render": {
                "headings": 16, "resolution": 128, "camera_azimuth_deg": info["camera"],
                "camera_elevation_deg": 35.264, "orthographic_scale": info["ortho"],
                "key_light": "upper_left", "assembly_scale": [1, 1, 1],
            },
            "quality": {
                "expected_silhouette": info["silhouette"],
                "qa_checks": ["source_sha", "glb_geometry", "alpha", "16_distinct_headings",
                              "silhouette", "color", "human_visual_review", "manual_golden"],
                "technical_status": "CANDIDATE_PENDING_QA", "golden_approved": False,
                "founder_review": "NOT_GOLDEN",
            },
            "tuning": {"scale_step": .07, "max_corrections": 1},
        }
        validate(recipe, masked_source, full_schema=True)
        target = output / "recipes" / f"ref_{position:04d}_{name}.json"
        dump(target, recipe)
        reports.append({"position": position, "name": name, "recipe_file": str(target),
                        "source_crop": str(source), "scoring_source": str(masked_source),
                        "source_sha256": sha256(masked_source), "source_masking": masking,
                        "component_count": len(components), "golden": False})
    dump(output / "recipe_experiment_manifest.json", {
        "schema": "last-light.manual-sheet-recipe-experiment.v1",
        "sheet_sha256": by_pos[5]["source_sheet_sha256"], "models_prepared": len(reports),
        "autonomous_vision_model_invoked": False, "artistic_approved": False,
        "unselected_sheet_slots": 47, "models": reports,
    })
    return reports


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--crops", type=Path, required=True, help="isolated 1–50 crop manifest")
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    reports = prepare(a.crops, a.out)
    print("LL_MANUAL_SHEET_MESH_RECIPES", len(reports), "CANDIDATES_PENDING_QA")


if __name__ == "__main__":
    main()
