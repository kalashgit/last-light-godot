"""Bounded, source-region-guided *mesh geometry* revisions with real Blender QA.

A trusted visual observation identifies one source-visible component and its
approximate 2D bounding box. This CPU optimizer changes *that component's*
allowed shape parameters, re-renders each proposal, and keeps it only when
part alignment improves without unacceptable whole-object regression.

The observations are not inferred by this module. This is not a VLM, a
semantic correctness oracle, or an automatic Golden approval mechanism.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import subprocess
from pathlib import Path

from PIL import Image

from .batch import fresh_output
from .contract import sha256, validate
from .pilot import dump, inspect_glb, run_blender
from .visual_qa import compare, normalization_fit

ROOT = Path(__file__).resolve().parents[2]


def recipe_digest(recipe: dict) -> str:
    """Stable binding for a vision observation to one exact recipe."""
    return hashlib.sha256(json.dumps(recipe, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def variants(recipe: dict, component: str, *, step: float = .18) -> list[tuple[dict, dict]]:
    """Generate small reversible shape-only mutations; no arbitrary code eval."""
    if not 0 < step <= .30 or not math.isfinite(step):
        raise ValueError("invalid bounded component deformation")
    original = next((c for c in recipe["components"] if c["name"] == component), None)
    if original is None or not original["observed"] or original["op"] == "boolean_cut":
        raise ValueError("part must exist and be source-observed non-cutter geometry")
    op = original["op"]
    params = {
        "box": ["size_x", "size_y", "size_z"],
        "cylinder": ["radius", "depth"],
        "polygon_extrude": ["points_x", "points_y", "depth"],
        "tube": ["radius", "points_x", "points_y", "points_z"],
        "lathe": ["radius", "height"],
        "text": ["size"],
    }[op]
    proposals = []
    for param in params:
        for factor in (1 + step, 1 - step):
            trial = copy.deepcopy(recipe)
            part = next(c for c in trial["components"] if c["name"] == component)
            g = part["geometry"]
            if param.startswith("size_"):
                axis = "xyz".index(param[-1])
                g["size"][axis] = round(g["size"][axis] * factor, 6)
            elif param == "radius" and op == "lathe":
                for row in g["profile"]:
                    row[0] = round(row[0] * factor, 6)
            elif param == "height" and op == "lathe":
                bottom = min(row[1] for row in g["profile"])
                for row in g["profile"]:
                    row[1] = round(bottom + (row[1] - bottom) * factor, 6)
            elif param.startswith("points_"):
                axis = "xyz".index(param[-1])
                points = g["points"]
                center = sum(row[axis] for row in points) / len(points)
                for row in points:
                    row[axis] = round(center + (row[axis] - center) * factor, 6)
            else:
                g[param] = round(g[param] * factor, 6)
            trial["identity"]["recipe_version"] += 1
            trial["identity"]["generation_method"] = "reviewed_revision"
            validate(trial, full_schema=True)
            proposals.append((trial, {"component": component, "parameter": param,
                                      "factor": round(factor, 6), "shape_changed": True}))
    return proposals


def guided_variants(recipe: dict, target: dict, *, step: float = .18) -> list[tuple[dict, dict]]:
    """Prioritize untrusted VLM hints without granting them acceptance authority."""
    suggestions = variants(recipe, target["component"], step=step)
    parameter = target.get("suggested_parameter")
    direction = target.get("suggested_direction")
    if parameter is not None or direction is not None:
        if (not any(item["parameter"] == parameter for _, item in suggestions) or
                direction not in ("increase", "decrease", "unknown")):
            raise ValueError("vision hint must identify a permitted bounded mutation")
        suggestions.sort(key=lambda item: (item[1]["parameter"] != parameter,
                           direction != "unknown" and
                           (item[1]["factor"] > 1) != (direction == "increase")))
    return suggestions


def normalize_rect(rect: list[float], image: Image.Image, *, size: int = 128) -> list[float]:
    if len(rect) != 4 or any(type(v) not in (int, float) or not math.isfinite(v) for v in rect):
        raise ValueError("invalid source-visible component rectangle")
    left, top, right, bottom = rect
    if not (0 <= left < right <= image.width and 0 <= top < bottom <= image.height):
        raise ValueError("component bounds must be inside source or render image")
    (crop_x, crop_y, crop_r, crop_b), (new_width, new_height), (ox, oy) = normalization_fit(image, size)
    return [round((ox + (left - crop_x) * new_width / (crop_r - crop_x)) / size, 6),
            round((oy + (top - crop_y) * new_height / (crop_b - crop_y)) / size, 6),
            round((ox + (right - crop_x) * new_width / (crop_r - crop_x)) / size, 6),
            round((oy + (bottom - crop_y) * new_height / (crop_b - crop_y)) / size, 6)]


def rect_error(reference: list[float], observed: list[float]) -> dict:
    """Compare two normalized 2D bounds without treating IoU as semantic QA."""
    if not all(math.isfinite(x) for x in [*reference, *observed]):
        raise ValueError("non-finite projection")
    rw, rh = reference[2] - reference[0], reference[3] - reference[1]
    ow, oh = observed[2] - observed[0], observed[3] - observed[1]
    if min(rw, rh, ow, oh) <= 1e-6:
        raise ValueError("degenerate projected physical component")
    ix = max(0, min(reference[2], observed[2]) - max(reference[0], observed[0]))
    iy = max(0, min(reference[3], observed[3]) - max(reference[1], observed[1]))
    inter = ix * iy
    iou = inter / (rw * rh + ow * oh - inter)
    scale_error = (abs(math.log(rw / ow)) + abs(math.log(rh / oh))) / 2
    center_error = math.dist(((reference[0] + reference[2]) / 2, (reference[1] + reference[3]) / 2),
                             ((observed[0] + observed[2]) / 2, (observed[1] + observed[3]) / 2))
    return {"bbox_iou": round(iou, 6), "scale_error": round(scale_error, 6),
            "center_error": round(center_error, 6),
            "feature_error": round(.52 * (1 - iou) + .38 * scale_error + .10 * center_error, 6)}


def measured_feature(source: Path, target: dict, render: Path, projections: Path) -> dict:
    with Image.open(source) as image:
        desired = normalize_rect(target["source_bbox_px"], image)
    with Image.open(render) as image:
        evidence = json.loads(projections.read_text())
        if evidence.get("schema") != "last-light.recipe-projections.v1" or evidence.get("resolution") != image.width:
            raise ValueError("wrong Blender projections or render dimension")
        part = evidence["components"].get(target["component"])
        if part is None or part.get("bbox_method") != "actual_blender_mesh_vertices_pre_bevel":
            raise ValueError("missing independently measured component physical extent")
        actual = normalize_rect(part["bbox_px"], image)
    return {"source_normalized_bbox": desired, "blender_normalized_bbox": actual,
            **rect_error(desired, actual)}


def measured_contacts(projections: Path, target: dict) -> dict[str, float]:
    """Measured component-to-neighbor 3D bounding-box separation (meters)."""
    components = json.loads(projections.read_text())["components"]
    target_bounds = components[target["component"]]["world_bbox_m"]
    gaps = {}
    for name in target.get("contact_neighbors", []):
        other = components[name]["world_bbox_m"]
        per_axis = [max(0., target_bounds[0][axis] - other[1][axis],
                        other[0][axis] - target_bounds[1][axis]) for axis in range(3)]
        gaps[name] = round(math.sqrt(sum(value * value for value in per_axis)), 6)
    return gaps


def validate_target(target: dict, recipe: dict, source: Path) -> None:
    provenance = target.get("provenance")
    valid_origin = (
        (provenance == "manual_source_image_estimate" and
         target.get("schema") == "last-light.manual-component-geometry-target.v1") or
        (provenance == "local_vlm_component_detection" and
         target.get("schema") == "last-light.vlm-component-geometry-target.v1")
    )
    if (not valid_origin or target.get("source_sha256") != sha256(source) or
            target.get("candidate_id") != recipe["identity"]["candidate_id"] or
            target.get("approval") != "NOT_GOLDEN"):
        raise ValueError("target must be pinned to observed source and candidate")
    if provenance == "local_vlm_component_detection":
        audit = target.get("vision_inference")
        if (not isinstance(audit, dict) or audit.get("recipe_sha256") != recipe_digest(recipe) or
                audit.get("source_sha256") != sha256(source) or
                audit.get("network_scope") != "loopback_only" or
                audit.get("pixels_supplied") is not True or
                audit.get("actual_local_vision_request_completed") is not True or
                not isinstance(audit.get("baseline_render_sha256"), str) or
                len(audit["baseline_render_sha256"]) != 64):
            raise ValueError("missing source/recipe-bound local vision inference receipt")
    part = next((c for c in recipe["components"] if c["name"] == target.get("component")), None)
    observations = {item["component"] for item in recipe["visual_analysis"]["observations"]}
    if part is None or not part["observed"] or part["name"] not in observations:
        raise ValueError("geometry target is not a source-observed component")
    required = target.get("required_visible_components")
    if (not isinstance(required, list) or not 1 <= len(required) <= 32 or
            len(set(required)) != len(required) or target["component"] not in required or
            not set(required).issubset(observations)):
        raise ValueError("target must preserve independently observed required physical parts")
    contacts = target.get("contact_neighbors", [])
    names = {component["name"] for component in recipe["components"] if component["op"] != "boolean_cut"}
    if (not isinstance(contacts, list) or len(contacts) > 8 or
            len(set(contacts)) != len(contacts) or target["component"] in contacts or
            not set(contacts).issubset(names)):
        raise ValueError("invalid physical contact neighbors")
    confidence = target.get("confidence")
    if type(confidence) not in (float, int) or not .65 <= confidence <= 1:
        raise ValueError("component region estimate requires confidence >= .65")
    with Image.open(source) as image:
        normalize_rect(target["source_bbox_px"], image)


def verify_final_visibility(blender: str, scene_file: Path, target: dict,
                            source_sha: str, out: Path) -> dict:
    """Reject improved pixels if real 3D line-of-sight hides a required part."""
    spec_file = out / "required_parts.json"
    evidence_file = out / "actual_visibility.json"
    dump(spec_file, {"schema": "last-light.component-visibility-constraints.v1",
                     "candidate_id": target["candidate_id"], "source_sha256": source_sha,
                     "input_scene_sha256": sha256(scene_file),
                     "required_visible_components": target["required_visible_components"],
                     "approval": "NOT_GOLDEN"})
    command = [blender, "-b", str(scene_file), "--python",
               str(ROOT / "tools/recipe_architect/blender_visibility_probe.py"), "--",
               "--constraints", str(spec_file), "--out", str(evidence_file)]
    with (out / "geometry_visibility_probe.log").open("w") as logfile:
        try:
            process = subprocess.run(command, stdout=logfile, stderr=subprocess.STDOUT,
                                     timeout=180, check=False)
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError("post-revision Blender visibility probe timed out") from exc
    if process.returncode or not evidence_file.is_file():
        raise RuntimeError("post-revision Blender visibility probe failed")
    evidence = json.loads(evidence_file.read_text())
    if (evidence.get("source_sha256") != source_sha or
            evidence.get("candidate_id") != target["candidate_id"] or
            evidence.get("required_visible_components") != target["required_visible_components"]):
        raise ValueError("actual visibility evidence is not pinned to this revised candidate")
    first = evidence["orientations"][0]
    passed = all(first["required_parts"][name]["ray_hit_samples"] >= 1 and
                 first["required_parts"][name]["on_screen_samples"] > 0
                 for name in target["required_visible_components"])
    return {"geometry_visible": passed, "checked_heading": 0,
            "required_parts": first["required_parts"],
            "actual_blender_scene_raycast": True}


def optimize(recipe_file: Path, source: Path, target_file: Path, out: Path, *,
             blender: str = "blender", step: float = .18, max_previews: int = 8,
             min_gain: float = .010, max_pixel_regression: float = .020,
             render_func=run_blender) -> dict:
    if type(max_previews) is not int or not 0 <= max_previews <= 8:
        raise ValueError("max eight real preview attempts")
    if not 0 <= max_pixel_regression <= .04 or not 0 < min_gain <= .10:
        raise ValueError("unbounded geometry-optimization acceptance thresholds")
    starting = json.loads(recipe_file.read_text())
    validate(starting, source, full_schema=True)
    target = json.loads(target_file.read_text())
    validate_target(target, starting, source)
    # The real Blender metric, contact gate and raycast still decide acceptance.
    suggestions = guided_variants(starting, target, step=step)[:max_previews]
    fresh_output(out)
    out.mkdir(parents=True, exist_ok=False)

    def render_once(doc: dict, name: str):
        folder = out / name
        filename = folder / "recipe.json"
        dump(filename, doc)
        render_func(blender, filename, folder, headings=1, export=False)
        metrics = compare(source, folder / "heading_00.png")
        feature = measured_feature(source, target, folder / "heading_00.png",
                                   folder / "component_projections.json")
        contacts = measured_contacts(folder / "component_projections.json", target)
        return folder, metrics, feature, contacts

    _, base_visual, base_feature, base_contacts = render_once(starting, "baseline_preview")
    if any(gap > .08 for gap in base_contacts.values()):
        raise ValueError("baseline critical geometry is disconnected; manual inspection required")
    winner = None
    best_error = base_feature["feature_error"]
    trials = []
    for idx, (proposal, mutation) in enumerate(suggestions):
        folder, visual, feature, contacts = render_once(proposal, f"trial_{idx:02d}")
        regression = round(base_visual["pixel_score"] - visual["pixel_score"], 6)
        contact_pass = all(gap <= max(.05, base_contacts[name] + .025)
                           for name, gap in contacts.items())
        eligible = (contact_pass and regression <= max_pixel_regression and
                    feature["feature_error"] < best_error - 1e-6)
        trials.append({"trial": idx, "mutation": mutation, "feature": feature,
                       "pixel_score": visual["pixel_score"], "pixel_regression": regression,
                       "physical_contact_gaps_m": contacts, "contact_gate_pass": contact_pass,
                       "eligible": eligible, "render_folder": str(folder)})
        if eligible:
            winner = (proposal, mutation, visual, feature)
            best_error = feature["feature_error"]
    gain = round(base_feature["feature_error"] - best_error, 6)
    accepted = winner is not None and gain >= min_gain
    result = {"schema": "last-light.component-geometry-correction.v1",
              "candidate_id": starting["identity"]["candidate_id"],
              "source_sha256": sha256(source), "provenance": target["provenance"],
              "component": target["component"], "baseline_feature": base_feature,
              "baseline_physical_contact_gaps_m": base_contacts,
              "baseline_pixel_score": base_visual["pixel_score"],
              "preview_blender_executions": len(trials) + 1,
              "max_previews": max_previews, "trials": trials,
              "measured_feature_gain": gain,
              "status": "ACCEPTED_GEOMETRY_REVIEW_CANDIDATE" if accepted else "HOLD_NO_BOUNDED_GEOMETRY_GAIN",
              "shape_changed": accepted, "golden_approved": False,
              "independent_vision_model_used": target["provenance"] == "local_vlm_component_detection",
              "automatic_game_admission": False}
    if accepted:
        proposal, mutation, _, _ = winner
        final = out / "revised_real_mesh"
        candidate_file = final / "recipe.json"
        dump(candidate_file, proposal)
        render_func(blender, candidate_file, final, headings=16, export=True, timeout=480)
        final_metrics = compare(source, final / "heading_00.png")
        final_feature = measured_feature(source, target, final / "heading_00.png",
                                         final / "component_projections.json")
        final_contacts = measured_contacts(final / "component_projections.json", target)
        glb = inspect_glb(final / "candidate.glb")
        if (final_feature["feature_error"] > base_feature["feature_error"] - min_gain or
                final_metrics["pixel_score"] < base_visual["pixel_score"] - max_pixel_regression):
            raise RuntimeError("final exported mesh failed independently measured acceptance gate")
        if any(gap > max(.05, base_contacts[name] + .025) for name, gap in final_contacts.items()):
            raise RuntimeError("source-visible part disconnected from an annotated neighbor")
        visibility = verify_final_visibility(blender, final / "editable_candidate.blend", target,
                                             sha256(source), out)
        if not visibility["geometry_visible"]:
            raise RuntimeError("revised part blocks a source-visible critical component; refuse promotion")
        result.update({"revised_recipe_path": str(candidate_file), "revised_glb_path": str(final / "candidate.glb"),
                       "revised_blend_path": str(final / "editable_candidate.blend"),
                       "revised_glb_sha256": glb["sha256"], "final_pixel_score": final_metrics["pixel_score"],
                       "final_feature": final_feature, "mutation": mutation,
                       "final_physical_contact_gaps_m": final_contacts,
                       "post_revision_component_visibility": visibility,
                       "final_real_blender_export": True, "technical_glb_structure_pass": glb["valid_glb_structure"]})
    else:
        result.update({"final_pixel_score": base_visual["pixel_score"],
                       "final_feature": base_feature, "final_real_blender_export": False})
    dump(out / "geometry_correction_report.json", result)
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--recipe", type=Path, required=True)
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--target", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--blender", default="blender")
    p.add_argument("--max-previews", type=int, default=8)
    p.add_argument("--step", type=float, default=.18)
    a = p.parse_args()
    r = optimize(a.recipe, a.source, a.target, a.out, blender=a.blender,
                 max_previews=a.max_previews, step=a.step)
    print("LL_ACTUAL_COMPONENT_GEOMETRY", r["component"], r["status"],
          "FEATURE_GAIN", r["measured_feature_gain"], "NOT_GOLDEN", flush=True)


if __name__ == "__main__":
    main()
