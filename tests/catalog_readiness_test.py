#!/usr/bin/env python3
"""Official identity binding and phone snapshot regression tests; no visual approval."""
import copy,hashlib,importlib.util,json,sqlite3,sys,tempfile,unittest
from pathlib import Path
from unittest import mock
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
import audit_sprite_catalog as a
spec=importlib.util.spec_from_file_location('phone_catalog_checker',ROOT/'LAST_LIGHT_CATALOG_CHECKS.py');phone=importlib.util.module_from_spec(spec);spec.loader.exec_module(phone)

def page(text,title='Acorn',pageid=2):return {'title':title,'pageid':pageid,'revisions':[{'revid':123,'timestamp':'2026-11-06T00:00:00Z','slots':{'main':{'content':text}}}]}
def box(icon='Acorn.png',name='Acorn',ids='|item_id=Base.Acorn'):
 return '{{Infobox item\n|name='+name+'\n|icon='+icon+'\n|category={{ll|Food}} / {{ll|Material}}\n'+ids+'\n}}'

class BindingTests(unittest.TestCase):
 def test_exact_icon_source_name_and_id(self):
  b=a.article_bindings(page(box()))[0]
  self.assertEqual(b['source_item_ids'],['Base.Acorn']);self.assertEqual(b['official_item_name'],'Acorn')
  self.assertEqual(b['icon_filename'],'Acorn.png');self.assertEqual(b['facts']['category'],'Food / Material')
 def test_recipe_and_history_illustrations_do_not_establish_identity(self):
  b=a.article_bindings(page(box('Apple.png','Apple','|item_id=Base.Apple')+'\n[[File:Acorn.png]]\n{{Recipe|icon=Acorn.png}}'))
  self.assertEqual([x['match_key'] for x in b],['Apple.png'])
 def test_no_infobox_no_binding(self):self.assertEqual(a.article_bindings(page('[[File:Acorn.png]] Acorn appears here.')),[])
 def test_spaces_underscores_are_mediawiki_aliases(self):self.assertEqual(a.filename_key('AirFilters_Tape.png'),a.filename_key('AirFilters Tape.png'))
 def test_different_objects_and_case_after_first_letter_stay_distinct(self):
  self.assertNotEqual(a.filename_key('Acorn.png'),a.filename_key('Apple.png'))
  self.assertNotEqual(a.filename_key('Knife.png'),a.filename_key('Screwdriver.png'))
  self.assertNotEqual(a.filename_key('RedBag.png'),a.filename_key('Redbag.png'))
 def test_nested_infobox_parameters_are_not_split(self):
  b=a.article_bindings(page(box()+ '\n{{Else|item_id=Base.Apple|icon=Apple.png}}'))
  self.assertEqual(len(b),1);self.assertEqual(b[0]['source_item_ids'],['Base.Acorn'])
 def test_multiple_ids_are_not_assigned_by_numeric_position(self):
  b=a.article_bindings(page(box(ids='|item_id=Base.Acorn\n|item_id2=Base.Apple')))[0]
  self.assertEqual(b['source_item_ids'],['Base.Acorn','Base.Apple'])
 def test_exact_script_icon_disambiguates_item_ids(self):
  text=box('RedBag.png','Bag','|item_id=Base.RedBag\n|item_id2=Base.BlueBag')+'\nitem RedBag {\n Icon = RedBag,\n}\nitem BlueBag {\n Icon = BlueBag,\n}'
  b=a.article_bindings(page(text))[0];self.assertEqual(b['source_item_ids'],['Base.RedBag']);self.assertEqual(b['all_infobox_item_ids'],['Base.BlueBag','Base.RedBag'])
 def test_script_cannot_invent_an_unlisted_item_id(self):
  b=a.article_bindings(page(box()+'\nitem Fake {\n Icon = Acorn,\n}'))[0];self.assertEqual(b['script_icon_item_ids'],[])
 def test_missing_and_unbalanced_infobox_not_approved(self):
  self.assertEqual(a.article_bindings(page('{{Infobox item|name=Acorn|icon=Acorn.png')),[])
 def test_dynamic_icon_values_not_resolved_by_guess(self):
  self.assertEqual(a.article_bindings(page(box('{{Something|Acorn.png}}'))),[])

