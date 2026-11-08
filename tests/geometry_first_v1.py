"""Static contract tests for full original model census and Golden40 reconstruction."""
import ast
import json
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools/geometry_first"))
from plan import build_plan, GOLDEN_SPECS

class GeometryFirstV1(unittest.TestCase):
    def test_full_plan_counts(self):
        p=build_plan()
        self.assertEqual(p["total_unique"],360)
        self.assertEqual(p["per_category"],{
            "golden40":40,"catalog":300,"furniture":3,"actor":5,"vehicle":12})
        self.assertEqual(len({x["asset_id"] for x in p["jobs"]}),360)
        self.assertTrue(all(j["status"]=="3D_SOURCE_PLANNED_NOT_EXPORTED" for j in p["jobs"]))
        self.assertTrue(all(j["template_source_hash"] and j["quality"] for j in p["jobs"]))
        self.assertTrue(all(not j.get("founder_golden_approved",False) for j in p["jobs"]))
        self.assertEqual(p["render_2_5d_status"],"PENDING_SEPARATE_MATERIAL_AND_RENDER_STAGE")

    def test_golden_all_40_explicit_geometry_families(self):
        golden=json.loads((ROOT/"assets/last_light/golden40/manifest.json").read_text())
        found={r["id"].removeprefix("ll_golden_") for r in golden["items"]}
        self.assertEqual(found,set(GOLDEN_SPECS))
        selected=build_plan(["golden40"])
        self.assertEqual(len(selected["jobs"]),40)
        self.assertGreaterEqual(len({j["geometry_family"] for j in selected["jobs"]}),19)
        self.assertTrue(all(j["source_reference"].startswith(
            "assets/last_light/golden40/") for j in selected["jobs"]))
        self.assertTrue(all(j["original_reference_only"] for j in selected["jobs"]))

    def test_no_overclaim_from_subset(self):
        sub=build_plan(["golden40","actor"],limit=8)
        self.assertEqual(sub["total_unique"],8)
        self.assertEqual(sub["per_category"]["vehicle"],0)
        with self.assertRaises(ValueError):build_plan(["nothing"])
        with self.assertRaises(ValueError):build_plan(["golden40"],limit=41)
        with self.assertRaises(ValueError):
            build_plan(["golden40"],include=["not_a_valid_asset"])
        self.assertEqual(build_plan().get("plan_sha256"),build_plan().get("plan_sha256"))

    def test_blender_export_files_compile(self):
        for filename in ("export.py","golden40_mesh.py"):
            ast.parse((ROOT/"tools/geometry_first"/filename).read_text())

if __name__=="__main__":
    unittest.main()
