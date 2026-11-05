#!/usr/bin/env python3
"""Review inherited swatches; repetition preview does not certify seamlessness."""
import json
from pathlib import Path
from PIL import Image, ImageDraw
ROOT=Path(__file__).resolve().parents[1]
data=json.loads((ROOT/'assets/materials/runtime_materials_v1.json').read_text())
preview=Image.new('RGB',(960,650),'#202b28')
draw=ImageDraw.Draw(preview)
i=0
for material in data['materials']:
    aid=material.get('asset_id')
    if aid is None: continue
    image=Image.open(ROOT/data['assets'][aid]['path'].removeprefix('res://')).convert('RGB')
    region=material.get('atlas_region_px')
    if region:
        x,y,w,h=region
        image=image.crop((x,y,x+w,y+h))
    image=image.resize((90,90))
    x0=(i%3)*320;y0=(i//3)*325
    draw.text((x0+8,y0+7),material['id'],fill='white')
    draw.text((x0+8,y0+23),'3x3 diagnostic; NOT repeat-certified',fill='#c6b98e')
    for y in range(3):
        for x in range(3): preview.paste(image,(x0+8+x*90,y0+43+y*90))
    i+=1
out=ROOT/'docs/checkpoints/modular-factory/material-repetition-review.png'
preview.save(out,optimize=True)
print(out.relative_to(ROOT))
