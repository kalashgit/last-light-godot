"""World-scale original 2.5D sprite packer, alpha-safe BOX reduction and actual V1/V3 comparisons."""
import argparse, hashlib, io, json, math, zipfile
from pathlib import Path
from PIL import Image,ImageDraw,ImageFilter,ImageFont

ITEMS=("refrigerator","cabinet","sofa")
FURNITURE=set(("refrigerator","cabinet","sofa","crate","chair","table"))
DARK=(45,59,49,255);MID=(136,143,130,255);PAPER=(238,237,225,255)

def font(sz=18):
    for path in ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf","/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf"):
        if Path(path).exists():return ImageFont.truetype(path,sz)
    return ImageFont.load_default()

def shadow(size,pivot,foot):
    layer=Image.new("RGBA",size,(0,0,0,0))
    d=ImageDraw.Draw(layer,"RGBA")
    cx,cy=pivot;fx,fy=foot
    # Width/depth proportional to actual base footprint projected into 80x40 world pixels.
    rx=max(3,math.floor((fx+fy)*22))
    ry=max(2,math.floor((fx+fy)*6))
    d.ellipse((cx-rx,cy-ry,cx+rx,cy+ry),fill=(10,12,10,67))
    # Darker center under actual support plane, not the full outer circular glow.
    d.ellipse((cx-rx*.66,cy-ry*.52,cx+rx*.66,cy+ry*.52),fill=(10,12,10,85))
    return layer.filter(ImageFilter.GaussianBlur(1.7))

