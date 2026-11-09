"""W04 deterministic world-generation tests (brief section 15, items 1-18).

Run: python3 -m unittest discover -s tests/worldgen -v
Items 19-20 (Godot scene compilation, existing game regression) run in Godot:
tests/worldgen/godot_worldgen.gd and tests/run.sh.
"""
from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

from worldgen import buildings as B  # noqa: E402
from worldgen.catalog import catalog, validate_catalog  # noqa: E402
from worldgen.core import GenerationError, dumps, load_json, sha256  # noqa: E402
from worldgen.export import export_world  # noqa: E402
from worldgen.loader import load_export, verify_export  # noqa: E402
from worldgen.neighborhood import generate_world, validate_world  # noqa: E402
from worldgen.plan import Frame, transform_building  # noqa: E402
from worldgen.terrain import adjacency_errors  # noqa: E402
from worldgen.validate import validate_building  # noqa: E402

RECIPES = ROOT / "data/worldgen/recipes"
GENERATED = ROOT / "data/worldgen/generated"
LOCK = ROOT / "tests/worldgen/fixtures/lab_a_lock.json"
PROGRAMS = ["house_small", "house_two_storey", "house_garage", "convenience_store", "workshop"]
FIXTURES = ["LAB-H01", "LAB-H02", "LAB-H03", "LAB-S01", "LAB-W01"]


def recipe(name, **changes):
    r = load_json(RECIPES / f"{name}.json")
    r.update(changes)
    return r


def codes(report):
    return {e["code"] for e in report["errors"]}


def failed(report):
    return {c["check"] for c in report["checks"] if not c["ok"]}


class Cached:
    _worlds = {}

    @classmethod
    def world(cls, name, **changes):
        key = (name, json.dumps(changes, sort_keys=True))
        if key not in cls._worlds:
            cls._worlds[key] = generate_world(recipe(name, **changes))
        return copy.deepcopy(cls._worlds[key])


class T01Determinism(unittest.TestCase):
    def test_same_seed_byte_identical_export(self):
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            for out in (a, b):
                w = generate_world(recipe("w04_demo_suburb"))
                export_world(w, validate_world(w), Path(out))
            fa = sorted(p.relative_to(a).as_posix() for p in Path(a).rglob("*.json"))
            fb = sorted(p.relative_to(b).as_posix() for p in Path(b).rglob("*.json"))
            self.assertEqual(fa, fb)
            for rel in fa:
                self.assertEqual((Path(a) / rel).read_bytes(), (Path(b) / rel).read_bytes(), rel)

    def test_committed_outputs_reproduce(self):
        for name in ("w04_demo_suburb", "lab_a_street"):
            committed = load_json(GENERATED / name / "world_manifest.json")
            with tempfile.TemporaryDirectory() as tmp:
                w = generate_world(recipe(name))
                m = export_world(w, validate_world(w), Path(tmp))
            self.assertEqual(m["blueprint_sha256"], committed["blueprint_sha256"], f"{name} drifted: regenerate or bump version")

    def test_building_layout_deterministic(self):
        for p in PROGRAMS:
            self.assertEqual(dumps(B.generate_building(p, "t.b", 99)), dumps(B.generate_building(p, "t.b", 99)))


class T02Variation(unittest.TestCase):
    def signature(self, b):
        return tuple(sorted((r["type"], tuple(r["rect"])) for f in b["floors"] for r in f["rooms"]))

    def test_programs_vary_with_seed_and_stay_valid(self):
        rules = catalog()["rules"]
        for p in PROGRAMS:
            sigs = set()
            for seed in range(25):
                b = B.generate_building(p, f"var.{p}", seed)
                self.assertTrue(validate_building(b, rules)["ok"])
                self.assertLessEqual(b["generation"]["attempt"], B.MAX_ATTEMPTS - 1)
                sigs.add(self.signature(b))
            self.assertGreaterEqual(len(sigs), 10, f"{p} only {len(sigs)} distinct layouts in 25 seeds")

    def test_world_seeds_vary_and_validate(self):
        lots = set()
        for seed in (1, 2, 3):
            w = generate_world(recipe("random_suburb", world_seed=seed, world_id=f"ll.world.v{seed}"))
            self.assertTrue(validate_world(w)["ok"], failed(validate_world(w)))
            lots.add(tuple(tuple(l["rect"]) for l in w["lots"]))
        self.assertEqual(len(lots), 3)

    def test_district_styles_are_meaningfully_distinct(self):
        stats = {}
        for name in ("random_suburb", "old_town", "rural"):
            w = Cached.world(name)
            self.assertTrue(validate_world(w)["ok"])
            lot_area = sum(l["rect"][2] * l["rect"][3] for l in w["lots"]) / len(w["lots"])
            trees = sum(p["type"] == "tree" for p in w["props"])
            surfaces = {r["surface"] for r in w["roads"]}
            commercial = sum(l["zoning"] in ("convenience_store", "workshop") for l in w["lots"])
            stats[name] = (lot_area, len(w["fences"]), surfaces, trees, commercial)
        self.assertGreater(stats["rural"][0], stats["old_town"][0])
        self.assertEqual(stats["rural"][1], 0)
        self.assertGreater(stats["random_suburb"][1], stats["old_town"][1])
        self.assertEqual(stats["rural"][2], {"gravel"})
        self.assertEqual(stats["old_town"][2], {"asphalt"})
        self.assertGreater(stats["old_town"][4], stats["random_suburb"][4] - 1)


