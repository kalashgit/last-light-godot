"""LAST LIGHT full-fidelity V2 provenance, complete 360 ledger and stage QA."""
import ast
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools/geometry_first"))
from plan import build_plan
from refine_spec_v2 import FAMILY_RULES,STAGES,required_skills,defects_for
from refinement_ledger_v2 import create

class FullFidelityV2(unittest.TestCase):
    def test_full_existing_geometry_coverage_and_quality_gate(self):
        plan=build_plan()
        self.assertEqual(plan["total_unique"],360)
        report=create(refined_report=ROOT/"preview/geometry-refinement-v2/__not_generated.json")
        self.assertEqual(report["counts"]["source_models"],360)
        self.assertEqual(report["counts"]["refined_geometry_verified"],0)
        self.assertEqual(report["counts"]["remaining_refinements"],360)
        self.assertEqual(report["counts"]["golden_visual_approved"],0)
        self.assertEqual(len(report["records"]),360)
        self.assertTrue(report["scope"]["full_census_unreconciled"])
        self.assertEqual({r["asset_id"] for r in report["records"]},
                         {j["asset_id"] for j in plan["jobs"]})

    def test_all_families_have_specialists_and_falsifiable_checks(self):
        plan=build_plan()
        for j in plan["jobs"]:
            s=required_skills(j)
            checks=defects_for(j)
            self.assertIn("LL-081",s)
            self.assertIn("LL-111",s)
            self.assertIn("LL-116",s)
            self.assertGreaterEqual(len(checks),4)
            self.assertFalse(any(not x for x in checks))
        self.assertEqual(FAMILY_RULES["world_tile_px"],[80,40])
        self.assertEqual(FAMILY_RULES["environment_condition_levels"],[0,1,2,3])
        self.assertEqual([x["id"] for x in STAGES],["G0","G1","G2","M","R","V","E","D"])

    def test_code_syntax_and_no_auto_promotion(self):
        for filename in ("refine_v2.py","refine_spec_v2.py","export.py",
            "refinement_ledger_v2.py","compare_v2.py","verify_refinement_v2.py"):
            with self.subTest(filename=filename):
                ast.parse((ROOT/"tools/geometry_first"/filename).read_text())
        result=create(refined_report=ROOT/"preview/geometry-refinement-v2/__not_generated.json")
        for row in result["records"]:
            self.assertFalse(row["release_gates"]["founder_golden_approved"])
            self.assertFalse(row["release_gates"]["gameplay_integrated"])

    def test_specific_families_must_keep_distinct_geometry(self):
        plans={j["asset_id"]:j for j in build_plan()["jobs"]}
        for aid in ("ll_tools_awl","ll_tools_cross_screwdriver",
                    "ll_tools_flat_screwdriver","ll_tools_crowbar",
                    "ll_master_vehicle_compact_hatchback","ll_master_vehicle_city_sedan"):
            self.assertIn(aid,plans)
        self.assertNotEqual(plans["ll_master_vehicle_compact_hatchback"]["dimensions_m"],
                            plans["ll_master_vehicle_city_sedan"]["dimensions_m"])

if __name__=="__main__":
    unittest.main()
