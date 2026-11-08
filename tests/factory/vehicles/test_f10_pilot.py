"""Technical-only audit for noncanonical F10 calibration artifacts.

Usage: python3 tests/factory/vehicles/test_f10_pilot.py build/f10/raw_v3 build/f10/packed_v3
Passing does not confer A00 identity, Golden visual or Godot approval.
"""
import hashlib
import json
import sys
from pathlib import Path
from PIL import Image


def audit(raw_root: Path, atlas_root: Path):
    result=[]
    for folder in sorted(raw_root.iterdir()):
        if not folder.is_dir() or not (folder/"manifest.json").exists():
            continue
        raw=json.loads((folder/"manifest.json").read_text())
        packed_dir=atlas_root/folder.name
        packed=json.loads((packed_dir/"manifest.json").read_text())
        assert raw["directions"]==packed["heading_count"]==16
        assert [row["index"] for row in raw["frames"]]==list(range(16))
        assert [row["angle_deg"] for row in raw["frames"]]==[22.5*i for i in range(16)]
        assert len({tuple(row["fixed_world_pivot_px"]) for row in raw["frames"]})==1
        assert (folder/"source_calibration.blend").stat().st_size>1024
        assert (folder/"source_calibration.glb").stat().st_size>1024
        atlas=packed_dir/packed["atlas"]
        pixel=packed_dir/packed["pixel_refined_atlas"]
        with Image.open(atlas) as a, Image.open(pixel) as p:
            assert a.mode==p.mode=="RGBA"
            assert a.size==p.size
            assert a.getchannel("A").tobytes()==p.getchannel("A").tobytes()
            assert a.getchannel("A").getextrema()==(0,255)
        for i in range(16):
            assert (packed_dir/f"heading_{i:02}.png").exists()
        assert hashlib.sha256(atlas.read_bytes()).hexdigest()==packed["sha256"]
        result.append((raw["model"],packed["heading_count"],packed["cell_px"]))
    assert result,"No complete F10 pilot artifacts found"
    for item in result:
        print("F10_TECHNICAL_PILOT_PASS",*item)
    print("F10_NONCANONICAL_CANDIDATES_AUDITED",len(result))


if __name__=="__main__":
    if len(sys.argv)!=3:
        raise SystemExit("usage: test_f10_pilot.py RAW_ROOT ATLAS_ROOT")
    audit(Path(sys.argv[1]),Path(sys.argv[2]))
