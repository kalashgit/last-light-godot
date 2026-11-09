"""LAST LIGHT — fail-closed schematic neighborhood and three house plan tests."""
from __future__ import annotations
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[2]
CITY=json.loads((ROOT/"data/neighborhood/showcase_60_v1.json").read_text())
LAB=json.loads((ROOT/"data/neighborhood/house_lab_h01_h02_h03_v1.json").read_text())
TAXONOMY={
    "Residential":("house_small house_large apartment_block trailer_park mobile_home garage shed townhouse duplex").split(),
    "Commercial":("grocery_store supermarket gas_station restaurant cafe diner bar_pub clothing_store department_store hardware_store pharmacy clinic hair_salon bank office").split(),
    "Civic / public":("police_station fire_station hospital medical_center elementary_school high_school college_building church community_center library post_office prison detention_facility").split(),
    "Industrial / utility / rural":("warehouse factory farm barn silo mechanic_shop power_station water_treatment construction_site storage_yard").split(),
    "Recreation":("gym bowling_alley movie_theater sports_field stadium park campground").split(),
    "Special":("military_base checkpoint radio_station tv_station hotel motel").split(),
}

def rect_intersects(a,b):
    return a[0]<b[0]+b[2] and b[0]<a[0]+a[2] and a[1]<b[1]+b[3] and b[1]<a[1]+a[3]

def tiles(rect):
    x,y,w,h=map(int,rect)
    return {(a,b) for a in range(x,x+w) for b in range(y,y+h)}


class NeighborhoodContractTests(unittest.TestCase):
    def test_all_60_exact_notional_archetypes(self):
        self.assertEqual(CITY["schema"],"last_light.neighborhood_60_prototype.v1")
        actual={group:{b["archetype_id"] for b in CITY["buildings"] if b["group"]==group}
                for group in TAXONOMY}
        for group,ids in TAXONOMY.items():
            self.assertEqual(actual[group],set(ids),group)
        self.assertEqual(len(CITY["buildings"]),60)

    def test_three_types_on_original_residential_street(self):
        self.assertEqual(CITY["three_house_street"],["house_small","house_large","duplex"])
        self.assertEqual([b["archetype_id"] for b in CITY["buildings"][:3]],
                         CITY["three_house_street"])

    def test_city_no_overlapping_parcels_or_duplicate_instance_ids(self):
        buildings=CITY["buildings"]
        self.assertEqual(len(set(b["instance_id"] for b in buildings)),60)
        for i,a in enumerate(buildings):
            x,y,w,h=a["footprint"]
            self.assertGreater(w,0)
            self.assertGreater(h,0)
            self.assertTrue(0<=x and 0<=y and x+w<=240 and y+h<=220)
            self.assertEqual(a["status"],"CALIBRATION_LAYOUT_ONLY")
            self.assertIsNone(a["asset_package"])
            self.assertEqual(a["front_door"],[x+w/2,y+h])
            for b in buildings[i+1:]:
                self.assertFalse(rect_intersects(a["footprint"],b["footprint"]),
                                 f"overlap: {a['archetype_id']} vs {b['archetype_id']}")

    def test_no_copyright_or_false_approved_assets(self):
        self.assertEqual(CITY["status"],"LAYOUT_PROTOTYPE_NO_GOLDEN_ART")
        self.assertEqual(LAB["status"],"LAYOUT_CALIBRATION_ONLY_NOT_GOLDEN")
        self.assertEqual(CITY["tile_pixel_basis"],[80,40])
        self.assertEqual(LAB["tile_pixel_basis"],[80,40])

    def test_three_authored_house_labs(self):
        self.assertEqual(LAB["schema"],"last_light.house_lab_v1")
        houses=LAB["houses"]
        self.assertEqual([h["id"] for h in houses],["LAB-H01","LAB-H02","LAB-H03"])
        self.assertEqual([h["footprint"][2:] for h in houses],[[12,10],[16,12],[18,14]])
        self.assertEqual([h["stories"] for h in houses],[1,2,1])
        self.assertEqual(houses[2]["cutout"],[14,0,4,4])
        self.assertEqual(houses[1]["stairwell"],[7,8,3,4])

    def test_every_lab_ground_room_tile_has_exactly_one_purpose(self):
        for h in LAB["houses"]:
            w,height=h["footprint"][2:]
            expected=tiles([0,0,w,height])
            if "cutout" in h:
                expected-=tiles(h["cutout"])
            actual=set()
            for room in h["rooms"]:
                room_tiles=tiles(room["rect"])
                self.assertFalse(actual & room_tiles,f"overlap in {h['id']}: {room['id']}")
                actual |=room_tiles
            self.assertEqual(actual,expected,f"missing/extra cells in {h['id']}")

    def test_h02_upstairs_all_rooms_and_stairs(self):
        h=LAB["houses"][1]
        self.assertEqual(len(h["upper_rooms"]),7)
        covered=set()
        for room in h["upper_rooms"]:
            cell=tiles(room["rect"])
            self.assertFalse(covered & cell)
            covered|=cell
        self.assertEqual(covered,tiles([0,0,16,12]))
        stairs=tiles(h["stairwell"])
        self.assertTrue(stairs <= covered)
        self.assertTrue(stairs <= tiles([0,0,16,12]))

    def test_lab_exits_and_entrances_not_overlapping(self):
        labs=LAB["houses"]
        for i,h in enumerate(labs):
            x,y,w,height=h["footprint"]
            self.assertEqual(h["front_door"][1],y+height)
            self.assertTrue(x < h["front_door"][0] < x+w)
            for other in labs[i+1:]:
                self.assertFalse(rect_intersects(h["footprint"],other["footprint"]))

if __name__=="__main__":
    unittest.main()
