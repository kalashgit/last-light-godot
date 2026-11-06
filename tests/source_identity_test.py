#!/usr/bin/env python3
"""Semantic gate regressions. Review fixtures confer no real approval."""
import copy
import hashlib
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import classify_sprite_sources as classifier
spec=importlib.util.spec_from_file_location('identity_factory',ROOT/'LAST_LIGHT_MASTER_SPRITE_FACTORY_V4.py')
f=importlib.util.module_from_spec(spec);sys.modules[spec.name]=f;spec.loader.exec_module(f)
HOME=ROOT/'production/source_identity'

class IdentityTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.ledger=[json.loads(x) for x in (HOME/'ledger.jsonl').read_text().splitlines()]
  cls.by_index={r['catalog_index']:r for r in cls.ledger}
  cls.gate=json.loads((HOME/'production_gate.json').read_text())
  cls.recipes={r['design']:r for r in f.demo_recipes()}

 def recipe(self,design,index,identity=None):
  r=copy.deepcopy(self.recipes[design]);s=self.by_index[index]
  r['source_reference_ids']=[s['reference_id']];r['canonical_item_id']=s['logical_item_id'] or 'item.technical.blocked'
  r['semantic_identity_key']=identity or design
  return r

 def test_all_4347_sources_accounted_once(self):
  self.assertEqual(len(self.ledger),4347)
  self.assertEqual(len({r['reference_id'] for r in self.ledger}),4347)
  self.assertEqual(sorted(self.by_index),list(range(1,4348)))
  self.assertTrue(all(r['disposition'] in classifier.DISPOSITIONS for r in self.ledger))

 def test_authoritative_source_records_are_preserved_field_for_field(self):
  original={r['reference_id']:r for r in classifier.inventory()}
  for row in self.ledger:
   self.assertEqual(row['authoritative_source_record'],original[row['reference_id']])
   for key in ['source_filename','source_page_url','source_image_url','source_catalog_page','source_metadata','reference_id','catalog_index']:
    self.assertEqual(row[key],original[row['reference_id']][key])

 def test_source_version_conflict_blocks_interpretation_without_renaming(self):
  row=self.by_index[18]
  self.assertEqual(row['source_filename'],'Amethyst Raw.png')
  self.assertEqual(row['classification_status'],'blocked_conflict')
  self.assertFalse(row['production_eligible'])

 def test_legacy_keywords_never_grant_identity_verification(self):
  for r in self.ledger:
   if r['classification_status']=='unverified':
    self.assertIsNone(r['logical_item_id']);self.assertFalse(r['production_eligible'])
    self.assertEqual(r['disposition'],'requires_human_classification')
  self.assertTrue(any(r.get('legacy_semantic_review',{}).get('reviewed') and not r['production_eligible'] for r in self.ledger))

 def test_complete_mass_classification_required(self):
  r=self.recipe('apple',38)
  with self.assertRaisesRegex(ValueError,'production paused'):f._v4_source_identity(r,self.gate)
  self.assertFalse(self.gate['catalog_review_complete']);self.assertFalse(self.gate['production_enabled'])

 def test_acorn_cannot_bind_to_apple_even_when_renamed(self):
  for design in ['apple','pear']:
   with self.subTest(design=design):
    with self.assertRaisesRegex(ValueError,'identity mismatch'):f._v4_source_identity(self.recipe(design,2),self.gate)

 def test_acorn_label_cannot_relabel_apple_pixels(self):
  with self.assertRaisesRegex(ValueError,'cannot render acorn'):f._v4_source_identity(self.recipe('apple',2,'acorn'),self.gate)

 def test_hunting_and_pocket_knives_cannot_bind_to_screwdrivers(self):
  for source in [1881,2136]:
   for design in ['flathead_screwdriver','phillips_screwdriver']:
    with self.subTest(source=source,design=design):
     with self.assertRaisesRegex(ValueError,'identity mismatch'):f._v4_source_identity(self.recipe(design,source),self.gate)

 def test_unspecified_screwdriver_tip_cannot_auto_become_flathead(self):
  with self.assertRaisesRegex(ValueError,'identity mismatch'):f._v4_source_identity(self.recipe('flathead_screwdriver',3188),self.gate)

 def test_source_ids_required_and_must_be_exact(self):
  r=copy.deepcopy(self.recipes['apple']);r['production_scope']='catalog_production'
  with self.assertRaisesRegex(ValueError,'exact source IDs'):f._v4_source_identity(r,self.gate)
  r['source_reference_ids']=['ll_golden_acorn']
  with self.assertRaisesRegex(ValueError,'Unverified source'):f._v4_source_identity(r,self.gate)

 def test_no_source_link_without_evidence_ledger(self):
  with self.assertRaisesRegex(ValueError,'classification required'):f._v4_source_identity(self.recipe('apple',38))

 def test_duplicate_and_string_source_ids_rejected(self):
  for value in ['pzwiki:catalog:2026-11-05:38',['x','x'],[None]]:
   r=copy.deepcopy(self.recipes['apple']);r['source_reference_ids']=value
   with self.assertRaisesRegex(ValueError,'distinct exact'):f._v4_source_identity(r,self.gate)

 def test_benchmarks_cannot_bypass_source_identity(self):
  with tempfile.TemporaryDirectory() as d:
   with self.assertRaisesRegex(ValueError,'classification required'):
    f.run_batch([self.recipe('apple',2)],d,limit=1,benchmark=True)
   self.assertFalse(list(Path(d).rglob('icon.png')))

 def test_no_visual_or_catalog_approval_for_unlinked_demo(self):
  m=f._v4_source_identity(self.recipes['apple'])
  self.assertEqual(m['scope'],'style_calibration_demo');self.assertEqual(m['catalog_records_covered'],0)
  self.assertFalse(m['production_eligible'])

 def test_technical_mask_is_not_respirator(self):
  r=self.by_index[8];self.assertEqual(r['identity_key'],'disinfectant_bottle_render_mask')
  self.assertEqual(r['disposition'],'unsupported_or_irrelevant');self.assertFalse(r['production_eligible'])

 def test_filtered_sources_and_states_not_generic_tape(self):
  self.assertEqual(self.by_index[5]['identity_key'],'respirator_filter_pair')
  self.assertEqual(self.by_index[6]['identity_key'],'respirator_filter_pair')
  self.assertEqual(self.by_index[5]['identity_review']['state'],'recharged')
  with self.assertRaisesRegex(ValueError,'identity mismatch'):f._v4_source_identity(self.recipe('duct_tape',5),self.gate)

 def test_old_wipes_are_not_expired_state(self):
  r=self.by_index[10];self.assertEqual(r['disposition'],'duplicate_reference')
  self.assertEqual(r['logical_item_id'],self.by_index[11]['logical_item_id'])
  self.assertEqual(r['identity_review']['state'],'intact')

 def test_foil_is_not_ingot_and_analog_clock_is_not_digital(self):
  self.assertEqual(self.by_index[16]['identity_key'],'aluminum_foil')
  self.assertEqual(self.by_index[7]['identity_key'],'analog_alarm_clock')

 def test_spoiled_apple_is_a_state_not_new_unique_item(self):
  self.assertEqual(self.by_index[38]['logical_item_id'],self.by_index[39]['logical_item_id'])
  self.assertEqual(self.by_index[39]['identity_review']['state'],'rotten')

 def test_changed_image_or_context_requires_reinspection(self):
  review=copy.deepcopy(self.by_index[2]['identity_review']);evidence=self.by_index[2]['evidence']
  for field in ['inspected_image_sha256','inspected_context_sha256']:
   changed=copy.deepcopy(review);changed[field]='0'*64
   with self.assertRaises(ValueError):classifier.validate_review(changed,self.by_index[2],evidence)

 def test_hash_or_keyword_alone_cannot_approve(self):
  r=copy.deepcopy(self.by_index[2]['identity_review']);r.pop('visual_observation')
  with self.assertRaisesRegex(ValueError,'visual observation'):classifier.validate_review(r,self.by_index[2],self.by_index[2]['evidence'])

 def test_relation_requires_explicit_target_and_evidence(self):
  r=copy.deepcopy(self.by_index[5]['identity_review']);r.pop('relationship_evidence')
  with self.assertRaisesRegex(ValueError,'explicit reviewed target'):classifier.validate_review(r,self.by_index[5],self.by_index[5]['evidence'])

 def test_valid_complete_fixture_allows_exact_apple_only(self):
  # A one-record isolated engineering fixture, not a claim the real catalog is complete.
  gate=copy.deepcopy(self.gate);ref=self.by_index[38]['reference_id']
  gate.update(total_reference_records=1,resolved_reference_records=1,catalog_review_complete=True,production_enabled=True,receipts={ref:gate['receipts'][ref]})
  self.assertEqual(f._v4_source_identity(self.recipe('apple',38),gate)['status'],'identity_verified')
  r=self.recipe('apple',38);r['canonical_item_id']='item.food.acorn'
  with self.assertRaisesRegex(ValueError,'canonical item ID'):f._v4_source_identity(r,gate)
  r=self.recipe('apple',38);r['state']='rotten'
  with self.assertRaisesRegex(ValueError,'state/view'):f._v4_source_identity(r,gate)
  r=self.recipe('apple',38);gate['receipts'][ref]['image_sha256']='bogus'
  with self.assertRaisesRegex(ValueError,'inspected image/context'):f._v4_source_identity(r,gate)

 def test_approved_24_template_and_export_hashes_unchanged(self):
  frozen=[json.loads(x) for x in (ROOT/'production/sprite_factory_v4/hybrid24/manifest.jsonl').read_text().splitlines()]
  for row in frozen:
   slug=row['logical_item_id'].split('.')[-1]
   png=f.base64.b64decode(f.AUTHORED_TEMPLATES[slug])
   self.assertEqual(hashlib.sha256(png).hexdigest(),f.AUTHORED_TEMPLATE_HASHES[slug])
   with tempfile.TemporaryDirectory() as d:
    path=Path(d)/'icon.png';f.render_icon(self.recipes[slug]).save(path,optimize=False)
    self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),row['sha256'],slug)

 def test_comparisons_never_bind_different_golden_objects(self):
  for name in ['hybrid24','final24']:
   path=ROOT/'production/sprite_factory_v4/reviews'/name
   mapping=json.loads((path/'comparison_map.json').read_text())
   self.assertEqual(len(mapping),24)
   for row in mapping:
    self.assertEqual(row['comparison_type'],'same_demo_identity')
    self.assertEqual(row['catalog_records_covered'],0)
    self.assertNotIn('golden_reference_id',row)
    self.assertEqual(len(row['paths']),2)
   self.assertFalse(list(path.glob('golden_v3_v4*.png')))

 def test_private_source_cache_cannot_write_game_assets(self):
  with self.assertRaisesRegex(ValueError,'outside the game repository'):classifier.fetch(classifier.CATALOG,ROOT/'assets/private_research',{2},1)
  with self.assertRaisesRegex(ValueError,'outside the game repository'):classifier.sheet(classifier.CATALOG,ROOT/'assets/private_research',1,20)

if __name__=='__main__':
 program=unittest.main(verbosity=2,exit=False)
 result=program.result
 report={'tests_run':result.testsRun,'passed':result.wasSuccessful(),'failures':[{ 'test':str(t),'traceback':s} for t,s in result.failures],'errors':[{ 'test':str(t),'traceback':s} for t,s in result.errors],'factory_sha256':hashlib.sha256((ROOT/'LAST_LIGHT_MASTER_SPRITE_FACTORY_V4.py').read_bytes()).hexdigest(),'purpose':'Source identity gates and unchanged visual processing; no production or device approval'}
 (HOME/'classification_test_report.json').write_text(json.dumps(report,indent=2)+'\n')
 sys.exit(0 if result.wasSuccessful() else 1)