class SourceCacheTests(unittest.TestCase):
 def test_corrupt_cache_recovers_and_valid_cache_resumes_without_network(self):
  import io
  from PIL import Image
  with tempfile.TemporaryDirectory() as d:
   root=Path(d)/'fixture';folder=root/'production/sprite_factory';folder.mkdir(parents=True)
   source={'reference_id':'fixture:1','catalog_index':1,'source_filename':'Fixture.png','source_image_url':'https://example.invalid/Fixture.png'}
   (folder/'catalog.json').write_text(json.dumps({'rows':[source]}))
   cache=Path(d)/'cache';cache.mkdir()
   png=io.BytesIO();Image.new('RGBA',(32,32),(255,0,0,255)).save(png,format='PNG');data=png.getvalue()
   with mock.patch.object(a,'ROOT',root),mock.patch.object(a,'CACHE',cache),mock.patch('builtins.print'):
    with mock.patch.object(a.urllib.request,'urlopen',side_effect=lambda *args,**kw:io.BytesIO(data)) as network:
     self.assertEqual(a.fetch_images()[0]['status'],'decoded_source_image')
     (cache/'images/1.json').write_text('broken metadata')
     self.assertEqual(a.fetch_images()[0]['status'],'decoded_source_image')
     (cache/'images/1.png').write_bytes(b'corrupt PNG')
     self.assertEqual(a.fetch_images()[0]['status'],'decoded_source_image')
     self.assertEqual(network.call_count,3)
    with mock.patch.object(a.urllib.request,'urlopen',side_effect=AssertionError('Valid cached image must not refetch')):
     self.assertEqual(a.fetch_images()[0]['sha256'],hashlib.sha256(data).hexdigest())

class FullCatalogTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.rows=[json.loads(x) for x in (ROOT/'production/catalog_readiness/readiness_manifest.jsonl').read_text().splitlines()]
  cls.source=json.loads((ROOT/'production/sprite_factory/catalog.json').read_text())['rows']
 def test_all_records_and_original_source_fields_preserved(self):
  self.assertEqual(len(self.rows),4347);self.assertEqual([r['catalog_index'] for r in self.rows],list(range(1,4348)))
  self.assertEqual(len({r['reference_id'] for r in self.rows}),4347)
  self.assertEqual([r['authoritative_source_record'] for r in self.rows],self.source)
 def test_all_images_really_decoded_and_hashes_recorded(self):
  for row in self.rows:
   image=row['image_check'];self.assertEqual(image['status'],'decoded_source_image')
   self.assertEqual(len(image['sha256']),64);self.assertEqual(len(image['pixel_sha256']),64)
   self.assertGreater(image['width'],0);self.assertGreater(image['height'],0)
 def test_metadata_never_grants_art_approval_or_generation(self):
  self.assertTrue(all(not r['actual_visual_approval'] and not r['factory_render_ready'] and not r['new_art_generated'] for r in self.rows))
 def test_acorn_and_apple_bound_independently(self):
  self.assertEqual(self.rows[1]['official_bindings'][0]['source_item_ids'],['Base.Acorn'])
  self.assertEqual(self.rows[37]['official_bindings'][0]['source_item_ids'],['Base.Apple'])
 def test_shared_hunting_knife_bayonet_icon_is_blocked(self):
  r=self.rows[1880];self.assertIn('icon_shared_by_multiple_official_item_articles',r['blocking_reasons']);self.assertFalse(r['ready_for_brief_draft'])
 def test_render_mask_never_invented_as_respirator(self):
  r=self.rows[7];self.assertEqual(r['official_icon_filename'],'Alcohol Mask.png');self.assertFalse(r['ready_for_brief_draft'])
 def test_raw_amethyst_original_name_and_conflict_retained(self):
  r=self.rows[17];self.assertEqual(r['official_icon_filename'],'Amethyst Raw.png');self.assertIn('icon_shared_by_multiple_official_item_articles',r['blocking_reasons'])
 def test_screwdriver_binding_is_tool_not_knife(self):
  self.assertEqual({b['official_item_name'] for b in self.rows[3187]['official_bindings']},{'Screwdriver'})
 def test_dimension_disagreement_blocks_without_faking_corruption(self):
  r=self.rows[998];self.assertEqual(r['image_check']['status'],'decoded_source_image')
  self.assertIn('served_image_dimensions_disagree_with_official_record',r['blocking_reasons'])
 def test_draft_queue_matches_only_unambiguous_sources(self):
  d=[json.loads(x) for x in (ROOT/'production/catalog_readiness/identity_bound_brief_drafts.jsonl').read_text().splitlines()]
  self.assertEqual({r['source_reference_id'] for r in d},{r['reference_id'] for r in self.rows if r['ready_for_brief_draft']})
  self.assertTrue(all(not r['factory_render_ready'] and not r['source_pixels_may_be_used_as_art'] for r in d))
 def test_218_batches_cover_every_source_once(self):
  batches=json.loads((ROOT/'production/catalog_readiness/batches.json').read_text());ids=[i for b in batches for i in b['reference_ids']]
  self.assertEqual(len(batches),218);self.assertEqual(len(ids),4347);self.assertEqual(len(set(ids)),4347)
 def test_approved_factory_source_is_byte_unchanged(self):
  expected=json.loads((ROOT/'production/source_identity/change_evidence.json').read_text())['factory_sha256']
  self.assertEqual(hashlib.sha256((ROOT/'LAST_LIGHT_MASTER_SPRITE_FACTORY_V4.py').read_bytes()).hexdigest(),expected)

