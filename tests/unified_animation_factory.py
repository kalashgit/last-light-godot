"""Deterministic plans and animation atlas correctness; Blender render tested in Actions separately."""
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"/"unified_factory"))
sys.path.insert(0,str(ROOT/"tools"/"animation_factory"))
from batch_plan import build_plan, source_registry
from object_contracts import validate_catalog, validate_object
from copy import deepcopy
from pack import process

class UnifiedAnimationFactoryV1(unittest.TestCase):
    def test_registered_300_and_large_batches(self):
        entries=source_registry()
        self.assertEqual(len(entries),300)
        plan=build_plan(entries,batch_size=128)
        self.assertEqual(plan["candidate_job_count"],1200)
        self.assertEqual(len(plan["batches"]),10)
        self.assertTrue(all(b["count"] <= 128 for b in plan["batches"]))
        self.assertEqual(plan["status"],"PLANNED_ONLY_NO_RENDER_OR_GODOT_INTEGRATION")
        self.assertEqual(len({j["job_id"] for j in plan["jobs"]}),1200)

    def test_seven_thousand_planned_are_not_visual_approvals(self):
        plan=build_plan(source_registry(),palettes=3,shapes=2,batch_size=256)
        self.assertEqual(plan["candidate_job_count"],7200)
        self.assertEqual(len(plan["batches"]),29)
        self.assertTrue(all(j["status"].startswith("planned_not_generated") for j in plan["jobs"]))

    def test_catalog_order_does_not_change_plan_hash(self):
        records=source_registry()[:35]
        a=build_plan(records,conditions=(0,1,2,3),batch_size=17)
        b=build_plan(list(reversed(records)),conditions=(3,2,1,0),batch_size=17)
        self.assertEqual(a["plan_hash"],b["plan_hash"])

    def test_duplicate_asset_id_fails(self):
        records=source_registry()[:2]
        with self.assertRaises(ValueError):
            build_plan(records+records)

    def test_invalid_settings_fail(self):
        r=source_registry()[:1]
        for cond in ((1,1),(4,),(-1,)):
            with self.assertRaises(ValueError):
                build_plan(r,conditions=cond)
        with self.assertRaises(ValueError):
            build_plan(r,batch_size=0)
        with self.assertRaises(ValueError):
            build_plan(r,shapes=0)

    def test_animation_recipe_contract(self):
        recipes=json.loads((ROOT/"tools"/"animation_factory"/"recipes.json").read_text())
        self.assertEqual(recipes["schema_version"],1)
        ids=[a["id"] for a in recipes["actions"]]
        self.assertEqual(len(ids),len(set(ids)))
        for action in recipes["actions"]:
            self.assertIn(action["rig"],("fridge_hinge","paired_cabinet_hinges"))
            self.assertGreaterEqual(action["frames"],3)
            self.assertGreater(action["event_frame"],0)
            self.assertLess(action["event_frame"],action["frames"])
            self.assertEqual(action["condition"],1)

    def test_fixed_crop_and_anchor_across_animation_frames(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); raw=root/"raw"; out=root/"packed"
            folder=raw/"test_open"; folder.mkdir(parents=True)
            frames=[]
            for idx,x in enumerate((13,18,23)):
                img=Image.new("RGBA",(64,64),(0,0,0,0))
                ImageDraw.Draw(img).rectangle((x,16,x+10,38),fill=(150,80,60,255))
                name=f"frame_{idx:02}.png"
                img.save(folder/name)
                frames.append(name)
            (raw/"manifest.json").write_text(json.dumps(dict(schema_version=1,tile_px=[80,40],
                entries=[dict(id="test_open",family="cabinet",fps=8,frames=frames,
                event_frame=1,reverse_for_close=True,condition=1,
                pivot_source_canvas=[32,48])])))
            result=process(raw,out)
            r=result["entries"][0]
            self.assertEqual(r["frame_count"],3)
            self.assertEqual(r["fps"],8)
            self.assertEqual(r["event_frame"],1)
            self.assertTrue((out/"test_open"/"strip.png").exists())
            self.assertTrue((out/"test_open"/"preview.gif").exists())
            cells=[Image.open(out/"test_open"/f) for f in frames]
            self.assertEqual(len({x.size for x in cells}),1)
            self.assertEqual(Image.open(out/"test_open"/"strip.png").size,
                (cells[0].width*3,cells[0].height))
            self.assertEqual(len(r["frame_sha256"]),3)
            self.assertNotEqual(r["frame_sha256"][0],r["frame_sha256"][-1])


    def test_extended_material_source_library(self):
        sys.path.insert(0,str(ROOT/"tools"/"material_factory"))
        import expanded_materials
        import numpy as np
        self.assertEqual(len(expanded_materials.FAMILIES),9)
        for name in expanded_materials.FAMILIES:
            one=expanded_materials.maps_for(name,64,1)
            again=expanded_materials.maps_for(name,64,1)
            weather=expanded_materials.maps_for(name,64,3)
            self.assertEqual(set(one),set(expanded_materials.CHANNELS))
            self.assertEqual(one["albedo"][0].shape,(64,64,3))
            self.assertTrue(np.array_equal(one["albedo"][0],again["albedo"][0]))
            self.assertTrue(np.all(one["metallic"][0] == 0))
            self.assertFalse(np.array_equal(one["albedo"][0],weather["albedo"][0]))

    def test_universal_world_object_templates(self):
        samples=json.loads((ROOT/"tools"/"unified_factory"/"examples"/"world_objects_v1.json").read_text())
        result=validate_catalog(samples)
        self.assertEqual(result["templates"],8)
        self.assertEqual(result["hollow_storage"],2)
        self.assertEqual(result["tile_count"],1)
        fridge=next(x for x in samples["templates"] if x["family"]=="refrigerator")
        self.assertEqual({p["bound_to_door"] for p in fridge["components"]["storage"]["compartments"]},
                         {"lower","upper"})
        cabinet=next(x for x in samples["templates"] if x["family"]=="cabinet")
        self.assertTrue(cabinet["components"]["storage"]["hollow"])
        floor=next(x for x in samples["templates"] if x["kind"]=="tile")
        self.assertNotIn("storage",floor["components"])
        self.assertEqual(floor["physical"]["collision"]["mode"],"passable")

    def test_storage_must_be_hollow_and_touch_action_reachable(self):
        samples=json.loads((ROOT/"tools"/"unified_factory"/"examples"/"world_objects_v1.json").read_text())
        fridge=next(x for x in samples["templates"] if x["family"]=="refrigerator")
        a=deepcopy(fridge)
        a["components"]["storage"]["hollow"]=False
        with self.assertRaisesRegex(ValueError,"hollow"):
            validate_object(a)
        a=deepcopy(fridge)
        del a["components"]["interaction"]["reach_m"]
        with self.assertRaisesRegex(ValueError,"reach"):
            validate_object(a)
        a=deepcopy(fridge)
        a["components"]["storage"]["compartments"][0]["slots"]=0
        with self.assertRaisesRegex(ValueError,"slots"):
            validate_object(a)

    def test_sight_and_collision_are_independent(self):
        samples=json.loads((ROOT/"tools"/"unified_factory"/"examples"/"world_objects_v1.json").read_text())
        glass=next(x for x in samples["templates"] if x["family"]=="glass_table")
        self.assertEqual(glass["physical"]["collision"]["mode"],"partial")
        self.assertEqual(glass["physical"]["sight"]["mode"],"transparent")
        sofa=next(x for x in samples["templates"] if x["family"]=="sofa")
        self.assertEqual(sofa["physical"]["collision"]["mode"],"solid")
        self.assertEqual(sofa["physical"]["sight"]["mode"],"partial")

    def test_tile_cannot_fake_storage_and_door_has_removable_barricade(self):
        samples=json.loads((ROOT/"tools"/"unified_factory"/"examples"/"world_objects_v1.json").read_text())
        tile=next(x for x in samples["templates"] if x["kind"]=="tile")
        a=deepcopy(tile)
        a["components"]["storage"]={"hollow":True,"compartments":[{"id":"x","bound_to_door":"always_open",
            "slots":1,"capacity_kg":1,"capacity_l":1}]}
        with self.assertRaisesRegex(ValueError,"tiles cannot"):
            validate_object(a)
        door=next(x for x in samples["templates"] if x["kind"]=="door")
        self.assertTrue(door["components"]["barricade"]["removable"])
        self.assertEqual(door["components"]["destruction"]["stages"],["intact","damaged","broken"])

    def test_every_catalog_item_receives_a_semantic_requirements_audit(self):
        from capability_audit import audit
        report=audit()
        self.assertEqual(report["catalog_id_count"],300)
        self.assertEqual(len(report["records"]),300)
        self.assertEqual(len({r["asset_id"] for r in report["records"]}),300)
        self.assertEqual(report["status"],"COVERAGE_AUDIT_NOT_GAMEPLAY_INTEGRATION")
        self.assertTrue(all({"collision","sight","sound","placement","persistence"}.issubset(r["required_components"])
            for r in report["records"]))
        fridge=[r for r in report["records"] if r["geometry_family"]=="fridge"]
        self.assertTrue(fridge)
        self.assertTrue(all("hollow_geometry" in r["required_components"] for r in fridge))
        self.assertTrue(all(r["status"] != "GAMEPLAY_INTEGRATED" for r in report["records"]))

if __name__ == "__main__":
    unittest.main()
