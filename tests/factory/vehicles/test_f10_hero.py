"""F10 hatchback hero technical evidence audit (not a visual approval)."""
import hashlib
import json
import sys
from pathlib import Path
from PIL import Image


def verify(raw_dir,packed_dir):
    src=json.loads((raw_dir/"manifest.json").read_text())
    atlas=json.loads((packed_dir/"manifest.json").read_text())
    assert src["canonical_master_id"] is None
    assert src["status"]=="NONCANONICAL_GEOMETRY_HERO_UNAPPROVED"
    assert len(src["frames"])==16
    assert [f["angle_deg"] for f in src["frames"]]==[22.5*i for i in range(16)]
    assert len({tuple(f["fixed_world_pivot_px"]) for f in src["frames"]})==1
    for name in ("hero_hatchback.blend","hero_hatchback.glb"):
        assert (raw_dir/name).stat().st_size>1024
    original=packed_dir/atlas["atlas"]
    refined=packed_dir/atlas["pixel_refined_atlas"]
    with Image.open(original) as a,Image.open(refined) as b:
        assert a.mode==b.mode=="RGBA" and a.size==b.size
        assert a.getchannel("A").tobytes()==b.getchannel("A").tobytes()
    assert hashlib.sha256(original.read_bytes()).hexdigest()==atlas["sha256"]
    for i in range(16):
        assert (packed_dir/f"heading_{i:02}.png").is_file()
    print("F10_HERO_TECHNICAL_PASS",atlas["heading_count"],atlas["cell_px"])


if __name__=="__main__":
    verify(Path(sys.argv[1]),Path(sys.argv[2]))
