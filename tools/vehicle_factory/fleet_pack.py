"""Fleet packer: reuse tested Golden Vehicle fixed-pivot exporter for every job."""
import argparse
import hashlib
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from pack import process

def pack_jobs(plan_path,raw_root,output_root):
    plan=json.loads(plan_path.read_text())
    output_root.mkdir(parents=True,exist_ok=True)
    completed=[]
    skipped=[]
    for job in plan["jobs"]:
        source=raw_root/job["job_id"]
        if not (source/"manifest.json").exists():
            skipped.append(job["job_id"])
            continue
        destination=output_root/job["job_id"]
        manifest=process(source,destination)
        manifest.update(job_id=job["job_id"],model=job["model"],
            palette_id=job["palette_id"],paint_hex=job["paint_hex"],
            condition_level=job["condition_level"],
            world_dimensions_m=job["dimensions_m"],
            source_ortho_scale=json.loads((source/"manifest.json").read_text())["ortho_scale"],
            status="PACKED_TECHNICAL_CANDIDATE_NOT_GOLDEN_APPROVED_OR_PLAYABLE")
        (destination/"manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")
        completed.append(dict(job_id=job["job_id"],asset_id=job["asset_id"],
            model=job["model"],palette_id=job["palette_id"],
            condition=job["condition_level"],
            manifest=str((destination/"manifest.json").relative_to(output_root)),
            atlas_sha256=hashlib.sha256((destination/manifest["pixel_refined_atlas"]).read_bytes()).hexdigest()))
    report=dict(schema_version=1,
        plan_sha256=plan["plan_sha256"],total_planned=len(plan["jobs"]),
        technical_candidate_count=len(completed),unrendered_count=len(skipped),
        status="PACKED_CANDIDATES_ONLY_NO_VISUAL_APPROVAL_NO_GODOT_INTEGRATION",
        completed=completed,unrendered_job_ids=skipped)
    (output_root/"batch_report.json").write_text(json.dumps(report,indent=2)+"\n")
    print("LL_FLEET_PACK_BATCH_DONE",len(completed),len(skipped),flush=True)
    return report

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--plan",type=Path,required=True)
    p.add_argument("--input",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    pack_jobs(a.plan,a.input,a.output)

if __name__=="__main__":main()
