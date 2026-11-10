"""Bounded original-model *authoring* handoff for the LAST LIGHT 3D agent.

This planner intentionally does not bypass semantic identity/rights/original
physical recipe checks or feed screenshots into a geometry/texture generator.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .build import SOURCE_DIR, build


def plan(records: list[dict], start: int, count: int) -> dict:
    if not 1 <= start <= 400 or count not in (10, 20, 40, 50, 60, 100, 200):
        raise ValueError("Only bounded 10, 20, 40, 50, 60, 100 or 200 reference authoring jobs")
    selected = [r for r in records if r["sheet_index"] >= start][:count]
    if len(selected) != count:
        raise ValueError("Requested more reference jobs than verified pictured slots")
    if any(r["admission"]["production_model_admitted"] or r["admission"]["founder_3d_golden_approved"] for r in selected):
        raise ValueError("Unexpected approval bits in reference-only queue")
    return {
        "schema_version": 1, "engine_lane": "F09_ORIGINAL_3D_RECIPE_AUTHORING",
        "status": "AWAITING_INDIVIDUAL_SEMANTIC_RIGHTS_AND_RECIPE_REVIEW",
        "reference_start": start, "selected_count": len(selected),
        "selected_reference_ids": [r["reference_id"] for r in selected],
        "jobs": selected,
        "source_pixels_to_mesh_or_texture": False,
        "production_model_admitted": False,
        "founder_3d_golden_approved": False,
        "next_stage": "review working labels and variants; create independent physical recipes then invoke Blender technical previews",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", type=Path, default=SOURCE_DIR)
    parser.add_argument("--start", type=int, default=1)
    parser.add_argument("--batch-size", type=int, choices=(10, 20, 40, 50, 60, 100, 200), default=40)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    records, _ = build(args.source_dir)
    result = plan(records, args.start, args.batch_size)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print("FOUNDER_REFERENCE_ENGINE_HANDOFF", len(result["jobs"]), result["status"])


if __name__ == "__main__":
    main()
