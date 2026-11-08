"""Reproducible geometry-refinement memory and 360-source work order generator.

Usage:
  python tools/geometry_first/refinement_memory.py --output build/geometry_first/refinement_work_orders.json
  python tools/geometry_first/refinement_memory.py --validate-only

A work order is NOT a completed refinement. Only accept recipe QA evidence after
source .blend edit, a new source SHA, three transfer variants and before/after
neutral clay and isometric renders have been verified.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from plan import build_plan

ROOT=Path(__file__).resolve().parents[2]
REGISTRY=Path(__file__).with_name("refinement_recipes.json")
REQUIRED_CATEGORIES={"golden40","catalog","furniture","actor","vehicle"}
DRAFT="DRAFT_NEEDS_CLAY_AND_TRANSFER_VALIDATION"
VALIDATED="FAMILY_REFINEMENT_VALIDATED"
VALID_STATES={DRAFT,"IN_PROGRESS_SOURCE_GEOMETRY",VALIDATED}

def sha(obj):
    return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(",",":")).encode()).hexdigest()

def compile_orders():
    source=json.loads(REGISTRY.read_text())
    if source.get("schema")!=1:raise ValueError("unknown refinement memory schema")
    entries=source["families"]
    mapping={f["category"]:f for f in entries}
    if len(entries)!=len(mapping) or set(mapping)!=REQUIRED_CATEGORIES:
        raise ValueError("missing, repeated or unsupported refinement family")
    for key,recipe in mapping.items():
        if recipe["status"] not in VALID_STATES:
            raise ValueError("unknown recipe state: "+key)
        if len(recipe["transfer_extremes"])<3:
            raise ValueError("each family requires at least three variation extremes")
        if not recipe["checks"] or not recipe["lead_skill"].startswith("LL-"):
            raise ValueError("missing specialist instructions: "+key)
        if recipe["status"]==VALIDATED:
            if len(recipe["accepted_source_hashes"])<3 or len(recipe["verified_outputs"])<3:
                raise ValueError("recipe claimed validated without transfer evidence: "+key)
            for proof in recipe["verified_outputs"]:
                if not all(proof.get(x) for x in (
                    "asset_id","before_source_sha256","after_source_sha256",
                    "clay_before","clay_after","isometric_before","isometric_after",
                    "qa_report")):
                    raise ValueError("recipe missing complete before/after evidence: "+key)
                if proof["before_source_sha256"]==proof["after_source_sha256"]:
                    raise ValueError("claimed source refinement without changed geometry: "+key)
    plan=build_plan()
    orders=[]
    for job in plan["jobs"]:
        family=mapping[job["category"]]
        orders.append({
            "asset_id":job["asset_id"],
            "category":job["category"],
            "source_template_hash":job["template_source_hash"],
            "baseline_geometry_state":job["status"],
            "geometry_family":job["geometry_family"],
            "recipe_id":family["recipe_id"],
            "recipe_version":family["version"],
            "recipe_hash":sha(family),
            "required_checks":family["checks"],
            "specialist":family["lead_skill"],
            "geometry_refinement_status":"PENDING_REAL_SOURCE_EDIT_AND_CLAY_QA",
            "source_3d_preserved":True,
            "material_approval":False,
            "2_5d_approval":False,
            "founder_golden_approval":False
        })
    if len(orders)!=360 or len({x["asset_id"] for x in orders})!=360:
        raise ValueError("full 360 geometry work orders not covered")
    counts={c:sum(x["category"]==c for x in orders) for c in sorted(mapping)}
    return dict(schema=1,source_count=len(orders),family_counts=counts,
                validated_family_recipes=sum(x["status"]==VALIDATED for x in entries),
                geometry_refinements_claimed=0,
                status="WORK_ORDERS_ONLY_NO_UNVERIFIED_QUALITY_CLAIMS",
                orders=orders,work_orders_sha256=sha(orders))

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--output",type=Path,default=Path("build/geometry_first/refinement_work_orders.json"))
    p.add_argument("--validate-only",action="store_true")
    args=p.parse_args()
    result=compile_orders()
    if not args.validate_only:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(result,indent=2)+"\n")
    print("LL_REFINEMENT_MEMORY_QA_PASS",result["source_count"],
          "work orders",result["validated_family_recipes"],"validated recipes",
          json.dumps(result["family_counts"],sort_keys=True),flush=True)

if __name__=="__main__":main()
