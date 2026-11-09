"""Transparent-frame and native-size QA contact sheet for F01 refrigerator.

python tools/factory/furniture/qa_f01_refrigerator.py \
  --input build/f01_calibration/refrigerator_v8b

Visual study only: F12 scale, pivot, trim and atlas acceptance is independent.
"""
import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFont


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def alpha_bbox(frame):
    return frame.getchannel("A").getbbox()


def checker(size, block=16):
    image=Image.new("RGBA",(size,size),(83,87,88,255))
    draw=ImageDraw.Draw(image)
    for y in range(0,size,block):
        for x in range(0,size,block):
            if (x//block+y//block)%2:
                draw.rectangle((x,y,x+block-1,y+block-1),fill=(99,103,105,255))
    return image


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--input",required=True,type=Path)
    parser.add_argument("--motion",choices=("hinge_open","crisper_open"),default="hinge_open")
    opt=parser.parse_args()
    folder=opt.input.resolve()
    paths=[folder/f"{opt.motion}_{i:02d}.png" for i in range(7)]
    frames=[Image.open(p).convert("RGBA") for p in paths]
    if any(im.size!=(512,512) for im in frames):
        raise AssertionError("F01 calibration frame shape changed; recheck F12 contract")
    bboxes=[alpha_bbox(im) for im in frames]
    if any(b is None for b in bboxes):
        raise AssertionError("Blank frame")
    # Do not hard-code the camera scale: only reject clipped sprites and
    # invisible state changes. F12 owns world pixels-per-meter acceptance.
    if any(min(b[0],b[1],512-b[2],512-b[3])<12 for b in bboxes):
        raise AssertionError("A render is clipped or too near the edge")
    # A drawer can move entirely *inside* an unchanged alpha silhouette. PIL's
    # RGBA getbbox() consults the alpha difference (zero), masking real RGB
    # motion; compare RGB as well as alpha to catch both animation types.
    if any(ImageChops.difference(frames[i].convert("RGB"),frames[i+1].convert("RGB")).getbbox() is None
           and ImageChops.difference(frames[i].getchannel("A"),frames[i+1].getchannel("A")).getbbox() is None
           for i in range(6)):
        raise AssertionError("Adjacent animation frames are identical")
    sheet=Image.new("RGB",(7*244,2*254+76),(33,37,40))
    draw=ImageDraw.Draw(sheet)
    draw.text((15,9),f"LAST LIGHT F01 - {opt.motion} | geometry/material calibration - NOT GOLDEN",fill=(230,231,217))
    draw.text((15,29),"TOP: transparent 512px source downscaled to 224px. BOTTOM: 128px native-size diagnostic, 2x nearest zoom.",fill=(175,190,190))
    for i,frame in enumerate(frames):
        x=10+i*244
        for row in (0,1):
            y=60+row*254
            bg=checker(224,16 if row==0 else 8)
            fg=frame.resize((224,224),Image.Resampling.LANCZOS) if row==0 else frame.resize((128,128),Image.Resampling.LANCZOS).resize((224,224),Image.Resampling.NEAREST)
            bg.alpha_composite(fg)
            sheet.paste(bg.convert("RGB"),(x,y))
            movement=f"{round(-105*i/6)} deg" if opt.motion=="hinge_open" else f"{.19*i/6:.3f} m"
            draw.text((x,y+228),f"frame {i:02d} / {movement}",fill=(208,214,212))
    png=folder/("qa_contact_sheet.png" if opt.motion=="hinge_open" else "qa_contact_sheet_crisper.png")
    sheet.save(png)
    report={
      "status":"NONCANONICAL_VISUAL_DIAGNOSTIC_NOT_F12_OR_GOLDEN_APPROVED",
      "motion":opt.motion,
      "frame_count":len(frames),"frame_size_px":[512,512],
      "alpha_bboxes_xyxy":[list(b) for b in bboxes],
      "clear_margins_px":[min(b[0],b[1],512-b[2],512-b[3]) for b in bboxes],
      "adjacent_frames_visibly_distinct":True,
      "native_scale_128px":"visual diagnostic only; F12 pixel density unresolved",
      "sha256":{"contact_sheet":sha(png),**{p.name:sha(p) for p in paths}},
    }
    report_name="render_qa.json" if opt.motion=="hinge_open" else "render_qa_crisper.json"
    (folder/report_name).write_text(json.dumps(report,indent=2)+"\n")
    print("F01_RENDER_QA_PASS",json.dumps({"bboxes":bboxes,"minimum_margin_px":min(report["clear_margins_px"])},separators=(",",":")))


if __name__=="__main__":
    main()
