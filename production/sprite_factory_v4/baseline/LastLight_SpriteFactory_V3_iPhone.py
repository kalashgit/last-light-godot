"""LAST LIGHT — SINGLE FILE ORIGINAL SPRITE FACTORY v3.0

Python 3.11 + Pillow only. Runs from the iPhone CodePad editor (Run button).

This script DRAWS original procedural objects from semantic archetype recipes.
It does not recolor copyrighted sprites and does not call any AI image model.
It cannot interpret arbitrary prose into unique polished pixel artwork: unknown
archetypes are rejected, not silently treated as the same sprite. Its output
is PROTOTYPE / NEEDS_HUMAN_QA, never certified GOLDEN artwork.

Instructions:
  FIRST RUN: DEMO_MODE=True, DRY_RUN=False => draws 24 DISTINCT draft icons.
  Review exported contact sheets at 32/48/64 px. Approve/fix artwork first.
  PRODUCTION: DEMO_MODE=False, load input briefs from BASE/recipes.jsonl.
  To generate variations, set VARIANTS_PER_RECIPE e.g. 3, 10, 100.
  For 100,000+ assets use START_AT, MAX_ITEMS, CHUNK_SIZE and restart in
  separate chunks. Finished individual PNGs are skipped if RESUME=True.
  Export ZIPs can be shared with Codex for an audited Godot import.

The script prints BASE and ZIP locations; CodePad may use private/temporary
storage. Use CUSTOM_WORK_FOLDER when the app supports a Files-accessible path.
Do not rely on /tmp for long-term storage.

Final Godot paths are PROPOSALS until the actual repository is inspected:
art/items/<family>/<slug>/icon_<variant>.png. Nothing is auto-imported.
"""
import hashlib
import json
import math
import random
import re
import tempfile
import zipfile
from pathlib import Path
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

# ============================ SETTINGS ============================
DEMO_MODE = True
DRY_RUN = False
CUSTOM_WORK_FOLDER = ""     # Example: a CodePad-accessible Documents directory.
WORK_FOLDER_NAME = "LAST_LIGHT_FACTORY_V3"
VARIANTS_PER_RECIPE = 1      # 1 for the 24-icon approval set.
START_AT = 0                 # Global zero-based output index for queued jobs.
MAX_ITEMS = 24               # 0 = everything; use 500 or 1000 for iPhone.
CHUNK_SIZE = 250             # ZIP group size; does NOT load all sprites in RAM.
RESUME = True                # Skip successfully existing output files.
ZIP_EVERY_RUN = True
CONTACT_SHEET_SIZE = 24      # One contact sheet per 24 processed items.
CONTACT_SHEET_SCALE = 3
PRINT_EVERY = 100
MAX_TOTAL_JOBS = 2_000_000   # Safety ceiling for accidental configuration.
STYLE_VERSION = "LAST_LIGHT_BIBLE_V2_PROCEDURAL_DRAFT_V3"
SEED = 20261106
# ==================================================================

