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
checks["blend_exists"]=(ev/"f03_materials.blend").exists() and (ev/"f03_materials.blend").stat().st_size>10000
checks["native_pass"]="F03_NATIVE_IMPORT_PASS" in (ev/"native.log").read_text() if (ev/"native.log").exists() else False
report={"pass":all(checks.values()),"checks":checks,"canonical_approved":False}
(ev/"validation.json").write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
sys.exit(0 if report["pass"] else 5)
