"""Alpha-safe one-heading contact sheet for the experimental front door clip."""
import argparse
import json
from pathlib import Path
from PIL import Image,ImageDraw


def pack(raw,dest):
    m=json.loads((raw/"manifest.json").read_text())
    frames=[Image.open(raw/f["png"]).convert("RGBA") for f in m["frames"]]
    assert len(frames)==4
    boxes=[f.getchannel("A").getbbox() for f in frames]
    crop=(min(b[0] for b in boxes)-5,min(b[1] for b in boxes)-5,
          max(b[2] for b in boxes)+5,max(b[3] for b in boxes)+5)
    w=crop[2]-crop[0];h=crop[3]-crop[1]
    dest.mkdir(parents=True,exist_ok=True)
    sheet=Image.new("RGB",(w*4,h+30),(68,78,72))
    for idx,frame in enumerate(frames):
        cell=frame.crop(crop).resize((w,h),Image.Resampling.NEAREST)
        background=Image.new("RGBA",(w,h),(68,78,72,255))
        background.alpha_composite(cell)
        sheet.paste(background.convert("RGB"),(idx*w,30))
        ImageDraw.Draw(sheet).text((idx*w+5,8),f"OPEN {m['frames'][idx]['angle_deg']:02d} deg",fill="white")
    sheet.save(dest/"door_open_review.png")
    # Inspect all four exported poses at native gameplay sprite width.
    native_width=214
    native_height=max(1,round(h*native_width/w))
    native=Image.new("RGB",(native_width*4,native_height+24),(68,78,72))
    native_draw=ImageDraw.Draw(native)
    for idx,frame in enumerate(frames):
        cell=frame.crop(crop).resize((native_width,native_height),Image.Resampling.NEAREST)
        layer=Image.new("RGBA",(native_width,native_height),(68,78,72,255))
        layer.alpha_composite(cell)
        native.paste(layer.convert("RGB"),(idx*native_width,24))
        native_draw.text((idx*native_width+4,6),
                         f"{m['frames'][idx]['angle_deg']:02d}deg",fill="white")
    native.save(dest/"door_open_gameplay_214px.png")
    print("F10_DOOR_SHEET",w,h)
    print("F10_DOOR_GAMEPLAY_SHEET",native_width,native_height)


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--input",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    pack(a.input,a.output)
