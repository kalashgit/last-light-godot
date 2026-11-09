"""UCF-001 tests: stdlib only. Run: python -m unittest discover -s tests -v"""
import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('unified_content_factory', ROOT / 'tools/unified_content_factory.py')
factory = importlib.util.module_from_spec(spec)
spec.loader.exec_module(factory)


class UnifiedFactoryTests(unittest.TestCase):
    def setUp(self):
        self.recipe = copy.deepcopy(factory.DEFAULT_RECIPE)

    def test_deterministic_same_seed_byte_identical(self):
        first = factory.dumps(factory.compile_world(self.recipe, 1234))
        self.assertEqual(first, factory.dumps(factory.compile_world(self.recipe, 1234)))

    def test_world_seed_changes_real_layout(self):
        first = factory.compile_world(self.recipe, 1234)
        second = factory.compile_world(self.recipe, 1235)
        self.assertNotEqual([b['bounds'] for b in first['buildings']], [b['bounds'] for b in second['buildings']])
        self.assertNotEqual([b['layout_variant'] for b in first['buildings']], [b['layout_variant'] for b in second['buildings']])

    def test_three_distinct_variants(self):
        world = factory.compile_world(self.recipe)
        self.assertEqual(len(world['buildings']), 3)
        self.assertEqual(len(set(b['roof_profile'] for b in world['buildings'])), 3)
        self.assertEqual(len(set(tuple(b['bounds'][2:]) for b in world['buildings'])), 3)
        self.assertEqual(sum(len(b['rooms']) for b in world['buildings']), 12)

    def test_all_rooms_connected_to_hall_and_exterior(self):
        world = factory.compile_world(self.recipe)
        factory.validate_world(world)
        for house in world['buildings']:
            entry = [d for d in house['doors'] if d['type'] == 'exterior']
            self.assertEqual(len(entry), 1)
            for room in house['rooms']:
                self.assertIn(room['id'], [d['connects'][0] for d in house['doors'] if d['type'] == 'interior'])

    def test_duplicate_lots_blocked(self):
        self.recipe['lots'][1]['id'] = self.recipe['lots'][0]['id']
        with self.assertRaisesRegex(ValueError, 'Duplicate lot'):
            factory.compile_world(self.recipe)

    def test_overlapping_lots_blocked(self):
        self.recipe['lots'][1]['rect'][0] = 7
        with self.assertRaisesRegex(ValueError, 'Overlapping lots'):
            factory.compile_world(self.recipe)

    def test_unavailable_archetype_rejected_not_silently_faked(self):
        self.recipe['lots'][1]['archetype_id'] = 'hospital'
        with self.assertRaisesRegex(ValueError, 'supports house_small only'):
            factory.compile_world(self.recipe)

    def test_output_can_be_reloaded_and_validated(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / 'world.json'
            rc = factory.main(['--out', str(out), '--seed', '20261106'])
            self.assertEqual(rc, 0)
            actual = json.loads(out.read_text())
            factory.validate_world(actual)
            self.assertEqual(actual['schema'], factory.SCHEMA)
            self.assertEqual(factory.main(['--verify', str(out)]), 0)


if __name__ == '__main__':
    unittest.main()