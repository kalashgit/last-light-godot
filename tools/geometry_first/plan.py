"""LAST LIGHT geometry-first reconstruction census, stage G.

Source sprites are VISUAL REFERENCES, not embedded geometry. Single sprites do
not contain back faces, depth or true camera calibration; all reconstructions are
original parametric approximations until founder geometry review passes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"tools"/"asset_factory"))
sys.path.insert(0,str(ROOT/"tools"/"vehicle_factory"))
from catalog import registry
from fleet_catalog import PROFILES

GOLD=ROOT/"assets/last_light/golden40/manifest.json"
ACTOR_VARIANTS=(
 "human_underwear","human_worker_crowbar","human_older",
 "zombie_hospital","zombie_construction"
)
FURNITURE=("refrigerator","cabinet","sofa")
SCOPE=("golden40","catalog","furniture","actor","vehicle")

# Dimensions x,y,z in physical metres, intentionally approximate and tunable
# against original reference and logical item size.
GOLDEN_SPECS={
 "ammo_box_40cal":("box",[.16,.10,.09]),
 "acorn":("organic",[.028,.028,.040]),
 "aerosol_canister":("aerosol",[.075,.075,.19]),
 "timed_aerosol_canister":("aerosol",[.08,.08,.21]),
 "air_filter_tape":("roll",[.105,.105,.035]),
 "air_filter_panel":("panel",[.27,.055,.32]),
 "digital_alarm_clock":("clock",[.18,.075,.12]),
 "respirator_mask":("respirator",[.16,.12,.16]),
 "isopropyl_alcohol":("bottle",[.085,.085,.22]),
 "alcohol_wipes_old":("packet",[.18,.12,.05]),
 "alcohol_wipes":("packet",[.18,.12,.05]),
 "field_pack_camo":("backpack",[.38,.24,.53]),
 "field_pack_sand":("backpack",[.38,.24,.53]),
 "field_pack_olive":("backpack",[.38,.24,.53]),
 "licorice_sweets":("packet",[.14,.10,.03]),
 "aluminum_ingot":("ingot",[.18,.08,.06]),
 "aluminum_scrap":("scrap",[.19,.15,.08]),
 "amethyst_raw":("geode",[.11,.10,.08]),
 "amethyst_gem":("gem",[.065,.05,.075]),
 "ammunition_case":("case",[.38,.21,.24]),
 "hand_axe":("axe",[.23,.13,.42]),
 "felling_axe":("axe",[.34,.15,.88]),
 "stone_axe":("axe",[.24,.13,.58]),
 "baseball_bat":("bat",[.08,.08,.82]),
 "reinforced_baseball_bat":("bat",[.095,.095,.84]),
 "basic_mace":("mace",[.16,.16,.62]),
 "bone_club":("club",[.105,.10,.52]),
 "meat_cleaver":("cleaver",[.075,.035,.31]),
 "crowbar":("crowbar",[.075,.075,.68]),
 "hunting_knife":("knife",[.04,.028,.30]),
 "single_edge_sword":("sword",[.08,.04,.89]),
 "butterfly_knife_folded":("folded_knife",[.036,.025,.14]),
 "pocket_knife":("folded_knife",[.035,.025,.12]),
 "crude_machete":("machete",[.08,.035,.58]),
 "machete":("machete",[.07,.035,.57]),
 "pickaxe":("pickaxe",[.48,.12,.88]),
 "pitchfork":("pitchfork",[.29,.10,1.25]),
 "scythe":("scythe",[.80,.11,1.45]),
 "short_pump_shotgun":("firearm_prop",[.12,.095,.72]),
 "hunting_rifle":("firearm_prop",[.12,.095,1.05])
}
# Future geometry families discovered by master census must extend this registry.
RECON_VERSION="last-light-reconstruction-v1.0"

def digest(obj):
    return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(",",":")).encode()).hexdigest()

def build_plan(categories=None,limit=0,include=None):
    categories=set(categories or SCOPE)
    if not categories or categories-set(SCOPE):
        raise ValueError("unsupported category selection")
    jobs=[]
    if "golden40" in categories:
        golden=json.loads(GOLD.read_text())
        if len(golden["items"])!=40: raise ValueError("Golden 40 changed; reconcile census")
        for row in golden["items"]:
            slug=row["id"].removeprefix("ll_golden_")
            if slug not in GOLDEN_SPECS:
                raise ValueError("missing physical Golden40 geometry design: "+slug)
            family,dimensions=GOLDEN_SPECS[slug]
            jobs.append(dict(
                asset_id=row["id"],category="golden40",name=row["name"],
                source_reference="assets/last_light/golden40/"+row["master"],
                source_reference_sha256=row["sha256"],
                geometry_family=family,dimensions_m=dimensions,
                geometry_recipe="golden40_original_parametric",
                quality="ORIGINAL_GEOMETRY_APPROXIMATION_NOT_VISUALLY_APPROVED",
                original_reference_only=True
            ))
    if "catalog" in categories:
        for row in registry():
            jobs.append(dict(
                asset_id=row["id"],category="catalog",name=row["name"],
                source_reference="assets/generated/factory/registry.json",
                geometry_family=row["family"],dimensions_m=row["dimensions_m"],
                geometry_recipe="existing_asset_factory_parametric",
                original_reference_only=False,
                quality="EXISTING_BASIC_GEOMETRY_NOT_GOLDEN_APPROVED"
            ))
    if "furniture" in categories:
        for item in FURNITURE:
            jobs.append(dict(asset_id="ll_master_furniture_"+item,
                category="furniture",name=item,geometry_family=item,
                dimensions_m={"refrigerator":[.70,.65,1.70],
                    "cabinet":[.9,.5,1.4],"sofa":[1.7,.82,.82]}[item],
                geometry_recipe="blender_factory_v3_hero_existing_source",
                original_reference_only=False,
                quality="ACTUAL_DETAILED_MESH_SOURCE_PENDING_GEOMETRY_REVIEW"))
    if "actor" in categories:
        for variant in ACTOR_VARIANTS:
            jobs.append(dict(asset_id="ll_master_actor_"+variant,
                category="actor",name=variant,geometry_family="biped",
                dimensions_m=[.52,.34,1.77],
                geometry_recipe="existing_actor_factory_pose_mesh",
                original_reference_only=False,
                quality="PROCEDURAL_ACTOR_POSE_NOT_SKINNED_ARMATURE_NOT_GOLDEN_APPROVED"))
    if "vehicle" in categories:
        for model,profile in PROFILES.items():
            jobs.append(dict(asset_id="ll_master_vehicle_"+model,
                category="vehicle",name=model,
                geometry_family=profile["geometry"],
                dimensions_m=profile["dimensions_m"],
                geometry_recipe="existing_fleet_factory_unique_chassis",
                original_reference_only=False,
                quality="SOURCE_CHASSIS_TECHNICAL_CANDIDATE_NOT_GOLDEN_APPROVED"))
    if include is not None:
        inc=set(include)
        if len(inc)!=len(include) or inc-set(x["asset_id"] for x in jobs):
            raise ValueError("unknown or repeated asset IDs")
        jobs=[x for x in jobs if x["asset_id"] in inc]
    jobs.sort(key=lambda x:(x["category"],x["asset_id"]))
    if limit:
        if limit<1 or limit>len(jobs):raise ValueError("invalid selection limit")
        jobs=jobs[:limit]
    seen=set()
    for job in jobs:
        a=job["asset_id"]
        if a in seen:raise ValueError("duplicate asset ID: "+a)
        seen.add(a)
        p=job["dimensions_m"]
        if len(p)!=3 or any(not .001<=float(v)<=20 for v in p):
            raise ValueError("unphysical geometry dimensions: "+a)
        job["template_source_hash"]=digest(dict(revision=RECON_VERSION,recipe=job))
        job["status"]="3D_SOURCE_PLANNED_NOT_EXPORTED"
    counts={k:sum(x["category"]==k for x in jobs) for k in SCOPE}
    plan=dict(schema=1,source_revision=RECON_VERSION,
        status="GEOMETRY_SOURCE_PLAN_NOT_RENDERED_NOT_GOLDEN_APPROVED",
        total_unique=len(jobs),per_category=counts,
        calibration_required=True,
        render_2_5d_status="PENDING_SEPARATE_MATERIAL_AND_RENDER_STAGE",
        jobs=jobs)
    plan["plan_sha256"]=digest(jobs)
    return plan

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--categories",default=",".join(SCOPE))
    p.add_argument("--limit",type=int,default=0)
    p.add_argument("--output",type=Path,default=Path("build/geometry_first/plan.json"))
    p.add_argument("--asset-ids",default="")
    a=p.parse_args()
    plan=build_plan(a.categories.split(","),a.limit,
                    a.asset_ids.split(",") if a.asset_ids else None)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(plan,indent=2)+"\n")
    print("LL_GEOMETRY_PLAN_OK",plan["total_unique"],
          json.dumps(plan["per_category"],sort_keys=True),flush=True)

if __name__=="__main__":main()
