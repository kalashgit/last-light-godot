#!/usr/bin/env python3
"""A00 R04: fail-closed machine dispatch/receipt gate. No Golden or game approval."""
import argparse
import json
import re
from collections import Counter
from pathlib import Path

class GateError(ValueError): pass

def need(ok, why):
    if not ok: raise GateError(why)

COHORT = frozenset("""
ll_furniture_bookcase ll_furniture_mattress ll_furniture_refrigerator
ll_crafting_firewood ll_crafting_glass_pane ll_household_bucket
ll_household_match_box ll_crafting_screw_box ll_household_fire_extinguisher
ll_household_propane_bottle ll_medical_medical_gloves ll_medical_splint
ll_medical_tweezers ll_tools_hand_drill ll_tools_hand_saw
""".split())
BLOCKED = ("source_pixel_comparison_verified","geometry_image_comparison_verified",
           "rights_reviewed","founder_visual_approved","technical_qa_passed",
           "godot_tested","iphone_verified","canonical_new_id_created")
HEXSHA = re.compile(r"[0-9a-f]{64}\Z")

def read(path):
    try: return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as err: raise GateError(f"Cannot read {path}: {err}") from err

def check(queue, geometry, handoff):
    """All three files required. Never infer GLB approval from filename."""
    p, g = read(queue), read(geometry)
    need(p.get("schema")=="A00_PRODUCTION_ADMISSION_R03_V1", "Unrecognized dispatch schema")
    for key,val in (("source_index_count",21025),("source_r02_count",6072),
                    ("geometry_source_count",360),("already_verified_a00_masters_at_review",22),
                    ("dispatch_total",15),("no_merge_no_deploy",True)):
        need(p.get(key)==val, f"Dispatch snapshot changed: {key}")
    need(g.get("generated_3d_source_count")==360 and g.get("source_plan_unique_count")==360,"Incorrect 360-model source manifest")
    models=g.get("items")
    need(isinstance(models,list) and len(models)==360,"Wrong geometry array length")
    model_by_id={x["asset_id"]:x for x in models}
    need(len(model_by_id)==360,"Duplicate geometry identities")
    orders=p.get("work_orders")
    need(isinstance(orders,list) and len(orders)==15,"Wrong number of work orders")
    need({x["master_id"] for x in orders}==COHORT,"Invented/removed canonical asset ID")
    need(len({x["work_order_id"] for x in orders})==15,"Duplicate work order ID")
    need(Counter(x["queue"] for x in orders)=={"F01":3,"F09":12},"Family rerouting detected")
    seen_sources=set()
    for o in orders:
        name=o["master_id"]
        m=model_by_id.get(name)
        need(m is not None,f"{name}: no matching original 360 GLB")
        need(o.get("work_order_id")==f'A00-R03-{o["queue"]}-{name}-v1',f"{name}: forged work order")
        need(o.get("existing_geometry_id")==name,f"{name}: model identity mismatch")
        need(o.get("notion_semantic_verification")=="Canonical Verified",f"{name}: not in canonical registry")
        need(o.get("classification_admission")=="EXISTING_A00_CANONICAL_VERIFIED_ID",f"{name}: not admitted")
        need(o.get("priority") in ("P0","P1"),f"{name}: unsupported priority")
        need(o.get("dispatch_permission")=="ORIGINAL_REFINEMENT_AND_TECHNICAL_SOURCE_QA_ONLY",f"{name}: expanded permissions")
        need(o.get("machine_worker_start_allowed") is True,f"{name}: work not admitted")
        need(o.get("source_rights")=="THE_INDIE_STONE_COPYRIGHT__RESEARCH_ONLY__NO_DIRECT_REUSE",f"{name}: rights boundary changed")
        need(o.get("source_page_status")=="HTTP_200_TITLE_AND_FILE_METADATA_CHECKED_2026_11_09",f"{name}: source evidence status changed")
        need(isinstance(o.get("notion_url"),str) and re.fullmatch(r"https://app\.notion\.com/p/[0-9a-f]{32}",o["notion_url"]) is not None,f"{name}: invalid registry URL")
        need(isinstance(o.get("source_page_url"),str) and o["source_page_url"].startswith("https://pzwiki.net/wiki/File:"),f"{name}: invalid source link")
        need(isinstance(o.get("source_image_link_research_only"),str) and o["source_image_link_research_only"].startswith("https://pzwiki.net/w/images/"),f"{name}: invalid research link")
        need(isinstance(o.get("source_reference_ids_raw"),str) and o["source_reference_ids_raw"].strip(),f"{name}: missing source record IDs")
        sha=o.get("geometry_source_manifest_sha256")
        need(isinstance(sha,str) and HEXSHA.fullmatch(sha) is not None and sha==m["glb_sha256"],f"{name}: stale/replaced GLB hash")
        bounds=o.get("geometry_source_bounds_m")
        need(bounds==m["actual_bounds_m"] and isinstance(bounds,list) and len(bounds)==3 and all(type(x) in (int,float) and 0<x<10 for x in bounds),f"{name}: invalid geometry bounds")
        need(isinstance(o.get("quality_focus"),str) and len(o["quality_focus"])>40,f"{name}: missing quality contract")
        need(isinstance(o.get("cross_family_dependencies"),str) and o["cross_family_dependencies"].strip(),f"{name}: missing dependencies")
        need(isinstance(o.get("validation_before_release"),list) and len(o["validation_before_release"])>=7,f"{name}: missing release gates")
        for field in BLOCKED: need(o.get(field) is False,f"{name}: unauthorized approval {field}")
        seen_sources.add(o["source_page_url"])
    need(len(seen_sources)==15,"Source evidence reused across different masters")
    matrix=p.get("queue_matrix")
    need(isinstance(matrix,list) and len(matrix)==12 and {x["queue"] for x in matrix}=={f"F{i:02d}" for i in range(1,13)},"Family matrix incomplete")
    for row in matrix:
        expected=[o["master_id"] for o in orders if o["queue"]==row["queue"]]
        need(row.get("dispatched_master_ids")==expected and row.get("dispatch_count")==len(expected),f'{row["queue"]}: master mismatch')
    try: lines=[json.loads(x) for x in Path(handoff).read_text(encoding="utf-8").splitlines() if x.strip()]
    except (OSError, ValueError) as err: raise GateError(f"Unreadable handoff: {err}") from err
    need(len(lines)==12 and {x.get("family") for x in lines}=={f"F{i:02d}" for i in range(1,13)},"Invalid handoff families")
    for row in lines:
        fam=row["family"]
        expected=[o["master_id"] for o in orders if o["queue"]==fam]
        actual=[t.get("master_id") for t in row.get("tasks",[]) if t.get("task")=="ORIGINAL_GEOMETRY_AND_MATERIAL_REFINEMENT"]
        need(row.get("release_authorized") is False and row.get("may_invent_canonical_ids") is False,f"{fam}: elevated worker permissions")
        need(row.get("direct_master_count")==len(expected) and actual==expected,f"{fam}: unauthorized family work order")
    return {o["master_id"]:o for o in orders}

