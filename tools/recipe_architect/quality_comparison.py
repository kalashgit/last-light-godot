"""Audit two private real-Blender packets for the same six founder references.

This is a deterministic, non-VLM, non-Golden visual/geometry checkpoint. Pixel
similarity is recorded as a diagnostic, not as semantic proof of improvement.
No candidate is accepted or released by this tool.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from .contract import sha256


def _load(packet: Path):
    intake = json.loads((packet / "benchmark_intake.json").read_text())
    report = json.loads((packet / "baseline_preview_report.json").read_text())
    if intake.get("schema") != "last-light.five-family-vision-intake.v1":
        raise ValueError("invalid founder-source intake")
    if report.get("real_vision_inferences") != 0 or report.get("founder_golden_approved") is not False:
        raise ValueError("expected candidate-only non-VLM preview")
    cases = {c["case_id"]: c for c in intake["cases"]}
    renders = {c["case_id"]: c for c in report["cases"]}
    if len(cases) != 6 or set(cases) != set(renders):
        raise ValueError("six identical source cases are required")
    return cases, renders


def compare_packets(before: Path, after: Path, out: Path) -> dict:
    if before.resolve() == after.resolve():
        raise ValueError("before and after must differ")
    b_cases, b_renders = _load(before)
    a_cases, a_renders = _load(after)
    if set(b_cases) != set(a_cases):
        raise ValueError("case sets do not match")
    summary = []
    for case_id in sorted(b_cases):
        old, new = b_cases[case_id], a_cases[case_id]
        if old["source_sha256"] != new["source_sha256"] or old["family"] != new["family"]:
            raise ValueError(f"source identity changed: {case_id}")
        for packet, case in ((before, old), (after, new)):
            if sha256(packet / case["source_file"]) != case["source_sha256"]:
                raise ValueError(f"source checksum mismatch: {case_id}")
        for render in (b_renders[case_id], a_renders[case_id]):
            if render.get("status") != "TECHNICAL_GLTF_PREVIEW_ONLY":
                raise ValueError(f"no real Blender GLB for {case_id}")
            if render.get("actual_blender_export") is not True or render.get("golden_approved") is not False:
                raise ValueError("candidate/Blender status not verified")
        old_recipe = json.loads((before / old["recipe_file"]).read_text())
        new_recipe = json.loads((after / new["recipe_file"]).read_text())
        old_parts = {p["name"] for p in old_recipe["components"]}
        new_parts = {p["name"] for p in new_recipe["components"]}
        b_score = b_renders[case_id]["visual_pixel_score"]
        a_score = a_renders[case_id]["visual_pixel_score"]
        summary.append({"case_id": case_id, "family": new["family"],
                        "source_sha256": old["source_sha256"],
                        "before_glb_sha256": b_renders[case_id]["glb_sha256"],
                        "after_glb_sha256": a_renders[case_id]["glb_sha256"],
                        "before_pixel_proxy": b_score, "after_pixel_proxy": a_score,
                        "pixel_proxy_delta": round(a_score - b_score, 6),
                        "before_mesh_count": b_renders[case_id]["mesh_count"],
                        "after_mesh_count": a_renders[case_id]["mesh_count"],
                        "added_components": sorted(new_parts - old_parts),
                        "removed_components": sorted(old_parts - new_parts),
                        "recipe_changed": old_recipe != new_recipe,
                        "quality_review": "HUMAN_REVIEW_REQUIRED"})
    result = {"schema": "last-light.five-family-geometry-quality-v2",
              "original_source_verification": "ALL_SIX_SHA256_MATCH",
              "actual_blender_glb_exports_before": 6,
              "actual_blender_glb_exports_after": 6,
              "vision_model_inferences": 0,
              "semantic_improvement_proven": False,
              "founder_golden_approved": False,
              "pixel_proxy_warning": "Pixel proxy is not geometry correctness; manual visual review needed",
              "cases": summary}
    out.mkdir(parents=True, exist_ok=True)
    (out / "quality_refinement_report.json").write_text(json.dumps(result, indent=2) + "\n")
    _sheet(before, after, summary, out / "source_before_after_NOT_GOLDEN.png")
    return result


def _sheet(before: Path, after: Path, cases: list[dict], target: Path) -> None:
    canvas = Image.new("RGB", (1516, 1160), "#101925")
    draw = ImageDraw.Draw(canvas)
    h1 = ImageFont.truetype("DejaVuSans-Bold.ttf", 27)
    name_font = ImageFont.truetype("DejaVuSans-Bold.ttf", 17)
    body = ImageFont.truetype("DejaVuSans.ttf", 13)
    draw.text((28, 17), "LAST LIGHT | Geometry quality refinement", font=h1, fill="#f2f7ff")
    draw.text((29, 57), "Original sprite  /  previous GLB  /  revised GLB    |    REAL BLENDER    |    NOT VLM    |    NOT GOLDEN", font=body, fill="#a3b8cd")

    def fitted(path: Path, bg: str, render: bool) -> Image.Image:
        art = Image.open(path).convert("RGBA")
        if render:
            canvas_bg = Image.new("RGBA", art.size, (229, 231, 232, 255))
            art = Image.alpha_composite(canvas_bg, art)
        art.thumbnail((219, 229), Image.Resampling.LANCZOS)
        if render and max(art.size) < 219:
            factor = 219 / max(art.size)
            art = art.resize((round(art.width * factor), round(art.height * factor)),
                             Image.Resampling.LANCZOS)
        frame = Image.new("RGB", (224, 231), bg)
        frame.paste(art.convert("RGB"), ((224 - art.width) // 2, (231 - art.height) // 2))
        return frame

    for i, row in enumerate(cases):
        col, r = i % 2, i // 2
        x, y = 28 + 754 * col, 89 + r * 354
        draw.rounded_rectangle((x, y, x + 724, y + 333), radius=9,
                               fill="#203143", outline="#365267", width=2)
        draw.text((x + 14, y + 8), row["case_id"], font=name_font, fill="#f4f6f8")
        for j, label in enumerate(("Founder source", "Old GLB", "Revised GLB")):
            draw.text((x + 13 + j * 236, y + 37), label, font=body, fill="#acc1d1")
        src = after / "cases" / row["case_id"] / "source.png"
        old = before / "cases" / row["case_id"] / "baseline_preview/heading_00.png"
        new = after / "cases" / row["case_id"] / "baseline_preview/heading_00.png"
        for j, (path, bg, render) in enumerate(((src, "white", False),
                                                 (old, "#e5e7e8", True),
                                                 (new, "#e5e7e8", True))):
            canvas.paste(fitted(path, bg, render), (x + 12 + j * 236, y + 58))
        delta = row["pixel_proxy_delta"]
        draw.text((x + 14, y + 300),
                  f"Pixel proxy: {row['before_pixel_proxy']:.3f} to {row['after_pixel_proxy']:.3f} ({delta:+.3f})"
                  f"  |  {row['before_mesh_count']} to {row['after_mesh_count']} meshes",
                  font=body, fill="#89dbcd" if delta >= 0 else "#f6b188")
    canvas.save(target, format="PNG", optimize=True)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--before", type=Path, required=True)
    p.add_argument("--after", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    result = compare_packets(args.before, args.after, args.out)
    print("LL_FIVE_FAMILY_QUALITY_COMPARISON", len(result["cases"]),
          "REAL_BLENDER_3D_CANDIDATES NOT_VLM NOT_GOLDEN")


if __name__ == "__main__":
    main()
