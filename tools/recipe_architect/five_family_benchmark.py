"""Privacy-preserving five-family VLM benchmark intake, scoring and audit.

Prepare images/recipes and human-truth HOLDs locally. Neither a successful
intake nor mocked inference constitutes a real VLM benchmark. Actual detection
and Blender repair use `vision_feature_repair` with an explicitly live local
model; human annotations are NEVER included in model requests.
"""
from __future__ import annotations

import argparse
import json
import math
import shutil
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from tools.foundry_reference_sheets.build import SOURCE_DIR, build
from .batch import fresh_output
from .benchmark_seed_recipes import FACTORIES, build_seed
from .contract import sha256, validate
from .pilot import ROOT, dump, inspect_glb, run_blender
from .sheet_isolation import SheetIsolator
from .visual_qa import compare
from .vision_feature_repair import inspect_and_repair


CASEBOOK = ROOT / "data/foundry_recipe_architect/benchmarks/five_family_v1.json"
ANNOTATIONS = ROOT / "data/foundry_recipe_architect/geometry_targets"
REQUIRED_FAMILIES = {"weapons_tools", "food", "furniture", "clothing_armor", "backpacks_containers"}


def _cases() -> list[dict]:
    document = json.loads(CASEBOOK.read_text())
    cases = document["cases"]
    if (document.get("schema") != "last-light.five-family-vision-benchmark-cases.v1" or
            document.get("approval") != "NOT_GOLDEN" or
            len(cases) != 6 or
            {c["family"] for c in cases} != REQUIRED_FAMILIES or
            len({c["sheet_position"] for c in cases}) != len(cases)):
        raise ValueError("five-family casebook does not cover required research families")
    return cases


