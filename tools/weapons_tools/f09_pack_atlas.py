"""Build F12-compatible candidate atlas at fixed native tool scale.

Cell pitch = 96 px, center placement anchor = (48,48). This is a
PROVISIONAL atlas contract until F12 defines canonical pivot and atlas policy.
"""
import hashlib
import json
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/"build"/"f09_integration_fixture"
IDS=("ll_tools_adjustable_wrench","ll_tools_socket_handle","ll_tools_hand_saw")
def main():
    width,height=1536,288
    atlas=Image.new("RGBA",(width,height),(0,0,0,0))
    records=[]
    seen=set()
    for row,ident in enumerate(IDS):
        cells=[]
        for heading in range(16):
            p=BASE/ident/"world_sprite_96"/f"h{heading:02}.png"
            image=Image.open(p).convert("RGBA")
            assert image.size==(96,96)
            x,y=heading*96,row*96
            region=(x,y,96,96)
            assert region not in seen
            seen.add(region)
            # Byte-exact paste: alpha_composite premultiplies translucent pixels.
            atlas.paste(image,(x,y))
            cells.append({"heading":heading,"region_px":[x,y,96,96],
                          "pivot_px":[48,48],"ground_anchor_px":[48,48],
                          "source_sha256":hashlib.sha256(p.read_bytes()).hexdigest()})
        records.append({"source_asset_id":ident,"row":row,"frames":cells,
                        "anchor_status":"PROVISIONAL_NOT_F12_SIGNED_OFF"})
    out=BASE/"f09_candidate_16_heading_atlas.png"
    atlas.save(out,optimize=True)
    # Pixel-perfect atlas verification, no rotation/trimming/rescaling.
    check=Image.open(out).convert("RGBA")
    assert check.size==(width,height)
    for record in records:
        for frame in record["frames"]:
            x,y,w,h=frame["region_px"]
            source=Image.open(BASE/record["source_asset_id"]/"world_sprite_96"/
                             f'h{frame["heading"]:02}.png').convert("RGBA")
            assert check.crop((x,y,x+w,y+h)).tobytes()==source.tobytes(),frame
    (BASE/"f09_candidate_16_heading_atlas.json").write_text(json.dumps({
        "schema_version":1,"asset_count":3,"frame_count":48,
        "atlas":"f09_candidate_16_heading_atlas.png",
        "dimensions_px":[width,height],"tile_pitch_px":[96,96],
        "camera_scale_source":"F12 fixed hero.ORTHO; no per-asset fit",
        "f12_approved":False,"records":records},indent=2)+"\n")
    print("F09_F12_ATLAS_PIXEL_EXACT_PASS 48 provisional headings",flush=True)
if __name__=="__main__":main()
