#!/usr/bin/env python3
"""LAST LIGHT Material Factory v1: deterministic, license-clean PBR texture map baking.
No game/reference images are sampled or copied. Pure Python NumPy + Pillow.
Usage: python tools/material_factory/generate.py --out build/material_factory --size 512
"""
import argparse, hashlib, json, math, zipfile
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

MATERIALS = Path(__file__).with_name("recipes.json")

def periodic_noise(size, cells, rng):
    grid=rng.random((cells,cells)).astype(np.float32)
    xs=np.arange(size,dtype=np.float32)*cells/size
    ix=np.floor(xs).astype(np.int32)%cells
    fx=xs-np.floor(xs)
    fx=fx*fx*(3-2*fx)
    x1=(ix+1)%cells
    # both axes periodic, seamless at tile boundary modulo discretization.
    v00=grid[np.ix_(ix,ix)]
    v10=grid[np.ix_(ix,x1)]
    v01=grid[np.ix_(x1,ix)]
    v11=grid[np.ix_(x1,x1)]
    wx=fx[:,None];wy=fx[None,:]
    return ((1-wx)*((1-wy)*v00+wy*v10)+wx*((1-wy)*v01+wy*v11))

def fbm(size,rng,base=4,octaves=5):
    noise=np.zeros((size,size),dtype=np.float32)
    weight=0.
    for i in range(octaves):
        step=max(2,base*2**i)
        amplitude=0.60**i
        noise+=(periodic_noise(size,step,rng)-.5)*amplitude
        weight+=amplitude
    return np.clip(.5+noise/weight,0,1)

def normal_map(height,strength=3.0):
    # periodic gradient; green is OpenGL +Y convention.
    gy=(np.roll(height,-1,0)-np.roll(height,1,0))*strength
    gx=(np.roll(height,-1,1)-np.roll(height,1,1))*strength
    n=np.stack([-gx,-gy,np.ones_like(height)],axis=-1)
    n=n/np.maximum(np.linalg.norm(n,axis=2,keepdims=True),1e-7)
    return np.clip((n*.5+.5)*255,0,255).astype(np.uint8)

def byte(a):
    return np.uint8(np.clip(a*255,0,255))

