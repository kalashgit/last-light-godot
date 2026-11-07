#!/usr/bin/env python3
"""Stable cosmetic condition assignment for independently generated original houses.

No runtime scene or save migration is performed here. The resulting manifest is
an input contract for a future Godot importer; no reference-game assets used.
"""
import argparse
import hashlib
import json
from pathlib import Path

SCHEMA=1
CONDITIONS=("maintained", "used", "weathered", "severely_neglected")
HOUSE_PROFILES={
    "occupied": (0.48,0.52,0.00,0.00),
    "recently_vacant": (0.25,0.58,0.17,0.00),
    "unoccupied": (0.00,0.32,0.54,0.14),
    "neglected": (0.00,0.00,0.60,0.40),
}
ROOM_MODIFIERS={"kitchen":0.05,"bathroom":0.10,"bedroom":-0.10,
                "living":-0.04,"garage":0.18,"basement":0.25,"attic":0.18}
OBJECT_MODIFIERS={"appliance":0.00,"upholstery":0.06,"cabinet":0.02,
                  "storage":0.05,"decoration":-0.03,"tool":0.09}

def stable_unit(*parts):
    raw="|".join(str(p) for p in parts).encode("utf-8")
    return int.from_bytes(hashlib.sha256(raw).digest()[:8],"big") / 2**64

def weighted_level(weights,u):
    acc=0.0
    for i,weight in enumerate(weights):
        acc+=weight
        if u<acc:return i
    return len(weights)-1

def condition_manifest(world_seed,neighborhood_id,houses):
    """Houses have stable IDs; rooms and objects may be reordered without rerolls."""
    if not isinstance(houses,list):raise ValueError("houses must be a list")
    result=[]; seen_houses=set()
    for house in sorted(houses,key=lambda h:h["id"]):
        hid=house["id"]
        if hid in seen_houses:raise ValueError("duplicate house id: "+hid)
        seen_houses.add(hid)
        profile=house["profile"]
        if profile not in HOUSE_PROFILES:raise ValueError("unknown profile: "+profile)
        house_level=weighted_level(HOUSE_PROFILES[profile],stable_unit(world_seed,neighborhood_id,hid,"house"))
        room_records=[];seen_rooms=set()
        for room in sorted(house.get("rooms",[]),key=lambda r:r["id"]):
            rid=room["id"]
            if rid in seen_rooms:raise ValueError("duplicate room id: "+rid)
            seen_rooms.add(rid)
            kind=room.get("type","living")
            # Stable house baseline plus spatially plausible local variation.
            climate=ROOM_MODIFIERS.get(kind,0.0)
            room_delta=(stable_unit(world_seed,hid,rid,"room")-.5)*.60
            room_level=max(0,min(3,round(house_level+climate*2+room_delta)))
            items=[];seen_items=set()
            for obj in sorted(room.get("objects",[]),key=lambda o:o["id"]):
                oid=obj["id"]
                if oid in seen_items:raise ValueError("duplicate object id: "+oid)
                seen_items.add(oid)
                role=obj.get("role","decoration")
                shift=OBJECT_MODIFIERS.get(role,0)
                noise=(stable_unit(world_seed,hid,rid,oid,"object")-.5)*1.45
                level=max(0,min(3,round(room_level+shift*2+noise)))
                items.append({"id":oid,"role":role,"material_id":obj.get("material_id"),
                              "condition_level":level,"condition_name":CONDITIONS[level]})
            room_records.append({"id":rid,"type":kind,"condition_level":room_level,"objects":items})
        result.append({"id":hid,"profile":profile,"condition_level":house_level,"rooms":room_records})
    return {"schema":SCHEMA,"world_seed":world_seed,"neighborhood_id":neighborhood_id,
            "status":"CANDIDATE_NOT_GODOT_IMPORTED","houses":result}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("input",type=Path,help="JSON containing world_seed, neighborhood_id, houses[]")
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    config=json.loads(a.input.read_text())
    manifest=condition_manifest(config["world_seed"],config["neighborhood_id"],config["houses"])
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n")
    print("LL_CONDITION_ASSIGNMENT_OK",len(manifest["houses"]),str(a.out))

if __name__=="__main__":main()
