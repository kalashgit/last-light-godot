"""Produce native-size visual QA sheets without altering the Blender sources.

The PNGs are provisional review sprites, not approved F12 atlas outputs. The
original transparent 768px renders remain available alongside them.
"""
import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw

LABELS=("door", "bonnet", "rear_hatch")
SIZE=214


def make(root: Path) -> None:
    sheet=Image.new("RGB",(SIZE*4,SIZE*len(LABELS)),(66,70,70))
    draw=ImageDraw.Draw(sheet)
    rows=[]
    for row,label in enumerate(LABELS):
        poses=[]
        for index in range(4):
            original=root/label/f"{label}_{index:02}.png"
            with Image.open(original) as img:
                assert img.size==(768,768),original
                sprite=img.convert("RGBA").resize((SIZE,SIZE),Image.Resampling.LANCZOS)
            # Preserve the genuine transparent sprite as well as the
            # composited contact sheet used for contrast inspection.
            out=root/label/f"{label}_{index:02}_214px.png"
            sprite.save(out)
            backdrop=Image.new("RGBA",(SIZE,SIZE),(66,70,70,255))
            backdrop.alpha_composite(sprite)
            sheet.paste(backdrop.convert("RGB"),(SIZE*index,SIZE*row))
            draw.text((SIZE*index+7,SIZE*row+7),f"{label} | frame {index}",
                      fill=(244,240,229))
            poses.append(str(out.relative_to(root)))
        rows.append({"panel":label,"sprites":poses})
    sheet.save(root/"F10_panel_contact_sheet_214px.png")
    (root/"native_preview_manifest.json").write_text(json.dumps({
        "status":"NONCANONICAL_VISUAL_QA_ONLY",
        "native_review_canvas_px":[SIZE,SIZE],
        "layout":"rows=panels, columns=door-open keyframes",
        "lighting":"shared Blender F12 camera/light rig; grey inspection backdrop",
        "f12_atlas_approved":False,"rows":rows},indent=2)+"\n")
    print("F10_NATIVE_REVIEW_PASS 12 transparent 214px poses + sheet")


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("root",type=Path)
    make(parser.parse_args().root)
