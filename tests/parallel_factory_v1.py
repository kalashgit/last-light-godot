"""Sharded sprite factory scheduling, source identity, and cache plan tests."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools/unified_factory"))
from run_parallel import selected_ids,plan_jobs
from batch_plan import source_registry

class ParallelProductionV1(unittest.TestCase):
    def test_deterministic_no_overlap(self):
        ids=selected_ids(35)
        a=plan_jobs(ids,chunk_size=16,workers=2,threads=2)
        b=plan_jobs(list(ids),chunk_size=16,workers=2,threads=2)
        self.assertEqual(a,b)
        self.assertEqual(a["asset_count"],35)
        self.assertEqual(a["shard_count"],3)
        all_ids=[s for c in a["shards"] for s in c["ids"]]
        self.assertEqual(sorted(all_ids),sorted(ids))
        self.assertEqual(len(set(all_ids)),len(ids))
        self.assertEqual(a["shards"][-1]["asset_count"],3)
        self.assertEqual(a["status"],"PLANNED_RENDER_ONLY_NO_GOLDEN_VISUAL_APPROVAL")

    def test_every_existing_original_registered(self):
        ids=selected_ids()
        self.assertEqual(len(ids),300)
        self.assertEqual(len({x for x in ids}),300)
        p=plan_jobs(ids,chunk_size=128,workers=4,threads=1)
        self.assertEqual(p["shard_count"],3)
        self.assertEqual([s["asset_count"] for s in p["shards"]],[128,128,44])

    def test_rejects_invalid_ids_and_excess_workers(self):
        self.assertRaises(ValueError,selected_ids,301)
        self.assertRaises(ValueError,selected_ids,0,["bad_not_existing"])
        self.assertRaises(ValueError,selected_ids,0,["ll_food_bean_tin","ll_food_bean_tin"])
        for kwargs in (dict(chunk_size=0),dict(workers=0),dict(workers=16),dict(threads=17)):
            with self.assertRaises(ValueError):
                plan_jobs(selected_ids(2),**kwargs)

if __name__=="__main__":
    unittest.main()
