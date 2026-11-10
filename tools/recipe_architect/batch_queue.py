"""Checkpointed 10–100 sheet-reference queue with three-job execution waves.

Every job is an independent, verified private crop -> local VLM -> procedural
Blender -> render comparison attempt. Only a running *local* vision endpoint may
receive the pixels. No inference or Blender work happens while creating a queue.
The three-build safety cap is per dispatch, never silently raised to 100.
"""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import re
import shutil
import signal
import socket
import subprocess
import sys
import time
import uuid
from pathlib import Path

from .batch import fresh_output
from .contract import sha256
from .local_vlm import checked_loopback_url
from .pilot import ROOT, dump


SCHEMA = "last-light.recipe-architect-100-queue.v1"
INPUT_SCHEMA = "last-light.local-vlm-sheet-crops.v1"
SUPPORTED = (10, 20, 40, 50, 60, 100)
MAX_PER_DISPATCH = 3
MAX_ATTEMPTS = 2
MIN_FREE_MEMORY = 1_500_000_000
MIN_FREE_DISK = 2_000_000_000
MAX_JOB_SECONDS = 1800
ID = re.compile(r"LL-FGS-\d{4}\Z")


def _source_records(manifest_path: Path) -> tuple[dict, dict[str, dict]]:
    data = manifest_path.read_bytes()
    manifest = json.loads(data)
    rows = manifest.get("crops")
    if (manifest.get("schema") != INPUT_SCHEMA or
        manifest.get("whole_sheet_isolation_used") is not True or
        not isinstance(rows, list) or len(rows) not in SUPPORTED or
        manifest.get("extracted") != len(rows)):
        raise ValueError("queue requires a complete verified 10–100 isolated crop manifest")
    root = manifest_path.parent.resolve()
    indexed = {}
    seen_positions = set()
    for item in rows:
        ref = item.get("reference_id")
        slot = item.get("sheet_position")
        if not isinstance(ref, str) or not ID.fullmatch(ref) or not isinstance(slot, int) or slot < 1:
            raise ValueError("untrusted source reference identifier")
        if ref in indexed or slot in seen_positions or ref != f"LL-FGS-{slot:04d}":
            raise ValueError("duplicate or mismatched reference slots")
        seen_positions.add(slot)
        relative = item.get("crop_file")
        expected = f"crops/ref_{slot:04d}.png"
        if relative != expected:
            raise ValueError("untrusted crop location")
        image_path = root / expected
        if (image_path.is_symlink() or not image_path.is_file() or
            not image_path.resolve().is_relative_to(root) or
            sha256(image_path) != item.get("crop_sha256")):
            raise ValueError("missing, moved or changed reference image")
        isolation = item.get("isolated_crop_qa")
        if (not isinstance(isolation, dict) or
            isolation.get("method") != "whole_sheet_connected_component_v1"):
            raise ValueError("reference did not pass an acknowledged isolation method")
        if (item.get("golden_approved") is not False or
            item.get("canonical_asset_id") is not None or
            item.get("source_rights") != "founder_original_pending_review"):
            raise ValueError("unreviewed sheet tries to assert approvals or rights")
        indexed[ref] = item
    return {"sha256": hashlib.sha256(data).hexdigest(), "root": root,
            "manifest": manifest}, indexed


def initialize(crop_manifest: Path, out: Path) -> dict:
    src, records = _source_records(crop_manifest)
    jobs = []
    for entry in src["manifest"]["crops"]:
        safe = entry["isolated_crop_qa"]["safe_for_unattended_proposal"] is True
        jobs.append({
            "reference_id": entry["reference_id"], "sheet_position": entry["sheet_position"],
            "suggested_family_unverified": entry.get("family_suggestion_unverified"),
            "crop_sha256": entry["crop_sha256"],
            "isolation_safe": safe, "state": "READY" if safe else "ISOLATION_HOLD",
            "attempts": [], "technical_pass": False, "golden_approved": False,
            "candidate_id": None, "visual_score_final": None,
        })
    fresh_output(out)
    out.mkdir(parents=True, exist_ok=True)
    queue = {
        "schema": SCHEMA, "source_manifest_sha256": src["sha256"],
        "source_collection_id": src["manifest"]["source_collection_id"],
        "sheet_reference_count": len(jobs), "queue_capacity": 100,
        "max_builds_per_dispatch": MAX_PER_DISPATCH,
        "source_crops_embedded": False, "local_vision_required": True,
        "automatic_golden_approval": False, "canonical_admission": False,
        "production_scaling_gate_passed": False,
        "jobs": jobs,
    }
    dump(out / "queue.json", queue)
    return queue


