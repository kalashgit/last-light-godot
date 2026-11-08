"""Durable, source-driven refinement ledger for all 360 existing 3D masters.

This ledger does not mistake 360 first-pass models for 360 Golden-approved
meshes, nor does it mistake 360 starter IDs for the entire 4,347+ reference
universe. Add one row per canonical ID in the full research census later.

Usage:
 python tools/geometry_first/refinement_ledger_v2.py \
     --out assets/master_library/geometry_refinement_ledger_v2.json
"""
import argparse
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(Path(__file__).resolve().parent))
from plan import build_plan
from refine_spec_v2 import FAMILY_RULES, STAGES,required_skills, defects_for

SOURCE=ROOT/"preview/geometry-first-all-360/batch_report.json"
REFINED_DEFAULT=ROOT/"preview/geometry-refinement-v2/refined_report.json"

def load_outcomes(path):
    if not path.exists():return {}
    raw=json.loads(path.read_text())
    if not isinstance(raw.get("items"),list):
        raise ValueError("refined report missing actual item list")
    outcomes={}
    for record in raw["items"]:
        key=record["asset_id"]
        if key in outcomes:
            raise ValueError("duplicate refinement evidence for "+key)
        outcomes[key]=record
    if raw.get("source_count") != len(outcomes):
        raise ValueError("refined report source_count does not match unique evidence")
    return outcomes

def verified_refinement(record, original):
    if not record or not record.get("refinement_applied") or not record.get("geometry_source_verified"):
        return False
    original_hash=record.get("original_sha256")
    refined_hash=record.get("glb_sha256")
    # The 360 immutable archive was exported on an earlier Blender/run version.
    # A fresh V1 comparison reconstruction may be byte-different while still
    # using the same canonical source recipe. Never mislabel the fresh V1 hash
    # as the archived GLB hash; report both distinctly below.
    if not isinstance(original_hash,str) or len(original_hash)!=64:
        raise ValueError("missing reconstructed V1 baseline hash: "+record["asset_id"])
    if record.get("rebuilt_source_recipe_sha256")!=original["recipe_hash"]:
        raise ValueError("canonical recipe differs in reconstructed V1 baseline: "+record["asset_id"])
    if not isinstance(refined_hash,str) or len(refined_hash)!=64 or refined_hash==original_hash:
        raise ValueError("missing or unchanged refined GLB hash: "+record["asset_id"])
    if not record.get("repair_parts") or not record.get("recipe_sha256"):
        raise ValueError("missing reproducible geometry repair evidence: "+record["asset_id"])
    return True

def create(refined_report=None):
    plan=build_plan()
    if len(plan["jobs"])!=360:
        raise ValueError("source census changed: inspect semantic IDs before release")
    original=json.loads(SOURCE.read_text())
    observed={r["asset_id"]:r for r in original["items"]}
    if len(observed)!=360 or len(original["items"])!=360:
        raise ValueError("360 source models are not uniquely present in verified archive")
    refined=load_outcomes(Path(refined_report) if refined_report else REFINED_DEFAULT)
    extra=set(refined)-set(observed)
    if extra:raise ValueError("unknown refinement records: "+str(sorted(extra)[:5]))
    records=[]
    for job in plan["jobs"]:
        key=job["asset_id"]
        prior=observed[key]
        r=refined.get(key)
        refined_pass=verified_refinement(r,prior)
        category=job["category"]
        stage=dict(geometry_source=True,
            refined_geometry=refined_pass,
            uv_material=False,
            sprite_2_5d=False,
            engine_import=False,
            gameplay_integrated=False,
            founder_golden_approved=False,
            iphone_device_qa=False)
        records.append(dict(
            asset_id=key,
            stable_source_recipe_hash=prior["recipe_hash"],
            source_glb_sha256=prior["glb_sha256"],
            comparison_rebuilt_v1_glb_sha256=(r.get("original_sha256") if r else None),
            comparison_v1_glb_matches_immutable_archive=(
                r.get("original_sha256")==prior["glb_sha256"] if r else None),
            original_geometry_source_archive="https://github.com/kalashgit/last-light-godot/actions/runs/42460745955",
            master_3d_source_category=category,
            semantic_geometry_family=job["geometry_family"],
            originally_requested_dimensions_m=job["dimensions_m"],
            required_skills=required_skills(job),
            family_defect_checks=defects_for(job),
            source_model_geometry_warning=prior.get("geometry_warning"),
            coverage_scope="EXISTING_360_SOURCE_SET_ONLY_NOT_EXHAUSTIVE_EXTERNAL_CENSUS",
            release_gates=stage,
            v2_refinement_source_archive=(r.get("source_archive") if r else None),
            v2_geometry_source_sha256=(r.get("glb_sha256") if r else None),
            latest_geometry_review_status=("V2_SOURCE_TECHNICALLY_VERIFIED_VISUAL_REVIEW_PENDING"
                    if refined_pass else "V1_GEOMETRY_RETAINED_REFINEMENT_PENDING"),
            next_action=("LL-111 founder shape/visual comparison then UV/material pass"
                    if refined_pass else "Apply family-specific reusable geometry refinement"),
        ))
    counts={
        "source_models":len(records),
        "refined_geometry_verified":sum(x["release_gates"]["refined_geometry"] for x in records),
        "uv_materials_verified":0,
        "golden_visual_approved":0,
        "godot_gameplay_integrated_v2":0,
        "remaining_refinements":sum(not x["release_gates"]["refined_geometry"] for x in records),
    }
    # Separate known starter/model identities from external media-reference counts.
    return dict(schema_version=2,
       name="LAST_LIGHT_SOURCE_GEOMETRY_REFINEMENT_LEDGER",
       status="SOURCE_FIDELITY_REFINEMENT_IN_PROGRESS_NOT_FULL_GOLDEN_COMPLETION",
       scope=dict(exact_starter_geometry_ids=360,
                  full_census_unreconciled=True,
                  research_reference_sprite_icons_at_least=4347,
                  media_research_snapshot_ids=21025,
                  never_conflate_research_records_with_unique_original_models=True),
       stages=STAGES,
       family_rules_version=FAMILY_RULES["version"],
       counts=counts,records=records)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path,default=ROOT/"assets/master_library/geometry_refinement_ledger_v2.json")
    p.add_argument("--refined-report",type=Path,default=REFINED_DEFAULT)
    a=p.parse_args()
    result=create(a.refined_report)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2)+"\n")
    print("LL_REFINEMENT_LEDGER_PASS",result["counts"]["source_models"],
          result["counts"]["refined_geometry_verified"],flush=True)

if __name__=="__main__":
    main()
