#!/usr/bin/env python3
"""Failure-focused export, provenance, resumption and promotion tests."""
import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('factory',ROOT/'tools/sprite_factory/factory.py')
f=importlib.util.module_from_spec(spec);spec.loader.exec_module(f)

class FactoryTests(unittest.TestCase):
 def setUp(self):
  self.manifest=f.read(ROOT/'production/sprite_factory/batches/LL-ICON-B0003/active.json')
 def bad(self, mutation, expected):
  m=copy.deepcopy(self.manifest);mutation(m)
  self.assertIn(expected,'\n'.join(f.validate_manifest(m)['errors']))
 def test_real_exports(self):self.assertEqual(f.validate_manifest(self.manifest)['errors'],[])
 def test_empty_manifest(self):self.bad(lambda m:m.update(items=[]),'no exports')
 def test_duplicate_logical_id(self):self.bad(lambda m:m['items'].append(copy.deepcopy(m['items'][0])),'duplicate logical_item_id')
 def test_conflicting_export_path(self):self.bad(lambda m:m['items'][1].update(export_path=m['items'][0]['export_path']),'duplicate export_path')
 def test_wrong_hash(self):self.bad(lambda m:m['items'][0].update(content_sha256='0'*64),'hash mismatch')
 def test_missing_source(self):self.bad(lambda m:m['items'][0].update(source_path='missing.png'),'broken source_path')
 def test_unknown_reference(self):self.bad(lambda m:m['items'][0].update(reference_ids=['pzwiki:invented']),'broken source reference')
 def test_wrong_anchor(self):self.bad(lambda m:m['items'][0].update(anchor=[128,192]),'invalid inventory anchor')
 def test_missing_state(self):self.bad(lambda m:m['items'][0].update(required_states=['sealed','open']),'required state/view missing')
 def test_world_view_not_faked(self):self.bad(lambda m:m['items'][0].update(required_views=['inventory_icon','ground_loot']),'required state/view missing')
 def test_metadata_required(self):self.bad(lambda m:m['items'][0].pop('generator'),'missing required metadata')
 def png_case(self,mode,size,fill,expected):
  with tempfile.TemporaryDirectory(dir=ROOT/'production') as d:
   p=Path(d)/'bad.png';Image.new(mode,size,fill).save(p)
   self.bad(lambda m:m['items'][0].update(export_path=str(p.relative_to(ROOT)),content_sha256=f.digest(p)),expected)
 def test_rgb_rejected(self):self.png_case('RGB',(64,64),'red','invalid PNG, alpha or dimensions')
 def test_wrong_dimensions(self):self.png_case('RGBA',(48,64),'red','invalid PNG, alpha or dimensions')
 def test_opaque_background(self):self.png_case('RGBA',(64,64),'red','background')
 def test_empty_sprite(self):self.png_case('RGBA',(64,64),(0,0,0,0),'nearly empty')
 def test_corrupt_png(self):
  with tempfile.TemporaryDirectory(dir=ROOT/'production') as d:
   p=Path(d)/'bad.png';p.write_text('not a png')
   self.bad(lambda m:m['items'][0].update(export_path=str(p.relative_to(ROOT)),content_sha256=f.digest(p)),'cannot identify image')
 def test_review_hash_binding(self):
  with tempfile.TemporaryDirectory(dir=ROOT/'production') as d:
   p=Path(d)/'decision.json';x=self.manifest['items'][0]
   f.write(p,dict(reviewer='fixture',reviewer_type='engineer_visual_inspection',evidence=['fixture'],items=[dict(asset_id=x['asset_id'],content_sha256='wrong')]))
   with self.assertRaisesRegex(ValueError,'exact inspected bytes'):f.review('LL-ICON-B0003','v001',p)
 def test_no_auto_promotion(self):
  with tempfile.TemporaryDirectory(dir=ROOT/'production') as d:
   p=Path(d)/'approval.json';f.write(p,{'approval_type':'automated'})
   before=f.digest(f.BASE/'approved_registry.json')
   with self.assertRaisesRegex(ValueError,'founder approval'):f.promote('LL-ICON-B0003','active',p)
   self.assertEqual(before,f.digest(f.BASE/'approved_registry.json'))
 def test_revision_resume_no_overwrite(self):
  p=f.BASE/'batches/LL-ICON-B0003/v001.json';before=f.digest(p)
  f.extract('LL-ICON-B0003','v001');self.assertEqual(before,f.digest(p))
 def test_catalog_resume_preserves_curation(self):
  before=f.digest(f.BASE/'catalog.json');f.intake(f.BASE/'source_catalog.json')
  self.assertEqual(before,f.digest(f.BASE/'catalog.json'))
 def test_retry_limit(self):
  with tempfile.TemporaryDirectory() as d,patch.object(f,'BASE',Path(d)):
   for n in range(3):f.rework('LL-ICON-B9999','fixture','defect','cause','targeted change')
   with self.assertRaisesRegex(ValueError,'retry limit'):f.rework('LL-ICON-B9999','fixture','defect','cause','change')
 def test_provenance_prompt_tamper(self):
  with tempfile.TemporaryDirectory(dir=ROOT/'production') as d:
   p=Path(d)/'provenance.json';g=f.read(f.safe(self.manifest['items'][0]['provenance_path']));g['prompt_sha256']='wrong';f.write(p,g)
   self.bad(lambda m:m['items'][0].update(provenance_path=str(p.relative_to(ROOT))),'prompt provenance hash mismatch')

 def promotion_sandbox(self, mutate=None):
  from contextlib import ExitStack
  with tempfile.TemporaryDirectory() as d, ExitStack() as stack:
   temp=Path(d);base=temp/'production/sprite_factory';b=base/'batches/LL-ICON-B0003'
   f.write(b/'active.json',self.manifest)
   f.write(base/'catalog.json',f.read(f.BASE/'catalog.json'))
   f.write(base/'approved_registry.json',{'schema':1,'items':[]})
   receipt={'approval_type':'founder','batch_id':'LL-ICON-B0003','evidence_url':'https://example.invalid/UNIT-TEST-FIXTURE-NOT-REAL-APPROVAL','style_calibration_approved':True,'approved_hashes':{x['asset_id']:x['content_sha256'] for x in self.manifest['items']}}
   if mutate:mutate(receipt)
   f.write(temp/'receipt.json',receipt)
   stack.enter_context(patch.object(f,'ROOT',temp))
   stack.enter_context(patch.object(f,'BASE',base))
   stack.enter_context(patch.object(f,'safe',lambda path:ROOT/path))
   if mutate:
    with self.assertRaisesRegex(ValueError,'exact asset hash'):f.promote('LL-ICON-B0003','active',temp/'receipt.json')
    self.assertFalse((temp/'assets/last_light/approved').exists())
   else:
    f.promote('LL-ICON-B0003','active',temp/'receipt.json')
    entries=f.read(base/'approved_registry.json')['items']
    self.assertEqual(len(entries),20)
    self.assertTrue(all('/active/' not in x['export_path'] for x in entries))
    self.assertTrue(all((temp/x['export_path']).exists() for x in entries))
    # Reapplying one exact receipt is safe and never duplicates logical IDs.
    f.promote('LL-ICON-B0003','active',temp/'receipt.json')
    self.assertEqual(len(f.read(base/'approved_registry.json')['items']),20)
 def test_promotion_transaction_in_temporary_fixture(self):self.promotion_sandbox()
 def test_partial_approval_cannot_copy_any_exports(self):self.promotion_sandbox(lambda a:a['approved_hashes'].pop(next(iter(a['approved_hashes']))))
 def test_tampered_approval_cannot_copy_any_exports(self):self.promotion_sandbox(lambda a:a['approved_hashes'].update({next(iter(a['approved_hashes'])):'wrong'}))

if __name__=='__main__':unittest.main(verbosity=2)
