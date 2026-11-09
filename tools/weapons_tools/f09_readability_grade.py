"""F12 candidate native-scale readability and contact-ground anchor calibration.

Only edits the existing 96x96 RGBA sprites (no scaling). Adds a bounded
one-pixel neutral dark silhouette edge to preserve tool recognition on mixed
foliage, plaster, pavement and timber. All source pixels remain unchanged.
Ground anchor derives from the lower opaque contour of each actual heading.
"""
from pathlib import Path
import json
from PIL import Image, ImageFilter, ImageChops

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/"build"/"f09_integration_fixture"
IDS=("ll_tools_adjustable_wrench","ll_tools_socket_handle","ll_tools_hand_saw")
MIN_ALPHA=48
SURFACES={"foliage":(58,75,56),"concrete":(149,150,136),
          "asphalt":(68,74,72),"plaster":(188,187,166)}

def anchor(alpha):
    bb=alpha.getbbox()
    assert bb is not None
    # Foot-point is the average horizontal location among lowest 3px
    # of actually occupied geometry; not the arbitrary 48,48 canvas center.
    pts=[]
    for y in range(max(bb[1],bb[3]-3),bb[3]):
        for x in range(bb[0],bb[2]):
            if alpha.getpixel((x,y))>=MIN_ALPHA:
                pts.append((x,y))
    assert pts
    foot_x=round(sum(p[0] for p in pts)/len(pts))
    foot_y=bb[3]-1
    assert 8<foot_x<88 and 8<foot_y<88
    return [foot_x,foot_y]

def readability_image(source):
    original=source.convert("RGBA")
    a=original.getchannel("A")
    expanded=a.filter(ImageFilter.MaxFilter(3))
    # Outer 1px silhouette matte, no internal recoloring and no resizing.
    outer=ImageChops.subtract(expanded,a)
    edge=Image.new("RGBA",original.size,(23,27,25,0))
    edge.putalpha(outer.point(lambda v:round(v*.78)))
    edge.alpha_composite(original)
    assert edge.size==original.size
    assert edge.getchannel("A").getbbox() is not None
    return edge

def main():
    evidence=[]
    for ident in IDS:
        folder=BASE/ident
        out=folder/"world_sprite_96_readable"
        out.mkdir(parents=True,exist_ok=True)
        headings=[]
        for heading in range(16):
            src=Image.open(folder/"world_sprite_96"/f"h{heading:02}.png").convert("RGBA")
            rim=readability_image(src)
            dest=out/f"h{heading:02}.png"
            rim.save(dest,optimize=True)
            anchor_xy=anchor(src.getchannel("A"))
            before=sum(1 for v in src.getchannel("A").getdata() if v>MIN_ALPHA)
            after=sum(1 for v in rim.getchannel("A").getdata() if v>MIN_ALPHA)
            original_bounds=src.getchannel("A").getbbox()
            grade_bounds=rim.getchannel("A").getbbox()
            assert after>=before and after<=before*2.5,(ident,heading,before,after)
            # Bound the actual contour spread to a strict single pixel on
            # every side; percent growth alone penalizes narrow metal tools.
            assert (grade_bounds[0]>=original_bounds[0]-1 and
                    grade_bounds[1]>=original_bounds[1]-1 and
                    grade_bounds[2]<=original_bounds[2]+1 and
                    grade_bounds[3]<=original_bounds[3]+1),(ident,heading,"rim too wide")
            assert src.getchannel("A").getbbox()!=None
            # Critical: all original interior RGB samples remain unchanged.
            assert all(rim.getpixel((x,y))[:3]==src.getpixel((x,y))[:3]
                       for y in range(96) for x in range(96)
                       if src.getpixel((x,y))[3]==255)
            headings.append({"heading":heading,"ground_anchor_px":anchor_xy,
                             "opaque_source_px":before,"opaque_with_rim_px":after,
                             "world_scale_changed":False})
        evidence.append({"asset_id":ident,"heading_count":16,"frames":headings})
    (BASE/"f09_f12_readability_report.json").write_text(json.dumps({
        "status":"F12_VISUAL_CANDIDATE_NOT_APPROVED",
        "native_px":[96,96],"scale_factor":1.0,
        "contour_width_px":1,"source_model_unmodified":True,
        "headings":evidence},indent=2)+"\n")
    print("F09_F12_CONTOUR_AND_CONTACT_ANCHORS_PASS 48",flush=True)

if __name__=="__main__":main()
