"""Noncanonical F02 runtime collision proposal for W04/W05 review.

This is an interchange contract, not a Godot scene or approved navigation mesh.
Static walls, floor and stair solids remain separate from movable leaf blockers.
"""
from __future__ import annotations

import json
from geometry import make_plan

STATIC_ROLES = frozenset({"wall", "frame", "floor", "stair"})
DYNAMIC_GROUPS = frozenset({"door_leaf", "window_leaf", "garage_gate"})


def collision_proposal(subject: str) -> dict:
    plan = make_plan(subject)
    static = []
    dynamic = []
    for part in plan.parts:
        item = {
            "part": part.name,
            "center_m": list(part.center),
            "size_m": list(part.size),
            "rotation_rad": list(part.rotation),
        }
        if part.group in DYNAMIC_GROUPS:
            item["default_state"] = "closed"
            item["collision_policy"] = "W05_STATE_DRIVEN_PENDING"
            dynamic.append(item)
        elif part.role in STATIC_ROLES:
            static.append(item)

    portals = []
    for opening in plan.openings:
        portals.append({
            "kind": opening["kind"],
            "wall": opening["wall"],
            "clear_width_m": opening["void_width_m"],
            "vertical_clearance_m": opening["z_range_m"][1] - opening["z_range_m"][0],
            "traversal": "W04_PENDING",
            "state": "W05_PENDING",
        })

    return {
        "schema": "last_light.f02.collision_proposal.v1",
        "status": "NONCANONICAL_CALIBRATION_ONLY",
        "subject": subject,
        "canonical_master_id": None,
        "static_box_colliders": static,
        "dynamic_box_candidates": dynamic,
        "portals": portals,
        "navmesh_baked": False,
        "approved_for_runtime": False,
    }


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("subject", choices=("small_house", "garage", "shopfront", "door_window", "roof_corner"))
    parser.add_argument("--output")
    args = parser.parse_args()
    data = json.dumps(collision_proposal(args.subject), indent=2) + "\n"
    if args.output:
        from pathlib import Path
        Path(args.output).write_text(data)
    else:
        print(data, end="")


if __name__ == "__main__":
    main()
