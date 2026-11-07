"""Independent, built-output checks for four original transparent world sprites."""
import json, sys
from pathlib import Path
from PIL import Image
def main(root: Path):
    m=json.loads((root/"manifest.json").read_text())
    assert m["schema"]==1 and m["tile_px"]==[80,40]
    assert {i["name"] for i in m["items"]}=={"refrigerator","cabinet","sofa","crate"}
    for item in m["items"]:
        assert item["representation"]=="world_facing_original_2_5d_candidate"
        assert all(v>0 for v in item["dimensions_m"])
        path=root/item["world_sprite"]
        assert path.exists()
        img=Image.open(path)
        assert img.mode=="RGBA"
        assert max(img.getchannel("A").getextrema())==255
        assert img.getchannel("A").getextrema()[0]==0
        assert list(img.size)==item["size_px"]
        pivot=item["anchor_px"]
        assert -30<pivot[0]<img.width+30 and -30<pivot[1]<img.height+30
        for key in ("shadow_sprite","icon_sprite"): assert (root/item[key]).exists()
        print(f"PASS {item['name']}: {img.size}, contact {pivot}, transparent")
    print("PASS: 4 original asset entries, 80x40 projection, textures, anchor, alpha and shadows")
if __name__=="__main__":
    main(Path(sys.argv[1]))
