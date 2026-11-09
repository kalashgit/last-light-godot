"""F12 lossless alpha crop with measured ground-anchor preservation.

Input: F12 16-direction source manifest and PNGs.
Output: new standalone source manifest with correctly translated pivot per frame.
Noncanonical; existing untrimmed renders are never modified.
"""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image

def trim(manifest, source, out, margin=2):
    if type(margin) is not int or not 0 <= margin <= 16:
        raise ValueError("margin must be integer in 0..16")
    source=Path(source).resolve()
    out=Path(out).resolve()
    if out.exists():
        raise FileExistsError(str(out))
    if not isinstance(manifest,dict) or not isinstance(manifest.get("frames"),list) or not manifest["frames"]:
        raise ValueError("invalid manifest")
    records=[]
    staged=[]
    for f in manifest["frames"]:
        name=f.get("file")
        if not isinstance(name,str) or Path(name).name!=name or name in (".","..") or not name.endswith(".png"):
            raise ValueError("unsafe source filename")
        source_path=(source/name).resolve()
        if not source_path.is_relative_to(source) or not source_path.is_file():
            raise ValueError("missing source")
        if hashlib.sha256(source_path.read_bytes()).hexdigest()!=f.get("source_sha256"):
            raise ValueError("source hash mismatch")
        pivot=f.get("world_ground_pivot_px")
        if not isinstance(pivot,list) or len(pivot)!=2 or not all(type(v) in (int,float) for v in pivot):
            raise ValueError("F12 world-ground pivot required")
        with Image.open(source_path) as im:
            if im.mode!="RGBA" or im.size!=(f["width"],f["height"]):
                raise ValueError("invalid source image")
            bound=im.getchannel("A").getbbox()
            if not bound:
                raise ValueError("empty frame")
            x0=max(0,bound[0]-margin); y0=max(0,bound[1]-margin)
            x1=min(im.width,bound[2]+margin); y1=min(im.height,bound[3]+margin)
            crop=im.crop((x0,y0,x1,y1))
        local=[round(pivot[0]-x0,5),round(pivot[1]-y0,5)]
        item=dict(f)
        item.update({"width":crop.width,"height":crop.height,
                     "source_canvas_px":[f["width"],f["height"]],
                     "source_crop_rect":[x0,y0,x1,y1],
                     "anchor_local_px":local})
        staged.append((name,crop,item))
        records.append({"key":f["key"],"original_pixels":f["width"]*f["height"],
                        "trimmed_pixels":crop.width*crop.height})
    out.mkdir(parents=True,exist_ok=False)
    frames=[]
    for name,crop,item in staged:
        path=out/name
        crop.save(path,format="PNG",optimize=False,compress_level=9)
        item["source_sha256"]=hashlib.sha256(path.read_bytes()).hexdigest()
        frames.append(item)
    result={k:v for k,v in manifest.items() if k!="frames"}
    result["status"]="TRIMMED_GROUND_ANCHORED_NONCANONICAL"
    result["frames"]=frames
    (out/"manifest.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    before=sum(v["original_pixels"] for v in records)
    after=sum(v["trimmed_pixels"] for v in records)
    audit={"status":"LOSSLESS_SOURCE_TRIM_CANDIDATE","frame_count":len(frames),
           "original_canvas_pixels":before,"trimmed_canvas_pixels":after,
           "pixel_reduction_fraction":round(1-after/before,6),
           "anchor_preserved":True,"frames":records}
    (out/"trim_audit.json").write_text(json.dumps(audit,indent=2,sort_keys=True)+"\n")
    print("F12_LOSSLESS_TRIM_PASS",len(frames),audit["pixel_reduction_fraction"])
    return audit

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("manifest",type=Path)
    p.add_argument("--source-dir",required=True,type=Path)
    p.add_argument("--output-dir",required=True,type=Path)
    p.add_argument("--margin",type=int,default=2)
    a=p.parse_args()
    trim(json.loads(a.manifest.read_text()),a.source_dir,a.output_dir,a.margin)
