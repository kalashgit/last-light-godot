import importlib.util, pathlib, tempfile, json, os, unittest
spec=importlib.util.spec_from_file_location('factory','/mnt/data/LAST_LIGHT_MASTER_FACTORY_V2.py')
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
class Test(unittest.TestCase):
 def test_reference_id_and_source_fields(self):
  r=mod.Catalog.normalize({'index':347,'source_filename':'Screwdriver.png','reference_image_url':'https://pzwiki.net/a.png','source_file_page':'https://pzwiki.net/wiki/File:Screwdriver.png'})
  self.assertEqual(r['id'],'pzwiki.icon.000347')
  self.assertIn('Screwdriver',r['title'])
  self.assertEqual(r['source_url'],'https://pzwiki.net/wiki/File:Screwdriver.png')
 def test_import_4347_records_and_repeat(self):
  with tempfile.TemporaryDirectory() as td:
   root=pathlib.Path(td);sources=root/'imports'/'notion_item_icon_batches';sources.mkdir(parents=True)
   for chunk in range(23):
    records=[]
    begin=chunk*200+1 if chunk<2 else (401 if chunk==2 else 501 if chunk==3 else 601+(chunk-4)*200)
    count=100 if chunk in (2,3) else 147 if chunk==22 else 200
    for n in range(begin,begin+count):
     records.append({'index':n,'source_filename':f'item{n}.png','reference_image_url':f'https://example.org/research/{n}.png','source_file_page':f'https://example.org/reference/{n}','rights':'research_only'})
    (sources/f'batch_{chunk+1:02d}.jsonl').write_text('\n'.join(json.dumps(x) for x in records)+'\n')
   catalog=mod.Catalog(root/'db.sqlite3')
   results=catalog.import_dir(root/'imports');self.assertEqual(results['records_accepted'],4347,results)
   reconcile=mod.reconcile_item_icons(catalog,root)
   self.assertTrue(reconcile['full_reference_coverage'],reconcile)
   results2=catalog.import_dir(root/'imports');self.assertEqual(results2['records_accepted'],4347)
   self.assertEqual(catalog.report()['total_unique_records'],4347)
   catalog.close()
 def test_missing_index_reconciliation(self):
  with tempfile.TemporaryDirectory() as td:
   root=pathlib.Path(td);catalog=mod.Catalog(root/'db.sqlite3')
   catalog.upsert({'index':1,'source_filename':'A.png'})
   result=mod.reconcile_item_icons(catalog,root)
   self.assertEqual(len(result['missing_indices']),4346)
   catalog.close()
 def test_neighborhood_stable_and_3_distinct_layouts(self):
  with tempfile.TemporaryDirectory() as td:
   root=pathlib.Path(td);a=mod.produce_neighborhood(root,20261106)
   raw=(root/'godot_export/data/generated/neighborhood_v2.json').read_bytes()
   b=mod.produce_neighborhood(root,20261106)
   self.assertEqual(raw,(root/'godot_export/data/generated/neighborhood_v2.json').read_bytes())
   self.assertEqual(a['sha256'],b['sha256'])
   data=json.loads(raw);self.assertEqual(len(data['buildings']),3)
   self.assertEqual(sum(len(x['rooms']) for x in data['buildings']),12)
   self.assertEqual(len({tuple(x['footprint'][2:])+(x['roof'],) for x in data['buildings']}),3)
   b2=mod.produce_neighborhood(root,13579)
   self.assertNotEqual(a['sha256'],b2['sha256'])
 def test_zip_integrity(self):
  with tempfile.TemporaryDirectory() as td:
   root=pathlib.Path(td);mod.produce_neighborhood(root,1)
   paths=mod.zip_outputs(root,'neighborhood')
   self.assertTrue(paths)
   import zipfile
   for p in paths:
    with zipfile.ZipFile(p) as z:self.assertIsNone(z.testzip())

if __name__=='__main__':unittest.main(verbosity=2)