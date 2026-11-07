#!/usr/bin/env python3
"""Candidate-only 2.5D pixel finishing for a world-sprite or tile set.

Source can contain manifested furniture, or a dedicated folder of RGBA tile
PNGs without a manifest. Every asset retains original dimensions and alpha.
Any authoritative furniture anchor is carried through unchanged; raw tile
PNGs have no anchor metadata and are previewed centered only. Outputs live
in a different directory and cannot overwrite the production game tree.
"""
import argparse
import hashlib
import json
import sys
import zipfile
from pathlib import Path

from PIL import Image, ImageDraw

from pixel_refine import refine_rgba

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"blender_factory"))
from package_v3_recovery import checker, paste_at_contact, font


def candidates(source, output, colors=80, edge_strength=.65):
    if source.resolve()==output.resolve() or source.resolve() in output.resolve().parents:
        raise ValueError("Candidate output cannot be inside or equal to the source tree")
    if (source/"manifest.json").exists():
        manifest=json.loads((source/"manifest.json").read_text())
        objects=manifest.get("items",[])
    else:
        # Tiles often come as independent PNGs with world positioning stored in
        # Godot resources instead of this manifest. Never invent or modify it.
        objects=[{"name":p.stem,"world_sprite":str(p.relative_to(source)),
                  "anchor_px":None} for p in sorted(source.rglob("*.png"))]
    if not objects:
        raise ValueError("Expected manifest items or a dedicated PNG tile folder")
    output.mkdir(parents=True,exist_ok=True)
    sheet_w,sheet_h=440,330
    sheet=Image.new("RGB",(sheet_w*2,sheet_h*len(objects)),(235,237,230))
    draw=ImageDraw.Draw(sheet)
    records=[]
    for i,item in enumerate(objects):
        name=item["name"]
        rel=Path(item["world_sprite"])
        if rel.is_absolute() or ".." in rel.parts:
            raise ValueError("Unsafe source sprite path")
        original=Image.open(source/rel).convert("RGBA")
        refined=refine_rgba(original,colors,edge_strength)
        assert original.size==refined.size
        assert original.getchannel("A").tobytes()==refined.getchannel("A").tobytes()
        destination=output/rel
        destination.parent.mkdir(parents=True,exist_ok=True)
        refined.save(destination,optimize=True)
        anchor=item.get("anchor_px")
        for col,(label,sprite) in enumerate((("CURRENT",original),("PIXEL CANDIDATE",refined))):
            panel=checker(sheet_w-22,sheet_h-56)
            # The preview-only centering is explicitly not asset pivot metadata.
            sprite.info["anchor"]=anchor if anchor is not None else [sprite.width/2,sprite.height/2]
            paste_at_contact(panel,sprite,(panel.width//2,round(panel.height*.80)),2.2)
            sheet.paste(panel.convert("RGB"),(sheet_w*col+11,sheet_h*i+35))
            draw.text((sheet_w*col+16,sheet_h*i+9),
                      name.upper().replace("_"," ")+" / "+label,
                      font=font(17),fill=(28,34,28))
        records.append({"name":name,"source":str(rel),"candidate":str(rel),
                        "anchor_px":anchor,"size_px":list(original.size),
                        "anchor_policy":"preserved" if anchor is not None else "external_not_inferred",
                        "alpha_preserved":True,
                        "sha256":hashlib.sha256(destination.read_bytes()).hexdigest(),
                        "status":"VISUAL_REVIEW_REQUIRED_NOT_GAME_APPROVED"})
        print("LL_PIXEL_CANDIDATE_OK",name,original.size,flush=True)
    sheet_path=output/"comparison-220-percent.png"
    sheet.save(sheet_path)
    summary={"schema":1,"source":"original 2.5D world sprites, no reference-game pixels",
             "pixel_art_policy":"subtle structural edge clarity + no-dither color clustering",
             "colors":colors,"edge_strength":edge_strength,"scale":2.2,
             "status":"candidate_only_awaiting_founder_Golden_40_comparison",
             "approved_replacements":0,"items":records}
    (output/"manifest.json").write_text(json.dumps(summary,indent=2)+"\n",encoding="utf8")
    archive=output/"LAST_LIGHT_pixel_finish_candidates.zip"
    with zipfile.ZipFile(archive,"w",zipfile.ZIP_DEFLATED,compresslevel=7) as zipped:
        for p in sorted(output.rglob("*")):
            if p.is_file() and p!=archive:
                zipped.write(p,str(p.relative_to(output)))
    print("LL_PIXEL_BATCH_DONE",len(records),archive,flush=True)
    return summary


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--source",type=Path,required=True)
    parser.add_argument("--out",type=Path,required=True)
    parser.add_argument("--colors",type=int,default=80)
    parser.add_argument("--edge-strength",type=float,default=.65)
    a=parser.parse_args()
    candidates(a.source,a.out,a.colors,a.edge_strength)


if __name__=="__main__":main()
