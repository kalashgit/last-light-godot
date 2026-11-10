"""Compare real Blender views against source, without assigning art approval.

The ranking is a 2D pixel proxy across 16 rotations, not a semantic quality
judge. Original source and its provenance remain private technical inputs.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from .pilot import dump, inspect_glb
from .visual_qa import compare, normalized

HUMAN_VISUAL_FINDINGS = {
    5: {"required_visible_parts": ["upper_hole_shadow", "bottom_flange", "thread_core"],
        "review_findings": ["Spool geometry and colors resemble source; thread microtexture and top hole depth remain stylized"],
        "best_pixel_angle_semantically_usable": True},
    35: {"required_visible_parts": ["wood_handle", "head_socket", "steel_blade_wedge"],
         "review_findings": ["View 2 improves shaft diagonal and blade alignment; metal head remains too blocky and smooth"],
         "best_pixel_angle_semantically_usable": True},
    44: {"required_visible_parts": ["case_lid_rim", "top_lid_plank_01", "brass_latch_upper"],
         "review_findings": ["Highest pixel-score view 12 hides the source-visible front latch",
                             "Default view shows latch but the side profile and wood detail still diverge"],
         "best_pixel_angle_semantically_usable": False},
}


def render_comparison(src: Path, default: Path, selected: Path, out: Path,
                      title: str, score: float, heading: int) -> None:
    size, margin, gap, header = 256, 24, 16, 78
    width = margin * 2 + 3 * size + 2 * gap
    canvas = Image.new("RGB", (width, header + size + 60), (235, 238, 241))
    draw = ImageDraw.Draw(canvas)
    draw.text((margin, 12), title.replace("_", " ").upper(), fill=(24, 29, 35))
    draw.text((margin, 34), f"Best angle: {heading}/16  |  Pixel proxy: {score:.3f}  |  NOT Golden",
              fill=(63, 68, 74))
    for i, (path, label) in enumerate(((src, "Source reference"),
                                       (default, "Original view"),
                                       (selected, "Closest of 16 angles"))):
        x = margin + i * (size + gap)
        with Image.open(path) as im:
            rgba = normalized(im, size)
        background = Image.new("RGBA", (size, size), (246, 246, 246, 255))
        background.alpha_composite(rgba)
        canvas.paste(background.convert("RGB"), (x, header))
        draw.rectangle((x, header, x + size - 1, header + size - 1), outline=(185, 190, 197), width=1)
        draw.text((x, header + size + 14), label, fill=(34, 40, 49))
    out.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out)


def build(experiment: Path, outputs: Path, output: Path) -> dict:
    data = json.loads(experiment.read_text())
    if data["schema"] != "last-light.manual-sheet-recipe-experiment.v1":
        raise ValueError("wrong sheet experiment manifest")
    results = []
    for entry in data["models"]:
        pos = entry["position"]
        base = outputs / f"ref_{pos:04d}"
        report_file = base / "pilot_report.json"
        if not report_file.is_file():
            raise FileNotFoundError(report_file)
        pilot = json.loads(report_file.read_text())
        if not pilot["technical_model_generated"] or not pilot["technical_qa_pass"]:
            raise ValueError(f"incomplete actual Blender pilot for {pos}")
        scoring = Path(entry["scoring_source"])
        if pilot["source_sha256"] != entry["source_sha256"]:
            raise ValueError("source provenance mismatch")
        options = []
        for heading in range(16):
            path = base / "best" / f"heading_{heading:02d}.png"
            metrics = compare(scoring, path)
            options.append({"heading": heading, "pixel_score": metrics["pixel_score"],
                            "silhouette_iou": metrics["silhouette_iou"],
                            "aspect_error": metrics["aspect_error"]})
        best = max(options, key=lambda option: option["pixel_score"])
        glb = inspect_glb(base / "best/candidate.glb")
        render_comparison(scoring, base / "best/heading_00.png",
                          base / "best" / f"heading_{best['heading']:02d}.png",
                          output / f"ref_{pos:04d}_comparison.png",
                          entry["name"], best["pixel_score"], best["heading"])
        results.append({
            "position": pos, "name": entry["name"],
            "original_view_score": options[0]["pixel_score"],
            "best_angle_score": best["pixel_score"],
            "best_heading": best["heading"], "best_silhouette_iou": best["silhouette_iou"],
            "model_meshes": glb["mesh_definitions"], "model_bytes": glb["binary_bytes"],
            "model_sha256": glb["sha256"], "all_angle_metrics": options,
            "visual_review": HUMAN_VISUAL_FINDINGS[pos],
            "pixel_winner_requires_semantic_veto": not HUMAN_VISUAL_FINDINGS[pos]["best_pixel_angle_semantically_usable"],
            "technical_qa_pass": pilot["technical_qa_pass"], "founder_approved": False,
            "review_image": str(output / f"ref_{pos:04d}_comparison.png"),
            "glb_path": str(base / "best/candidate.glb"),
            "blend_path": str(base / "best/editable_candidate.blend"),
        })
    report = {
        "schema": "last-light.manual-sheet-3d-review.v1",
        "input_sheet_sha256": data["sheet_sha256"],
        "models_tested": len(results),
        "all_models_real_blender_exports": True,
        "semantic_vision_model_used": False,
        "pixel_scores_not_golden_certification": True,
        "artistic_approval_required": True,
        "results": results,
    }
    dump(output / "report.json", report)
    return report


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--experiment", type=Path, required=True)
    p.add_argument("--outputs", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    report = build(a.experiment, a.outputs, a.out)
    for row in report["results"]:
        print("LL_SHEET_EXPERIMENT", row["position"], "GLB_MESHES", row["model_meshes"],
              "SCORE", row["original_view_score"], "BEST_ANGLE", row["best_heading"],
              "BEST_SCORE", row["best_angle_score"], "NOT_GOLDEN")


if __name__ == "__main__":
    main()
