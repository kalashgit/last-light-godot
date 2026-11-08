"""F05 calibration artifact validator. Python stdlib only.

Usage: python tools/actor_factory/f05_validate.py /path/to/f05-cal
Fails closed: no canonical ID, no GLB, invalid PNG, missing bones/sockets/actions,
or an explicit failed export prevents a successful calibration result.
"""
import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path

EXPECTED_BONES = {
    "root", "pelvis", "spine", "chest", "neck", "head",
    *{f"{name}_{side}" for side in ("L", "R") for name in (
        "shoulder", "upper_arm", "forearm", "hand", "thigh", "shin", "foot", "toe"
    )}
}
EXPECTED_SOCKETS = {
    "floor_feet", "hand_R", "hand_L", "backpack", "headwear",
    "waist", "holster", "held_item_tip", "attack_contact", "depth_sort"
}
EXPECTED_CLIPS = {
    "idle", "walk", "run", "sneak", "interact", "attack", "hurt", "death"
}
EXPECTED_FILES = (
    "calibration.png",
    "f05_noncanonical_calibration.blend",
    "f05_noncanonical_calibration.glb",
)

def validate(directory):
    errors = []
    manifest_path = directory / "manifest.json"
    if not manifest_path.is_file():
        return ["Missing manifest.json"]
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return [f"Unreadable manifest: {exc}"]
    if manifest.get("status") != "CALIBRATION_ONLY":
        errors.append("Unexpected release status; calibration must remain noncanonical")
    physique = manifest.get("physique")
    expected_dimensions = {"lean": (1.0, 1.0), "broad": (1.18, 1.12)}
    if physique not in expected_dimensions:
        errors.append("Missing or unsupported physique calibration")
    elif (manifest.get("body_width_factor"), manifest.get("limb_width_factor")) != expected_dimensions[physique]:
        errors.append("Physique dimensions do not match calibration contract")
    if manifest.get("canonical_master_id") is not None:
        errors.append("Noncanonical calibration must not claim a master ID")
    if not EXPECTED_BONES.issubset(set(manifest.get("bones", []))):
        errors.append("Missing required skeleton bones")
    if not EXPECTED_SOCKETS.issubset(set(manifest.get("sockets", []))):
        errors.append("Missing required attachment sockets")
    clips = manifest.get("clips", {})
    if not EXPECTED_CLIPS.issubset(set(clips)):
        errors.append("Missing required calibration animation actions")
    for name, clip in clips.items():
        if not isinstance(clip, dict) or clip.get("frames", 0) < 2 or clip.get("ms_per_frame", 0) <= 0:
            errors.append(f"Invalid animation timing: {name}")
        if clip.get("contract") != "PROVISIONAL_W07_APPROVAL_REQUIRED":
            errors.append(f"Clip {name} claims an unapproved timing contract")
    hashes = manifest.get("sha256", {})
    for filename in EXPECTED_FILES:
        path = directory / filename
        if not path.is_file() or path.stat().st_size < 20:
            errors.append(f"Missing or empty artifact: {filename}")
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if hashes.get(filename) != digest:
            errors.append(f"Missing or mismatched SHA-256: {filename}")
    png = directory / "calibration.png"
    if png.is_file():
        raw = png.read_bytes()
        if raw[:8] != bytes((137, 80, 78, 71, 13, 10, 26, 10)):
            errors.append("Calibration render is not a PNG")
        elif len(raw) >= 26:
            width, height, depth, color_type = struct.unpack(">IIBB", raw[16:26])
            if width <= 0 or height <= 0 or color_type not in (4, 6):
                errors.append("PNG dimensions or alpha channel invalid")
    glb = directory / "f05_noncanonical_calibration.glb"
    if glb.is_file():
        data = glb.read_bytes()
        if len(data) < 12 or data[:4] != b"glTF":
            errors.append("GLB magic header invalid")
        elif struct.unpack("<I", data[8:12])[0] != len(data):
            errors.append("GLB declared length does not match file")
        elif len(data) < 20:
            errors.append("GLB missing JSON chunk")
        else:
            chunk_length, chunk_type = struct.unpack("<I4s", data[12:20])
            if chunk_type != b"JSON" or 20 + chunk_length > len(data):
                errors.append("GLB JSON chunk invalid")
            else:
                try:
                    scene = json.loads(data[20:20 + chunk_length])
                    skins = scene.get("skins", [])
                    if not skins or not any(skin.get("joints") for skin in skins):
                        errors.append("GLB missing skinned armature")
                    animations = scene.get("animations", [])
                    if not animations or not any(
                        animation.get("channels") and animation.get("samplers")
                        for animation in animations
                    ):
                        errors.append("GLB missing exported animation")
                    meshes = scene.get("meshes", [])
                    if not meshes or not any(mesh.get("primitives") for mesh in meshes):
                        errors.append("GLB missing mesh geometry")
                except (UnicodeDecodeError, ValueError):
                    errors.append("GLB JSON chunk cannot be decoded")
    qa = manifest.get("qa", {})
    if qa.get("glb_export") != "PASS":
        errors.append("GLB export did not pass")
    # Do not conflate artifact validation with visual, animation or integration QA.
    return errors

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    errors = validate(args.directory)
    result = {"status": "FAIL" if errors else "ARTIFACT_GATE_PASS",
              "errors": errors, "scope": "artifact_integrity_only",
              "visual_approval": False, "godot_tested": False}
    print(json.dumps(result, indent=2))
    return 1 if errors else 0

if __name__ == "__main__":
    sys.exit(main())
