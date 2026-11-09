#!/usr/bin/env python3
"""LAST LIGHT W02: check render outputs against the gameplay presentation contract.

Stdlib only. Reads, never writes. Fail-closed: anything unproven is a finding.

Accepted inputs (auto-detected):
  * F12 render manifest (schema_version 1, "frames" with clip/direction/frame/duration_ms)
  * W01 fixture manifest from tests/godot_fixture/prepare_fixture.py ("cases")
  * V2 asset package (schema_version 2, "package_id") -> identity binding check only

This checks GAMEPLAY compatibility (event markers, timing, directions, identity).
It does not check art quality, pixels, A00 rights, W09 review, founder Golden
approval or the V2 approval ledger; those stay with their owners and validators.

Usage:
  python tools/gameplay_contract/check_presentation.py MANIFEST --subject player
  python tools/gameplay_contract/check_presentation.py fixture_manifest.json
  python tools/gameplay_contract/check_presentation.py v2_package.json --mode production
Exit codes: 0 PASS, 2 BLOCKED / not bindable / out of scope, 1 invalid input.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONTRACT = ROOT / "data/contracts/w02_gameplay_presentation_v1.json"
DEFAULT_RULES = ROOT / "data/gameplay_rules.json"
CATALOGS = (ROOT / "data/survival_items.json", ROOT / "data/golden40_items.json")
# W01 fixture subjects (PR #53) -> W02 contract subject. Others are not gameplay subjects.
FIXTURE_SUBJECTS = {"fridge": "container"}
FIXTURE_CLIP_NAMES = {"fridge": "freezer_open", "cube": "cube_static"}
NOT_VERIFIED = ["pixels/art quality", "A00 rights and live identity", "W09 review",
                "founder Golden approval", "V2 approval ledger", "Godot runtime", "iPhone/Xogot"]


class InvalidInput(ValueError):
    pass


def load_json(path: Path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise InvalidInput(f"{path}: {exc}") from exc


def rule_value(rules: dict, dotted: str) -> float:
    node = rules
    for part in dotted.split("."):
        if not isinstance(node, dict) or part not in node:
            raise InvalidInput(f"contract references missing rule {dotted}")
        node = node[part]
    if isinstance(node, bool) or not isinstance(node, (int, float)) or not math.isfinite(node):
        raise InvalidInput(f"rule {dotted} is not a finite number")
    return float(node)


def load_catalog() -> dict:
    items = {}
    for path in CATALOGS:
        data = load_json(path)
        for record in data.get("items", []):
            items[record["id"]] = record
    return items


def normalize_f12(data: dict) -> dict:
    """F12 render manifest -> {clip: {direction: [frame dicts sorted]}} plus metadata."""
    frames = data.get("frames")
    if not isinstance(frames, list) or not frames:
        raise InvalidInput("manifest has no frames")
    clips: dict = {}
    for frame in frames:
        if not isinstance(frame, dict):
            raise InvalidInput("frame must be an object")
        clip, direction, index, duration = (frame.get("clip"), frame.get("direction"),
                                            frame.get("frame"), frame.get("duration_ms"))
        if not isinstance(clip, str) or type(direction) is not int or type(index) is not int:
            raise InvalidInput("frame needs clip/direction/frame")
        if type(duration) is not int or duration <= 0:
            raise InvalidInput(f"{clip}: invalid duration_ms")
        clips.setdefault(clip, {}).setdefault(direction, []).append(
            {"frame": index, "duration_ms": duration, "sockets": frame.get("sockets")})
    for per_dir in clips.values():
        for direction in per_dir:
            per_dir[direction].sort(key=lambda f: f["frame"])
    events = data.get("events", [])
    if not isinstance(events, list):
        raise InvalidInput("events must be a list")
    clip_meta = data.get("clips", {})
    if not isinstance(clip_meta, dict):
        raise InvalidInput("clips must be an object")
    return {"clips": clips, "events": events, "clip_meta": clip_meta,
            "direction_count": data.get("direction_count"),
            "production_status": data.get("production_status"),
            "canonical_master_id": data.get("canonical_master_id")}


def check_actor(norm: dict, spec: dict, rules: dict) -> list:
    findings = []
    clips, events = norm["clips"], norm["events"]
    min_dirs = int(spec.get("min_directions", 1))
    contract_clips = spec["clips"]
    for name in clips:
        if name not in contract_clips:
            findings.append(f"clip '{name}' is not in the W02 contract (W07 must name it)")
    for name, clip in contract_clips.items():
        gameplay_events = clip.get("events", [])
        if name not in clips:
            if gameplay_events:
                findings.append(f"clip '{name}' missing; it carries gameplay event(s) "
                                + ", ".join(e["name"] for e in gameplay_events))
            continue
        per_dir = clips[name]
        if len(per_dir) < min_dirs:
            findings.append(f"{name}: {len(per_dir)} direction(s), contract needs {min_dirs}")
        meta = norm["clip_meta"].get(name, {})
        if gameplay_events and meta.get("loop") is not False:
            findings.append(f"{name}: carries gameplay events so must declare loop=false")
        limit_ms = None
        if "max_duration_rule" in clip:
            limit_ms = rule_value(rules, clip["max_duration_rule"]) * 1000.0
        elif "max_duration_rule_sum" in clip:
            limit_ms = sum(rule_value(rules, r) for r in clip["max_duration_rule_sum"]) * 1000.0
        if limit_ms is not None:
            for direction, frames in per_dir.items():
                total = sum(f["duration_ms"] for f in frames)
                if total > limit_ms + 0.5:
                    findings.append(f"{name} dir {direction}: {total} ms exceeds gameplay limit "
                                    f"{limit_ms:.0f} ms (a new action could start mid-clip)")
                    break
        speed_rule = clip.get("ground_speed_rule")
        if speed_rule and "root_motion_m_per_cycle" in meta:
            cycle_s = sum(f["duration_ms"] for f in next(iter(per_dir.values()))) / 1000.0
            visual = float(meta["root_motion_m_per_cycle"]) / cycle_s
            target = rule_value(rules, speed_rule)
            if abs(visual - target) > target * 0.10:
                findings.append(f"{name}: root motion {visual:.2f} m/s vs gameplay {target:.2f} m/s "
                                "(foot sliding beyond 10%)")
        for forbidden in clip.get("forbidden_events", []):
            if any(e.get("clip") == name and e.get("name") == forbidden for e in events):
                findings.append(f"{name}: forbidden gameplay event '{forbidden}'")
        for event in gameplay_events:
            findings.extend(check_event(name, event, per_dir, events, rules))
        allowed = {e["name"] for e in gameplay_events} | set(clip.get("presentation_events", []))
        for e in events:
            if e.get("clip") == name and e.get("name") not in allowed \
                    and e.get("name") not in clip.get("forbidden_events", []):
                findings.append(f"{name}: unknown event '{e.get('name')}' (not approved by W02)")
    return findings


def check_event(clip_name, event, per_dir, events, rules) -> list:
    findings = []
    target_ms = rule_value(rules, event["at_rule"]) * 1000.0 if "at_rule" in event else None
    for direction, frames in per_dir.items():
        hits = [e for e in events if e.get("clip") == clip_name and e.get("name") == event["name"]
                and e.get("direction", direction) == direction]
        if len(hits) != 1:
            findings.append(f"{clip_name} dir {direction}: '{event['name']}' appears "
                            f"{len(hits)} time(s), needs exactly once")
            continue
        index = hits[0].get("frame")
        positions = [f["frame"] for f in frames]
        if index not in positions:
            findings.append(f"{clip_name} dir {direction}: '{event['name']}' on missing frame {index}")
            continue
        if target_ms is not None:
            start = sum(f["duration_ms"] for f in frames if f["frame"] < index)
            width = next(f["duration_ms"] for f in frames if f["frame"] == index)
            if abs(start - target_ms) > width:
                findings.append(f"{clip_name} dir {direction}: '{event['name']}' at {start} ms, "
                                f"gameplay resolves at {target_ms:.0f} ms (±{width} ms)")
    return findings


def check_item(norm: dict, item_id: str, contract: dict, catalog: dict) -> list:
    findings = []
    if item_id not in catalog:
        return [f"item '{item_id}' is not a gameplay item id"]
    spec = contract["items"]
    roles = spec["roles_by_kind"].get(catalog[item_id].get("kind"), ["inventory_icon", "world_ground"])
    for role in roles:
        if role not in norm["clips"]:
            findings.append(f"{item_id}: missing role clip '{role}'")
    held = norm["clips"].get("held")
    if held is not None:
        if len(held) < int(spec["held_min_directions"]):
            findings.append(f"{item_id}: held has {len(held)} directions, needs {spec['held_min_directions']}")
        for direction, frames in held.items():
            for frame in frames:
                sockets = frame.get("sockets") or {}
                missing = [s for s in spec["held_sockets"] if s not in sockets]
                if missing:
                    findings.append(f"{item_id}: held dir {direction} frame {frame['frame']} "
                                    f"missing sockets {missing}")
                    break
    return findings


def identity_findings(canonical, mode, subject, catalog) -> list:
    if mode != "production":
        return []
    if not canonical:
        return ["production mode needs an A00 canonical_master_id (calibration output cannot bind)"]
    if subject.startswith("item:") and canonical != subject[5:]:
        return [f"canonical_master_id {canonical} does not match gameplay item {subject[5:]}"]
    if canonical.startswith("ll_golden_"):
        return [f"{canonical} is a Golden 40 prototype icon, not an A00 canonical master"]
    return []


def check_f12(data, subject, mode, contract, rules, catalog) -> dict:
    norm = normalize_f12(data)
    if mode == "production" and norm["production_status"] != "A00_VERIFIED_SOURCE":
        findings = ["production mode needs production_status A00_VERIFIED_SOURCE"]
    else:
        findings = []
    findings += identity_findings(norm["canonical_master_id"], mode, subject, catalog)
    if subject.startswith("item:"):
        findings += check_item(norm, subject[5:], contract, catalog)
    elif subject in contract["actors"]:
        findings += check_actor(norm, contract["actors"][subject], rules)
    elif subject in contract["objects"]:
        findings += check_actor(norm, contract["objects"][subject], rules)
    else:
        raise InvalidInput(f"unknown subject {subject}")
    return {"status": "BLOCKED" if findings else "PASS_GAMEPLAY_CONTRACT", "subject": subject,
            "mode": mode, "findings": findings, "not_verified": NOT_VERIFIED}


def check_fixture(data, mode, contract, rules, catalog) -> dict:
    cases = data.get("cases")
    if not isinstance(cases, dict) or not cases:
        raise InvalidInput("fixture manifest has no cases")
    results = {}
    for name, case in sorted(cases.items()):
        subject = FIXTURE_SUBJECTS.get(name)
        if subject is None:
            results[name] = {"status": "OUT_OF_W02_SCOPE", "findings": [
                "no gameplay subject maps to this calibration case"]}
            continue
        frames = []
        for entry in case.get("frames", []):
            frames.append({"clip": FIXTURE_CLIP_NAMES.get(name, "unnamed"),
                           "direction": int(entry["heading"]), "frame": int(entry["source_frame"]),
                           "duration_ms": int(entry["duration_ms"])})
        f12_like = {"frames": frames, "events": case.get("events", []), "clips": case.get("clips", {}),
                    "production_status": data.get("approval_status"),
                    "canonical_master_id": case.get("canonical_master_id")}
        result = check_f12(f12_like, subject, mode, contract, rules, catalog)
        results[name] = {"status": result["status"], "subject": subject, "findings": result["findings"]}
    blocked = any(r["status"] != "PASS_GAMEPLAY_CONTRACT" for r in results.values())
    return {"status": "BLOCKED" if blocked else "PASS_GAMEPLAY_CONTRACT", "mode": mode,
            "cases": results, "not_verified": NOT_VERIFIED}


def check_package(data, mode, catalog) -> dict:
    canonical = data.get("canonical_master_id")
    stage = data.get("stage")
    if stage == "CALIBRATION" or not canonical:
        return {"status": "NOT_BINDABLE_CALIBRATION", "package_id": data.get("package_id"),
                "findings": ["calibration package has no canonical id; it may only be shown in "
                             "isolated fixtures, never bound to a gameplay item or object"],
                "not_verified": NOT_VERIFIED}
    findings = []
    if canonical.startswith("ll_golden_"):
        findings.append(f"{canonical} is a Golden 40 prototype icon, not an A00 canonical master")
    elif canonical not in catalog:
        findings.append(f"{canonical} has no W02 gameplay definition (presentation-only object or "
                        "missing data/survival_items.json entry)")
    return {"status": "BLOCKED" if findings else "BINDABLE_IDENTITY_ONLY", "package_id": data.get("package_id"),
            "canonical_master_id": canonical, "stage": stage, "findings": findings,
            "not_verified": NOT_VERIFIED + ["run validate_package.py for hashes and approvals"]}


def run(manifest: Path, subject, mode, contract_path, rules_path) -> dict:
    data = load_json(manifest)
    if not isinstance(data, dict):
        raise InvalidInput("manifest must be an object")
    contract = load_json(contract_path)
    rules = load_json(rules_path)
    if contract.get("schema_version") != 1 or contract.get("owner") != "W02":
        raise InvalidInput("unexpected contract")
    catalog = load_catalog()
    if data.get("schema_version") == 2 and "package_id" in data:
        return check_package(data, mode, catalog)
    if "cases" in data:
        return check_fixture(data, mode, contract, rules, catalog)
    if not subject:
        raise InvalidInput("--subject is required for an F12 render manifest")
    return check_f12(data, subject, mode, contract, rules, catalog)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--subject", help="player | infected | container | item:<gameplay id>")
    parser.add_argument("--mode", choices=("fixture", "production"), default="fixture")
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--rules", type=Path, default=DEFAULT_RULES)
    args = parser.parse_args(argv)
    try:
        result = run(args.manifest, args.subject, args.mode, args.contract, args.rules)
    except InvalidInput as exc:
        print(json.dumps({"status": "INVALID", "reason": str(exc)}))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] in ("PASS_GAMEPLAY_CONTRACT", "BINDABLE_IDENTITY_ONLY") else 2


if __name__ == "__main__":
    sys.exit(main())
