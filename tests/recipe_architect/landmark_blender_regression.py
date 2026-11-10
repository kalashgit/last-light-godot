"""Real CPU Blender regression for LL-127's component-level visual repair.

The reference in this regression is generated from the original procedural
recipe, then one terminal is deliberately moved. It is NOT founder artwork,
an independent artistic benchmark, or an F12 camera calibration.

Run: PYTHONPATH=. python tests/recipe_architect/landmark_blender_regression.py --out /tmp/ll-landmark-test
"""
from __future__ import annotations

import argparse
import copy
import json
import shutil
from pathlib import Path

from PIL import Image

from tools.recipe_architect.contract import sha256
from tools.recipe_architect.pilot import dump, execute, run_blender
from tools.recipe_architect.seed_recipes import battery
from tools.recipe_architect.visual_qa import fitted_point


def exercise(out: Path, blender: str = "blender", iterations: int = 3) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    truth = battery()
    truth_path = out / "known_geometry_recipe.json"
    dump(truth_path, truth)
    baseline_folder = out / "known_geometry_blender"
    run_blender(blender, truth_path, baseline_folder, headings=1, export=False)
    reference = out / "synthetic_generated_reference.png"
    shutil.copyfile(baseline_folder / "heading_00.png", reference)
    projections = json.loads((baseline_folder / "component_projections.json").read_text())
    name = "positive_terminal_post"
    with Image.open(reference) as im:
        anchor = fitted_point(projections["components"][name]["origin_px"], im)

    damaged = copy.deepcopy(truth)
    before = next(c for c in truth["components"] if c["name"] == name)
    shifted = next(c for c in damaged["components"] if c["name"] == name)
    shifted["location"][0] += .18
    damaged["identity"].update({"source_reference_id": "generated_blender_fixture_known_geometry",
                                "source_sha256": sha256(reference),
                                "source_rights": "verified_reusable"})
    damaged["visual_analysis"].update({"provider": "synthetic_blender_regression_pixel_inspection",
                                       "image_dimensions": [128, 128],
                                       "landmarks": [{"component": name, "xy": anchor, "confidence": 1.0}],
                                       "artifacts": []})
    damaged_path = out / "deliberately_wrong_recipe.json"
    dump(damaged_path, damaged)
    report = execute(damaged_path, reference, out / "repaired", blender, iterations)
    final_recipe = json.loads((out / "repaired/best/recipe.json").read_text())
    updated = next(c for c in final_recipe["components"] if c["name"] == name)
    original_error = abs(shifted["location"][0] - before["location"][0])
    repaired_error = abs(updated["location"][0] - before["location"][0])
    assertions = {
        "score_improved": report["final_score"] > report["initial_score"] + .002,
        "real_geometry_changed": repaired_error < original_error,
        "other_components_preserved": all(
            a["location"] == b["location"] for a, b in zip(damaged["components"], final_recipe["components"])
            if a["name"] != name),
        "assembly_scale_preserved": damaged["render"]["assembly_scale"] == final_recipe["render"]["assembly_scale"],
        "component_patch_accepted": any(h.get("change") == "component_location_xy" and
                                        h.get("decision") == "accepted_better_recipe"
                                        for h in report["correction_history"]),
        "not_golden": report["founder_golden_approved"] is False,
        "actual_glb": report["final_glb"]["valid_glb_structure"],
        "16_views": report["sprites"]["sprite_count"] == 16,
    }
    summary = {"fixture": "Blender-generated synthetic reference, NOT founder art",
               "original_displacement_m": original_error, "remaining_displacement_m": repaired_error,
               "initial_score": report["initial_score"], "final_score": report["final_score"],
               "accepted_corrections": report["accepted_corrections"], "assertions": assertions}
    dump(out / "regression_summary.json", summary)
    print("LL_LANDMARK_REPAIR_REGRESSION", json.dumps(summary, sort_keys=True), flush=True)
    if not all(assertions.values()):
        raise AssertionError("Blender landmark repair regression failed: " + json.dumps(assertions))
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--blender", default="blender")
    parser.add_argument("--iterations", type=int, default=3)
    args = parser.parse_args()
    exercise(args.out.resolve(), args.blender, args.iterations)
