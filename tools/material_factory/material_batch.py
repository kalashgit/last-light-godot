"""Generate all approved-source PBR recipe families for four condition levels, with coverage report.
No claim that 5 source textures cover every physical material or every asset archetype.
"""
import argparse
import hashlib
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"unified_factory"))
from batch_plan import source_registry
from expanded_materials import FAMILIES as EXPANDED_FAMILIES, generate as generate_extra

ROOT=Path(__file__).resolve().parents[2]
GENERATE=ROOT/"tools"/"material_factory"/"generate.py"
SOURCE_MATERIALS=ROOT/"tools"/"material_factory"/"recipes.json"
# Explicit compatibility only; no silent substitute of paper/ceramic/plastic for enamel.
CATALOG_TO_PBR={
 "steel":"oxidized_metal",
 "wood":"wood",
 "fabric":"fabric",
 "sage":"plastic",
 "paper":"paper",
 "amber":"amber_glass",
 "clay":"clay",
 "dark":"rubber",
}
APPLIANCES={"fridge","stove","washer","microwave"}

def coverage(records):
    matched=[];missing=[]
    for a in records:
        family=CATALOG_TO_PBR.get(a["material"])
        if a["material"]=="ivory":
            if a["family"] in APPLIANCES:
                family="painted_metal"
            elif a["category"]=="medical":
                # Medical cartons/cases are packaging/plastics, not porcelain.
                family="plastic"
            else:
                family="ceramic"
        item=dict(asset_id=a["id"],catalog_material=a["material"],pbr_family=family,
                  geometry_family=a["family"],category=a["category"])
        (matched if family else missing).append(item)
    return matched,missing

def produce(out,size=256,conditions=(0,1,2,3),run_generator=True):
    if size not in (256,512,1024):
        raise ValueError("invalid material size")
    if len(set(conditions))!=len(conditions) or any(i not in range(4) for i in conditions):
        raise ValueError("invalid condition selection")
    source=json.loads(SOURCE_MATERIALS.read_text())
    pbr_families={r["family"] for r in source}|set(EXPANDED_FAMILIES)
    if not {"painted_metal","wood","fabric","plastic","oxidized_metal"}.issubset(pbr_families):
        raise ValueError("required original material families missing")
    records=source_registry()
    matched,missing=coverage(records)
    if any(a["pbr_family"] not in pbr_families for a in matched):
        raise ValueError("unresolved map to original source PBR")
    packs=[]
    out.mkdir(parents=True,exist_ok=True)
    for c in sorted(conditions):
        folder=out/f"condition_{c}"
        if run_generator:
            subprocess.run([sys.executable,str(GENERATE),"--condition",str(c),
                            "--size",str(size),"--out",str(folder)],check=True)
        manifest_path=folder/"manifest.json"
        if run_generator and not manifest_path.exists():
            raise RuntimeError("material run omitted manifest")
        if manifest_path.exists():
            m=json.loads(manifest_path.read_text())
            if len(m["items"]) != len(source) or m["condition_level"]!=c:
                raise ValueError("wrong material output/condition")
            for r in m["items"]:
                for p in r["maps"].values():
                    file=folder/p
                    if not file.is_file() or file.stat().st_size < 100:
                        raise ValueError("material source missing: "+str(file))
            packs.append(dict(condition=c,material_count=len(m["items"]),
                              manifest_sha256=hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
                              directory=str(folder.relative_to(out))))
    expanded=generate_extra(out/"expanded",size,conditions) if run_generator else None
    if expanded is not None:
        if expanded["material_count"]!=len(EXPANDED_FAMILIES)*len(conditions):
            raise ValueError("expanded material batch count incorrect")
        for rec in expanded["records"]:
            for p in rec["map_files"].values():
                if not (out/"expanded"/p).is_file():
                    raise ValueError("missing expanded material map: "+p)
    summary=dict(schema_version=2,material_source_recipes=len(source)+len(EXPANDED_FAMILIES),
        baseline_material_map_sets=len(source)*len(conditions) if run_generator else 0,
        expanded_material_map_sets=expanded["material_count"] if expanded is not None else 0,
        environmental_condition_count=len(conditions),
        material_map_sets=(len(source)+len(EXPANDED_FAMILIES))*len(conditions) if run_generator else 0,
        catalog_id_count=len(records),mapped_asset_ids=len(matched),
        missing_material_asset_ids=len(missing),
        unmapped_material_types=dict(sorted(Counter(x["catalog_material"] for x in missing).items())),
        coverage="BASE_MATERIAL_FAMILIES_MAPPED_VISUAL_APPROVAL_PENDING" if not missing else "PARTIAL_SOURCE_COVERAGE",
        validation="source_map_presence_only_not_GOLDEN_40_VISUAL_APPROVAL",
        packs=packs,expanded_material_directory="expanded" if expanded is not None else None,
        mapping=[dict(asset_id=x["asset_id"],pbr_family=x["pbr_family"]) for x in matched],
        missing=[x["asset_id"] for x in missing])
    (out/"batch_manifest.json").write_text(json.dumps(summary,indent=2)+"\n")
    print("LL_MATERIAL_BATCH_DONE",summary["material_map_sets"],
          "covered_ids",len(matched),"unmapped_ids",len(missing),flush=True)
    return summary

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path,default=Path("build/unified_factory/material_batch"))
    p.add_argument("--size",type=int,default=256)
    p.add_argument("--conditions",default="0,1,2,3")
    a=p.parse_args()
    produce(a.out,a.size,tuple(int(x) for x in a.conditions.split(",")))

if __name__=="__main__": main()
