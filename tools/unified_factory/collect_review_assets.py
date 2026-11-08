"""Package the REAL existing LAST LIGHT reference, preview and factory output files.

GitHub repository is the source of truth. This script does not make any new art,
modify runtime scenes or assert Golden/gameplay approval.

  python tools/unified_factory/collect_review_assets.py --output build/asset_collection

Outputs:
  Last_Light_Collected_Visual_Assets_V1.zip
  Last_Light_Factory_Source_And_Godot_V1.zip
  collection_index.json

The archive is a durable snapshot only if the user downloads/saves it: GitHub
Actions artifacts themselves expire according to retention policy.
"""
import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VISUAL_FOLDERS = [
  "assets/last_light/golden40",
  "preview/vehicle-factory-v1",
  "preview/fleet-factory-v1",
  "preview/actor-factory-v1",
  "preview/animation-factory-v1",
  "preview/material-factory-v1",
  "preview/material-factory-v2",
  "preview/material-factory-batch-v1",
  "preview/v3-recovery",
  "preview/parallel-factory-v1",
  "assets/generated/factory"
]
SOURCE_FOLDERS = [
  "tools/asset_factory",
  "tools/blender_factory",
  "tools/material_factory",
  "tools/animation_factory",
  "tools/actor_factory",
  "tools/vehicle_factory",
  "tools/unified_factory",
  "assets/generated/master_import_v1",
  "assets/master_library",
  "docs/LAST_LIGHT_COLLECTED_ASSET_GALLERY_V1.md",
  "docs/CODEX_COMPLETE_CENSUS_MASTER_FACTORY_V2.md",
  "docs/CODEX_MASTER_FACTORY_SINGLE_MAP_DIRECTIVE_V1.md",
  "AGENTS.md",
  "scenes/animation_lab.tscn",
  "scenes/actor_lab.tscn",
  "scenes/vehicle_lab.tscn",
  "scenes/master_factory_import_lab.tscn",
  "scripts/animation_lab.gd",
  "scripts/actor_lab.gd",
  "scripts/vehicle_lab.gd",
  "scripts/master_factory_import_lab.gd"
]

def digest(path):
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for part in iter(lambda: stream.read(1048576), b""):
            hasher.update(part)
    return hasher.hexdigest()

def resolve_entries(root, paths):
    files=[]
    for relative in paths:
        start=(root/relative).resolve()
        if not start.is_relative_to(root.resolve()) or not start.exists():
            raise ValueError("required source missing: "+relative)
        if start.is_file():
            files.append(start)
        else:
            files.extend(f for f in start.rglob("*") if f.is_file() and ".git" not in f.parts)
    if len(files)!=len({f.relative_to(root).as_posix() for f in files}):
        raise ValueError("duplicate path included in collection")
    return sorted(files)

def inventory(root):
    gold=json.loads((root/"assets/last_light/golden40/manifest.json").read_text())
    actors=json.loads((root/"preview/actor-factory-v1/manifest.json").read_text())
    animations=json.loads((root/"preview/animation-factory-v1/manifest.json").read_text())
    car=json.loads((root/"preview/vehicle-factory-v1/manifest.json").read_text())
    items=json.loads((root/"assets/generated/factory/manifest.json").read_text())
    assert gold["count"]==40 and len(gold["items"])==40
    assert len({x["id"] for x in gold["items"]})==40
    assert len(actors["actors"])==5
    assert len(animations["entries"])==3 and sum(x["frame_count"] for x in animations["entries"])==27
    assert car["heading_count"]==16
    assert len(items["objects"])==300
    for n in range(4):
        assert (root/f"preview/material-factory-batch-v1/condition_{n}_sheet.png").exists()
    sprite_files=list((root/"assets/last_light/golden40").rglob("*.png"))
    assert len(sprite_files)>=122  # 40 x three + two contact sheets
    return dict(
        golden40_icons=40,
        golden40_png_files=len(sprite_files),
        actor_variants=5,
        furniture_animation_actions=3,
        furniture_animation_frames=27,
        original_hatchback_directions=16,
        additional_vehicle_smoke_profiles=2,
        material_condition_levels=4,
        existing_item_factory_entries=300,
        note="Counts are research references / technical candidates, NOT all founder approved or gameplay integrated."
    )

def archive(output, root, files, name, info):
    dst=output/name
    records=[]
    with zipfile.ZipFile(dst,"w",zipfile.ZIP_DEFLATED,compresslevel=6,allowZip64=True) as bundle:
        readme=(
          "LAST LIGHT / ORIGINAL PRODUCTION ASSET COLLECTION V1\n"
          "Source repository: https://github.com/kalashgit/last-light-godot\n"
          "Single visual gallery: docs/LAST_LIGHT_COLLECTED_ASSET_GALLERY_V1.md\n"
          "This is an archive of EXISTING files, not new generation or a gameplay release.\n"
          "Golden 40 are founder-approved style references, not 40 playable world objects.\n"
          "Actor, prop animation, vehicle and material batches include technical CANDIDATES.\n"
          "Full quality and device approval must be checked separately.\n"
          "No files were merged to main or deployed by this packaging tool.\n\n"
          +json.dumps(info,indent=2)
          +"\n"
        )
        bundle.writestr("COLLECTION_README.txt",readme)
        for path in files:
            rel=path.relative_to(root).as_posix()
            records.append(dict(path=rel,size_bytes=path.stat().st_size,sha256=digest(path)))
            bundle.write(path,arcname=rel)
        bundle.writestr("COLLECTION_FILES_SHA256.json",json.dumps(records,indent=2)+"\n")
    print("LAST_LIGHT_ARCHIVE_OK",name,len(records),dst.stat().st_size,flush=True)
    return dict(filename=name,file_count=len(records),archive_size_bytes=dst.stat().st_size,
                sha256=digest(dst),files=records)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    output=a.output.resolve()
    output.mkdir(parents=True,exist_ok=True)
    counts=inventory(ROOT)
    visual=archive(output,ROOT,resolve_entries(ROOT,VISUAL_FOLDERS),
      "Last_Light_Collected_Visual_Assets_V1.zip",counts)
    source=archive(output,ROOT,resolve_entries(ROOT,SOURCE_FOLDERS),
      "Last_Light_Factory_Source_And_Godot_V1.zip",counts)
    brief=dict(schema_version=1,status="COLLECTED_EXISTING_ASSETS_CANDIDATES_NOT_FULL_GAMEPLAY_RELEASE",
      categories=counts,archives=[{k:v for k,v in rec.items() if k!="files"} for rec in (visual,source)])
    (output/"collection_index.json").write_text(json.dumps(brief,indent=2)+"\n")
    assert all((output/r["filename"]).stat().st_size>1000 for r in brief["archives"])
    print("LAST_LIGHT_COLLECTED_ASSETS_PASS",visual["file_count"],
          source["file_count"],flush=True)

if __name__=="__main__":
    main()
