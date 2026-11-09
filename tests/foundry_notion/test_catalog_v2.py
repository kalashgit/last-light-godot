from __future__ import annotations
import copy
import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
SPEC=importlib.util.spec_from_file_location('foundry_notion_catalog_v2',ROOT/'tools/foundry_notion/catalog_v2.py')
mod=importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name]=mod
SPEC.loader.exec_module(mod)

def fixture():
    return json.loads((ROOT/'data/foundry/notion_machine_catalog_v2.json').read_text())

class CatalogV2Tests(unittest.TestCase):
    def test_real_notion_snapshot(self):
        doc=fixture()
        mod.validate(doc)
        self.assertEqual(len(doc['masters']),60)
        self.assertEqual(sum(r['automation_gate']=='SPEC_READY_RECIPE_ONLY' for r in doc['masters']),22)
        result=mod.plan(doc,batch_size=10)
        self.assertEqual(len(result['orders']),10)
        self.assertEqual(result['remaining_ready'],12)
        self.assertEqual(result['held_masters'],38)
        self.assertTrue(all(not x['automatic_golden_approval'] and not x['reference_image_copy_allowed'] for x in result['orders']))

    def test_hold_gate_cannot_dispatch(self):
        doc=fixture()
        doc['masters']=[r for r in doc['masters'] if r['automation_gate']=='HOLD']
        doc['canonical_rows']=len(doc['masters'])
        self.assertEqual(mod.plan(doc)['orders'],[])

    def test_rejects_fake_gate(self):
        doc=fixture();doc['masters'][0]['automation_gate']='RELEASE_READY'
        with self.assertRaises(ValueError):mod.plan(doc)

    def test_rejects_unverified_master_promoted_to_recipe(self):
        doc=fixture();doc['masters'][0]['automation_gate']='SPEC_READY_RECIPE_ONLY'
        with self.assertRaises(ValueError):mod.plan(doc)

    def test_rejects_missing_core_spec(self):
        doc=fixture()
        row=next(r for r in doc['masters'] if r['automation_gate']=='SPEC_READY_RECIPE_ONLY')
        row['spec_fields_present']['materials']=False
        with self.assertRaises(ValueError):mod.plan(doc)

    def test_rejects_fake_worker_and_duplicate(self):
        doc=fixture();doc['masters'][0]['queue']='F99'
        with self.assertRaises(ValueError):mod.plan(doc)
        doc=fixture();doc['masters'][1]['content_id']=doc['masters'][0]['content_id']
        with self.assertRaises(ValueError):mod.plan(doc)

    def test_rejects_bad_boolean_approval_flag(self):
        doc=fixture();doc['masters'][0]['provenance_flags']['founder_visual_approved']='__YES__'
        with self.assertRaises(ValueError):mod.plan(doc)

    def test_completion_is_idempotent_and_bounded(self):
        doc=fixture();first=mod.plan(doc,batch_size=4)
        done=[x['content_id'] for x in first['orders']]
        second=mod.plan(doc,completed=done,batch_size=4)
        self.assertFalse(set(done)&{x['content_id'] for x in second['orders']})
        with self.assertRaises(ValueError):mod.plan(doc,completed=['forged_asset'])
        with self.assertRaises(ValueError):mod.plan(doc,batch_size=200)

if __name__=='__main__':unittest.main()
