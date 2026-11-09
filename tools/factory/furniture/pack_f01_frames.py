"""F01 intermediary atlas and interaction-metadata packer (F12 review required).

python tools/factory/furniture/pack_f01_frames.py --frames build/f01_calibration/refrigerator_v3 --output build/f01_calibration/refrigerator_v4_export
"""
import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate(frames):
    assert len(frames)==7
    images=[Image.open(path).convert("RGBA") for path in frames]
    size=images[0].size
    assert size==(512,512),f"unexpected calibration envelope: {size}"
    assert all(im.size==size for im in images)
    assert len({path.read_bytes() for path in frames})==7,"duplicate animation frame"
    for idx,im in enumerate(images):
        alpha=im.getchannel("A")
        bbox=alpha.getbbox()
        assert bbox is not None and bbox[0]>0 and bbox[1]>0 and bbox[2]<size[0] and bbox[3]<size[1],(idx,bbox)
        assert alpha.getextrema()[0]==0,"transparent background lost"
    return images


def extrude(atlas,image,x,y,amount):
    w,h=image.size
    atlas.paste(image,(x,y))
    for i in range(1,amount+1):
        atlas.paste(image.crop((0,0,1,h)),(x-i,y))
        atlas.paste(image.crop((w-1,0,w,h)),(x+w-1+i,y))
        atlas.paste(image.crop((0,0,w,1)),(x,y-i))
        atlas.paste(image.crop((0,h-1,w,h)),(x,y+h-1+i))
    for dx in range(1,amount+1):
        for dy in range(1,amount+1):
            for corner,crop in [
                ((-dx,-dy),(0,0,1,1)),((w-1+dx,-dy),(w-1,0,w,1)),
                ((-dx,h-1+dy),(0,h-1,1,h)),((w-1+dx,h-1+dy),(w-1,h-1,w,h))]:
                atlas.paste(image.crop(crop),(x+corner[0],y+corner[1]))


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--frames",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--motion",choices=("hinge_open","crisper_open"),default="hinge_open")
    a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
    sources=[a.frames/f"{a.motion}_{i:02d}.png" for i in range(7)]
    images=validate(sources)
    w,h=images[0].size
    extrude_px=2; spacing=4; step=w+2*extrude_px+spacing
    atlas=Image.new("RGBA",(step*len(images),h+2*extrude_px),(0,0,0,0))
    result=[]
    for i,img in enumerate(images):
        x=extrude_px+i*step;y=extrude_px
        extrude(atlas,img,x,y,extrude_px)
        result.append({"name":f"{a.motion}_{i:02d}","frame":i,
          "rect_px":{"x":x,"y":y,"w":w,"h":h},
          "pivot_px":{"x":256,"y":256},
          "duration_ms_proposed":75,
          **({"door_angle_deg":round(-105*i/6,4)} if a.motion=="hinge_open"
             else {"crisper_travel_m":round(.19*i/6,5)}),
          "source_sha256":digest(sources[i])})
    image_path=a.output/f"refrigerator_{a.motion}_atlas.png"
    atlas.save(image_path,optimize=True)
    # Downsampled diagnostic only: not a calibrated F12 game sprite resolution.
    diagnostic=images[-1].resize((128,128),resample=Image.Resampling.LANCZOS)
    diagnostic_path=a.output/"diagnostic_128_not_game_approved.png"
    diagnostic.save(diagnostic_path)
    metadata={"schema":1,"queue":"F01","status":"INTERMEDIATE_ATLAS_NOT_F12_APPROVED",
      "motion":a.motion,
      "canonical_candidate":"ll_furniture_refrigerator","source_revision":"A00-20261108-B001-r1",
      "source_model_status":"NONCANONICAL_REFINEMENT_CALIBRATION",
      "atlas":image_path.name,"atlas_sha256":digest(image_path),
      "frames":result,"coordinate_system":"RGBA top-left pixel origin; local metres for physical data",
      "frame_count":len(result),"directions":["calibrated_view_only"],
      "pivot_policy":"UNTRIMMED_ENVELOPE_ORIGIN_CENTER; verify F12 against Blender world_ground projection",
      "animation_contract":"PROPOSAL_PENDING_W05_W07",
      "proposed_events":[{"at_frame":6,"event":("access_enabled" if a.motion=="hinge_open" else "contents_exposed")}],
      "physical_dimensions_m":{"width":.77,"depth":.71,"height":1.77},
      "footprint_proposal_m":{"x_min":-.385,"x_max":.385,"y_min":-.355,"y_max":.355},
      "hinge_local_proposal_m":{"x":-.37,"y":-.374,"z":.885},
      "door_swing_radius_proposal_m":.77,
      "collision_contract":"PROPOSAL_UNVALIDATED_WITH_ENGINE_OR_WALLS",
      "contents":"EMPTY_NO_BAKED_LOOT","rights_gate":"REVIEW_PENDING",
      "founder_visual_benchmark":{"approved":True,"date":"2026-11-09",
        "scope":"F01 V10 visual benchmark only; not canonical or mass-production release"},
      "founder_approval":False,"mass_production_eligible":False,
      "godot_tested":False,"godot_isolated_fixture_ci":"42543992661",
      "iphone_verified":False}
    (a.output/"atlas_metadata.json").write_text(json.dumps(metadata,indent=2)+"\n")
    print("F01_ATLAS_PACK_PASS",len(result),atlas.size,flush=True)


if __name__=="__main__":main()
