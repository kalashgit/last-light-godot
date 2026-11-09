"""Independent integrity and contact-sheet QA for real F05 Blender paperdoll frames.

No Golden promotion; source is only admitted to a candidate build after all
160 original Blender-rendered frames and editable source signatures pass.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageDraw

HEADING_ORDER = (
    "front", "front_right", "right", "back_right",
    "back", "back_left", "left", "front_left",
)
ITEMS = (
    ("body", "base"), ("pants", "jeans"),
    ("shirt", "green_shirt"), ("shirt", "blue_shirt"),
    ("backpack", "pack"),
)
CLIPS = {"idle": 1, "walk": 3}


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as inp:
        for part in iter(lambda: inp.read(1024 * 1024), b""):
            h.update(part)
    return h.hexdigest()


def verify(root: Path, contact: bool = True) -> dict:
    root = root.resolve()
    data = json.loads((root / "manifest.json").read_text())
    if (data.get("schema") != "last-light.paperdoll.frames.v1"
            or data.get("rig") != "ll_biped_v1"
            or data.get("tile_px") != [80, 40]
            or data.get("golden_approved") is not False):
        raise ValueError("F05 invalid candidate source contract")
    if data["directions"] != list(HEADING_ORDER):
        raise ValueError("F05 noncanonical directional order")
    if data["frame_size"] != [128, 160]:
        raise ValueError("unexpected F05 sprite cell")
    if len(data["pivot"]) != 2 or not (0 <= data["pivot"][0] <= 128
                                       and 0 <= data["pivot"][1] <= 160):
        raise ValueError("clipped world-foot pivot")
    if {key: value["frames"] for key, value in data["animations"].items()} != CLIPS:
        raise ValueError("F05 missing animation clips")
    expected_count = len(HEADING_ORDER) * sum(CLIPS.values()) * len(ITEMS)
    if len(data["frames"]) != expected_count:
        raise ValueError("incomplete Blender frame count")
    entries = {}
    opaque = 0
    for record in data["frames"]:
        key = (record["slot"], record["item_id"], record["animation"],
               record["direction"], record["frame"])
        if key in entries:
            raise ValueError("duplicate Blender frame")
        if (record["slot"], record["item_id"]) not in ITEMS:
            raise ValueError("unknown F05 clothing item")
        if (record["animation"] not in CLIPS
                or record["direction"] not in HEADING_ORDER
                or not isinstance(record["frame"], int)
                or record["frame"] not in range(CLIPS[record["animation"]])):
            raise ValueError("invalid Blender direction/frame")
        rel = Path(record["file"])
        path = (root / rel).resolve()
        if rel.is_absolute() or path.suffix != ".png" or not path.is_relative_to(root):
            raise ValueError("unsafe F05 render path")
        if sha256(path) != record["sha256"]:
            raise ValueError("F05 PNG hash mismatch")
        with Image.open(path) as image:
            if image.format != "PNG" or image.mode != "RGBA" or image.size != (128, 160):
                raise ValueError("F05 PNG dimensions or alpha invalid")
            box = image.getchannel("A").getbbox()
            if not box:
                raise ValueError("blank Blender geometry render")
            if box[0] < 2 or box[1] < 2 or box[2] > 126 or box[3] > 158:
                raise ValueError("3D silhouette clipping at frame edge " + str(key))
            opaque += 1
        entries[key] = path
    for slot, item in ITEMS:
        for clip, count in CLIPS.items():
            for heading in HEADING_ORDER:
                for frame in range(count):
                    if (slot, item, clip, heading, frame) not in entries:
                        raise ValueError("missing actual 3D render")

    provenance = data.get("provenance", {}).get("actual_editable_sources", {})
    for field, expected in (("blend", b"BLENDER"), ("glb", b"glTF")):
        rel = Path(provenance[field])
        path = (root / rel).resolve()
        if not path.is_relative_to(root) or not path.is_file():
            raise ValueError("editable source missing or unsafe")
        if path.open("rb").read(len(expected)) != expected:
            raise ValueError("editable source header invalid")
        if sha256(path) != provenance[field + "_sha256"]:
            raise ValueError("editable source hash mismatch")

    report = {
        "status": "TECHNICAL_CANDIDATE_NOT_GOLDEN",
        "asset_id": data["asset_id"],
        "native_blend": True,
        "native_glb": True,
        "original_render_frames": opaque,
        "camera_pivot_px": data["pivot"],
        "headings": len(HEADING_ORDER),
        "distinct_garments": 2,
        "golden_approved": False,
    }
    if contact:
        # Preview-only composited contact sheets; never become production art.
        # Two independent original shirt geometry variants must both receive
        # eight-direction human visual QA, not merely API/sheet-size checks.
        w, h, scale = 128, 160, 2
        for garment in (ITEMS[2], ITEMS[3]):
            contact_sheet = Image.new("RGB", (4*w*scale, 2*(h*scale + 24)), (58, 61, 62))
            draw = ImageDraw.Draw(contact_sheet)
            for i, heading in enumerate(HEADING_ORDER):
                composed = Image.new("RGBA", (w, h), (0, 0, 0, 0))
                # Match native Godot front/back backpack depth order.
                order = ((ITEMS[4], ITEMS[0], ITEMS[1], garment)
                         if heading in ("front", "front_right", "front_left")
                         else (ITEMS[0], ITEMS[1], garment, ITEMS[4]))
                for slot, item in order:
                    with Image.open(entries[(slot, item, "idle", heading, 0)]) as layer:
                        composed.alpha_composite(layer)
                bg = Image.new("RGBA", (w, h), (78, 80, 79, 255))
                bg.alpha_composite(composed)
                x = (i % 4)*w*scale
                y = (i // 4)*(h*scale + 24)
                contact_sheet.paste(bg.convert("RGB").resize((w*scale,h*scale), Image.Resampling.NEAREST), (x,y))
                draw.text((x+4, y+h*scale+3), heading, fill=(240, 234, 220))
            label = "qa_contact_8directions.png" if garment[1] == "green_shirt" else "qa_contact_blue_shirt_8directions.png"
            contact_sheet.save(root / label)
    (root / "qa_report.json").write_text(json.dumps(report, sort_keys=True, indent=2) + "\n")
    print("LL_F05_ORIGINAL_LAYERS_QA_PASS", json.dumps(report, sort_keys=True))
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--skip-contact", action="store_true")
    args = parser.parse_args()
    verify(args.source, contact=not args.skip_contact)
