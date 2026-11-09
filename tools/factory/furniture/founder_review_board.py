"""Build a large, honest three-state F01 visual review board from actual Blender PNGs."""
import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def checker(size,step=20):
    image=Image.new("RGBA",size,(92,96,98,255))
    draw=ImageDraw.Draw(image)
    for y in range(0,size[1],step):
        for x in range(0,size[0],step):
            if (x//step+y//step)%2:
                draw.rectangle((x,y,x+step-1,y+step-1),fill=(105,109,110,255))
    return image


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source",required=True,type=Path)
    opt=p.parse_args()
    base=opt.source.resolve()
    states=[("Closed door",base/"hinge_open_00.png"),
            ("Open refrigerator",base/"hinge_open_06.png"),
            ("Crisper extended",base/"crisper_open_06.png")]
    out=Image.new("RGB",(1450,680),(28,34,38))
    draw=ImageDraw.Draw(out)
    draw.text((32,24),"LAST LIGHT — F01 REFRIGERATOR | V10 ART REVIEW",fill=(232,238,230))
    draw.text((32,47),"Real Blender 3D renders; models, dimensions and animation remain editable. Founder review required.",fill=(164,187,182))
    for i,(name,path) in enumerate(states):
        im=Image.open(path).convert("RGBA")
        bbox=im.getchannel("A").getbbox()
        assert bbox is not None
        margin=14
        crop=im.crop((max(0,bbox[0]-margin),max(0,bbox[1]-margin),
                      min(im.width,bbox[2]+margin),min(im.height,bbox[3]+margin)))
        max_w,max_h=390,445
        scale=min(max_w/crop.width,max_h/crop.height)
        enlarged=crop.resize((round(crop.width*scale),round(crop.height*scale)),Image.Resampling.LANCZOS)
        x=26+i*474;y=89
        bg=checker((442,478),22)
        bg.alpha_composite(enlarged,((bg.width-enlarged.width)//2,(bg.height-enlarged.height)//2))
        out.paste(bg.convert("RGB"),(x,y))
        draw.text((x+8,y+483),name,fill=(234,235,219))
        draw.text((x+8,y+509),"Full-resolution crop for review; not native sprite scale",fill=(158,171,173))
    draw.text((32,648),"NOT GOLDEN APPROVED  •  128px QA contact sheets supplied separately  •  F11/F12 and real gameplay acceptance pending",fill=(237,178,136))
    dest=base/"founder_review_board.png"
    out.save(dest)
    print("F01_FOUNDER_REVIEW_BOARD_CREATED",dest)


if __name__=="__main__":
    main()