def prepare(out: Path, *, artifacts: Path | None = None,
            include_human_seed_baselines: bool = False,
            source_dir: Path = SOURCE_DIR) -> dict:
    """Version/rights-preserving private crop pack, with explicit missing inputs."""
    fresh_output(out)
    records, registry = build(source_dir)
    index = {record["sheet_index"]: record for record in records}
    sheet_specs = {Path(record["file"]).name: record for record in
                   json.loads((source_dir / "sheets_manifest_v1.json").read_text())["sheets"]}
    isolators = {}
    rows = []
    for spec in _cases():
        record = index[spec["sheet_position"]]
        if (record["working_label"] != spec["working_label"] or
                record["reference_id"] != f"LL-FGS-{spec['sheet_position']:04d}" or
                record["admission"]["production_model_admitted"]):
            raise ValueError("benchmark source no longer matches verified sheet reference")
        folder = out / "cases" / spec["case_id"]
        folder.mkdir(parents=True)
        source = folder / "source.png"
        existing = None
        if artifacts is not None and spec.get("existing_recipe"):
            existing = artifacts / "scoring_sources" / f"ref_{spec['sheet_position']:04d}.png"
        if existing is not None and existing.is_file():
            with Image.open(existing) as original:
                if original.format != "PNG" or max(original.size) > 2048:
                    raise ValueError("previous source scoring crop is not bounded PNG")
            shutil.copyfile(existing, source)
            isolation = "prior_source_scoring_crop_sha_pinned"
        else:
            sheet_name = Path(record["sheet_path"]).name
            sheet_path = source_dir / "sheets" / sheet_name
            if sha256(sheet_path) != record["sheet_sha256"]:
                raise ValueError("benchmark sheet SHA drift")
            if sheet_name not in isolators:
                with Image.open(sheet_path) as original:
                    sheet_spec = sheet_specs[sheet_name]
                    isolators[sheet_name] = SheetIsolator(original,
                        rows=sheet_spec["rows"], columns=sheet_spec["columns"])
            crop, qa = isolators[sheet_name].isolate(record["cell_row"], record["cell_column"])
            crop.save(source)
            isolation = ("verified_connected_component_crop" if qa["safe_for_unattended_proposal"]
                         else "ISOLATION_HOLD")
        recipe_status = "BASELINE_RECIPE_MISSING"
        recipe_file = folder / "recipe.json"
        if artifacts is not None and spec.get("existing_recipe"):
            original_recipe = artifacts / "recipes" / spec["existing_recipe"]
            if original_recipe.is_file():
                recipe = json.loads(original_recipe.read_text())
                if recipe["identity"]["source_sha256"] == sha256(source):
                    validate(recipe, source, full_schema=True)
                    shutil.copyfile(original_recipe, recipe_file)
                    recipe_status = "SOURCE_PINNED_BASELINE_READY"
                else:
                    recipe_status = "SOURCE_RECIPE_SHA_MISMATCH_HOLD"
        if (include_human_seed_baselines and recipe_status == "BASELINE_RECIPE_MISSING" and
                spec["case_id"] in FACTORIES):
            seed = build_seed(spec["case_id"], source,
                              reference_id=record["reference_id"])
            dump(recipe_file, seed)
            recipe_status = "PROVISIONAL_HUMAN_BASELINE_READY"
        truth_status = "GROUND_TRUTH_MISSING"
        if spec.get("provisional_annotation"):
            target = json.loads((ANNOTATIONS / spec["provisional_annotation"]).read_text())
            if target["source_sha256"] == sha256(source):
                dump(folder / "manual_truth.json", {
                    "schema": "last-light.held-out-manual-feature-truth.v1",
                    "source_sha256": sha256(source), "component": target["component"],
                    "source_bbox_px": target["source_bbox_px"], "defect_present": True,
                    "review_status": "PROVISIONAL_NEEDS_INDEPENDENT_REVIEW",
                    "provenance": "prior_founder_sheet_manual_estimate",
                })
                truth_status = "PROVISIONAL_NEEDS_INDEPENDENT_REVIEW"
            else:
                truth_status = "ANNOTATION_SOURCE_SHA_MISMATCH_HOLD"
        elif spec.get("provisional_component"):
            with Image.open(source) as image:
                from .component_geometry_optimize import normalize_rect
                normalize_rect(spec["provisional_source_bbox_px"], image)
            dump(folder / "manual_truth.json", {
                "schema": "last-light.held-out-manual-feature-truth.v1",
                "source_sha256": sha256(source),
                "component": spec["provisional_component"],
                "source_bbox_px": spec["provisional_source_bbox_px"],
                "defect_present": True,
                "review_status": "PROVISIONAL_NEEDS_INDEPENDENT_REVIEW",
                "provenance": "initial_human_visual_estimate_not_yet_independently_verified",
            })
            truth_status = "PROVISIONAL_NEEDS_INDEPENDENT_REVIEW"
        rows.append({"case_id": spec["case_id"], "family": spec["family"],
                     "reference_id": record["reference_id"], "working_label": record["working_label"],
                     "source_sha256": sha256(source), "source_file": f"cases/{spec['case_id']}/source.png",
                     "isolation": isolation, "recipe_status": recipe_status,
                     "recipe_file": f"cases/{spec['case_id']}/recipe.json" if recipe_file.exists() else None,
                     "truth_status": truth_status,
                     "truth_file": f"cases/{spec['case_id']}/manual_truth.json" if
                     (folder / "manual_truth.json").exists() else None,
                     "model_inference_completed": False, "golden_approved": False})
    receipt = {"schema": "last-light.five-family-vision-intake.v1",
               "source_collection_id": registry["collection_id"],
               "cases": rows, "families": sorted(REQUIRED_FAMILIES),
               "ready_recipe_count": sum(r["recipe_status"] in
                    ("SOURCE_PINNED_BASELINE_READY", "PROVISIONAL_HUMAN_BASELINE_READY") for r in rows),
               "independently_verified_truth_count": 0,
               "real_model_inference_count": 0, "benchmark_complete": False,
               "founder_golden_approved": False}
    dump(out / "benchmark_intake.json", receipt)
    return receipt


