"""Source master QA / review PNG contact sheet; never imply Golden approval."""
from pathlib import Path
import argparse
import hashlib
import gzip
import json
import zipfile
from PIL import Image,ImageDraw,ImageFont

def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as s:
        for chunk in iter(lambda:s.read(1048576),b""):
            h.update(chunk)
    return h.hexdigest()

def validate(src,expected=None):
    report=json.loads((src/"batch_report.json").read_text())
    items=report["items"]
    if expected is not None and len(items)!=expected:
        raise ValueError("wrong actual geometry output count")
    if len({x["asset_id"] for x in items})!=len(items):
        raise ValueError("duplicate original 3D source IDs")
    checked=[]
    for item in items:
        d=src/item["asset_id"]
        m=json.loads((d/"geometry_manifest.json").read_text())
        glb=d/"model.glb"
        blend=d/"model.blend"
        if not glb.exists() or glb.open("rb").read(4)!=b"glTF":
            raise ValueError("invalid source 3D GLB: "+item["asset_id"])
        if not blend.exists():
            raise ValueError("missing editable Blender source: "+item["asset_id"])
        with blend.open("rb") as stream:
            header=stream.read(7)
        # Blender's save_as_mainfile(compress=True) stores a gzip-compressed
        # .blend, whose on-disk first bytes are NOT the plain "BLENDER" magic.
        if header != b"BLENDER":
            try:
                with gzip.open(blend,"rb") as stream:
                    header=stream.read(7)
            except (gzip.BadGzipFile, OSError, EOFError) as exc:
                raise ValueError("invalid compressed Blender source: "+item["asset_id"]) from exc
            if header != b"BLENDER":
                raise ValueError("unrecognized Blender source file: "+item["asset_id"])
        if sha(glb)!=m["glb_sha256"] or sha(blend)!=m["editable_blend_sha256"]:
            raise ValueError("original geometry source hash mismatch: "+item["asset_id"])
        if not m["actual_bounds_m"] or not m["original_geometry"]:
            raise ValueError("missing physical source bounds")
        checked.append(m)
    return checked

def sheet(src,out,max_items=60):
    records=validate(src)
    tiles=[]
    for m in records:
        file=src/m["asset_id"]/"preview_source.png"
        if file.is_file():
            im=Image.open(file).convert("RGBA")
            tiles.append((m["asset_id"],im))
    if not tiles:
        raise ValueError("no real Blender source preview images")
    tw,th=220,246
    cols=4
    import math
    rows=math.ceil(len(tiles[:max_items])/cols)
    canvas=Image.new("RGB",(cols*tw,rows*th),(52,55,51))
    d=ImageDraw.Draw(canvas)
    for i,(name,img) in enumerate(tiles[:max_items]):
        x=(i%cols)*tw;y=(i//cols)*th
        img.thumbnail((210,210))
        thumb=Image.new("RGBA",(210,210),(88,92,86,255))
        thumb.alpha_composite(img,((210-img.width)//2,(210-img.height)//2))
        canvas.paste(thumb.convert("RGB"),(x+5,y+3))
        d.text((x+7,y+216),name[:30],fill=(235,230,218))
        d.text((x+7,y+229),"3D MODEL SOURCE; MATERIALS PENDING",fill=(181,189,184))
    out.parent.mkdir(parents=True,exist_ok=True)
    canvas.save(out)
    return len(tiles)

def package(src,dest,expected=None):
    records=validate(src,expected)
    dest.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(dest,"w",zipfile.ZIP_DEFLATED,compresslevel=3,allowZip64=True) as f:
        f.write(src/"batch_report.json","batch_report.json")
        for m in records:
            for filename in ("model.glb","model.blend","geometry_manifest.json"):
                p=src/m["asset_id"]/filename
                f.write(p,m["asset_id"]+"/"+filename)
    return dest.stat().st_size

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--sources",type=Path,required=True)
    parser.add_argument("--expected",type=int)
    parser.add_argument("--sheet",type=Path,required=True)
    parser.add_argument("--zip",type=Path,required=True)
    p=parser.parse_args()
    n=sheet(p.sources,p.sheet)
    bytes=package(p.sources,p.zip,p.expected)
    print("LL_GEOMETRY_SOURCE_QA_PASS",len(validate(p.sources)),n,
          "preview source meshes",bytes,"bytes ZIP",flush=True)

if __name__=="__main__":
    main()