class T03to06WorldChecks(unittest.TestCase):
    def test_all_presets_pass_every_world_check(self):
        for name in ("w04_demo_suburb", "lab_a_street", "random_suburb", "old_town", "rural"):
            rep = validate_world(Cached.world(name))
            self.assertTrue(rep["ok"], f"{name}: {failed(rep)}")

    def test_duplicate_id_detected(self):
        w = Cached.world("w04_demo_suburb")
        w["props"][1]["id"] = w["props"][0]["id"]
        self.assertIn("unique_ids", failed(validate_world(w)))

    def test_overlapping_parcels_detected(self):
        w = Cached.world("w04_demo_suburb")
        w["lots"][1]["rect"] = list(w["lots"][0]["rect"])
        self.assertIn("no_overlapping_parcels", failed(validate_world(w)))

    def test_disconnected_road_graph_detected(self):
        w = Cached.world("w04_demo_suburb")
        node = w["intersections"][0]["id"]
        w["road_graph"] = [e for e in w["road_graph"] if node not in e[:2]]
        self.assertIn("road_network_connected", failed(validate_world(w)))

    def test_blocked_entrance_detected(self):
        w = Cached.world("w04_demo_suburb")
        b = w["buildings"][0]
        door = next(d for d in b["floors"][0]["doors"] if d["kind"] == "exterior")
        from worldgen.neighborhood import door_outside
        cx, cy = door_outside(door, door["world_side"])
        w["props"].append({"id": "ll.test.block", "type": "crate", "rect": [cx, cy, 1, 1], "container": False})
        w["props"].append({"id": "ll.test.block2", "type": "crate", "rect": [cx - 1, cy, 1, 1], "container": False})
        w["props"].append({"id": "ll.test.block3", "type": "crate", "rect": [cx + 1, cy, 1, 1], "container": False})
        w["props"].append({"id": "ll.test.block4", "type": "crate", "rect": [cx, cy + (1 if door["world_side"] == "south" else -1), 1, 1], "container": False})
        self.assertIn("building_entrances_reachable", failed(validate_world(w)))


