"""Output invariants for the optional native 2.5D palette pass."""
import importlib.util
import json
import sys
import tempfile
from pathlib import Path
import numpy as np
from PIL import Image

script=Path(__file__).resolve().parents[1]/"tools/material_factory/pixel_refine.py"
spec=importlib.util.spec_from_file_location("ll_pixel_refine",script)
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)

rgba=np.zeros((48,48,4),dtype=np.uint8)
for y in range(5,43):
    for x in range(7,41):
        rgba[y,x,:3]=((x*7)%256,(y*6)%256,(x*3+y*2)%256)
        rgba[y,x,3]=255
rgba[5,7,3]=128
src=Image.fromarray(rgba,"RGBA")
out=mod.refine_rgba(src,32)
assert out.size==src.size
assert np.array_equal(np.asarray(out)[:,:,3],rgba[:,:,3])
assert len(np.unique(np.asarray(out)[:,:,:3].reshape(-1,3),axis=0))<=33
assert np.array_equal(np.asarray(out),np.asarray(mod.refine_rgba(src,32)))
assert mod.comparison(src,out).size[0]>src.width
assert not np.array_equal(np.asarray(out),np.asarray(mod.refine_rgba(src,32,0)))
for bad in (-.01,2.01):
    try: mod.refine_rgba(src,32,bad)
    except ValueError: pass
    else: raise AssertionError("Invalid detail level accepted")

# Any furniture or tile collection uses the exact same scale-preserving batch.
sys.path.insert(0,str(script.parent))
import pixel_batch
with tempfile.TemporaryDirectory() as temp:
    root=Path(temp)
    source=root/"game_ready";output=root/"candidate"
    (source/"sofa").mkdir(parents=True)
    src.save(source/"sofa/ground.png")
    (source/"manifest.json").write_text(json.dumps({"items":[{"name":"sofa",
        "world_sprite":"sofa/ground.png","anchor_px":[25,45]}]}))
    result=pixel_batch.candidates(source,output,48,.65)
    assert result["approved_replacements"]==0
    assert result["items"][0]["alpha_preserved"]
    assert (output/"comparison-220-percent.png").stat().st_size>1000
    assert (output/"LAST_LIGHT_pixel_finish_candidates.zip").stat().st_size>1000
print("LL_PIXEL_REFINE_PASS alpha, dimensions, palette, detail, batch packaging and 3 zoom previews")
