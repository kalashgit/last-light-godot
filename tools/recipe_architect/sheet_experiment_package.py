"""Create a small portable, source-verified founder review ZIP for 3 pilot meshes."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from .contract import sha256


def package(experiment: Path, outputs: Path, review: Path, output: Path) -> dict:
    registry = json.loads(experiment.read_text())
    report = json.loads((review / "report.json").read_text())
    if registry["schema"] != "last-light.manual-sheet-recipe-experiment.v1":
        raise ValueError("wrong experiment")
    if report["schema"] != "last-light.manual-sheet-3d-review.v1":
        raise ValueError("wrong review")
    if [m["position"] for m in registry["models"]] != [5, 35, 44]:
        raise ValueError("three distinct pilot positions required")
    packed = []
    files: list[tuple[Path, str]] = []
    for model, evaluation in zip(registry["models"], report["results"], strict=True):
        position = model["position"]
        if evaluation["position"] != position or evaluation["founder_approved"]:
            raise ValueError("review/model mismatch")
        if sha256(Path(model["scoring_source"])) != model["source_sha256"]:
            raise ValueError("scoring image drift")
        if sha256(Path(model["source_crop"])) != model["source_masking"]["source_crop_sha256"]:
            raise ValueError("original isolated source drift")
        folder = f"ref_{position:04d}_{model['name']}"
        root = outputs / f"ref_{position:04d}" / "best"
        expected = [
            (Path(model["source_crop"]), f"{folder}/original_crop.png"),
            (Path(model["scoring_source"]), f"{folder}/scoring_reference.png"),
            (Path(model["recipe_file"]), f"{folder}/construction_recipe.json"),
            (root / "candidate.glb", f"{folder}/editable_model.glb"),
            (root / "editable_candidate.blend", f"{folder}/editable_model.blend"),
            (review / f"ref_{position:04d}_comparison.png", f"{folder}/visual_comparison.png"),
        ] + [(root / f"heading_{heading:02d}.png", f"{folder}/views/heading_{heading:02d}.png")
             for heading in range(16)]
        for path, arcname in expected:
            if not path.is_file():
                raise FileNotFoundError(path)
            files.append((path, arcname))
        if sha256(root / "candidate.glb") != evaluation["model_sha256"]:
            raise ValueError("GLB changed after measured review")
        packed.append({
            "position": position, "name": model["name"],
            "original_crop_sha256": model["source_masking"]["source_crop_sha256"],
            "scoring_reference_sha256": model["source_sha256"],
            "glb_sha256": evaluation["model_sha256"],
            "blender_meshes": evaluation["model_meshes"],
            "initial_view_pixel_score": evaluation["original_view_score"],
            "best_pixel_angle": evaluation["best_heading"],
            "best_pixel_score": evaluation["best_angle_score"],
            "pixel_best_semantic_veto": evaluation["pixel_winner_requires_semantic_veto"],
            "founder_golden_approved": False,
            "critical_visual_review": evaluation["visual_review"],
        })
    public_summary = {
        "schema": "last-light.sheet-001-050-3d-review-bundle.v1",
        "source_sheet_sha256": registry["sheet_sha256"],
        "actual_blender_models": 3,
        "manual_chatgpt_visual_recipes": 3,
        "vision_model_inference_calls": 0,
        "gpu_rental_eur": 0,
        "golden_approved": False,
        "note": "Pixel scores are alignment proxies, not semantic or final art quality",
        "models": packed,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output, "w", compression=ZIP_DEFLATED, compresslevel=6) as archive:
        for source, destination in files:
            archive.write(source, destination)
        archive.writestr("README.txt", "LAST LIGHT founder review — sheet 001–050\n"
                         "3 original procedural test meshes. Not Golden. Not game integrated.\n"
                         "Source pixels are for comparison ONLY, not model textures.\n"
                         "See individual folders for GLB, Blender scene, recipe, 16 angle renders, and side-by-side.\n"
                         "A high pixel score can hide critical components; the wooden case example exposes this.\n")
        archive.writestr("MANIFEST.json", json.dumps(public_summary, indent=2, sort_keys=True) + "\n")
    return public_summary


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--experiment", type=Path, required=True)
    p.add_argument("--outputs", type=Path, required=True)
    p.add_argument("--review", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    result = package(a.experiment, a.outputs, a.review, a.out)
    print("LL_SHEET_REVIEW_ZIP", result["actual_blender_models"], "ACTUAL_MODELS_NOT_GOLDEN")


if __name__ == "__main__":
    main()