class T07to11BuildingRules(unittest.TestCase):
    def base(self):
        return B.fixture_building("LAB-H01", "neg.H01")

    def rules(self):
        return catalog()["rules"]

    def test_lab_a_fixtures_valid_in_all_rotations(self):
        for fx in FIXTURES:
            local = B.fixture_building(fx, f"rot.{fx}")
            for r in range(4):
                world = transform_building(local, Frame(local["size"], (30, 40), r))
                rep = validate_building(world, self.rules())
                self.assertTrue(rep["ok"], f"{fx} r{r}: {rep['errors'][:3]}")

    def test_procedural_valid_in_all_rotations(self):
        for p in PROGRAMS:
            local = B.generate_building(p, f"rot.{p}", 5)
            for r in range(4):
                rep = validate_building(transform_building(local, Frame(local["size"], (7, 3), r)), self.rules())
                self.assertTrue(rep["ok"], f"{p} r{r}: {rep['errors'][:3]}")

    def test_missing_door_makes_room_unreachable(self):
        b = self.base()
        f = b["floors"][0]
        f["doors"] = [d for d in f["doors"] if set(d["connects"]) != {"neg.H01.f0.HAL", "neg.H01.f0.UTL"}]
        f.pop("walls")
        self.assertIn("E_UNREACHABLE_ROOM", codes(validate_building(b, self.rules())))

    def test_door_between_wrong_rooms_rejected(self):
        b = self.base()
        b["floors"][0]["doors"][1]["connects"] = ["neg.H01.f0.HAL", "neg.H01.f0.BAT"]
        self.assertIn("E_DOOR_WRONG_ROOMS", codes(validate_building(b, self.rules())))

    def test_door_off_shared_edge_raises(self):
        floor = copy.deepcopy(self.base()["floors"][0])
        with self.assertRaises(GenerationError) as ctx:
            from worldgen.plan import make_door
            make_door("x", floor, 99, "LIV", "BAT", 3.0, 1.2)
        self.assertEqual(ctx.exception.code, "E_DOOR_OFF_EDGE")

    def test_window_on_interior_wall_rejected(self):
        b = self.base()
        w = b["floors"][0]["windows"][0]
        w["a"], w["b"] = [6.0, 0.6], [6.0, 1.6]  # LIV/KIT party wall
        self.assertIn("E_WINDOW_NOT_EXTERIOR", codes(validate_building(b, self.rules())))

    def test_overlapping_and_missing_walls_rejected(self):
        b = self.base()
        walls = b["floors"][0]["walls"]
        walls.append(dict(walls[0]))
        self.assertIn("E_WALL_OVERLAP", codes(validate_building(b, self.rules())))
        b = self.base()
        b["floors"][0]["walls"].pop(0)
        self.assertIn("E_WALL_GAP", codes(validate_building(b, self.rules())))

    def test_bedroom_never_required_passage(self):
        from worldgen.plan import make_door
        b = B.fixture_building("LAB-H02", "neg.H02")
        up = b["floors"][1]
        up["doors"] = [d for d in up["doors"] if set(d["connects"]) != {"neg.H02.f1.BATH1", "neg.H02.f1.CORR"}]
        up["doors"].append(make_door("neg.H02", up, 60, "BED2", "BATH1", 2.5, 1.2))  # ensuite-only bathroom
        up.pop("walls")
        self.assertIn("E_PRIVATE_PASSAGE", codes(validate_building(b, self.rules())))

    def test_stairs_aligned_and_reachable(self):
        b = B.fixture_building("LAB-H02", "neg.H02")
        self.assertTrue(validate_building(b, self.rules())["ok"])
        b["stairs"][0]["upper"]["entry"] = [0, 6]
        self.assertIn("E_STAIR_ENTRY", codes(validate_building(b, self.rules())))
        b = B.fixture_building("LAB-H02", "neg.H02")
        b["stairs"][0]["rect"] = [0, 6, 2, 3]
        self.assertIn("E_STAIR_MISALIGNED", codes(validate_building(b, self.rules())))

    def test_furniture_blocking_door_and_overlap_rejected(self):
        b = self.base()
        item = b["floors"][0]["furniture"][0]
        item["rect"] = [5, 9, 1, 1]  # hall cell inside the front door clearance
        item["room"] = "neg.H01.f0.HAL"
        self.assertIn("E_FURNITURE_BLOCKS_DOOR", codes(validate_building(b, self.rules())))
        b = self.base()
        f = b["floors"][0]["furniture"]
        f[1]["rect"] = list(f[0]["rect"])
        self.assertIn("E_FURNITURE_OVERLAP", codes(validate_building(b, self.rules())))

    def test_unreachable_container_rejected(self):
        b = self.base()
        f = b["floors"][0]
        # wall in the medicine cabinet (11,7) with crates on its only free neighbours
        for n, cell in enumerate([(10, 7), (10, 6), (9, 7), (9, 6), (8, 6), (8, 7), (7, 7), (7, 5), (8, 5), (9, 5)]):
            f["furniture"].append({"id": f"neg.H01.f0.x{n}", "type": "crate", "room": "neg.H01.f0.BAT", "rect": [*cell, 1, 1],
                                   "height_m": 0.5, "container": True})
        found = codes(validate_building(b, self.rules()))
        self.assertTrue({"E_UNREACHABLE_FURNITURE", "E_FURNITURE_BLOCKS_DOOR", "E_UNREACHABLE_CELL"} & found, found)


class T12to13TerrainAndChunks(unittest.TestCase):
    def test_export_verifies_and_seams_match_at_several_chunk_sizes(self):
        w = Cached.world("w04_demo_suburb")
        rep = validate_world(w)
        for size in (8, 16, 24):
            with tempfile.TemporaryDirectory() as tmp:
                export_world(w, rep, Path(tmp), size)
                _, _, problems = verify_export(tmp)
                self.assertEqual(problems, [], f"chunk {size}")

    def test_tampered_chunk_detected(self):
        w = Cached.world("w04_demo_suburb")
        with tempfile.TemporaryDirectory() as tmp:
            export_world(w, validate_world(w), Path(tmp))
            path = Path(tmp) / "chunks/chunk_1_1.json"
            data = json.loads(path.read_text())
            row = data["terrain_rows"][0]
            data["terrain_rows"][0] = ("w" if row[0] != "w" else "g") + row[1:]
            path.write_text(json.dumps(data))
            _, _, problems = verify_export(tmp)
            self.assertTrue(any("hash mismatch" in p for p in problems))

    def test_water_banking_rule(self):
        grid = {(0, 0): "water", (1, 0): "asphalt", (0, 1): "grass"}
        self.assertTrue(adjacency_errors(grid))
        rural = Cached.world("rural")
        self.assertEqual(adjacency_errors(rural["terrain"]), [])
        self.assertIn("field", {t for t in rural["terrain"].values()})


