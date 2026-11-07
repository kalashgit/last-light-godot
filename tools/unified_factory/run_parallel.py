"""LAST LIGHT bounded parallel ORIGINAL sprite render runner.

This orchestrates the existing 300-ID bpy renderer and its real pack/validate
steps. It does not create fictional geometry or claim Golden visual approval.

Usage:
  python tools/unified_factory/run_parallel.py --dry-run --limit 32
  python tools/unified_factory/run_parallel.py --limit 12 --workers 2 --resume
  python tools/unified_factory/run_parallel.py --workers 4 --resume --limit 300

Review and approve family visuals before scaling beyond the test batch.
"""
import argparse
import concurrent.futures
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(Path(__file__).resolve().parent))
from batch_plan import source_registry, canonical_hash

RENDERER=ROOT/"tools/asset_factory/render_batch.py"
PACKER=ROOT/"tools/asset_factory/pack.py"
VALIDATOR=ROOT/"tools/asset_factory/validate.py"


def selected_ids(limit=0, include=None):
    names=sorted(a["id"] for a in source_registry())
    if include:
        chosen=list(include)
        if len(set(chosen))!=len(chosen) or set(chosen)-set(names):
            raise ValueError("invalid or duplicate selected asset IDs")
        return sorted(chosen)
    if not 0<=limit<=len(names):
        raise ValueError("limit must be 0..300")
    return names[:limit] if limit else names


def plan_jobs(ids, chunk_size=32, workers=2, threads=2):
    if not ids or len(set(ids))!=len(ids):raise ValueError("empty or duplicate IDs")
    if not 1<=chunk_size<=256:raise ValueError("invalid chunk size 1..256")
    if not 1<=workers<=8:raise ValueError("max_workers should be 1..8 within observed RAM")
    if not 1<=threads<=16:raise ValueError("threads should be 1..16")
    groups=[]
    for offset in range(0,len(ids),chunk_size):
        chunk=ids[offset:offset+chunk_size]
        groups.append(dict(id="sprite_shard_%04d" % (len(groups)+1),
                           ids=chunk,asset_count=len(chunk),
                           content_sha256=canonical_hash(chunk)))
    return dict(schema=1,asset_count=len(ids),shard_count=len(groups),
                worker_count=workers,threads_per_blender=threads,
                status="PLANNED_RENDER_ONLY_NO_GOLDEN_VISUAL_APPROVAL",
                shards=groups,selection_sha256=canonical_hash(ids))


def _do_shard(shard, folder, blender, threads, resume):
    ids_path=folder/(shard["id"]+".json")
    manifest_path=folder/(shard["id"]+"_result.json")
    log_path=folder/(shard["id"]+".log")
    ids_path.write_text(json.dumps(shard["ids"],indent=2)+"\n")
    command=[blender,"-b","--factory-startup","-t",str(threads),
             "--python",str(RENDERER),"--","--output",str(folder),
             "--ids-file",str(ids_path),"--batch-manifest",str(manifest_path),
             "--threads",str(threads)]
    if resume:
        command.append("--resume")
    started=time.monotonic()
    with log_path.open("w") as log:
        result=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,check=False)
    elapsed=time.monotonic()-started
    log_text=log_path.read_text(errors="replace")
    if result.returncode or "Traceback (most recent call last)" in log_text or "FACTORY DONE" not in log_text:
        raise RuntimeError(shard["id"]+" failed: "+log_text[-1600:])
    if not manifest_path.is_file():
        raise RuntimeError(shard["id"]+" did not write its own manifest")
    contents=json.loads(manifest_path.read_text())
    observed={obj["id"] for obj in contents.get("objects",[])}
    if observed != set(shard["ids"]):
        raise RuntimeError(shard["id"]+" produced wrong IDs")
    return dict(shard=shard["id"],duration_s=round(elapsed,3),
                item_count=len(observed),manifest=str(manifest_path),
                source_hash=contents["source_hash"])