def material_maps(recipe,size):
    seed=int(recipe["seed"])
    rng=np.random.default_rng(seed)
    yy,xx=np.mgrid[:size,:size].astype(np.float32)
    x=xx/size;y=yy/size
    low=fbm(size,rng,3,4)
    mid=fbm(size,rng,9,5)
    fine=fbm(size,rng,23,4)
    base=np.asarray(tuple(int(recipe["base_hex"][i:i+2],16) for i in (1,3,5)),dtype=np.float32)/255
    family=recipe["family"]
    wear=np.zeros((size,size),dtype=np.float32)
    local_ao=np.zeros((size,size),dtype=np.float32)
    if family=="painted_metal":
        # Clustered primer exposure, not an indiscriminate bright rust speckle.
        chip_field=.48*low+.35*mid+.17*fine
        chips=np.clip((chip_field-.60)*12,0,1)**1.8
        scuff=np.clip((fine-.61)*1.8,0,.30)
        wear=np.clip(chips+.10*scuff,0,1)
        variation=.035*(fine-.5)+.027*(mid-.5)-.12*wear
        height=np.clip(.52+.024*(fine-.5)+.018*(mid-.5)-.13*chips,0,1)
        rough=np.clip(recipe["roughness"]+.085*(low-.5)+.19*chips+.10*scuff,0,1)
        metal=np.clip(recipe["metallic"]*(1-chips)+.24*chips,0,1)
    elif family=="wood":
        # Longitudinal fibers with wandering growth boundaries and sparse knots.
        # X is along the board. Object-specific board rotation remains a UV task.
        knot_x=.24;knot_y=.62
        dx=np.minimum(abs(x-knot_x),1-abs(x-knot_x))
        dy=np.minimum(abs(y-knot_y),1-abs(y-knot_y))
        knot=np.exp(-((dx/.105)**2+(dy/.085)**2)*2.0)
        flow=y+.12*(low-.5)+.075*(mid-.5)+.035*knot*np.sin(2*np.pi*dx/.21)
        rings=flow*8.5+.65*(mid-.5)+.20*(fine-.5)
        phase=np.abs((rings%1)-.5)*2
        grain=np.clip((phase-.43)*2.1,0,1)**2.3
        fibers=np.clip((np.abs(((flow*57+.7*fine)%1)-.5)*2-.52)*2.0,0,1)
        pores=np.clip((fine-.62)*3,0,1)
        heartwood=np.clip(.56*low+.44*mid,0,1)
        variation=-.17*grain-.045*fibers+.23*(heartwood-.5)-.16*knot-.075*pores
        height=np.clip(.54-.11*grain-.025*fibers+.055*(fine-.5)-.045*knot,0,1)
        wear=np.clip(.11*pores+.10*(1-grain)*np.maximum(0,.48-mid),0,1)
        rough=np.clip(recipe["roughness"]+.11*(fine-.5)+.09*pores+.055*knot,0,1)
        metal=np.zeros((size,size),dtype=np.float32)
    elif family=="fabric":
        # Alternating warp and weft yarns; low-frequency compression source is
        # intentionally subtle until object-specific seams and folds are supplied.
        warp=np.sin(2*np.pi*(x*82+.003*mid))
        weft=np.sin(2*np.pi*(y*78+.003*fine))
        weave=.5*(warp+weft)+.24*warp*weft
        compression=np.clip((.49-low)*2.7,0,.48)
        slub=np.clip((mid-.59)*3.4,0,.45)
        variation=.17*(low-.5)+.025*weave+.075*(mid-.5)-.19*compression+.035*slub
        height=np.clip(.51+.09*weave+.032*(fine-.5)-.085*compression+.025*slub,0,1)
        wear=np.clip(.11*mid+.24*compression,0,1)
        rough=np.clip(recipe["roughness"]+.075*(low-.5)-.15*compression+.025*weave,0,1)
        metal=np.zeros((size,size),dtype=np.float32)
    elif family=="plastic":
        mild=.07*(low-.5)+.025*(fine-.5)
        scuff=np.clip((mid-.70)*.9,0,.20)
        variation=mild-.05*scuff
        height=.5+.018*(fine-.5)+.035*(mid-.5)
        wear=.025+.25*scuff
        rough=np.clip(recipe["roughness"]+.07*(low-.5)+scuff*.25,0,1)
        metal=np.zeros((size,size),dtype=np.float32)
    elif family=="oxidized_metal":
        corrosion=low*.56+mid*.44
        rust=np.clip((corrosion-.38)*2.3,0,1)**1.6
        # Rust is nonmetallic, bare steel is metallic.
        metal=np.clip((1-rust)*.84,0,1)
        variation=.18*(fine-.5)-.12*rust
        height=np.clip(.52+.16*(fine-.5)-.23*rust,0,1)
        wear=rust
        rough=np.clip(.43+.49*rust+.11*(mid-.5),0,1)
    else:
        raise ValueError(family)
    variation=np.asarray(variation,dtype=np.float32)
    # Original maps; no proprietary reference-game textures.
    color=np.clip(base[None,None,:]*(1+variation[:,:,None]),0,1)
    if family=="oxidized_metal":
        rust_rgb=np.array([.42,.225,.115],dtype=np.float32)
        color=color*(1-wear[:,:,None]) + rust_rgb[None,None,:]*wear[:,:,None]
    if family=="painted_metal":
        # Exposed muted primer and oxidized undercoat, not chrome chips.
        primer=np.array([.30,.31,.29],dtype=np.float32)
        color=color*(1-chips[:,:,None])+primer[None,None,:]*chips[:,:,None]
        color[:,:,0]=np.clip(color[:,:,0]+.014*low,0,1)
    # local mask is a texture cavity proxy, NOT mesh ambient occlusion.
    local_ao=np.clip(1-.16*np.maximum(0,.49-height)*2,0,1)
    maps={
      "albedo":(byte(color),"RGB"),
      "roughness":(byte(rough),"L"),
      "metallic":(byte(metal),"L"),
      "height":(byte(height),"L"),
      "normal":(normal_map(height,recipe["normal_strength"]),"RGB"),
      "wear_source":(byte(wear),"L"),
      "cavity_proxy":(byte(local_ao),"L")
    }
    return maps