def bbox_iou(a: list, b: list) -> float:
    if any(not isinstance(box, list) or len(box) != 4 or
           any(type(v) not in (int, float) or not math.isfinite(v) for v in box) or
           box[2] <= box[0] or box[3] <= box[1] for box in (a, b)):
        raise ValueError("invalid independent comparison rectangle")
    ix = max(0., min(a[2], b[2]) - max(a[0], b[0]))
    iy = max(0., min(a[3], b[3]) - max(a[1], b[1]))
    return round(ix * iy / ((a[2]-a[0])*(a[3]-a[1]) + (b[2]-b[0])*(b[3]-b[1]) - ix * iy), 6)


def score_case(truth: dict, proposal: dict, repair: dict) -> dict:
    """Ground truth must be reviewed independently and withheld from inference."""
    if (truth.get("schema") != "last-light.held-out-manual-feature-truth.v1" or
            truth.get("review_status") != "INDEPENDENTLY_VERIFIED" or
            not isinstance(truth.get("defect_present"), bool)):
        raise ValueError("a provisional human rectangle cannot establish model accuracy")
    if not repair.get("actual_local_vision_request_completed") or repair.get("golden_approved") is not False:
        raise ValueError("missing real inference evidence or illegal approval claim")
    predicted_defect = proposal.get("status") == "defect"
    if proposal.get("status") not in ("defect", "no_confident_defect"):
        raise ValueError("unknown independent model decision")
    expected = truth["defect_present"]
    component_hit = (proposal.get("component") == truth.get("component")) if expected and predicted_defect else False
    iou = bbox_iou(truth["source_bbox_px"], proposal["source_bbox_px"]) if expected and predicted_defect else None
    gain = repair.get("measured_feature_gain")
    return {"correct_defect_decision": predicted_defect == expected,
            "correct_component": component_hit if expected else None,
            "source_bbox_iou": iou,
            "measured_feature_gain": gain if type(gain) in (float, int) else None,
            "shape_changed": repair.get("shape_changed") is True,
            "golden_approved": False}


def preview(packet: Path, *, blender: str = "blender") -> dict:
    """Render real preliminary GLBs; neither model inference nor Golden QA."""
    manifest = json.loads((packet / "benchmark_intake.json").read_text())
    if manifest.get("schema") != "last-light.five-family-vision-intake.v1":
        raise ValueError("wrong benchmark intake")
    rows = []
    for case in manifest["cases"]:
        if case["recipe_file"] is None or case["isolation"] == "ISOLATION_HOLD":
            rows.append({"case_id": case["case_id"], "status": "HOLD_MISSING_SOURCE_OR_RECIPE"})
            continue
        folder = packet / "cases" / case["case_id"]
        source = packet / case["source_file"]
        recipe = packet / case["recipe_file"]
        validate(json.loads(recipe.read_text()), source, full_schema=True)
        out = folder / "baseline_preview"
        fresh_output(out)
        run_blender(blender, recipe, out, headings=1, export=True)
        visual = compare(source, out / "heading_00.png")
        glb = inspect_glb(out / "candidate.glb")
        rows.append({"case_id": case["case_id"], "family": case["family"],
                     "status": "TECHNICAL_GLTF_PREVIEW_ONLY",
                     "visual_pixel_score": visual["pixel_score"],
                     "glb_sha256": glb["sha256"], "mesh_count": glb["mesh_definitions"],
                     "actual_blender_export": True, "golden_approved": False})
    report = {"schema": "last-light.five-family-baseline-preview.v1",
              "cases": rows, "actual_blender_previews": sum(r.get("actual_blender_export", False) for r in rows),
              "real_vision_inferences": 0, "founder_golden_approved": False}
    dump(packet / "baseline_preview_report.json", report)
    return report


