"""M02 factory V1: bounded, evidence-only candidate evaluation.

This controller does not promote candidates or execute AI-generated code. Its repair
protocol accepts independently reviewed patches in a NEW commit/run, never a
blind recursive model call. Attempts are bounded and distinguish unchanged-source
retries from actual repairs.
"""
import argparse
import hashlib
import json
import os
import struct
import subprocess
import sys
from pathlib import Path

ASSET_ID = "ll_furniture_refrigerator"
SOURCE = Path("tools/factory/furniture/refrigerator_calibration.py")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def emit(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def inspect(root):
    """Technical QA with explicit stage gates, no invented visual approval."""
    root = Path(root)
    defects = []
    report = root / "calibration_report.json"
    metadata = {}
    if not report.exists():
        defects.append({"code": "MISSING_SOURCE_REPORT", "stage": "geometry"})
    else:
        metadata = json.loads(report.read_text())
        if metadata.get("mesh_count", 0) < 70:
            defects.append({"code": "MESH_COUNT_REGRESSION", "stage": "geometry"})
        if set(metadata.get("animation_clip_names", [])) != {"F01_Door_Open", "F01_Crisper_Open"}:
            defects.append({"code": "ANIMATION_CLIPS", "stage": "animation"})
        if len(metadata.get("original_texture_images", [])) < 18:
            defects.append({"code": "PBR_TEXTURE_COVERAGE", "stage": "material"})
        for name in metadata.get("original_texture_images", []):
            if Path(name).is_absolute() or ".." in Path(name).parts or not (root / name).is_file():
                defects.append({"code": "MISSING_OR_UNSAFE_TEXTURE", "stage": "material", "file": name})
    blend = root / "refrigerator_refined_calibration.blend"
    glb = root / "refrigerator_refined_calibration.glb"
    # Blender 5 may save zstd-compressed .blend files (magic 28 B5 2F FD)
    # rather than the legacy uncompressed BLENDER header.
    if not blend.exists() or blend.stat().st_size < 1024 or not (
        blend.read_bytes()[:7] == b"BLENDER" or blend.read_bytes()[:4] == b"\x28\xb5\x2f\xfd"
    ):
        defects.append({"code": "BLEND_SOURCE", "stage": "geometry"})
    if not glb.exists() or glb.read_bytes()[:4] != b"glTF":
        defects.append({"code": "GLB_SOURCE", "stage": "geometry"})
    elif len(glb.read_bytes()) < 20 or struct.unpack_from("<I", glb.read_bytes(), 8)[0] != glb.stat().st_size:
        defects.append({"code": "GLB_LENGTH", "stage": "geometry"})
    files = []
    for state in ("hinge_open", "crisper_open"):
        for i in range(7):
            p = root / f"{state}_{i:02d}.png"
            if not p.exists() or p.read_bytes()[:8] != b"\x89PNG\r\n\x1a\n":
                defects.append({"code": "MISSING_FRAME", "stage": "sprite", "file": p.name})
            else:
                files.append(p)
        if len([p for p in files if p.name.startswith(state)]) == 7:
            if len({sha(p) for p in files if p.name.startswith(state)}) != 7:
                defects.append({"code": "DUPLICATE_ANIMATION_FRAMES", "stage": "animation", "state": state})
    return {"asset_id": ASSET_ID, "status": "TECHNICAL_CANDIDATE" if not defects else "BLOCKED", "founder_approved": False,
            "canonical_promoted": False, "engine_import_validated": False, "gameplay_integrated": False,
            "defects": defects, "source_sha256": sha(SOURCE), "files_sha256": {p.name: sha(p) for p in files},
            "geometry_source_sha256": sha(blend) if blend.exists() else None,
            "glb_sha256": sha(glb) if glb.exists() else None}


def execute(blender, output, attempts, samples):
    if not 1 <= attempts <= 3:
        raise ValueError("attempts must be in [1,3]")
    out = Path(output)
    out.mkdir(parents=True, exist_ok=True)
    attempts_log = []
    last_source = sha(SOURCE)
    for iteration in range(1, attempts + 1):
        candidate = out / f"attempt_{iteration}"
        candidate.mkdir(exist_ok=True)
        # The max-attempt policy does not disguise identical-source reruns as repairs.
        command = [blender, "-b", "--factory-startup", "--python-exit-code", "3", "-t", "2", "--python", str(SOURCE), "--", "--output", str(candidate), "--samples", str(samples)]
        try:
            with (candidate / "blender.log").open("w") as log:
                proc = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, timeout=600, check=False)
            exit_code = proc.returncode
        except (subprocess.TimeoutExpired, FileNotFoundError) as exc:
            exit_code = -1
            (candidate / "execution_error.txt").write_text(type(exc).__name__)
        result = inspect(candidate)
        if exit_code:
            result["defects"].append({"code": "BLENDER_EXECUTION_FAILURE", "stage": "runtime", "exit_code": exit_code})
            result["status"] = "BLOCKED"
        result.update({"attempt": iteration, "command": command, "blender_exit_code": exit_code,
                       "source_changed_since_previous": sha(SOURCE) != last_source, "samples": samples})
        emit(candidate / "candidate.json", result)
        attempts_log.append({"attempt": iteration, "status": result["status"], "defects": result["defects"]})
        if result["status"] == "TECHNICAL_CANDIDATE":
            break
        # No automatic AI code execution. Repeating a deterministic geometry defect
        # without changing source is useless; require a new reviewed commit/run.
        if any(d["stage"] != "runtime" for d in result["defects"]):
            break
        last_source = sha(SOURCE)
    summary = {"asset_id": ASSET_ID, "attempts": attempts_log, "iterations_used": len(attempts_log),
               "max_iterations": attempts, "total_ai_calls": 0, "estimated_ai_cost_usd": 0,
               "human_review_required": True, "canonical_promoted": False,
               "feedback_contract": "defects are structured for a separate bounded AI coding task; no automatic patch execution"}
    emit(out / "summary.json", summary)
    emit(out / "ai_feedback.json", {"asset_id": ASSET_ID, "source_sha256": sha(SOURCE),
         "defects": attempts_log[-1]["defects"], "maximum_repair_iterations": 3,
         "instructions": "Propose a source patch for independent review; do not approve, merge or deploy."})
    return 0 if attempts_log[-1]["status"] == "TECHNICAL_CANDIDATE" else 1


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--output", required=True)
    p.add_argument("--blender", default="blender")
    p.add_argument("--attempts", type=int, default=3)
    p.add_argument("--samples", type=int, default=2)
    args = p.parse_args()
    sys.exit(execute(args.blender, args.output, args.attempts, args.samples))


if __name__ == "__main__":
    main()
