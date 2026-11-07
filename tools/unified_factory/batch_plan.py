"""Deterministic batch plan, not a claim of rendered/approved assets.
Runs with Python stdlib only; never calls Notion, Blender, AI APIs, or spending APIs.
"""
import argparse
import collections
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CATALOG = ROOT / "tools" / "asset_factory" / "catalog.py"
CONDITIONS = {0: "maintained", 1: "used", 2: "weathered", 3: "severely_neglected"}

def canonical_hash(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

def source_registry():
    spec = importlib.util.spec_from_file_location("last_light_catalog", CATALOG)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.registry()

def build_plan(records, conditions=(0,1,2,3), palettes=1, shapes=1, batch_size=128):
    """Immutable job IDs; order-insensitive input; explicit candidate vs verified status."""
    if not 1 <= batch_size <= 1024:
        raise ValueError("batch_size must be 1..1024")
    if palettes < 1 or shapes < 1:
        raise ValueError("variants must be positive")
    if len(set(conditions)) != len(conditions) or any(c not in CONDITIONS for c in conditions):
        raise ValueError("invalid or duplicate environmental conditions")
    ids = [r["id"] for r in records]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate catalog ID")
    output = []
    for rec in sorted(records, key=lambda r:r["id"]):
        for condition in sorted(conditions):
            for palette in range(palettes):
                for shape in range(shapes):
                    identity = dict(asset_id=rec["id"], condition=condition, palette_variant=palette,
                                    geometry_variant=shape, asset_family=rec["family"],
                                    material_family=rec["material"])
                    key = canonical_hash(identity)[:20]
                    output.append(dict(job_id="lljob_"+key, **identity,
                                       category=rec["category"],
                                       target="world_sprite" if rec["category"] != "furniture" else "furniture",
                                       status="planned_not_generated_not_approved"))
    if len({j["job_id"] for j in output}) != len(output):
        raise ValueError("job hash collision")
    # Sort by stable job_id, making batch boundaries independent of input order.
    output.sort(key=lambda j:j["job_id"])
    batches = []
    for n,offset in enumerate(range(0,len(output),batch_size)):
        subset = output[offset:offset+batch_size]
        batches.append(dict(batch_id=f"llbatch_{n+1:04}", count=len(subset),
                            job_ids=[j["job_id"] for j in subset],
                            work_hash=canonical_hash(subset)))
    categories=dict(sorted(collections.Counter(j["category"] for j in output).items()))
    families=len({r["family"] for r in records})
    return dict(schema_version=1, factory="LAST_LIGHT_UNIFIED_FACTORY",
                record_count=len(records), unique_family_count=families,
                candidate_job_count=len(output), batch_size=batch_size,
                conditions=list(sorted(conditions)),
                palettes=palettes, geometry_variants=shapes,
                status="PLANNED_ONLY_NO_RENDER_OR_GODOT_INTEGRATION",
                categories=categories, batches=batches, jobs=output,
                plan_hash=canonical_hash(dict(batches=batches, jobs=output)))

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--output",type=Path,default=Path("build/unified_factory/plan.json"))
    p.add_argument("--batch-size",type=int,default=128)
    p.add_argument("--conditions",default="0,1,2,3")
    p.add_argument("--palettes",type=int,default=1)
    p.add_argument("--geometry-variants",type=int,default=1)
    p.add_argument("--limit",type=int,default=0)
    args=p.parse_args()
    records=source_registry()
    if args.limit: records=sorted(records,key=lambda r:r["id"])[:args.limit]
    plan=build_plan(records,tuple(int(x) for x in args.conditions.split(",")),
                    args.palettes,args.geometry_variants,args.batch_size)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(plan,indent=2)+"\n")
    print(json.dumps({k:plan[k] for k in ("record_count","unique_family_count",
        "candidate_job_count","batch_size","conditions","plan_hash","status")},indent=2))

if __name__=="__main__": main()