def review_sheet(packet: Path) -> Path:
    """Honest source-vs-real-GLB diagnostic montage, never a VLM result."""
    report = json.loads((packet / "baseline_preview_report.json").read_text())
    rows = report["cases"]
    if len(rows) != 6 or report.get("real_vision_inferences") != 0:
        raise ValueError("missing six-case no-VLM baseline report")
    width, height = 1480, 1210
    canvas = Image.new("RGB", (width, height), "#121c29")
    draw = ImageDraw.Draw(canvas)
    title = ImageFont.truetype("DejaVuSans-Bold.ttf", 26)
    heading = ImageFont.truetype("DejaVuSans-Bold.ttf", 17)
    body = ImageFont.truetype("DejaVuSans.ttf", 14)
    draw.text((32, 20), "LAST LIGHT | Five-family Blender baselines", font=title, fill="#eef6ff")
    draw.text((32, 57), "Source sprite  /  real GLB render  |  NO VISION MODEL RUN  |  NOT GOLDEN", font=body, fill="#b0c3d5")

    def fitted(p: Path, *, white: bool) -> Image.Image:
        with Image.open(p) as original:
            art = original.convert("RGBA")
        if not white:
            backdrop = Image.new("RGBA", art.size, (230, 231, 232, 255))
            art = Image.alpha_composite(backdrop, art)
        art.thumbnail((248, 248), Image.Resampling.LANCZOS)
        frame = Image.new("RGB", (265, 254), "#ffffff" if white else "#e6e7e8")
        frame.paste(art.convert("RGB"), ((frame.width-art.width)//2,
                                         (frame.height-art.height)//2))
        return frame

    for idx, case in enumerate(rows):
        col, row = idx % 2, idx // 2
        left, top = 32 + col * 723, 97 + row * 361
        draw.rounded_rectangle((left, top, left + 686, top + 341), radius=11,
                               fill="#1f3043", outline="#37556d", width=2)
        draw.text((left + 20, top + 11), case["case_id"], font=heading, fill="#f2f6ff")
        draw.text((left + 22, top + 42), "Founder reference", font=body, fill="#b8cadb")
        draw.text((left + 349, top + 42), "3D Blender baseline", font=body, fill="#b8cadb")
        folder = packet / "cases" / case["case_id"]
        canvas.paste(fitted(folder / "source.png", white=True), (left + 21, top + 63))
        canvas.paste(fitted(folder / "baseline_preview/heading_00.png", white=False),
                     (left + 348, top + 63))
        if case.get("status") == "TECHNICAL_GLTF_PREVIEW_ONLY":
            score = case["visual_pixel_score"]
            text = f"Pixel proxy {score:.3f} (not semantic QA)  |  {case['mesh_count']} meshes"
        else:
            text = "BASELINE HOLD"
        draw.text((left + 21, top + 319), text, font=body, fill="#8fe0d6")
    dest = packet / "five_family_baselines_NOT_VLM_NOT_GOLDEN.png"
    canvas.save(dest, format="PNG", optimize=True)
    return dest


def run(packet: Path, out: Path, *, endpoint: str, model: str,
        blender: str = "blender") -> dict:
    """Run only complete, independently reviewed cases. No cost fallback."""
    from .local_vlm import checked_loopback_url
    from .batch_queue import _local_model_available
    checked_loopback_url(endpoint)
    manifest = json.loads((packet / "benchmark_intake.json").read_text())
    if (manifest.get("schema") != "last-light.five-family-vision-intake.v1" or
            {c["family"] for c in manifest["cases"]} != REQUIRED_FAMILIES):
        raise ValueError("wrong five-family benchmark packet")
    for case in manifest["cases"]:
        if (case["recipe_status"] not in
                ("SOURCE_PINNED_BASELINE_READY", "PROVISIONAL_HUMAN_BASELINE_READY") or
                case["isolation"] == "ISOLATION_HOLD" or
                case["truth_status"] != "INDEPENDENTLY_VERIFIED"):
            raise ValueError("five-family benchmark blocked: source, recipe or independent human truth missing")
        source = packet / case["source_file"]
        recipe = packet / case["recipe_file"]
        manual = json.loads((packet / case["truth_file"]).read_text())
        if sha256(source) != case["source_sha256"]:
            raise ValueError("private benchmark source drift")
        if (manual.get("source_sha256") != sha256(source) or
                manual.get("review_status") != "INDEPENDENTLY_VERIFIED"):
            raise ValueError("independent held-out annotation missing or source-drifted")
        validate(json.loads(recipe.read_text()), source, full_schema=True)
    if not _local_model_available(endpoint):
        raise ValueError("no live local VLM endpoint: no paid/remote fallback permitted")
    fresh_output(out)
    out.mkdir(parents=True)
    assessments = []
    for case in manifest["cases"]:
        result_dir = out / case["case_id"]
        report = inspect_and_repair(packet / case["recipe_file"],
                                    packet / case["source_file"], result_dir,
                                    endpoint=endpoint, model=model, blender=blender)
        truth = json.loads((packet / case["truth_file"]).read_text())
        proposal = json.loads((result_dir / "model_proposal_untrusted.json").read_text())
        score = score_case(truth, proposal, report)
        assessments.append({"case_id": case["case_id"], "family": case["family"], **score})
    tally = {"cases_scored": len(assessments), "families_scored": len({c["family"] for c in assessments}),
             "correct_defect_decisions": sum(c["correct_defect_decision"] for c in assessments),
             "correct_components": sum(c["correct_component"] is True for c in assessments),
             "accepted_geometry_revisions": sum(c["shape_changed"] for c in assessments)}
    result = {"schema": "last-light.five-family-vision-evaluation.v1",
              **tally, "cases": assessments, "benchmark_complete": len(assessments) == 6 and tally["families_scored"] == 5,
              "technical_metrics_only": True, "founder_golden_approved": False}
    dump(out / "benchmark_results.json", result)
    return result


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="action", required=True)
    first = sub.add_parser("prepare")
    first.add_argument("--out", required=True, type=Path)
    first.add_argument("--artifacts", type=Path,
                       help="private prior sheet-experiment-50 root (optional)")
    first.add_argument("--source-dir", type=Path, default=SOURCE_DIR)
    first.add_argument("--include-human-seed-baselines", action="store_true",
                       help="author 4 provisional non-Golden baselines from inspected physical primitives")
    checks = sub.add_parser("preview")
    checks.add_argument("--packet", type=Path, required=True)
    checks.add_argument("--blender", default="blender")
    picture = sub.add_parser("review-sheet")
    picture.add_argument("--packet", type=Path, required=True)
    live = sub.add_parser("run")
    live.add_argument("--packet", type=Path, required=True)
    live.add_argument("--out", type=Path, required=True)
    live.add_argument("--endpoint", required=True)
    live.add_argument("--model", required=True)
    live.add_argument("--blender", default="blender")
    args = p.parse_args()
    if args.action == "prepare":
        result = prepare(args.out, artifacts=args.artifacts, source_dir=args.source_dir,
                         include_human_seed_baselines=args.include_human_seed_baselines)
        print("LL_FIVE_FAMILY_BENCHMARK_INTAKE", result["ready_recipe_count"],
              "BASELINES_READY", "NOT_SCORED", flush=True)
    elif args.action == "preview":
        result = preview(args.packet, blender=args.blender)
        print("LL_FIVE_FAMILY_BLENDER_BASELINES", result["actual_blender_previews"],
              "REAL_PREVIEWS", "NOT_VLM", "NOT_GOLDEN", flush=True)
    elif args.action == "review-sheet":
        path = review_sheet(args.packet)
        print("LL_FIVE_FAMILY_PREVIEW_CONTACT_SHEET", path, flush=True)
    else:
        result = run(args.packet, args.out, endpoint=args.endpoint, model=args.model,
                     blender=args.blender)
        print("LL_FIVE_FAMILY_REAL_MODEL", result["cases_scored"], "CASES", "NOT_GOLDEN", flush=True)


if __name__ == "__main__":
    main()
