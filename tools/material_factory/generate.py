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

def periodic_ridges(size, rng, frequency=32):
    """Non-sinusoidal, locally varying fibre paths; opposite tile edges match."""
    yy, xx = np.mgrid[:size, :size].astype(np.float32)
    x=xx/size; y=yy/size
    broad=fbm(size,rng,3,4)-.5
    warp=fbm(size,rng,7,4)-.5
    drift=.035*broad+.013*warp
    phase=(y+drift)*frequency + .32*(fbm(size,rng,17,3)-.5)
    fractional=np.mod(phase,1.)
    ridge=np.exp(-((fractional-.5)/.12)**2)
    breaks=fbm(size,rng,11,4)
    return np.clip(ridge*(.45+.8*breaks),0,1)

def anisotropic_noise(size, rng, across=72, along=5):
    """Periodic grain fields stretched along boards, without evenly repeated bands."""
    values=rng.random((along,across)).astype(np.float32)
    y=np.arange(size,dtype=np.float32)*along/size
    x=np.arange(size,dtype=np.float32)*across/size
    iy=np.floor(y).astype(int)%along;ix=np.floor(x).astype(int)%across
    fy=y-np.floor(y);fx=x-np.floor(x)
    fy=fy*fy*(3-2*fy);fx=fx*fx*(3-2*fx)
    a=values[np.ix_(iy,ix)];b=values[np.ix_(iy,(ix+1)%across)]
    c=values[np.ix_((iy+1)%along,ix)];d=values[np.ix_((iy+1)%along,(ix+1)%across)]
    return (a*(1-fx)[None,:]+b*fx[None,:])*(1-fy)[:,None]+(c*(1-fx)[None,:]+d*fx[None,:])*fy[:,None]

def normal_map(height,strength=3.0):
    # periodic gradient; green is OpenGL +Y convention.
    gy=(np.roll(height,-1,0)-np.roll(height,1,0))*strength
    gx=(np.roll(height,-1,1)-np.roll(height,1,1))*strength
    n=np.stack([-gx,-gy,np.ones_like(height)],axis=-1)
    n=n/np.maximum(np.linalg.norm(n,axis=2,keepdims=True),1e-7)
    return np.clip((n*.5+.5)*255,0,255).astype(np.uint8)

def byte(a):
    return np.uint8(np.clip(a*255,0,255))

CONDITION_NAMES=("maintained", "used", "weathered", "severely_neglected")

def material_maps(recipe,size,condition=1):
    if condition not in range(4):
        raise ValueError("condition must be 0, 1, 2 or 3")
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
        orange=.035*(fine-.5)+.018*(mid-.5)
        # Fine micro-scuff source mask only: per-object exposed-edge wear is applied in Blender.
        scuff=np.clip((fine-.66)*1.5,0,.25)
        wear=np.clip(.08*mid+.16*scuff,0,1)
        variation=orange-.07*wear
        height=.48+.04*(fine-.5)+.025*(low-.5)
        rough=np.clip(recipe["roughness"]+.07*(low-.5)+.12*scuff,0,1)
        metal=np.full((size,size),recipe["metallic"],dtype=np.float32)
    elif family=="wood":
        # Broad uneven growth texture plus fine lengthwise (Y) open-pore fibres.
        growth=anisotropic_noise(size,rng,27,3)
        fibres=anisotropic_noise(size,rng,110,7)
        pores=np.maximum(0,.49-fine)*np.clip(mid*.9,0,1)
        knots=np.maximum(0,low-.67)**2*12
        grain=.65*growth+.35*fibres
        variation=.22*(low-.5)+.13*(mid-.5)+.32*(growth-.5)+.095*(fibres-.5)-.12*pores-.08*knots
        height=np.clip(.5+.12*(growth-.5)+.045*(fibres-.5)+.045*(fine-.5),0,1)
        wear=np.clip(.07*pores+.06*np.maximum(0,.34-mid),0,1)
        rough=np.clip(recipe["roughness"]+.10*(fine-.5)+.11*pores-.04*grain,0,1)
        metal=np.zeros((size,size),dtype=np.float32)
    elif family=="fabric":
        # Offset plain-weave fibres, with broken slubs and yarn coloration.
        threads=96
        row=np.floor(y*threads).astype(np.int32)
        col=np.floor(x*threads).astype(np.int32)
        warp=np.maximum(0,np.cos(2*np.pi*x*threads))**3
        weft=np.maximum(0,np.cos(2*np.pi*y*threads))**3
        crossing=((row+col)&1).astype(np.float32)
        weave=warp*(.72+.28*crossing)+weft*(1-.28*crossing)
        slub=np.clip((fine-.42)*2,0,1)
        yarn=mid-.5
        # Coarse dye/fiber differences must survive conversion from 512px PBR
        # sources to roughly 100px wide world sprites. Slightly deepen yarn
        # color variation while preserving a wearable, relatively fresh sofa.
        variation=.29*(low-.5)+.18*yarn+.095*(weave-.55)+.055*(slub-.5)
        height=np.clip(.46+.18*weave+.050*(fine-.5),0,1)
        wear=np.clip(.06+.07*np.maximum(0,.4-mid),0,1)
        rough=np.clip(recipe["roughness"]+.080*(low-.5)-.030*weave,0,1)
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
        corrosion=low*.46+mid*.40+fine*.14
        rust=np.clip((corrosion-.40)*3.0,0,1)**1.5
        # Rust is nonmetallic, bare steel is metallic.
        metal=np.clip((1-rust)*.84,0,1)
        pitting=np.maximum(0,.48-fine)*rust
        variation=.20*(fine-.5)+.075*(mid-.5)-.12*rust
        height=np.clip(.53+.10*(fine-.5)-.24*pitting+.035*rust,0,1)
        wear=rust
        rough=np.clip(.43+.49*rust+.11*(mid-.5),0,1)
    else:
        raise ValueError(family)
    variation=np.asarray(variation,dtype=np.float32)
    # Environmental age is distinct from construction and intrinsic material
    # texture. Keep the default relatively fresh; severe decay is opt-in.
    severity=(0.0, .22, .55, 1.0)[condition]
    deposition=np.clip(.52*low+.33*mid+.15*fine,0,1)
    patches=np.clip((deposition-(.57-.10*severity))*3.8,0,1)**1.7
    micro=np.clip((fine-.57)*3,0,1)
    if family=="painted_metal":
        # Sparse damaged paint; object-edge and grip masks still belong in Blender.
        chips=np.clip((patches*.55+micro*.45-.71)*4,0,1)*severity
        variation-=.11*severity*patches
        rough=np.clip(rough+.13*severity*patches,0,1)
        metal=np.clip(metal*(1-chips)+.72*chips,0,1)
        wear=np.maximum(wear, chips)
    elif family=="wood":
        variation-=.13*severity*patches
        rough=np.clip(rough+.16*severity*patches,0,1)
        wear=np.maximum(wear,.65*severity*patches)
    elif family=="fabric":
        variation-=.17*severity*patches
        rough=np.clip(rough+.035*severity*patches,0,1)
        wear=np.maximum(wear,.8*severity*patches)
    elif family=="plastic":
        variation-=.09*severity*patches
        rough=np.clip(rough+.12*severity*patches,0,1)
        wear=np.maximum(wear,.55*severity*patches)
    elif family=="oxidized_metal":
        # Clean steel remains recognizably metallic; oxidation grows with neglect.
        rust=np.clip(wear*(.35+.9*severity),0,1)
        wear=rust
        metal=np.clip((1-rust)*.84,0,1)
        rough=np.clip(.43+.49*rust+.11*(mid-.5),0,1)
    # Original maps; no proprietary reference-game textures.
    color=np.clip(base[None,None,:]*(1+variation[:,:,None]),0,1)
    if family=="oxidized_metal":
        rust_rgb=np.array([.42,.225,.115],dtype=np.float32)
        color=color*(1-wear[:,:,None]) + rust_rgb[None,None,:]*wear[:,:,None]
    if family=="painted_metal":
        # slight warm age patina only; keep enamel read
        color[:,:,0]=np.clip(color[:,:,0]+.014*low,0,1)
        exposed=np.array([.32,.36,.37],dtype=np.float32)
        color=color*(1-chips[:,:,None])+exposed[None,None,:]*chips[:,:,None]
    if family=="fabric" and severity>0:
        # Atmospheric soiling is a soft dye shift, never sharp random pixels.
        color=np.clip(color*(1-.10*severity*patches[:,:,None]),0,1)
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

