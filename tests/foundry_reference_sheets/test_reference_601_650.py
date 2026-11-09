import copy
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools'))
from foundry_601_650 import ACTIVE_RECIPES, CONCEPTS, SHEETS, produce, verify, sha256


class FounderReferenceIntakeTests(unittest.TestCase):
    def test_unique_source_bytes(self):
        self.assertEqual(len(SHEETS),8)
        self.assertEqual(len({x[2] for x in SHEETS}),8)

    def test_distinct_semantic_names(self):
        self.assertEqual(len(CONCEPTS),len({x[0] for x in CONCEPTS}))

    def test_reference_grouping_not_numeric_merge(self):
        d=produce();verify(d)
        self.assertEqual(d['counts']['numbered_visual_slots'],300)
        self.assertEqual(d['counts']['dense_unsegmented_sheets'],2)
        a=next(x for x in d['numbered_visual_slots'] if x['source_sheet']=='S01_SURVIVAL_KITCHEN' and x['visual_slot']==601)
        b=next(x for x in d['numbered_visual_slots'] if x['source_sheet']=='S06_MIXED_PARTS' and x['visual_slot']==601)
        self.assertNotEqual(a['concept_id'],b['concept_id'])

    def test_no_duplicate_slot_assignment(self):
        all_observations=[o for _,_,ref in CONCEPTS for o in ref]
        self.assertEqual(len(all_observations),len(set(all_observations)))

    def test_only_eight_distinct_active_recipe_candidates(self):
        d=produce()
        self.assertEqual(len(ACTIVE_RECIPES),8)
        self.assertEqual(sum(x['requires_distinct_model'] for x in d['reconciled_concepts']),8)

    def test_forged_golden_flag_fails(self):
        d=copy.deepcopy(produce());d['founder_golden_approved']=True
        with self.assertRaises(ValueError):verify(d)

    def test_forged_notion_id_fails(self):
        d=copy.deepcopy(produce());d['reconciled_concepts'][0]['notion_canonical_id']='made-up'
        with self.assertRaises(ValueError):verify(d)

    def test_corrupted_reference_pin_fails(self):
        folder=Path(__file__).resolve().parents[1]/'upload'
        if folder.is_dir():
            produce(folder)
            with patch('foundry_601_650.sha256',return_value='0'*64):
                with self.assertRaisesRegex(ValueError,'missing/tampered'):
                    produce(folder)
        else:
            self.skipTest('private originals are archived separately, not stored in public Git checkout')


if __name__=='__main__': unittest.main()
