#!/usr/bin/env python3
"""Optional native-size palette clustering for original 2.5D RGBA sprites.

Produces visual candidates, not automatic approved replacements. Never changes
alpha, pivots, geometry or game-world scale. No proprietary reference pixels.
"""
import argparse
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter


def refine_rgba(sprite, colors=80, edge_strength=0.65):
    if sprite.mode!="RGBA":
        raise ValueError("Expected straight-alpha RGBA sprite")
    if not 16<=colors<=256:
        raise ValueError("Palette size must be 16..256")
    if not 0<=edge_strength<=2:
        raise ValueError("edge_strength must be 0..2")
    arr=np.asarray(sprite,dtype=np.uint8)
    alpha=arr[:,:,3].copy()
    rgb=arr[:,:,:3].copy()
    opaque=alpha>=64
    if not np.any(opaque):
        raise ValueError("No visible source pixels")
    # Transparent pixels cannot consume palette entries or shift opaque colors.
    average=np.median(rgb[opaque],axis=0).astype(np.uint8)
    rgb[~opaque]=average
    # Sharpen structural boundaries (recessed wood panels, cushion piping,
    # metal seams) before clustering tones. The high threshold protects tiny
    # cloth/wood fibres from exploding into photographic pixel noise.
    shaped=Image.fromarray(rgb,"RGB")
    if edge_strength:
        shaped=shaped.filter(ImageFilter.UnsharpMask(
            radius=.95, percent=round(88*edge_strength), threshold=3))
    quantized=shaped.quantize(
        colors=colors, method=Image.Quantize.MEDIANCUT,
        dither=Image.Dither.NONE).convert("RGB")
    output=np.dstack((np.asarray(quantized),alpha))
    return Image.fromarray(output,"RGBA")


def comparison(original,refined,zoom_values=(1,2.2,3.25)):
    panels=[]
    for z in zoom_values:
        size=(round(original.width*z),round(original.height*z))
        pad=12
        bg=Image.new("RGBA",(size[0]*2+pad*3,size[1]+pad*2+20),(100,115,105,255))
        d=ImageDraw.Draw(bg)
        for col,im in enumerate((original,refined)):
            scaled=im.resize(size,Image.Resampling.NEAREST)
            bg.alpha_composite(scaled,(pad+col*(size[0]+pad),pad+20))
        d.text((pad,5),f"ORIGINAL {z:.2f}x",fill=(245,245,237))
        d.text((pad*2+size[0],5),f"REFINED {z:.2f}x",fill=(245,245,237))
        panels.append(bg.convert("RGB"))
    width=max(p.width for p in panels)
    total=sum(p.height for p in panels)
    canvas=Image.new("RGB",(width,total),(229,231,225))
    y=0
    for p in panels:
        canvas.paste(p,(0,y));y+=p.height
    return canvas


def main():
    p=argparse.ArgumentParser()
    p.add_argument("source",type=Path)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--colors",type=int,default=80)
    p.add_argument("--edge-strength",type=float,default=.65)
    a=p.parse_args()
    source=Image.open(a.source).convert("RGBA")
    refined=refine_rgba(source,a.colors,a.edge_strength)
    a.out.mkdir(parents=True,exist_ok=True)
    refined.save(a.out/"pixel-refined.png")
    comparison(source,refined).save(a.out/"comparison.png")
    print("LL_PIXEL_REFINEMENT_CANDIDATE",source.size,a.colors,a.edge_strength,a.out)

if __name__=="__main__":main()
