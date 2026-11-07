"""LAST LIGHT actor factory V1: deterministic day-based aging, fitness, cosmetics and location-specific zombie loadouts.

Pure stdlib / no engine dependencies. Source data, not a complete gameplay integration.
Every update applies to an immutable world day exactly once; replays are deterministic.
No unlicensed models or Project Zomboid artwork are used.
"""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import math
import random

SCHEMA=1
WEARABLES={
 "ll_wear_grey_underwear":dict(slot="underwear",color="#777a7b",weight_kg=.15),
 "ll_wear_grey_tank":dict(slot="torso_inner",color="#81878b",weight_kg=.22),
 "ll_wear_jeans":dict(slot="legs",color="#515c65",weight_kg=.72),
 "ll_wear_work_boots":dict(slot="feet",color="#35312b",weight_kg=1.35),
 "ll_wear_civilian_shirt":dict(slot="torso_inner",color="#788272",weight_kg=.28),
 "ll_wear_hoodie":dict(slot="torso_outer",color="#555f58",weight_kg=.68),
 "ll_wear_medical_scrubs":dict(slot="torso_inner",color="#5d8880",weight_kg=.38),
 "ll_wear_medical_pants":dict(slot="legs",color="#5d8880",weight_kg=.43),
 "ll_wear_lab_coat":dict(slot="torso_outer",color="#cbcabe",weight_kg=.65),
 "ll_wear_hivis_vest":dict(slot="torso_outer",color="#aba44a",weight_kg=.45),
 "ll_wear_work_pants":dict(slot="legs",color="#626055",weight_kg=.89),
 "ll_wear_police_shirt":dict(slot="torso_inner",color="#35445c",weight_kg=.46),
 "ll_wear_police_pants":dict(slot="legs",color="#30384b",weight_kg=.70),
 "ll_wear_shop_apron":dict(slot="torso_outer",color="#5e5449",weight_kg=.32),
 "ll_wear_office_shirt":dict(slot="torso_inner",color="#a2a8a6",weight_kg=.32),
 "ll_wear_office_trousers":dict(slot="legs",color="#4b4a4c",weight_kg=.55),
 "ll_wear_gym_top":dict(slot="torso_inner",color="#646d7b",weight_kg=.19),
 "ll_wear_gym_shorts":dict(slot="legs",color="#454b50",weight_kg=.22),
 "ll_wear_athletic_shoes":dict(slot="feet",color="#454343",weight_kg=.60),
 "ll_wear_street_shoes":dict(slot="feet",color="#383837",weight_kg=.72),
 "ll_wear_backpack":dict(slot="back",color="#4a5640",weight_kg=1.2),
 "ll_wear_hard_hat":dict(slot="head",color="#b8a864",weight_kg=.37),
}
# All items from existing starter inventory are stable actual LAST LIGHT IDs.
SURVIVAL_LOOT={
 "bandage":"ll_medical_sterile_bandage",
 "first_aid":"ll_medical_first_aid_case",
 "hammer":"ll_tools_claw_hammer",
 "hatchet":"ll_tools_hatchet",
 "flashlight":"ll_household_flashlight",
 "water":"ll_food_water_bottle",
 "beans":"ll_food_bean_tin",
}
# Weighted role choices, not universal outfits. Includes civilian visitors/staff.
AREAS={
 "hospital":(("medical_staff",65),("civilian",25),("maintenance",10)),
 "clinic":(("medical_staff",68),("civilian",32)),
 "construction":(("builder",72),("civilian",18),("security",10)),
 "workshop":(("builder",60),("civilian",30),("security",10)),
 "police_station":(("security",75),("civilian",20),("maintenance",5)),
 "supermarket":(("shop_staff",52),("civilian",43),("maintenance",5)),
 "shop":(("shop_staff",50),("civilian",50)),
 "office":(("office_worker",65),("civilian",30),("maintenance",5)),
 "gym":(("gym_goer",80),("civilian",20)),
 "residential":(("civilian",85),("gym_goer",10),("office_worker",5)),
 "road":(("civilian",75),("builder",10),("office_worker",10),("medical_staff",5))
}
ROLES={
 "medical_staff":dict(clothes=("ll_wear_medical_scrubs","ll_wear_medical_pants","ll_wear_street_shoes"),
                       optional=("ll_wear_lab_coat",),loot=("bandage","first_aid")),
 "builder":dict(clothes=("ll_wear_grey_tank","ll_wear_work_pants","ll_wear_work_boots","ll_wear_hivis_vest"),
                optional=("ll_wear_hard_hat",),loot=("hammer","water")),
 "security":dict(clothes=("ll_wear_police_shirt","ll_wear_police_pants","ll_wear_work_boots"),
                 optional=(),loot=("flashlight","water")),
 "shop_staff":dict(clothes=("ll_wear_civilian_shirt","ll_wear_jeans","ll_wear_street_shoes","ll_wear_shop_apron"),
                   optional=(),loot=("water","beans")),
 "office_worker":dict(clothes=("ll_wear_office_shirt","ll_wear_office_trousers","ll_wear_street_shoes"),
                      optional=(),loot=("water",)),
 "gym_goer":dict(clothes=("ll_wear_gym_top","ll_wear_gym_shorts","ll_wear_athletic_shoes"),
                optional=(),loot=("water",)),
 "maintenance":dict(clothes=("ll_wear_hoodie","ll_wear_work_pants","ll_wear_work_boots"),
                    optional=(),loot=("hammer","flashlight")),
 "civilian":dict(clothes=("ll_wear_civilian_shirt","ll_wear_jeans","ll_wear_street_shoes"),
                 optional=("ll_wear_backpack",),loot=("water",))
}
ACTOR_RIG={
 "id":"ll_biped_v1","axes":"x_left_right_y_front_back_z_up",
 "bones":["root","pelvis","spine","chest","neck","head",
          "upper_arm_L","forearm_L","hand_L","upper_arm_R","forearm_R","hand_R",
          "thigh_L","calf_L","foot_L","thigh_R","calf_R","foot_R"],
 "sockets":["left_hand","right_hand","two_hand_left","back","hip_right","headgear"],
 "direction_count":4,"tile_px":[80,40],"projection":"fixed_2_to_1"
}
REACHABLE_HEIGHT=(1.55,1.95)
BASE_AGE_YEARS=27.0
BASE_DAYS_PER_YEAR=365
HAIR_GROWTH_MM_PER_DAY=.34

