"""Bounded R03 Notion->existing Blender geometry production pilot.

No broad source discovery, third-party image fetch, or implicit Golden approval.
The full A00 catalog remains research evidence; only explicitly admitted original
refinement work orders may enter the render/atlas review lane.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
import zipfile
from pathlib import Path

from tools.foundry_mass.queue import read_catalog
from tools.foundry_notion.catalog import validate as validate_snapshot

ADMISSION_SCHEMA = "A00_PRODUCTION_ADMISSION_R03_V1"
ADMISSION_SHA256 = "04845071b8a2f5509ad953cef8701249bca13f61a8b1731016de50ee6145574a"
ID = re.compile(r"ll_[a-z0-9_]{2,90}\Z")
ALLOWED_WORKERS = {"F01", "F09"}


def _sha(contents: bytes) -> str:
    return hashlib.sha256(contents).hexdigest()


def _canonical(doc: dict) -> bytes:
    return json.dumps(doc, sort_keys=True, separators=(",", ":")).encode()


def validate_admission(snapshot: dict, admission: dict) -> list[dict]:
    validate_snapshot(snapshot)
    if (admission.get("schema") != ADMISSION_SCHEMA
            or admission.get("dispatch_total") != 15
            or admission.get("source_index_count") != 21025
            or admission.get("approve_only") != "Start original-asset geometry/material/refinement with explicit art QA gates. Not Golden or game-ready."):
        raise ValueError("Untrusted R03 admission contract")
    orders = admission.get("work_orders")
    if not isinstance(orders, list) or len(orders) != 15:
        raise ValueError("R03 work-order count changed")
    ids = [o.get("master_id") for o in orders]
    if (len(set(ids)) != 15 or any(not isinstance(i, str) or not ID.fullmatch(i) for i in ids)):
        raise ValueError("Duplicate or invalid admitted model ID")
    masters = {m["content_id"]: m for m in snapshot["production_masters"]}
    for order in orders:
        ident = order["master_id"]
        master = masters.get(ident)
        if (not master or master.get("semantic_verification") != "Canonical Verified"
                or master.get("queue") != order.get("queue")
                or master.get("queue") not in ALLOWED_WORKERS
                or not master.get("work_order")
                or order.get("notion_semantic_verification") != "Canonical Verified"
                or order.get("existing_geometry_id") != ident
                or order.get("dispatch_permission") != "ORIGINAL_REFINEMENT_AND_TECHNICAL_SOURCE_QA_ONLY"
                or order.get("machine_worker_start_allowed") is not True
                or order.get("source_pixel_comparison_verified") is not False
                or order.get("geometry_image_comparison_verified") is not False
                or order.get("source_rights") != "THE_INDIE_STONE_COPYRIGHT__RESEARCH_ONLY__NO_DIRECT_REUSE"
                or any(order.get(k) is not False for k in (
                    "rights_reviewed", "founder_visual_approved", "technical_qa_passed",
                    "godot_tested", "iphone_verified", "canonical_new_id_created"))
                or any(master.get(k) is not False for k in (
                    "founder_visual_approved", "technical_qa_passed", "godot_tested", "iphone_verified"))):
            raise ValueError(f"Unverified or wrongly authorized master: {ident}")
        digest = order.get("geometry_source_manifest_sha256")
        if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise ValueError(f"Missing immutable geometry fingerprint: {ident}")
        if not isinstance(order.get("work_order_id"), str) or ident not in order["work_order_id"]:
            raise ValueError(f"Missing attributable work-order ID: {ident}")
    return sorted(orders, key=lambda x: (x["priority"], x["queue"], x["work_order_id"]))


def _validated_state(state: dict | None, order_ids: list[str], fingerprint: str) -> list[str]:
    if state is None:
        return []
    if (state.get("schema_version") != 1
            or state.get("source_plan_sha256") != fingerprint
            or state.get("golden_approved") is not False
            or not isinstance(state.get("completed"), list)):
        raise ValueError("Incompatible or unsafe production cursor")
    done = state["completed"]
    if len(done) != len(set(done)) or not set(done).issubset(order_ids):
        raise ValueError("Unknown/duplicate completed IDs")
    return done


def plan(snapshot: dict, admission: dict, archive: Path, output: Path,
         state: dict | None = None, batch_size: int = 1,
         asset_id: str | None = None) -> dict:
    if not isinstance(batch_size, int) or not 1 <= batch_size <= 2:
        raise ValueError("Pilot budget: 1 or 2 existing geometry sources")
    orders = validate_admission(snapshot, admission)
    if asset_id is not None and asset_id not in {o["master_id"] for o in orders}:
        raise ValueError("Requested asset is not in the verified R03 admission")
    with zipfile.ZipFile(archive) as source:
        geometry = read_catalog(source)
        archived = {row["asset_id"]: row for row in geometry["items"]}
        expected = [o["master_id"] for o in orders]
        if not set(expected).issubset(archived):
            raise ValueError("Admitted geometry missing from real source archive")
        fingerprint = _sha(_canonical({
            "snapshot": _sha(_canonical(snapshot)),
            "admission": _sha(_canonical(admission)),
            "archive": geometry["source_plan_sha256"],
        }))
        completed = _validated_state(state, expected, fingerprint)
        available = [o for o in orders if o["master_id"] not in completed]
        if asset_id is not None:
            available = [o for o in available if o["master_id"] == asset_id]
        chosen = available[:batch_size]
        selected = []
        for order in chosen:
            ident = order["master_id"]
            manifest_name = f"{ident}/geometry_manifest.json"
            glb_name = f"{ident}/model.glb"
            blend_name = f"{ident}/model.blend"
            if any(name not in source.namelist() for name in (manifest_name, glb_name, blend_name)):
                raise ValueError(f"Incomplete editable geometry source: {ident}")
            # R03's historic field is named geometry_source_manifest_sha256,
            # but its value is the original GLB SHA-256, as verified against
            # the preserved geometry reconstruction batch report. Compare the
            # actual source bytes; never weaken or ignore the R03 fingerprint.
            if archived[ident]["glb_sha256"] != order["geometry_source_manifest_sha256"]:
                raise ValueError(f"R03/source GLB fingerprint drift: {ident}")
            source_manifest = json.loads(source.read(manifest_name))
            if not isinstance(source_manifest, dict):
                raise ValueError(f"Invalid source geometry manifest: {ident}")
            info = source.getinfo(glb_name)
            if not 20 <= info.file_size <= 10 * 1024 * 1024:
                raise ValueError(f"Unsafe GLB size: {ident}")
            binary = source.read(info)
            if (_sha(binary) != archived[ident]["glb_sha256"]
                    or binary[:4] != b"glTF"
                    or struct.unpack_from("<I", binary, 8)[0] != len(binary)):
                raise ValueError(f"Bad original source GLB: {ident}")
            path = output / "models" / ident / "model.glb"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(binary)
            selected.append({
                "asset_id": ident, "glb_path": str(path.resolve()),
                "glb_sha256": archived[ident]["glb_sha256"],
                "original_blend_size_bytes": source.getinfo(blend_name).file_size,
                "work_order_id": order["work_order_id"],
                "notion_url": order["notion_url"], "queue": order["queue"],
                "quality_focus": order["quality_focus"],
                "expected_geometry_bounds_m": order["geometry_source_bounds_m"],
                "source_rights": "RESEARCH_ONLY__NO_DIRECT_REUSE",
                "source_image_copy_allowed": False,
                "golden_approved": False, "candidate_only": True,
            })
    doc = {
        "schema_version": 1, "status": "READY" if selected else "COMPLETE",
        "source_plan_sha256": fingerprint, "source_count": len(orders),
        "completed_before": completed, "selected": selected,
        "remaining_before": len(orders) - len(completed),
        "notion_snapshot_date": snapshot["snapshot_date"],
        "admission_schema": ADMISSION_SCHEMA,
        "f11_material_approved": False, "f12_world_scale_approved": False,
        "golden_approved": False, "gameplay_integrated": False,
    }
    output.mkdir(parents=True, exist_ok=True)
    (output / "plan.json").write_text(json.dumps(doc, indent=2) + "\n")
    return doc


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--snapshot", type=Path, required=True)
    p.add_argument("--admission", type=Path, required=True)
    p.add_argument("--archive", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--state", type=Path)
    p.add_argument("--asset-id")
    p.add_argument("--batch-size", type=int, default=1)
    a = p.parse_args()
    admission_bytes = a.admission.read_bytes()
    if _sha(admission_bytes) != ADMISSION_SHA256:
        raise ValueError("R03 admission source digest changed; review required")
    report = plan(json.loads(a.snapshot.read_text()), json.loads(admission_bytes),
                  a.archive, a.output,
                  json.loads(a.state.read_text()) if a.state else None,
                  a.batch_size, a.asset_id)
    print("FOUNDRY_CONTROLLED_PLAN", len(report["selected"]), report["remaining_before"])


if __name__ == "__main__":
    main()
