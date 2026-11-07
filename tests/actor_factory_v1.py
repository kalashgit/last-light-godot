"""LAST LIGHT actor factory contract/aging/zombie/world-scale regression tests."""
import json
import sys
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path
from PIL import Image,ImageDraw

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"/"actor_factory"))
from actor_state import (create_actor,advance_day,trim_hair,spawn_zombie,set_equipment,
                        appearance,AREAS,ROLES,WEARABLES,SURVIVAL_LOOT,ACTOR_RIG)
from pack import pack

class ActorFactoryV1(unittest.TestCase):
    def test_one_shared_biped_and_size(self):
        a=create_actor("a","seed",height_m=1.74)
        b=create_actor("b","seed",build="broad",presentation="feminine",height_m=1.83)
        self.assertEqual(a["rig"],b["rig"])
        self.assertEqual(ACTOR_RIG["direction_count"],4)
        self.assertEqual(ACTOR_RIG["tile_px"],[80,40])
        for id in ("a","b"):
            self.assertTrue(id)
        with self.assertRaises(ValueError):
            create_actor("invalid","seed",height_m=2.8)

    def test_age_hair_grow_every_day_deterministic(self):
        p=create_actor("survivor",1234,age_years=39)
        original=deepcopy(p)
        d=advance_day(p,1,exercise=.8,nutrition=.8,recovery=.8)
        self.assertEqual(d["day_index"],1)
        self.assertAlmostEqual(d["biological_age_days"],p["biological_age_days"]+1)
        self.assertAlmostEqual(d["hair_length_mm"],p["hair_length_mm"]+.34)
        self.assertEqual(p,original)
        self.assertEqual(d,advance_day(deepcopy(p),1,.8,.8,.8))
        with self.assertRaises(ValueError):
            advance_day(d,1)
        with self.assertRaises(ValueError):
            advance_day(d,4)

    def test_age_grey_progress_and_haircuts(self):
        a=create_actor("age_reference",43,age_years=20)
        a["grey_onset_age"]=39
        a["hair_length_mm"]=105
        a.update(appearance(a))
        self.assertEqual(a["grey_fraction"],0)
        b=deepcopy(a)
        b["biological_age_days"]=55*b["days_per_biological_year"]
        b.update(appearance(b))
        self.assertGreater(b["grey_fraction"],a["grey_fraction"])
        self.assertLess(b["grey_fraction"],1)
        c=trim_hair(b,20,beard_mm=0)
        self.assertLessEqual(c["hair_length_mm"],20)
        self.assertEqual(c["head_hair_style"],"cropped")

    def test_training_and_inactivity_slowly_change_body(self):
        start=create_actor("fitness_actor",98)
        active=deepcopy(start)
        inactive=deepcopy(start)
        for day in range(1,181):
            active=advance_day(active,day,exercise=1,nutrition=.9,recovery=.95)
            inactive=advance_day(inactive,day,exercise=0,nutrition=.4,recovery=.5)
        self.assertGreater(active["muscle"],start["muscle"])
        self.assertLess(inactive["muscle"],start["muscle"])
        self.assertGreater(active["muscle"],inactive["muscle"]+.1)
        self.assertGreater(active["fitness"],inactive["fitness"])
        self.assertEqual(active["height_m"],start["height_m"])
        self.assertGreater(active["body_morph"]["arm_radius_scale"],inactive["body_morph"]["arm_radius_scale"])

    def test_inevitable_age_death_under_adjustable_calendar(self):
        actor=create_actor("aged_survivor",44,age_years=110,days_per_biological_year=30)
        for day in range(1,451):
            if not actor["alive"]:
                break
            actor=advance_day(actor,day,exercise=0,nutrition=.6,recovery=.6)
        self.assertFalse(actor["alive"])
        self.assertEqual(actor["cause_of_death"],"natural_ageing")
        self.assertEqual(actor,advance_day(deepcopy(actor),actor["day_index"]+1))

    def test_zombies_spawn_in_building_linked_outfits_and_loot(self):
        for area in AREAS:
            for i in range(15):
                a=spawn_zombie(15,"building_"+area,"room_1",i,area)
                again=spawn_zombie(15,"building_"+area,"room_1",i,area)
                self.assertEqual(a,again)
                self.assertEqual(a["kind"],"zombie")
                self.assertIn(a["role"],[role for role,_ in AREAS[area]])
                self.assertEqual(a["visual_loadout_ids"],a["apparel"])
                for clothing_id in a["apparel"]:
                    self.assertIn(clothing_id,WEARABLES)
                    self.assertIn({"item_id":clothing_id,"count":1,"worn":True},a["inventory"])
                for item in a["inventory"]:
                    self.assertIn(item["item_id"],WEARABLES.keys()|SURVIVAL_LOOT.values())

    def test_equipment_unique_slots_and_held_item(self):
        a=create_actor("equipped_actor",7)
        a=set_equipment(a,["ll_wear_grey_underwear","ll_wear_grey_tank","ll_wear_work_pants",
                           "ll_wear_work_boots","ll_wear_hivis_vest"],"ll_tools_crowbar")
        self.assertEqual(a["held_item_id"],"ll_tools_crowbar")
        self.assertEqual(a["hand"],"right")
        with self.assertRaisesRegex(ValueError,"conflicting wearable"):
            set_equipment(a,["ll_wear_jeans","ll_wear_work_pants"])
        with self.assertRaisesRegex(ValueError,"unknown wearable"):
            set_equipment(a,["ll_wear_unknown"])

    def test_pack_keeps_fixed_anchor_and_all_directions(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            raw=root/"raw";packed=root/"packed"
            files=[]
            for i,direction in enumerate(("front","right","back","left")):
                folder=raw/"test"/"idle"/direction;folder.mkdir(parents=True)
                img=Image.new("RGBA",(512,512),(0,0,0,0))
                ImageDraw.Draw(img).rectangle((225+i,165,285+i,405),fill=(150,126,96,255))
                img.save(folder/"frame_00.png")
                files.append(dict(render_id="test",actor_id="test1",kind="human",
                    clip="idle",direction=direction,frame=0,fps=8,height_m=1.7,
                    apparel=["ll_wear_grey_tank"],held_item_id=None,grey_fraction=0,muscle=.5,
                    source_canvas=[512,512],anchor_source_px=[256,380],
                    render_file=f"test/idle/{direction}/frame_00.png"))
            (raw/"manifest.json").write_text(json.dumps(dict(schema_version=1,tile_px=[80,40],frames=files)))
            result=pack(raw,packed)
            self.assertEqual(len(result["actors"]),1)
            actor=result["actors"][0]
            clip=actor["clips"]["idle"]
            sheet=Image.open(packed/clip["atlas"])
            self.assertEqual(sheet.size,(clip["cell_px"][0],clip["cell_px"][1]*4))
            self.assertTrue((packed/"actor_review_sheet.png").exists())
            self.assertEqual(clip["frame_count_per_direction"],1)
            self.assertTrue(clip["anchor_px"][1] > 0)

if __name__=="__main__":
    unittest.main()
