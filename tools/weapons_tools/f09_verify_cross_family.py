"""Fail closed on fake/blank F09 F11/F12 cross-stage asset outputs."""
import json
import struct
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/"build"/"f09_integration_fixture"
STAGE=ROOT/"build"/"f09_godot_stage"

def glb_json(path):
    data=path.read_bytes()
    if data[:4]!=b"glTF":raise AssertionError("bad GLB "+str(path))
    total=struct.unpack_from("<I",data,8)[0]
    assert total==len(data),("truncated GLB",path,total,len(data))
    length,typ=struct.unpack_from("<II",data,12)
    assert typ==0x4e4f534a
    return json.loads(data[20:20+length])

def main():
    records=json.loads((BASE/"integration_source_manifest.json").read_text())["records"]
    assert len(records)==3
    result=[]
    for item in records:
        ident=item["asset_id"]
        folder=BASE/ident
        atlas=Image.open(folder/"albedo_baked.png").convert("RGBA")
        assert atlas.size==(512,512)
        rgb=atlas.convert("RGB")
        assert len(rgb.resize((64,64)).getcolors(4096) or [])>60,("blank/simple atlas",ident)
        document=glb_json(folder/"preview_albedo_baked.glb")
        for filename in ("roughness_baked.png","metallic_baked.png",
                         "normal_tangent_baked.png",
                         "occlusion_roughness_metallic.png"):
            img=Image.open(folder/filename).convert("RGB")
            assert img.size==(512,512),(ident,filename,"invalid map size")
            assert (folder/filename).stat().st_size>3000,(ident,filename,"empty map")
        assert item.get("pbr_maps_complete") is True
        materials=document.get("materials",[])
        assert len(materials)>=3
        assert len(document.get("images",[]))>=2, ("GLB lost PBR textures",ident)
        assert all(mat.get("pbrMetallicRoughness",{}).get("baseColorTexture")
                   for mat in materials),("GLB lost albedo texture",ident)
        assert all(mat.get("normalTexture") for mat in materials),(
            "GLB lost tangent normals",ident)
        assert all(mat.get("pbrMetallicRoughness",{}).get("metallicRoughnessTexture")
                   for mat in materials),("GLB lost packed ORM map",ident)
        for h in range(16):
            sprite=Image.open(folder/"world_sprite_96"/f"h{h:02}.png")
            assert sprite.size==(96,96)
            assert sprite.convert("RGBA").getchannel("A").getbbox() is not None
            assert (STAGE/"sprites"/ident/f"h{h:02}.png").exists()
        assert (STAGE/"models"/(ident+".glb")).exists()
        result.append({"asset_id":ident,"baked_atlas":[512,512],
                       "embedded_texture_count":len(document["images"]),
                       "glb_materials":len(materials),
                       "world_frames":16,"world_frame_size":[96,96],
                       "status":"CROSS_FAMILY_FIXTURE_NOT_APPROVED"})
    (BASE/"cross_family_validation.json").write_text(json.dumps({
        "checked":result,"f11_approved":False,"f12_approved":False,
        "godot_gameplay_approved":False},indent=2)+"\n")
    print("F09_CROSS_FAMILY_FILE_QA_PASS",len(result),"tools",flush=True)

if __name__=="__main__":
    main()
