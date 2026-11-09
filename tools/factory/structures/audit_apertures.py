"""F02 aperture collision geometry audit (noncanonical, engine independent).

Tests whether any static AABB occupies the center of a walkable portal.
Does not replace Godot physics, agent-radius, or navigation validation.
"""
from __future__ import annotations
import json
from collision_contract import collision_proposal

EPS = 1e-6

def overlaps(a0, a1, b0, b1):
    return a0 < b1 - EPS and b0 < a1 - EPS

def audit_apertures(subject: str, probe_height_m: float = 1.0) -> dict:
    data = collision_proposal(subject)
    failures = []
    tested = 0
    for portal in data["portals"]:
        if portal["kind"] == "window":
            continue
        x, y, axis = portal["wall"]
        # The wide garage portal begins at x and spans three metres.
        along = x + (1.5 if portal["kind"] == "garage" else .5) if axis == "x" else y + .5
        px, py = (along, y) if axis == "x" else (x, along)
        tested += 1
        for part in data["static_box_colliders"]:
            cx, cy, cz = part["center_m"]
            sx, sy, sz = part["size_m"]
            if (overlaps(px, px + EPS * 2, cx - sx/2, cx + sx/2)
                and overlaps(py, py + EPS * 2, cy - sy/2, cy + sy/2)
                and overlaps(probe_height_m, probe_height_m + EPS * 2,
                             cz - sz/2, cz + sz/2)):
                failures.append({"portal": portal["wall"], "blocking_part": part["part"]})
    return {
        "subject": subject,
        "status": "NONCANONICAL_CALIBRATION_ONLY",
        "probe_height_m": probe_height_m,
        "walkable_portals_checked": tested,
        "static_blockers": failures,
        "passed": not failures,
        "godot_physics_verified": False,
    }

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("subject", choices=("small_house", "garage", "shopfront", "door_window", "roof_corner"))
    args = parser.parse_args()
    report = audit_apertures(args.subject)
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report["passed"] else 1)
