"""F11-style PBR map and F12 CAL-01 projection/PNG gate for an unapproved F01.

This validates *candidate technical properties*; it cannot grant art approval.
"""
import argparse
import hashlib
import json
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
    residual = max(abs(measured[i][j] - [[-40, 20], [40, 20]][i][j])
                   for i in range(2) for j in range(2))
    if residual > .001 or abs(data.get("max_absolute_residual_px", 100)) > .001:
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

    report = {"schema_version": 1, "status": "F11_F12_TECHNICAL_PASS_CANDIDATE_ONLY",
              "paired_pbr_materials": materials_count, "f12_angle_count": len(imgs),
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
