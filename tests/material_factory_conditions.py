"""Deterministic environmental-condition checks for original PBR source maps."""
import importlib.util
import json
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"tools/material_factory/generate.py"
spec=importlib.util.spec_from_file_location("ll_material_generator",SOURCE)
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

recipes=json.loads((ROOT/"tools/material_factory/recipes.json").read_text())
assert len(recipes)==5
for recipe in recipes:
    variants=[mod.material_maps(recipe,256,c) for c in range(4)]
    for c,v in enumerate(variants):
        assert np.array_equal(v["albedo"][0],mod.material_maps(recipe,256,c)["albedo"][0])
        assert v["normal"][0].shape==(256,256,3)
    assert not np.array_equal(variants[0]["albedo"][0],variants[3]["albedo"][0])
    means=[float(v["wear_source"][0].mean()) for v in variants]
    assert all(a<=b+0.001 for a,b in zip(means,means[1:])),(recipe["id"],means)
    if recipe["family"] in ("wood","fabric","plastic"):
        assert all(v["metallic"][0].max()==0 for v in variants)
    print("LL_CONDITION_QA_PASS",recipe["id"],means)
print("LL_CONDITIONS_PASS 5 families x 4 levels, deterministic and monotonic wear")
