"""Per-asset original state and attachment handoff for Godot artists/programmers.

Pure, deterministic metadata authoring; does not claim physical animation exists.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from tools.foundry_original_23.contract import DEFAULT_MANIFEST, MASTER, check_manifest


def state_delta(name: str) -> dict:
    """An actionable geometry/material/interaction edit, not a clone sprite."""
    table = {
        "loose": ("place original mesh at floor pivot", "pickup"),
        "loose_pair": ("place two independent boots together at floor pivot", "pickup_pair"),
        "dropped": ("rigid-body rest; grip horizontal to contact plane", "pickup"),
        "coiled": ("five rope loops with a visible loose tail", "pickup"),
        "uncoiled": ("replace loops with authored rope spline and two free ends", "deploy_rope"),
        "cut": ("separate physical rope segment with frayed fiber ends", "craft"),
        "equipped": ("bind authored attachment sockets to character skeleton", "unequip"),
        "held": ("bind original hand_grip pivot to hand skeleton", "attack_or_use"),
        "swing": ("tool grip pivot arcs; handle and head remain rigid", "attack"),
        "closed": ("latch fastened; preserve closed original silhouette", "open"),
        "open": ("hinge or flap rotated about authored hinge axis", "close"),
        "opened": ("break seal and reveal independently authored interior", "interact"),
        "sealed": ("intact top seam, lid or blister foil", "break_seal"),
        "folded": ("multiple gauze layers held together", "unfold"),
        "unwrapped": ("unfold fabric and expose underside weave", "use"),
        "used": ("visibly disturbed surface, no source art reuse", "discard"),
        "full": ("full bulge or fill line; intact lid and carrying silhouette", "consume_or_open"),
        "half": ("liquid surface moved to half bottle height", "drink"),
        "empty": ("collapse sack or remove filling; keep original shell", "refill"),
        "empty_core": ("remove tape windings; expose paper ring", "discard"),
        "partially_used": ("reduce fill, tape winding or tablet cells; keep same parent ID", "consume"),
        "partly_used": ("replace filled grain volume with folded sack creases", "consume"),
        "lid_removed": ("move independent lid mesh to side; preserve parent ID", "replace_lid"),
        "written": ("add original procedural ink marks to interior pages", "read"),
        "worn": ("material-driven scuffs near contact points only", "repair"),
        "muddy": ("add boot grime to tread and lower upper only", "clean"),
        "torn": ("split plastic panel near load-bearing ties", "repair"),
        "broken": ("fracture original antler trunk into two endpoints", "craft"),
        "bruised": ("patchy reduced-red subsurface material and indentation", "eat"),
        "rotten": ("localized discoloration and deformation; no new asset ID", "discard"),
        "spoiled": ("localized food discoloration within existing open tin", "discard"),
        "fresh": ("unbroken original fruit geometry and bright shoulder", "eat"),
        "consumed": ("independent bitten core/cut geometry; keep state lineage", "discard"),
        "empty_pair": ("remove both contents, preserve pair carrier", "store"),
    }
    geometry, action = table.get(name, ("author an original variant without changing canonical identity", "interact"))
    return {"state": name, "geometry_or_material_delta": geometry,
            "interaction_hint": action, "visual_qa_required": True,
            "mesh_animation_implemented": False, "godot_binding_implemented": False}


def socket_spec(socket: str, asset: dict) -> dict:
    x, y, z = asset["nominal_dimensions_m"]
    # Parent-relative placement guide. These are *design coordinates*, not
    # verified Godot bone/transform numbers. Per-family F11 must correct them.
    guide = {
        "world_base": (0, 0, 0), "hand_grip": (0, 0, .5),
        "right_hand_grip": (0, 0, .34), "left_hand_grip": (0, 0, .34),
        "spine": (0, .45, .55),
        "left_shoulder": (-.35, .23, .83), "right_shoulder": (.35, .23, .83),
        "shoulder": (.3, .15, .83), "hip": (-.35, .0, .15),
        "torso": (0, .0, .55), "torso_front": (0, -.42, .55),
        "chest_diagonal": (0, -.42, .56), "neck": (0, .0, .91),
        "waist_left": (-.45, 0, .42), "waist_right": (.45, 0, .42),
        "arms": (0, 0, .52), "left_foot": (-.3, 0, .0),
        "right_foot": (.3, 0, .0),
    }
    fx, fy, fz = guide.get(socket, (0, 0, .5))
    return {"socket": socket, "local_position_m_provisional": [round(fx*x, 4), round(fy*y, 4), round(fz*z, 4)],
            "coordinate_frame": "asset_bbox_center_xy_base_z",
            "pivot_and_animation_status": "REQUIRES_F11_F12_AND_GODOT_VALIDATION"}


def build_gameplay(doc: dict) -> dict:
    verdict = check_manifest(doc, MASTER)
    if verdict["errors"]:
        raise ValueError("Cannot derive gameplay contract from untrusted manifest: " + "; ".join(verdict["errors"]))
    return {
        "schema_version": 1, "batch_id": doc["batch_id"],
        "assets": [{
            "asset_id": a["asset_id"], "kind": a["kind"],
            "gameplay_roles": a["gameplay_roles"],
            "state_machine": [state_delta(s) for s in a["states"]],
            "attachment_sockets": [socket_spec(s, a) for s in a["attachment_sockets"]],
            "directional_world_render_spec": a["world"],
            "inventory_icon_spec": a["inventory"],
            "implementation_status": "DESIGNED_NOT_GODOT_TESTED",
            "founder_golden_approved": False,
        } for a in doc["assets"]],
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    result = build_gameplay(json.loads(args.manifest.read_text()))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print("LL_GAMEPLAY_CONTRACTS_CREATED", len(result["assets"]), "GODOT_VALIDATED=0")


if __name__ == "__main__":
    main()
