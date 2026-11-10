"""Owner-dispatched, zero-inference Recipe Architect CPU batch candidates.

Never infer source pixels from filenames. This lane re-executes three existing
SHA-pinned, human-inspected recipe *seeds* without their private PNG sources.
No source-image comparison, auto-correction, Golden promotion or game import is
performed. An Astryx (or other) UI can consume the machine-readable report.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

from .contract import validate
from .pilot import ROOT, dump, inspect_glb, run_blender


PRESETS = {
    "battery": "vehicle_battery_recipe_v1.json",
    "canteen": "canvas_canteen_recipe_v1.json",
    "skillet": "cast_iron_skillet_recipe_v1.json",
}
# Reviewed seed bytes, not merely a hash generated at runtime. Changes to
# these work orders require a new explicit review and updated test evidence.
APPROVED_RECIPE_SHA256 = {
    "battery": "774284fbc5187c8c46dd3a52f578deaee16dc1457e83aa27d00266909ce7e402",
    "canteen": "d5672d459b808a5c7d549201090c2fe88f985dd8ffe72a2122adb807176e4ae5",
    "skillet": "926570c976c79464c2a96380e0c8edf6dfd49fd63c065be2aa01a1baf0efb531",
}
SOURCE_DIR = ROOT / "data/foundry_recipe_architect"
MAX_ASSETS = 3
MAX_ARTIFACT_BYTES = 25_000_000
RUNNER_SOURCES = ("batch.py", "contract.py", "blender_execute.py", "recipe.schema.json")


def selected(preset: str, limit: int) -> list[str]:
    if preset not in {*PRESETS, "all"}:
        raise ValueError("unsupported preset")
    if type(limit) is not int or not 1 <= limit <= MAX_ASSETS:
        raise ValueError("batch size exceeds hard cap")
    if preset != "all" and limit != 1:
        raise ValueError("single preset requires limit=1")
    return list(PRESETS)[:limit] if preset == "all" else [preset]


def recipes(preset: str, limit: int) -> list[dict]:
    rows = []
    for name in selected(preset, limit):
        path = SOURCE_DIR / PRESETS[name]
        blob = path.read_bytes()
        digest = hashlib.sha256(blob).hexdigest()
        if digest != APPROVED_RECIPE_SHA256[name]:
            raise ValueError(f"preset {name} differs from reviewed recipe SHA-256")
        recipe = validate(json.loads(blob), full_schema=True)
        if recipe["identity"]["canonical_id"] is not None:
            raise ValueError("canonical production identity is forbidden in candidate batch")
        rows.append({"preset": name, "path": path, "recipe": recipe,
                     "recipe_sha256": digest})
    return rows


def fingerprint(rows: list[dict]) -> str:
    h = hashlib.sha256()
    for name in RUNNER_SOURCES:
        path = Path(__file__).with_name(name)
        h.update(name.encode() + b"\0" + path.read_bytes())
    for row in rows:
        h.update(row["preset"].encode() + b"\0" + row["recipe_sha256"].encode())
    return h.hexdigest()


def fresh_output(out: Path) -> None:
    # Never erase prior models, logs or review evidence from a retry.
    if out.exists() and (not out.is_dir() or any(out.iterdir())):
        raise FileExistsError("batch output must be a new or empty directory")


def artifact_bytes(root: Path) -> int:
    return sum(path.stat().st_size for path in root.rglob("*") if path.is_file())


def execute(preset: str, limit: int, out: Path, *, mode: str = "plan",
            blender: str = "blender", run_id: str = "local") -> dict:
    if mode not in {"plan", "build"}:
        raise ValueError("mode must be plan or build")
    if re.fullmatch(r"[A-Za-z0-9_-]{1,64}", run_id) is None:
        raise ValueError("unsafe run identifier")
    rows = recipes(preset, limit)
    out = out.resolve()
    fresh_output(out)
    out.mkdir(parents=True, exist_ok=True)
    report = {
        "schema": "last-light.recipe-architect-batch.v1",
        "run_id": run_id, "mode": mode,
        "job_fingerprint": fingerprint(rows),
        "status": "PLAN_ONLY" if mode == "plan" else "RUNNING",
        "max_assets_per_run": MAX_ASSETS, "max_artifact_bytes": MAX_ARTIFACT_BYTES,
        "candidate_count": len(rows), "technical_pass_count": 0,
        "candidates": [], "errors": [],
        "image_source_pixels_inspected_this_run": False,
        "reference_vs_render_comparison_this_run": False,
        "autonomous_vision_inference_run": False,
        "automatic_recipe_correction_run": False,
        "founder_golden_approved": False, "canonical_admission": False,
        "f11_f12_production_approved": False,
        "monetary_spend_eur": 0,
        "artifact_retention_note": "GitHub Actions artifacts expire; archive approved technical candidates separately",
    }
    for row in rows:
        recipe = row["recipe"]
        record = {
            "preset": row["preset"], "candidate_id": recipe["identity"]["candidate_id"],
            "source_reference_id": recipe["identity"]["source_reference_id"],
            "source_sha256": recipe["identity"]["source_sha256"],
            "source_rights": recipe["identity"]["source_rights"],
            "recipe_sha256": row["recipe_sha256"],
            "asset_family": recipe["identity"]["asset_family"],
            "state": "PLANNED" if mode == "plan" else "BUILDING",
            "golden_approved": False, "founder_review": "NOT_GOLDEN",
        }
        report["candidates"].append(record)
        if mode == "plan":
            continue
        folder = out / "candidates" / row["preset"]
        try:
            # Exact committed work-order bytes are passed to the existing
            # allowlisted Blender executor. No external image or AI endpoint.
            execution = run_blender(blender, row["path"], folder, headings=16,
                                    export=True, timeout=420)
            glb = inspect_glb(folder / "candidate.glb")
            from tools.foundry_sf3d_sprite_qa import pack
            sprites = pack(folder, folder / "sprites")
            if sprites["status"] != "TECHNICAL_PASS_VISUAL_PENDING":
                raise ValueError("sprite QA refused candidate")
            geom = json.loads((folder / "geometry_qa.json").read_text())
            if geom["mesh_objects"] < 3 or geom["rendered_headings"] != 16:
                raise ValueError("invalid Blender geometry counts")
            record.update({
                "state": "TECHNICAL_PASS_VISUAL_PENDING", "meshes": geom["mesh_objects"],
                "triangles_estimate": geom["triangles_estimate"],
                "blender_version": geom["blender_version"],
                "glb_sha256": glb["sha256"],
                "blend_sha256": geom["editable_candidate.blend_sha256"],
                "distinct_headings": sprites["distinct_frame_hashes"],
                "execution_exit": execution["exit_code"],
                "artifacts": {name: str((folder / target).relative_to(out)) for name, target in {
                    "glb": "candidate.glb", "blend": "editable_candidate.blend",
                    "atlas": "sprites/world_atlas_16.png",
                    "inventory": "sprites/inventory_64.png",
                    "contact_sheet": "sprites/contact_sheet_16.png",
                    "log": "blender.log"}.items()},
            })
            report["technical_pass_count"] += 1
        except (OSError, RuntimeError, ValueError, KeyError) as exc:
            record["state"] = "TECHNICAL_FAIL"
            record["error"] = f"{type(exc).__name__}: {exc}"
            report["errors"].append({"preset": row["preset"], "reason": record["error"]})
        if artifact_bytes(out) > MAX_ARTIFACT_BYTES:
            report["errors"].append({"preset": row["preset"], "reason": "artifact size budget exceeded"})
            break
    if mode == "build":
        report["status"] = ("TECHNICAL_PASS_VISUAL_PENDING" if not report["errors"] and
                            report["technical_pass_count"] == len(rows) else "TECHNICAL_FAIL")
    report["observed_artifact_bytes"] = artifact_bytes(out)
    dump(out / "batch_report.json", report)
    return report


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--mode", choices=["plan", "build"], default="plan")
    p.add_argument("--preset", choices=["all", *PRESETS], default="battery")
    p.add_argument("--limit", type=int, default=1)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--blender", default="blender")
    p.add_argument("--run-id", default="local")
    args = p.parse_args()
    report = execute(args.preset, args.limit, args.out, mode=args.mode,
                     blender=args.blender, run_id=args.run_id)
    print("LL_RECIPE_BATCH", json.dumps({
        "status": report["status"], "candidates": report["candidate_count"],
        "technical_pass": report["technical_pass_count"], "errors": report["errors"],
        "golden": False}, sort_keys=True), flush=True)
    if report["status"] == "TECHNICAL_FAIL":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
