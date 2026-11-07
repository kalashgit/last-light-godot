#!/usr/bin/env python3
"""Candidate-only 2.5D pixel finishing for any world-sprite set.

Source can contain furniture or world tiles with a packaging manifest. Every
object retains its original file, dimensions, alpha, anchor and scale. Outputs
live in a different directory and cannot overwrite the production game tree.
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
    manifest=json.loads((source/"manifest.json").read_text())
    objects=manifest.get("items",[])
    if not objects:
        raise ValueError("Expected package manifest with items")
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
        anchor=item["anchor_px"]
        for col,(label,sprite) in enumerate((("CURRENT",original),("PIXEL CANDIDATE",refined))):
            panel=checker(sheet_w-22,sheet_h-56)
            sprite.info["anchor"]=anchor
            paste_at_contact(panel,sprite,(panel.width//2,round(panel.height*.80)),2.2)
            sheet.paste(panel.convert("RGB"),(sheet_w*col+11,sheet_h*i+35))
            draw.text((sheet_w*col+16,sheet_h*i+9),
                      name.upper().replace("_"," ")+" / "+label,
                      font=font(17),fill=(28,34,28))
        records.append({"name":name,"source":str(rel),"candidate":str(rel),
                        "anchor_px":anchor,"size_px":list(original.size),
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
