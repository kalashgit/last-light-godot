"""Actual Blender smoke test of all eight original geometry recipes.

Not a mock. Called inside headless Blender in a PR-only GitHub runner.
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parent))
from plan import catalog, CATALOG_SHA256, TOTAL
from generate import export_one

def main():
    argv=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    p=argparse.ArgumentParser()
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args(argv)
    a.output.mkdir(parents=True,exist_ok=True)
    items=list(catalog())[:8]
    if len({x["archetype"] for x in items})!=8:
        raise ValueError("Smoke missing an asset archetype")
    selected=[]
    for spec in items:
        actual=export_one(spec,a.output)
        actual["family"]=spec["family"]
        actual["archetype"]=spec["archetype"]
        selected.append(actual)
    plan={
        "schema_version":1,"status":"READY","source_plan_sha256":CATALOG_SHA256,
        "source_count":TOTAL,"completed_before":[],"selected":selected,
        "golden_approved":False,
    }
    (a.output/"render_plan.json").write_text(json.dumps(plan,indent=2)+"\n")
    print("FOUNDRY_ALL_8_ORIGINAL_RECIPES_PASS", ",".join(s["archetype"] for s in selected),flush=True)

if __name__=="__main__":
    main()
