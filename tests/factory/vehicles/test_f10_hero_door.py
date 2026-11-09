"""Technical animation audit; does not grant visual/engine approval."""
import json
import sys
from pathlib import Path
from PIL import Image


def audit(raw):
    manifest=json.loads((raw/"manifest.json").read_text())
    assert manifest["canonical_master_id"] is None
    assert manifest["status"]=="EXPERIMENTAL_DRIVER_DOOR_NOT_APPROVED"
    assert manifest["cabin_opening"]=="separated_body_surface_with_recessed_floor_and_fixed_seat"
    assert "inner_card" in manifest["moving_door_parts"]
    frames=manifest["frames"]
    assert [f["angle_deg"] for f in frames]==[0,22,44,66]
    assert [f["duration_ms"] for f in frames]==[100]*4
    assert manifest["blender_keyframes"]==[1,2,3,4,5]
    assert manifest["blender_fps"]==10
    assert len({tuple(f["pivot_xyz_m"]) for f in frames})==1
    assert len({tuple(f["fixed_world_pivot_px"]) for f in frames})==1
    assert (raw/"hero_front_door_calibration.blend").stat().st_size>1024
    for frame in frames:
        with Image.open(raw/frame["png"]) as image:
            assert image.mode=="RGBA"
            assert image.getchannel("A").getbbox()
    print("F10_HERO_DOOR_TECHNICAL_PASS",len(frames))


if __name__=="__main__":
    audit(Path(sys.argv[1]))
