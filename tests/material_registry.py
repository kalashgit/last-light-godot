import copy
import importlib.util
import json
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('validator', ROOT/'tools/validate_material_registry.py')
v = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v)

class Materials(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(v.REGISTRY.read_text())
    def test_valid(self):
        self.assertEqual(v.validate(self.data), [])
    def test_invalid_definitions(self):
        mutations = [lambda d: d.update(schema_version=99),
                     lambda d: d['materials'].append(copy.deepcopy(d['materials'][0])),
                     lambda d: d['materials'][0].update(asset_id='missing'),
                     lambda d: d['materials'][0].update(palette={'base':'oops'}),
                     lambda d: d['materials'][0].update(spec_id='missing'),
                     lambda d: d['materials'][0].update(surfaces=['ceiling']),
                     lambda d: d['materials'][7].update(atlas_region_px=[500,0,256,256]),
                     lambda d: d['assets']['wall_atlas'].update(path='res://missing.png'),
                     lambda d: d['assets']['wall_atlas'].update(sha256='wrong'),
                     lambda d: d['assets']['wall_atlas'].update(size_px=[1,1]),
                     lambda d: d['materials'][0].update(tile_px=[64,32])]
        for mutate in mutations:
            d = copy.deepcopy(self.data)
            mutate(d)
            with self.subTest(data=d): self.assertTrue(v.validate(d))
    def test_incompatible_bindings(self):
        catalog=json.loads((ROOT/'assets/buildings/building_archetypes_v1.json').read_text())
        lab=json.loads((ROOT/'assets/buildings/five_building_lab_v2.json').read_text())
        self.assertEqual(v.validate_bindings(self.data,catalog,lab),[])
        lab['buildings'][0]['floor']='brick_aged'
        self.assertTrue(v.validate_bindings(self.data,catalog,lab))

if __name__=='__main__': unittest.main(verbosity=2)
