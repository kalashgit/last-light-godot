"""Fail-closed safety regression suite for unapproved founder reference sheets."""
import copy
import shutil
import os
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools' / 'foundry_reference_sheets'))
from verify_supplemental_queue import verify

ROOT = Path(__file__).resolve().parents[2]
QUEUE = ROOT / 'data/foundry_reference_catalog/supplement_20261110/derived/supplemental_reference_queue.jsonl'
REPORT = ROOT / 'data/foundry_reference_catalog/supplement_20261110/derived/supplemental_intake_report.json'
IMAGES = Path(os.environ.get('LL_FOUNDER_PRIVATE_JPEGS', str(ROOT / 'private_originals_not_in_git')))


class IntakeSafetyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)
        self.rows = [json.loads(r) for r in QUEUE.read_text().splitlines() if r.strip()]
        self.report = json.loads(REPORT.read_text())

    def attempt(self, mutation=None, report_mutation=None):
        rows = copy.deepcopy(self.rows)
        rep = copy.deepcopy(self.report)
        if mutation:
            mutation(rows)
        if report_mutation:
            report_mutation(rep)
        q = self.dir / 'rows.jsonl'
        r = self.dir / 'report.json'
        q.write_text(''.join(json.dumps(row)+'\n' for row in rows))
        r.write_text(json.dumps(rep))
        return verify(q, r)

    def test_complete_250_queue_blocked(self):
        result = verify(QUEUE, REPORT)
        self.assertEqual(result['reference_slots'], 250)
        self.assertFalse(result['independent_original_image_verification'])
        self.assertEqual(result['founder_golden_approved'], 0)

    def test_image_source_sha_when_originals_available(self):
        aliases = {
            'founder_extra_50_cells_unmapped.jpeg': 'founder_extra_50_cells_unmapped.jpeg',
            'founder_401_600_dense_overview.jpeg': 'founder_401_600_dense_overview.jpeg',
        }
        if not all((IMAGES / original).is_file() for original in aliases):
            self.skipTest('Private founder JPEG binaries not in GitHub checkout')
        for original, expected in aliases.items():
            shutil.copyfile(IMAGES / original, self.dir / expected)
        result = verify(QUEUE, REPORT, self.dir)
        self.assertTrue(result['independent_original_image_verification'])

    def test_rejects_forged_golden(self):
        with self.assertRaisesRegex(ValueError, 'unsafe'):
            self.attempt(lambda x: x[0].update(founder_golden_approved=True))

    def test_rejects_forged_canonical_id(self):
        with self.assertRaisesRegex(ValueError, 'unsafe'):
            self.attempt(lambda x: x[0].update(canonical_notion_id='fabricated'))

    def test_rejects_duplicate_reference_key(self):
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            self.attempt(lambda x: x[1].update(reference_id=x[0]['reference_id']))

    def test_rejects_ghost_model_count(self):
        with self.assertRaisesRegex(ValueError, 'falsely'):
            self.attempt(report_mutation=lambda x: x.update(model_count=250))

    def test_rejects_grid_cropping_drift(self):
        with self.assertRaisesRegex(ValueError, 'unsafe'):
            self.attempt(lambda x: x[50].update(cell_column=19))

    def test_fails_closed_when_image_source_not_available(self):
        with self.assertRaisesRegex(ValueError, 'missing or modified'):
            verify(QUEUE, REPORT, self.dir)


if __name__ == '__main__':
    unittest.main()