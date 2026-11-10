"""Isolated, read-only mesh review rooms for 40/100-reference planning or CPU batches.

A room is a provenance container, not a Blender collection or a Golden catalog
entry. Private founder art is never copied into this dashboard. The planner may
stage 100 rooms; it does NOT increase the hard limit on actual Blender builds.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
from pathlib import Path

from PIL import Image

from tools.foundry_reference_sheets.build import SOURCE_DIR, build

from .batch import fresh_output
from .contract import sha256
from .pilot import dump, inspect_glb


SCHEMA = "last-light.mesh-workspace.v1"
MAX_ROOMS = 100
MAX_IMPORT_BYTES = 150_000_000
ID_PATTERN = re.compile(r"[A-Za-z0-9_-]{1,100}\Z")


def clean_id(value: str) -> str:
    if not isinstance(value, str) or not ID_PATTERN.fullmatch(value):
        raise ValueError("invalid isolated room identifier")
    return value


def _make(out: Path, rooms: list[dict], *, source_kind: str, fingerprint: str) -> dict:
    if not 1 <= len(rooms) <= MAX_ROOMS:
        raise ValueError("workspace size must be between 1 and 100")
    if len({room["room_id"] for room in rooms}) != len(rooms):
        raise ValueError("duplicate room identity")
    fresh_output(out)
    out.mkdir(parents=True, exist_ok=True)
    for room in rooms:
        directory = out / "rooms" / clean_id(room["room_id"])
        directory.mkdir(parents=True, exist_ok=False)
        dump(directory / "room.json", room)
    manifest = {
        "schema": SCHEMA,
        "kind": source_kind,
        "source_fingerprint_sha256": fingerprint,
        "room_count": len(rooms),
        "capacity": MAX_ROOMS,
        "production_build_cap_unchanged": 3,
        "source_pixels_publicly_embedded": False,
        "automated_vision_inference_completed": False,
        "automated_golden_approval": False,
        "founder_approval_requires_exact_artifact_review": True,
        "rooms": rooms,
    }
    dump(out / "manifest.json", manifest)
    return manifest


def plan_reference_rooms(*, start: int, count: int, out: Path,
                         source_dir: Path = SOURCE_DIR) -> dict:
    """Stage separate review workspaces from verified F09 sheet metadata.

    100 is the review/organization cap only; existing F09 Blender execution,
    local VLM and reference extraction caps remain unchanged.
    """
    if type(start) is not int or not 1 <= start <= 400:
        raise ValueError("reference start outside pictured range")
    if type(count) is not int or count not in (10, 20, 40, 100):
        raise ValueError("supported review capacities are 10, 20, 40 or 100")
    records, intake = build(source_dir)  # Validates source sheet bytes and layout.
    selected = [record for record in records if record["sheet_index"] >= start][:count]
    if len(selected) != count:
        raise ValueError("requested more rooms than verified pictured references")
    rooms = []
    for index, item in enumerate(selected, start=1):
        if item["admission"]["founder_3d_golden_approved"] or item["admission"]["production_model_admitted"]:
            raise ValueError("review-only source unexpectedly claims Golden or admission")
        reference_id = clean_id(item["reference_id"])
        rooms.append({
            "room_id": reference_id,
            "ordinal": index,
            "title": item["working_label"],
            "title_status": "UNVERIFIED_WORKING_LABEL",
            "reference_position_not_canonical_id": item["sheet_index"],
            "source_reference_id": reference_id,
            "source_sheet_sha256": item["sheet_sha256"],
            "source_cell_xyxy": item["cell_box_xyxy"],
            "family": item["model_family_suggestion"],
            "candidate_id": None,
            "model_glb_sha256": None,
            "status": "SOURCE_ISOLATION_AND_RIGHTS_PENDING",
            "technical_pass": False,
            "golden_approved": False,
            "founder_review": "AWAITING_EXACT_MODEL",
            "source_image_exposed": False,
            "preview": None,
            "headings": [],
            "files": {},
        })
    fingerprint = hashlib.sha256((intake["collection_id"] + ":" +
                                  ",".join(r["source_reference_id"] for r in rooms)).encode()).hexdigest()
    return _make(out, rooms, source_kind="verified_founder_sheet_reference_metadata",
                 fingerprint=fingerprint)


def _artifact(root: Path, name: str, *, allowed_exts: tuple[str, ...]) -> Path:
    if not isinstance(name, str) or name.startswith("/") or "\\" in name:
        raise ValueError("invalid artifact path")
    relative = Path(name)
    if not relative.parts or any(part in ("..", ".") for part in relative.parts):
        raise ValueError("artifact path escaped batch root")
    candidate = root / relative
    if not candidate.is_file() or candidate.suffix.lower() not in allowed_exts:
        raise ValueError("missing or invalid candidate artifact")
    if not candidate.resolve().is_relative_to(root.resolve()):
        raise ValueError("artifact symlink escaped batch root")
    return candidate


def import_batch_rooms(*, report_path: Path, out: Path) -> dict:
    """Copy only verified locally built outputs into segregated review rooms.

    Import is fail-closed and atomic with respect to creating the destination:
    all source reports and artifact checks complete before writing anything.
    """
    report_bytes = report_path.read_bytes()
    report = json.loads(report_bytes)
    if report.get("schema") != "last-light.recipe-architect-batch.v1":
        raise ValueError("unrecognized technical batch receipt")
    if report.get("founder_golden_approved") or report.get("canonical_admission"):
        raise ValueError("batch receipt attempts unauthorized promotion")
    candidates = report.get("candidates")
    if not isinstance(candidates, list) or not 1 <= len(candidates) <= MAX_ROOMS:
        raise ValueError("invalid number of batch candidates")
    source_root = report_path.parent.resolve()
    staged: list[tuple[dict, dict[str, Path]]] = []
    bytes_needed = 0
    for index, item in enumerate(candidates, start=1):
        if item.get("golden_approved") or item.get("founder_review") != "NOT_GOLDEN":
            raise ValueError("only not-Golden candidates can be imported")
        source_ref = item.get("source_reference_id")
        candidate_id = item.get("candidate_id")
        if not isinstance(source_ref, str) or not isinstance(candidate_id, str):
            raise ValueError("missing candidate provenance")
        room_id = "mesh_" + hashlib.sha256((source_ref + "\0" + candidate_id).encode()).hexdigest()[:16]
        is_built = item.get("state") == "TECHNICAL_PASS_VISUAL_PENDING"
        files = {}
        if is_built:
            assets = item.get("artifacts", {})
            for key, ext in {"glb": (".glb",), "blend": (".blend",),
                             "contact_sheet": (".png",), "inventory": (".png",),
                             "atlas": (".png",), "log": (".log",)}.items():
                files[key] = _artifact(source_root, assets.get(key), allowed_exts=ext)
            if sha256(files["glb"]) != item.get("glb_sha256"):
                raise ValueError("GLB does not match technical receipt")
            inspect_glb(files["glb"])
            if sha256(files["blend"]) != item.get("blend_sha256"):
                raise ValueError("Blender master does not match technical receipt")
            heading_dir = files["glb"].parent
            for heading in range(16):
                files[f"heading_{heading:02d}"] = _artifact(
                    source_root, str((heading_dir / f"heading_{heading:02d}.png").relative_to(source_root)),
                    allowed_exts=(".png",))
            if item.get("distinct_headings") != 16 or item.get("meshes", 0) < 3:
                raise ValueError("batch technical pass lacks verified multi-view geometry")
            for key in ("inventory", "contact_sheet", "atlas", *(f"heading_{n:02d}" for n in range(16))):
                with Image.open(files[key]) as frame:
                    if frame.format != "PNG" or frame.width < 16 or frame.height < 16:
                        raise ValueError("invalid directional image")
                    if key == "inventory" and frame.size != (64, 64):
                        raise ValueError("inventory frame must be native 64x64")
                    frame.verify()
        bytes_needed += sum(path.stat().st_size for path in files.values())
        staged.append(({"room_id": room_id, "ordinal": index,
                        "title": item.get("preset", "Unlabelled candidate").replace("_", " ").title(),
                        "title_status": "TECHNICAL_PRESET_LABEL",
                        "source_reference_id": source_ref, "source_sha256": item.get("source_sha256"),
                        "reference_position_not_canonical_id": None,
                        "family": item.get("asset_family"), "candidate_id": candidate_id,
                        "model_glb_sha256": item.get("glb_sha256") if is_built else None,
                        "status": item.get("state"), "technical_pass": is_built,
                        "golden_approved": False, "founder_review": "EXACT_MODEL_REVIEW_REQUIRED",
                        "reference_vs_render_measured_this_run": report.get("reference_vs_render_comparison_this_run") is True,
                        "source_image_exposed": False,
                        "mesh_objects": item.get("meshes") if is_built else None,
                        "triangles_estimate": item.get("triangles_estimate") if is_built else None}, files))
    if bytes_needed > MAX_IMPORT_BYTES:
        raise ValueError("workspace asset copy exceeds bounded byte budget")
    # Disallow nonempty output before side effects and duplicate room identities.
    if len({room["room_id"] for room, _ in staged}) != len(staged):
        raise ValueError("duplicate candidates in source batch")
    fresh_output(out)
    rooms = []
    for room, files in staged:
        identifier = room["room_id"]
        destination = out / "rooms" / identifier
        destination.mkdir(parents=True, exist_ok=True)
        mapped = {}
        for key, source in files.items():
            dest_name = key + source.suffix
            shutil.copy2(source, destination / dest_name)
            mapped[key] = f"rooms/{identifier}/{dest_name}"
        room["files"] = mapped
        room["preview"] = mapped.get("inventory")
        room["headings"] = [mapped[f"heading_{n:02d}"] for n in range(16)] if files else []
        rooms.append(room)
    return _make_manifest_for_existing(out, rooms, hashlib.sha256(report_bytes).hexdigest())


def _make_manifest_for_existing(out: Path, rooms: list[dict], fingerprint: str) -> dict:
    # Import has already copied outputs and therefore cannot call _make().
    for room in rooms:
        dump(out / "rooms" / room["room_id"] / "room.json", room)
    result = {
        "schema": SCHEMA, "kind": "verified_cpu_batch_outputs",
        "source_fingerprint_sha256": fingerprint,
        "room_count": len(rooms), "capacity": MAX_ROOMS,
        "production_build_cap_unchanged": 3,
        "source_pixels_publicly_embedded": False,
        "automated_vision_inference_completed": False,
        "automated_golden_approval": False,
        "founder_approval_requires_exact_artifact_review": True,
        "rooms": rooms,
    }
    dump(out / "manifest.json", result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Local isolated mesh review dashboard source")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--reference-start", type=int)
    group.add_argument("--batch-report", type=Path)
    parser.add_argument("--count", type=int, default=40, choices=(10, 20, 40, 100))
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.batch_report:
        report = import_batch_rooms(report_path=args.batch_report, out=args.out)
    else:
        report = plan_reference_rooms(start=args.reference_start, count=args.count, out=args.out)
    print("LL_MESH_WORKSPACE", json.dumps({"rooms": report["room_count"],
        "kind": report["kind"], "golden": False, "production_build_cap": 3}))


if __name__ == "__main__":
    main()