def _atomic_dump(path: Path, payload: dict) -> None:
    scratch = path.with_name(path.name + ".tmp")
    try:
        dump(scratch, payload)
        scratch.replace(path)
    finally:
        scratch.unlink(missing_ok=True)


def _available_memory() -> int:
    try:
        for line in Path("/proc/meminfo").read_text().splitlines():
            if line.startswith("MemAvailable:"):
                return int(line.split()[1]) * 1024
    except (OSError, ValueError, IndexError):
        pass
    return 0  # Unknown resources must fail closed.


def _resources_sufficient(root: Path) -> bool:
    return (_available_memory() >= MIN_FREE_MEMORY and
            shutil.disk_usage(root).free >= MIN_FREE_DISK)


def _local_model_available(endpoint: str) -> bool:
    from urllib.parse import urlsplit
    url = urlsplit(checked_loopback_url(endpoint))
    try:
        with socket.create_connection((url.hostname, url.port), timeout=2):
            return True
    except OSError:
        return False


def _invoke_job(source: Path, *, reference_id: str, manifest: Path, out: Path,
                endpoint: str, model: str, blender: str, timeout: int) -> dict:
    command = [sys.executable, "-m", "tools.recipe_architect.autonomous_job",
               "--source", str(source), "--reference-id", reference_id,
               "--source-rights", "founder_original_pending_review",
               "--endpoint", endpoint, "--model", model, "--blender", blender,
               "--crop-manifest", str(manifest), "--max-iterations", "1",
               "--out", str(out)]
    out.parent.mkdir(parents=True, exist_ok=True)
    # The single-job engine must receive a *nonexistent* output directory.
    # Its own fresh_output guard refuses to overwrite any previous attempt.
    with (out.parent / (out.name + ".console.log")).open("xb") as log:
        process = subprocess.Popen(command, cwd=ROOT, stdout=log,
                                   stderr=subprocess.STDOUT, start_new_session=True)
        try:
            code = process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait()
            raise RuntimeError(f"per-asset process-group timeout after {timeout}s") from None
    if code:
        raise RuntimeError(f"recipe/Blender job exited {code}; inspect private job_console.log")
    result_file = out / "autonomous_job_report.json"
    if not result_file.is_file():
        raise RuntimeError("job exited without a signed provenance report")
    return json.loads(result_file.read_text())


