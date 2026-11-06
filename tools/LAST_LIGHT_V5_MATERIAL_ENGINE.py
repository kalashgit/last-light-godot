#!/usr/bin/env python3
"""LAST LIGHT V5 — offline, single-file material renderer and V4 benchmark upgrader.

Uses ONLY Pillow and standard Python. Respects the Golden 40 *style* as a
qualitative reference; does not reuse reference-sheet pixels. Does not confer
founder or Godot approval. Supports native geometry recipes and a migration
path from prior V4 transparent candidate PNGs.

Run:
  python LAST_LIGHT_V5_MATERIAL_ENGINE.py --input-zip V4_CANDIDATES.zip --output OUT
  python LAST_LIGHT_V5_MATERIAL_ENGINE.py --recipe recipe.json --output OUT
"""
from __future__ import annotations
import argparse, hashlib, io, json, math, os, random, tempfile, zipfile
from pathlib import Path
from PIL import Image, ImageDraw, ImageChops, ImageFilter, ImageFont

VERSION = 'll.v5.material_physics.0.3'
# Paint codes are legacy V4 material families; no third-party pixels are read.
PALETTES = {
 'steel':['#252e33','#46535a','#687a82','#8b9ba0','#b6c3c7','#e2e5dc'],
 'blued_steel':['#1d292e','#35484e','#50636b','#6c8289','#91a4a7','#c8d1cd'],
 'aluminum':['#3a4549','#5d696c','#8a9899','#b2c0be','#d1dad4','#edf0e8'],
 'wood':['#37251e','#5a3c2b','#805739','#a1754d','#bd9364','#dfb67c'],
 'olive_canvas':['#283129','#3d4937','#586b4a','#758466','#98a487','#bec3a8'],
 'khaki_canvas':['#37352c','#5c5a46','#80795e','#a29a78','#c4b997','#e0d4b2'],
 'leather':['#2b201b','#493126','#694633','#906346','#b18560','#d5ab7c'],
 'rubber':['#151d1e','#293436','#3f4b4c','#596566','#798486','#a1aaab'],
 'paper':['#625e4f','#8c8570','#b1a993','#d0c8b2','#e5decc','#f6efdc'],
 'medical_blue':['#263e49','#3c6070','#598092','#7ba3b1','#acc6cd','#d4e3df'],
 'painted_red':['#402a2b','#713c3b','#98544a','#b8715a','#d69b76','#efc0a0'],
 'painted_green':['#27362d','#3e5240','#557157','#768d6d','#9aaa8c','#cfceb0'],
 'glass':['#23383f','#3e5e65','#668388','#91b1b3','#b8d1cf','#e0ede6'],
 'amber_glass':['#392e22','#62432b','#8b6438','#b38b51','#c5a66c','#ecce93'],
 'crystal':['#281f37','#473059','#684779','#9065a0','#b08dbb','#dfc7e5'],
 'stone':['#303337','#4c5051','#696f6f','#8e9290','#b1b2a9','#d4d2c5'],
}
KINDS = {
 'steel':'metal','blued_steel':'metal','aluminum':'metal',
 'wood':'wood','olive_canvas':'cloth','khaki_canvas':'cloth',
 'leather':'leather','rubber':'rubber','paper':'paper',
 'medical_blue':'plastic','painted_red':'paint','painted_green':'paint',
 'glass':'glass','amber_glass':'glass','crystal':'crystal','stone':'stone',
}
RGB = {m:[tuple(bytes.fromhex(c[1:])) for c in cols] for m,cols in PALETTES.items()}
LOOKUP = {color:(m,i) for m, colors in RGB.items() for i,color in enumerate(colors)}
SCALE=2   # 128 working master from 64 logical-grid recipe

def stable_seed(*parts):
    return int.from_bytes(hashlib.sha256('|'.join(map(str,parts)).encode()).digest()[:8], 'big')

def shade(rgb, shift, warmth=0):
    return tuple(max(0,min(255,round(c + shift + (warmth if i==0 else -warmth if i==2 else 0)))) for i,c in enumerate(rgb))

