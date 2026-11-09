#!/usr/bin/env python3
"""Read-only map-plan preview directly from LIVE neighborhood JSON.
Schematic overview, NOT a Godot screenshot or proof of approved visual assets.
"""
from __future__ import annotations
from collections import defaultdict
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
CITY = json.loads((ROOT / "data/neighborhood/showcase_60_v1.json").read_text())
LAB = json.loads((ROOT / "data/neighborhood/house_lab_h01_h02_h03_v1.json").read_text())
OUT = ROOT / "build/neighborhood-showcase"
OUT.mkdir(parents=True, exist_ok=True)
COLORS = {
    "Residential": "#66847b",
    "Commercial": "#a18f6b",
    "Civic / public": "#7795a5",
    "Industrial / utility / rural": "#9a7867",
    "Recreation": "#669574",
    "Special": "#9480a3",
}
BG = "#101b1a"
INK = "#e3ddc9"
ROAD = "#465050"
FONT = ImageFont.load_default(size=15)
SMALL = ImageFont.load_default(size=11)
BIG = ImageFont.load_default(size=25)
MED = ImageFont.load_default(size=18)


def p_iso(x, y, origin, scale):
    return (int(round(origin[0] + (x-y)*40*scale)),
            int(round(origin[1] + (x+y)*20*scale)))


def quad(d, rect, fill, origin, scale, outline=None):
    x,y,w,h = rect
    pts=[p_iso(px,py,origin,scale) for px,py in
         [(x,y),(x+w,y),(x+w,y+h),(x,y+h)]]
    d.polygon(pts, fill=fill, outline=outline)
    return pts


def shape(d, b, fill, origin, scale):
    x,y,w,h=b["footprint"]
    cut=b.get("cutout")
    if cut:
        cx,cy,cw,ch=cut
        coords=[(x,y),(x+w-cw,y),(x+w-cw,y+ch),
                (x+w,y+ch),(x+w,y+h),(x,y+h)]
    else:
        coords=[(x,y),(x+w,y),(x+w,y+h),(x,y+h)]
    d.polygon([p_iso(a,b,origin,scale) for a,b in coords],
              fill=fill, outline="#d5c6a7")


def city_preview():
    img=Image.new("RGB",(2400,1450),BG)
    d=ImageDraw.Draw(img)
    scale=.091
    origin=(900,160)
    d.text((42,25),"LAST LIGHT // 60-ARCHETYPE NEIGHBORHOOD",font=BIG,fill=INK)
    d.text((42,65),"One original showcase instance for every documented type; no Golden art or finished interiors.",font=MED,fill="#a8b7ac")
    quad(d,[0,0,240,220],"#304b3a",origin,scale)
    for i in range(10):
        quad(d,[19+23*i,0,5,220],ROAD,origin,scale)
    for i in range(8):
        quad(d,[0,21+27*i,240,7],ROAD,origin,scale)
    for i,b in enumerate(CITY["buildings"],1):
        tint=COLORS[b["group"]]
        shape(d,b,tint,origin,scale)
        x,y,w,h=b["footprint"]
        cx,cy=p_iso(x+w/2,y+h/2,origin,scale)
        d.text((cx,cy),str(i),font=SMALL,fill="#151c1b",anchor="mm")
        if i<=3:
            d.ellipse([cx-15,cy-15,cx+15,cy+15],outline="#ffe6a0",width=3)
        dx,dy=b["front_door"]
        sidewalk=21+27*int(dy//27)
        d.line([p_iso(dx,dy,origin,scale),
                p_iso(dx,sidewalk,origin,scale)],fill="#a5a399",width=2)
    d.rounded_rectangle((1860,102,2370,1370),radius=12,fill="#172726",outline="#5b7066",width=2)
    d.text((1890,118),"DISTRICT & ARCHETYPE INDEX",font=MED,fill=INK)
    grouped=defaultdict(list)
    for i,b in enumerate(CITY["buildings"],1):
        grouped[b["group"]].append((i,b["archetype_id"]))
    yy=165
    for group,entries in grouped.items():
        d.text((1890,yy),f"{group} ({len(entries)})",font=MED,fill=COLORS[group])
        yy+=24
        for idx,key in entries:
            d.text((1895,yy),f"{idx:02d}   {key.replace('_',' ')}",font=SMALL,fill="#d5d8c9")
            yy+=17
        yy+=14
    d.text((55,1310),"FIRST THREE HOMES (gold circles): SMALL HOUSE / LARGE HOUSE / DUPLEX",font=MED,fill="#f1d895")
    d.text((55,1342),"Schematic preview generated from actual authored JSON. See Godot scene for interactive tour.",font=MED,fill="#abb7af")
    img.save(OUT/"city_60_archetypes_preview.png",optimize=True)


def lab_preview():
    img=Image.new("RGB",(1700,900),BG)
    d=ImageDraw.Draw(img)
    scale=.235
    origin=(540,100)
    d.text((35,24),"LAST LIGHT // THREE AUTHOR-DEFINED HOUSE LABS",font=BIG,fill=INK)
    d.text((35,62),"H01 Oak 12x10  |  H02 Cedar 16x12, two-storey  |  H03 Birch 18x14, L-shaped garage",font=MED,fill="#a8b7ac")
    quad(d,[0,0,96,46],"#344d3b",origin,scale)
    quad(d,[0,22,96,7],ROAD,origin,scale)
    for b in LAB["houses"]:
        for room in b["rooms"]:
            x,y,w,h=room["rect"]
            ox,oy=b["footprint"][:2]
            color={"living":"#8d8874","kitchen":"#88a49a","bedroom":"#a0786d",
                   "hall":"#b2a785","bathroom":"#829aa8","garage":"#737a77",
                   "utility":"#938b73","laundry":"#a59f8e","storage":"#786d62",
                   "pantry":"#927c62"}.get(room["type"],"#918977")
            quad(d,[x+ox,y+oy,w,h],color,origin,scale,outline="#272c2b")
            xx,yy=p_iso(x+ox+w/2,y+oy+h/2,origin,scale)
            d.text((xx,yy),room["id"].split("-")[-1],font=SMALL,fill="#12191a",anchor="mm")
        # Rectangular houses = exact floor; H03 notched at top right.
        shape(d,b,None,origin,scale)
        xx,yy=p_iso(*b["front_door"],origin,scale)
        d.ellipse([xx-7,yy-7,xx+7,yy+7],fill="#f3cc80")
        d.line([(xx,yy),p_iso(b["front_door"][0],22,origin,scale)],fill="#c2bd9f",width=5)
        tx,ty=p_iso(b["footprint"][0]+b["footprint"][2]/2,b["footprint"][1]-3,origin,scale)
        short={"LAB-H01":"OAK / STARTER","LAB-H02":"CEDAR / 2 FLOORS","LAB-H03":"BIRCH / L + GARAGE"}
    d.text((tx,ty-12),b["id"]+"  "+short[b["id"]],font=MED,fill="#ffe0a0",anchor="mm")
    d.text((35,825),"Roof-off floor-plan inspection | H02 upstairs via F in Godot | H03 garage/cutout preserved",font=MED,fill="#d6caa6")
    d.text((35,858),"Room positions trace to LAB A. Props, collision, stairs and final textures remain calibration work.",font=MED,fill="#aab7ad")
    img.save(OUT/"h01_h02_h03_rooms_preview.png",optimize=True)


if __name__ == "__main__":
    city_preview()
    lab_preview()
    print("NEIGHBORHOOD_PREVIEW_CREATED",str(OUT))
