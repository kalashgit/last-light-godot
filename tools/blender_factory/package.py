"""Crop, size, alpha-check and package original 2.5D Blender output.
python tools/blender_factory/package.py --input build/blender_factory/raw --output build/blender_factory/game_ready
"""
import argparse, json, hashlib, zipfile
from pathlib import Path
from PIL import Image, ImageFilter, ImageDraw

def produce(raw, dest):
    manifest = json.loads((raw/"manifest.json").read_text())
    assert manifest["schema"]==1 and manifest["tile_px"]==[80,40]
    dest.mkdir(parents=True,exist_ok=True)
    output = {"schema":1,"tile_px":[80,40],"pixel_art_filter":"nearest",
              "source":"Original scripted Blender 3D-to-2D render pilot", "items":[]}
    for item in manifest["entries"]:
        name=item["name"]
        img=Image.open(raw/item["raw_file"]).convert("RGBA")
        assert img.size==(manifest["render_resolution"],)*2
        # Final pixels at 80x40 / 1m diamond; preserve full-resolution raw separately.
        img=img.resize((img.width//manifest["downsample"],img.height//manifest["downsample"]),Image.Resampling.LANCZOS)
        alpha=img.getchannel("A")
        bounds=alpha.getbbox()
        if bounds is None: raise ValueError("blank rendered sprite: "+name)
        pad=4
        x0=max(0,bounds[0]-pad);y0=max(0,bounds[1]-pad)
        x1=min(img.width,bounds[2]+pad);y1=min(img.height,bounds[3]+pad)
        cropped=img.crop((x0,y0,x1,y1))
        # Validate hard transparency and avoid solid white JPEG slabs.
        if cropped.getchannel("A").getextrema()[0]!=0:
            raise ValueError("sprite lacks transparent padding: "+name)
        contact=[round(item["contact_px_raw"][0]/manifest["downsample"]-x0,2),
                 round(item["contact_px_raw"][1]/manifest["downsample"]-y0,2)]
        # Ground-only drop shadow (separate sprite, physically scaled by footprint).
        shadow=Image.new("RGBA",cropped.size,(0,0,0,0))
        draw=ImageDraw.Draw(shadow)
        fw,fd=item["footprint_m"]
        rx=max(3,int(28*fw));ry=max(2,int(8*fd))
        cx,cy=round(contact[0]),round(contact[1])
        draw.ellipse((cx-rx,cy-ry,cx+rx,cy+ry),fill=(9,13,12,95))
        shadow=shadow.filter(ImageFilter.GaussianBlur(radius=2.2))
        folder=dest/name
        folder.mkdir(exist_ok=True)
        cropped.save(folder/"ground.png")
        shadow.save(folder/"shadow.png")
        # UI icon intentionally separate from native-resolution world sprite.
        icon=cropped.copy()
        icon.thumbnail((112,112),Image.Resampling.LANCZOS)
        canvas=Image.new("RGBA",(128,128),(0,0,0,0))
        canvas.alpha_composite(icon,((128-icon.width)//2,(128-icon.height)//2))
        canvas.save(folder/"icon.png")
        record={"id":item["id"],"name":name,
                "world_sprite":name+"/ground.png","shadow_sprite":name+"/shadow.png",
                "icon_sprite":name+"/icon.png",
                "dimensions_m":item["dimensions_m"],"footprint_m":item["footprint_m"],
                "anchor_px":contact,"size_px":list(cropped.size),
                "sha256":hashlib.sha256((folder/"ground.png").read_bytes()).hexdigest(),
                "representation":"world_facing_original_2_5d_candidate",
                "status":"automated_qa_pending_visual_approval"}
        output["items"].append(record)
    (dest/"manifest.json").write_text(json.dumps(output,indent=2)+"\n")
    archive=dest.parent/"last-light-blender-pilot.zip"
    with zipfile.ZipFile(archive,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=7) as zipf:
        for path in sorted(dest.rglob("*")):
            if path.is_file(): zipf.write(path,arcname=path.relative_to(dest.parent))
    print(f"BLENDER PACK: {len(output['items'])} sprites, ZIP {archive}, tile 80x40")
    return output

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    produce(args.input,args.output)

if __name__=="__main__":
    main()
