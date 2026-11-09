"""Fail-closed A00 Notion asset master snapshot -> F01–F12 recipe work orders.

No network, Notion credentials, third-party image imports or approvals are required.
The snapshot is a machine-readable *candidate-authoring* contract, not a release.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

SCHEMA=2
WORKERS={f"F{i:02d}" for i in range(1,13)}
PRIORITIES={"P0":0,"P1":1,"P2":2,"P3":3}
STAGES={"Backlog","Original Design","Generating","QA Review","Approved","Blocked"}
GATES={"HOLD","SPEC_READY_RECIPE_ONLY"}
ID=re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{1,127}\Z")


def validate(doc: dict) -> None:
    if doc.get("schema_version")!=SCHEMA or doc.get("status")!="NOTION_READ_ONLY_EXPORT_RECIPE_ONLY_NO_GOLDEN":
        raise ValueError("Incorrect snapshot contract")
    if doc.get("source_reference_count")!=21025 or doc.get("legacy_3d_sources")!=360:
        raise ValueError("Missing research or 360-model lineage")
    masters=doc.get("masters")
    if not isinstance(masters,list) or len(masters)!=doc.get("canonical_rows"):
        raise ValueError("Missing canonical records")
    ids=[r.get("content_id") for r in masters]
    if len(ids)!=len(set(ids)) or any(not isinstance(i,str) or not ID.fullmatch(i) for i in ids):
        raise ValueError("Invalid or duplicated master ID")
    for r in masters:
        if r.get("automation_gate") not in GATES or r.get("stage") not in STAGES or r.get("priority") not in PRIORITIES:
            raise ValueError(f"Invalid state for {r['content_id']}")
        if r.get("queue") is not None and r["queue"] not in WORKERS:
            raise ValueError(f"Invalid family worker for {r['content_id']}")
        flags=r.get("provenance_flags")
        expected={"rights_reviewed","founder_visual_approved","technical_qa_passed","godot_tested","iphone_verified"}
        if not isinstance(flags,dict) or set(flags)!=expected or any(type(v)is not bool for v in flags.values()):
            raise ValueError("Invalid QA provenance flags")
        if r.get("automation_gate")=="SPEC_READY_RECIPE_ONLY":
            core=r.get("spec_fields_present",{})
            if (r.get("semantic_verification")!="Canonical Verified" or not r.get("queue")
                    or not r.get("work_order") or r.get("contract_version")!="A00_ASSET_CONTRACT_V2"
                    or r.get("stage")=="Blocked" or not all(core.get(k) is True for k in ("geometry","materials","gameplay","render"))):
                raise ValueError(f"Unsafe recipe gate: {r['content_id']}")
        if r.get("notion_page","").startswith("https://app.notion.com/") is False:
            raise ValueError("Missing canonical Notion provenance")


def plan(doc: dict, completed: list[str] | None=None, batch_size: int=4) -> dict:
    validate(doc)
    if type(batch_size) is not int or not 1<=batch_size<=10:
        raise ValueError("Only 1–10 bounded recipe work orders")
    done=completed or []
    known={r["content_id"] for r in doc["masters"]}
    if len(done)!=len(set(done)) or not set(done).issubset(known):
        raise ValueError("Invalid completion cursor")
    ready=[r for r in doc["masters"] if r["automation_gate"]=="SPEC_READY_RECIPE_ONLY"
           and r["content_id"] not in done]
    ready.sort(key=lambda r:(PRIORITIES[r["priority"]],r["work_order"],r["content_id"]))
    payload=json.dumps(doc,sort_keys=True,separators=(',',':')).encode()
    orders=[{
        "content_id":r["content_id"],"canonical_notion_url":r["notion_page"],
        "worker":r["queue"],"work_order":r["work_order"],"priority":r["priority"],
        "mode":"ORIGINAL_RECIPE_AUTHORING_ONLY","requires_existing_geometry_check":True,
        "requires_live_notionspec_or_approved_K00_mirror":True,
        "reference_image_copy_allowed":False,"automatic_golden_approval":False,
        "automatic_merge_or_deploy":False,"requires_f11_f12_godot_qa":True,
    } for r in ready[:batch_size]]
    return {"schema_version":2,"snapshot_sha256":hashlib.sha256(payload).hexdigest(),
            "source_status":doc["status"],"orders":orders,"remaining_ready":len(ready)-len(orders),
            "held_masters":sum(r["automation_gate"]=="HOLD" for r in doc["masters"]),
            "total_canonical_rows":len(doc["masters"]),"golden_approval":False,
            "release_authorized":False}


def main() -> None:
    p=argparse.ArgumentParser()
    p.add_argument("--catalog",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--completed",type=Path)
    p.add_argument("--batch-size",type=int,default=4)
    a=p.parse_args()
    completed=json.loads(a.completed.read_text()) if a.completed else []
    result=plan(json.loads(a.catalog.read_text()),completed,a.batch_size)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,indent=2)+'\n')
    print(f"A00_V2_PLAN ready={len(result['orders'])} remaining={result['remaining_ready']} held={result['held_masters']}")


if __name__=="__main__":
    main()
