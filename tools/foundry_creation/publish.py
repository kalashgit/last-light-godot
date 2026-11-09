"""Commit release-backed progress only after source ZIP was accepted into draft GitHub Release."""
from __future__ import annotations
import argparse
import hashlib
import json
import re
from pathlib import Path

def stage(plan: dict, manifest: dict, destination: Path, release_tag: str) -> dict:
    if plan.get("generator_kind")!="DETERMINISTIC_BLENDER_PROCEDURAL_SOURCE":
        raise ValueError("Wrong generated asset class")
    if manifest.get("golden_approved") is not False or manifest.get("canonical_promoted") is not False:
        raise ValueError("Cannot promote unapproved sources")
    if manifest.get("catalog_sha256")!=plan.get("catalog_sha256") or manifest.get("total")!=plan.get("total"):
        raise ValueError("Catalog hash mismatch")
    if not re.fullmatch(r"foundry-created-[0-9]{1,18}",release_tag):
        raise ValueError("Release tag must be tied to immutable GitHub run id")
    new=[asset["asset_id"] for asset in plan["selected"]]
    if not 1 <= len(new) <= 4 or new != [x["asset_id"] for x in manifest["batch"]]:
        raise ValueError("Invalid new model IDs")
    state_path=destination/"foundry_creation/state.json"
    prior=json.loads(state_path.read_text()) if state_path.exists() else {
        "schema_version":1,"catalog_sha256":plan["catalog_sha256"],
        "total":plan["total"],"completed":[]}
    if (prior.get("schema_version")!=1 or prior.get("catalog_sha256")!=plan["catalog_sha256"]
        or prior.get("total")!=512 or prior.get("completed")!=plan["completed_before"]):
        raise ValueError("Stale, incompatible, or skipped progress cursor")
    if len(set(new)) != len(new) or any(x in prior["completed"] for x in new):
        raise ValueError("Repeated sources are not allowed")
    next_completed=prior["completed"]+new
    report={
        **manifest,
        "release_tag":release_tag,
        "release_archive":"foundry_new_sources.zip",
        "release_state":"DRAFT_DO_NOT_PUBLISH",
        "run_id":release_tag.split("-")[-1],
        "golden_approved":False,
    }
    next_state={
        "schema_version":1,"catalog_sha256":plan["catalog_sha256"],
        "total":512,"completed":next_completed,
        "remaining":512-len(next_completed),
        "last_approved_source_bundle_tag":release_tag,
        "golden_approved":False,
    }
    if not 0 <= next_state["remaining"] < 512:
        raise ValueError("Invalid completion cursor")
    dest=destination/"foundry_creation/reports"
    dest.mkdir(parents=True,exist_ok=True)
    (dest/f"{report['run_id']}.json").write_text(json.dumps(report,indent=2)+"\n")
    state_path.parent.mkdir(parents=True,exist_ok=True)
    state_path.write_text(json.dumps(next_state,indent=2)+"\n")
    print("FOUNDRY_CREATED_PROGRESS",len(new),len(next_completed),next_state["remaining"])
    return next_state

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--plan",type=Path,required=True)
    p.add_argument("--manifest",type=Path,required=True)
    p.add_argument("--destination",type=Path,required=True)
    p.add_argument("--release-tag",required=True)
    a=p.parse_args()
    stage(json.loads(a.plan.read_text()),json.loads(a.manifest.read_text()),a.destination,a.release_tag)

if __name__=="__main__":
    main()
