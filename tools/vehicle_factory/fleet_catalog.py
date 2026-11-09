"""LAST LIGHT Fleet Factory V1: original vehicle master profiles and resumable job planner.

Census reference: Notion vehicle research has 241 *reference variant IDs*, NOT
241 individually modeled original chassis. This catalog defines a smaller set
of original semantic archetypes, and does not imply visual approval or gameplay.
Python standard library only.
"""
import argparse
import hashlib
import json
from pathlib import Path

# Original dimensions, not measurements copied from reference-game assets.
# x = length, y = width, z = height; all metres.
PROFILES={
 "compact_hatchback":dict(dimensions_m=[3.86,1.69,1.46],wheelbase_m=2.48,
      geometry="hatchback",doors=5,seats=5,category="civilian"),
 "city_sedan":dict(dimensions_m=[4.48,1.76,1.43],wheelbase_m=2.65,
      geometry="sedan",doors=4,seats=5,category="civilian"),
 "family_wagon":dict(dimensions_m=[4.58,1.79,1.51],wheelbase_m=2.66,
      geometry="wagon",doors=5,seats=5,category="civilian"),
 "compact_suv":dict(dimensions_m=[4.42,1.84,1.72],wheelbase_m=2.62,
      geometry="suv",doors=5,seats=5,category="civilian"),
 "work_pickup":dict(dimensions_m=[5.18,1.89,1.78],wheelbase_m=3.05,
      geometry="pickup",doors=4,seats=5,category="utility"),
 "delivery_van":dict(dimensions_m=[5.12,1.94,2.38],wheelbase_m=3.20,
      geometry="van",doors=4,seats=3,category="utility"),
 "box_truck":dict(dimensions_m=[6.48,2.26,3.04],wheelbase_m=3.75,
      geometry="box_truck",doors=2,seats=3,category="heavy"),
 "city_bus":dict(dimensions_m=[9.70,2.50,3.15],wheelbase_m=5.15,
      geometry="bus",doors=3,seats=32,category="heavy"),
 "sport_coupe":dict(dimensions_m=[4.32,1.82,1.31],wheelbase_m=2.53,
      geometry="coupe",doors=2,seats=2,category="civilian"),
 "service_ambulance":dict(dimensions_m=[5.27,1.98,2.39],wheelbase_m=3.31,
      geometry="van",doors=4,seats=3,category="emergency"),
 "service_security":dict(dimensions_m=[4.48,1.76,1.43],wheelbase_m=2.65,
      geometry="sedan",doors=4,seats=5,category="emergency"),
 "rural_tractor":dict(dimensions_m=[3.74,2.00,2.48],wheelbase_m=2.31,
      geometry="tractor",doors=2,seats=1,category="machinery")
}
PALETTE={
 "faded_red":"#82483f",
 "dark_blue":"#364958",
 "cream_white":"#c9c8bb",
 "charcoal_grey":"#454847",
 "olive_green":"#616b54",
 "muted_beige":"#aca08b",
 "rust_brown":"#82523f",
 "pale_silver":"#a6aeae"
}
CONDITIONS={0:"maintained",1:"used",2:"weathered",3:"severely_neglected"}
# Only possible visual source combinations. Missing distinct geometry never
# silently becomes a differently colored stretched hatchback.
MAX_DIRECTIONS=16

def digest(obj):
    return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(",",":")).encode()).hexdigest()

def validate():
    assert len(PROFILES)==12 and len(PALETTE)==8
    for name,item in PROFILES.items():
        assert item["geometry"] in {"hatchback","sedan","wagon","suv","pickup","van",
                 "box_truck","bus","coupe","tractor"}
        assert all(.0 < float(v) < 20 for v in item["dimensions_m"])
        assert item["wheelbase_m"] < item["dimensions_m"][0]
        assert item["doors"]>0 and item["seats"]>0
    return True

def build_plan(profiles=None,colors=None,conditions=None,directions=16,batch_size=128):
    validate()
    profiles=list(PROFILES) if profiles is None else list(profiles)
    colors=list(PALETTE) if colors is None else list(colors)
    conditions=list(CONDITIONS) if conditions is None else list(conditions)
    if not profiles or not colors or not conditions:raise ValueError("empty selection")
    if len(set(profiles))!=len(profiles) or len(set(colors))!=len(colors) or len(set(conditions))!=len(conditions):
        raise ValueError("duplicate production selection")
    if any(x not in PROFILES for x in profiles):raise ValueError("unknown vehicle profile")
    if any(x not in PALETTE for x in colors):raise ValueError("unknown paint color")
    if any(x not in CONDITIONS for x in conditions):raise ValueError("unknown condition")
    if directions != 16:raise ValueError("production views require sixteen directions")
    if not 1<=batch_size<=256:raise ValueError("batch size outside 1..256")
    jobs=[]
    for model in sorted(profiles):
        for col in sorted(colors):
            for condition in sorted(conditions):
                payload=dict(asset_id="ll_vehicle_"+model,model=model,
                    geometry_template=PROFILES[model]["geometry"],
                    dimensions_m=PROFILES[model]["dimensions_m"],
                    palette_id=col,paint_hex=PALETTE[col],
                    condition_level=condition,condition_name=CONDITIONS[condition],
                    directions=directions,render_recipe_version=1)
                jobs.append(dict(job_id="llveh_"+digest(payload)[:20],**payload,
                    status="PLANNED_NOT_RENDERED_NOT_VISUALLY_APPROVED"))
    jobs.sort(key=lambda j:j["job_id"])
    batches=[]
    for n,start in enumerate(range(0,len(jobs),batch_size)):
        subset=jobs[start:start+batch_size]
        batches.append(dict(batch_id=f"fleet_{n+1:04d}",
             count=len(subset),job_ids=[x["job_id"] for x in subset],
             sha256=digest(subset)))
    return dict(schema_version=1,factory="LAST_LIGHT_FLEET_FACTORY",
      source="Original profile registry, no PZ game assets",
      status="PLAN_ONLY_NO_GAMEPLAY_INTEGRATION",
      distinct_archetypes=len(profiles),distinct_paint_colors=len(colors),
      environmental_conditions=len(conditions),
      total_candidate_variants=len(jobs),
      planned_frame_count=len(jobs)*directions,
      directions=directions,batch_size=batch_size,
      batches=batches,jobs=jobs,plan_sha256=digest(jobs))

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--models",default="")
    p.add_argument("--colors",default="")
    p.add_argument("--conditions",default="")
    p.add_argument("--batch-size",type=int,default=128)
    p.add_argument("--output",type=Path,default=Path("build/vehicle_factory/fleet_plan.json"))
    a=p.parse_args()
    selections=lambda v,transform=str:[transform(x.strip()) for x in v.split(",")] if v else None
    plan=build_plan(selections(a.models),selections(a.colors),selections(a.conditions,int),batch_size=a.batch_size)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(plan,indent=2)+"\n")
    print("LL_FLEET_PLAN_OK",plan["distinct_archetypes"],plan["total_candidate_variants"],
          plan["planned_frame_count"],len(plan["batches"]),flush=True)

if __name__=="__main__":main()
