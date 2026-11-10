"""Run and measure bounded camera repairs after true Blender occlusion gating.

This adjusts *viewing geometry* only. Underlying mesh deformation remains a
separate future gate. Every repair is independently rerendered, and measured
regressions are rejected while the original approved source is left intact.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .batch import fresh_output
from .contract import sha256, validate
from .pilot import dump, execute as run_visual_loop


def repair(gate_report: Path, baseline_review: Path, scoring_sources: Path,
           output: Path, *, max_real_builds: int = 3, blender: str = "blender",
           run=run_visual_loop) -> dict:
    if type(max_real_builds) is not int or not 0 <= max_real_builds <= 3:
        raise ValueError("three-real-build cap cannot be bypassed")
    gate = json.loads(gate_report.read_text())
    baseline = json.loads(baseline_review.read_text())
    if (gate.get("schema") != "last-light.source-visible-gate-run.v1" or
            baseline.get("schema") != "last-light.manual-sheet-3d-review.v1" or
            gate.get("golden_approved") is not False):
        raise ValueError("unverified visual correction input")
    known = {r["position"]: r for r in baseline["results"]}
    changes = []
    for entry in gate["models"]:
        decision = entry["selection"]
        selected = decision.get("approved_candidate")
        position = entry["position"]
        if position not in known or not decision.get("unrestricted_pixel_winner"):
            raise ValueError("incomplete camera correction evidence")
        if selected is not None and not selected["semantic_geometry_gate_pass"]:
            raise ValueError("visibility-gate bypass refused")
        if selected is None:
            changes.append((entry, None, "HOLD_OCCLUSION"))
        elif selected["heading"] == 0:
            changes.append((entry, selected, "UNCHANGED_ORIGINAL_VIEW"))
        else:
            changes.append((entry, selected, "REBUILD_REQUIRED"))
    planned = sum(state == "REBUILD_REQUIRED" for _, _, state in changes)
    if planned > max_real_builds:
        raise ValueError("camera repairs exceed bounded real Blender builds")
    fresh_output(output)
    output.mkdir(parents=True, exist_ok=False)
    records = []
    for entry, selected, state in changes:
        position = entry["position"]
        original = known[position]
        row = {"position": position, "candidate_id": entry["candidate_id"],
               "baseline_score": original["original_view_score"],
               "proposed_heading": selected["heading"] if selected else None,
               "original_pixel_winner_vetoed": entry["selection"].get("pixel_winner_vetoed", False),
               "golden_approved": False, "source_rights_auto_promoted": False,
               "autonomous_vision_model_run": False,
               "repair_type": "bounded_camera_orientation_not_mesh_deformation"}
        if state == "REBUILD_REQUIRED":
            proposal_path = Path(entry["correction_recipe_path"])
            proposal = json.loads(proposal_path.read_text())
            image = scoring_sources / f"ref_{position:04d}.png"
            validate(proposal, image, full_schema=True)
            if (sha256(image) != entry["source_sha256"] or
                    proposal["identity"]["candidate_id"] != entry["candidate_id"]):
                raise ValueError("source or repair provenance mismatch")
            rerender = run(proposal_path, image, output / f"ref_{position:04d}" / "rendered",
                           blender=blender, max_iterations=0)
            score = rerender["final_score"]
            score_gain = round(score - original["original_view_score"], 6)
            accepted = rerender["technical_qa_pass"] and score_gain >= .015
            row.update({"status": "ACCEPTED_AS_REVIEW_CANDIDATE" if accepted else "REJECTED_NO_GAIN",
                        "real_blender_execution": True, "after_score": score,
                        "measured_score_gain": score_gain,
                        "source_visible_parts_checked_before_rerender": True,
                        "glb_sha256": rerender["final_glb"]["sha256"],
                        "artifact_review_only": True})
        else:
            row.update({"status": state, "real_blender_execution": False,
                        "after_score": original["original_view_score"],
                        "measured_score_gain": 0, "artifact_review_only": True})
        records.append(row)
    result = {"schema": "last-light.source-visible-correction-receipt.v1",
              "real_builds_executed": planned, "maximum_real_builds": max_real_builds,
              "changes": records, "golden_approved": False,
              "semantic_geometry_gate_uses_blender_not_visual_ai": True}
    dump(output / "correction_report.json", result)
    return result


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--gate", type=Path, required=True)
    p.add_argument("--baseline", type=Path, required=True)
    p.add_argument("--scoring-sources", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--blender", default="blender")
    a = p.parse_args()
    result = repair(a.gate, a.baseline, a.scoring_sources, a.out, blender=a.blender)
    for item in result["changes"]:
        print("LL_SEMANTIC_CAMERA_REPAIR", item["position"], item["status"],
              "GAIN", item["measured_score_gain"], "NOT_GOLDEN", flush=True)


if __name__ == "__main__":
    main()
