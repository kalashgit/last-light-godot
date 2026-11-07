"""Universal LAST LIGHT world-object contract V1.

The factory emits canonical *template* definitions. Game instances persist their own
door states, container inventory, health, barricades, position and environmental wear.
This module validates source contracts; it does not implement game physics or AI.
"""
import argparse
import json
from pathlib import Path

KINDS={"furniture","item","tile","door","window","structure","vehicle","character","effect"}
COLLISION={"solid","passable","partial"}
SIGHT={"blocks","partial","transparent"}
MOVE={"static","pickup","push","drag","carry"}
STAGES=("intact","damaged","broken")
CONDITIONS=(0,1,2,3)

def need(test,msg):
    if not test:
        raise ValueError(msg)

def number(x):
    return type(x) in (int,float) and x==x and abs(x)!=float("inf")

def nonnegative(x):
    return number(x) and x>=0

def positive(x):
    return number(x) and x>0

def validate_object(obj):
    name=obj.get("template_id","<missing template_id>")
    def check(expr,message):
        need(expr,f"{name}: {message}")
    check(isinstance(name,str) and name.startswith("ll_"),"stable template ID required")
    check(obj.get("schema_version")==1,"schema 1 required")
    check(obj.get("kind") in KINDS,"unknown kind")
    check(isinstance(obj.get("family"),str) and obj["family"],"family missing")
    visual=obj.get("appearance",{})
    check(isinstance(visual,dict),"appearance missing")
    check(isinstance(visual.get("geometry_template"),str)
          and visual["geometry_template"],"geometry template missing")
    check(isinstance(visual.get("materials"),list) and visual["materials"]
          and all(isinstance(x,str) and x for x in visual["materials"]),
          "material library IDs required")
    check(visual.get("conditions")==list(CONDITIONS),"all four wear levels required")
    check(visual.get("tile_px")==[80,40],"invalid LAST LIGHT projection tile scale")
    check(isinstance(visual.get("animations"),list),"animation names must be an array")
    physical=obj.get("physical",{})
    check(isinstance(physical,dict),"physical component required")
    dims=physical.get("dimensions_m")
    check(isinstance(dims,list) and len(dims)==3
          and all(positive(x) for x in dims),"dimensions in metres invalid")
    check(nonnegative(physical.get("empty_mass_kg")),"invalid empty mass")
    collision=physical.get("collision",{})
    check(isinstance(collision,dict) and collision.get("mode") in COLLISION,"invalid collision mode")
    shapes=collision.get("shapes",[])
    check(isinstance(shapes,list),"shapes must be array")
    if collision["mode"]!="passable":
        check(len(shapes)>0,"solid and partial objects require collision shapes")
    for sh in shapes:
        check(sh.get("kind")=="aabb","only fixed 2D AABBs in V1")
        check(isinstance(sh.get("center_m"),list) and len(sh["center_m"])==2
              and all(number(n) for n in sh["center_m"]),"collision center invalid")
        check(isinstance(sh.get("size_m"),list) and len(sh["size_m"])==2
              and all(positive(n) for n in sh["size_m"]),"collision extents invalid")
        check(all(sh["size_m"][i] <= dims[i]+.001 for i in (0,1)),
              "collision larger than physical footprint")
    sight=physical.get("sight",{})
    check(isinstance(sight,dict) and sight.get("mode") in SIGHT,"sight mode required")
    check(nonnegative(sight.get("attenuation")) and sight["attenuation"]<=1,
          "sight attenuation must be 0..1")
    sound=physical.get("sound",{})
    check(isinstance(sound,dict) and isinstance(sound.get("material"),str)
          and sound["material"],"sound material required")
    check(nonnegative(sound.get("break_noise")) and sound["break_noise"]<=1,
          "break noise must be 0..1")
    move=physical.get("movability",{})
    check(isinstance(move,dict) and isinstance(move.get("modes"),list) and move["modes"]
          and all(x in MOVE for x in move["modes"]), "movability modes invalid")
    check(nonnegative(move.get("strength_required")),"strength required invalid")
    if "static" in move["modes"]:
        check(len(move["modes"])==1,"static conflicts with movable modes")
    components=obj.get("components",{})
    check(isinstance(components,dict),"components must be an object")
    storage=components.get("storage")
    if storage is not None:
        check(isinstance(storage,dict) and storage.get("hollow") is True,
              "container requires physically hollow construction")
        check(isinstance(storage.get("compartments"),list) and storage["compartments"],
              "container must declare distinct compartments")
        ids=[]
        for part in storage["compartments"]:
            check(isinstance(part.get("id"),str) and part["id"],"compartment ID missing")
            ids.append(part["id"])
            check(isinstance(part.get("bound_to_door"),str) and part["bound_to_door"],
                  "compartment must bind to a door/drawer or always_open socket")
            for key in ("slots","capacity_kg","capacity_l"):
                check(positive(part.get(key)), "compartment "+key+" must be positive")
        check(len(set(ids))==len(ids),"duplicate compartment IDs")
    interaction=components.get("interaction")
    if interaction is not None:
        check(isinstance(interaction,dict),"interaction must be object")
        check(isinstance(interaction.get("actions"),list) and interaction["actions"],
              "interactive object needs actions")
        check(positive(interaction.get("reach_m")) and interaction["reach_m"]<=3,
              "interaction reach must be practical metres")
        for action in interaction["actions"]:
            check(isinstance(action.get("verb"),str) and action["verb"],"action verb missing")
            check(nonnegative(action.get("duration_s")),"action duration negative")
            check(isinstance(action.get("interruptible"),bool),
                  "actions require interruption decision")
        if storage:
            check(any(a["verb"]=="search" for a in interaction["actions"]),
                  "storage requires a search interaction")
    destruction=components.get("destruction")
    if destruction is not None:
        check(isinstance(destruction,dict) and destruction.get("stages")==list(STAGES),
              "damage stages must be intact, damaged, broken")
        check(positive(destruction.get("max_hp")),"destructibility HP missing")
    placement=components.get("placement")
    if placement is not None:
        check(isinstance(placement,dict) and placement.get("snap") in ("floor_tile","wall_edge","free","grid"),
              "invalid placement snap")
        check(isinstance(placement.get("adjacent_access_cell_required"),bool),
              "access-cell requirement must be bool")
    barricade=components.get("barricade")
    if barricade is not None:
        check(obj.get("kind") in ("door","window","structure"),
              "barricade anchor only permitted on openings/structures")
        check(isinstance(barricade.get("anchor_slots"),list)
              and barricade["anchor_slots"],"barricade anchor slots missing")
        check(isinstance(barricade.get("removable"),bool),"barricade removability required")
    if obj["kind"]=="tile":
        check(collision["mode"]=="passable" or "structure" in obj.get("tags",[]),
              "ordinary floor tiles must not block movement")
        check(storage is None,"tiles cannot silently contain inventory")
    if obj["family"] in ("refrigerator","cabinet","wardrobe","dresser","locker","chest"):
        check(storage is not None and storage["hollow"] is True,
              "storage furniture must have a real hollow interior")
    check(obj.get("qa_status")=="contract_candidate_not_gameplay_integrated",
          "candidate status must remain explicit")
    return True

def validate_catalog(data):
    need(data.get("schema_version")==1,"unsupported catalog schema")
    items=data.get("templates")
    need(isinstance(items,list) and bool(items),"missing object templates")
    ids=[o.get("template_id") for o in items]
    need(len(set(ids))==len(ids),"duplicate object template IDs")
    for obj in items:
        validate_object(obj)
    return {"schema":1,"status":"CONTRACT_VALIDATED_NOT_ENGINE_INTEGRATED",
            "templates":len(items),
            "hollow_storage":sum("storage" in o["components"] for o in items),
            "tile_count":sum(o["kind"]=="tile" for o in items)}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("file",type=Path)
    a=p.parse_args()
    report=validate_catalog(json.loads(a.file.read_text()))
    print("LL_WORLD_OBJECT_CONTRACT_PASS",json.dumps(report,sort_keys=True))

if __name__=="__main__":
    main()
