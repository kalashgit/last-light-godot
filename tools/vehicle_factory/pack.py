"""Golden Vehicle V1: alpha-safe 16-direction atlas and review sheet.

Common crop and foot anchor across 16 headings; never recenter cars per frame.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path
from PIL import Image,ImageDraw
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"material_factory"))
from pixel_refine import refine_rgba

def downsample(im):
    return im.convert("RGBa").resize((im.width//2,im.height//2),Image.Resampling.BOX).convert("RGBA")

def process(input_path,output_path):
    raw=json.loads((input_path/"manifest.json").read_text())
    if raw["directions"]!=16 or raw["tile_px"]!=[80,40]:raise ValueError("wrong heading/projection contract")
    out=[]
    frames=[]
    for row in sorted(raw["frames"],key=lambda z:z["index"]):
        im=downsample(Image.open(input_path/row["source_png"]).convert("RGBA"))
        if im.size!=(384,384):raise ValueError("source size mismatch")
        bbox=im.getchannel("A").getbbox()
        if not bbox:raise ValueError("empty vehicle heading")
        if bbox[0]<4 or bbox[1]<4 or bbox[2]>380 or bbox[3]>380:
            raise ValueError("vehicle clipped: heading "+str(row["index"]))
        frames.append(im)
    if len(frames)!=16 or [x["index"] for x in raw["frames"]]!=list(range(16)):
        raise ValueError("missing or unordered headings")
    boxes=[f.getchannel("A").getbbox() for f in frames]
    left=min(b[0] for b in boxes)-5
    top=min(b[1] for b in boxes)-5
    right=max(b[2] for b in boxes)+5
    bottom=max(b[3] for b in boxes)+5
    w=right-left;h=bottom-top
    anchor_set={tuple(row["fixed_world_pivot_px"]) for row in raw["frames"]}
    if len(anchor_set)!=1:raise ValueError("inconsistent vehicle root pivot")
    anchor=(round(raw["frames"][0]["fixed_world_pivot_px"][0]/2-left,4),
            round(raw["frames"][0]["fixed_world_pivot_px"][1]/2-top,4))
    output_path.mkdir(parents=True,exist_ok=True)
    native=Image.new("RGBA",(w*4,h*4),(0,0,0,0))
    preview=Image.new("RGBA",((w+12)*4,(h+32)*4),(70,80,70,255))
    draw=ImageDraw.Draw(preview)
    for i,frame in enumerate(frames):
        x=i%4;y=i//4
        crop=frame.crop((left,top,right,bottom))
        crop.save(output_path/f"heading_{i:02}.png",optimize=True)
        native.alpha_composite(crop,(x*w,y*h))
        preview.alpha_composite(crop,(x*(w+12)+6,y*(h+32)+22))
        draw.text((x*(w+12)+6,y*(h+32)+5),f"{i*22.5:05.1f} deg",fill=(240,239,222))
    native.save(output_path/"vehicle_16_headings.png",optimize=True)
    # Quantize the complete 16-view atlas as ONE palette to eliminate heading
    # color drift. Never alter alpha, crop boxes, native scale or world pivots.
    finished=refine_rgba(native,colors=96,edge_strength=.55)
    finished.save(output_path/"vehicle_16_headings_pixel_refined.png",optimize=True)
    if finished.getchannel("A").tobytes()!=native.getchannel("A").tobytes():
        raise ValueError("pixel refinement damaged alpha mask")
    if finished.size!=native.size:
        raise ValueError("pixel finishing changed world scale")
    q=Image.new("RGBA",(w*8,h),(77,86,78,255))
    for i in range(4):
        src_box=(i*w,0,(i+1)*w,h)
        q.alpha_composite(native.crop(src_box),(i*w,0))
        q.alpha_composite(finished.crop(src_box),((i+4)*w,0))
    q.convert("RGB").save(output_path/"pixel_finish_comparison.png")
    preview.convert("RGB").save(output_path/"vehicle_review_16_headings.png")
    # 16 frame preview shows rotation visually without adding gameplay movement.
    gif_frames=[]
    for im in frames:
        bg=Image.new("RGBA",(w,h),(87,96,82,255))
        bg.alpha_composite(im.crop((left,top,right,bottom)))
        gif_frames.append(bg.convert("RGB"))
    gif_frames[0].save(output_path/"vehicle_rotation_preview.gif",save_all=True,
                append_images=gif_frames[1:],duration=130,loop=0,optimize=False)
    result=dict(schema_version=1,asset_id=raw["asset_id"],source=raw["original_source"],
       dimensions_m=raw["declared_dimensions_m"],wheelbase_m=raw["wheelbase_m"],
       angle_increment_deg=22.5,heading_count=16,grid=[4,4],cell_px=[w,h],
       anchor_px=anchor,tile_px=[80,40],wear_condition=1,
       collision_footprint_m=[raw["declared_dimensions_m"][0],raw["declared_dimensions_m"][1]],
       proposed_gameplay_components=["body","wheels","doors","hood","trunk","windows","seats"],
       status="RENDERED_CANDIDATE_NOT_FOUNDER_APPROVED_NOT_GODOT_INTEGRATED",
       atlas="vehicle_16_headings.png",pixel_refined_atlas="vehicle_16_headings_pixel_refined.png",\n       pixel_comparison="pixel_finish_comparison.png",review="vehicle_review_16_headings.png",
       sha256=hashlib.sha256((output_path/"vehicle_16_headings.png").read_bytes()).hexdigest())
    (output_path/"manifest.json").write_text(json.dumps(result,indent=2)+"\n")
    print("LL_VEHICLE_PACK_DONE",result["heading_count"],result["cell_px"],flush=True)
    return result

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    process(a.input,a.output)

if __name__=="__main__":main()
