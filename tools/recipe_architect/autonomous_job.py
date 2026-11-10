"""Opt-in single-asset local VLM -> allowlisted Blender -> bounded QA loop.

No external inference, GPU rental, automatically admitted models or recurring
scheduler. The existing Recipe Architect pilot owns visual comparisons and
corrections; this worker only supplies a validated new recipe and receipt.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .batch import fresh_output
from .contract import sha256
from .local_vlm import checked_loopback_url, request_proposal, seal_proposal
from .pilot import dump, execute as run_visual_loop


def check_crop_for_unattended(source: Path, manifest: Path | None, reference_id: str) -> dict:
    """When using numbered founder sheets, refuse a suspicious source cell."""
    if manifest is None:
        return {"provided_isolated_image": True, "sheet_crop_verified": False}
    registry = json.loads(manifest.read_text())
    if registry.get("schema") != "last-light.local-vlm-sheet-crops.v1":
        raise ValueError("unknown crop manifest")
    rows = [r for r in registry["crops"] if r["reference_id"] == reference_id
            and r["crop_sha256"] == sha256(source)]
    if len(rows) != 1:
        raise ValueError("source crop checksum/reference ID not in manifest")
    entry = rows[0]
    isolation = entry.get("isolated_crop_qa")
    if isolation is not None:
        if not isolation.get("safe_for_unattended_proposal", False):
            raise ValueError("uncertain sheet isolation needs human review")
    elif entry["crop_boundary_qa"]["possible_neighbor_or_truncation"]:
        raise ValueError("border-contaminated source needs human isolation review")
    if entry["golden_approved"] or entry["canonical_asset_id"] is not None:
        raise ValueError("unreviewed sheet intake cannot confer approvals")
    return {"provided_isolated_image": False, "sheet_crop_verified": True,
            "whole_sheet_isolation_verified": isolation is not None,
            "sheet_position_not_canonical_id": entry["sheet_position"]}


def execute(source: Path, *, reference_id: str, rights: str,
            endpoint: str, model: str, out: Path, blender: str = "blender",
            crop_manifest: Path | None = None, max_iterations: int = 2) -> dict:
    if not 0 <= max_iterations <= 2:
        raise ValueError("unattended pilot allows 0-2 correction iterations")
    checked_loopback_url(endpoint)
    fresh_output(out)
    provenance = check_crop_for_unattended(source, crop_manifest, reference_id)
    proposal, inference = request_proposal(source, endpoint=endpoint, model=model)
    recipe = seal_proposal(source, proposal, reference_id=reference_id,
                           source_rights=rights, model=model)
    out.mkdir(parents=True, exist_ok=True)
    recipe_path = out / "candidate_recipe.json"
    dump(recipe_path, recipe)
    dump(out / "inference_receipt.json", inference)
    # Real Blender calls happen inside the prior bounded correction engine.
    # That engine's phase-level flag is false because IT does not invoke VLMs;
    # the outer job receipt records the separately verified VLM call.
    visual = run_visual_loop(recipe_path, source, out / "visual", blender=blender,
                             max_iterations=max_iterations, auto_color_landmarks=False)
    summary = {
        "schema": "last-light.local-vlm-autonomous-job.v1",
        "candidate_id": recipe["identity"]["candidate_id"],
        "source_reference_id": reference_id, "source_sha256": sha256(source),
        "crop_provenance": provenance,
        "actual_local_vision_request_completed": True,
        "inference_receipt": "inference_receipt.json",
        "model_used": model, "new_recipe_validated": True,
        "blender_glb_generated": visual["technical_model_generated"],
        "technical_qa_pass": visual["technical_qa_pass"],
        "measured_visual_score_initial": visual["initial_score"],
        "measured_visual_score_final": visual["final_score"],
        "accepted_corrections": visual["accepted_corrections"],
        "stop_reason": visual["stop_reason"],
        "founder_golden_approved": False, "canonical_admitted": False,
        "human_visual_review_required": True, "paid_model_calls": 0,
        "gpu_rental_eur": 0,
    }
    dump(out / "autonomous_job_report.json", summary)
    return summary


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--source", required=True, type=Path)
    p.add_argument("--reference-id", required=True)
    p.add_argument("--source-rights", required=True,
                   choices=("founder_original_pending_review", "verified_reusable"))
    p.add_argument("--endpoint", required=True)
    p.add_argument("--model", required=True)
    p.add_argument("--out", required=True, type=Path)
    p.add_argument("--crop-manifest", type=Path)
    p.add_argument("--blender", default="blender")
    p.add_argument("--max-iterations", type=int, default=2)
    args = p.parse_args()
    result = execute(args.source, reference_id=args.reference_id, rights=args.source_rights,
                     endpoint=args.endpoint, model=args.model, out=args.out,
                     crop_manifest=args.crop_manifest, blender=args.blender,
                     max_iterations=args.max_iterations)
    print("LL_LOCAL_AUTONOMOUS_JOB", json.dumps({
        "candidate": result["candidate_id"], "technical": result["technical_qa_pass"],
        "corrections": result["accepted_corrections"], "golden": False}))


if __name__ == "__main__":
    main()