def _seed(*values):
    source=":".join(map(str,values))
    return int.from_bytes(sha256(source.encode("utf-8")).digest()[:8],"big")

def _smoothstep(a,b,x):
    t=max(0.0,min(1.0,(x-a)/max(.0001,b-a)))
    return t*t*(3-2*t)

def create_actor(actor_id,world_seed=1,build="average",presentation="neutral",
                 height_m=1.74,age_years=BASE_AGE_YEARS,days_per_biological_year=365):
    if not 1.55<=height_m<=1.95: raise ValueError("actor height out of calibrated range")
    if build not in ("average","narrow","broad"): raise ValueError("unknown actor build")
    if presentation not in ("neutral","masculine","feminine"): raise ValueError("bad presentation")
    if not 10<=age_years<=110 or not 30<=days_per_biological_year<=730:
        raise ValueError("invalid age/calendar settings")
    genetic=rng_for("genetic",world_seed,actor_id)
    predisposition=genetic.uniform(-8,8)
    hair_length=genetic.uniform(8,40)
    actor=dict(schema=SCHEMA,actor_id=actor_id,kind="human",rig=ACTOR_RIG["id"],
        build=build,presentation=presentation,height_m=height_m,
        world_seed=world_seed,day_index=0,
        days_per_biological_year=days_per_biological_year,
        biological_age_days=round(age_years*days_per_biological_year,6),
        grey_onset_age=40+predisposition,hair_length_mm=hair_length,
        beard_length_mm=0.0,hair_cut_day=0,
        muscle=({"narrow":.32,"average":.5,"broad":.68}[build]),
        fat=.47,fitness=.48,stamina_condition=.65,
        alive=True,cause_of_death=None,life_event_log=[],
        apparel=["ll_wear_grey_underwear","ll_wear_grey_tank"],
        held_item_id=None,hand="right")
    return appearance(actor) | actor

def rng_for(*ids):
    return random.Random(_seed(*ids))

def appearance(actor):
    age=float(actor["biological_age_days"])/float(actor["days_per_biological_year"])
    grey=_smoothstep(actor["grey_onset_age"]-6,actor["grey_onset_age"]+35,age)
    hair=max(0,min(450,float(actor["hair_length_mm"])))
    # Cosmetic ageing and fitness changes use scalar body morphs, not new rigs.
    muscle=max(0.1,min(.95,float(actor["muscle"])))
    return dict(grey_fraction=round(grey,5),head_hair_style=(
         "cropped" if hair<24 else "short" if hair<65 else "medium" if hair<190 else "long"),
         body_morph={"muscle":round(muscle,4),"fat":round(float(actor["fat"]),4),
                     "chest_width_scale":round(.92+.25*muscle,4),
                     "arm_radius_scale":round(.87+.32*muscle,4),
                     "leg_radius_scale":round(.91+.27*muscle,4)})

def mortality_hazard(age_years):
    # Preliminary gameplay pacing curve; mortality almost certain after sufficient years.
    if age_years<65: return 0.0
    return min(.30,.000025*math.exp(.135*(age_years-65)))

