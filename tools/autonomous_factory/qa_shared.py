"""F11-style PBR map and F12 CAL-01 projection/PNG gate for an unapproved F01.

This validates *candidate technical properties*; it cannot grant art approval.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path

F12_SHA = "eba8e2c6d78bbc41b2de413d176d805b6c288337"


def check_f12_report(data):
    if data.get("schema_version") != 1:
        raise ValueError("F12 report schema mismatch")
    if data.get("status") != "F12_CAL01_WORLD_SCALE_TECHNICAL_CANDIDATE_NOT_GOLDEN":
        raise ValueError("F12 report is not a noncanonical candidate")
    if data.get("f12_pinned_source_sha") != F12_SHA:
        raise ValueError("F12 calibration source SHA not pinned")
    if data.get("founder_approved") is not False or data.get("canonical_promoted") is not False:
        raise ValueError("candidate claims an unauthorized approval")
    if data.get("tile_logical_pixels") != [80, 40]:
        raise ValueError("F12 tile grid mismatch")
    if data.get("target_basis_px") != [[-40, 20], [40, 20]]:
        raise ValueError("F12 target world basis mismatch")
    measured = data.get("measured_basis_px")
    if not isinstance(measured, list) or len(measured) != 2 or any(len(row) != 2 for row in measured):
        raise ValueError("F12 measured world basis missing")
    try:
        deviations = [abs(float(measured[i][j]) - [[-40, 20], [40, 20]][i][j])
                      for i in range(2) for j in range(2)]
        claimed_residual = float(data.get("max_absolute_residual_px", 100))
    except (ValueError, TypeError) as exc:
        raise ValueError("F12 basis contains nonnumeric coordinates") from exc
    if not all(math.isfinite(x) for x in (*deviations, claimed_residual)):
        raise ValueError("F12 report contains nonfinite projection")
    residual = max(deviations)
    if residual > .001 or abs(claimed_residual) > .001:
        raise ValueError(f"F12 basis residual too large: {residual}")
    if data.get("canvas_px") != [256, 256]:
        raise ValueError("F12 canvas mismatch")
    if [entry.get("degrees") for entry in data.get("frames", [])] != [0, 90, 180, 270]:
        raise ValueError("F12 headings incomplete")


def check_pbr(textures):
    # Pillow imported here so pure source/metadata tests need no image dependency.
    from PIL import Image

    names = sorted(p.stem for p in textures.glob("f01_*_basecolor.png"))
    if len(names) != 9:
        raise ValueError(f"F11-style PBR expected nine original F01 materials, got {len(names)}")
    for name in names:
        base = textures / (name + ".png")
        rough = textures / (name.removesuffix("_basecolor") + "_roughness.png")
        if not rough.exists():
            raise ValueError(f"unpaired F01 roughness map: {base.name}")
        with Image.open(base) as b, Image.open(rough) as r:
            if b.mode != "RGBA" or r.mode != "RGBA" or b.size != r.size:
                raise ValueError(f"F11-style PBR map format/size mismatch: {name}")
            if b.size[0] not in (128, 256, 512, 1024) or b.size[0] != b.size[1]:
                raise ValueError(f"unexpected map dimensions: {name}")
            if b.getchannel("A").getextrema() != (255, 255):
                raise ValueError(f"unexpected translucent base map: {name}")
            if r.getchannel("A").getextrema() != (255, 255):
                raise ValueError(f"unexpected roughness alpha: {name}")
            rgb = r.convert("RGB")
            if any(channel.tobytes() != rgb.split()[0].tobytes() for channel in rgb.split()[1:]):
                raise ValueError(f"roughness encoded with inconsistent RGB channels: {name}")
            if not (1 <= rgb.getextrema()[0][0] <= rgb.getextrema()[0][1] <= 254):
                raise ValueError(f"roughness outside physical candidate range: {name}")
    return len(names)


def check_atlas(root, candidate):
    from PIL import Image

    atlas_dir = root / "f12_atlas"
    data = json.loads((atlas_dir / "atlas.json").read_text())
    if data.get("status") != "COMPOSED_NOT_GODOT_APPROVED":
        raise ValueError("F12 specialist atlas has unexpected status")
    if data.get("page_size") != 1024 or data.get("padding") != 2:
        raise ValueError("F12 page packing contract mismatch")
    frames = data.get("frames", [])
    if len(frames) != 4 or sorted(f.get("direction") for f in frames) != [0, 4, 8, 12]:
        raise ValueError("F12 atlas headings incomplete")
    files = {row["degrees"] // 90 * 4: row for row in candidate["frames"]}
    pages = data.get("atlas_files", [])
    if len(pages) != data.get("pages") or not pages:
        raise ValueError("F12 atlas page count mismatch")
    for page_idx, page in enumerate(pages):
        path = atlas_dir / page["file"]
        if hashlib.sha256(path.read_bytes()).hexdigest() != page["sha256"]:
            raise ValueError(f"F12 atlas digest mismatch: {path.name}")
        with Image.open(path) as raw:
            if raw.mode != "RGBA" or raw.size != (1024, 1024):
                raise ValueError("F12 atlas must be 1024px RGBA")
            atlas = raw.copy()
        for frame in (f for f in frames if f["page"] == page_idx):
            fmeta = files[frame["direction"]]
            if fmeta["sha256"] != frame["source_sha256"]:
                raise ValueError("F12 source digest changed after packing")
            x, y, w, h = frame["rect"]
            if (w, h) != (256, 256) or x < 2 or y < 2 or x+w+2 > 1024 or y+h+2 > 1024:
                raise ValueError("F12 atlas frame outside padded page")
            with Image.open(root / "f12_calibrated" / fmeta["file"]) as source:
                if atlas.crop((x, y, x+w, y+h)).tobytes() != source.tobytes():
                    raise ValueError("F12 atlas pixels differ from calibrated source")
    return len(frames), len(pages)


def run(root):
    from PIL import Image, ImageChops
    materials_count = check_pbr(root / "attempt_1" / "textures")
    output = root / "f12_calibrated"
    metadata = json.loads((output / "f12_candidate.json").read_text())
    check_f12_report(metadata)
    imgs = []
    for entry in metadata["frames"]:
        path = output / entry["file"]
        if hashlib.sha256(path.read_bytes()).hexdigest() != entry.get("sha256"):
            raise ValueError(f"F12 image digest mismatch: {path.name}")
        with Image.open(path) as picture:
            if picture.mode != "RGBA" or picture.size != (256, 256):
                raise ValueError(f"F12 image format mismatch: {path.name}")
            image = picture.copy()
        bounds = image.getchannel("A").getbbox()
        if not bounds or min(bounds[0], bounds[1], 256-bounds[2], 256-bounds[3]) < 4:
            raise ValueError(f"F12 candidate clipped or empty: {path.name}")
        imgs.append(image)
    if not any(
        ImageChops.difference(imgs[0].convert("RGB"), other.convert("RGB")).getbbox()
        or ImageChops.difference(imgs[0].getchannel("A"), other.getchannel("A")).getbbox()
        for other in imgs[1:]
    ):
        raise ValueError("F12 candidate headings identical")

    atlas_frames, atlas_pages = check_atlas(root, metadata)
    report = {"schema_version": 1, "status": "F11_F12_TECHNICAL_PASS_CANDIDATE_ONLY",
              "paired_pbr_materials": materials_count, "f12_angle_count": len(imgs),
              "f12_atlas_frames": atlas_frames, "f12_atlas_pages": atlas_pages,
              "f12_world_basis_residual_px": metadata["max_absolute_residual_px"],
              "founder_approved": False, "canonical_promoted": False}
    (root / "shared_quality.json").write_text(json.dumps(report, indent=2) + "\n")
    print("M02_F11_F12_SHARED_TECHNICAL_PASS", json.dumps(report))
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    args = parser.parse_args()
    run(args.root)
