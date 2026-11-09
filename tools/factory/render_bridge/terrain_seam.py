"""CAL-05 noncanonical grass/asphalt diamond seam fixture at 80x40.

This is a pixel-grid adjacency and alpha check, not F11 material approval.
"""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image

SIZE=(240,160)
TILE=(80,40)
CENTERS=((80,60),(120,80))

def diamond(cx,cy,x,y):
    return abs((x+0.5-cx)/40)+abs((y+0.5-cy)/20)<1

def generate(out):
    out=Path(out).resolve()
    if out.exists():
        raise FileExistsError(str(out))
    out.mkdir(parents=True)
    masks=[]
    for center in CENTERS:
        masks.append({(x,y) for y in range(SIZE[1]) for x in range(SIZE[0]) if diamond(*center,x,y)})
    assert len(masks[0])==len(masks[1])==1600, "expected 1600 pixels per 80x40 diamond"
    assert not masks[0].intersection(masks[1]), "adjacent tiles overlap"
    grass=Image.new("RGBA",SIZE,(0,0,0,0))
    asphalt=Image.new("RGBA",SIZE,(0,0,0,0))
    for layer,mask,base in [(grass,masks[0],(69,113,58)),(asphalt,masks[1],(87,87,87))]:
        for x,y in mask:
            # Deterministic fine variation without opaque backgrounds.
            n=((x*47+y*71+(x*y)%29)%11)-5
            layer.putpixel((x,y),(*[max(0,min(255,v+n)) for v in base],255))
    merged=Image.alpha_composite(grass,asphalt)
    union=masks[0]|masks[1]
    gaps=[]
    for y in range(SIZE[1]):
        xs=sorted(x for x,yy in union if yy==y)
        if xs:
            gaps.extend((y,x0,x1) for x0,x1 in zip(xs,xs[1:]) if x1-x0>1)
    if gaps:
        raise AssertionError("discontinuous rasterized seam: "+str(gaps[:3]))
    # Audit actual raster alpha, not merely the mathematical tile masks.
    # An accidental omitted pixel, merged opacity leak, or invisible island
    # must fail even when the ideal geometric polygons still agree.
    for image, mask, name in ((grass, masks[0], "grass"), (asphalt, masks[1], "asphalt"), (merged, union, "composite")):
        observed = {(x,y) for y in range(SIZE[1]) for x in range(SIZE[0])
                    if image.getpixel((x,y))[3] > 0}
        if observed != mask:
            raise AssertionError(name+" raster alpha mismatch with tile geometry")
        if any(image.getpixel((x,y))[3] != 255 for x,y in observed):
            raise AssertionError(name+" has partial-alpha pixels on pixel-exact tile")
    for name,img in [("grass.png",grass),("asphalt.png",asphalt),("seam_preview.png",merged)]:
        img.save(out/name)
    report={"fixture":"CAL-05","canonical_status":"NONCANONICAL_TILE_SEAM_ONLY",
            "tile_pixels":list(TILE),"neighbor_delta_pixels":[40,20],
            "centers":[list(c) for c in CENTERS],
            "tile_alpha_coverage_pixels":[len(m) for m in masks],
            "overlap_pixels":0,"row_gap_count":len(gaps),
            "raster_mask_matches_geometry":True,"all_filled_pixels_opaque":True,
            "files":{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.glob("*.png"))}}
    (out/"report.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print("F12_CAL05_RASTER_SEAM_PASS",json.dumps(report))
    return report

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--output",type=Path,required=True)
    generate(p.parse_args().output)
