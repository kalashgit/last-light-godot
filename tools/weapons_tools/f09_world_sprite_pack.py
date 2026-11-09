"""Package actual fixed-scale Blender world renders into 96px sprite candidates.

No per-tool enlargement, no auto-normalization and no approval promotion.
"""
import json
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/"build"/"f09_integration_fixture"
EXPECTED={"ll_tools_hand_saw","ll_tools_adjustable_wrench","ll_tools_socket_handle"}

def main():
    manifest=json.loads((BASE/"integration_source_manifest.json").read_text())
    assert {x["asset_id"] for x in manifest["records"]}==EXPECTED
    results=[]
    for item in manifest["records"]:
        folder=BASE/item["asset_id"]
        output=folder/"world_sprite_96"
        output.mkdir(exist_ok=True)
        coverage=[]
        for heading in range(16):
            raw=Image.open(folder/"world_16_heading_raw"/f"h{heading:02}.png").convert("RGBA")
            assert raw.size==(384,384)
            bbox=raw.getchannel("A").getbbox()
            assert bbox is not None
            # This is a fixed camera 96px cut, never centered to the object bbox.
            crop_box=(144,144,240,240)
            assert all((bbox[0]>=crop_box[0],bbox[1]>=crop_box[1],
                        bbox[2]<=crop_box[2],bbox[3]<=crop_box[3])),(
                            item["asset_id"],heading,"world sprite clipped",bbox)
            sprite=raw.crop(crop_box)
            mask=sprite.getchannel("A")
            assert mask.getbbox() is not None
            visible=sum(1 for value in mask.getdata() if value>=32)
            assert visible>=20,(item["asset_id"],heading,"invisible world sprite",visible)
            sprite.save(output/f"h{heading:02}.png",optimize=True)
            coverage.append({"heading":heading,"opaque_pixels":visible,"source_bbox":list(bbox)})
        results.append({"asset_id":item["asset_id"],"sprite_size_px":[96,96],
                        "headings":16,"coverage":coverage,
                        "world_camera_scale":item["world_ortho"],
                        "status":"PROVISIONAL_F12_SCALE_NOT_APPROVED"})
    out=BASE/"world_sprite_qa.json"
    out.write_text(json.dumps({"schema":1,"items":results,"f12_approved":False},indent=2)+"\n")
    print("F09_WORLD_NATIVE_SPRITES_PASS",len(results)*16,flush=True)

if __name__=="__main__":main()
