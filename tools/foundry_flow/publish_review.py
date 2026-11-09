"""Immutably stage technical review packages outside the playable game branch.

Publishing never sets Golden approval and never copies the 360 source archive,
copyrighted research images or a 3D source into the runtime content tree.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
from pathlib import Path


IDENT = re.compile(r"ll_[a-z0-9_]{2,90}\Z")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stage(source: Path, destination: Path) -> dict:
    packet = json.loads((source / "review" / "approval_packet.json").read_text())
    atlas = json.loads((source / "sheets" / "sprite_sheet_manifest.json").read_text())
    godot = json.loads((source / "godot_report.json").read_text())
    if (packet.get("status") != "TECHNICAL_QA_PASSED_AWAITING_FOUNDER_VISUAL_REVIEW"
            or packet.get("technical_qa_passed") is not True
            or packet.get("godot_import_verified") is not True
            or any(packet.get(flag) is not False for flag in (
                "founder_visual_approved", "iphone_verified", "golden_approved",
                "gameplay_integrated", "f11_material_approved", "f12_world_scale_approved"))
            or atlas.get("status") != "TECHNICAL_SPRITE_SHEET_CANDIDATE"
            or atlas.get("golden_approved") is not False
            or godot.get("result") != "GODOT_ATLAS_IMPORT_PASS"):
        raise ValueError("Only independently verified non-Golden review candidates can publish")
    objects = packet.get("objects", [])
    if len(objects) != 1 or not IDENT.fullmatch(objects[0].get("asset_id", "")):
        raise ValueError("Review publishing is limited to one admitted model")
    ident = objects[0]["asset_id"]
    model_hash = objects[0].get("geometry_sha256")
    if not isinstance(model_hash, str) or not re.fullmatch(r"[0-9a-f]{64}", model_hash):
        raise ValueError("Review has no attributable geometry hash")
    pages = atlas.get("pages", [])
    if not 1 <= len(pages) <= 8 or len(atlas.get("frames", [])) != 16:
        raise ValueError("Review atlas incomplete")
    paths = {
        "approval_packet.json": source / "review" / "approval_packet.json",
        "founder_contact_sheet.png": source / "review" / "founder_contact_sheet.png",
        "sprite_sheet_manifest.json": source / "sheets" / "sprite_sheet_manifest.json",
        "godot_report.json": source / "godot_report.json",
        "blender_audit.json": source / "blender_audit.json",
    }
    for i, page in enumerate(pages):
        name = f"sheet_{i:04d}.png"
        if page.get("file") != name or digest(source / "sheets" / name) != page.get("sha256"):
            raise ValueError("Atlas page was modified after quality assurance")
        paths[name] = source / "sheets" / name
    if sum(path.stat().st_size for path in paths.values()) > 20 * 1024 * 1024:
        raise ValueError("Review package exceeds 20MB quota")
    fingerprints = {name: digest(path) for name, path in paths.items()}
    target = destination / "foundry_controlled_review" / ident / model_hash[:16]
    manifest = {"schema_version": 1, "asset_id": ident,
                "source_glb_sha256": model_hash, "files": fingerprints,
                "status": "TECHNICAL_REVIEW_IMMUTABLE_NOT_GOLDEN",
                "founder_visual_approved": False, "iphone_verified": False,
                "gameplay_integrated": False, "golden_approved": False}
    if target.exists():
        previous = json.loads((target / "review_package.json").read_text())
        if previous != manifest or any(digest(target / name) != fingerprint
                                       for name, fingerprint in fingerprints.items()):
            raise ValueError("Immutable review package content collision")
        return manifest
    target.mkdir(parents=True)
    for name, path in paths.items():
        shutil.copyfile(path, target / name)
    (target / "review_package.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--destination", type=Path, required=True)
    a = p.parse_args()
    result = stage(a.source, a.destination)
    print("FOUNDRY_REVIEW_STAGED", result["asset_id"], result["status"])


if __name__ == "__main__":
    main()
