"""Measured local-space anchors for the noncanonical F10 flat hatchback.

These are art proposals, never gameplay contracts or valid mechanical rigs.
Origin is the fixed sprite/world pivot; +X is the hood, Z is up.
"""
import argparse
import json
from pathlib import Path

from hero_profile import L, W, H, WB, R


def propose():
    sockets = {
        "ground_center": [0, 0, 0],
        "front_axle": [WB / 2, 0, R],
        "rear_axle": [-WB / 2, 0, R],
        "hood_hinge": [1.05, 0, 0.97],
        "rear_hatch_hinge": [-1.36, 0, 1.475],
        "engine_access": [1.45, 0, 0.79],
        "cargo_access": [-1.80, 0, 0.58],
        "fuel_port": [-1.22, -0.74, 0.77],
        "driver_seat_proposal": [0.22, -0.28, 0.52],
    }
    for side, suffix in ((-1, "L"), (1, "R")):
        # Door panels do not yet move. Positions are hinge-design starting points.
        y = side * .71
        sockets[f"front_door_hinge_{suffix}"] = [0.97, y, 0.94]
        sockets[f"front_door_access_{suffix}"] = [0.40, side * .86, 0.91]
        sockets[f"rear_door_hinge_{suffix}"] = [-0.36, y, 0.94]
        sockets[f"rear_door_access_{suffix}"] = [-0.47, side * .86, 0.91]
        for axle_name, x in (("front", WB / 2), ("rear", -WB / 2)):
            sockets[f"{axle_name}_wheel_hub_{suffix}"] = [x, side * .705, R]
    return {
        "schema_version": 1,
        "asset_id": "NONCANONICAL_F10_HERO_HATCHBACK_V2",
        "canonical_master_id": None,
        "status": "ART_SOCKET_PROPOSAL_NOT_ENGINE_ACCEPTED",
        "coordinate_system": "x_forward_y_right_z_up_m",
        "dimensions_m": [L, W, H],
        "wheelbase_m": WB,
        "wheel_radius_m": R,
        "collision_proposal_m": [L * .98, W * .96],
        "animation_state": "NO_VALIDATED_PANEL_RIG",
        "reviews_required": ["W01", "W05", "W07", "W09"],
        "sockets": {k: [round(v, 4) for v in xyz] for k, xyz in sockets.items()},
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(propose(), indent=2) + "\n")
    print("F10_HERO_SOCKETS_PROPOSED", len(propose()["sockets"]))
