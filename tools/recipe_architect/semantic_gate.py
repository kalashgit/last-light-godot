"""Fail-closed, component-aware review and bounded camera correction.

Consumes Blender ray-cast occlusion evidence and pixel metrics. Human/VLM
identified source-visible components are required: this detector does NOT
independently discover which parts should exist in an arbitrary new object.
"""
from __future__ import annotations

import argparse
import copy
import json
import subprocess
from pathlib import Path

from .batch import fresh_output
from .contract import sha256, validate
from .pilot import dump

ROOT = Path(__file__).resolve().parents[2]


def select_heading(pixel_metrics: list[dict], visibility: dict, *, minimum_ray_hits: int = 1) -> dict:
    if visibility.get("schema") != "last-light.component-visibility-evidence.v1":
        raise ValueError("missing actual Blender component-visibility evidence")
    if type(minimum_ray_hits) is not int or not 1 <= minimum_ray_hits <= 9:
        raise ValueError("invalid ray support")
    scores = {r["heading"]: r for r in pixel_metrics}
    orientations = visibility["orientations"]
    if set(scores) != set(range(16)) or len(pixel_metrics) != 16 or len(orientations) != 16:
        raise ValueError("expected 16 real directional views")
    required = visibility["required_visible_components"]
    options = []
    for row in orientations:
        heading = row["heading"]
        if heading not in scores or set(row["required_parts"]) != set(required):
            raise ValueError("missing source-visible component evidence")
        passes = all(row["required_parts"][name]["ray_hit_samples"] >= minimum_ray_hits
                     and row["required_parts"][name]["on_screen_samples"] > 0
                     for name in required)
        options.append({"heading": heading, "pixel_score": scores[heading]["pixel_score"],
                        "semantic_geometry_gate_pass": passes,
                        "visible_count": sum(row["required_parts"][name]["ray_hit_samples"] >= minimum_ray_hits
                                             for name in required),
                        "required_total": len(required)})
    unrestricted = max(options, key=lambda option: option["pixel_score"])
    eligible = [option for option in options if option["semantic_geometry_gate_pass"]]
    if not eligible:
        return {"status": "HOLD_ALL_ANGLES_OCCLUDED", "unrestricted_pixel_winner": unrestricted,
                "approved_candidate": None, "options": options,
                "human_approval": False, "autonomous_semantic_vision_run": False}
    chosen = max(eligible, key=lambda option: option["pixel_score"])
    return {"status": "GEOMETRY_VISIBLE_CANDIDATE_PENDING_VISUAL_REVIEW",
            "unrestricted_pixel_winner": unrestricted, "approved_candidate": chosen,
            "pixel_winner_vetoed": not unrestricted["semantic_geometry_gate_pass"],
            "options": options, "human_approval": False,
            "autonomous_semantic_vision_run": False}


def correct_camera(recipe: dict, selected_heading: int) -> dict:
    if not 0 <= selected_heading < 16:
        raise ValueError("invalid orientation correction")
    repaired = copy.deepcopy(recipe)
    repaired["render"]["camera_azimuth_deg"] = (
        repaired["render"]["camera_azimuth_deg"] - 22.5 * selected_heading) % 360
    repaired["identity"]["recipe_version"] += 1
    repaired["identity"]["generation_method"] = "reviewed_revision"
    return repaired


def evaluate(review_file: Path, outputs: Path, dest: Path, *, blender: str = "blender") -> dict:
    """Run actual Blender occlusion probe without mutating any existing scene."""
    registry = json.loads(review_file.read_text())
    if registry.get("schema") != "last-light.manual-sheet-3d-review.v1":
        raise ValueError("wrong source evaluation report")
    fresh_output(dest)
    dest.mkdir(parents=True, exist_ok=False)
    candidates = []
    for result in registry["results"]:
        pos = result["position"]
        base = outputs / f"ref_{pos:04d}" / "best"
        recipe_path = base / "recipe.json"
        scene = base / "editable_candidate.blend"
        original_recipe = json.loads(recipe_path.read_text())
        qa = json.loads((base / "geometry_qa.json").read_text())
        if (sha256(scene) != qa["editable_candidate.blend_sha256"] or
                sha256(base / "candidate.glb") != result["model_sha256"] or
                original_recipe["identity"]["candidate_id"] != qa["candidate_id"]):
            raise ValueError("Blender source artifact drift")
        required = result["visual_review"]["required_visible_parts"]
        observed = {o["component"] for o in original_recipe["visual_analysis"]["observations"]}
        if not set(required).issubset(observed):
            raise ValueError("critical geometry not grounded in source observations")
        folder = dest / f"ref_{pos:04d}"
        spec = {"schema": "last-light.component-visibility-constraints.v1",
                "candidate_id": original_recipe["identity"]["candidate_id"],
                "source_sha256": original_recipe["identity"]["source_sha256"],
                "required_visible_components": required,
                "input_scene_sha256": sha256(scene),
                "approval": "NOT_GOLDEN"}
        dump(folder / "constraints.json", spec)
        command = [blender, "-b", str(scene), "--python",
                   str(ROOT / "tools/recipe_architect/blender_visibility_probe.py"), "--",
                   "--constraints", str(folder / "constraints.json"),
                   "--out", str(folder / "visibility.json")]
        with (folder / "probe.log").open("w") as log:
            try:
                proc = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT,
                                      timeout=180, check=False)
            except subprocess.TimeoutExpired as exc:
                raise RuntimeError("Blender semantic probe timed out") from exc
        if proc.returncode or not (folder / "visibility.json").is_file():
            raise RuntimeError(f"Blender semantic probe failed: {folder / 'probe.log'}")
        evidence = json.loads((folder / "visibility.json").read_text())
        if (evidence["candidate_id"] != spec["candidate_id"] or
                evidence["source_sha256"] != spec["source_sha256"]):
            raise ValueError("visibility evidence not bound to current recipe")
        selection = select_heading(result["all_angle_metrics"], evidence)
        candidate_file = None
        if selection["approved_candidate"] is not None:
            correction = correct_camera(original_recipe, selection["approved_candidate"]["heading"])
            validate(correction, full_schema=True)
            candidate_file = folder / "camera_correction_candidate.json"
            dump(candidate_file, correction)
        record = {"position": pos, "candidate_id": spec["candidate_id"],
                  "selection": selection, "correction_recipe_path": str(candidate_file) if candidate_file else None,
                  "source_sha256": spec["source_sha256"],
                  "approval": "NOT_GOLDEN", "live_vision_model_called": False,
                  "actual_blender_raycast_run": True}
        dump(folder / "decision.json", record)
        candidates.append(record)
    summary = {"schema": "last-light.source-visible-gate-run.v1",
               "model_count": len(candidates), "models": candidates,
               "golden_approved": False, "autonomous_semantic_vision_run": False,
               "corrections_are_candidates_not_artistic_approval": True}
    dump(dest / "summary.json", summary)
    return summary


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--review", type=Path, required=True)
    p.add_argument("--outputs", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--blender", default="blender")
    a = p.parse_args()
    report = evaluate(a.review, a.outputs, a.out, blender=a.blender)
    for item in report["models"]:
        result = item["selection"]
        heading = result["approved_candidate"]["heading"] if result["approved_candidate"] else None
        print("LL_SOURCE_VISIBLE_GATE", item["position"], result["status"],
              "PIXEL_BEST", result["unrestricted_pixel_winner"]["heading"],
              "VISIBLE_BEST", heading, "NOT_GOLDEN", flush=True)


if __name__ == "__main__":
    main()
