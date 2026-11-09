"""F12 gameplay-scale art contact sheets for real 16-heading RGBA manifests.

Outputs truthful technical diagnostics; no Golden approval is implied.
Native scale is *1 rendered pixel to 1 review pixel*, never upscaled.
"""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageDraw

def build(manifest_path, source_dir, output_dir):
    manifest_path=Path(manifest_path)
    source_dir=Path(source_dir).resolve()
    output_dir=Path(output_dir)
    if output_dir.exists():
        raise FileExistsError(str(output_dir))
    manifest=json.loads(manifest_path.read_text())
    frames=sorted(manifest["frames"],key=lambda f:f["direction"])
    if len(frames)!=16 or [f["direction"] for f in frames]!=list(range(16)):
        raise ValueError("Expected all 16 directional frames exactly once")
    tile_size=(190,160)
    sheet=Image.new("RGB",(tile_size[0]*4,tile_size[1]*4),(37,44,39))
    records=[]
    for idx,frame in enumerate(frames):
        name=frame["file"]
        if Path(name).name!=name or name in (".",".."):
            raise ValueError("unsafe source filename")
        path=source_dir/name
        raw=path.read_bytes()
        if hashlib.sha256(raw).hexdigest()!=frame["source_sha256"]:
            raise ValueError("source hash mismatch")
        with Image.open(path) as opened:
            if opened.mode!="RGBA" or opened.size!=(frame["width"],frame["height"]):
                raise ValueError("invalid RGBA frame")
            img=opened.copy()
        bounds=img.getchannel("A").getbbox()
        if not bounds:
            raise ValueError("empty render")
        pivot=frame.get("world_ground_pivot_px")
        if not isinstance(pivot,list) or len(pivot)!=2:
            raise ValueError("missing verified world pivot")
        left,top,right,bottom=bounds
        # Crop alpha only for QA composition; placement offsets preserve world anchor.
        crop=img.crop(bounds)
        w,h=crop.size
        # 80x40 one-metre tile diamond below the item; fixed native-pixel scale.
        x0=(idx%4)*tile_size[0]
        y0=(idx//4)*tile_size[1]
        cell=Image.new("RGB",tile_size,(65,72,63))
        draw=ImageDraw.Draw(cell)
        for y in range(tile_size[1]):
            draw.line([(0,y),(tile_size[0],y)],fill=(67+y//8,72+y//10,66+y//9))
        anchor_x,anchor_y=tile_size[0]//2,tile_size[1]-40
        draw.polygon([(anchor_x,anchor_y-20),(anchor_x+40,anchor_y),(anchor_x,anchor_y+20),(anchor_x-40,anchor_y)],fill=(95,101,84),outline=(125,135,109))
        # World root pixel is the origin used by F12; preserve it through crop.
        paste_x=round(anchor_x-pivot[0]+left)
        paste_y=round(anchor_y-pivot[1]+top)
        cell.paste(crop,(paste_x,paste_y),crop)
        draw.text((8,7),f"F10 heading {idx:02d}",fill=(235,237,229))
        sheet.paste(cell,(x0,y0))
        alpha=img.getchannel("A")
        visible_pixels=sum(1 for a in alpha.tobytes() if a>=128)
        bright=0
        pixels=img.tobytes()
        for r,g,b,a in zip(*[iter(pixels)]*4):
            if a>=128 and min(r,g,b)>215:
                bright+=1
        records.append({"heading":idx,"alpha_bounds":list(bounds),
                       "visible_pixels":visible_pixels,
                       "near_white_fraction":round(bright/max(1,visible_pixels),5),
                       "world_pivot_px":pivot,
                       "crop_size":[w,h]})
    output_dir.mkdir(parents=True)
    image_path=output_dir/"f10_gameplay_16_headings_1x.png"
    sheet.save(image_path)
    anchor0=records[0]["world_pivot_px"]
    drift=max(((r["world_pivot_px"][0]-anchor0[0])**2+(r["world_pivot_px"][1]-anchor0[1])**2)**0.5 for r in records)
    result={"status":"VISUAL_REVIEW_CANDIDATE_NOT_GOLDEN",
            "source":"ACTUAL_F10_NONCANONICAL_PROCEDURAL_MODEL",
            "headings":16,"max_world_pivot_drift_px":round(drift,6),
            "native_render_pixels_per_world_metre":40,
            "native_sheet_size":list(sheet.size),
            "min_silhouette_pixels":min(r["visible_pixels"] for r in records),
            "max_near_white_fraction":max(r["near_white_fraction"] for r in records),
            "frames":records,
            "image_sha256":hashlib.sha256(image_path.read_bytes()).hexdigest()}
    (output_dir/"visual_review.json").write_text(json.dumps(result,indent=2)+"\n")
    print("F12_GAMEPLAY_NATIVE_CONTACT_SHEET_DONE",result["headings"],result["max_world_pivot_drift_px"])
    return result

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--manifest",type=Path,required=True)
    p.add_argument("--source-dir",type=Path,required=True)
    p.add_argument("--output-dir",type=Path,required=True)
    a=p.parse_args()
    build(a.manifest,a.source_dir,a.output_dir)

if __name__=="__main__":
    main()
