#!/usr/bin/env python3
"""A00 R03 dispatch gate: fail closed on invented masters, rights or release claims."""
import argparse
import json
import re
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
REQUIRED_FIELDS = (
    "work_order_id","master_id","queue","priority","notion_url",
    "source_reference_ids_raw","source_page_url","source_image_link_research_only",
    "source_page_status","source_rights","existing_geometry_id",
    "geometry_source_manifest_sha256","geometry_source_bounds_m",
    "dispatch_permission","quality_focus","cross_family_dependencies"
)
FALSE_GATES = ("source_pixel_comparison_verified","geometry_image_comparison_verified",
               "rights_reviewed","founder_visual_approved",
               "technical_qa_passed","godot_tested","iphone_verified",
               "canonical_new_id_created")

def validate(queue_path: Path, geometry_path: Path | None = None):
    payload=json.loads(queue_path.read_text(encoding="utf-8"))
    assert payload["schema"]=="A00_PRODUCTION_ADMISSION_R03_V1"
    assert payload["source_index_count"]==21025
    assert payload["source_r02_count"]==6072
    assert payload["geometry_source_count"]==360
    assert payload["already_verified_a00_masters_at_review"]==22
    assert payload["no_merge_no_deploy"] is True
    orders=payload["work_orders"]
    assert len(orders)==payload["dispatch_total"]==15
    assert len({x["master_id"] for x in orders})==15
    assert len({x["work_order_id"] for x in orders})==15
    assert Counter(x["queue"] for x in orders)=={"F01":3,"F09":12}
    matrix=payload["queue_matrix"]
    assert len(matrix)==12 and {x["queue"] for x in matrix}=={f"F{i:02d}" for i in range(1,13)}
    for entry in orders:
        for key in REQUIRED_FIELDS:
            assert entry.get(key), (entry.get("master_id"),key)
        assert entry["queue"] in ("F01","F09")
        assert entry["priority"] in ("P0","P1")
        assert entry["existing_geometry_id"]==entry["master_id"]
        assert entry["notion_semantic_verification"]=="Canonical Verified"
        assert entry["dispatch_permission"]=="ORIGINAL_REFINEMENT_AND_TECHNICAL_SOURCE_QA_ONLY"
        assert entry["machine_worker_start_allowed"] is True
        assert entry["source_rights"]=="THE_INDIE_STONE_COPYRIGHT__RESEARCH_ONLY__NO_DIRECT_REUSE"
        assert entry["source_page_url"].startswith("https://pzwiki.net/wiki/File:")
        assert entry["source_image_link_research_only"].startswith("https://pzwiki.net/w/images/")
        assert entry["source_page_status"].startswith("HTTP_200_")
        assert entry["notion_url"].startswith("https://app.notion.com/p/")
        assert re.fullmatch(r"[0-9a-f]{64}",entry["geometry_source_manifest_sha256"])
        assert len(entry["geometry_source_bounds_m"])==3
        assert all(isinstance(v,(int,float)) and 0<v<10 for v in entry["geometry_source_bounds_m"])
        for key in FALSE_GATES:
            assert entry[key] is False, (entry["master_id"],key)
        assert len(entry["validation_before_release"])>=5
    for family in matrix:
        expected={x["master_id"] for x in orders if x["queue"]==family["queue"]}
        assert set(family["dispatched_master_ids"])==expected
        assert family["dispatch_count"]==len(expected)
    handoff=queue_path.parent/"f01_f12_family_handoff.jsonl"
    if handoff.exists():
        lines=[json.loads(x) for x in handoff.read_text(encoding="utf-8").splitlines() if x.strip()]
        assert len(lines)==12 and {r["family"] for r in lines}=={f"F{i:02d}" for i in range(1,13)}
        assert all(x["release_authorized"] is False and x["may_invent_canonical_ids"] is False for x in lines)
    if geometry_path:
        manifest=json.loads(geometry_path.read_text(encoding="utf-8"))
        assert manifest["generated_3d_source_count"]==360
        indexed={x["asset_id"]:x for x in manifest["items"]}
        assert len(indexed)==360
        for x in orders:
            g=indexed[x["master_id"]]
            assert g["glb_sha256"]==x["geometry_source_manifest_sha256"]
            assert g["actual_bounds_m"]==x["geometry_source_bounds_m"]
    return orders

if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--queue",type=Path,default=HERE/"admitted_refinement_queue.json")
    parser.add_argument("--geometry-manifest",type=Path)
    args=parser.parse_args()
    orders=validate(args.queue,args.geometry_manifest)
    print("PASS: {} original-refinement work orders, 12-family routing, no rights or Golden approvals".format(len(orders)))
