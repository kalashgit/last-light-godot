"""Factory-wide semantic-component audit for the 300 stable starter catalog IDs.

Reports which *requirements* apply to each family, and which authored semantic
templates exist. It does not infer fictional capacity/mass/sight values or mark
unknown objects game-ready. Extend the audit to tile/terrain census once indexed.
"""
import argparse
import collections
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from batch_plan import source_registry
from object_contracts import validate_catalog

ROOT=Path(__file__).resolve().parents[2]
EXAMPLES=ROOT/"tools"/"unified_factory"/"examples"/"world_objects_v1.json"
HOLLOW={"fridge","cabinet","wardrobe","chest"}
OPEN_STORAGE={"shelf","rack"}
STATIC_FIXTURE={"counter","sink","stove","washer","toilet","bath"}
HOLDABLE={"food","medical","tools","crafting","household"}
FAMILY_ALIASES={"fridge":"refrigerator"}
BASE=("identity","original_art","material","condition","collision","sight",
      "sound","mass","placement","persistence","visual_qa")

def requirements(rec):
    family=rec["family"];category=rec["category"]
    required=set(BASE)
    if category=="furniture":
        required.update(("movability","footprint","room_placement","damage_state"))
        if family in HOLLOW:
            required.update(("hollow_geometry","container_capacity","compartment_access","interaction","interior_render"))
        if family in OPEN_STORAGE:
            required.update(("accessible_surface_storage","interaction"))
        if family in STATIC_FIXTURE:
            required.add("interaction")
    if category in HOLDABLE:
        required.update(("inventory_weight","stacking","pickup_reach"))
    if rec.get("visible_carry"):
        required.update(("held_pose","directional_attachment"))
    if category=="tools":
        required.add("action_impact_event")
    return sorted(required)

def audit():
    templates=json.loads(EXAMPLES.read_text())
    validate_catalog(templates)
    by_family=collections.defaultdict(list)
    for t in templates["templates"]:
        by_family[t["family"]].append(t)
    rows=[]
    for rec in source_registry():
        family=FAMILY_ALIASES.get(rec["family"],rec["family"])
        matches=by_family.get(family,[])
        match=matches[0] if len(matches)==1 else None
        rows.append(dict(asset_id=rec["id"],category=rec["category"],
            geometry_family=rec["family"],required_components=requirements(rec),
            candidate_template_id=match["template_id"] if match else None,
            status=("FAMILY_TEMPLATE_CANDIDATE_NEEDS_ASSET_REVIEW" if match
                    else "SEMANTIC_TEMPLATE_NOT_AUTHORED")))
    counters=collections.Counter(x["status"] for x in rows)
    return dict(schema_version=1,status="COVERAGE_AUDIT_NOT_GAMEPLAY_INTEGRATION",
        catalog_id_count=len(rows),template_example_count=len(templates["templates"]),
        tile_catalog_status="SEPARATE_TILE_CENSUS_AND_MATERIAL_TESTS_PENDING",
        status_counts=dict(sorted(counters.items())),records=rows)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--output",type=Path,default=Path("build/unified_factory/capability_audit.json"))
    a=p.parse_args()
    result=audit()
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,indent=2)+"\n")
    assert result["catalog_id_count"]==300
    print("LL_CAPABILITY_AUDIT_PASS",result["status_counts"],flush=True)

if __name__=="__main__":
    main()
