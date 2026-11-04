#!/usr/bin/env python3
"""Validate proposed LAST LIGHT content definitions. Python stdlib only.

Does not import or generate game assets. Non-zero exit on malformed IDs/references.
"""
import argparse
import json
import re
import sys
from pathlib import Path

PARTS = ("items", "props", "buildings", "vehicles", "enemies", "loot_profiles")
ID_RE = re.compile(r"^(item|prop|building|vehicle|entity|loot)\\.[a-z][a-z0-9_]*(?:\\.[a-z][a-z0-9_]*)+$")
PREFIX = {"items":"item.","props":"prop.","buildings":"building.","vehicles":"vehicle.","enemies":"entity.","loot_profiles":"loot."}

def validate(data):
    errors = []
    if data.get("schema") != 1:
        errors.append("schema must equal 1")
    allowed = set(data.get("capability_vocabulary", []))
    if len(allowed) != len(data.get("capability_vocabulary", [])):
        errors.append("duplicate capability vocabulary values")
    index = {}
    for section in PARTS:
        records = data.get(section)
        if not isinstance(records, list):
            errors.append(f"{section}: expected array")
            continue
        for offset, rec in enumerate(records):
            key = f"{section}[{offset}]"
            if not isinstance(rec, dict):
                errors.append(f"{key}: expected object")
                continue
            ident = rec.get("id")
            if not isinstance(ident, str) or not ID_RE.fullmatch(ident) or not ident.startswith(PREFIX[section]):
                errors.append(f"{key}: bad id: {ident!r}")
                continue
            if ident in index:
                errors.append(f"{key}: duplicate id {ident}")
            index[ident] = section
            if not isinstance(rec.get("name", ident), str):
                errors.append(f"{ident}: name must be string")
            for capability in rec.get("capabilities", []):
                if capability not in allowed:
                    errors.append(f"{ident}: unknown capability {capability}")
            if section == "items":
                if not isinstance(rec.get("weight_kg"), (int, float)) or rec["weight_kg"] < 0:
                    errors.append(f"{ident}: invalid weight_kg")
                if type(rec.get("stack_max")) is not int or rec["stack_max"] < 1:
                    errors.append(f"{ident}: invalid stack_max")
                visual = rec.get("visual")
                if not isinstance(visual, dict) or not all(isinstance(visual.get(v), str) for v in ("icon","ground")):
                    errors.append(f"{ident}: icon and ground art refs required")
    for building in data.get("buildings", []):
        ident = building.get("id", "<missing>")
        if index.get(building.get("loot_profile")) != "loot_profiles":
            errors.append(f"{ident}: unknown loot_profile")
        if not isinstance(building.get("rooms"), list) or not building["rooms"]:
            errors.append(f"{ident}: rooms missing")
        for prop in building.get("starter_props", []):
            if index.get(prop) != "props":
                errors.append(f"{ident}: unknown starter prop {prop}")
    for loot in data.get("loot_profiles", []):
        for item in loot.get("entries", []):
            if index.get(item) != "items":
                errors.append(f"{loot.get('id')}: unknown loot item {item}")
    return errors

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("catalog", nargs="?",default="data/catalog/starter_v1.json")
    args = parser.parse_args()
    try:
        data = json.loads(Path(args.catalog).read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        print("CATALOG FAIL:",e,file=sys.stderr)
        return 1
    errors = validate(data)
    if errors:
        for e in errors:
            print("CATALOG ERROR:", e, file=sys.stderr)
        return 1
    print("CATALOG PASS: "+", ".join(f"{part}={len(data[part])}" for part in PARTS)+"; design-only, not imported into Godot")
    return 0
if __name__=="__main__":
    raise SystemExit(main())
