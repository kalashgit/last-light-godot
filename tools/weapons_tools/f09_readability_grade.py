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

def v19_reference(source):
    """Exact previous 1px charcoal edge, retained for fair A/B rendering."""
    original=source.convert("RGBA")
    alpha=original.getchannel("A")
    outer=ImageChops.subtract(alpha.filter(ImageFilter.MaxFilter(3)),alpha)
    edge=Image.new("RGBA",original.size,(23,27,25,0))
    edge.putalpha(outer.point(lambda v:round(v*.78)))
    edge.alpha_composite(original)
    return edge


def readability_image(source):
    """F20: subtle 1px two-tone contact contour, never scaling geometry.

    On shadow edges use low-opacity charcoal; on upper-left-lit edges use a
    desaturated warm steel highlight. This preserves recognition on foliage
    *and* pale interiors without the previous uniform near-black sticker rim.
    """
    original=source.convert("RGBA")
    alpha=original.getchannel("A")
    expanded=alpha.filter(ImageFilter.MaxFilter(3))
    rim=ImageChops.subtract(expanded,alpha)
    out=Image.new("RGBA",original.size,(0,0,0,0))
    a=alpha.load()
    r=rim.load()
    p=out.load()
    for y in range(96):
        for x in range(96):
            opacity=r[x,y]
            if not opacity:
                continue
            # Upper-left pixels are lit when solid material lies to their SE.
            se=max(a[min(95,x+1),y],a[x,min(95,y+1)],
                   a[min(95,x+1),min(95,y+1)])
            nw=max(a[max(0,x-1),y],a[x,max(0,y-1)],
                   a[max(0,x-1),max(0,y-1)])
            if se>nw and se>=MIN_ALPHA:
                p[x,y]=(181,169,143,round(opacity*.39))
            else:
                p[x,y]=(23,29,27,round(opacity*.52))
    out.alpha_composite(original)
    return out


def main():
    evidence=[]
    for ident in IDS:
        folder=BASE/ident
        out=folder/"world_sprite_96_readable"
        out.mkdir(parents=True,exist_ok=True)
        reference=folder/"world_sprite_96_v19_reference"
        reference.mkdir(parents=True,exist_ok=True)
        headings=[]
        for heading in range(16):
            src=Image.open(folder/"world_sprite_96"/f"h{heading:02}.png").convert("RGBA")
            rim=readability_image(src)
            v19_reference(src).save(reference/f"h{heading:02}.png",optimize=True)
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
            headings.append({"heading":heading,"ground_contact_px":anchor_xy,
                             "pivot_px":[48,48],
                             "opaque_source_px":before,"opaque_with_rim_px":after,
                             "world_scale_changed":False})
        evidence.append({"asset_id":ident,"heading_count":16,"frames":headings})
    # Pack a separate REVIEW atlas of the graded frames; preserve the
    # original pixel-exact F12 candidate atlas as immutable reference.
    atlas=Image.new("RGBA",(16*96,3*96),(0,0,0,0))
    atlas_records=[]
    for row,ident in enumerate(IDS):
        frames=[]
        for heading in range(16):
            frame=Image.open(BASE/ident/"world_sprite_96_readable"/
                             f"h{heading:02}.png").convert("RGBA")
            rect=[heading*96,row*96,96,96]
            atlas.paste(frame,(rect[0],rect[1]))
            foot=evidence[row]["frames"][heading]["ground_contact_px"]
            frames.append({"heading":heading,"rect_px":rect,
                           "pivot_px":[48,48],"contact_point_px":foot,
                           "source_id":ident})
        atlas_records.append({"asset_id":ident,"frames":frames})
    atlas_path=BASE/"f09_f12_readable_candidate_atlas.png"
    atlas.save(atlas_path,optimize=True)
    atlas_check=Image.open(atlas_path).convert("RGBA")
    for record in atlas_records:
        for frame in record["frames"]:
            x,y,w,h=frame["rect_px"]
            expected=Image.open(BASE/record["asset_id"]/"world_sprite_96_readable"/
                                f'h{frame["heading"]:02}.png').convert("RGBA")
            assert atlas_check.crop((x,y,x+w,y+h)).tobytes()==expected.tobytes()
    (BASE/"f09_f12_readable_candidate_atlas.json").write_text(json.dumps({
        "status":"F12_PROVISIONAL_NATIVE_SCALE_REVIEW_ONLY",
        "atlas":"f09_f12_readable_candidate_atlas.png",
        "size_px":[1536,288],"cells":48,
        "resampling":"NONE","scale_multiplier":1,
        "anchor_calibration":"fixed world pivot (48,48), independent visible contact estimate",
        "records":atlas_records},indent=2)+"\n")
    print("F09_F12_READABLE_ATLAS_PIXEL_EXACT_PASS 48",flush=True)
    (BASE/"f09_f12_readability_report.json").write_text(json.dumps({
        "status":"F12_VISUAL_CANDIDATE_NOT_APPROVED",
        "native_px":[96,96],"scale_factor":1.0,
        "contour_width_px":1,"source_model_unmodified":True,
        "pivot_fixed_all_headings_px":[48,48],\n        "previous_v19_comparison_frames":48,
        "headings":evidence},indent=2)+"\n")
    print("F09_F12_CONTOUR_AND_CONTACT_ANCHORS_PASS 48",flush=True)

if __name__=="__main__":main()
