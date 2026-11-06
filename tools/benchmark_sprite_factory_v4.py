#!/usr/bin/env python3
"""Measured, isolated V4 engineering benchmarks; never an art-approval tool.

Each size runs in a fresh process and directory. Outputs reuse the demo recipes
with deterministic variant indices. PNG count is not a count of independent
designs. Pillow and the standard library are sufficient. Peak RSS is measured
where the desktop Python resource module is available, not asserted on iPhone.
"""
import argparse
import hashlib
import importlib.util
import json
import math
import os
import platform
import subprocess
import sys
import time
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FACTORY_PATH = ROOT / "LAST_LIGHT_MASTER_SPRITE_FACTORY_V4.py"


def write_json(path, value):
    path = Path(path)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    os.replace(temporary, path)


def load_factory():
    spec = importlib.util.spec_from_file_location("last_light_v4_benchmark", FACTORY_PATH)
    module = importlib.util.module_from_spec(spec)
    # Compile the exact captured bytes so concurrent development cannot make
    # the reported source hash differ from the renderer used by this process.
    source = FACTORY_PATH.read_bytes()
    sys.modules[spec.name] = module
    exec(compile(source, str(FACTORY_PATH), "exec"), module.__dict__)
    module.benchmark_source_bytes = source
    return module


def rss_bytes():
    try:
        import resource
        value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        return int(value if sys.platform == "darwin" else value * 1024)
    except ImportError:
        return None


def verify_exports(directory, summary):
    """Read one file/manifest row at a time; do not retain image data."""
    directory = Path(directory)
    unique_ids, unique_archetypes, paths, asset_ids, image_hashes = set(), set(), set(), set(), set()
    png_bytes, checked = 0, 0
    with (directory / "manifest.jsonl").open() as stream:
        for line in stream:
            if not line.strip():
                continue
            row = json.loads(line)
            relative = row["relative_path"]
            if relative in paths or row["asset_id"] in asset_ids:
                raise ValueError("Duplicate path or asset ID in benchmark manifest")
            if Path(relative).is_absolute() or ".." in Path(relative).parts:
                raise ValueError("Unsafe export path")
            path = directory / relative
            data = path.read_bytes()
            if hashlib.sha256(data).hexdigest() != row["sha256"]:
                raise ValueError("Output hash mismatch: " + relative)
            if row["production_status"] != "visual_review_required" or row["founder_approved"]:
                raise ValueError("Benchmark data was incorrectly approved")
            unique_ids.add(row["logical_item_id"])
            unique_archetypes.add(row["archetype"])
            paths.add(relative)
            asset_ids.add(row["asset_id"])
            image_hashes.add(row["sha256"])
            png_bytes += len(data)
            checked += 1

    archived_paths, archive_bytes, zip_count = set(), 0, 0
    for value in summary["zip_paths"]:
        path = Path(value)
        if not path.is_absolute():
            path = directory / path
        archive_bytes += path.stat().st_size
        zip_count += 1
        with zipfile.ZipFile(path) as archive:
            if archive.testzip() is not None:
                raise ValueError("ZIP CRC failure: " + str(path))
            with archive.open("manifest.jsonl") as stream:
                for line in stream:
                    if not line.strip():
                        continue
                    row = json.loads(line)
                    relative = row["relative_path"]
                    if relative in archived_paths:
                        raise ValueError("Duplicate export across archive chunks")
                    if hashlib.sha256(archive.read(relative)).hexdigest() != row["sha256"]:
                        raise ValueError("ZIP content hash mismatch: " + relative)
                    archived_paths.add(relative)
    if archived_paths != paths:
        raise ValueError("ZIP export coverage differs from manifest")

    storage_bytes = sum(path.stat().st_size for path in directory.rglob("*") if path.is_file())
    return {
        "verified_png_files": checked,
        "unique_png_content_hashes": len(image_hashes),
        "duplicate_png_file_count": checked - len(image_hashes),
        "unique_logical_objects_in_manifest": len(unique_ids),
        "independently_designed_archetypes_in_manifest": len(unique_archetypes),
        "png_payload_bytes": png_bytes,
        "verified_zip_files": zip_count,
        "archive_bytes": archive_bytes,
        "directory_storage_bytes": storage_bytes,
        "zip_crc_verified": True,
        "export_and_archive_sha256_verified": True,
    }


