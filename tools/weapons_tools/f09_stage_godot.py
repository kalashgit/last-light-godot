"""Create an isolated Godot project with only the three F09 baked GLBs and 48 sprites."""
import json
import shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
SRC=ROOT/"build"/"f09_integration_fixture"
DST=ROOT/"build"/"f09_godot_stage"
IDS=("ll_tools_hand_saw","ll_tools_adjustable_wrench","ll_tools_socket_handle")
def main():
    DST.mkdir(parents=True,exist_ok=True)
    (DST/"project.godot").write_text(
        'config_version=5\n[application]\nconfig/name="F09 Isolated Candidate Gameplay QA"\n'
        '[rendering]\nrenderer/rendering_method="gl_compatibility"\n'
        'renderer/rendering_method.mobile="gl_compatibility"\n')
    (DST/"fixture.gd").write_text(
        (ROOT/"tools"/"weapons_tools"/"f09_godot_fixture.gd").read_text())
    # Reuse the real LAST LIGHT gameplay source, without changing it.
    # This is an isolated copy, not the main game's running scene.
    shutil.copytree(ROOT/"scripts",DST/"scripts",dirs_exist_ok=True)
    shutil.copytree(ROOT/"data",DST/"data",dirs_exist_ok=True)
    shutil.copyfile(ROOT/"main.tscn",DST/"main.tscn")
    # Real in-game lookup tables refer to these canonical Golden 40 icons.
    # Copy actual repository files; never fabricate placeholder art.
    golden=ROOT/"assets"/"last_light"/"golden40"
    assert golden.is_dir(),"Golden 40 assets not present in repo"
    shutil.copytree(golden,DST/"assets"/"last_light"/"golden40",
                    dirs_exist_ok=True)
    # Main house_art.gd reads this genuine factory manifest and the matching
    # grounded furniture/decor sprites. Stage only referenced assets; copying
    # the entire production factory would be wasteful and obscure defects.
    original_factory=ROOT/"assets"/"generated"/"factory"
    manifest_path=original_factory/"manifest.json"
    assert manifest_path.exists(),"Actual gameplay factory manifest missing"
    factory_dst=DST/"assets"/"generated"/"factory"
    factory_dst.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(manifest_path,factory_dst/"manifest.json")
    manifest=json.loads(manifest_path.read_text())
    house_layout=json.loads((ROOT/"data"/"house_layout.json").read_text())
    referenced={entry["asset_id"] for category in ("furniture","decorations")
                for entry in house_layout.get(category,[])}
    factory_map={obj["id"]:obj for obj in manifest["objects"]}
    assert referenced.issubset(factory_map),referenced-set(factory_map)
    for asset_id in sorted(referenced):
        definition=factory_map[asset_id]
        ground=[frame["file"] for frame in definition["frames"]
                if frame["mode"]=="ground"]
        assert ground,("ground frame missing",asset_id)
        for filename in ground:
            origin=original_factory/filename
            dest=factory_dst/filename
            assert origin.is_file(),origin
            dest.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(origin,dest)
    print("F09_REAL_HOUSE_FACTORY_STAGED",len(referenced),flush=True)
    (DST/"main_game_fixture.gd").write_text(
        (ROOT/"tools"/"weapons_tools"/"f09_main_game_fixture.gd").read_text())
    (DST/"real_pickup_fixture.gd").write_text(
        (ROOT/"tools"/"weapons_tools"/"f09_real_pickup_fixture.gd").read_text())
    (DST/"graphical_house_fixture.gd").write_text(
        (ROOT/"tools"/"weapons_tools"/"f09_graphical_house_fixture.gd").read_text())
    (DST/"f09_candidate_16_heading_atlas.png").write_bytes(
        (SRC/"f09_candidate_16_heading_atlas.png").read_bytes())
    (DST/"f09_candidate_16_heading_atlas.json").write_bytes(
        (SRC/"f09_candidate_16_heading_atlas.json").read_bytes())
    for ident in IDS:
        source=SRC/ident
        out=DST/"sprites"/ident
        out.mkdir(parents=True,exist_ok=True)
        for heading in range(16):
            name=f"h{heading:02}.png"
            shutil.copyfile(source/"world_sprite_96"/name,out/name)
        models=DST/"models"
        models.mkdir(exist_ok=True)
        shutil.copyfile(source/"preview_albedo_baked.glb",models/(ident+".glb"))
    # INTEGRATION TEST ONLY: add provisional inventory definitions and
    # art records in the throwaway clone, NEVER modify the real data files.
    recipes=json.loads((ROOT/"tools"/"weapons_tools"/"recipes.json").read_text())
    selected={entry["asset_id"]:entry for entry in recipes["assets"]
              if entry["asset_id"] in IDS}
    assert len(selected)==3
    item_path=DST/"data"/"survival_items.json"
    inventory=json.loads(item_path.read_text())
    original={entry["id"] for entry in inventory["items"]}
    assert not original.intersection(IDS),"provisional fixture already canonical"
    factory_manifest=json.loads((factory_dst/"manifest.json").read_text())
    for ident in IDS:
        recipe=selected[ident]
        inventory["items"].append({
            "id":ident,"art_id":ident,"name":recipe.get("display_name",recipe["name"]),
            "category":"Tools","kind":"utility","weight_kg":0.55,
            "stack_max":1,
        })
        src=SRC/ident/"world_sprite_96"
        target=factory_dst/"sprites"/ident
        target.mkdir(parents=True,exist_ok=True)
        frames=[]
        for heading in range(16):
            filename=f"h{heading:02}.png"
            shutil.copyfile(src/filename,target/filename)
            frames.append({
                "file":f"sprites/{ident}/{filename}",
                "mode":"ground" if heading==0 else "held",
                "angle_degrees":heading*22.5,
                "size_px":[96,96],
                "anchor_px":[48,48],
                "source_canvas_px":[384,384],
                "crop_rect_px":[144,144,240,240]})
        factory_manifest["objects"].append({
            "id":ident,"name":recipe["name"],"category":"tools",
            "family":"f09_v18_candidate",
            "dimensions_m":recipe["dimensions_m"],
            "collision":{"footprint_m":recipe["dimensions_m"][:2],
                         "solid":False},
            "visible_carry":False,"frames":frames,
            "status":"PROVISIONAL_CANDIDATE_ISOLATED_TEST_ONLY",
            "license":"CC0-1.0","source":"F09 procedural candidate"})
    item_path.write_text(json.dumps(inventory,indent=2)+"\\n")
    (factory_dst/"manifest.json").write_text(
        json.dumps(factory_manifest,indent=2)+"\\n")
    print("F09_ACTUAL_INVENTORY_FIXTURE_STAGED",len(IDS),flush=True)
    (DST/"candidate_manifest.json").write_text(json.dumps({
        "status":"ISOLATED_GODOT_CANDIDATE_NOT_MAIN_GAME",
        "tools":list(IDS),"sprite_count":48,"baked_glbs":3},indent=2)+"\n")
    print("F09_GODOT_STAGE_PACK_PASS",DST,flush=True)
if __name__=="__main__":main()
