"""Package F01 single-frame calibration sprites with explicit nonfinal metadata."""
import argparse
import json
from pathlib import Path

from PIL import Image
from pack_f01_frames import digest,extrude

SPECS={
 "bookcase":{"canonical_candidate":"ll_furniture_bookcase","source_revision":"A00-20261108-B004-r1",
  "bounds_m":[.935,.312,1.584],"pivot_proposal":"floor_rear_centre","collision_role":"static_storage_occludes_sight_proposed"},
 "mattress":{"canonical_candidate":"ll_furniture_mattress","source_revision":"A00-20261108-B002-r1",
  "bounds_m":[.9,1.80397,.2484],"pivot_proposal":"floor_centre","collision_role":"movable_sleep_surface_proposed"}}


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--family",choices=SPECS,required=True)
    p.add_argument("--source",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
    im=Image.open(a.source).convert("RGBA")
    assert im.size==(512,512)
    assert im.getchannel("A").getbbox() is not None
    atlas=Image.new("RGBA",(516,516),(0,0,0,0))
    extrude(atlas,im,2,2,2)
    out=a.output/(a.family+"_single_frame_atlas.png")
    atlas.save(out)
    metadata={"schema":1,"queue":"F01","status":"INTERMEDIATE_ATLAS_NOT_F12_APPROVED",
      **SPECS[a.family],"directions":["calibrated_view_only"],"conditions":["calibration_base"],
      "frames":[{"name":"world_static_00","rect_px":{"x":2,"y":2,"w":512,"h":512},
        "pivot_px":{"x":256,"y":256},"source_sha256":digest(a.source)}],
      "atlas_sha256":digest(out),"rights_reviewed":False,
      "technical_qa":"SOURCE_FILES_PASSED_NOT_INDEPENDENT_W09","godot_tested":False,"founder_approved":False}
    (a.output/"atlas_metadata.json").write_text(json.dumps(metadata,indent=2)+"\n")
    print("F01_STATIC_ATLAS_PASS",a.family,out,flush=True)

if __name__=="__main__":main()
