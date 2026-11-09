"""V4 source contracts: authored family roles, no forged Golden approval, and 3 distinct house themes."""
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[2]
FURNISH=json.loads((ROOT/'data/neighborhood/house_lab_furnishing_v4.json').read_text())
LAB=json.loads((ROOT/'data/neighborhood/house_lab_h01_h02_h03_v1.json').read_text())
LEDGER=json.loads((ROOT/'docs/production/integration_v2/approval_ledger.json').read_text())


class FurnishingV4ContractTests(unittest.TestCase):
    def test_three_distinct_authored_surface_styles(self):
        self.assertEqual(FURNISH['schema'],'last_light.house_lab_furnishing.v4')
        self.assertEqual(FURNISH['lab_ids'],[h['id'] for h in LAB['houses']])
        styles=FURNISH['visual_themes']
        self.assertEqual(len(styles),3)
        self.assertEqual(len({v['floor'] for v in styles.values()}),3)
        self.assertEqual(len({v['walls'] for v in styles.values()}),3)
        self.assertLess(styles['LAB-H01']['wear'],styles['LAB-H02']['wear'])
        self.assertLess(styles['LAB-H02']['wear'],styles['LAB-H03']['wear'])

    def test_supplements_are_plausible_and_are_not_canonical_ids(self):
        known_rooms={r['id'] for h in LAB['houses'] for r in h['rooms']+h['upper_rooms']}
        self.assertTrue(set(FURNISH['room_overrides']) <= known_rooms)
        self.assertGreaterEqual(len(FURNISH['supplements']),10)
        for profile in list(FURNISH['supplements'].values())+list(FURNISH['room_overrides'].values()):
            for fixture in profile:
                self.assertTrue(fixture['role'])
                self.assertNotIn('canonical_asset_id',fixture)
                self.assertNotIn('golden_approved',fixture)
                self.assertTrue(all(0 < x < 1 for x in fixture['at']))
                self.assertTrue(all(x>0 for x in fixture['size']))
        self.assertEqual(LEDGER['asset_approvals'],[])


if __name__=='__main__':
    unittest.main()
