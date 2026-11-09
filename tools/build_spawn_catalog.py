#!/usr/bin/env python3
"""Build data/sandbox/spawn_catalog_v1.json from the F01-F12 family queues.

Rules (GM00 Mission 3/5):
- Never mint A00 canonical IDs. Queue work orders carry `candidate_key` with
  identity_status NEEDS_CANONICAL_REGISTRY_RECONCILIATION; we copy that key and
  status verbatim and set canonical_asset_id = null.
- Spawn IDs are provisional ("prov.<family>.<slug>") and clearly labelled.
- Gameplay items that already exist as prototype definitions (proto.*) are
  taken from data/neighborhood/survival_pilot_v1.json.
Deterministic: same inputs -> byte-identical output.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUEUES = ROOT / "docs" / "production" / "queues"
OUT = ROOT / "data" / "sandbox" / "spawn_catalog_v1.json"
PILOT = ROOT / "data" / "neighborhood" / "survival_pilot_v1.json"

# name -> (category, behavior)
CLASSIFY = {
    # F01
    "chair": ("Furniture", "furniture"), "sofa": ("Furniture", "furniture"), "bed": ("Furniture", "furniture"),
    "single bed": ("Furniture", "furniture"), "table": ("Furniture", "furniture"),
    "cabinet": ("Containers", "container"), "drawer": ("Containers", "container"),
    "kitchen drawer": ("Containers", "container"), "locker": ("Containers", "container"),
    "shelf": ("Containers", "container"), "crate": ("Containers", "container"),
    "refrigerator": ("Appliances", "container"), "freezer": ("Appliances", "container"),
    "cooker": ("Appliances", "machine"), "washer": ("Appliances", "machine"), "sink": ("Appliances", "furniture"),
    # F02
    "walls": ("Building components", "wall"), "corners": ("Building components", "wall"),
    "floors": ("Building components", "floor"), "doors": ("Building components", "door"),
    "windows": ("Building components", "window"), "stairs": ("Building components", "furniture"),
    "rooftops": ("Building components", "floor"), "fences": ("Building components", "wall"),
    "gates": ("Building components", "door"), "door window": ("Building components", "door"),
    "roof corner": ("Building components", "floor"), "shopfront": ("Building components", "window"),
    # F03 terrain props
    "potholes": ("Environmental props", "prop"), "puddles": ("Environmental props", "prop"),
    "curbs and transitions": ("Environmental props", "prop"),
    # F04
    "deciduous tree": ("Vegetation", "tree"), "pine": ("Vegetation", "tree"), "oak": ("Vegetation", "tree"),
    "sapling": ("Vegetation", "plant"), "dead tree": ("Vegetation", "tree"), "hedge": ("Vegetation", "tree"),
    "bush": ("Vegetation", "plant"), "berry bush": ("Vegetation", "plant"), "crop": ("Vegetation", "plant"),
    "wheat": ("Vegetation", "plant"), "weed": ("Vegetation", "plant"), "reed": ("Vegetation", "plant"),
    "vine": ("Vegetation", "plant"), "stump": ("Environmental props", "prop"), "flowers": ("Vegetation", "plant"),
    # F05
    "neutral underwear character": ("Characters", "character"), "human bodies": ("Characters", "character"),
    "backpack": ("Items", "pickup"), "bags and equipped items": ("Items", "pickup"),
    "held tool": ("Tools", "pickup"),
    # F06
    "civilian": ("Zombies", "zombie"), "worker": ("Zombies", "zombie"), "medical": ("Zombies", "zombie"),
    "security": ("Zombies", "zombie"), "police": ("Zombies", "zombie"), "fire rescue": ("Zombies", "zombie"),
    "elderly": ("Zombies", "zombie"), "weak": ("Zombies", "zombie"), "hospital orderly": ("Zombies", "zombie"),
    "injured crawler": ("Zombies", "zombie"), "wounded and crawling actor variants": ("Zombies", "zombie"),
    # F07
    "cattle": ("Animals", "animal"), "v8 adult cow": ("Animals", "animal"), "calf": ("Animals", "animal"),
    "chicken": ("Animals", "animal"), "pig": ("Animals", "animal"), "sheep": ("Animals", "animal"),
    "turkey": ("Animals", "animal"), "deer": ("Animals", "animal"), "mouse": ("Animals", "animal"),
    "rabbit": ("Animals", "animal"), "raccoon": ("Animals", "animal"), "rat": ("Animals", "animal"),
    # F08
    "generator": ("Machinery", "machine"), "portable generator": ("Machinery", "machine"),
    "compressor": ("Machinery", "machine"), "water pump": ("Machinery", "machine"),
    "conveyor": ("Machinery", "machine"), "conveyor segment": ("Machinery", "machine"),
    "press": ("Machinery", "machine"), "forklift": ("Vehicles", "vehicle"), "motor": ("Machinery", "machine"),
    "furnace": ("Machinery", "machine"), "air conditioner": ("Machinery", "machine"),
    # F09
    "screwdriver": ("Tools", "pickup"), "cross screwdriver": ("Tools", "pickup"), "awl": ("Tools", "pickup"),
    "wrench": ("Tools", "pickup"), "saw": ("Tools", "pickup"), "shovel": ("Tools", "pickup"),
    "crowbar": ("Weapons", "weapon"), "hammer": ("Weapons", "weapon"), "hatchet": ("Weapons", "weapon"),
    "axe": ("Weapons", "weapon"), "knife": ("Weapons", "weapon"), "cleaver": ("Weapons", "weapon"),
    "machete": ("Weapons", "weapon"), "pitchfork": ("Weapons", "weapon"),
    # F10
    "hatchback": ("Vehicles", "vehicle"), "v6 1 inspired compact hatchback": ("Vehicles", "vehicle"),
    "sedan": ("Vehicles", "vehicle"), "wagon": ("Vehicles", "vehicle"), "suv": ("Vehicles", "vehicle"),
    "pickup": ("Vehicles", "vehicle"), "coupe": ("Vehicles", "vehicle"), "van": ("Vehicles", "vehicle"),
    "truck": ("Vehicles", "vehicle"), "ambulance": ("Vehicles", "vehicle"), "bus": ("Vehicles", "vehicle"),
    "tractor": ("Vehicles", "vehicle"), "wreck": ("Vehicles", "vehicle"),
}
# Pipeline/material-only records that are not spawnable world objects.
SKIP = {"physique morphs", "hair", "clothing layers", "footwear", "two morphs", "original firearm exterior props",
        "small house", "garage", "60 building archetype compositions",
        # F03 terrain tiles are ground materials, not spawnable world objects
        "asphalt", "roads", "sidewalks", "grass", "dirt", "mud", "gravel", "sand", "water", "snow",
        "asphalt to grass", "shoreline",
        "canonical catalog to be reconciled"}  # queue annotation, not an object
SIZES = {"furniture": [1.2, 0.8], "container": [1.0, 0.7], "machine": [1.2, 1.0], "wall": [2.0, 0.3],
         "floor": [2.0, 2.0], "door": [1.0, 0.3], "window": [1.4, 0.3], "prop": [1.0, 1.0], "tree": [0.9, 0.9],
         "plant": [0.8, 0.8], "character": [0.6, 0.6], "zombie": [0.6, 0.6], "animal": [0.8, 0.6],
         "vehicle": [2.2, 4.2], "pickup": [0.4, 0.4], "weapon": [0.4, 0.4]}
SOLID = {"furniture", "container", "machine", "wall", "door", "window", "tree", "vehicle", "character"}
WEAPON_DAMAGE = {"axe": 3, "machete": 2, "hatchet": 2, "crowbar": 2, "hammer": 2, "cleaver": 2, "knife": 1, "pitchfork": 2}


def norm(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def slug(text: str) -> str:
    return norm(text).replace(" ", "-")


def main() -> int:
    entries = {}
    pilot = json.loads(PILOT.read_text())
    for item_id, item in sorted(pilot["items"].items()):
        entries[item_id] = {
            "spawn_id": item_id, "name": item["name"], "category": "Items", "behavior": "pickup",
            "family": None, "candidate_key": None, "identity_status": "PROTOTYPE_GAMEPLAY_DEFINITION",
            "canonical_asset_id": None, "source": "data/neighborhood/survival_pilot_v1.json",
            "gameplay_item_id": item_id, "art_status": "PROVISIONAL_PROCEDURAL"}
    for path in sorted(QUEUES.glob("F*_v1.json")):
        queue = json.loads(path.read_text())
        fam = queue["queue_id"]
        if fam in ("F11", "F12"):
            continue  # materials and render bridge: not spawnable objects
        sources = []
        for wo in queue.get("calibration_work_orders", []):
            sources.append((wo["candidate_key"].split(":", 1)[1].replace("-", " "), wo["candidate_key"], wo["identity_status"], wo["work_order_id"]))
        for ref in queue.get("reference_archetypes", []):
            for part in str(ref).split(";"):
                sources.append((part.split(" from ")[0].strip(), None, "REFERENCE_ARCHETYPE_ONLY", None))
        for name, key, status, work_order in sources:
            n = norm(name)
            if n in SKIP or not n:
                continue
            if n not in CLASSIFY:
                print("unclassified:", fam, n, file=sys.stderr)
                return 1
            category, behavior = CLASSIFY[n]
            spawn_id = "prov.%s.%s" % (fam.lower(), slug(name))
            if spawn_id in entries:
                if key and not entries[spawn_id]["candidate_key"]:
                    entries[spawn_id].update({"candidate_key": key, "identity_status": status, "work_order_id": work_order})
                continue
            entry = {"spawn_id": spawn_id, "name": name[:1].upper() + name[1:], "category": category,
                     "behavior": behavior, "family": fam, "candidate_key": key, "identity_status": status,
                     "work_order_id": work_order, "canonical_asset_id": None,
                     "source": "docs/production/queues/%s" % path.name, "art_status": "PROVISIONAL_PROCEDURAL",
                     "size": SIZES[behavior], "solid": behavior in SOLID}
            if behavior == "weapon":
                entry["damage"] = WEAPON_DAMAGE.get(n, 2)
            entries[spawn_id] = entry
    out = {
        "schema": "last_light.spawn_catalog.v1",
        "status": "PROVISIONAL_NO_A00_CANONICAL_IDS",
        "generated_by": "tools/build_spawn_catalog.py",
        "notes": "No entry is Golden-approved. canonical_asset_id stays null until the A00 registry reconciles the queue candidate_key.",
        "categories": ["Items", "Weapons", "Tools", "Furniture", "Containers", "Appliances", "Building components",
                       "Vehicles", "Zombies", "Characters", "Animals", "Vegetation", "Environmental props", "Machinery"],
        "entries": [entries[k] for k in sorted(entries)],
    }
    missing = [c for c in out["categories"] if not any(e["category"] == c for e in out["entries"])]
    if missing:
        print("empty categories:", missing, file=sys.stderr)
        return 1
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")
    print("wrote %d entries to %s" % (len(out["entries"]), OUT.relative_to(ROOT)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
