"""Dependency-free V10 palette and wear-locality regression.

This is NOT a Blender rendering test. Its purpose is to catch parameter drift
before the next full headless Blender/F11/F12 art review.
"""
import ast
import json
import sys
from pathlib import Path

factory=Path(__file__).resolve().parents[3] / 'tools/factory/zombies'
sys.path.insert(0,str(factory))
from f06_reference_recipe_v10 import (JACKET_BASE,JACKET_LINING,
                                       EARTH_TWILL,OLD_DRY_DAMAGE,
                                       localized_damage,periorbital_tone,
                                       palette_is_muted)

assert palette_is_muted((JACKET_BASE,JACKET_LINING,
                        OLD_DRY_DAMAGE,*EARTH_TWILL))
assert len(EARTH_TWILL)==4
peak=localized_damage(.117,1.323)
assert .55<peak<=.72,peak
assert localized_damage(-.10,1.10)<.005
assert localized_damage(.20,1.45)<.02
samples=[localized_damage(-.2+i*.01,1.04+j*.01)
         for j in range(42) for i in range(41)]
assert sum(x>.12 for x in samples)/len(samples)<.13
assert .65<=periorbital_tone(-.055,1.683)<.90
assert periorbital_tone(.0,1.55)>.99

source=(factory/'f06_hero_calibration_v2.py').read_text()
module=ast.parse(source)
functions={n.name for n in module.body if isinstance(n,ast.FunctionDef)}
assert 'refine_v10_reference_grounding' in functions
assert "if args.geometry_profile=='v10_reference':" in source
assert 'V10 open-front work jacket hood' in source
assert 'V10 localized damaged jacket' in source

print(json.dumps({'status':'PASS','scope':'pure-Python V10 material recipe',
                  'peak_damage':round(peak,4),
                  'damage_fraction':round(sum(x>.12 for x in samples)/len(samples),4),
                  'blender_execution':'NOT_RUN',
                  'f11_bake':'NOT_RUN','f12_render':'NOT_RUN'},indent=2))