# Unique semantic references; these are independently authored original object
# briefs, NOT repackaged / traced sprites from another game.
DEMO_BRIEFS = [
    ("food", "canned_beans", "can", "steel", "#A36A4F", "Tin can with abstract ochre label"),
    ("food", "canned_peas", "can", "steel", "#667A5B", "Tin can with subdued green panel"),
    ("food", "apple", "fruit", "organic", "#A55642", "Red apple with leaf and uneven shape"),
    ("food", "pear", "fruit", "organic", "#87934E", "Pear with green rind and narrow shoulder"),
    ("medical", "first_aid_kit", "case", "plastic", "#B8BEB4", "Hard medical box, generic cross sign"),
    ("medical", "bandage_box", "box", "cardboard", "#CABDA8", "Matte medical packaging with stripe"),
    ("tools", "claw_hammer", "hammer", "steel_wood", "#70808B", "Claw hammer, metal head and wooden handle"),
    ("tools", "ball_peen_hammer", "hammer", "steel_wood", "#77858B", "Ball peen hammer, rounded end"),
    ("tools", "flathead_screwdriver", "screwdriver", "steel_plastic", "#A56D4E", "Slotted screwdriver with plastic grip"),
    ("tools", "phillips_screwdriver", "screwdriver", "steel_plastic", "#63778A", "Cross-head screwdriver with dark grip"),
    ("tools", "adjustable_wrench", "wrench", "steel", "#849198", "Adjustable open-jaw wrench"),
    ("tools", "pipe_wrench", "wrench", "steel", "#A46555", "Pipe wrench with heavy angular jaw"),
    ("materials", "wooden_plank", "plank", "wood", "#957455", "Solid cut plank with end grain"),
    ("materials", "steel_bar", "bar", "steel", "#87959A", "Rectangular steel stock"),
    ("materials", "duct_tape", "tape", "rubber", "#686E6D", "Roll of dark industrial tape"),
    ("materials", "rope_coil", "rope", "fabric", "#B49B70", "Coiled utility cord"),
    ("containers", "rucksack", "backpack", "fabric", "#68765D", "Worn canvas backpack with pockets"),
    ("containers", "tool_bag", "bag", "fabric", "#8F7357", "Rectangular soft bag with handles"),
    ("clothing", "work_gloves", "gloves", "leather", "#937656", "Pair of utility gloves"),
    ("clothing", "winter_beanie", "hat", "fabric", "#616F7B", "Ribbed knitted cap"),
    ("electronics", "handheld_radio", "radio", "plastic", "#616B71", "Portable radio with antenna"),
    ("electronics", "flashlight", "flashlight", "metal", "#808991", "Compact metal torch"),
    ("survival", "water_bottle", "bottle", "plastic", "#6E99A0", "Reusable bottle with cap"),
    ("survival", "camping_mug", "mug", "metal", "#7B898A", "Metal camp mug and side handle"),
]

SUPPORTED = {"can", "fruit", "case", "box", "hammer", "screwdriver", "wrench",
             "plank", "bar", "tape", "rope", "backpack", "bag", "gloves", "hat",
             "radio", "flashlight", "bottle", "mug"}


def writable(path):
    try:
        path.mkdir(parents=True, exist_ok=True)
        p = path / ".ll_probe"
        p.write_bytes(b"ok")
        p.unlink()
        return True
    except (OSError, ValueError):
        return False


def pick_base():
    if CUSTOM_WORK_FOLDER.strip():
        p = Path(CUSTOM_WORK_FOLDER).expanduser()
        if not writable(p):
            raise RuntimeError("CUSTOM_WORK_FOLDER not writable: " + str(p))
        return p
    options = []
    if "__file__" in globals():
        p = Path(__file__).resolve().parent
        if p != Path(p.anchor):
            options.append(p / WORK_FOLDER_NAME)
    options += [Path.home() / "Documents" / WORK_FOLDER_NAME,
                Path.home() / WORK_FOLDER_NAME,
                Path(tempfile.gettempdir()) / WORK_FOLDER_NAME]
    for p in options:
        if writable(p):
            return p
    raise RuntimeError("No writable folder. Configure CUSTOM_WORK_FOLDER.")


def hexrgb(value):
    s = str(value).lstrip("#")
    if len(s) != 6 or not re.fullmatch("[a-fA-F0-9]{6}", s):
        raise ValueError("Bad color " + str(value))
    return tuple(bytes.fromhex(s))


def shade(c, factor):
    return tuple(max(0, min(255, round(v * factor))) for v in c) + (255,)


def pointpoly(draw, points, c):
    draw.polygon(points, fill=c)


