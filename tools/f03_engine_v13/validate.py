"""Reject blank or missing Blender/Godot images; verify required editable project."""
from pathlib import Path
from PIL import Image
import json,sys
root=Path(__file__).resolve().parent
ev=root/"evidence"
checks={}
for label,path in [("blender",ev/"blender_swatch.png"),("godot",ev/"godot_tilemap.png")]:
    checks[label+"_exists"]=path.exists() and path.stat().st_size>1000 if path.exists() else False
    if checks[label+"_exists"]:
        im=Image.open(path).convert("RGB")
        palette=im.getcolors(maxcolors=10000000) or []
        checks[label+"_nonblank"]=len(palette)>20
        checks[label+"_size"]=im.width>=320 and im.height>=160
        if label=="godot":
            bg=im.getpixel((0,0))
            diff=lambda color:max(abs(color[k]-bg[k]) for k in range(3))>17
            edge=[im.getpixel((x,5)) for x in range(im.width)]+[im.getpixel((x,im.height-6)) for x in range(im.width)]+[im.getpixel((5,y)) for y in range(im.height)]+[im.getpixel((im.width-6,y)) for y in range(im.height)]
            checks["godot_not_clipped"]=sum(map(diff,edge))==0
            checks["godot_has_substantial_terrain"]=sum(diff(color)*count for count,color in palette)>40000
checks["blend_exists"]=(ev/"f03_materials.blend").exists() and (ev/"f03_materials.blend").stat().st_size>10000
checks["native_pass"]="F03_NATIVE_IMPORT_PASS" in (ev/"native.log").read_text() if (ev/"native.log").exists() else False
report={"pass":all(checks.values()),"checks":checks,"canonical_approved":False}
(ev/"validation.json").write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
sys.exit(0 if report["pass"] else 5)
