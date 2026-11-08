"""Validate actual Blender mechanical calibration exports, not Golden approval."""
import json
import sys
from pathlib import Path


def verify(folder):
    data=json.loads((folder/"manifest.json").read_text())
    assert data["canonical_master_id"] is None
    assert data["status"]=="PANEL_OVERLAY_CALIBRATION_NOT_GOLDEN_NOT_GODOT_INTEGRATED"
    assert data["visual_qa"]=="REQUIRES_MANUAL_REVIEW_NOT_AUTOMATICALLY_PASSED"
    assert set(data["aperture_faces_removed"])=={"door","hood","rear"}
    assert all(n>0 for n in data["aperture_faces_removed"].values())
    expected={"front_left_door_open":64,"hood_open":-48,"trunk_open":58}
    assert len(data["clips"])==len(expected)
    for item in data["clips"]:
        assert item["clip"] in expected
        assert item["frames"]==4 and item["ms_per_frame"]==100
        assert abs(item["final_angle_deg"]-expected[item["clip"]])<.01
        source=folder/item["blend"]
        assert source.is_file() and source.stat().st_size>1024
        if item["rendered_frames"]:
            for i in range(item["frames"]):
                assert (folder/item["clip"]/f"frame_{i:02}.png").is_file()
    print("F10_HINGE_TRANSFORM_PASS_VISUAL_UNAPPROVED",data["model"],len(data["clips"]))


if __name__=="__main__":
    for path in sys.argv[1:]:verify(Path(path))
