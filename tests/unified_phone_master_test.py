#!/usr/bin/env python3
import copy,hashlib,importlib.util,json,sys,tempfile,unittest
from pathlib import Path
from unittest import mock
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('unified_master',ROOT/'LAST_LIGHT_MASTER.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class UnifiedMasterTests(unittest.TestCase):
 def test_embedded_components_match_unchanged_original_files(self):
  for filename,expected in [('LAST_LIGHT_MASTER_SPRITE_FACTORY_V4.py',m.RENDERER_SHA256),('LAST_LIGHT_CATALOG_CHECKS.py',m.CATALOG_CHECKER_SHA256)]:
   self.assertEqual(hashlib.sha256((ROOT/filename).read_bytes()).hexdigest(),expected)
 def test_2725_remaining_queued_briefs_remain_exact_source_linked_not_render_recipes(self):
  rows=[json.loads(x) for x in m.brief_lines(m.checker())]
  self.assertEqual(len(rows),2725);self.assertEqual(len({r['source_reference_ids'][0] for r in rows}),2725)
  self.assertTrue(all(r['status']=='needs_original_art_recipe' and not r['factory_render_ready'] for r in rows))
  self.assertTrue(all(r['official_source_filename'] and r['official_item_ids'] for r in rows))
 def test_modified_queue_is_preserved_as_versioned_export(self):
  with tempfile.TemporaryDirectory() as d:
   path=Path(m.durable_export(d,'queue.jsonl',['original']));path.write_text('user edits')
   new=Path(m.durable_export(d,'queue.jsonl',['original']))
   self.assertNotEqual(path,new);self.assertEqual(path.read_text(),'user edits');self.assertEqual(new.read_text(),'original\n')
 def test_no_new_designs_inferred_from_test_or_reference_counts(self):
  with tempfile.TemporaryDirectory() as d,mock.patch('builtins.print'):
   result=m.run(d,action='catalog_only')
   self.assertEqual(result['new_catalog_sprites_generated'],0)
   self.assertEqual(result['completed_designs_available'],44)
   self.assertEqual(result['new_catalog_render_ready_records'],0)
   self.assertEqual(result['source_briefs_requiring_original_art_recipes'],2725)
 def test_default_run_and_resume_reproduce_all_24_prior_export_hashes(self):
  expected={r['logical_item_id']:r['sha256'] for r in (json.loads(x) for x in (ROOT/'production/sprite_factory_v4/hybrid24/manifest.jsonl').read_text().splitlines())}
  with tempfile.TemporaryDirectory() as d,mock.patch('builtins.print'):
   first=m.run(d);second=m.run(d)
   self.assertEqual(first['demo_or_recipe_result']['generated'],24);self.assertEqual(first['demo_or_recipe_result']['failed'],0)
   self.assertEqual(second['demo_or_recipe_result']['generated'],0);self.assertEqual(second['demo_or_recipe_result']['resumed'],24)
   rows=[json.loads(x) for x in (Path(d)/'approved_style_demo/manifest.jsonl').read_text().splitlines()]
   self.assertEqual({r['logical_item_id']:r['sha256'] for r in rows},expected)
 def test_combined_file_runs_without_neighbor_source_files(self):
  with tempfile.TemporaryDirectory() as d,mock.patch('builtins.print'):
   p=Path(d)/'standalone.py';p.write_bytes((ROOT/'LAST_LIGHT_MASTER.py').read_bytes())
   namespace={'__name__':'standalone_fixture','__file__':str(p)}
   exec(compile(p.read_bytes(),str(p),'exec'),namespace)
   result=namespace['run'](str(Path(d)/'output'),action='demo_only')
   self.assertEqual(result['demo_or_recipe_result']['png_files'],24)
 def test_catalog_rendering_cannot_take_source_less_or_unsupported_recipes(self):
  with tempfile.TemporaryDirectory() as d,mock.patch('builtins.print'):
   p=Path(d)/'recipes.jsonl';p.write_text(json.dumps(m.renderer().demo_recipes()[0])+'\n')
   with self.assertRaisesRegex(ValueError,'exact source IDs'):m.run(d,action='render_recipes',recipes=str(p))
   self.assertFalse(list((Path(d)/'catalog_candidates').rglob('icon.png')))
 def test_new_20_candidates_export_resume_repair_and_identity_binding(self):
  master=m.renderer();pack=m.catalog_art_pack();runner=m.catalog_art_runtime()
  self.assertEqual(len(pack['assets']),20)
  self.assertEqual({a['record']['catalog_index'] for a in pack['assets']},{25,26,29,32,33,34,37,40,41,45,55,58,63,76,78,81,82,83,89,94})
  with tempfile.TemporaryDirectory() as d,mock.patch('builtins.print'):
   first=runner.export(pack,d,master);second=runner.export(pack,d,master)
   self.assertEqual(first['new_catalog_sprites_generated'],20);self.assertEqual(second['resumed'],20)
   self.assertEqual(first['technical_qa_passes'],20);self.assertEqual(first['founder_approvals'],0)
   records=[json.loads(x) for x in Path(first['manifest_path']).read_text().splitlines()]
   folder=Path(first['manifest_path']).parent
   damaged=folder/records[0]['relative_path'];damaged.write_bytes(b'corrupt candidate')
   recovered=runner.export(pack,d,master);self.assertEqual(recovered['new_catalog_sprites_generated'],1)
   self.assertEqual(hashlib.sha256(damaged.read_bytes()).hexdigest(),records[0]['sha256'])
   changed=copy.deepcopy(pack);changed['assets'][0]['png']=changed['assets'][1]['png']
   with self.assertRaisesRegex(ValueError,'hash mismatch'):runner.export(changed,d,master)
   changed=copy.deepcopy(pack);changed['assets'][1]['record']['reference_id']=changed['assets'][0]['record']['reference_id']
   with self.assertRaisesRegex(ValueError,'Duplicate catalog identity'):runner.export(changed,d,master)

 def test_catalog_recipe_missing_path_is_actionable(self):
  with self.assertRaisesRegex(ValueError,'finished original-art recipes'):m.run(action='render_recipes')
 def test_acorn_cannot_be_replaced_by_embedded_apple(self):
  f=m.renderer();r=copy.deepcopy(next(r for r in f.demo_recipes() if r['design']=='apple'));r['semantic_identity_key']='acorn'
  with self.assertRaisesRegex(ValueError,'cannot render acorn'):f._v4_source_identity(r)
if __name__=='__main__':
 program=unittest.main(verbosity=2,exit=False);result=program.result
 report={'tests_run':result.testsRun,'passed':result.wasSuccessful(),'failures':[{'test':str(t),'traceback':s} for t,s in result.failures],'errors':[{'test':str(t),'traceback':s} for t,s in result.errors],'master_sha256':hashlib.sha256((ROOT/'LAST_LIGHT_MASTER.py').read_bytes()).hexdigest(),'renderer_sha256':m.RENDERER_SHA256,'iphone_execution_of_combined_file_verified':False}
 (ROOT/'production/unified_master/test_report.json').write_text(json.dumps(report,indent=2)+'\n')
 sys.exit(0 if result.wasSuccessful() else 1)
