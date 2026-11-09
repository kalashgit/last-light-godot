#!/usr/bin/env python3
"""Positive and negative tests for tools/gameplay_contract/check_presentation.py."""
from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/gameplay_contract"))
import check_presentation as cp  # noqa: E402

CONTRACT = json.loads((ROOT / "data/contracts/w02_gameplay_presentation_v1.json").read_text())
RULES = json.loads((ROOT / "data/gameplay_rules.json").read_text())


def clip_frames(clip, count, duration, directions=8):
    return [{"clip": clip, "direction": d, "frame": i, "duration_ms": duration}
            for d in range(directions) for i in range(count)]


def every_dir(clip, name, frame, directions=8):
    return [{"clip": clip, "name": name, "frame": frame, "direction": d} for d in range(directions)]


def good_player():
    frames = (clip_frames("idle", 4, 180) + clip_frames("walk", 8, 105) + clip_frames("attack", 5, 90)
              + clip_frames("shove", 4, 100) + clip_frames("interact", 6, 80) + clip_frames("death", 7, 125))
    events = (every_dir("attack", "attack_contact", 2) + every_dir("shove", "shove_contact", 1)
              + every_dir("interact", "interact_commit", 3))
    clips = {name: {"loop": False} for name in ("attack", "shove", "interact", "death")}
    clips["walk"] = {"loop": True, "root_motion_m_per_cycle": 2.2 * 0.84}
    return {"schema_version": 1, "production_status": "CALIBRATION_ONLY", "direction_count": 8,
            "frames": frames, "events": events, "clips": clips}


def good_infected():
    # Wind-up 0.4 s: contact on frame 4 when frames are 100 ms (starts at 400 ms).
    frames = clip_frames("attack", 12, 100)
    return {"schema_version": 1, "production_status": "CALIBRATION_ONLY", "frames": frames,
            "events": every_dir("attack", "attack_contact", 4), "clips": {"attack": {"loop": False}}}


def fixture_replica():
    """Same shape prepare_fixture.py writes for PR #53 (hashes/pivots omitted: not read here)."""
    def case(count, headings, poses):
        return {"frames": [{"heading": h, "source_frame": p, "duration_ms": 100, "rect": [0, 0, 384, 384]}
                           for h in headings for p in poses][:count]}
    return {"schema_version": 1, "approval_status": "CALIBRATION_ONLY", "logical_tile_px": [80, 40],
            "cases": {"cube": case(1, [0], [1]), "vehicle": case(16, range(16), [1]),
                      "cow": case(16, range(8), [1, 4]), "fridge": case(7, [0], range(1, 8))}}


