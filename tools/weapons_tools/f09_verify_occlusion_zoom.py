"""Review genuine F09 Godot screenshots under occlusion at actual zoom levels.

Do not infer founder visual signoff from mathematical pixel differences.
Each comparison is source-pixel native scale; contact sheets magnify nearest.
"""
import json
from collections import defaultdict
from pathlib import Path
from PIL import Image, ImageChops, ImageDraw, ImageStat

ROOT=Path(__file__).resolve().parents[2]
AREA=ROOT/"build"/"f09_godot_stage"/"f09_graphical_qa"/"occlusion_v20"
SCENARIOS={"vegetation":{.75,1.0},"furniture":{2.2,3.25},
           "player":{1.0,1.75}}

def crop_near_points(image,points):
    left=max(0,min(p[0] for p in points)-42)
    upper=max(0,min(p[1] for p in points)-70)
    right=min(image.width,max(p[0] for p in points)+42)
    lower=min(image.height,max(p[1] for p in points)+44)
    assert right>left and lower>upper
    return image.crop((left,upper,right,lower))

def main():
    manifest=json.loads((AREA/"f09_occlusion_zoom_manifest.json").read_text())
    entries=manifest["screenshots"]
    assert manifest["scenario_count"]==3 and len(entries)==12
    pair=defaultdict(dict)
    for row in entries:
        assert row["scenario"] in SCENARIOS
        assert float(row["zoom"]) in SCENARIOS[row["scenario"]]
        assert row["variant"] in ("v19","v20")
        assert row["native_sprite_size_px"]==[96,96]
        path=AREA/row["filename"]
        assert path.stat().st_size>15000,path
        im=Image.open(path).convert("RGB")
        assert im.size==(1280,720)
        thumb=im.resize((160,90),Image.Resampling.BOX)
        assert max(ImageStat.Stat(thumb).stddev)>=15
        pair[(row["scenario"],float(row["zoom"]))][row["variant"]]=(im,row)
    assert len(pair)==6
    w,h=432,226
    sheet=Image.new("RGB",(w*2,h*6+45),(26,29,30))
    draw=ImageDraw.Draw(sheet)
    draw.text((8,7),"V19 previous anchors/contour",fill=(240,237,219))
    draw.text((w+8,7),"V20 stable pivot/soft two-tone rim",fill=(240,237,219))
    differences=[]
    for index,((scenario,zoom),items) in enumerate(sorted(pair.items())):
        assert set(items)=={"v19","v20"}
        a,meta_a=items["v19"]
        b,meta_b=items["v20"]
        assert meta_a["screen_contact_points_px"]==meta_b["screen_contact_points_px"]
        points=meta_a["screen_contact_points_px"]
        assert len(points)==3
        # Changed target-local pixels are required; background/HUD motion alone
        # is not sufficient to claim any art or placement change.
        ca=crop_near_points(a,points)
        cb=crop_near_points(b,points)
        assert ca.size==cb.size
        diff=ImageChops.difference(ca,cb)
        assert diff.getbbox() is not None,(scenario,zoom,"no model-local change")
        bbox=diff.getbbox()
        scores=ImageStat.Stat(diff).mean
        differences.append({"scenario":scenario,"zoom":zoom,
                            "local_diff_bbox_px":list(bbox),
                            "mean_rgb_abs_delta":[round(x,3) for x in scores]})
        for col,crop in enumerate((ca,cb)):
            crop.thumbnail((w-16,h-43),Image.Resampling.NEAREST)
            # No bicubic blur or generated enhancements in the contact sheet.
            enlarged=crop.resize((w-16,h-43),Image.Resampling.NEAREST)
            sheet.paste(enlarged,(col*w+8,index*h+50))
        draw.text((8,index*h+32),f"{scenario}  zoom={zoom:.2f}x",
                  fill=(238,226,181))
    sheet_path=AREA/"f09_v19_vs_v20_occlusion_zoom_review.png"
    sheet.save(sheet_path,optimize=True)
    results={"status":"PIXEL_DIFF_QA_PASS_F12_ART_APPROVAL_PENDING",
             "source":"Actual Godot main.tscn gameplay OpenGL screenshots",
             "screenshots_checked":12,"pairs":6,"results":differences,
             "f12_approved":False,"iphone_tested":False,
             "contact_sheet":sheet_path.name}
    (AREA/"f09_occlusion_zoom_qa.json").write_text(json.dumps(results,indent=2)+"\n")
    print("F09_OCCLUSION_ZOOM_AB_COMPARISON_PASS 6 pairs 12 images",flush=True)
if __name__=="__main__":main()