def dispatch(queue_dir: Path, crop_manifest: Path, *, endpoint: str, model: str,
             max_jobs: int = 3, seconds_per_job: int = 900,
             wall_seconds: int = 2700, blender: str = "blender",
             retry_failed: bool = False) -> dict:
    checked_loopback_url(endpoint)
    if not re.fullmatch(r"[A-Za-z0-9_.:/-]{1,100}", model):
        raise ValueError("invalid local model ID")
    if (type(max_jobs) is not int or not 1 <= max_jobs <= MAX_PER_DISPATCH or
        type(seconds_per_job) is not int or not 60 <= seconds_per_job <= MAX_JOB_SECONDS or
        type(wall_seconds) is not int or not 60 <= wall_seconds <= 5400):
        raise ValueError("dispatch exceeds resource/time constraints")
    src, records = _source_records(crop_manifest)
    queue_dir = queue_dir.resolve()
    with (queue_dir / ".dispatch.lock").open("a+b") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise RuntimeError("another dispatch already owns this queue") from None
        path = queue_dir / "queue.json"
        queue = json.loads(path.read_text())
        if (queue.get("schema") != SCHEMA or
            queue.get("source_manifest_sha256") != src["sha256"] or
            queue.get("sheet_reference_count") != len(records) or
            queue.get("automatic_golden_approval") is not False or
            queue.get("canonical_admission") is not False or
            queue.get("production_scaling_gate_passed") is not False):
            raise ValueError("queue receipt/source drift or forbidden admission claim")
        if len(queue.get("jobs", [])) != len(records):
            raise ValueError("queue jobs incomplete")
        for job in queue["jobs"]:
            entry = records.get(job.get("reference_id"))
            if (entry is None or job.get("sheet_position") != entry["sheet_position"] or
                job.get("crop_sha256") != entry["crop_sha256"] or
                job.get("suggested_family_unverified") != entry.get("family_suggestion_unverified") or
                job.get("golden_approved") is not False or
                job.get("isolation_safe") is not
                (entry["isolated_crop_qa"]["safe_for_unattended_proposal"] is True) or
                job.get("state") not in {"READY", "ISOLATION_HOLD", "RUNNING",
                                         "JOB_FAILED", "TECHNICAL_PASS_VISUAL_REVIEW"} or
                not isinstance(job.get("attempts"), list) or
                len(job["attempts"]) > MAX_ATTEMPTS):
                raise ValueError("queue job provenance tampering")
        # After an unclean exit, the OS file lock was released but an attempt
        # may remain RUNNING on disk. Preserve its partial artifacts and require
        # an explicit retry rather than silently reusing the same directory.
        for job in queue["jobs"]:
            if job["state"] == "RUNNING":
                if not job["attempts"]:
                    raise ValueError("RUNNING job without an attempt receipt")
                job["attempts"][-1].update({
                    "state": "JOB_FAILED", "error": "interrupted_dispatch_requires_explicit_retry"})
                job["state"] = "JOB_FAILED"
                _atomic_dump(path, queue)
        selectable = [job for job in queue["jobs"] if job["isolation_safe"] and
                      (job["state"] == "READY" or
                       (retry_failed and job["state"] == "JOB_FAILED" and
                        len(job["attempts"]) < MAX_ATTEMPTS))]
        if selectable and not _local_model_available(endpoint):
            raise ValueError("no live local VLM on the requested loopback endpoint; queue unchanged")
        start = time.monotonic()
        events = []
        for job in selectable[:max_jobs]:
            remaining = int(wall_seconds - (time.monotonic() - start))
            if remaining < 60 or not _resources_sufficient(queue_dir):
                events.append({"state": "RESOURCE_OR_WALL_BUDGET_HOLD", "reference_id": job["reference_id"]})
                break
            attempt_index = len(job["attempts"]) + 1
            attempt_dir = queue_dir / "jobs" / job["reference_id"] / f"attempt_{attempt_index:02d}"
            # A preexisting attempt is evidence; never overwrite or erase it.
            if attempt_dir.exists():
                raise FileExistsError(f"preserved attempt directory: {attempt_dir}")
            image = src["root"] / records[job["reference_id"]]["crop_file"]
            item = {"attempt": attempt_index, "model": model, "endpoint_scope": "loopback_only",
                    "source_sha256": job["crop_sha256"], "state": "RUNNING"}
            job["attempts"].append(item)
            job["state"] = "RUNNING"
            _atomic_dump(path, queue)
            job_started = time.monotonic()
            try:
                result = _invoke_job(image, reference_id=job["reference_id"],
                                     manifest=crop_manifest, out=attempt_dir,
                                     endpoint=endpoint, model=model, blender=blender,
                                     timeout=min(seconds_per_job, remaining))
                if (result.get("source_reference_id") != job["reference_id"] or
                    result.get("source_sha256") != job["crop_sha256"] or
                    result.get("founder_golden_approved") is not False or
                    result.get("canonical_admitted") is not False or
                    result.get("actual_local_vision_request_completed") is not True):
                    raise ValueError("model result violates source/approval provenance")
                passed = (result.get("blender_glb_generated") is True and
                          result.get("technical_qa_pass") is True)
                item.update({"state": "TECHNICAL_PASS_VISUAL_REVIEW" if passed else "JOB_FAILED",
                             "candidate_id": result.get("candidate_id"),
                             "visual_score_final": result.get("measured_visual_score_final"),
                             "accepted_corrections": result.get("accepted_corrections")})
                job["technical_pass"] = passed
                job["candidate_id"] = result.get("candidate_id")
                job["visual_score_final"] = result.get("measured_visual_score_final")
            except (OSError, ValueError, RuntimeError, KeyError, json.JSONDecodeError) as exc:
                item.update({"state": "JOB_FAILED", "error": f"{type(exc).__name__}: {exc}"})
            item["elapsed_seconds"] = round(time.monotonic() - job_started, 3)
            item["artifact_bytes"] = sum(
                f.stat().st_size for f in attempt_dir.rglob("*") if f.is_file()
            ) if attempt_dir.exists() else 0
            job["state"] = item["state"]
            events.append({"reference_id": job["reference_id"], "state": item["state"],
                           "attempt": attempt_index})
            _atomic_dump(path, queue)
        receipt = {
            "schema": "last-light.recipe-architect-dispatch.v1",
            "dispatch_id": uuid.uuid4().hex,
            "source_manifest_sha256": src["sha256"],
            "attempted": len([e for e in events if "attempt" in e]),
            "technical_pass_this_dispatch": len([e for e in events if e["state"] == "TECHNICAL_PASS_VISUAL_REVIEW"]),
            "ready_remaining": sum(j["state"] == "READY" for j in queue["jobs"]),
            "manual_isolation_holds": sum(j["state"] == "ISOLATION_HOLD" for j in queue["jobs"]),
            "golden_approved": False, "human_model_review_required": True,
            "events": events,
        }
        dump(queue_dir / "runs" / (receipt["dispatch_id"] + ".json"), receipt)
        return receipt