def run_child(args):
    from PIL import __version__ as pillow_version
    factory = load_factory()
    recipes = [factory.normalize_recipe(recipe) for recipe in factory.demo_recipes()]
    directory = Path(args.child_output)
    directory.mkdir(parents=True, exist_ok=False)
    source_snapshot = directory / "LAST_LIGHT_MASTER_SPRITE_FACTORY_V4.snapshot.py"
    source_snapshot.write_bytes(factory.benchmark_source_bytes)
    count = args.child_count
    variants = int(math.ceil(count / len(recipes)))
    started = time.perf_counter()
    summary = factory.run_batch(
        recipes, directory, variants=variants, limit=count,
        workers=args.workers, chunk_size=args.chunk_size,
        resume=False, benchmark=True,
    )
    batch_wall = time.perf_counter() - started
    verification_started = time.perf_counter()
    verification = verify_exports(directory, summary)
    if verification["verified_png_files"] != count or summary["failed"]:
        raise RuntimeError("Requested benchmark count was not successfully exported")
    result = {
        "purpose": "synthetic technical benchmark; no visual or founder approval",
        "requested_png_files": count,
        "available_unique_demo_recipes": len(recipes),
        "requested_variants_per_recipe": variants,
        "generated_variants": summary["generated_variants"],
        "generated_png_files": summary["png_files"],
        "technical_qa_passes": summary["technical_qa_passes"],
        "visual_qa_passes": 0,
        "founder_approvals": 0,
        "godot_integrations": 0,
        "device_verified": False,
        "batch_wall_seconds": round(batch_wall, 6),
        "png_files_per_second": round(count / batch_wall, 6),
        "independent_verification_wall_seconds": round(time.perf_counter() - verification_started, 6),
        "peak_process_rss_bytes": rss_bytes(),
        "peak_rss_includes_import_render_export_and_verification": True,
        "python_version": platform.python_version(),
        "pillow_version": pillow_version,
        "platform": platform.platform(),
        "generator_version": factory.GENERATOR_VERSION,
        "recipe_version": factory.RECIPE_VERSION,
        "factory_sha256": hashlib.sha256(factory.benchmark_source_bytes).hexdigest(),
        "factory_source_snapshot": str(source_snapshot),
        "workers": args.workers,
        "chunk_size": args.chunk_size,
        "output_directory": str(directory),
        "factory_summary": summary,
        **verification,
    }
    write_json(directory / "benchmark_result.json", result)
    print(json.dumps({key: value for key, value in result.items() if key != "factory_summary"}, sort_keys=True))


def run_parent(args):
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_directory = Path(args.output_root).expanduser().resolve() / (timestamp + "_" + uuid.uuid4().hex[:6])
    run_directory.mkdir(parents=True, exist_ok=False)
    report = {
        "purpose": "Synthetic variant throughput and recovery engineering evidence, not a production art library",
        "created_utc": timestamp,
        "factory_path": str(FACTORY_PATH),
        "factory_sha256": hashlib.sha256(FACTORY_PATH.read_bytes()).hexdigest(),
        "run_directory": str(run_directory),
        "sizes_requested": args.sizes,
        "iPhone_CodePad_execution_verified": False,
        "results": [],
    }
    report_path = run_directory / "benchmark_report.json"
    write_json(report_path, report)
    failed = False
    for count in args.sizes:
        directory = run_directory / ("count_%06d" % count)
        log_path = run_directory / ("count_%06d.log" % count)
        command = [sys.executable, str(Path(__file__).resolve()), "--child-count", str(count),
                   "--child-output", str(directory), "--workers", str(args.workers),
                   "--chunk-size", str(args.chunk_size)]
        print("Benchmarking %d synthetic PNG exports in %s" % (count, directory), flush=True)
        start = time.perf_counter()
        timed_out = False
        with log_path.open("w") as log:
            try:
                process = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT,
                                         timeout=args.timeout_seconds, check=False)
                exit_code = process.returncode
            except subprocess.TimeoutExpired:
                timed_out = True
                exit_code = None
        result_path = directory / "benchmark_result.json"
        if exit_code == 0 and result_path.exists():
            result = json.loads(result_path.read_text())
            result["subprocess_wall_seconds"] = round(time.perf_counter() - start, 6)
            result["log_path"] = str(log_path)
            result["status"] = "passed"
            print("Verified %d PNGs, %d logical objects, %.2f seconds, peak RSS %s bytes" % (
                result["verified_png_files"], result["unique_logical_objects_in_manifest"],
                result["batch_wall_seconds"], result["peak_process_rss_bytes"]), flush=True)
        else:
            failed = True
            result = {"requested_png_files": count, "status": "timed_out" if timed_out else "failed",
                      "exit_code": exit_code, "log_path": str(log_path), "output_directory": str(directory),
                      "subprocess_wall_seconds": round(time.perf_counter() - start, 6)}
            print("Benchmark failed; inspect " + str(log_path), flush=True)
        report["results"].append(result)
        write_json(report_path, report)
    print("Measured report: " + str(report_path), flush=True)
    return int(failed)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sizes", nargs="+", type=int, default=[100, 1000, 10000])
    parser.add_argument("--output-root", default="/workspace/sprite_v4_benchmarks")
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--chunk-size", type=int, default=250)
    parser.add_argument("--timeout-seconds", type=float, default=1800)
    parser.add_argument("--child-count", type=int, help=argparse.SUPPRESS)
    parser.add_argument("--child-output", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.workers < 1 or args.chunk_size < 1 or any(size < 1 for size in args.sizes):
        parser.error("sizes, worker count and chunk size must be positive")
    if args.child_count is not None:
        if args.child_count < 1 or not args.child_output:
            parser.error("child benchmark requires positive count and output directory")
        run_child(args)
        return 0
    return run_parent(args)


if __name__ == "__main__":
    raise SystemExit(main())