def draw_icon(recipe, variant):
    """Low-res semantic construction; native 64x64 RGBA, no blur or interpolation."""
    archetype = recipe["archetype"]
    if archetype not in SUPPORTED:
        raise ValueError("Unsupported archetype: " + str(archetype))
    seed = int.from_bytes(hashlib.sha256((recipe["id"] + ":" + str(variant) + ":" + str(SEED)).encode()).digest()[:8], "big")
    rng = random.Random(seed)
    base = hexrgb(recipe.get("color", "#788089"))
    top, light, mid, dark, deep = (shade(base,x) for x in (1.26, 1.12, 1.0, 0.76, 0.55))
    steel = (120, 139, 148, 255); steel_hi = (166, 179, 182, 255); steel_lo = (65, 77, 83, 255)
    wood = (142, 105, 75, 255); wood_hi = (184, 141, 95, 255); ink=(35, 40, 43, 255)
    im = Image.new("RGBA", (64,64), (0,0,0,0)); d=ImageDraw.Draw(im)
    # Each archetype has its own geometry, material boundaries and compact AO.
    if archetype == "can":
        d.rounded_rectangle((14,18,48,49),radius=5,fill=dark)
        d.rectangle((17,22,44,46), fill=mid)
        d.polygon([(18,25),(26,24),(26,44),(18,45)],fill=light)
        d.polygon([(38,24),(45,23),(45,45),(38,44)],fill=dark)
        d.ellipse((14,15,48,25),fill=steel_lo)
        d.ellipse((17,16,46,22),fill=steel_hi)
        d.arc((15,44,48,53),0,180,fill=steel_hi,width=2)
        d.rectangle((23,30,39,36),fill=shade(base,0.87))
        d.rectangle((23,30,36,31),fill=top)
        d.line((20,28,20,43),fill=shade(base,1.35),width=1)
    elif archetype == "fruit":
        pear = "pear" in recipe["id"]
        if pear:
            d.ellipse((20,24,45,50),fill=dark);d.ellipse((24,14,40,39),fill=mid)
            d.ellipse((24,20,33,39),fill=light)
        else:
            d.ellipse((15,19,48,51),fill=dark)
            d.ellipse((17,19,37,47),fill=mid)
            d.ellipse((21,23,30,39),fill=light)
        d.line((32,20,34,12),fill=wood,width=2)
        d.polygon([(34,13),(40,9),(45,11),(40,16)],fill=(80,110,72,255))
        d.point((24,28), fill=top)
    elif archetype in ("case", "box"):
        d.polygon([(12,23),(36,16),(52,25),(27,33)],fill=light)
        d.polygon([(12,23),(27,33),(27,51),(12,42)],fill=dark)
        d.polygon([(27,33),(52,25),(52,44),(27,51)],fill=mid)
        d.line([(13,25),(27,34),(51,26)],fill=deep,width=1)
        d.line((30,34,30,48),fill=light,width=1)
        if archetype == "case":
            d.line([(22,18),(25,12),(37,9),(40,14)],fill=steel_lo,width=3)
            d.rectangle((31,34,38,44), fill=(157,76,73,255))
            d.rectangle((29,37,40,40), fill=(157,76,73,255))
        else:
            d.polygon([(15,32),(25,38),(25,42),(15,36)],fill=shade(base,1.4))
    elif archetype == "hammer":
        d.polygon([(16,44),(21,47),(43,17),(38,14)],fill=wood)
        d.line((19,43,39,17),fill=wood_hi,width=2)
        if "ball" in recipe["id"]:
            d.ellipse((14,10,28,24),fill=steel_lo)
        else:
            d.polygon([(12,15),(22,10),(27,15),(19,23)],fill=steel_lo)
            d.polygon([(12,15),(8,14),(8,18),(15,21)],fill=steel)
        d.polygon([(22,10),(41,11),(46,16),(27,20)],fill=steel)
        d.polygon([(22,10),(35,8),(41,11),(27,15)],fill=steel_hi)
    elif archetype == "screwdriver":
        d.polygon([(10,45),(18,52),(36,29),(29,23)],fill=dark)
        d.polygon([(13,44),(18,48),(32,28),(29,25)],fill=light)
        d.polygon([(28,24),(32,28),(53,8),(50,5)],fill=steel)
        d.line((31,25,49,8),fill=steel_hi,width=2)
        if "phillips" in recipe["id"]:
            d.line((47,7,54,11),fill=steel_lo,width=2)
        else:
            d.line((50,5,54,7),fill=steel_lo,width=2)
    elif archetype == "wrench":
        d.polygon([(12,48),(17,51),(39,26),(33,21)],fill=dark)
        d.polygon([(13,46),(17,47),(35,25),(33,23)],fill=steel_hi)
        d.polygon([(33,22),(35,11),(43,7),(42,17),(51,13),(49,25),(39,30)],fill=mid)
        d.line([(35,15),(40,12)],fill=steel_hi,width=2)
        d.ellipse((14,43,19,48),fill=steel_lo)
        if "pipe" in recipe["id"]:
            d.line((38,18,50,23),fill=deep,width=3)
    elif archetype in ("plank", "bar"):
        material = wood if archetype == "plank" else steel
        hi = wood_hi if archetype == "plank" else steel_hi
        lo = dark if archetype == "plank" else steel_lo
        pointpoly(d,[(8,37),(39,13),(53,18),(22,43)],hi)
        pointpoly(d,[(22,43),(53,18),(53,26),(22,51)],material)
        pointpoly(d,[(8,37),(22,43),(22,51),(8,44)],lo)
        if archetype == "plank":
            d.line((13,36,39,17),fill=wood,width=1)
            d.line((26,41,48,23),fill=dark,width=1)
        else: d.line((25,45,50,25),fill=steel_hi,width=1)
    elif archetype == "tape":
        d.ellipse((15,15,48,49),fill=deep)
        d.ellipse((17,13,45,44),fill=mid)
        d.ellipse((23,19,40,36),fill=(43,48,49,255))
        d.ellipse((26,22,37,33),fill=(142,136,122,255))
        d.arc((16,15,45,44),190,295,fill=light,width=3)
    elif archetype == "rope":
        for off in range(7):
            d.arc((13+off,13+off//2,49-off//2,49-off),25,335,fill=dark,width=3)
        d.arc((18,17,45,46),20,340,fill=light,width=3)
        d.line((40,39,50,48),fill=mid,width=3)
    elif archetype in ("backpack", "bag"):
        d.arc((22,9,44,31),180,360,fill=dark,width=4)
        d.rounded_rectangle((15,18,50,51),radius=5,fill=dark)
        d.polygon([(17,20),(26,17),(26,49),(17,45)],fill=light)
        d.polygon([(37,18),(49,20),(48,47),(37,50)],fill=deep)
        if archetype == "backpack":
            d.rounded_rectangle((23,31,43,46),radius=3,fill=mid,outline=deep)
            d.line((24,33,43,33),fill=light,width=2)
            d.rectangle((29,24,35,27),fill=steel)
        else:
            d.rectangle((17,30,48,35),fill=mid)
            d.line((19,36,45,36),fill=light,width=2)
    elif archetype == "gloves":
        for shift in (-9,9):
            d.polygon([(30+shift,48),(22+shift,41),(20+shift,29),(23+shift,21),(26+shift,32),(27+shift,17),(30+shift,15),(32+shift,32),(34+shift,20),(37+shift,19),(36+shift,43)],fill=mid)
            d.line((25+shift,40,32+shift,43),fill=dark,width=2)
    elif archetype == "hat":
        d.pieslice((14,15,50,55),180,360,fill=mid)
        d.rectangle((14,38,50,48),fill=dark)
        for x in range(19,47,5):d.line((x,30,x,45),fill=light,width=1)
        d.ellipse((29,13,35,18),fill=light)
    elif archetype == "radio":
        d.rounded_rectangle((19,17,49,53),radius=4,fill=deep)
        d.polygon([(21,19),(35,17),(35,50),(21,49)],fill=mid)
        d.rectangle((25,23,44,33),fill=(54,75,82,255))
        d.line((18,18,15,4),fill=steel_hi,width=2)
        d.ellipse((29,37,40,48),fill=dark)
        for y in (39,42,45): d.line((40,y,46,y),fill=steel_lo,width=1)
    elif archetype == "flashlight":
        d.polygon([(15,45),(23,51),(45,25),(37,20)],fill=dark)
        d.polygon([(17,43),(22,47),(39,25),(36,22)],fill=light)
        d.polygon([(35,19),(47,10),(55,17),(44,30)],fill=mid)
        d.line((45,10,54,17),fill=steel_hi,width=2)
        d.ellipse((45,10,56,21),fill=steel_hi)
        d.ellipse((47,12,54,19),fill=(209,199,154,255))
    elif archetype == "bottle":
        d.polygon([(24,22),(28,16),(28,10),(38,10),(38,17),(43,23),(43,53),(22,53)],fill=dark)
        d.polygon([(25,25),(29,18),(30,11),(34,11),(34,51),(25,50)],fill=light)
        d.rectangle((27,8,39,13),fill=steel_lo)
        d.line((29,27,29,46),fill=shade(base,1.38),width=2)
    elif archetype == "mug":
        d.polygon([(17,25),(45,25),(43,51),(21,51)],fill=mid)
        d.ellipse((17,20,46,29),fill=light)
        d.ellipse((22,22,42,26),fill=deep)
        d.arc((37,26,59,48),260,95,fill=steel_lo,width=4)
        d.line((21,30,23,46),fill=light,width=2)
    # Deliberately restrained wear; distinct state-specific changes require
    # separate approved recipes, NOT cosmetic random scratches everywhere.
    if int(variant) > 0 and recipe.get("allow_cosmetic_variants", True):
        # Only tiny deterministic material-aware shifts, not new item identities.
        if archetype in ("can", "case", "box", "backpack", "bag", "radio"):
            px = 22+rng.randrange(17); py=34+rng.randrange(9)
            if im.getpixel((px,py))[3] > 0:
                d.line((px,py,px+2,py),fill=shade(base,0.72),width=1)
    return im


def normalize(raw):
    if not isinstance(raw,dict): raise ValueError("Recipe must be JSON object")
    item_id = str(raw.get("id", "")).strip()
    if not re.fullmatch(r"[a-z0-9_]+(?:\.[a-z0-9_]+)*", item_id):
        raise ValueError("id must be stable lowercase dotted ID: " + item_id)
    family = str(raw.get("family", "")).strip()
    if not re.fullmatch(r"[a-z0-9_]+",family):raise ValueError("Bad family")
    archetype = str(raw.get("archetype", ""))
    if archetype not in SUPPORTED: raise ValueError("Unsupported archetype: " + archetype)
    hexrgb(raw.get("color", "#788089"))
    out = dict(raw)
    out["id"] = item_id
    out["family"] = family
    out["archetype"] = archetype
    return out


def initial_recipes(base):
    p=base / "recipes.jsonl"
    if not p.exists():
        with p.open("w",encoding="utf-8") as f:
            for family,slug,arch,material,color,brief in DEMO_BRIEFS:
                f.write(json.dumps({"id":"item."+family+"."+slug,"family":family,
                     "archetype":arch,"material":material,"color":color,
                     "brief":brief,"qa_status":"unreviewed"},ensure_ascii=False)+"\n")
        print("Created editable recipes:",p)
    if DEMO_MODE:
        return [normalize({"id":"item."+family+"."+slug,"family":family,"archetype":arch,
                           "material":material,"color":color,"brief":brief})
                for family,slug,arch,material,color,brief in DEMO_BRIEFS]
    arr=[]; seen=set()
    with p.open(encoding="utf-8") as f:
        for line_no,line in enumerate(f,1):
            if not line.strip():continue
            try: recipe=normalize(json.loads(line))
            except Exception as e: raise ValueError("recipes.jsonl line %s: %s"%(line_no,e)) from e
            if recipe["id"] in seen: raise ValueError("Duplicate recipe ID: "+recipe["id"])
            seen.add(recipe["id"]);arr.append(recipe)
    return arr


def chunks(seq,n):
    for k in range(0,len(seq),n):yield seq[k:k+n]


def make_sheet(records, output):
    # Resize NEAREST, small bounded-memory contact sheets.
    scale=CONTACT_SHEET_SCALE; cell=80*scale
    cols=min(6,max(1,math.ceil(math.sqrt(len(records)))))
    rows=math.ceil(len(records)/cols)
    sheet=Image.new("RGB",(cols*cell,rows*cell),(43,47,51))
    d=ImageDraw.Draw(sheet)
    for i,record in enumerate(records):
        with Image.open(record["path"]) as original: icon=original.convert("RGBA")
        icon=icon.resize((64*scale,64*scale),Image.Resampling.NEAREST)
        x=(i%cols)*cell+8*scale; y=(i//cols)*cell+3*scale
        # Checker background
        for cy in range(0,64*scale,8*scale):
            for cx in range(0,64*scale,8*scale):
                v=58 if ((cx+cy)//(8*scale))%2==0 else 70
                d.rectangle((x+cx,y+cy,x+cx+8*scale-1,y+cy+8*scale-1),fill=(v,v,v))
        sheet.paste(icon,(x,y),icon)
        d.text((x,y+65*scale),record["id"].split(".")[-1][:18],fill=(231,229,214))
    output.parent.mkdir(parents=True,exist_ok=True)
    sheet.save(output,format="PNG",optimize=True)
    sheet.close()


def main():
    if VARIANTS_PER_RECIPE<1 or CHUNK_SIZE<1 or CONTACT_SHEET_SIZE<1 or MAX_ITEMS<0 or START_AT<0:
        raise ValueError("Invalid job configuration")
    base=pick_base(); out=base/"output"; sheets=base/"review_sheets"; zips=base/"zip_exports"
    for p in (out,sheets,zips):p.mkdir(parents=True,exist_ok=True)
    print("LAST LIGHT | ORIGINAL PROCEDURAL SPRITE FACTORY v3")
    print("BASE:",base)
    print("DRY_RUN:",DRY_RUN,"DEMO_MODE:",DEMO_MODE)
    if str(base).startswith(str(Path(tempfile.gettempdir()))):
        print("WARNING: TEMPORARY STORAGE. EXPORT ZIP TO FILES BEFORE IOS CLEARS IT.")
    recipes=initial_recipes(base)
    total=len(recipes)*VARIANTS_PER_RECIPE
    if total>MAX_TOTAL_JOBS:raise ValueError("Job count exceeds MAX_TOTAL_JOBS safety cap")
    stop=total if MAX_ITEMS==0 else min(total,START_AT+MAX_ITEMS)
    if START_AT>=total:
        print("NO WORK: START_AT beyond total",total);return
    print("RECIPES:",len(recipes),"TOTAL POSSIBLE JOBS:",total,"RANGE:",START_AT,stop)
    generated=0;skipped=0;errors=0; review=[]; exported=[]
    # Manifest is JSONL to stream millions of records without large memory use.
    run_id="range_%09d_%09d"%(START_AT,stop)
    mf=base/("manifest_"+run_id+".jsonl")
    ef=base/("errors_"+run_id+".jsonl")
    with mf.open("w",encoding="utf-8") as manifest,ef.open("w",encoding="utf-8") as error_log:
        for job in range(START_AT,stop):
            recipe=recipes[job//VARIANTS_PER_RECIPE]
            variant=job%VARIANTS_PER_RECIPE
            file_slug=recipe["id"].split(".")[-1]
            rel=Path("art/items")/recipe["family"]/file_slug/("icon_%05d.png"%variant)
            dest=out/rel
            try:
                if not DRY_RUN:
                    dest.parent.mkdir(parents=True,exist_ok=True)
                    if RESUME and dest.exists():
                        with Image.open(dest) as check:
                            if check.size==(64,64) and check.mode=="RGBA":
                                skipped+=1
                            else:
                                raise ValueError("Existing output invalid; do not overwrite "+str(dest))
                    else:
                        im=draw_icon(recipe,variant)
                        if im.getbbox() is None:raise ValueError("Empty icon")
                        im.save(dest,format="PNG",optimize=False)
                        im.close();generated+=1
                row={"job":job,"logical_item_id":recipe["id"],"family":recipe["family"],
                     "archetype":recipe["archetype"],"variant":variant,
                     "relative_path":rel.as_posix(),"format":"RGBA_PNG","size":[64,64],
                     "style_version":STYLE_VERSION,"qa_status":"needs_human_review",
                     "godot_import_status":"not_tested","provenance":"original_procedural_geometry",
                     "semantic_brief":recipe.get("brief", ""),"external_reference_pixels_used":False}
                if not DRY_RUN:
                    row["sha256"]=hashlib.sha256(dest.read_bytes()).hexdigest()
                    review.append({"path":dest,"id":recipe["id"]+" #"+str(variant)})
                    exported.append((dest,rel.as_posix(),row))
                    if len(review)>=CONTACT_SHEET_SIZE:
                        make_sheet(review,sheets/("sheet_%s_%05d.png"%(run_id,(job-START_AT)//CONTACT_SHEET_SIZE)))
                        review.clear()
                manifest.write(json.dumps(row,ensure_ascii=False)+"\n")
                if (job-START_AT+1)%PRINT_EVERY==0:print("Progress",job-START_AT+1,"/",stop-START_AT)
            except Exception as ex:
                errors+=1
                error_log.write(json.dumps({"job":job,"id":recipe["id"],"error":str(ex)})+"\n")
                print("ERROR",job,recipe["id"],str(ex))
        if review and not DRY_RUN:
            make_sheet(review,sheets/("sheet_%s_final.png"%run_id))
    if not DRY_RUN and ZIP_EVERY_RUN:
        # ZIP each bounded export chunk; no in-memory archive and no huge single ZIP.
        for part,subset in enumerate(chunks(exported,CHUNK_SIZE),1):
            zip_path=zips/("LAST_LIGHT_%s_part_%04d.zip"%(run_id,part))
            with zipfile.ZipFile(zip_path,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=3,allowZip64=True) as z:
                for path,rel,row in subset:z.write(path,arcname=rel)
                z.writestr("factory_manifest.jsonl", "".join(json.dumps(row,ensure_ascii=False)+"\n" for _,_,row in subset))
                if ef.stat().st_size:z.write(ef,arcname="factory_errors.jsonl")
                z.writestr("README.txt", "LAST LIGHT procedural DRAFT exports. All icons NEED HUMAN VISUAL QA. Not approved Golden 40.\\nImport via Codex only after registry/path reconciliation.\\n")
            with zipfile.ZipFile(zip_path) as z:
                if z.testzip():raise RuntimeError("ZIP integrity failed: "+str(zip_path))
            print("ZIP:",zip_path,"icons:",len(subset))
    print("SUMMARY",json.dumps({"generated":generated,"resumed":skipped,"errors":errors,"requested":stop-START_AT,"qa_approved":0,"godot_imported":0}))
    print("Manifest:",mf)
    print("Review sheets:",sheets)
    print("ZIP folder:",zips)
    print("NEXT: visually review first 24; do NOT mass-produce unapproved archetypes.")

if __name__=="__main__":
    try:main()
    except Exception as e:
        import traceback
        print("FATAL:",type(e).__name__,str(e));traceback.print_exc()