class PhoneCheckerTests(unittest.TestCase):
 def test_embedded_snapshot_bytes_match_full_manifest(self):
  self.assertEqual(hashlib.sha256(b''.join(x+b'\n' for x in phone.lines())).hexdigest(),phone.SNAPSHOT_SHA256)
  self.assertEqual(phone.SNAPSHOT_SHA256,hashlib.sha256((ROOT/'production/catalog_readiness/readiness_manifest.jsonl').read_bytes()).hexdigest())
 def test_interruption_resume_corruption_recovery_and_atomic_export(self):
  with tempfile.TemporaryDirectory() as d:
   with mock.patch('builtins.print'):
    r=phone.run(d,stop_after=17);self.assertTrue(r['interrupted'])
    self.assertFalse((Path(d)/'source_readiness.jsonl').exists())
    r=phone.run(d);self.assertEqual(r['resumed'],17);self.assertEqual(r['checked'],4347)
    (Path(d)/'source_readiness.jsonl').write_text('corrupt export')
    db=sqlite3.connect(str(Path(d)/'source_checks.sqlite3'));db.execute("UPDATE records SET record_json='corrupt' WHERE catalog_index=2");db.commit();db.close()
    r=phone.run(d);self.assertEqual(r['resumed'],4346);self.assertEqual(r['sprites_generated'],0)
   self.assertEqual(hashlib.sha256((Path(d)/'source_readiness.jsonl').read_bytes()).hexdigest(),phone.SNAPSHOT_SHA256)

if __name__=='__main__':
 program=unittest.main(verbosity=2,exit=False);result=program.result
 report={'tests_run':result.testsRun,'passed':result.wasSuccessful(),'failures':[{'test':str(t),'traceback':s} for t,s in result.failures],'errors':[{'test':str(t),'traceback':s} for t,s in result.errors],'checker_sha256':hashlib.sha256((ROOT/'LAST_LIGHT_CATALOG_CHECKS.py').read_bytes()).hexdigest(),'snapshot_sha256':phone.SNAPSHOT_SHA256,'iphone_execution_of_new_checker_verified':False}
 (ROOT/'production/catalog_readiness/test_report.json').write_text(json.dumps(report,indent=2)+'\n')
 sys.exit(0 if result.wasSuccessful() else 1)