def execute(plan, raw, output, sheets, blender="blender", resume=False, pack=True):
    if plan["status"]!="PLANNED_RENDER_ONLY_NO_GOLDEN_VISUAL_APPROVAL":
        raise ValueError("refusing unknown plan schema")
    raw.mkdir(parents=True,exist_ok=True)
    output.parent.mkdir(parents=True,exist_ok=True)
    sheets.parent.mkdir(parents=True,exist_ok=True)
    started=time.monotonic()
    results=[]
    # Memory-bound Blender processes; never start 300 simultaneous Blender jobs.
    with concurrent.futures.ThreadPoolExecutor(max_workers=plan["worker_count"]) as pool:
        futures=[pool.submit(_do_shard,s,raw,blender,plan["threads_per_blender"],resume)
                 for s in plan["shards"]]
        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())
    source_hashes={r["source_hash"] for r in results}
    if len(source_hashes)!=1:
        raise RuntimeError("shards rendered different source revisions; reject mixed output")
    objects=[]
    for result in sorted(results,key=lambda x:x["shard"]):
        record=json.loads(Path(result["manifest"]).read_text())
        objects.extend(record["objects"])
    expected={a for shard in plan["shards"] for a in shard["ids"]}
    ids=[obj["id"] for obj in objects]
    if len(ids)!=len(set(ids)) or set(ids)!=expected:
        raise RuntimeError("shard assembly has duplicate or missing assets")
    merged=dict(schema=1,objects=sorted(objects,key=lambda x:x["id"]),
                elapsed_seconds=round(time.monotonic()-started,3),
                source_hash=next(iter(source_hashes)),
                blender="bounded_parallel_shards")
    (raw/"batch.json").write_text(json.dumps(merged,indent=2)+"\n")
    if pack:
        subprocess.run([sys.executable,str(PACKER),str(raw),
                        "--output",str(output),"--sheets",str(sheets)],check=True)
        subprocess.run([sys.executable,str(VALIDATOR),str(output),
                        "--count",str(len(expected))],check=True)
    report=dict(schema=1,items=len(ids),shards=len(results),
                completed_frames=sum(len(o["frames"]) for o in objects),
                elapsed_s=round(time.monotonic()-started,3),
                workers=plan["worker_count"],threads=plan["threads_per_blender"],
                status=("RENDERED_PACKED_TECHNICAL_QA_PASSED_GOLDEN_REVIEW_PENDING"
                        if pack else "RENDERED_CANDIDATES_PENDING_PACK_AND_VISUAL_QA"),
                # Individual shard timing allows a measured rather than invented throughput.
                shard_results=sorted(results,key=lambda r:r["shard"]))
    (raw/"run_report.json").write_text(json.dumps(report,indent=2)+"\n")
    print("LL_PARALLEL_FACTORY_PASS",len(ids),report["completed_frames"],
          round(report["elapsed_s"],2),flush=True)
    return report


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--raw",type=Path,default=ROOT/"build/unified_factory/sharded_raw")
    p.add_argument("--output",type=Path,default=ROOT/"build/unified_factory/sharded_packed")
    p.add_argument("--sheets",type=Path,default=ROOT/"build/unified_factory/review_sheets")
    p.add_argument("--blender",default="blender")
    p.add_argument("--workers",type=int,default=2)
    p.add_argument("--threads",type=int,default=2)
    p.add_argument("--chunk-size",type=int,default=8)
    p.add_argument("--limit",type=int,default=0)
    p.add_argument("--asset-ids",default="")
    p.add_argument("--resume",action="store_true")
    p.add_argument("--dry-run",action="store_true")
    p.add_argument("--no-pack",action="store_true")
    a=p.parse_args()
    ids=selected_ids(a.limit,
        [v.strip() for v in a.asset_ids.split(",")] if a.asset_ids else None)
    plan=plan_jobs(ids,a.chunk_size,a.workers,a.threads)
    a.raw.mkdir(parents=True,exist_ok=True)
    (a.raw/"plan.json").write_text(json.dumps(plan,indent=2)+"\n")
    if a.dry_run:
        print("LL_PARALLEL_PLAN_PASS",len(ids),plan["shard_count"],
              "candidate IDs, no Blender jobs launched")
        return
    execute(plan,a.raw,a.output,a.sheets,a.blender,a.resume,not a.no_pack)


if __name__=="__main__":
    main()