def advance_day(actor,day_index,exercise=0.0,nutrition=.65,recovery=.65):
    """Advance exactly one absolute game day. Reject repeated/skipped days.

    Hair and fitness change daily. Age increases by 1 biological-day unit per game
    day; convert to years using configurable days_per_biological_year.
    """
    if not actor["alive"]: return deepcopy(actor)
    if day_index != actor["day_index"]+1:
        raise ValueError("time update must be sequential and never repeated")
    for value in (exercise,nutrition,recovery):
        if not 0<=value<=1: raise ValueError("inputs must be 0..1")
    a=deepcopy(actor)
    a["day_index"]=day_index
    a["biological_age_days"]+=1
    a["hair_length_mm"]=min(450,a["hair_length_mm"]+HAIR_GROWTH_MM_PER_DAY)
    a["beard_length_mm"]=min(125,a["beard_length_mm"]+.20)
    # Capped gradual muscle development/atrophy; modified by nutrition and recovery.
    growth=(exercise*.65 +nutrition*.20+recovery*.15-.60)*.0015
    a["muscle"]=max(.12,min(.88,a["muscle"]+growth))
    a["fitness"]=max(.10,min(.92,a["fitness"]+(exercise-.38)*.0012))
    a["fat"]=max(.10,min(.90,a["fat"]+(nutrition-.55-exercise*.27)*.0008))
    a["stamina_condition"]=max(.12,min(.94,a["stamina_condition"]+
                                              (recovery-.4)*.0010-exercise*.00015))
    age=a["biological_age_days"]/a["days_per_biological_year"]
    # A world/actor/day keyed draw makes death determinstic and not reload-rerollable.
    if rng_for("natural_mortality",a["world_seed"],a["actor_id"],day_index).random() < mortality_hazard(age):
        a["alive"]=False
        a["cause_of_death"]="natural_ageing"
        a["life_event_log"].append({"day":day_index,"event":"death","cause":"natural_ageing"})
    # Optional design cap avoids immortal actors; not reached in normal pilot.
    if age >= 125 and a["alive"]:
        a["alive"]=False
        a["cause_of_death"]="natural_ageing"
        a["life_event_log"].append({"day":day_index,"event":"death","cause":"natural_ageing"})
    a.update(appearance(a))
    return a

def trim_hair(actor,length_mm,beard_mm=None):
    if length_mm<0 or length_mm>450: raise ValueError("hair length out of range")
    a=deepcopy(actor)
    a["hair_length_mm"]=min(float(length_mm),a["hair_length_mm"])
    a["hair_cut_day"]=a["day_index"]
    if beard_mm is not None:
        if not 0<=beard_mm<=125: raise ValueError("beard invalid")
        a["beard_length_mm"]=min(float(beard_mm),a["beard_length_mm"])
    a.update(appearance(a))
    return a

def _choose_weighted(rng,options):
    total=sum(weight for _,weight in options)
    x=rng.randrange(total)
    for name,weight in options:
        x-=weight
        if x<0: return name
    raise AssertionError("bad weights")

def spawn_zombie(world_seed,building_id,room_id,spawn_index,area,age_years=None):
    if not building_id or not room_id or spawn_index<0: raise ValueError("stable location ID required")
    if area not in AREAS: raise ValueError("unknown area; do not randomly assign uniforms")
    rng=rng_for("zombie_spawn",world_seed,building_id,room_id,spawn_index)
    role=_choose_weighted(rng,AREAS[area])
    wear=list(ROLES[role]["clothes"])
    for optional in ROLES[role]["optional"]:
        if rng.random()<.3: wear.append(optional)
    if age_years is None: age_years=round(rng.uniform(20,80),2)
    id=f"ll_zombie_{_seed(world_seed,building_id,room_id,spawn_index):016x}"
    zombie=create_actor(id,world_seed,build=rng.choice(["narrow","average","broad"]),
                        presentation=rng.choice(["neutral","masculine","feminine"]),
                        height_m=round(rng.uniform(1.55,1.92),3),age_years=age_years)
    zombie.update(kind="zombie",role=role,area=area,building_id=building_id,room_id=room_id,
                  spawn_index=spawn_index,apparel=wear,posture=rng.choice(["hunched","upright","leaning"]),
                  deterioration=round(rng.uniform(.03,.55),3),alive=False,
                  death_state="reanimated",cause_of_death="infection")
    # Clothes are ACTUAL retrievable loot item instances, not just visual decals.
    belongings=[{"item_id":w,"count":1,"worn":True} for w in wear]
    for loot in ROLES[role]["loot"]:
        if rng.random()<.52:
            belongings.append({"item_id":SURVIVAL_LOOT[loot],"count":1,"worn":False})
    zombie["inventory"]=belongings
    zombie["visual_loadout_ids"]=list(wear)
    zombie.update(appearance(zombie))
    return zombie

def set_equipment(actor,wearables=None,held_item_id=None,hand="right"):
    a=deepcopy(actor)
    if wearables is not None:
        if any(w not in WEARABLES for w in wearables):raise ValueError("unknown wearable")
        # Same slot can have only one fitted item. Torso outer/inner are separate slots.
        slots=[WEARABLES[w]["slot"] for w in wearables]
        if len(set(slots))!=len(slots):raise ValueError("conflicting wearable slots")
        a["apparel"]=list(wearables)
    if held_item_id is not None and held_item_id not in SURVIVAL_LOOT.values():
        raise ValueError("item must have a stable inventory ID")
    if hand not in ("left","right","two_handed"):raise ValueError("bad hand socket")
    a["held_item_id"]=held_item_id
    a["hand"]=hand
    return a