class T14to16References(unittest.TestCase):
    def test_bad_cross_reference_detected(self):
        w = Cached.world("w04_demo_suburb")
        w["buildings"][0]["floors"][0]["furniture"][0]["room"] = "ll.nowhere"
        self.assertIn("no_invalid_cross_references", failed(validate_world(w)))

    def test_catalog_has_required_archetypes(self):
        c = catalog()
        self.assertEqual(len(c["archetypes"]), 60)
        for p in c["programs"].values():
            self.assertIn(p["archetype_id"], c["archetypes"])
        broken = copy.deepcopy(c)
        broken["programs"]["house_small"]["archetype_id"] = "not_an_archetype"
        with self.assertRaises(GenerationError) as ctx:
            validate_catalog(broken)
        self.assertEqual(ctx.exception.code, "E_MISSING_ARCHETYPE")

    def test_reload_preserves_identities(self):
        w = Cached.world("lab_a_street")
        with tempfile.TemporaryDirectory() as tmp:
            m = export_world(w, validate_world(w), Path(tmp))
            _, loaded, _ = load_export(tmp)
        def ids(world):
            out = []
            for b in world["buildings"]:
                for f in b["floors"]:
                    out += [r["id"] for r in f["rooms"]] + [d["id"] for d in f["doors"]] + [i["id"] for i in f["furniture"]]
            return out + [p["id"] for p in world["props"]] + [l["id"] for l in world["lots"]]
        self.assertEqual(ids(w), ids(loaded))
        self.assertEqual(m["world_seed"], 20261107)
        self.assertTrue(all(i.startswith("ll.") for i in ids(loaded)))

    def test_lab_a_fixtures_frozen(self):
        lock = load_json(LOCK)
        for fx in FIXTURES:
            self.assertEqual(sha256(dumps(B.fixture_building(fx, f"lab.{fx}"))), lock[fx], f"{fx} changed; fixtures are immutable")


class T17to18Rejection(unittest.TestCase):
    def test_malformed_recipes_rejected(self):
        good = recipe("w04_demo_suburb")
        cases = {"E_RECIPE_SCHEMA": {"schema": "nope"}, "E_RECIPE_SEED": {"world_seed": -4},
                 "E_RECIPE_STYLE": {"style": "atlantis"}, "E_RECIPE_BLOCKS": {"blocks": [0, 9]},
                 "E_UNKNOWN_PROGRAM": {"lot_overrides": {"1": {"program": "castle"}}},
                 "E_UNKNOWN_FIXTURE": {"lot_overrides": {"1": {"fixture": "LAB-X99"}}},
                 "E_RECIPE_OVERRIDE": {"lot_overrides": {"1": {"colour": "red"}}}}
        for code, change in cases.items():
            bad = dict(good, **change)
            with self.assertRaises(GenerationError) as ctx:
                generate_world(bad)
            self.assertEqual(ctx.exception.code, code)
        bad = dict(good)
        del bad["world_id"]
        with self.assertRaises(GenerationError):
            generate_world(bad)
        with self.assertRaises(GenerationError):
            generate_world(["not", "a", "dict"])

    def test_fixture_that_cannot_fit_is_rejected(self):
        bad = recipe("w04_demo_suburb", lot_overrides={"5": {"fixture": "LAB-H03"}})
        with self.assertRaises(GenerationError) as ctx:
            generate_world(bad)
        self.assertEqual(ctx.exception.code, "E_FIXTURE_DOES_NOT_FIT")

    def test_retries_are_bounded(self):
        calls = []
        original = B.STRATEGIES["residential_spine"]
        B.STRATEGIES["residential_spine"] = lambda *a: calls.append(1) or original(*a)
        try:
            with self.assertRaises(GenerationError) as ctx:
                B.generate_building("house_small", "tiny", 1, max_size=(5, 5))
        finally:
            B.STRATEGIES["residential_spine"] = original
        self.assertEqual(ctx.exception.code, "E_LAYOUT_EXHAUSTED")
        self.assertEqual(len(calls), B.MAX_ATTEMPTS)

    def test_impossible_parcel_falls_back_without_crashing(self):
        w = Cached.world("old_town")
        self.assertTrue(all(l["zoning"] in catalog()["programs"] or l["zoning"] == "vacant" for l in w["lots"]))


if __name__ == "__main__":
    unittest.main()