def checker(width,height):
    im=Image.new("RGBA",(width,height),(115,128,111))
    d=ImageDraw.Draw(im)
    for y in range(-100,height+100,46):
        for x in range(-120,width+120,92):
            poly=[(x,y+23),(x+46,y),(x+92,y+23),(x+46,y+46)]
            d.polygon(poly,fill=(123,137,122) if ((x//92+y//46)%2==0) else (111,124,112),outline=(82,91,84))
    return im

def paste_at_contact(canvas,sprite,center,scale=2.2):
    new_size=(max(1,round(sprite.width*scale)),max(1,round(sprite.height*scale)))
    im=sprite.resize(new_size,Image.Resampling.NEAREST)
    pivot=sprite.info.get("anchor",[sprite.width//2,sprite.height-4])
    top_left=(round(center[0]-pivot[0]*scale),round(center[1]-pivot[1]*scale))
    canvas.alpha_composite(im,top_left)

def qa_image(img,name):
    assert img.mode=="RGBA",(name,img.mode)
    alpha=img.getchannel("A")
    assert alpha.getbbox() and alpha.getextrema()[0]==0 and alpha.getextrema()[1]==255,name
    assert 0<img.width<720 and 0<img.height<720,(name,img.size)
    # Not a solid-color card / matte image.
    corners=[img.getpixel((x,y))[3] for x,y in ((0,0),(img.width-1,0),(0,img.height-1),(img.width-1,img.height-1))]
    assert min(corners)==0,(name,"opaque rectangular canvas")

def make_sheet(records, dest):
    w,h=350,365
    sheet=Image.new("RGBA",(w*5,h*2),(236,237,231))
    draw=ImageDraw.Draw(sheet)
    for i,rec in enumerate(records):
        name=rec["name"];x=(i%5)*w;y=(i//5)*h
        bg=checker(w-22,h-95)
        shot=Image.open(dest/rec["world_sprite"]).convert("RGBA")
        shad=Image.open(dest/rec["shadow_sprite"]).convert("RGBA")
        pivot=rec["anchor_px"]
        shot.info["anchor"]=pivot;shad.info["anchor"]=pivot
        anchor=(int(bg.width*.50),int(bg.height*.78))
        # A 220% world camera exactly as on the iPhone. Small items stay small.
        paste_at_contact(bg,shad,anchor,2.2)
        paste_at_contact(bg,shot,anchor,2.2)
        sheet.alpha_composite(bg,(x+11,y+45))
        draw.text((x+18,y+10),name.upper().replace("_"," "),fill=(25,35,30),font=font(21))
        draw.text((x+18,y+h-42),"220% WORLD (true scale)",fill=(60,70,61),font=font(14))
        draw.rectangle((x+7,y+40,x+w-7,y+h-45),outline=(179,183,172),width=2)
    sheet.convert("RGB").save(dest.parent/"preview-grid-v3.jpg",quality=95)
    sheet.save(dest.parent/"preview-grid-v2.png")

def make_compare(records,dest,old_zip):
    if not old_zip.exists(): return
    try:
        z=zipfile.ZipFile(old_zip)
    except Exception as e:
        print("Comparison skipped",str(e));return
    rows=3
    w=450;h=400
    output=Image.new("RGBA",(w*2,h*rows),(240,242,235))
    draw=ImageDraw.Draw(output)
    for i,rec in enumerate(records[:4]):
        name=rec["name"]
        try: old=Image.open(io.BytesIO(z.read("game_ready/"+name+"/ground.png"))).convert("RGBA")
        except Exception as e:print("Missing baseline",e);continue
        for c,(title,im) in enumerate((("V1 BLOCK-OUT",old),("V2 MATERIAL + MESH",Image.open(dest/rec["world_sprite"]).convert("RGBA")))):
            bg=checker(w-30,h-70)
            if c==0: pivot=(old.width*.5,old.height-17)
            else: pivot=rec["anchor_px"]
            im.info["anchor"]=pivot
            paste_at_contact(bg,im,(bg.width//2,int(bg.height*.81)),2.2)
            output.alpha_composite(bg,(c*w+15,i*h+43))
            draw.text((c*w+18,i*h+10),name.upper()+" / "+title,fill=(22,30,26),font=font(19))
    output.convert("RGB").save(dest.parent/"comparison-v1-v2.jpg",quality=95)
    output.save(dest.parent/"comparison-v1-v2.png")

def produce(raw,dest,old_zip):
    m=json.loads((raw/"manifest.json").read_text())
    assert m["schema"]==3 and m["tile_px"]==[80,40] and m["downsample"]==4
    dest.mkdir(parents=True,exist_ok=True)
    result={"schema":3,"tile_px":[80,40],"pixel_filter":"BOX premultiplied alpha; Godot nearest at runtime",
            "render_pipeline":"Blender original mesh+PBR procedural texture -> RGBA -> alpha-safe scale -> world/icon/shadow",
            "status":"mechanically_verified_visual_approval_pending","items":[]}
    for asset in m["entries"]:
        name=asset["name"]
        img=Image.open(raw/asset["file"]).convert("RGBA")
        # Premultiply first so empty transparent pixels cannot contaminate edge colors.
        factor=m["downsample"]
        half=img.convert("RGBa").resize((img.width//factor,img.height//factor),Image.Resampling.BOX).convert("RGBA")
        box=half.getchannel("A").getbbox()
        if box is None:raise ValueError("Blank render "+name)
        margin=5;left=max(0,box[0]-margin);upper=max(0,box[1]-margin)
        right=min(half.width,box[2]+margin);bottom=min(half.height,box[3]+margin)
        crop=half.crop((left,upper,right,bottom))
        qa_image(crop,name)
        pivot=[round(asset["contact_px_raw"][0]/factor-left,2),round(asset["contact_px_raw"][1]/factor-upper,2)]
        folder=dest/name;folder.mkdir(exist_ok=True)
        crop.save(folder/"ground.png",optimize=True)
        shad=shadow(crop.size,pivot,asset["footprint_m"])
        shad.save(folder/"shadow.png",optimize=True)
        # Inventory art is explicitly presented at larger visual size than world art.
        bbox=img.getchannel("A").getbbox()
        master=img.crop(bbox)
        master.thumbnail((112,112),Image.Resampling.LANCZOS)
        icon=Image.new("RGBA",(128,128),(0,0,0,0))
        icon.alpha_composite(master,((128-master.width)//2,(128-master.height)//2))
        icon.save(folder/"icon.png",optimize=True)
        rec={"id":asset["id"],"name":name,"world_sprite":name+"/ground.png",
             "icon_sprite":name+"/icon.png","shadow_sprite":name+"/shadow.png",
             "dimensions_m":asset["dimensions_m"],"footprint_m":asset["footprint_m"],
             "size_px":list(crop.size),"anchor_px":pivot,
             "source_master":name+".png","source":"Original Blender parametric V2",
             "status":"automated_qa_pass_visual_pending",
             "sha256":hashlib.sha256((folder/"ground.png").read_bytes()).hexdigest()}
        result["items"].append(rec)
        print("LL_V2_PACK_OK",name,rec["size_px"],pivot,flush=True)
    assert len(result["items"])==3
    (dest/"manifest.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf8")
    make_sheet(result["items"],dest)
    make_compare(result["items"],dest,old_zip)
    # All individual transparent sprites, manifests and comparison contact sheets.
    package=dest.parent/"last-light-v2-10-sprite-preview.zip"
    with zipfile.ZipFile(package,"w",zipfile.ZIP_DEFLATED,compresslevel=7) as z:
        for p in sorted(dest.rglob("*")):
            if p.is_file():z.write(p,arcname="game_ready/"+str(p.relative_to(dest)))
        for name in ("preview-grid-v2.png","comparison-v1-v2.png"):
            src=dest.parent/name
            if src.exists():z.write(src,arcname=name)
        for p in sorted(raw.glob("*.png")):
            z.write(p,arcname="master_renders/"+p.name)
    print("LL_V2_PACK_DONE",len(result["items"]),package,flush=True)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--baseline",type=Path,default=Path("tools/blender_factory/output/last-light-blender-pilot.zip"))
    a=p.parse_args()
    produce(a.input,a.output,a.baseline)
if __name__=="__main__":main()
