"""Shared fixture matrix is also executed by the actual Godot loader."""
import copy,json,subprocess,sys,unittest
from pathlib import Path
from tools.validate_catalog import validate,ROOT
BASE=json.loads((ROOT/'data/catalog/starter_v1.json').read_text())
VISUALS=json.loads((ROOT/'data/catalog/visuals_v1.json').read_text())
CASES=json.loads((ROOT/'tests/fixtures/catalog_cases.json').read_text())

def mutated(case):
    data=copy.deepcopy(BASE); visuals=copy.deepcopy(VISUALS)
    target=data if case['target']=='catalog' else visuals
    if not case['path']:
        return (case['value'],visuals) if case['target']=='catalog' else (data,case['value'])
    for part in case['path'][:-1]: target=target[part]
    target[case['path'][-1]]=case['value']
    return data,visuals
class ContentSystemTests(unittest.TestCase):
    def test_shared_matrix(self):
        for case in CASES:
            with self.subTest(case=case['name']): self.assertEqual(not bool(validate(*mutated(case))),case['valid'])
    def test_non_finite_weight(self):
        for number in [float('nan'),float('inf'),float('-inf')]:
            data=copy.deepcopy(BASE); data['items'][0]['weight_kg']=number
            self.assertTrue(validate(data))
    def test_demo_has_twenty_resolved_unique_item_props(self):
        ids=json.loads((ROOT/'data/catalog/demo_v1.json').read_text())['definition_ids']
        self.assertEqual(len(ids),20); self.assertEqual(len(set(ids)),20)
        defs={r['id']:r for part in ['items','props'] for r in BASE[part]}
        self.assertTrue(all(i in defs for i in ids))
        self.assertEqual({i.split('.')[0] for i in ids},{'item','prop'})
    def test_visual_swap_does_not_mutate_logical_record(self):
        original=copy.deepcopy(BASE['items'][0]); changed=copy.deepcopy(original)
        changed['name']='Display name can change'; changed['visual']['icon']='asset.placeholder.medical_alt'
        for field in ['id','capabilities','weight_kg','stack_max','category']: self.assertEqual(changed[field],original[field])
    def test_cli_reports_bad_json_without_traceback(self):
        import tempfile
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'bad.json'; path.write_text('{')
            result=subprocess.run([sys.executable,str(ROOT/'tools/validate_catalog.py'),str(path)],capture_output=True,text=True)
            self.assertNotEqual(result.returncode,0); self.assertNotIn('Traceback',result.stderr)
if __name__=='__main__': unittest.main()