def status(queue_dir: Path) -> dict:
    queue = json.loads((queue_dir / "queue.json").read_text())
    if queue.get("schema") != SCHEMA:
        raise ValueError("not a LAST LIGHT batch queue")
    jobs = queue["jobs"]
    technical = [j for j in jobs if j["state"] == "TECHNICAL_PASS_VISUAL_REVIEW"]
    families = {j.get("suggested_family_unverified") for j in technical}
    return {
        "schema": "last-light.recipe-architect-capacity-status.v1",
        "total": len(jobs),
        "ready": sum(j["state"] == "READY" for j in jobs),
        "isolation_hold": sum(j["state"] == "ISOLATION_HOLD" for j in jobs),
        "failed_needs_explicit_retry": sum(j["state"] == "JOB_FAILED" for j in jobs),
        "technical_pass_visual_review_pending": len(technical),
        "distinct_unverified_families_in_technical_pass": len(families - {None}),
        "technical_passes_required_for_scale_trial": 10,
        "held_out_quality_and_artistic_approval_verified": False,
        "batch_size_100_enabled_for_planning": len(jobs) == 100,
        "builds_per_dispatch_hard_cap": MAX_PER_DISPATCH,
        "safe_to_unconditionally_build_100": False,
        "golden_approved": False,
    }


def main() -> None:
    p = argparse.ArgumentParser(description="100-reference queue, at most three builds per dispatch")
    sub = p.add_subparsers(dest="action", required=True)
    setup = sub.add_parser("init")
    setup.add_argument("--crop-manifest", type=Path, required=True)
    setup.add_argument("--out", type=Path, required=True)
    work = sub.add_parser("dispatch")
    work.add_argument("--queue", type=Path, required=True)
    work.add_argument("--crop-manifest", type=Path, required=True)
    work.add_argument("--endpoint", required=True)
    work.add_argument("--model", required=True)
    work.add_argument("--blender", default="blender")
    work.add_argument("--max-jobs", type=int, default=3)
    work.add_argument("--seconds-per-job", type=int, default=900)
    work.add_argument("--wall-seconds", type=int, default=2700)
    work.add_argument("--retry-failed", action="store_true")
    overview = sub.add_parser("status")
    overview.add_argument("--queue", type=Path, required=True)
    args = p.parse_args()
    if args.action == "init":
        data = initialize(args.crop_manifest, args.out)
        print("LL_MESH_QUEUE", json.dumps({"jobs": data["sheet_reference_count"],
              "ready": sum(j["state"] == "READY" for j in data["jobs"]),
              "golden": False}))
    elif args.action == "dispatch":
        report = dispatch(args.queue, args.crop_manifest, endpoint=args.endpoint,
                          model=args.model, blender=args.blender,
                          max_jobs=args.max_jobs, seconds_per_job=args.seconds_per_job,
                          wall_seconds=args.wall_seconds, retry_failed=args.retry_failed)
        print("LL_MESH_DISPATCH", json.dumps(report, sort_keys=True))
    else:
        print("LL_MESH_QUEUE_STATUS", json.dumps(status(args.queue), sort_keys=True))


if __name__ == "__main__":
    main()
