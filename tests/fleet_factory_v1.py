"""Fleet production scheduling and source geometry contracts (stdlib + Pillow)."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"/"vehicle_factory"))
from fleet_catalog import PROFILES,PALETTE,CONDITIONS,build_plan,digest,validate

class FleetFactoryV1(unittest.TestCase):
    def test_count_and_unique_real_template_identities(self):
        self.assertTrue(validate())
        plan=build_plan(batch_size=128)
        self.assertEqual(len(PROFILES),12)
        self.assertEqual(len(PALETTE),8)
        self.assertEqual(len(CONDITIONS),4)
        self.assertEqual(plan["total_candidate_variants"],384)
        self.assertEqual(plan["planned_frame_count"],6144)
        self.assertEqual(len(plan["batches"]),3)
        self.assertEqual(len({j["job_id"] for j in plan["jobs"]}),384)
        self.assertEqual(plan["status"],"PLAN_ONLY_NO_GAMEPLAY_INTEGRATION")
        self.assertTrue(all("NOT_RENDERED" in j["status"] for j in plan["jobs"]))
    def test_deterministic_order_independent_of_selection(self):
        models=["city_sedan","delivery_van","work_pickup"]
        colors=["olive_green","cream_white"]
        cond=[0,3]
        a=build_plan(models,colors,cond)
        b=build_plan(models[::-1],colors[::-1],cond[::-1])
        self.assertEqual(a["plan_sha256"],b["plan_sha256"])
        self.assertEqual(a["jobs"],b["jobs"])
    def test_enforce_source_coverage_and_no_fake_variants(self):
        self.assertEqual(len({x["geometry"] for x in PROFILES.values()}),10)
        self.assertNotEqual(PROFILES["work_pickup"]["geometry"],PROFILES["city_sedan"]["geometry"])
        for bad in ({"profiles":["unknown"]},{"colors":["magic"]},{"conditions":[8]},
                    {"directions":8},{"batch_size":257}):
            with self.assertRaises(ValueError):build_plan(**bad)
    def test_small_batch_job_manifest_preparation(self):
        plan=build_plan(["city_sedan","work_pickup"],["faded_red","dark_blue"],[1],batch_size=2)
        self.assertEqual(plan["total_candidate_variants"],4)
        self.assertEqual(len(plan["batches"]),2)
        with tempfile.TemporaryDirectory() as d:
            f=Path(d)/"plan.json"
            f.write_text(json.dumps(plan))
            loaded=json.loads(f.read_text())
            self.assertEqual(loaded["plan_sha256"],digest(loaded["jobs"]))
            self.assertEqual(len(loaded["jobs"]),4)

if __name__=="__main__":unittest.main()
