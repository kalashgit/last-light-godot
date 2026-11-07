import copy,importlib.util,json,unittest,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('validator',ROOT/'tools/world_art/validate.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
class WorldArtTests(unittest.TestCase):
 def setUp(self):self.doc=json.loads((ROOT/'data/world_art_manifest.json').read_text())
 def world(self):return next(r for r in self.doc['assets'] if r.get('world_sprite_path'))
 def test_current_contract_validates(self):self.assertEqual(v.validate(self.doc),[])
 def test_duplicate_ids_rejected(self):self.doc['assets'].append(copy.deepcopy(self.doc['assets'][0]));self.assertTrue(v.validate(self.doc))
 def test_inventory_icon_world_substitution_rejected(self):self.world()['world_sprite_path']='assets/last_light/golden40/objects/acorn/64.png';self.assertTrue(v.validate(self.doc))
 def test_contact_anchor_offset_rejected(self):self.world()['anchor_px'][0]+=1;self.assertTrue(v.validate(self.doc))
 def test_negative_dimensions_rejected(self):self.world()['dimensions_m'][0]=-1;self.assertTrue(v.validate(self.doc))
 def test_wrong_projection_rejected(self):self.doc['projection']['tile_px']=[40,20];self.assertTrue(v.validate(self.doc))
 def test_magnification_applied_once(self):self.doc['projection']['world_zoom_applications']=2;self.assertTrue(v.validate(self.doc))
 def test_unsupported_facing_rejected(self):self.world()['facing']='unavailable_90';self.assertTrue(v.validate(self.doc))
 def test_source_hash_change_rejected(self):self.world()['sha256']='0'*64;self.assertTrue(v.validate(self.doc))
 def test_marker_cannot_become_billboard(self):next(r for r in self.doc['assets'] if r['definition_id']=='ll_golden_acorn')['marker_radius_px']=20;self.assertTrue(v.validate(self.doc))
 def test_all_golden_ids_retained_without_world_art(self):
  old=json.loads((ROOT/'data/golden40_items.json').read_text())['items'];records={r['definition_id']:r for r in self.doc['assets']}
  self.assertEqual(len(old),40)
  for r in old:self.assertIsNone(records[r['id']]['world_sprite_path'])
 def test_support_bindings_inside_actual_footprints(self):
  layout=json.loads((ROOT/'data/house_layout.json').read_text());items={i['id']:i for i in layout['furniture']}
  for b in self.doc['decoration_supports']:
   if b['parent_support']:
    item=items[b['parent_support']];prop=layout['decorations'][b['decoration_index']]
    for axis in (0,1):self.assertLessEqual(item['pos'][axis],prop['pos'][axis]);self.assertLessEqual(prop['pos'][axis],item['pos'][axis]+item['size'][axis])
 def test_manifest_build_is_idempotent(self):
  path=ROOT/'data/world_art_manifest.json';before=path.read_bytes();subprocess.run([sys.executable,str(ROOT/'tools/world_art/build_manifest.py')],check=True,capture_output=True);self.assertEqual(before,path.read_bytes())
if __name__=='__main__':unittest.main()
