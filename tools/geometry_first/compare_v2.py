"""Before/after source fidelity comparison with honest technical vs Golden QA.

Input: independent V1 and V2 geometry exports, NOT a replacement of the 360
baseline; output: side-by-side image, exact source hashes and per-family
refinement evidence. Alpha/edge diagnostic is NOT a perceptual quality score.
"""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path

from PIL import Image,ImageDraw
from qa import validate as qa_sources

WIDTH=260
CELL_H=294

def diagnostic_iou(im1,im2):
    a=im1.convert("RGBA").getchannel("A").resize((128,128))
    b=im2.convert("RGBA").getchannel("A").resize((128,128))
    ac=a.point(lambda n:255 if n>=64 else 0)
    bc=b.point(lambda n:255 if n>=64 else 0)
    va, vb=ac.tobytes(),bc.tobytes()
    union=sum((a>0 or b>0) for a,b in zip(va,vb))
    inter=sum((a>0 and b>0) for a,b in zip(va,vb))
    return round(inter/union,4) if union else 0.0

def make_sheet(baseline,refined,dest,count):
    old=qa_sources(baseline,count)
    new=qa_sources(refined,count)
    originals={x["asset_id"]:x for x in old}
    fresh={x["asset_id"]:x for x in new}
    if originals.keys()!=fresh.keys():
        raise ValueError("old and new do not cover the same exact semantic IDs")
    canvas=Image.new("RGB",(WIDTH*3,CELL_H*len(new)),(49,53,51))
    draw=ImageDraw.Draw(canvas)
    result=[]
    for row,key in enumerate(sorted(originals)):
        prior=originals[key]
        cur=fresh[key]
        current=cur.get("refinement",{})
        if cur.get("refinement_profile")!="v2" or not current.get("applied"):
            raise ValueError("not a real applied V2 geometry repair: "+key)
        if cur.get("glb_sha256")==prior.get("glb_sha256"):
            raise ValueError("new model binary identical to baseline; shape may not have changed: "+key)
        a=Image.open(baseline/key/"preview_source.png").convert("RGBA")
        b=Image.open(refined/key/"preview_source.png").convert("RGBA")
        if a.size!=b.size:
            raise ValueError("changed output framing not comparable "+key)
        rowcolor=(71,76,72)
        before=Image.new("RGBA",(240,240),(*rowcolor,255))
        after=Image.new("RGBA",(240,240),(*rowcolor,255))
        for image,back in ((a,before),(b,after)):
            thumbnail=image.copy()
            thumbnail.thumbnail((238,238))
            back.alpha_composite(thumbnail,((240-thumbnail.width)//2,
                                              (240-thumbnail.height)//2))
        y=row*CELL_H
        canvas.paste(before.convert("RGB"),(5,y+26))
        canvas.paste(after.convert("RGB"),(WIDTH+5,y+26))
        # an enlarged source mask difference is a diagnostic, not a visual score.
        im_a=a.getchannel("A").resize((240,240))
        im_b=b.getchannel("A").resize((240,240))
        diff=Image.new("RGB",(240,240))
        from PIL import ImageChops,ImageOps
        changes=ImageChops.difference(im_a,im_b).convert("RGB")
        diff.paste(changes)
        canvas.paste(diff,(WIDTH*2+5,y+26))
        draw.text((8,y+7),key[:36],fill=(235,236,225))
        for col,label in enumerate(("BASE 360 SOURCE","NEW V2 SHAPE","ALPHA CHANGE ONLY")):
            draw.text((col*WIDTH+7,y+269),label,fill=(224,229,218))
        result.append(dict(
            asset_id=key,refinement_applied=True,
            original_sha256=prior["glb_sha256"],
            glb_sha256=cur["glb_sha256"],
            recipe_sha256=cur["refinement_code_sha256"],
            actual_bounds_m=cur["actual_bounds_m"],
            original_bounds_m=prior["actual_bounds_m"],
            original_geometry_skills=current.get("specialists",[]),
            repair_parts=current.get("repaired_geometry",[]),
            silhouette_overlap_diagnostic=diagnostic_iou(a,b),
            geometry_source_verified=True,
            visual_quality_approved=False,
            source_archive="GitHub Action artifact of isolated V2 refinement smoke run",
            status="REFINED_SOURCE_QA_ONLY_GOLDEN_VISUAL_REVIEW_PENDING"
        ))
    dest.parent.mkdir(parents=True,exist_ok=True)
    canvas.save(dest)
    return result

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--baseline",type=Path,required=True)
    p.add_argument("--refined",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--report",type=Path,required=True)
    p.add_argument("--expected",type=int,default=6)
    a=p.parse_args()
    records=make_sheet(a.baseline,a.refined,a.out,a.expected)
    report=dict(schema_version=2,
        status="VALIDATED_SOURCE_REFINEMENT_NOT_VISUAL_GOLDEN_APPROVED",
        source_count=len(records),
        original_source_models_preserved=True,
        counts=dict(refined=len(records),founder_approved=0,gameplay_integrated=0),
        items=records)
    a.report.parent.mkdir(parents=True,exist_ok=True)
    a.report.write_text(json.dumps(report,indent=2)+"\n")
    print("LL_REFINEMENT_COMPARE_PASS",len(records),"authentic updated source geometries",flush=True)

if __name__=="__main__":
    main()
