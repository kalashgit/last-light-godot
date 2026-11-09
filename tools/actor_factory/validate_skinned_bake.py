"""Fail-closed QA for real Blender armature/NLA-to-sprite baking.

This checks source GLB skinning, clip data, original RGBA frames, alpha,
consistent rig and source integrity. Passing is never founder Golden approval.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import struct
from pathlib import Path
from PIL import Image

DIRECTIONS = (
    "front", "front_right", "right", "back_right", "back",
    "back_left", "left", "front_left",
)
SAMPLES = {"idle": 2, "walk": 4}
ITEMS = {
    ("body", "base"),
    ("pants", "calibration_pants"),
    ("shirt", "calibration_shirt"),
    ("backpack", "calibration_pack"),
    ("effects", "calibration_tool"),
}
SIZE = (128, 160)


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as file:
        for block in iter(lambda: file.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def restricted_file(root, relative):
    if not isinstance(relative, str):
        raise ValueError("invalid source path")
    path = Path(relative)
    if path.is_absolute() or ".." in path.parts or "\\" in relative:
        raise ValueError("path traversal")
    resolved = (root / path).resolve()
    if not resolved.is_relative_to(root) or not resolved.is_file():
        raise ValueError("missing or unsafe source file")
    return resolved


def check_glb_skins_and_clips(path):
    raw = path.read_bytes()
    if len(raw) < 20 or raw[:4] != b"glTF":
        raise ValueError("not glTF binary")
    version, length = struct.unpack_from("<II", raw, 4)
    if version != 2 or length != len(raw):
        raise ValueError("invalid glTF length/version")
    json_size, json_chunk_type = struct.unpack_from("<II", raw, 12)
    if json_chunk_type != 0x4E4F534A or 20 + json_size > len(raw):
        raise ValueError("GLB JSON chunk missing")
    gltf = json.loads(raw[20:20 + json_size])
    if not gltf.get("skins") or not gltf.get("animations"):
        raise ValueError("GLB lacks real skeletal skin and animation data")
    names = {str(anim.get("name", "")) for anim in gltf["animations"]}
    for clip in ("idle", "walk"):
        if not any(clip in name for name in names):
            raise ValueError("NLA clip not exported: " + clip)
    return len(gltf["skins"]), len(gltf["animations"])


def validate(root: Path):
    root = root.resolve()
    manifest = json.loads((root / "manifest.json").read_text())
    if (manifest.get("schema") != "last-light.paperdoll.frames.v1"
            or manifest.get("rig") != "ll_biped_v1"
            or manifest.get("tile_px") != [80, 40]
            or manifest.get("golden_approved") is not False
            or manifest.get("frame_size") != list(SIZE)):
        raise ValueError("invalid shared F05/F12 source contract")
    if manifest.get("directions") != list(DIRECTIONS):
        raise ValueError("camera headings not canonical")
    if {c: d.get("frames") for c, d in manifest["animations"].items()} != SAMPLES:
        raise ValueError("sampled clips incomplete")
    if len(manifest.get("pivot", [])) != 2 or not all(
        type(v) is int and 0 <= v <= SIZE[i] for i, v in enumerate(manifest["pivot"])
    ):
        raise ValueError("invalid shared world-foot pivot")
    src = manifest.get("provenance", {})
    if not src.get("confirmed_live_skin_deformation"):
        raise ValueError("no actual evaluated skinning proof")
    if src.get("status") != "CALIBRATION_ONLY_NOT_GOLDEN":
        raise ValueError("invalid approval state")
    if len(src.get("source_meshes", {})) != len(ITEMS):
        raise ValueError("source garment meshes missing")
    # Face and hairstyle features must be genuine weighted meshes exported
    # alongside the rig, not flattened in from a third-party reference image.
    details = src.get("original_face_hair_meshes")
    if (not isinstance(details, list) or len(details) != 18
            or len(set(details)) != len(details)
            or not set(details).issubset(set(src["source_meshes"].get("body/base", [])))):
        raise ValueError("original skinned head details missing or excluded from body render")
    if src.get("facial_geometry_status") != "ORIGINAL_CALIBRATION_NOT_GOLDEN":
        raise ValueError("missing provisional face/art quality status")
    if src.get("hair_layer") != "BAKED_IN_BODY_PENDING_SEPARATE_SLOT":
        raise ValueError("hair slot status falsely claims modular runtime")
    blend = restricted_file(root, src["source_blend"])
    glb = restricted_file(root, src["source_glb"])
    if blend.open("rb").read(7) != b"BLENDER":
        raise ValueError("editable Blender source invalid")
    if sha(blend) != src["source_blend_sha256"] or sha(glb) != src["source_glb_sha256"]:
        raise ValueError("editable source checksum mismatch")
    skins, actions = check_glb_skins_and_clips(glb)
    expected = len(ITEMS) * len(DIRECTIONS) * sum(SAMPLES.values())
    if len(manifest.get("frames", [])) != expected:
        raise ValueError("not all skinned frames rendered")
    observed = set()
    for frame in manifest["frames"]:
        key = (frame["slot"], frame["item_id"], frame["animation"],
               frame["direction"], frame["frame"])
        if key in observed:
            raise ValueError("duplicate source frame")
        if (frame["slot"], frame["item_id"]) not in ITEMS:
            raise ValueError("unknown source layer")
        if (frame["animation"] not in SAMPLES
                or frame["direction"] not in DIRECTIONS
                or type(frame["frame"]) is not int
                or not 0 <= frame["frame"] < SAMPLES[frame["animation"]]):
            raise ValueError("missing NLA frame index")
        path = restricted_file(root, frame["file"])
        if path.suffix != ".png" or sha(path) != frame["sha256"]:
            raise ValueError("PNG missing or altered")
        with Image.open(path) as img:
            if img.format != "PNG" or img.mode != "RGBA" or img.size != SIZE:
                raise ValueError("invalid alpha/frame canvas")
            if img.getchannel("A").getbbox() is None:
                raise ValueError("armature render is blank")
        observed.add(key)
    for slot, item in ITEMS:
        for clip, frames in SAMPLES.items():
            for heading in DIRECTIONS:
                for frame in range(frames):
                    if (slot, item, clip, heading, frame) not in observed:
                        raise ValueError("skinned layer frame missing")
    return {"status": "TECHNICAL_CANDIDATE_NOT_GOLDEN", "skinned_layers": len(ITEMS),
            "source_frames": len(observed), "real_glb_skins": skins,
            "real_glb_animations": actions, "golden_approved": False}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, type=Path)
    result = validate(parser.parse_args().source)
    print("LL_SKINNED_SOURCE_QA_PASS", json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
