"""Native-size RGBA sprite reduction, paired-review, deterministic manifest + ZIP.

Use system Python + Pillow after Blender generation. Alpha, 2:1 source camera,
fixed pivot and distinct icon/world profiles remain inspectable in metadata.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import zipfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[2]
RECIPES=Path(__file__).with_name("recipes.json")


def sha(file):
    h=hashlib.sha256()
    with file.open("rb") as stream:
        for piece in iter(lambda:stream.read(1024*1024),b""):
            h.update(piece)
    return h.hexdigest()


def fit_icon(img, n):
    bounds=img.getchannel("A").getbbox()
    if bounds is None:
        raise ValueError("blank raw Blender icon")
    x0,y0,x1,y1=bounds
    crop=img.crop(bounds)
    limit=n-8
    ratio=min(limit/crop.width,limit/crop.height)
    size=(max(1,round(crop.width*ratio)),max(1,round(crop.height*ratio)))
    crop=crop.resize(size,Image.Resampling.BOX)
    square=Image.new("RGBA",(n,n),(0,0,0,0))
    square.alpha_composite(crop,((n-size[0])//2,(n-size[1])//2))
    return square


def world_set(imgs, dirout):
    boxes=[im.getchannel("A").getbbox() for im in imgs]
    if not all(boxes):raise ValueError("empty fixed camera render")
    pad=8
    bounds=(max(0,min(b[0] for b in boxes)-pad),
            max(0,min(b[1] for b in boxes)-pad),
            min(1024,max(b[2] for b in boxes)+pad),
            min(1024,max(b[3] for b in boxes)+pad))
    # Crucial: one envelope and one anchor for all four headings. No per-view
    # auto-scale/recenter. Quarter-size converts the locked 1024px master to
    # the native 80x40 projected floor tile profile.
    x0,y0,x1,y1=bounds
    size=(max(1,math.ceil((x1-x0)/4)),max(1,math.ceil((y1-y0)/4)))
    anchor=[round((512-x0)/4,2),round((512-y0)/4,2)]
    results=[]
    for head,im in enumerate(imgs):
        im=im.crop(bounds).resize(size,Image.Resampling.BOX)
        target=dirout/f"ground_{head:02d}.png"
        im.save(target,optimize=True)
        results.append({"angle_index":head,"path":target.name,
                        "rgba_sha256":sha(target),"size_px":list(im.size),
                        "ground_anchor_px":anchor})
    return results


def contact_sheet(items,output):
    count=len(items); cols=5; tw,th=280,300
    canvas=Image.new("RGB",(tw*cols,th*math.ceil(count/cols)),(39,43,43))
    dr=ImageDraw.Draw(canvas)
    for i,rec in enumerate(items):
        x=(i%cols)*tw; y=(i//cols)*th
        path=output/rec["asset_id"]
        raw=Image.open(path/"icon_raw.png").convert("RGBA")
        bbox=raw.getchannel("A").getbbox()
        raw=raw.crop(bbox)
        raw.thumbnail((260,175),Image.Resampling.BOX)
        tile=Image.new("RGBA",(268,182),(74,78,77,255))
        tile.alpha_composite(raw,((268-raw.width)//2,(182-raw.height)//2))
        canvas.paste(tile.convert("RGB"),(x+6,y+5))
        native=Image.open(path/"icon_64.png").convert("RGBA")
        zoom=native.resize((128,128),Image.Resampling.NEAREST)
        sample=Image.new("RGBA",(135,128),(85,88,88,255))
        sample.alpha_composite(zoom,(3,0))
        canvas.paste(sample.convert("RGB"),(x+5,y+170))
        dr.text((x+143,y+183),rec["asset_id"].removeprefix("ll_tools_")[:18],fill=(241,233,218))
        dr.text((x+143,y+207),f"{rec['model_parts']} editable parts",fill=(180,200,193))
        dr.text((x+143,y+225),"64px original icon",fill=(180,200,193))
        dr.text((x+143,y+252),"2.5D CANDIDATE",fill=(243,192,100))
    dest=output/f"weapons_tools_{len(items)}_contact_sheet.png"
    canvas.save(dest,optimize=True)
    return dest


def process(directory,archive):
    recipe=json.loads(RECIPES.read_text())
    sources=json.loads((directory/"source_report.json").read_text())
    records=[]
    for metadata in sources["items"]:
        ident=metadata["asset_id"]
        folder=directory/ident
        glb=folder/"model.glb"; blend=folder/"model.blend"
        if glb.read_bytes()[:4]!=b"glTF" or blend.read_bytes()[:7]!=b"BLENDER":
            raise ValueError("not actual editable/exported 3D source: "+ident)
        if sha(glb)!=metadata["model_glb_sha256"] or sha(blend)!=metadata["model_blend_sha256"]:
            raise ValueError("source geometry SHA mismatch: "+ident)
        imgs=[Image.open(folder/f"world_raw_{idx:02d}.png").convert("RGBA") for idx in range(4)]
        frames=world_set(imgs,folder)
        raw=Image.open(folder/"icon_raw.png").convert("RGBA")
        sizes={}
        for n in (32,48,64,128):
            f=folder/f"icon_{n}.png"
            fit_icon(raw,n).save(f,optimize=True)
            sizes[str(n)]={"sha256":sha(f),"size_px":[n,n]}
        record={**metadata,"world_frames":frames,"inventory_icons":sizes,
                "technical_status":"SOURCE_AND_RGBA_VALIDATION_PASSED",
                "visual_status":"AWAITING_FOUNDER_GOLDEN40_REVIEW",
                "in_engine_status":"NOT_GODOT_INTEGRATED"}
        (folder/"production_manifest.json").write_text(json.dumps(record,indent=2)+"\n")
        records.append(record)
    if len(records)!=len(recipe["assets"]) or len({r["asset_id"] for r in records})!=len(records):
        raise ValueError("pilot must preserve every selected unique registry ID")
    preview=contact_sheet(records,directory)
    manifest={"schema":1,"unique_3d_masters":len(records),"world_rgba_frames":len(records)*4,
              "original_inventory_icons":len(records)*4,
              "founder_approved":0,"godot_integrated":0,"iphone_tested":0,
              "art_standard":"LAST_LIGHT_GROUNDED_PIXEL_REALISM_CANDIDATE",
              "preview":preview.name,"items":records}
    (directory/"pilot_manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")
    archive.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(archive,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=3) as z:
        z.write(directory/"pilot_manifest.json","pilot_manifest.json")
        z.write(preview,preview.name)
        for r in records:
            folder=directory/r["asset_id"]
            for filename in ("model.blend","model.glb","production_manifest.json",
                             "icon_32.png","icon_48.png","icon_64.png","icon_128.png",
                             "ground_00.png","ground_01.png","ground_02.png","ground_03.png"):
                z.write(folder/filename,r["asset_id"]+"/"+filename)
    if archive.stat().st_size<100000:
        raise ValueError("unexpectedly small 3D/2.5D package")
    print("LL_WEAPONS_TOOLS_RGBA_QA_PASS",len(records),len(records)*4,
          "world directions",archive.stat().st_size,"ZIP bytes",flush=True)
    return manifest


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--sources",type=Path,required=True)
    p.add_argument("--zip",type=Path,required=True)
    a=p.parse_args()
    process(a.sources,a.zip)


if __name__=="__main__": main()
