"""Alpha-safe animated atlas/transparent frame export with a fixed per-action crop.
Do not normalize frames individually: that would move interaction anchors every frame.
"""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageChops, ImageDraw

def rgba_downsample(im, scale=2):
    return im.convert("RGBa").resize((im.width//scale, im.height//scale),
                    Image.Resampling.BOX).convert("RGBA")

def make_preview(frames):
    previews=[]
    for im in frames:
        bg=Image.new("RGBA",im.size,(94,106,92,255))
        d=ImageDraw.Draw(bg)
        for y in range(0,im.height,20):
            d.line([(0,y),(im.width,y)],fill=(112,126,110,255),width=1)
        bg.alpha_composite(im)
        previews.append(bg.convert("RGB"))
    return previews

def process(input_dir, output_dir):
    src=json.loads((input_dir/"manifest.json").read_text())
    if src["schema_version"] != 1 or src["tile_px"] != [80,40]:
        raise ValueError("Unsupported animation manifest/tile projection")
    output_dir.mkdir(parents=True,exist_ok=True)
    results=[]
    for entry in src["entries"]:
        name=entry["id"]
        frames=[rgba_downsample(Image.open(input_dir/name/f).convert("RGBA")) for f in entry["frames"]]
        if not frames or len({im.size for im in frames}) != 1:
            raise ValueError(name+": missing/uneven full-size frames")
        w,h=frames[0].size
        bounds=[im.getchannel("A").getbbox() for im in frames]
        if any(b is None for b in bounds):
            raise ValueError(name+": blank animation frame")
        if any(b[0] < 2 or b[1] < 2 or b[2] >= w-2 or b[3] >= h-2 for b in bounds):
            raise ValueError(name+": source clipping; change camera/geometry")
        left=max(0,min(b[0] for b in bounds)-4)
        top=max(0,min(b[1] for b in bounds)-4)
        right=min(w,max(b[2] for b in bounds)+4)
        bottom=min(h,max(b[3] for b in bounds)+4)
        cells=[im.crop((left,top,right,bottom)) for im in frames]
        cell_w,cell_h=cells[0].size
        if ImageChops.difference(cells[0],cells[-1]).getbbox() is None:
            raise ValueError(name+": no visual motion from closed to open")
        folder=output_dir/name
        folder.mkdir(parents=True,exist_ok=True)
        strip=Image.new("RGBA",(cell_w*len(cells),cell_h),(0,0,0,0))
        hashes=[]
        for i,cell in enumerate(cells):
            frame_name=f"frame_{i:02}.png"
            cell.save(folder/frame_name,optimize=True)
            hashes.append(hashlib.sha256((folder/frame_name).read_bytes()).hexdigest())
            strip.alpha_composite(cell,(i*cell_w,0))
        strip.save(folder/"strip.png",optimize=True)
        preview=make_preview(cells)
        preview[0].save(folder/"preview.gif",save_all=True,append_images=preview[1:],
                        duration=round(1000/entry["fps"]),loop=0,optimize=False)
        anchor=[round(entry["pivot_source_canvas"][0]/2-left,3),
                round(entry["pivot_source_canvas"][1]/2-top,3)]
        results.append(dict(id=name,family=entry["family"],fps=entry["fps"],
            frame_count=len(cells),event_frame=entry["event_frame"],
            reverse_for_close=entry["reverse_for_close"],
            condition=entry["condition"],cell_px=[cell_w,cell_h],
            anchor_px=anchor,frame_sha256=hashes,
            strip=name+"/strip.png",preview=name+"/preview.gif",
            status="mechanically_packed_visual_and_godot_qa_pending"))
        print("LL_ANIM_PACK_OK",name,len(cells),[cell_w,cell_h],anchor,flush=True)
    manifest=dict(schema_version=1,tile_px=[80,40],
                  style="LAST_LIGHT_GOLDEN_FURNITURE_REFERENCE_V1",
                  pipeline="Blender articulated meshes -> RGBA -> shared crop -> atlas",
                  status="CANDIDATE_NOT_FOUNDER_OR_GODOT_APPROVED",
                  entries=results)
    (output_dir/"manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")
    return manifest

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    manifest=process(args.input,args.output)
    print("LL_ANIM_PACK_DONE",len(manifest["entries"]),flush=True)

if __name__=="__main__": main()