def generate(out,size,condition=1):
    recipes=json.loads(MATERIALS.read_text(encoding="utf8"))
    assert len(recipes)==5
    out.mkdir(parents=True,exist_ok=True)
    records=[];cards=[]
    for recipe in recipes:
        name=recipe["id"];target=out/name
        target.mkdir(exist_ok=True)
        maps=material_maps(recipe,size,condition)
        files={}
        for key,(array,mode) in maps.items():
            path=target/(key+".png")
            # Pillow's optimized PNG writer can leave an empty file on some
            # runtime/library combinations; reproducible lossless PNG suffices.
            Image.fromarray(array,mode).save(path,optimize=False)
            files[key]=str(path.relative_to(out))
        lit=preview(maps,recipe,size)
        lit.save(target/"preview.png",optimize=True)
        cards.append((name,Image.fromarray(maps["albedo"][0],"RGB"),lit,
                     Image.fromarray(maps["wear_source"][0],"L").convert("RGB")))
        records.append({"id":name,"family":recipe["family"],"status":"GENERATED_PENDING_VISUAL_APPROVAL",
          "rights":"ORIGINAL_PROCEDURAL","seed":recipe["seed"],"base_hex":recipe["base_hex"],
          "condition_level":condition,"condition_name":CONDITION_NAMES[condition],
          "roughness":recipe["roughness"],"metallic":recipe["metallic"],
          "maps":files,"resolution":[size,size],
          "uv_scale_m":recipe["uv_scale_m"],"wear_semantics":recipe["wear_semantics"],
          "shader_note":"wear_source is ONLY source noise; combine with geometry-specific exposed-edge/handling masks",
          "ao_note":"cavity_proxy is NOT ray-traced/geometry-derived ambient occlusion",
          "sha256_albedo":hashlib.sha256((target/"albedo.png").read_bytes()).hexdigest()})
        print("LL_MAT_GENERATED",name,flush=True)
    make_contact_sheet(cards,out)
    data={"schema":1,"condition_level":condition,"condition_name":CONDITION_NAMES[condition],
      "projection":"world texture source maps; independent of 2:1 camera",
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
    p.add_argument("--size",type=int,default=512)
    p.add_argument("--condition",type=int,choices=range(4),default=1);a=p.parse_args()
    if a.size not in (256,512,1024):raise ValueError("size must be 256/512/1024")
    generate(a.out,a.size,a.condition)
if __name__=="__main__":main()
