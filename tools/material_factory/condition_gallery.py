#!/usr/bin/env python3
"""Side-by-side four-condition material QA, not a Blender or Godot render."""
import argparse, json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from generate import MATERIALS, CONDITION_NAMES, material_maps, preview

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",type=Path,default=Path("build/material_factory/condition-gallery.png"))
    parser.add_argument("--size",type=int,default=256)
    args=parser.parse_args()
    recipes=json.loads(MATERIALS.read_text())
    tile=256; header=36; labelw=230
    image=Image.new("RGB",(labelw+4*tile,header+len(recipes)*tile),(224,226,220))
    draw=ImageDraw.Draw(image);font=ImageFont.load_default()
    for condition,name in enumerate(CONDITION_NAMES):
        draw.text((labelw+condition*tile+12,12),f"{condition} / {name}",fill=(28,34,30),font=font)
    for row,recipe in enumerate(recipes):
        y=header+row*tile
        draw.text((10,y+20),recipe["id"].replace("LL_MAT_", ""),fill=(26,30,28),font=font)
        for condition in range(4):
            maps=material_maps(recipe,args.size,condition)
            # Pseudo-light response on a flat sample, not a physical-object render.
            sample=preview(maps,recipe,args.size).resize((tile,tile),Image.Resampling.NEAREST)
            image.paste(sample,(labelw+condition*tile,y))
    args.out.parent.mkdir(parents=True,exist_ok=True)
    image.save(args.out)
    print("LL_CONDITION_GALLERY",str(args.out))

if __name__=="__main__":main()