def safe_save(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile(mode='wb',dir=path.parent,prefix='.v5-',delete=False) as f:
        f.write(data); f.flush(); os.fsync(f.fileno()); tmp=f.name
    os.replace(tmp,path)

def as_png(im):
    buf=io.BytesIO(); im.save(buf,format='PNG',optimize=False); return buf.getvalue()

def material_mask_legacy(im,material):
    """Exact legacy palette lookup, without recoloring third-party source art."""
    im=im.convert('RGBA')
    mask=Image.new('L',im.size,0); p=im.load(); q=mask.load()
    n=0
    for y in range(im.height):
        for x in range(im.width):
            if p[x,y][3] and LOOKUP.get(p[x,y][:3],(None,None))[0]==material:
                q[x,y]=255;n+=1
    return mask,n

def _material_pass(im,mask,material,seed,orientation='auto',tone_bias=0,detail=1.0,face_normal=None,roughness=None,wear_state='clean'):
    """Paint a physically differentiated surface within an existing mask only.

    Uses edge distance, 10:30 top-left key, material-specific broad reflection,
    anisotropic grain and *edge-local* wear. All micro-marking is deterministic.
    """
    material=material if material in KINDS else 'stone'
    if wear_state not in ('clean','used','weathered'):
        raise ValueError('Unsupported condition state')
    if face_normal is not None:
        if not isinstance(face_normal,(list,tuple)) or len(face_normal)!=3:
            raise ValueError('face_normal must be a 3-vector')
        normal=[float(v) for v in face_normal]
        length=math.sqrt(sum(v*v for v in normal))
        if not .001 < length < 1000:
            raise ValueError('face_normal magnitude invalid')
        normal=[v/length for v in normal]
        light=(-.45,-.65,.61)
        ndotl=sum(v*l for v,l in zip(normal,light))
        tone_bias += max(-13,min(13,ndotl*13))
    if roughness is not None:
        if not isinstance(roughness,(int,float)) or not 0<=roughness<=1:
            raise ValueError('roughness must be between 0 and 1')
    else:
        roughness={'metal':.3,'glass':.13,'crystal':.24,'wood':.73,'cloth':.91,'leather':.65,'paper':.97,'rubber':.83}.get(KINDS[material],.8)
    kind=KINDS[material]
    b=mask.getbbox()
    if not b: return im
    x0,y0,x1,y1=b; w=x1-x0; h=y1-y0
    if w<2 or h<2:return im
    color=im.load(); mx=mask.load()
    pix=im.copy().load() # original values preserve authored V4 planes
    inside=mask.filter(ImageFilter.MinFilter(3))
    insidepix=inside.load()
    rng=random.Random(seed)
    # Orientation is only the grain *axis*, not an undocumented image rotation.
    # 'vertical' for shafts, bags and bottles; 'horizontal' for sheets and bars.
    vertical = (h>w*1.35) if orientation=='auto' else orientation=='vertical'
    # Material surface coherence measured on the entire nontransparent region.
    # This pattern does not synthesize the construction or the object identity.
    metal_band=((x0+x1)//2 + seed%7-3)
    hash01=lambda x,y: (stable_seed(seed,x//2,y//2)%1000)/1000
    for y in range(y0,y1):
        for x in range(x0,x1):
            if not mx[x,y]: continue
            old=pix[x,y]; rgb=old[:3]
            if old[3]==0:continue
            # Controlled plane gradient: lit upper-left; deep lower-right.
            nx=(x-x0)/(max(1,w-1));ny=(y-y0)/(max(1,h-1))
            base=(0.65-nx)*5.5 + (0.55-ny)*6.5 + tone_bias
            if kind=='metal':
                # Narrow near-vertical satin stripe, broader dark face.
                d=abs(x-metal_band)/max(1,w)
                base+= max(0,1-d*(5+11*(1-roughness)))*(9+13*(1-roughness)) - 2
            elif kind=='glass':
                d=abs(nx-.18)
                base += max(0,1-d*10)*17 - 3
            elif kind=='crystal':
                # Separate broad facet bands; angular breaks, no arbitrary glow.
                facet=(x-x0 + (y-y0)//2)%max(7,w//2)
                base+= 9 if facet < max(1,w//6) else (-5 if facet>max(5,w//3) else 1)
            elif kind in ('cloth','paper'): base*=.55
            elif kind in ('wood','leather'): base*=.75
            elif kind=='rubber': base*=.35
            # Edge response: light catches upper-left rim, dark catches lower-right.
            edge=not insidepix[x,y]
            if edge:
                # Ignore edges caused by tone boundaries (legacy extracted mask may have holes).
                up=mx[max(x0,x-1),y] and mx[x,max(y0,y-1)]
                down=mx[min(x1-1,x+1),y] and mx[x,min(y1-1,y+1)]
                if kind in ('metal','crystal','glass'):
                    base += 13 if not up else (-11 if not down else 1)
                elif kind in ('cloth','wood','leather'):
                    base += 4 if not up else (-7 if not down else 0)
                else: base+= 3 if not up else -4
            # Directional micro-grain only on sufficiently broad faces.
            grain=0
            if w>=7 and h>=7 and insidepix[x,y] and detail>0:
                if kind=='wood':
                    coord=x if vertical else y
                    aligned=y if vertical else x
                    if (coord + (aligned//11)%2) % 7 in (0,1) and hash01(x//4,aligned//7)>.28: grain=-8
                elif kind=='metal':
                    if (y if vertical else x)%7==seed%7 and hash01(x,y)>.40:grain=7
                elif kind=='cloth':
                    if (x + y//4)%7==seed%7 and (y%6 in (0,1)):grain=-5
                elif kind=='leather':
                    if (x*3+y*2+seed)%19==0:grain=-5
                elif kind=='paper':
                    if (x+y*2+seed)%31==0:grain=-2
                elif kind=='stone':
                    if (x+y*3+seed)%23==0:grain=-6
                elif kind=='crystal':
                    if (x+y//2+seed)%17==0:grain=5
                elif kind=='glass':
                    if (x-x0)%max(5,w//3)==0 and y%5!=0:grain=4
            # Tiny clustered abrasion only near physical edge, *not* global dust noise.
            # Do not apply on sterile/surgical paper or pristine glass.
            wear=0
            if wear_state!='clean' and edge and kind in ('metal','wood','leather','stone') and hash01(x,y)>(.97 if wear_state=='used' else .90):
                wear=5 if kind=='metal' else -5
            rgb=shade(rgb,base+grain*detail+wear)
            color[x,y]=(*rgb,old[3])
    return im

def material_enhance_legacy(icon,asset_id,scale=2):
    """Conservative non-destructive re-lighting, not a general icon generator."""
    icon=icon.convert('RGBA')
    if icon.size!=(64,64):raise ValueError('V4 migration expects 64px sprites')
    # upscale only by exact integer replication, retaining the authored pixel grid.
    im=icon.resize((64*scale,64*scale),Image.Resampling.NEAREST)
    # Reuse exact palette-segmentation masks of the *original*, never re-segment
    # the already modified output. This prevents material color mixing errors.
    source=im.copy()
    order=['wood','olive_canvas','khaki_canvas','leather','paper','medical_blue',
           'painted_red','painted_green','rubber','glass','amber_glass','stone',
           'steel','blued_steel','aluminum','crystal']
    stats={}
    for m in order:
        mask,count=material_mask_legacy(source,m)
        if count>0:
            im=_material_pass(im,mask,m,stable_seed(asset_id,m));stats[m]=count
    # Unclassified legacy pixels are left byte-identical. Alpha must be unchanged.
    if im.getchannel('A').tobytes()!=source.getchannel('A').tobytes():
        raise AssertionError('Material pass mutated alpha')
    return im,stats

def _paint_geometry(mask,layer,S):
    d=ImageDraw.Draw(mask)
    shape=layer['shape']
    if shape=='polygon':d.polygon([tuple(v*S for v in p) for p in layer['points']],fill=255)
    elif shape=='line':d.line([tuple(v*S for v in p) for p in layer['points']],fill=255,width=max(1,layer.get('width',1)*S),joint='curve')
    elif shape=='ellipse':d.ellipse(tuple(v*S for v in layer['bbox']),fill=255)
    elif shape=='rectangle':d.rectangle(tuple(v*S for v in layer['bbox']),fill=255)
    elif shape=='point':d.point(tuple(v*S for v in layer['xy']),fill=255)
    else:raise ValueError('Unsupported shape: '+shape)

def render_recipe(recipe,S=2):
    """Data-only components; no per-item drawing functions. Accepts V4 layer schema.

    Shape plane visibility is deterministic; layer-specific semantic orientation
    and face direction are optional schema additions. Alpha remains pixel crisp.
    """
    if recipe.get('approval')!='candidate_needs_founder_review' or recipe.get('rights')!='original_independent_design':
        raise ValueError('Candidate/rights state required; no auto-approval')
    if recipe.get('size') != [64,64] or not recipe.get('layers'):
        raise ValueError('Expected versioned 64px geometry layers')
    size=(64*S,64*S)
    out=Image.new('RGBA',size)
    for i,layer in enumerate(recipe['layers']):
        m=layer['material']
        if m not in PALETTES or m not in recipe.get('materials',[]):raise ValueError('Unknown material')
        tone=layer['tone']
        if not isinstance(tone,int) or not 0<=tone<=5:raise ValueError('Invalid tone')
        mask=Image.new('L',size,0)
        _paint_geometry(mask,layer,S)
        col=Image.new('RGBA',size,RGB[m][tone]+(255,))
        _material_pass(col,mask,m,stable_seed(recipe['id'],layer['name']),
             orientation=layer.get('grain_axis','auto'),
             tone_bias=float(layer.get('light_bias',0)),
             detail=max(0,min(1,float(layer.get('detail',1)))),
             face_normal=layer.get('face_normal'),roughness=layer.get('roughness'),
             wear_state=layer.get('wear_state','clean'))
        col.putalpha(mask)
        out.alpha_composite(col)
    return out

def nearest_export(master):
    """64px export with stable grid. Preview at 128 master is the detail authority."""
    if master.size!=(128,128):raise ValueError('128 working canvas required')
    # Sample central sub-pixel so details never bleed through transparency.
    # No blur, glow or interpolated alpha introduced.
    result=Image.new('RGBA',(64,64)); rp=result.load(); mp=master.load()
    for y in range(64):
        for x in range(64):rp[x,y]=mp[x*2+1,y*2+1]
    return result

def qa_png(im,orig=None):
    if im.mode!='RGBA':raise ValueError('PNG not RGBA')
    a=im.getchannel('A'); bb=a.getbbox()
    if not bb:raise ValueError('Empty artwork')
    if bb[0]<=0 or bb[1]<=0 or bb[2]>=im.width or bb[3]>=im.height:
        raise ValueError('Potential frame clipping')
    if orig is not None and (a.size!=orig.getchannel('A').size or a.tobytes()!=orig.getchannel('A').tobytes()):
        raise ValueError('Alpha contract regression')
    return {'rgba':True,'bbox':list(bb),'technical_valid':True,'founder_approved':False,'godot_integrated':False}

def sheet(pairs,scale,background):
    cols=4; rows=(len(pairs)+cols-1)//cols; slot=196
    bg='#252932' if background=='dark' else '#e4e1d8'
    fg='#f6ecda' if background=='dark' else '#242d31'
    im=Image.new('RGB',(cols*slot,rows*slot),bg);d=ImageDraw.Draw(im)
    for i,(label,icon) in enumerate(pairs):
        x=i%cols*slot;y=i//cols*slot
        d.rounded_rectangle((x+3,y+3,x+192,y+192),radius=6,fill='#333b43' if background=='dark' else '#f0ece4')
        size=min(128,max(32,scale))
        thumb=icon.resize((size,size),Image.Resampling.NEAREST)
        # Show master at intended size; no label pixels baked into sprites.
        im.paste(thumb,(x+(slot-size)//2,y+29+(130-size)//2),thumb)
        d.text((x+9,y+9),label[:23],font=ImageFont.load_default(),fill=fg)
        d.text((x+9,y+171),'CANDIDATE / NOT APPROVED',font=ImageFont.load_default(),fill=fg)
    return im

def produce_from_zip(input_zip,output):
    output=Path(output)
    with zipfile.ZipFile(input_zip) as z:
        names=sorted(n for n in z.namelist() if n.startswith('candidates/') and n.endswith('.png'))
        if len(names)!=12:raise ValueError('Expected 12 V4 benchmark candidates')
        pairs=[];manifest=[]
        for name in names:
            original=Image.open(io.BytesIO(z.read(name))).convert('RGBA')
            slug=Path(name).stem
            working,material_pixels=material_enhance_legacy(original,slug)
            small=nearest_export(working)
            qa=qa_png(small,original)
            master=as_png(working);png=as_png(small)
            safe_save(output/'candidates_128'/f'{slug}.png',master)
            safe_save(output/'candidates_64'/f'{slug}.png',png)
            pairs.append((slug,working))
            manifest.append({'id':f'll.benchmark.{slug}', 'source':'v4_candidate_semantic_color_migration',
                            'master':f'candidates_128/{slug}.png', 'export':f'candidates_64/{slug}.png',
                            'sha256_master':hashlib.sha256(master).hexdigest(),
                            'sha256_export':hashlib.sha256(png).hexdigest(),
                            'materials_detected':material_pixels,'qa':qa,
                            'visual':'candidate_reject_pending_founder_review'})
    for theme in ('light','dark'):
        for sz in (32,64,128):
            safe_save(output/'reviews'/f'v5_{sz}_{theme}.png',as_png(sheet(pairs,sz,theme)))
    report={'engine':VERSION,'count':len(manifest),'inputs':'existing V4 original candidate pixels only',
            'technical_vs_visual':'technical pass does NOT imply golden fidelity',
            'reference_pixels_copied':False,'founder_approved_count':0,
            'godot_integrated_count':0,'items':manifest}
    safe_save(output/'manifest.json',json.dumps(report,indent=2).encode())
    archive=output/'LAST_LIGHT_V5_MATERIAL_BENCHMARK_CANDIDATES.zip'
    paths=sorted(p for p in output.rglob('*') if p.is_file() and p!=archive)
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
        for p in paths:
            info=zipfile.ZipInfo(str(p.relative_to(output)),date_time=(2026,1,1,0,0,0))
            z.writestr(info,p.read_bytes(),compress_type=zipfile.ZIP_DEFLATED)
    return {'count':len(manifest),'zip':str(archive),'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'bytes':archive.stat().st_size}

def produce_from_recipes(recipe_path,output):
    """Authoring mode: reproducible PNGs, contact sheets, states and ZIP.

    Catalog identity and human visual approval remain external to this render step.
    """
    source=Path(recipe_path).read_bytes()
    payload=json.loads(source)
    recipes=payload.get('recipes') if isinstance(payload,dict) and 'recipes' in payload else payload
    if isinstance(recipes,dict):recipes=[recipes]
    if not isinstance(recipes,list) or not recipes:raise ValueError('Recipes required')
    output=Path(output)
    seen=set();pairs=[];items=[]
    for recipe in recipes:
        asset_id=recipe.get('id','')
        if asset_id in seen or not asset_id.startswith('ll.'):raise ValueError('Invalid or duplicated ID')
        seen.add(asset_id)
        master=render_recipe(recipe)
        icon=nearest_export(master)
        qa=qa_png(icon)
        name=asset_id.split('.')[-1]
        mb=as_png(master);sb=as_png(icon)
        safe_save(output/'candidates_128'/f'{name}.png',mb)
        safe_save(output/'candidates_64'/f'{name}.png',sb)
        pairs.append((recipe.get('label',name),master))
        items.append({'id':asset_id,'description':recipe.get('semantic_brief',''),
                      'materials':recipe['materials'],'component_count':len(recipe['layers']),
                      'size':list(icon.size),'sha256':hashlib.sha256(sb).hexdigest(),
                      'rights':'original_independent_design',
                      'state':'candidate_needs_founder_review','qa':qa})
    for theme in ('light','dark'):
        for size in (32,64,128):
            safe_save(output/'reviews'/f'authored_{size}_{theme}.png',as_png(sheet(pairs,size,theme)))
    manifest={'engine':VERSION,'mode':'original_semantic_recipe','input_sha256':hashlib.sha256(source).hexdigest(),
              'count':len(recipes),'founder_approved_count':0,'godot_integrated_count':0,
              'rights':'original_independent_design','items':items}
    safe_save(output/'manifest.json',json.dumps(manifest,sort_keys=True,indent=2).encode('utf8'))
    archive=output/'LAST_LIGHT_V5_AUTHORED_ORIGINAL_CANDIDATES.zip'
    files=sorted(p for p in output.rglob('*') if p.is_file() and p != archive)
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
        for f in files:
            info=zipfile.ZipInfo(f.relative_to(output).as_posix(),date_time=(2026,1,1,0,0,0))
            z.writestr(info,f.read_bytes(),compress_type=zipfile.ZIP_DEFLATED)
    return {'count':len(recipes),'zip':str(archive),'sha256':hashlib.sha256(archive.read_bytes()).hexdigest()}


def main():
    ap=argparse.ArgumentParser()
    group=ap.add_mutually_exclusive_group(required=True)
    group.add_argument('--input-zip',type=Path)
    group.add_argument('--recipe',type=Path)
    ap.add_argument('--output',type=Path,default=Path('LAST_LIGHT_V5_CANDIDATES'))
    args=ap.parse_args()
    if args.input_zip:
        print(json.dumps(produce_from_zip(args.input_zip,args.output),indent=2))
    else:
        print(json.dumps(produce_from_recipes(args.recipe,args.output),indent=2))
if __name__=='__main__':main()
