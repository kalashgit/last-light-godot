"""Neighborhood cosmetic condition contracts; no gameplay or world writes."""
import importlib.util
from copy import deepcopy
from pathlib import Path

source=Path(__file__).resolve().parents[1]/"tools/material_factory/condition_assignment.py"
spec=importlib.util.spec_from_file_location("ll_condition_assignment",source)
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)

houses=[
 {"id":"house_a","profile":"occupied","rooms":[
     {"id":"kitchen","type":"kitchen","objects":[
         {"id":"fridge","role":"appliance","material_id":"LL_MAT_ENAMEL_AGED_001"},
         {"id":"cabinet","role":"cabinet","material_id":"LL_MAT_WOOD_WORN_001"}]},
     {"id":"living","type":"living","objects":[
         {"id":"sofa","role":"upholstery","material_id":"LL_MAT_FABRIC_MOSS_001"}]}]},
 {"id":"house_b","profile":"recently_vacant","rooms":[
     {"id":"kitchen","type":"kitchen","objects":[{"id":"fridge","role":"appliance"}]}]},
 {"id":"house_c","profile":"unoccupied","rooms":[
     {"id":"garage","type":"garage","objects":[{"id":"toolbox","role":"tool"}]}]},
 {"id":"house_d","profile":"neglected","rooms":[
     {"id":"basement","type":"basement","objects":[{"id":"shelf","role":"storage"}]}]},
]

a=mod.condition_manifest(41007,"district_01",houses)
assert a==mod.condition_manifest(41007,"district_01",houses)
flipped=deepcopy(houses);flipped.reverse()
for h in flipped:
    h["rooms"].reverse()
    for room in h["rooms"]:room["objects"].reverse()
assert a==mod.condition_manifest(41007,"district_01",flipped)
assert a!=mod.condition_manifest(41008,"district_01",houses)
assert len(a["houses"])==4
for house in a["houses"]:
    assert 0<=house["condition_level"]<=3
    if house["profile"]=="occupied":assert house["condition_level"]<=1
    if house["profile"]=="unoccupied":assert house["condition_level"]>=1
    if house["profile"]=="neglected":assert house["condition_level"]>=2
    for room in house["rooms"]:
        for item in room["objects"]:
            assert item["condition_name"]==mod.CONDITIONS[item["condition_level"]]
try:
    mod.condition_manifest(41007,"district_01",houses+houses[:1])
except ValueError:
    pass
else:raise AssertionError("duplicate house accepted")
print("LL_NEIGHBORHOOD_CONDITIONS_PASS stable IDs, ordering, seed changes and 4 house profiles")