def receipts(path, orders):
    """A worker may submit only to independent QA, never approve its own work."""
    try: rows=[json.loads(s) for s in Path(path).read_text(encoding="utf-8").splitlines() if s.strip()]
    except (OSError,ValueError) as err: raise GateError(f"Unreadable receipts: {err}") from err
    need(bool(rows),"Empty receipts")
    need(len({x.get("master_id") for x in rows})==len(rows),"Duplicate worker receipt")
    for r in rows:
        name=r.get("master_id")
        need(name in orders,f"Unknown worker asset {name}")
        original=orders[name]
        need(r.get("schema")=="A00_WORKER_REFINEMENT_RECEIPT_V1",f"{name}: invalid receipt schema")
        need(r.get("work_order_id")==original["work_order_id"] and r.get("family")==original["queue"],f"{name}: misrouted receipt")
        need(r.get("input_glb_sha256")==original["geometry_source_manifest_sha256"],f"{name}: stale GLB input")
        sha=r.get("output_glb_sha256")
        need(isinstance(sha,str) and HEXSHA.fullmatch(sha) is not None and sha!=r["input_glb_sha256"],f"{name}: unchanged/missing output")
        need(r.get("status")=="SUBMITTED_FOR_INDEPENDENT_QA",f"{name}: invalid self-approval status")
        evidence=r.get("evidence")
        need(isinstance(evidence,dict),f"{name}: missing artifact evidence")
        for key in ("original_blend_path","original_glb_path","render_contact_sheet_path","material_report_path","scale_collision_report_path"):
            val=evidence.get(key)
            need(isinstance(val,str) and val.startswith("artifacts/") and ".." not in val.split("/"),f"{name}: missing/unsafe {key}")
        for key in ("rights_approval","golden_approval","technical_qa_passed","godot_tested","iphone_verified"):
            need(r.get(key) is False,f"{name}: worker self-approval {key}")
    return len(rows)

def main():
    a=argparse.ArgumentParser(description=__doc__)
    a.add_argument("--queue",required=True,type=Path)
    a.add_argument("--geometry",required=True,type=Path)
    a.add_argument("--handoff",required=True,type=Path)
    a.add_argument("--receipts",type=Path)
    args=a.parse_args()
    try:
        orders=check(args.queue,args.geometry,args.handoff)
        count=receipts(args.receipts,orders) if args.receipts else 0
    except GateError as err: a.exit(2,f"FAIL CLOSED: {err}\n")
    print(f"PASS: {len(orders)} registered masters, 360 source models, 12 family contracts, {count} unapproved worker submissions")

if __name__=="__main__": main()
