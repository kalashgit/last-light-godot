"""F12 RGBA atlas compositor. Requires Pillow. Never overwrites existing output."""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image
from atlas_layout import layout

def compose(manifest, source_dir, output_dir, page_size=2048, padding=2):
    source_dir=Path(source_dir).resolve()
    output_dir=Path(output_dir).resolve()
    if output_dir.exists():
        raise FileExistsError(str(output_dir))
    frames=manifest["frames"]
    packed=layout(frames,page_size,padding)
    sources={}
    for f in frames:
        filename=f.get("file")
        if not isinstance(filename,str) or not filename or Path(filename).name!=filename or filename in (".","..") or not filename.lower().endswith(".png"):
            raise ValueError("unsafe source filename")
        path=(source_dir/filename).resolve()
        if not path.is_relative_to(source_dir) or not path.is_file():
            raise ValueError("source outside directory or missing")
        if hashlib.sha256(path.read_bytes()).hexdigest()!=f["source_sha256"]:
            raise ValueError("source SHA256 mismatch: "+f["key"])
        with Image.open(path) as img:
            if img.format!="PNG" or img.mode!="RGBA" or img.size!=(f["width"],f["height"]):
                raise ValueError("expected exact-size RGBA PNG: "+f["key"])
            sources[f["key"]]=img.copy()
    pages=[Image.new("RGBA",(page_size,page_size),(0,0,0,0)) for _ in range(packed["pages"])]
    for entry in packed["frames"]:
        im=sources[entry["key"]]
        x,y,w,h=entry["rect"]
        canvas=pages[entry["page"]]
        canvas.paste(im,(x,y))
        canvas.paste(im.crop((0,0,w,1)).resize((w,padding)),(x,y-padding))
        canvas.paste(im.crop((0,h-1,w,h)).resize((w,padding)),(x,y+h))
        canvas.paste(im.crop((0,0,1,h)).resize((padding,h)),(x-padding,y))
        canvas.paste(im.crop((w-1,0,w,h)).resize((padding,h)),(x+w,y))
        for sx,sy,dx,dy in [(0,0,x-padding,y-padding),(w-1,0,x+w,y-padding),(0,h-1,x-padding,y+h),(w-1,h-1,x+w,y+h)]:
            canvas.paste(Image.new("RGBA",(padding,padding),im.getpixel((sx,sy))),(dx,dy))
    output_dir.mkdir(parents=True,exist_ok=False)
    packed["status"]="COMPOSED_NOT_GODOT_APPROVED"
    packed["atlas_files"]=[]
    for i,page in enumerate(pages):
        name=f"atlas_{i:03d}.png"
        page.save(output_dir/name,format="PNG",optimize=False,compress_level=9)
        packed["atlas_files"].append({"file":name,"sha256":hashlib.sha256((output_dir/name).read_bytes()).hexdigest()})
    (output_dir/"atlas.json").write_text(json.dumps(packed,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    return packed

def main():
    p=argparse.ArgumentParser()
    p.add_argument("manifest",type=Path)
    p.add_argument("--source-dir",type=Path,required=True)
    p.add_argument("--output-dir",type=Path,required=True)
    p.add_argument("--page-size",type=int,default=2048)
    p.add_argument("--padding",type=int,default=2)
    a=p.parse_args()
    print(json.dumps(compose(json.loads(a.manifest.read_text()),a.source_dir,a.output_dir,a.page_size,a.padding),indent=2))

if __name__=="__main__":
    main()
