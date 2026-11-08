"""F12 image-level QA and review montage for actual Blender pilot frames."""
import hashlib
import json
import sys
from pathlib import Path
from PIL import Image, ImageDraw

root = Path(sys.argv[1]).resolve()
report_path = root / "render_report.json"
if not report_path.exists():
    raise RuntimeError("Blender render_report.json missing: render did not finish")
report = json.loads(report_path.read_text())
results = report["results"]
for slug in ("cube","vehicle","cow","fridge"):
    if slug not in results or results[slug]["status"] == "FAIL":
        raise RuntimeError("missing/failed source output: "+slug)

expected = {"cube":1,"vehicle":16,"cow":16,"fridge":7}
records = report["frames"]
if len(records)!=sum(expected.values()):
    raise RuntimeError("expected 40 frames from actual Blender, saw "+str(len(records)))
checks = {}
montages=[]
for slug,count in expected.items():
    frames=[rec for rec in records if rec["slug"]==slug]
    if len(frames)!=count:
        raise RuntimeError("missing frames "+slug)
    if slug=="vehicle" and set(x["heading"] for x in frames)!=set(range(16)):
        raise RuntimeError("vehicle heading coverage invalid")
    if slug=="cow" and set((x["heading"],x["source_frame"]) for x in frames)!={(h,f) for h in range(8) for f in (1,4)}:
        raise RuntimeError("cow gait samples incomplete")
    if slug=="fridge" and set(x["source_frame"] for x in frames)!=set(range(1,8)):
        raise RuntimeError("fridge hinge frame coverage incomplete")
    columns=8 if slug in ("cow","vehicle") else 7 if slug=="fridge" else 1
    rows=(len(frames)+columns-1)//columns
    tile=200
    montage=Image.new("RGB",(columns*tile,rows*(tile+26)),(39,42,41))
    draw=ImageDraw.Draw(montage)
    a_bboxes=[]
    anchors=[]
    for i,r in enumerate(sorted(frames,key=lambda x:(x["source_frame"],x["heading"]) if slug=="cow" else (x["heading"],x["source_frame"]))):
        path=(root/r["png"]).resolve()
        if not path.is_relative_to(root):
            raise RuntimeError("path traversal in Blender result")
        with Image.open(path) as im:
            if im.mode!="RGBA" or im.size!=(384,384):
                raise RuntimeError("wrong PNG format/dimensions: "+str(path))
            alpha=im.getchannel("A")
            bbox=alpha.getbbox()
            if bbox is None or bbox[0]<2 or bbox[1]<2 or bbox[2]>382 or bbox[3]>382:
                raise RuntimeError("blank or cropped PNG: "+str((path,bbox)))
            a_bboxes.append(bbox)
            anchors.append(tuple(r["origin_px"]))
            if hashlib.sha256(path.read_bytes()).hexdigest()!=r["sha256"]:
                raise RuntimeError("SHA mismatch "+str(path))
            # Checkerboard previews are review-only, never composited into outputs.
            thumb=Image.new("RGBA",(384,384),(64,67,63,255))
            thumb.alpha_composite(im)
            thumb.thumbnail((190,190),Image.Resampling.LANCZOS)
            x=(i%columns)*tile;y=(i//columns)*(tile+26)
            montage.paste(thumb.convert("RGB"),(x+5,y+2))
            draw.text((x+8,y+202),f"{slug} heading {r['heading']:02d} f{r['source_frame']}",fill=(230,229,220))
    if any(max(abs(a[j]-anchors[0][j]) for j in range(2))>.05 for a in anchors):
        raise RuntimeError("ground origin drift "+slug)
    target=root/(slug+"_native_review_sheet.png")
    montage.save(target)
    checks[slug]={"frame_count":len(frames),"alpha_nonempty_pass":True,
                  "not_cropped_pass":True,"source_sha_match":True,
                  "ground_pivot_stability_pass":True,
                  "source_model_sha256":results[slug]["source_sha"],
                  "contact_sheet":target.name}
    montages.append(target.name)
report["image_qa"]=checks
report["status"]="ACTUAL_BLENDER_RENDER_AND_IMAGE_CHECKS_PASS_NOT_GOLDEN_OR_GODOT"
report["not_verified"]=["exact Godot visual projection comparison", "founder Golden review",
                       "F07 biological gait foot-contact", "F01 gameplay hinge collision",
                       "Godot import", "real iPhone/Xogot device"]
report_path.write_text(json.dumps(report,indent=2)+"\n")
print("F12_REAL_FRAMES_QA_PASS",len(records),json.dumps(checks,sort_keys=True))
