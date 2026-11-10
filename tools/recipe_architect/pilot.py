"""Bounded CPU Blender -> pixel comparison -> recipe correction -> best export.

No model inference or paid services. Explicit private original path required.
The pixel heuristic cannot make artistic/Godot/Golden approval decisions.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import subprocess
import sys
from pathlib import Path

from .contract import validate, sha256
from .visual_qa import compare

ROOT = Path(__file__).resolve().parents[2]


def dump(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def run_blender(blender: str, recipe_file: Path, out: Path, headings: int, export: bool, timeout: int = 270):
    args = [blender, "-b", "--factory-startup", "-t", "2", "--python",
            str(ROOT / "tools/recipe_architect/blender_execute.py"), "--",
            "--recipe", str(recipe_file), "--output", str(out), "--headings", str(headings)]
    if not export: args.append("--no-export")
    out.mkdir(parents=True, exist_ok=True)
    with (out / "blender.log").open("w") as log:
        try:
            proc = subprocess.run(args, stdout=log, stderr=subprocess.STDOUT, timeout=timeout, check=False)
        except subprocess.TimeoutExpired as e:
            raise RuntimeError(f"Blender timeout after {timeout}s; see {out / 'blender.log'}") from e
    if proc.returncode != 0:
        raise RuntimeError(f"Blender failed exit={proc.returncode}; see {out / 'blender.log'}")
    if not (out / "heading_00.png").is_file() or not (out / "geometry_qa.json").is_file():
        raise RuntimeError("Blender exit=0 but required evidence missing")
    return {"command": args, "exit_code": proc.returncode, "log_file": str(out / "blender.log")}


def inspect_glb(path: Path) -> dict:
    import struct
    data = path.read_bytes()
    if len(data) < 28 or data[:4] != b"glTF" or struct.unpack_from("<I", data, 4)[0] != 2 or struct.unpack_from("<I", data, 8)[0] != len(data):
        raise ValueError("corrupt GLB header/length")
    length, kind = struct.unpack_from("<I4s", data, 12)
    if kind != b"JSON" or 20 + length > len(data): raise ValueError("missing glTF JSON chunk")
    gltf = json.loads(data[20:20 + length])
    nodes = gltf.get("nodes", [])
    meshes = gltf.get("meshes", [])
    if len(meshes) < 3 or len(nodes) < 3 or not all(m.get("primitives") for m in meshes):
        raise ValueError("GLB missing actual multi-component geometry")
    return {"mesh_definitions": len(meshes), "nodes": len(nodes), "materials": len(gltf.get("materials", [])),
            "binary_bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(), "valid_glb_structure": True}


def propose_component_shift(recipe: dict, comparison: dict) -> tuple[dict, dict] | None:
    """Solve a bounded Blender-local XY translation from observed 2D landmarks.

    Only documented pixel landmarks may drive this repair. With a single
    orthographic image, Z is underconstrained and is deliberately kept fixed.
    The subsequent real Blender render must prove improvement before adoption.
    """
    candidates = sorted(comparison.get("landmarks", []),
                        key=lambda item: item["error"] * item["confidence"], reverse=True)
    for candidate in candidates:
        if candidate["error"] <= .015:
            continue
        part = next((c for c in recipe["components"] if c["name"] == candidate["component"]), None)
        if part is None or part["op"] == "boolean_cut" or not part["observed"]:
            continue
        (ax, ay), (bx, by) = candidate["local_xy_axes"]
        determinant = ax * by - bx * ay
        if not math.isfinite(determinant) or abs(determinant) < 1e-5:
            continue
        dx, dy = candidate["delta_xy"]
        shift_x = (dx * by - bx * dy) / determinant
        shift_y = (ax * dy - dx * ay) / determinant
        magnitude = math.hypot(shift_x, shift_y)
        if not math.isfinite(magnitude) or magnitude < 1e-5:
            continue
        # Do not move components more than the pre-approved per-iteration
        # geometric correction bound; huge displacements need human review.
        bound = recipe["tuning"]["scale_step"]
        fraction = min(1., bound / magnitude)
        adjustment = [round(shift_x * fraction, 6), round(shift_y * fraction, 6)]
        trial = copy.deepcopy(recipe)
        moved = next(c for c in trial["components"] if c["name"] == candidate["component"])
        for axis in range(2):
            moved["location"][axis] = round(moved["location"][axis] + adjustment[axis], 6)
        return trial, {"change": "component_location_xy", "component": candidate["component"],
                       "delta_local_m": adjustment, "before_landmark_error": candidate["error"],
                       "z_unchanged": True}
    return None


def execute(recipe: Path, source: Path, out: Path, blender: str = "blender", max_iterations: int = 2,
            auto_color_landmarks: bool = False) -> dict:
    if not 0 <= max_iterations <= 5: raise ValueError("max corrections must be <= 5")
    out = out.resolve()
    source = source.resolve()
    initial = json.loads(recipe.read_text())
    validate(initial, source, full_schema=True)
    if auto_color_landmarks and initial["visual_analysis"].get("landmarks"):
        raise ValueError("auto pixel landmarks cannot overwrite existing observed landmarks")
    history = []

    def attempt(doc, index, variant):
        folder = out / f"iteration_{index:02d}_{variant}"
        file = folder / "recipe.json"
        validate(doc, source, full_schema=True)
        dump(file, doc)
        evidence = run_blender(blender, file, folder, headings=1, export=False)
        projected = json.loads((folder / "component_projections.json").read_text())
        visual = compare(source, folder / "heading_00.png", folder,
                         doc["visual_analysis"].get("landmarks", []), projected)
        history.append({"index": index, "variant": variant, "recipe": str(file),
                        "scale": doc["render"]["assembly_scale"], "comparison": visual, "execution": evidence})
        return visual

    best = copy.deepcopy(initial)
    current = attempt(best, 0, "base")
    auto_report = None
    if auto_color_landmarks:
        from .color_landmarks import discover
        base_folder = out / "iteration_00_base"
        projection = json.loads((base_folder / "component_projections.json").read_text())
        auto_report = discover(source, best, base_folder / "heading_00.png", projection)
        dump(out / "provisional_color_landmarks.json", auto_report)
        if auto_report["landmarks"]:
            best["visual_analysis"]["landmarks"] = auto_report["landmarks"]
            validate(best, source, full_schema=True)
            # No new Blender execution is claimed here: the *same* heading-zero
            # image is re-compared against newly inspected source-color pixels.
            current = compare(source, base_folder / "heading_00.png", out / "initial_anchored_comparison",
                              auto_report["landmarks"], projection)
            history.append({"index": 0, "decision": "provisional_color_landmarks_attached",
                            "new_blender_execution": False, "comparison": current,
                            "evidence": "provisional_color_landmarks.json"})
        else:
            history.append({"index": 0, "decision": "no_unambiguous_color_landmarks",
                            "new_blender_execution": False,
                            "evidence": "provisional_color_landmarks.json"})
    start_score = current["score"]
    stopped = "iteration_bound"
    for iteration in range(1, max_iterations + 1):
        if best["visual_analysis"].get("landmarks"):
            proposal = propose_component_shift(best, current)
            if proposal is None:
                stopped = "no_actionable_landmark_displacement"
                break
            trial, change = proposal
            trial["identity"]["recipe_version"] += 1
            trial["identity"]["generation_method"] = "reviewed_revision"
            result = attempt(trial, iteration, "part_" + change["component"])
            if (result["score"] <= current["score"] + .002 or
                    result["pixel_score"] < current["pixel_score"] - .015):
                history.append({"index": iteration, "decision": "rejected_no_measured_improvement",
                                "before_score": current["score"], "trial_score": result["score"],
                                "pixel_regression": result["pixel_score"] < current["pixel_score"] - .015,
                                **change})
                stopped = "no_measured_improvement"
                break
            best, current = trial, result
            history.append({"index": iteration, "decision": "accepted_better_recipe",
                            "score": current["score"], **change})
            continue
        # Diagnose rendered silhouette's projected aspect; test real geometry
        # amendments rather than changing a score without rerendering.
        direction = 1 if current["reference_aspect"] > current["render_aspect"] else -1
        proposals = [(0, direction), (2, -direction)]
        winner, winner_metric = None, current
        for j, (axis, sign) in enumerate(proposals):
            trial = copy.deepcopy(best)
            old = trial["render"]["assembly_scale"][axis]
            trial["render"]["assembly_scale"][axis] = round(max(.55, min(1.45, old + sign * trial["tuning"]["scale_step"])), 5)
            if trial["render"]["assembly_scale"][axis] == old: continue
            trial["identity"]["recipe_version"] = best["identity"]["recipe_version"] + 1
            trial["identity"]["generation_method"] = "reviewed_revision"
            result = attempt(trial, iteration, "axis" + str(axis) + ("plus" if sign > 0 else "minus"))
            if result["score"] > winner_metric["score"] + .002:
                winner, winner_metric = trial, result
        if winner is None:
            stopped = "no_measured_improvement"
            break
        best, current = winner, winner_metric
        history.append({"index": iteration, "decision": "accepted_better_recipe", "score": current["score"],
                        "change": "assembly_scale", "scale": best["render"]["assembly_scale"]})
    final = out / "best"
    final_recipe = final / "recipe.json"
    dump(final_recipe, best)
    evidence = run_blender(blender, final_recipe, final, headings=16, export=True, timeout=480)
    final_visual = compare(source, final / "heading_00.png", final / "visual",
                           best["visual_analysis"].get("landmarks", []),
                           json.loads((final / "component_projections.json").read_text()))
    glb = inspect_glb(final / "candidate.glb")
    # Reuse existing 16-heading/64px atlas QA instead of another packing engine.
    sys.path.insert(0, str(ROOT / "tools"))
    from foundry_sf3d_sprite_qa import pack
    sprites = pack(final, final / "sprites")
    accepted = [e for e in history if e.get("decision") == "accepted_better_recipe"]
    is_founder_original = best["identity"]["source_rights"] == "founder_original_pending_review"
    report = {
        "schema": "last-light.recipe-architect-pilot.v1", "candidate_id": best["identity"]["candidate_id"],
        "source_sha256": sha256(source), "source_reference_id": best["identity"]["source_reference_id"],
        "source_rights": best["identity"]["source_rights"],
        "founder_original_sha256": sha256(source) if is_founder_original else None,
        "source_private": is_founder_original,
        "vision_method": initial["visual_analysis"]["provider"],
        "autonomous_model_inference_run": False,
        "auto_color_landmarks_requested": auto_color_landmarks,
        "provisional_color_landmarks": auto_report["landmarks"] if auto_report else [],
        "autonomous_semantic_vision_run": False,
        "initial_score": start_score, "final_score": final_visual["score"],
        "accepted_corrections": len(accepted),
        "attempts": len([e for e in history if "execution" in e]) - 1,
        "stop_reason": stopped, "correction_history": history, "final_glb": glb,
        "geometry": json.loads((final / "geometry_qa.json").read_text()),
        "sprites": sprites, "final_visual": final_visual, "final_execution": evidence,
        "technical_model_generated": True, "technical_qa_pass": sprites["status"].startswith("TECHNICAL_PASS"),
        "artistic_approved": False, "founder_golden_approved": False, "notion_admitted": False,
        "budget": {"monetary_spend_eur": 0, "billable_model_calls": 0, "gpu_rental": False},
    }
    dump(out / "pilot_report.json", report)
    print("LL_RECIPE_PILOT", json.dumps({"candidate": report["candidate_id"], "score_initial": report["initial_score"],
             "score_final": report["final_score"], "corrections": report["accepted_corrections"],
             "glb_meshes": glb["mesh_definitions"], "views": sprites["sprite_count"], "golden": False}))
    return report


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--source", required=True, type=Path)
    p.add_argument("--recipe", required=True, type=Path)
    p.add_argument("--out", required=True, type=Path)
    p.add_argument("--blender", default="blender")
    p.add_argument("--max-iterations", type=int, default=2)
    p.add_argument("--auto-color-landmarks", action="store_true",
                   help="opt-in CPU color-based provisional component anchors; NOT semantic AI vision")
    a = p.parse_args()
    execute(a.recipe, a.source, a.out, a.blender, a.max_iterations, a.auto_color_landmarks)
