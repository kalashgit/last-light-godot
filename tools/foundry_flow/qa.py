"""Independent fail-closed PNG/atlas/Godot evidence reconciliation.

Checks exact source-frame reconstruction from packed atlas pages, image/geometry
provenance, and recorded Godot import success. Artistic Golden acceptance and
physical iPhone performance ALWAYS remain external founder-owned gates.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _verify_pages(packed: dict, sheets: Path) -> list[Image.Image]:
    if (packed.get("schema_version") != 1
            or packed.get("golden_approved") is not False
            or packed.get("f12_world_scale_approved") is not False
            or packed.get("status") != "TECHNICAL_SPRITE_SHEET_CANDIDATE"):
        raise ValueError("Source atlas was preemptively promoted or has wrong schema")
    pages = []
    for index, page in enumerate(packed["pages"]):
        expected_name = f"sheet_{index:04d}.png"
        if page["file"] != expected_name:
            raise ValueError("Untrusted atlas page name")
        p = sheets / expected_name
        if sha(p) != page["sha256"]:
            raise ValueError("Packed atlas checksum drift")
        with Image.open(p) as im:
            if im.format != "PNG" or im.mode != "RGBA" or im.size != (page["width"], page["height"]):
                raise ValueError("Untrusted atlas file image")
            pages.append(im.copy())
    if not 1 <= len(pages) <= 32:
        raise ValueError("No atlas pages or excessive page count")
    return pages


def verify(plan: dict, styled_views: Path, candidates: Path,
           sheets: Path, godot_report: dict, output: Path,
           offline_bridge: Path | None = None,
           blender_audit: dict | None = None) -> dict:
    if plan.get("schema_version") != 1 or plan.get("golden_approved") is not False:
        raise ValueError("Untrusted production plan")
    if (godot_report.get("result") != "GODOT_ATLAS_IMPORT_PASS"
            or godot_report.get("frame_count") != len(plan["selected"]) * 16
            or godot_report.get("instantiated_sprites") != len(plan["selected"]) * 16
            or godot_report.get("golden_approved") is not False
            or godot_report.get("iphone_verified") is not False):
        raise ValueError("Godot import evidence missing or mismatched")
    packed = json.loads((sheets / "sprite_sheet_manifest.json").read_text())
    pages = _verify_pages(packed, sheets)
    frames = packed["frames"]
    expected_ids = [item["asset_id"] for item in plan["selected"]]
    if (len(expected_ids) != len(set(expected_ids))
            or len(frames) != 16 * len(expected_ids)
            or {f["asset_id"] for f in frames} != set(expected_ids)):
        raise ValueError("Packed frame coverage does not match admitted work orders")
    frame_map = {(f["asset_id"], f["heading"]): f for f in frames}
    if len(frame_map) != len(frames):
        raise ValueError("Duplicate heading frame in packed atlas")
    if blender_audit is not None:
        entries = blender_audit.get("objects", [])
        if (blender_audit.get("source_plan_sha256") != plan["source_plan_sha256"]
                or blender_audit.get("golden_approved") is not False
                or {entry.get("asset_id") for entry in entries} != set(expected_ids)
                or len(entries) != len(expected_ids)):
            raise ValueError("Source Blender audit does not match admitted plan")
        by_id = {entry["asset_id"]: entry for entry in entries}
        for item in plan["selected"]:
            audit = by_id[item["asset_id"]]
            if (audit.get("source_glb_sha256") != item["glb_sha256"]
                    or audit.get("geometry_present") is not True
                    or audit.get("pbr_material_quality_verified") is not False
                    or audit.get("golden_approved") is not False
                    or audit.get("mesh_count", 0) <= 0
                    or audit.get("vertex_count", 0) < 8):
                raise ValueError("Missing Blender geometry/material provenance")
    bridge_manifest = None
    if offline_bridge is not None:
        bridge_manifest = json.loads((offline_bridge / "sprite_sheet_manifest.json").read_text())
        if (len(expected_ids) != 1 or bridge_manifest.get("asset_id") != expected_ids[0]
                or bridge_manifest.get("origin") != "sprite-gen-offline-export"
                or len(bridge_manifest.get("frames", [])) != 16
                or bridge_manifest.get("golden_approved") is not False):
            raise ValueError("Offline sprite-gen interchange failed verification")

    objects = []
    for item in plan["selected"]:
        ident = item["asset_id"]
        root = styled_views / ident
        metadata = json.loads((root / "render_metadata.json").read_text())
        candidate_dir = candidates / ident
        candidate = json.loads((candidate_dir / "manifest.json").read_text())
        if (metadata.get("source_sha256") != item["glb_sha256"]
                or metadata.get("golden_approved") is not False
                or metadata.get("f11_approved") is not False
                or metadata.get("f12_world_scale_approved") is not False
                or metadata.get("pixel_style_preset") != "GOLDEN40_PIXEL_REALISM_CANDIDATE_V1"
                or candidate.get("source_glb_sha256") != item["glb_sha256"]
                or candidate.get("atlas_sha256") != sha(candidate_dir / "atlas_16_headings.png")
                or candidate.get("status") != "TECHNICAL_SPRITE_CANDIDATE"):
            raise ValueError(f"Geometry/material provenance or status failed: {ident}")
        actual = metadata.get("dimensions_m", [])
        expected = item.get("expected_geometry_bounds_m", [])
        if len(actual) != 3 or len(expected) != 3 or any(
            abs(float(a) - float(b)) > max(0.025, 0.15 * float(b))
            for a, b in zip(actual, expected)
        ):
            raise ValueError(f"Geometry bounds differ from admitted R03 source: {ident}")
        digests = []
        for heading in range(16):
            frame = frame_map[(ident, heading)]
            if (frame["state"] != "static" or frame["frame"] != 0
                    or frame["pivot_world_verified"] is not False
                    or frame["source_size"] != [metadata["resolution"]] * 2):
                raise ValueError("Invalid heading semantics or provisional pivot")
            original_path = root / f"{heading:02d}.png"
            with Image.open(original_path) as im:
                source = im.convert("RGBA")
            bbox = source.getchannel("A").getbbox()
            if bbox is None or frame["trim_offset"] != [bbox[0], bbox[1]]:
                raise ValueError("Trim alignment or transparency mismatch")
            page = pages[frame["page"]]
            x, y, w, h = frame["region"]
            if min(x, y) < 0 or x + w > page.width or y + h > page.height:
                raise ValueError("Packed frame escapes page")
            if page.crop((x, y, x + w, y + h)).tobytes() != source.crop(bbox).tobytes():
                raise ValueError(f"Pixel loss/color modification during packing: {ident}/{heading}")
            digests.append(sha(original_path))
        objects.append({
            "asset_id": ident,
            "work_order_id": item["work_order_id"],
            "notion_url": item["notion_url"],
            "geometry_sha256": item["glb_sha256"],
            "technical_atlas_sha256": candidate["atlas_sha256"],
            "frame_count": 16,
            "unique_directional_frames": len(set(digests)),
            "quality_focus": item["quality_focus"],
            "automatic_art_quality_pass": False,
        })
    output.mkdir(parents=True, exist_ok=True)
    if objects:
        # Contact sheet labels are on a *review preview only*, never baked into
        # transparent source sprites or the runtime atlas.
        first = objects[0]["asset_id"]
        width = json.loads((styled_views / first / "render_metadata.json").read_text())["resolution"]
        preview = Image.new("RGB", (4 * (width + 16), 4 * (width + 30)), (54, 61, 66))
        draw = ImageDraw.Draw(preview)
        for i in range(16):
            with Image.open(styled_views / first / f"{i:02d}.png") as im:
                image = im.convert("RGBA")
            x, y = i % 4 * (width + 16), i // 4 * (width + 30)
            tile = Image.new("RGBA", image.size, (95, 99, 100, 255))
            tile.alpha_composite(image)
            preview.paste(tile.convert("RGB"), (x, y))
            draw.text((x + 4, y + width + 5), f"{first} · {i * 22.5:.1f}°", fill=(240, 240, 237))
        preview.save(output / "founder_contact_sheet.png", optimize=True)
    packet = {
        "schema_version": 1,
        "status": "TECHNICAL_QA_PASSED_AWAITING_FOUNDER_VISUAL_REVIEW",
        "source_plan_sha256": plan["source_plan_sha256"],
        "objects": objects,
        "technical_qa_passed": True,
        "godot_import_verified": True,
        "f11_material_approved": False,
        "f12_world_scale_approved": False,
        "founder_visual_approved": False,
        "iphone_verified": False,
        "golden_approved": False,
        "gameplay_integrated": False,
        "original_art_and_rights_final_review_required": True,
        "next_human_gates": [
            "F11 original PBR materials and source geometry inspection",
            "F12 fixed world-pixel scale and ground pivot calibration",
            "Founder compare contact sheet to Golden 40 at 32/48/64px",
            "Godot real scene interaction and on-device iPhone FPS/memory review",
        ],
    }
    (output / "approval_packet.json").write_text(json.dumps(packet, indent=2) + "\n")
    return packet


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--plan", type=Path, required=True)
    p.add_argument("--styled-views", type=Path, required=True)
    p.add_argument("--candidates", type=Path, required=True)
    p.add_argument("--sheets", type=Path, required=True)
    p.add_argument("--godot-report", type=Path, required=True)
    p.add_argument("--offline-bridge", type=Path)
    p.add_argument("--blender-audit", type=Path)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    packet = verify(json.loads(a.plan.read_text()), a.styled_views, a.candidates,
                    a.sheets, json.loads(a.godot_report.read_text()), a.output,
                    a.offline_bridge,
                    json.loads(a.blender_audit.read_text()) if a.blender_audit else None)
    print("FOUNDRY_CONTROLLED_QA", len(packet["objects"]), packet["status"])


if __name__ == "__main__":
    main()
