"""Static 3D weapons/tools production contract; runnable without Blender."""
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"/"asset_factory"))
from catalog import registry


def test_recipe_contract():
    recipes=json.loads((ROOT/"tools/weapons_tools/recipes.json").read_text())
    assert recipes["schema"]==1
    assert recipes["camera"].startswith("existing_blender_v3_fixed_2_to_1")
    assert recipes["base_world_tile_px"]==[80,40]
    assert len(recipes["assets"])==10
    names=[a["asset_id"] for a in recipes["assets"]]
    assert len(set(names))==len(names)
    registered={row["id"]:row for row in registry()}
    assert set(names)<=registered.keys()
    assert set(a["archetype"] for a in recipes["assets"])=={
        "awl","screwdriver","hammer","hatchet","crowbar",
        "wrench","saw","knife","shovel","machete"}
    for a in recipes["assets"]:
        assert a["name"]==registered[a["asset_id"]]["name"]
        assert len(a["dimensions_m"])==3
        assert all(.01<=x<2 for x in a["dimensions_m"])
        assert a["dimensions_m"][1]>a["dimensions_m"][0]
        assert a["material_preset"]
    assert "ll_tools_awl" in names
    assert "ll_tools_cross_screwdriver" in names
    print("LL_WEAPONS_TOOLS_RECIPE_TEST_PASS 10 immutable IDs, 10 distinct silhouettes")


if __name__=="__main__":test_recipe_contract()
