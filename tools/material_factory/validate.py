#!/usr/bin/env python3
"""Automated technical QA of generated maps, not subjective visual/style approval."""
import hashlib,json,sys
from pathlib import Path
import numpy as np
from PIL import Image
def main(root):
    data=json.loads((root/"manifest.json").read_text())
    assert data["schema"]==1 and len(data["items"])==5
    seen=set()
    keys={"albedo","roughness","normal","height","metallic","wear_source","cavity_proxy"}
    for entry in data["items"]:
        assert entry["id"] not in seen
        seen.add(entry["id"])
        assert set(entry["maps"])==keys
        for key,rel in entry["maps"].items():
            im=Image.open(root/rel)
            assert im.size==(512,512)
            assert im.mode==("RGB" if key in ("albedo","normal") else "L")
            assert np.asarray(im).size>0
            if key=="normal":
                a=np.asarray(im)
                assert np.mean(a[:,:,2])>170,entry["id"]
        metals=np.asarray(Image.open(root/entry["maps"]["metallic"]))
        if entry["family"] in ("wood","fabric","plastic"):
            assert metals.max()==0,entry["id"]
        if entry["family"]=="oxidized_metal":
            assert metals.max()-metals.min()>30,entry["id"]
        sha=hashlib.sha256((root/entry["maps"]["albedo"]).read_bytes()).hexdigest()
        assert sha==entry["sha256_albedo"]
        print("LL_MATERIAL_QA_PASS",entry["id"],flush=True)
    assert (root/"contact-sheet.png").exists()
    assert (root.parent/"LAST_LIGHT_Material_Factory_5_Recipes.zip").stat().st_size>10000
    print("LL_MATERIAL_FACTORY_PASS 5 recipes; maps, channels, metallic physics, metadata",flush=True)
if __name__=="__main__":main(Path(sys.argv[1]))