def preview(maps,recipe,size):
    al=maps["albedo"][0].astype(np.float32)/255
    normal=maps["normal"][0].astype(np.float32)/255*2-1
    rough=maps["roughness"][0].astype(np.float32)/255
    nx,ny,nz=normal[:,:,0],normal[:,:,1],normal[:,:,2]
    light=np.array([-.35,-.53,.77],dtype=np.float32)
    light=light/np.linalg.norm(light)
    intensity=np.clip(nx*light[0]+ny*light[1]+nz*light[2],0,1)
    # Diagnostic pseudo-lit plane; not a ray-traced render or Godot scene.
    lit=al*(.47+.58*intensity[:,:,None])
    lit+=((1-rough)**3*.18*intensity)[:,:,None]
    return Image.fromarray(byte(np.clip(lit,0,1)),"RGB")

def make_contact_sheet(cards,outdir):
    font=ImageFont.load_default()
    width=380;rowh=215
    sheet=Image.new("RGB",(width*3,rowh*len(cards)),(233,234,229))
    d=ImageDraw.Draw(sheet)
    for i,(name,al,lit,wear) in enumerate(cards):
        for j,im in enumerate((al,lit,wear)):
            x=j*width+18;y=i*rowh+30
            im=im.resize((180,180),Image.Resampling.LANCZOS)
            sheet.paste(im,(x,y))
            label=("ALBEDO","PSEUDO LIT","WEAR SOURCE")[j]
            d.text((x,y-18),name+" / "+label,fill=(20,25,20),font=font)
    sheet.save(outdir/"contact-sheet.png",optimize=True)
    return sheet

def generate(out,size):
    recipes=json.loads(MATERIALS.read_text(encoding="utf8"))
    assert len(recipes)==5
    out.mkdir(parents=True,exist_ok=True)
    records=[];cards=[]
    for recipe in recipes:
        name=recipe["id"];target=out/name
        target.mkdir(exist_ok=True)
        maps=material_maps(recipe,size)
        files={}
        for key,(array,mode) in maps.items():
            path=target/(key+".png")
            Image.fromarray(array,mode).save(path,optimize=True)
            files[key]=str(path.relative_to(out))
        lit=preview(maps,recipe,size)
        lit.save(target/"preview.png",optimize=True)
        cards.append((name,Image.fromarray(maps["albedo"][0],"RGB"),lit,
                     Image.fromarray(maps["wear_source"][0],"L").convert("RGB")))
        records.append({"id":name,"family":recipe["family"],"status":"GENERATED_PENDING_VISUAL_APPROVAL",
          "rights":"ORIGINAL_PROCEDURAL","seed":recipe["seed"],"base_hex":recipe["base_hex"],
          "roughness":recipe["roughness"],"metallic":recipe["metallic"],
          "maps":files,"resolution":[size,size],
          "uv_scale_m":recipe["uv_scale_m"],"wear_semantics":recipe["wear_semantics"],
          "shader_note":"wear_source is ONLY source noise; combine with geometry-specific exposed-edge/handling masks",
          "ao_note":"cavity_proxy is NOT ray-traced/geometry-derived ambient occlusion",
          "sha256_albedo":hashlib.sha256((target/"albedo.png").read_bytes()).hexdigest(),
          "channel_sha256":{key:hashlib.sha256((target/(key+".png")).read_bytes()).hexdigest()
                            for key in sorted(maps)},
          "channel_color_space":{key:("sRGB" if key=="albedo" else "Non-Color") for key in maps},
          "normal_convention":"OpenGL tangent-space +Y",
          "physical_asset_master_ids":[]})
        print("LL_MAT_GENERATED",name,flush=True)
    make_contact_sheet(cards,out)
    data={"schema":1,"projection":"world texture source maps; independent of 2:1 camera",
      "license":"original procedural generated outputs; texture inputs are synthesized, not copied",
      "format":"PNG RGB/greyscale; normal map OpenGL convention (+Y)",
      "notes":"Prototype PBR maps; material appearance is not yet approved at 80x40 tile in Godot",
      "items":records}
    (out/"manifest.json").write_text(json.dumps(data,indent=2)+"\n")
    archive=out.parent/"LAST_LIGHT_Material_Factory_5_Recipes.zip"
    with zipfile.ZipFile(archive,"w",zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for f in sorted(out.rglob("*")):
            if f.is_file(): z.write(f,arcname=f.relative_to(out.parent))
    print("LL_MAT_DONE",len(records),str(archive),flush=True)

def main():
    p=argparse.ArgumentParser();p.add_argument("--out",type=Path,default=Path("build/material_factory/materials"))
    p.add_argument("--size",type=int,default=512);a=p.parse_args()
    if a.size not in (256,512,1024):raise ValueError("size must be 256/512/1024")
    generate(a.out,a.size)
if __name__=="__main__":main()