class CheckerTests(unittest.TestCase):
    def run_check(self, data, subject=None, mode="fixture"):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "m.json"
            path.write_text(json.dumps(data))
            return cp.run(path, subject, mode, cp.DEFAULT_CONTRACT, cp.DEFAULT_RULES)

    def assertBlockedWith(self, result, fragment):
        self.assertEqual(result["status"], "BLOCKED", result)
        self.assertTrue(any(fragment in f for f in result["findings"]), result["findings"])

    def test_contract_rules_resolve(self):
        for actor in list(CONTRACT["actors"].values()) + list(CONTRACT["objects"].values()):
            for clip in actor["clips"].values():
                for key in ("max_duration_rule", "ground_speed_rule"):
                    if key in clip:
                        cp.rule_value(RULES, clip[key])
                for rule in clip.get("max_duration_rule_sum", []):
                    cp.rule_value(RULES, rule)
                for event in clip.get("events", []):
                    if "at_rule" in event:
                        cp.rule_value(RULES, event["at_rule"])

    def test_good_player_passes(self):
        self.assertEqual(self.run_check(good_player(), "player")["status"], "PASS_GAMEPLAY_CONTRACT")

    def test_good_infected_passes(self):
        self.assertEqual(self.run_check(good_infected(), "infected")["status"], "PASS_GAMEPLAY_CONTRACT")

    def test_f05_proposed_attack_is_longer_than_cooldown(self):
        data = good_player()
        data["frames"] = [f for f in data["frames"] if f["clip"] != "attack"] + clip_frames("attack", 6, 85)
        self.assertBlockedWith(self.run_check(data, "player"), "exceeds gameplay limit 500 ms")

    def test_missing_contact_marker(self):
        data = good_player()
        data["events"] = [e for e in data["events"] if not (e["name"] == "attack_contact" and e["direction"] == 3)]
        self.assertBlockedWith(self.run_check(data, "player"), "dir 3: 'attack_contact' appears 0")

    def test_duplicate_contact_marker(self):
        data = good_player()
        data["events"].append({"clip": "attack", "name": "attack_contact", "frame": 3, "direction": 0})
        self.assertBlockedWith(self.run_check(data, "player"), "appears 2 time(s)")

    def test_event_on_missing_frame(self):
        data = good_player()
        data["events"] = [dict(e, frame=99) if e["name"] == "shove_contact" else e for e in data["events"]]
        self.assertBlockedWith(self.run_check(data, "player"), "on missing frame 99")

    def test_looping_event_clip_rejected(self):
        data = good_player()
        data["clips"]["attack"]["loop"] = True
        self.assertBlockedWith(self.run_check(data, "player"), "loop=false")

    def test_missing_gameplay_clip(self):
        data = good_player()
        data["frames"] = [f for f in data["frames"] if f["clip"] != "interact"]
        data["events"] = [e for e in data["events"] if e["clip"] != "interact"]
        self.assertBlockedWith(self.run_check(data, "player"), "clip 'interact' missing")

    def test_too_few_directions(self):
        data = good_player()
        data["frames"] = [f for f in data["frames"] if f["direction"] < 4]
        data["events"] = [e for e in data["events"] if e["direction"] < 4]
        self.assertBlockedWith(self.run_check(data, "player"), "contract needs 8")

    def test_forbidden_death_loot_event(self):
        data = good_player()
        data["events"].append({"clip": "death", "name": "loot_spawn", "frame": 6, "direction": 0})
        self.assertBlockedWith(self.run_check(data, "player"), "forbidden gameplay event 'loot_spawn'")

    def test_unapproved_event_name(self):
        data = good_player()
        data["events"].append({"clip": "walk", "name": "deal_damage", "frame": 1, "direction": 0})
        self.assertBlockedWith(self.run_check(data, "player"), "not approved by W02")

    def test_foot_sliding(self):
        data = good_player()
        data["clips"]["walk"]["root_motion_m_per_cycle"] = 3.0
        self.assertBlockedWith(self.run_check(data, "player"), "foot sliding")

    def test_unknown_clip_name(self):
        data = good_player()
        data["frames"] += clip_frames("swing_heavy", 3, 100)
        self.assertBlockedWith(self.run_check(data, "player"), "not in the W02 contract")

    def test_infected_contact_timing(self):
        data = good_infected()
        data["events"] = every_dir("attack", "attack_contact", 7)
        self.assertBlockedWith(self.run_check(data, "infected"), "gameplay resolves at 400 ms")

    def test_infected_attack_too_long(self):
        data = good_infected()
        data["frames"] = clip_frames("attack", 13, 100)
        self.assertBlockedWith(self.run_check(data, "infected"), "exceeds gameplay limit 1200 ms")

    def test_production_mode_rejects_calibration(self):
        self.assertBlockedWith(self.run_check(good_player(), "player", "production"), "A00_VERIFIED_SOURCE")

    def test_item_roles_sockets_and_identity(self):
        frames = (clip_frames("inventory_icon", 1, 100, 1) + clip_frames("world_ground", 1, 100, 1)
                  + clip_frames("held", 1, 100, 8))
        for f in frames:
            if f["clip"] == "held":
                f["sockets"] = {"grip": [1, 2], "held_item_tip": [3, 4]}
        data = {"schema_version": 1, "production_status": "A00_VERIFIED_SOURCE",
                "canonical_master_id": "ll_tools_claw_hammer", "frames": frames}
        self.assertEqual(self.run_check(data, "item:ll_tools_claw_hammer", "production")["status"],
                         "PASS_GAMEPLAY_CONTRACT")
        self.assertBlockedWith(self.run_check(data, "item:ll_tools_hatchet", "production"), "does not match")
        no_socket = json.loads(json.dumps(data))
        for f in no_socket["frames"]:
            f.pop("sockets", None)
        self.assertBlockedWith(self.run_check(no_socket, "item:ll_tools_claw_hammer"), "missing sockets")
        no_held = dict(data, frames=[f for f in frames if f["clip"] != "held"])
        self.assertBlockedWith(self.run_check(no_held, "item:ll_tools_claw_hammer"), "missing role clip 'held'")
        food = dict(data, canonical_master_id="ll_food_bean_tin", frames=frames[:2])
        self.assertEqual(self.run_check(food, "item:ll_food_bean_tin", "production")["status"],
                         "PASS_GAMEPLAY_CONTRACT")
        golden = dict(data, canonical_master_id="ll_golden_crowbar")
        self.assertBlockedWith(self.run_check(golden, "item:ll_golden_crowbar", "production"), "prototype")

    def test_pr53_fixture_shape(self):
        result = self.run_check(fixture_replica())
        self.assertEqual(result["status"], "BLOCKED")
        for name in ("cube", "vehicle", "cow"):
            self.assertEqual(result["cases"][name]["status"], "OUT_OF_W02_SCOPE")
        fridge = result["cases"]["fridge"]
        self.assertEqual(fridge["subject"], "container")
        joined = " ".join(fridge["findings"])
        self.assertIn("'freezer_open' is not in the W02 contract", joined)
        self.assertIn("clip 'open' missing", joined)

    def test_v2_package_binding(self):
        calibration = {"schema_version": 2, "package_id": "LL-F01-CALIBRATION-FRIDGE-RUN42533683097",
                       "family": "F01", "stage": "CALIBRATION"}
        self.assertEqual(self.run_check(calibration)["status"], "NOT_BINDABLE_CALIBRATION")
        hammer = dict(calibration, stage="GOLDEN_CANDIDATE", canonical_master_id="ll_tools_claw_hammer")
        self.assertEqual(self.run_check(hammer)["status"], "BINDABLE_IDENTITY_ONLY")
        prototype = dict(hammer, canonical_master_id="ll_golden_hand_axe")
        self.assertBlockedWith(self.run_check(prototype), "prototype")
        stranger = dict(hammer, canonical_master_id="ll_household_bucket")
        self.assertBlockedWith(self.run_check(stranger), "no W02 gameplay definition")

    def test_invalid_inputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "bad.json"
            bad.write_text("{not json")
            self.assertEqual(cp.main([str(bad)]), 1)
            no_subject = Path(tmp) / "f12.json"
            no_subject.write_text(json.dumps(good_player()))
            self.assertEqual(cp.main([str(no_subject)]), 1)
            broken = Path(tmp) / "broken.json"
            broken.write_text(json.dumps({"frames": [{"clip": "attack", "direction": 0, "frame": 0, "duration_ms": 0}]}))
            self.assertEqual(cp.main([str(broken), "--subject", "player"]), 1)
            self.assertEqual(cp.main([str(no_subject), "--subject", "player"]), 0)

    def test_gameplay_items_resolve_to_factory_art(self):
        """W02's eight playable items use factory geometry IDs (the shape A00 uses)."""
        manifest = json.loads((ROOT / "assets/generated/factory/manifest.json").read_text())
        art = {o["id"] for o in manifest["objects"]}
        items = json.loads((ROOT / "data/survival_items.json").read_text())["items"]
        for item in items:
            self.assertEqual(item["id"], item["art_id"])
            self.assertIn(item["id"], art)
        golden = json.loads((ROOT / "data/golden40_items.json").read_text())["items"]
        self.assertTrue(all(g["id"].startswith("ll_golden_") and g.get("prototype") is True for g in golden))


if __name__ == "__main__":
    unittest.main(verbosity=1)
