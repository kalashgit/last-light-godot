import importlib.util, tempfile, pathlib, json, hashlib, shutil, sqlite3, zipfile, time, unittest
HERE=pathlib.Path(__file__).resolve().parent
SOURCE=next((q for q in (HERE/'LAST_LIGHT_MASTER_FACTORY_V3_RECONCILE_AND_CREATE.py', HERE.parent/'tools'/'LAST_LIGHT_MASTER_FACTORY_V3_RECONCILE_AND_CREATE.py', pathlib.Path('/mnt/data/LAST_LIGHT_MASTER_FACTORY_V3_RECONCILE_AND_CREATE.py')) if q.exists()), None)
if SOURCE is None: raise RuntimeError('Place V3 master script next to the tests, or at tools/ within the repository')
spec=importlib.util.spec_from_file_location('llv3',str(SOURCE))
v3=importlib.util.module_from_spec(spec);spec.loader.exec_module(v3)

class V3FactoryTests(unittest.TestCase):
 def mk(self,root,full=False):
  c=v3.Catalog(root/'database'/'production.sqlite3')
  size=4347 if full else 5
  for n in range(1,size+1):
   fn= ('AliceBag Camo.png' if n==1 else 'AliceBag SandCamo.png' if n==2 else 'Acorn.png' if n==3 else f'SampleItem{n}.png')
   c.upsert({'index':n,'source_filename':fn,'source_file_page':f'https://example.org/File:{fn}','reference_image_url':f'https://example.org/source/{n}.png','kind':'item','rights':'research_only','source_collection':'pzwiki_item_icons'})
   c.db.execute('INSERT INTO classifications (source_id,source_index,original_filename,proposed_category,family_candidate,variant_clues,confidence,notion_page,review_state,metadata_json) VALUES(?,?,?,?,?,?,?,?,?,?)',(
    f'pzwiki.icon.{n:06d}',n,fn,'Food & cooking' if n==3 else 'Needs review / unclassified' if n%7==0 else 'Containers & storage',fn.replace('.png',''),'none','keyword-provisional','https://example.org/notion','keyword_provisional','{}'))
  for n in range(1640 if full else 3):
   family=['animal_images','tile_images','animated_images','vehicle_models'][n%4]
   c.upsert({'id':f'pzwiki.media.{family}.{n:06d}', 'name':f'Gallery {n}.png','kind':'image','category':family,'source_collection':'pzwiki_'+family,'provenance':'external_reference','rights':'research_only'})
  for n in range(60 if full else 2):
   c.upsert({'id':f'll.archetype.house_test_{n:02d}','name':f'House test {n}', 'kind':'building','category':'Residential','source_collection':'notion_original_buildings','rights':'original','provenance':'original_internal','approved_original_recipe':False})
  c.db.commit();return c
 def test_empty_catalog_requires_sync(self):
  with tempfile.TemporaryDirectory() as t:
   root=pathlib.Path(t);c=v3.Catalog(root/'database/production.sqlite3')
   with self.assertRaisesRegex(ValueError,'sync_catalog'):
    v3.v3_reconcile_and_generate(c,root,2026,8)
   c.close()
 def test_full_6047_catalog_and_queue(self):
  with tempfile.TemporaryDirectory() as t:
   root=pathlib.Path(t);c=self.mk(root,True)
   before=c.db.execute('SELECT COUNT(*),SUM(approved) FROM sources').fetchone()
   self.assertEqual(before[0],6047)
   a=v3.v3_reconcile_and_generate(c,root,20261106,32)
   self.assertEqual(a['reconciliation']['total_source_records'],6047)
   self.assertEqual(a['reconciliation']['indexed_item_icons'],4347)
   self.assertEqual(a['reconciliation']['provisional_classification_rows'],4347)
   self.assertEqual(a['reconciliation']['proposed_building_recipes'],60)
   self.assertEqual(a['reconciliation']['flags']['icon_missing'],0)
   self.assertEqual(a['art']['icons_generated'],32)
   self.assertEqual(a['art']['texture_samples'],10)
   self.assertEqual(a['art']['vegetation_candidates'],8)
   self.assertEqual(a['art']['environmental_effect_frames'],16)
   self.assertEqual(a['art']['duplicate_icon_binary_hashes'],0)
   self.assertEqual(a['art']['failure_count'],0)
   self.assertFalse(a['art']['golden_40_approved'])
   self.assertEqual(c.db.execute('SELECT COUNT(*),SUM(approved) FROM sources').fetchone(),before)
   self.assertEqual(c.db.execute('SELECT COUNT(*) FROM outputs').fetchone()[0],0)
   with zipfile.ZipFile(a['export_zip']) as z:
    self.assertIsNone(z.testzip())
    self.assertGreaterEqual(len(z.namelist()),52)
   lines=(root/'reports/reconciliation_v3/production_queue.jsonl').read_text().splitlines()
   self.assertEqual(len(lines),6047)
   self.assertTrue(all(json.loads(x)['renderer_available_for_this_source'] is False for x in lines))
   sheet=root/'review/v3_original_icon_contact_sheet.png'
   self.assertTrue(sheet.is_file())
   self.assertGreater(sheet.stat().st_size,5000)
   digest1=hashlib.sha256(pathlib.Path(a['export_zip']).read_bytes()).hexdigest()
   b=v3.v3_reconcile_and_generate(c,root,20261106,32)
   digest2=hashlib.sha256(pathlib.Path(b['export_zip']).read_bytes()).hexdigest()
   self.assertEqual(digest1,digest2)
   self.assertEqual(b['reconciliation']['total_source_records'],6047)
   c.close()
 def test_heuristic_does_not_merge_disparate_types(self):
  f,variants,_=v3.v3_family_hint('AliceBag Camo.png')
  self.assertEqual(f,'alice_bag');self.assertEqual(variants,['camo'])
  f2,variants2,_=v3.v3_family_hint('AliceBag SandCamo.png')
  self.assertEqual(f2,'alice_bag');self.assertEqual(variants2,['sandcamo'])
  self.assertNotEqual(v3.v3_family_hint('AlcoholWipes.png')[0],v3.v3_family_hint('Alcohol_Mask.png')[0])
 def test_no_external_source_pixels_used(self):
  with tempfile.TemporaryDirectory() as t:
   root=pathlib.Path(t);c=self.mk(root)
   result=v3.v3_reconcile_and_generate(c,root,6,2)
   manifest=json.loads((root/'manifests/v3_art_candidate_manifest.json').read_text())
   self.assertTrue(all(o['source_reference_image_copied'] is False for o in manifest['icons']))
   self.assertEqual(manifest['asset_approval'],'none_automatically_approved')
   c.close()
 def test_legacy_seed_compatibility(self):
  expected='ll-ucf-master-2.1-ios-ca'
  self.assertEqual(v3.SEED_NAMESPACE,expected)
  self.assertNotEqual(v3.VERSION,expected)
 def test_no_pillow_metadata_survives(self):
  with tempfile.TemporaryDirectory() as t:
   root=pathlib.Path(t);c=self.mk(root)
   orig=v3.optional_pillow
   try:
    v3.optional_pillow=lambda:(None,None)
    result=v3.v3_reconcile_and_generate(c,root,123,2)
   finally:v3.optional_pillow=orig
   self.assertEqual(result['art']['status'],'blocked_missing_pillow')
   self.assertEqual(result['reconciliation']['total_source_records'],10)
   c.close()

if __name__=='__main__': unittest.main(verbosity=2)