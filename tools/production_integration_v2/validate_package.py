#!/usr/bin/env python3
"""LAST LIGHT V2 shared-package and mass-production gate, stdlib only.

This validates provenance/metadata, hashes and records in an external approval
ledger. Ledger trust requires GitHub branch protection and authorized review:
this script DOES NOT authenticate who edited the ledger or prove Notion rights.
No Blender run, deployment, merge, data write or automation is triggered here.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

FAMILIES = {f"F{i:02d}" for i in range(1, 11)}
STAGES = ("CALIBRATION", "GOLDEN_CANDIDATE", "APPROVED_TEMPLATE",
          "PILOT_5", "PILOT_20", "MASS_100")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
GIT_SHA = re.compile(r"^[0-9a-f]{40}$")
DIRECTIONS = {1, 2, 4, 8, 16}


class GateError(ValueError):
    pass


def require(ok, message):
    if not ok:
        raise GateError(message)


def is_sha(s):
    return isinstance(s, str) and bool(SHA256.fullmatch(s))


def is_git_sha(s):
    return isinstance(s, str) and bool(GIT_SHA.fullmatch(s))


def nonempty(s):
    return isinstance(s, str) and bool(s.strip())


def filehash(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def validate_package(p, package_path):
    require(isinstance(p, dict) and p.get("schema_version") == 2, "schema_version must be 2")
    require(nonempty(p.get("package_id")), "package_id required")
    family = p.get("family")
    require(family in FAMILIES, "family must be F01-F10, not F11/F12")
    stage = p.get("stage")
    require(stage in STAGES, "invalid stage")
    assert_list = p.get("artifacts")
    require(isinstance(assert_list, list), "artifacts array required")
    for item in assert_list:
        require(isinstance(item, dict), "artifact must be an object")
        require(item.get("kind") in ("sprite", "atlas", "metadata", "source", "texture", "animation"),
                "invalid artifact kind")
        require(is_sha(item.get("sha256")), "artifact sha256 missing/invalid")
        loc = item.get("uri")
        require(nonempty(loc), "artifact URI missing")
        # Avoid insecure shell/file traversal; remote binary verification is separate.
        require(not loc.startswith("file://") and ".." not in loc, "unsafe artifact URI")
        if loc.startswith("./"):
            rel = Path(loc[2:])
            require(not rel.is_absolute(), "absolute local path not allowed")
            local = (package_path.parent / rel).resolve()
            require(local.is_relative_to(package_path.parent.resolve()), "local traversal")
            require(local.is_file(), "local artifact missing")
            require(filehash(local) == item["sha256"], "local artifact hash mismatch")
    renderer = p.get("renderer")
    require(isinstance(renderer, dict), "renderer required")
    require(is_git_sha(renderer.get("commit")), "F12 renderer commit must be pinned")
    require(nonempty(renderer.get("profile")), "F12 profile missing")
    require(renderer.get("directions") in DIRECTIONS, "invalid renderer directions")
    require(renderer.get("logical_tile_px") == [80, 40], "Godot tile must be [80,40]")
    source = p.get("source")
    require(isinstance(source, dict) and is_sha(source.get("sha256")), "original source sha256 missing")
    require(nonempty(source.get("archive_uri")), "durable source archive pointer missing")
    require(is_git_sha(source.get("builder_commit")), "source builder commit not pinned")
    require(isinstance(p.get("material_recipe_ids"), list), "material_recipe_ids list required")
    require(len(set(p["material_recipe_ids"])) == len(p["material_recipe_ids"]),
            "duplicate material recipe IDs")
    if stage != "CALIBRATION":
        require(nonempty(p.get("canonical_master_id")), "A00 canonical ID required")
        require(p["canonical_master_id"].startswith("ll_") or p["canonical_master_id"].startswith("animal."),
                "canonical ID shape not recognized (does not prove A00 validity)")
        require(nonempty(p.get("a00_notion_url"))
                and p["a00_notion_url"].startswith("https://"), "A00 Notion record required")
        require(is_git_sha(p.get("a00_snapshot_commit")), "A00 snapshot git commit required")
        require(is_sha(p.get("a00_snapshot_record_sha256")), "A00 record SHA required")
        require(p.get("rights_status") == "CLEARED", "rights not cleared")
    else:
        require(not p.get("canonical_master_id"), "calibration cannot claim canonical ID")
    return stage


def _matching_approvals(p, package_digest, ledger):
    require(isinstance(ledger, dict) and ledger.get("schema_version") == 2, "invalid ledger schema")
    approvals = ledger.get("asset_approvals")
    require(isinstance(approvals, list), "ledger asset_approvals must be a list")
    needed = {"W09_TECHNICAL", "FOUNDER_GOLDEN"}
    found = set()
    for a in approvals:
        if not isinstance(a, dict):
            continue
        if (a.get("package_id") == p["package_id"]
            and a.get("canonical_master_id") == p.get("canonical_master_id")
            and a.get("package_sha256") == package_digest
            and a.get("source_sha256") == p["source"]["sha256"]
            and a.get("renderer_commit") == p["renderer"]["commit"]):
            require(a.get("decision") == "APPROVED", "matching explicit rejection or revocation")
            require(nonempty(a.get("reviewer")) and nonempty(a.get("review_url"))
                    and nonempty(a.get("reviewed_at")), "review evidence incomplete")
            found.add(a.get("role"))
    require(needed <= found, "missing exact-package W09 and founder Golden approvals")


def check_gate(p, manifest_path, ledger, target_stage, governance_protected=False):
    current = validate_package(p, manifest_path)
    require(target_stage in STAGES[2:], "target must be APPROVED_TEMPLATE or pilot stage")
    require(governance_protected, "branch protection and authorized review not attested")
    require(STAGES.index(current) >= STAGES.index(target_stage),
            "package stage does not reach requested target")
    digest = filehash(manifest_path)
    _matching_approvals(p, digest, ledger)
    families = ledger.get("family_authorizations")
    require(isinstance(families, list), "ledger family_authorizations must be a list")
    matches = [f for f in families if isinstance(f, dict)
               and f.get("family") == p["family"] and f.get("decision") == "AUTHORIZED"
               and f.get("scope") == target_stage and f.get("package_sha256") == digest
               and nonempty(f.get("founder_review_url")) and nonempty(f.get("reviewed_at"))]
    require(len(matches) > 0, "missing exact-stage founder family authorization")
    if target_stage in ("PILOT_5", "PILOT_20", "MASS_100"):
        expected = {"PILOT_5": 5, "PILOT_20": 20, "MASS_100": 100}[target_stage]
        batch = p.get("batch")
        require(isinstance(batch, dict) and batch.get("target_count") == expected,
                "batch target_count mismatch")
        approved = batch.get("distinct_approved_master_ids")
        require(isinstance(approved, list) and len(approved) >= expected,
                "insufficient distinct approved master IDs in approved batch")
        require(len(approved) == len(set(approved)), "duplicate approved master IDs")
        require(nonempty(batch.get("qa_evidence_url")), "batch QA evidence required")
    return {"status": "GATE_ELIGIBLE_METADATA_ONLY", "stage": target_stage,
            "package_id": p["package_id"], "manifest_sha256": digest,
            "warnings": ["Ledger reviewers not cryptographically authenticated",
                         "GitHub branch protection must be independently enforced",
                         "External A00/rights and Golden evidence require human verification",
                         "No deployment or merge has occurred"]}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--ledger", type=Path)
    parser.add_argument("--target-stage", choices=STAGES[2:])
    parser.add_argument("--protected-governance", action="store_true",
                        help="Manual attestation only; does not itself prove GitHub protection")
    args = parser.parse_args()
    try:
        p = json.loads(args.manifest.read_text())
        stage = validate_package(p, args.manifest.resolve())
        if args.target_stage:
            require(args.ledger is not None, "--ledger required for promotion")
            ledger = json.loads(args.ledger.read_text())
            result = check_gate(p, args.manifest.resolve(), ledger,
                                args.target_stage, args.protected_governance)
        else:
            result = {"status": "VALID_CANDIDATE_NOT_APPROVED", "stage": stage,
                      "package_id": p["package_id"]}
        print(json.dumps(result, sort_keys=True))
        return 0
    except (GateError, OSError, ValueError, json.JSONDecodeError) as e:
        print(json.dumps({"status": "REJECTED", "reason": str(e)}))
        return 1


if __name__ == "__main__":
    sys.exit(main())
