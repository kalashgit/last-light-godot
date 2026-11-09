#!/usr/bin/env python3
"""Build a CALIBRATION-stage asset_package_v2 from F12 render_headings.py output.

Input is the manifest.json that F12's render_headings.py writes; no rendering here.

Steps (each reuses the owning worker's code, nothing is reimplemented):
  1. F12 compose_atlas.compose()            -> atlas_000.png..., atlas.json
  2. W06 LL_ATLAS_OUTPUTS_V2 extension       -> outputs_v2.json (pivot/canvas/pixel hashes)
  3. W06 atlas_outputs_v2.validate_outputs() -> technical QA
  4. V2 package JSON, then the shared tools/production_integration_v2/validate_package.py

Only stage CALIBRATION is produced. Canonical IDs, rights and approvals are never
written here: they belong to A00, W09 and the founder via the protected ledger.

Usage:
  python build_package.py F12_RENDER_DIR/manifest.json --frames-dir F12_RENDER_DIR \
     --calibration-report CAL-01_report.json --f12-tools F12/tools/factory/render_bridge \
     --family F01 --package-id LL-F01-CALIBRATION-... --renderer-commit <40hex> \
     --builder-commit <40hex> --source-archive-uri URI --output-dir OUT
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import atlas_outputs_v2 as outputs_v2  # noqa: E402

REPO = HERE.parents[2]
SHARED_VALIDATOR = REPO / "tools" / "production_integration_v2" / "validate_package.py"


def sha_file(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def load_shared_validator():
    spec = importlib.util.spec_from_file_location("ll_validate_package_v2", SHARED_VALIDATOR)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def build(frame_manifest: Path, frames_dir: Path, calibration_report: Path, f12_tools: Path,
          family: str, package_id: str, renderer_commit: str, builder_commit: str,
          source_archive_uri: str, output_dir: Path, profile="F12_2TO1_CALIBRATION_NOT_GOLDEN",
          fps=10, loop=False, page_size=1024, padding=2) -> dict:
    fm = json.loads(Path(frame_manifest).read_text())
    cal = json.loads(Path(calibration_report).read_text())
    output_dir = Path(output_dir).resolve()
    if "CALIBRATION" not in package_id:
        raise ValueError("this builder only emits CALIBRATION packages; package_id must say so")
    # Input is F12's own render_headings.py manifest; nothing here re-renders.
    for field in ("headings", "source_blend_sha256", "frames", "pivot_policy"):
        if field not in fm:
            raise ValueError(f"not an F12 render_headings manifest: missing {field}")
    origin = cal["measured_origin_px"]
    for f in fm["frames"]:
        if [f["width"], f["height"]] == [256, 256]:
            # Same canvas as CAL-01: the ground pivot must land on the measured origin.
            if max(abs(f["world_ground_pivot_px"][i] - origin[i]) for i in (0, 1)) > 0.01:
                raise ValueError(f"{f['key']}: pivot disagrees with CAL-01 measured origin")

    compose = outputs_v2.load_f12_module(f12_tools, "compose_atlas")
    layout_input = {"frames": [{k: f[k] for k in ("key", "file", "width", "height", "duration_ms",
                                                   "direction", "clip", "source_sha256")}
                               for f in fm["frames"]]}
    packed = compose.compose(layout_input, frames_dir, output_dir, page_size, padding)

    by_key = {f["key"]: f for f in fm["frames"]}
    frames = []
    for entry in packed["frames"]:  # F12's deterministic key order
        src = by_key[entry["key"]]
        with Image.open(Path(frames_dir) / src["file"]) as img:
            m = outputs_v2.frame_pixel_metrics(img.convert("RGBA"))
            psha = outputs_v2.pixel_sha(img)
        frames.append({**{k: entry[k] for k in outputs_v2.F12_FRAME_FIELDS},
                       "frame_index": src["frame_index"],
                       "canvas_px": [src["width"], src["height"]], "trim_offset_px": [0, 0],
                       "ground_pivot_px": src["world_ground_pivot_px"],
                       "alpha_bbox": m["alpha_bbox"], "pixel_sha256": psha})
    pages = []
    for a in packed["atlas_files"]:
        with Image.open(output_dir / a["file"]) as img:
            pages.append({"file": a["file"], "sha256": a["sha256"], "size": list(img.size)})
    clips = {c: {"fps": fps, "loop": loop} for c in sorted({f["clip"] for f in frames})}
    outputs = {
        "schema": outputs_v2.SCHEMA, "schema_version": 1, "status": "CALIBRATION_ONLY",
        "logical_tile_px": [80, 40],
        "projection": {"basis_px": cal["target_basis_px"],
                       "world_axis_mapping": cal["world_axis_mapping"],
                       "max_residual_px": cal["max_absolute_residual_px"],
                       "f12_calibration_report_sha256": sha_file(calibration_report)},
        "directions": fm["headings"],
        "heading_convention": {"source": "F12 render_headings.py",
                               "rule": "root rotation_euler.z += 2*pi*k/N (counter-clockwise from above)",
                               "zero": "source root rest orientation", "pivot": fm["pivot_policy"],
                               "status": "F12_CANDIDATE_PENDING_W01_W08_LOCK"},
        "source_frame_manifest_sha256": sha_file(frame_manifest),
        "f12_atlas": {"file": "atlas.json", "sha256": sha_file(output_dir / "atlas.json")},
        "pages": pages, "clips": clips, "frames": frames,
        "godot_hint": {"animation_name": "<clip>_d<NN>", "node_origin": "ground_pivot",
                       "texture_filter": "nearest", "mipmaps": False},
    }
    outputs_path = output_dir / "outputs_v2.json"
    outputs_path.write_text(json.dumps(outputs, indent=2, sort_keys=True) + "\n")
    qa = outputs_v2.validate_outputs(outputs_path, f12_tools, fm["headings"])

    artifacts = [{"kind": "atlas", "uri": "./" + p["file"], "sha256": p["sha256"]} for p in pages]
    artifacts += [{"kind": "metadata", "uri": "./atlas.json", "sha256": outputs["f12_atlas"]["sha256"]},
                  {"kind": "metadata", "uri": "./outputs_v2.json", "sha256": sha_file(outputs_path)}]
    package = {
        "schema_version": 2, "package_id": package_id, "family": family, "stage": "CALIBRATION",
        "source": {"sha256": fm["source_blend_sha256"], "archive_uri": source_archive_uri,
                   "builder_commit": builder_commit},
        "renderer": {"commit": renderer_commit, "profile": profile,
                     "directions": fm["headings"], "logical_tile_px": [80, 40]},
        "material_recipe_ids": [], "artifacts": artifacts,
        "outputs_contract": {"schema": outputs_v2.SCHEMA, "uri": "./outputs_v2.json"},
        "approval_note": "CALIBRATION ONLY: not A00 canonical, not W09-reviewed, not founder Golden",
        "mass_production_authorized": False,
    }
    package_path = output_dir / "asset_package_v2.json"
    package_path.write_text(json.dumps(package, indent=2, sort_keys=True) + "\n")
    shared = load_shared_validator()
    stage = shared.validate_package(json.loads(package_path.read_text()), package_path)
    return {"status": "BUILT_CALIBRATION_PACKAGE", "shared_validator": "VALID_CANDIDATE_NOT_APPROVED",
            "stage": stage, "package_sha256": sha_file(package_path), "outputs_qa": qa}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("frame_manifest", type=Path)
    ap.add_argument("--frames-dir", type=Path, required=True)
    ap.add_argument("--calibration-report", type=Path, required=True)
    ap.add_argument("--f12-tools", type=Path, required=True)
    ap.add_argument("--family", required=True)
    ap.add_argument("--package-id", required=True)
    ap.add_argument("--renderer-commit", required=True)
    ap.add_argument("--builder-commit", required=True)
    ap.add_argument("--source-archive-uri", required=True)
    ap.add_argument("--output-dir", type=Path, required=True)
    a = ap.parse_args()
    result = build(a.frame_manifest, a.frames_dir, a.calibration_report, a.f12_tools, a.family,
                   a.package_id, a.renderer_commit, a.builder_commit, a.source_archive_uri, a.output_dir)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
