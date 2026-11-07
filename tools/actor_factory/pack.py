"""Alpha-safe world-scale actor atlas packer. Actor positions never recentered frame-by-frame."""
import argparse
import collections
import hashlib
import json
from pathlib import Path
from PIL import Image,ImageDraw

DIRECTIONS=("front","right","back","left")

def downsample(im,divisor=2):
    return im.convert("RGBa").resize((im.width//divisor,im.height//divisor),Image.Resampling.BOX).convert("RGBA")

def pack(raw_dir,outdir):
    source=json.loads((raw_dir/"manifest.json").read_text())
    if source["schema_version"]!=1 or source["tile_px"] != [80,40]:
        raise ValueError("unexpected actor source atlas coordinate contract")
    by_actor=collections.defaultdict(list)
    for entry in source["frames"]:
        by_actor[entry["render_id"]].append(entry)
    outdir.mkdir(parents=True,exist_ok=True)
    all_results=[]
    cards=[]
    for render_id in sorted(by_actor):
        records=by_actor[render_id]
        images={}
        for r in records:
            key=(r["clip"],r["direction"],r["frame"])
            if key in images: raise ValueError("duplicate actor frame "+str(key))
            image=downsample(Image.open(raw_dir/r["render_file"]).convert("RGBA"))
            if image.size!=(256,256):raise ValueError("wrong actor canvas size")
            if image.getchannel("A").getbbox() is None:raise ValueError("blank actor frame")
            images[key]=image
        bounds=[im.getchannel("A").getbbox() for im in images.values()]
        l=max(0,min(b[0] for b in bounds)-5)
        t=max(0,min(b[1] for b in bounds)-5)
        r=min(256,max(b[2] for b in bounds)+5)
        b=min(256,max(b[3] for b in bounds)+5)
        if min(l,t)<2 or max(r,b)>254:
            raise ValueError("actor clipped or too close to native world canvas edge")
        w,h=r-l,b-t
        # Anchor is the projected world origin; never use frame-specific centers.
        pivots={tuple(round(x/2,3) for x in entry["anchor_source_px"]) for entry in records}
        if len(pivots)!=1:raise ValueError("actor root anchor drift")
        px,py=next(iter(pivots))
        anchor=[round(px-l,3),round(py-t,3)]
        actor_out=outdir/render_id
        actor_out.mkdir(parents=True,exist_ok=True)
        clips={}
        for clip in sorted({entry["clip"] for entry in records}):
            per_direction={d:sorted([x for x in records if x["clip"]==clip and x["direction"]==d],
                     key=lambda x:x["frame"]) for d in DIRECTIONS}
            counts={len(items) for items in per_direction.values()}
            if len(counts)!=1 or not counts or min(counts)<1:raise ValueError("missing direction frames")
            n=next(iter(counts))
            atlas=Image.new("RGBA",(n*w,4*h),(0,0,0,0))
            files=[]
            for y,d in enumerate(DIRECTIONS):
                if [x["frame"] for x in per_direction[d]]!=list(range(n)):
                    raise ValueError("missing continuous frames "+clip+" "+d)
                for x,frame in enumerate(per_direction[d]):
                    img=images[(clip,d,x)].crop((l,t,r,b))
                    atlas.alpha_composite(img,(x*w,y*h))
                    filename=f"{clip}_{d}_{x:02d}.png"
                    img.save(actor_out/filename,optimize=True)
                    files.append(filename)
            atlas_file=clip+"_atlas.png"
            atlas.save(actor_out/atlas_file,optimize=True)
            # Small 4-angle contact sheet on neutral backdrop.
            if clip=="idle":
                bg=Image.new("RGBA",(4*(w+12),h+20),(66,71,68,255))
                for idx,d in enumerate(DIRECTIONS):
                    bg.alpha_composite(images[("idle",d,0)].crop((l,t,r,b)),(idx*(w+12)+6,8))
                bg.save(actor_out/"review_4_angles.png")
                cards.append((render_id,bg.convert("RGB")))
            if n>1:
                frames=[]
                for i in range(n):
                    img=images[(clip,"front",i)].crop((l,t,r,b))
                    bg=Image.new("RGBA",(w,h),(87,91,82,255))
                    bg.alpha_composite(img)
                    frames.append(bg.convert("RGB"))
                frames[0].save(actor_out/(clip+"_preview.gif"),save_all=True,
                    append_images=frames[1:],loop=0,duration=125,optimize=False)
            clips[clip]=dict(atlas=render_id+"/"+atlas_file,
                directions=list(DIRECTIONS),frame_count_per_direction=n,
                cell_px=[w,h],anchor_px=anchor,
                sha256=hashlib.sha256((actor_out/atlas_file).read_bytes()).hexdigest(),
                files=files)
        all_results.append(dict(render_id=render_id,actor_id=records[0]["actor_id"],
              kind=records[0]["kind"],height_m=records[0]["height_m"],
              apparel=records[0]["apparel"],held_item_id=records[0]["held_item_id"],
              grey_fraction=records[0]["grey_fraction"],muscle=records[0]["muscle"],
              clips=clips,status="PIXEL_CANDIDATE_NOT_IN_GAME"))
    # One complete report view for phone/founder QA. It is a preview, not an asset.
    if cards:
        maxwidth=max(img.width for _,img in cards)
        hsum=sum(img.height+30 for _,img in cards)
        sheet=Image.new("RGB",(maxwidth+30,hsum),(48,52,49))
        draw=ImageDraw.Draw(sheet)
        y=8
        for label,img in cards:
            draw.text((12,y),label,fill=(240,237,220))
            y+=20
            sheet.paste(img,(12,y))
            y+=img.height+10
        sheet.save(outdir/"actor_review_sheet.png")
    manifest=dict(schema_version=1,rig="ll_biped_v1",tile_px=[80,40],
                  status="RENDERED_CANDIDATE_NOT_GOLDEN_APPROVED_OR_GODOT_INTEGRATED",
                  actors=all_results)
    (outdir/"manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")
    print("LL_ACTOR_PACK_DONE",len(all_results),
          sum(sum(c["frame_count_per_direction"]*4 for c in a["clips"].values()) for a in all_results),
          flush=True)
    return manifest

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    pack(a.input,a.output)

if __name__=="__main__":
    main()
