"""Original deterministic extended material source library for catalog gaps and terrain.
All outputs are PBR *sources*, not visually approved Godot surfaces or geometry-derived wear.
Periodic Fourier noise; no downloaded, sampled or copied proprietary textures.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import numpy as np
from PIL import Image

# Stable family IDs and physically distinct roughness/color behavior.
FAMILIES={
 "paper":           ("#c4b7a1",.86, .030, .10),
 "ceramic":         ("#e8e4d9",.24, .008, .014),
 "amber_glass":     ("#896333",.12, .020, .030),
 "clay":            ("#9b5940",.87, .065, .11),
 "rubber":          ("#323b37",.93, .020, .08),
 "concrete":        ("#92948a",.88, .045, .13),
 "asphalt":         ("#464a46",.94, .050, .16),
 "soil":            ("#59422e",.96, .100, .22),
 "grass":           ("#596e40",.95, .065, .22),
}
CONDITIONS=("maintained","used","weathered","severely_neglected")
CHANNELS=("albedo","roughness","metallic","height","normal","wear_source","cavity_proxy")

def periodic_field(seed,size,frequencies):
    """Smooth periodic original source texture; same seed produces identical pixels."""
    rng=np.random.default_rng(seed)
    t=np.arange(size,dtype=np.float32)*np.float32(2*np.pi/size)
    x=t[None,:];y=t[:,None]
    out=np.zeros((size,size),dtype=np.float32)
    total=0.
    for index,f in enumerate(frequencies):
        fx=int(f); fy=int(f+index%3+1)
        amp=1.0/(1.0+index*.66)
        phase=float(rng.uniform(0,2*np.pi))
        phase2=float(rng.uniform(0,2*np.pi))
        out += amp * (np.sin(fx*x+fy*y+phase)+.5*np.cos((fy+1)*y-(fx+1)*x+phase2))
        total+=amp*1.5
    return np.clip(out/(total*2)+.5,0,1).astype(np.float32)

def normal_from_height(h,strength):
    dx=np.roll(h,-1,axis=1)-np.roll(h,1,axis=1)
    dy=np.roll(h,-1,axis=0)-np.roll(h,1,axis=0)
    n=np.stack((-dx*strength,dy*strength,np.ones_like(h)),axis=-1)
    n=n/np.sqrt(np.sum(n*n,axis=-1,keepdims=True))
    return np.round((n*.5+.5)*255).clip(0,255).astype("uint8")

def maps_for(family,size,condition):
    if family not in FAMILIES or condition not in range(4):
        raise ValueError("unknown family or condition")
    color_hex,base_rough,relief,variation=FAMILIES[family]
    seed=int(hashlib.sha256((family+":LL_ORIGINAL_MAT_V1").encode()).hexdigest()[:16],16)
    low=periodic_field(seed,size,(1,2,3,4))
    mid=periodic_field(seed+1,size,(5,8,12,17))
    fine=periodic_field(seed+2,size,(23,31,41,53))
    severity=(0.0,.18,.5,1.0)[condition]
    grain=.55*(low-.5)+.33*(mid-.5)+.12*(fine-.5)
    deposition=np.clip(.58*low+.34*mid+.08*fine,0,1)
    dust=np.clip((deposition-(.61-.12*severity))*4,0,1)**1.3
    wear=np.clip(dust*severity+(fine>.81)*.14*severity,0,1)
    h=np.clip(.5+relief*(grain*2)+severity*.015*(dust-.5),0,1)
    rough=np.clip(base_rough+.07*(mid-.5)+.14*wear,0,1)
    base=np.array([int(color_hex[i:i+2],16)/255.0 for i in (1,3,5)],dtype=np.float32)
    tint=1.0+variation*grain*2-severity*.12*dust
    if family=="grass":
        # Color change follows dense clumps; no flat uniform lawn.
        tint+=.12*(fine-.5)
    if family=="asphalt":
        tint+=.04*(fine-.5)
    if family=="ceramic":
        tint+=.008*(fine-.5)
    rgb=np.clip(base[None,None,:]*tint[:,:,None],0,1)
    if family=="clay":
        rgb[:,:,0]=np.clip(rgb[:,:,0]+.055*(mid-.5),0,1)
    if family=="amber_glass":
        # Transmission/IOR belong in Blender shader; RGB alone is NOT glass transparency.
        rough=np.clip(.10+.06*severity*dust+.025*(fine-.5),0,1)
    if family=="paper":
        h=.5+.015*(fine-.5)+.009*(mid-.5)
    if family=="ceramic":
        h=.5+.006*(mid-.5)
    # Preserve source normal convention: OpenGL +Y.
    normal=normal_from_height(h,5.0 if family in ("grass","soil","asphalt","clay") else 2.2)
    byte=lambda a: np.round(np.clip(a,0,1)*255).astype("uint8")
    zero=np.zeros((size,size),dtype=np.uint8)
    return {
       "albedo":(byte(rgb),"RGB"),
       "roughness":(byte(rough),"L"),
       "metallic":(zero,"L"),
       "height":(byte(h),"L"),
       "normal":(normal,"RGB"),
       "wear_source":(byte(wear),"L"),
       "cavity_proxy":(byte(np.clip(1-.20*np.maximum(0,.5-h),0,1)),"L")
    }

def generate(output,size=256,conditions=(0,1,2,3)):
    if size not in (256,512,1024): raise ValueError("size must be 256/512/1024")
    if len(set(conditions))!=len(conditions) or any(c not in range(4) for c in conditions):
        raise ValueError("invalid conditions")
    output.mkdir(parents=True,exist_ok=True)
    records=[]
    for family in FAMILIES:
        for condition in sorted(conditions):
            name=f"{family}_c{condition}"
            folder=output/name;folder.mkdir(exist_ok=True)
            m=maps_for(family,size,condition)
            paths={}
            for channel,(pixels,mode) in m.items():
                file=folder/(channel+".png")
                Image.fromarray(pixels,mode).save(file,optimize=False)
                paths[channel]=str(file.relative_to(output))
            Image.fromarray(m["albedo"][0],"RGB").save(folder/"preview.png")
            # Screen-space edge pixels differ slightly because periodic samples are spaced one pixel apart.
            # Keep a measured edge discontinuity; texture wrapping, not literal pixel equality.
            a=m["albedo"][0].astype("float32")/255
            seam=max(float(np.abs(a[:,0,:]-a[:,-1,:]).mean()),
                     float(np.abs(a[0,:,:]-a[-1,:,:]).mean()))
            if seam > .10: raise ValueError("Unacceptable periodic seam "+name+" "+str(seam))
            records.append(dict(id=name,family=family,condition_level=condition,
                condition_name=CONDITIONS[condition],resolution_px=size,
                source="original_periodic_procedural",rights="ORIGINAL_GENERATED",
                map_files=paths,seam_mean_max=round(seam,6),
                albedo_sha256=hashlib.sha256((folder/"albedo.png").read_bytes()).hexdigest(),
                shader_note="Glass requires transmission/IOR; no geometric edge/handle grime baked",
                status="SOURCE_MAP_CANDIDATE_NOT_GOLDEN_VISUAL_APPROVED"))
            print("LL_EXTRA_MAT",name,round(seam,4),flush=True)
    result=dict(schema_version=1,material_count=len(records),
                family_count=len(FAMILIES),condition_count=len(conditions),
                qa="SOURCE_MAP_SEAMS_AND_HASHES_NOT_GODOT_VISUAL_APPROVAL",records=records)
    (output/"manifest.json").write_text(json.dumps(result,indent=2)+"\n")
    print("LL_EXTRA_MAT_DONE",len(FAMILIES),len(records),flush=True)
    return result

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path,default=Path("build/unified_factory/extra_materials"))
    p.add_argument("--size",type=int,default=256)
    p.add_argument("--conditions",default="0,1,2,3")
    a=p.parse_args()
    generate(a.out,a.size,tuple(map(int,a.conditions.split(","))))

if __name__=="__main__":main()
