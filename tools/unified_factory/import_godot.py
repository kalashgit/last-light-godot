"""LAST LIGHT master factory -> Godot 4 resource importer (stdlib only).

This is *not* a renderer. It turns verified existing PNG/atlas manifests into
reproducible Godot SpriteFrames .tres and AnimatedSprite2D .tscn resources.
No Godot editor GUI or nonstandard plugin is needed.

Usage:
  python tools/unified_factory/import_godot.py --project . \
      --output assets/generated/master_import_v1

Production is still subject to Golden visual approval and actual gameplay QA.
Never modify main.tscn, project.godot, player save files or approved references.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import re
import struct
from collections import defaultdict
from pathlib import Path

PNG_HEADER = b"\x89PNG\r\n\x1a\n"
ID_PATTERN = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_-]*$")
DIRS = ("front", "right", "back", "left")
PROPS = Path("preview/animation-factory-v1")
ACTORS = Path("preview/actor-factory-v1")
VEHICLES = Path("preview/vehicle-factory-v1")
ITEMS = Path("assets/generated/factory")
FLEET = Path("preview/fleet-factory-v1")
GODOT_IMPORT = Path("assets/generated/master_import_v1")


def require(value, message):
    if not value:
        raise ValueError(message)


def asset_id(value):
    require(isinstance(value, str) and ID_PATTERN.fullmatch(value), "unsafe asset id: " + str(value))
    return value


def quote(value):
    # Only JSON-compatible strings are emitted; Godot accepts escaped quotes.
    return json.dumps(str(value), ensure_ascii=False)


def relative_file(root, relative):
    """Prevent traversal/URL/absolute path injection in community JSON sources."""
    require(isinstance(relative, str) and relative and "\\" not in relative,
            "invalid relative asset path")
    p = Path(relative)
    require(not p.is_absolute() and ".." not in p.parts and not str(p).startswith("res:"),
            "path traversal or external path: " + relative)
    resolved = (root / p).resolve()
    require(resolved.is_relative_to(root.resolve()), "asset file outside repository")
    require(resolved.is_file(), "missing file: " + relative)
    return resolved


def png_size(file):
    with file.open("rb") as f:
        header = f.read(26)
    require(len(header) == 26 and header[:8] == PNG_HEADER and header[12:16] == b"IHDR",
            "bad PNG: " + str(file))
    width, height = struct.unpack(">II", header[16:24])
    require(0 < width < 16384 and 0 < height < 16384, "unreasonable PNG size: " + str(file))
    return (width, height)


def stable_sha(file):
    h = hashlib.sha256()
    with file.open("rb") as f:
        for chunk in iter(lambda: f.read(1048576), b""):
            h.update(chunk)
    return h.hexdigest()


def checked_texture(root, rel, width=None, height=None, source_sha=None):
    p = relative_file(root, rel)
    observed = png_size(p)
    if width is not None or height is not None:
        require(observed == (width, height),
                "texture dimensions mismatch: " + rel + " " + str(observed))
    if source_sha is not None:
        require(stable_sha(p) == source_sha, "texture SHA256 mismatch: " + rel)
    return "res://" + p.relative_to(root.resolve()).as_posix()


def checked_cell(value, label):
    require(isinstance(value, list) and len(value) == 2 and
            all(type(v) is int and 0 < v <= 4096 for v in value),
            "invalid cell size: " + label)
    return value


def checked_anchor(value, label):
    require(isinstance(value, list) and len(value) == 2 and
            all(type(v) in (int, float) and math.isfinite(v) for v in value),
            "invalid pivot: " + label)
    return value


def read_manifest(root, relative):
    p = relative_file(root, relative.as_posix())
    obj = json.loads(p.read_text())
    require(obj.get("tile_px") == [80, 40], "wrong 80x40 tile projection: " + str(relative))
    return obj


def frame(texture, rect=None):
    return dict(texture=texture, region=rect)


def animation(name, frames, fps=8.0, loop=False):
    require(name and ID_PATTERN.fullmatch(name), "invalid animation name")
    require(frames and fps > 0 and math.isfinite(fps), "missing animation frames")
    return dict(name=name, frames=frames, speed=float(fps), loop=bool(loop))


def add_actor_source(root, entries):
    manifest = read_manifest(root, ACTORS / "manifest.json")
    require(manifest.get("schema_version") == 1, "actor schema not supported")
    for actor in manifest["actors"]:
        name = asset_id(actor["render_id"])
        clips = actor["clips"]
        require(bool(clips) and "idle" in clips, "actor idle missing: " + name)
        animations = []
        pivot = None
        for clip_name in sorted(clips):
            clip = clips[clip_name]
            cell_w, cell_h = checked_cell(clip["cell_px"], name)
            anchor = checked_anchor(clip["anchor_px"], name)
            require(pivot is None or pivot == (cell_w, cell_h, *anchor),
                    "actor changed bounding/pivot across clips: " + name)
            pivot = (cell_w, cell_h, *anchor)
            count = clip["frame_count_per_direction"]
            require(type(count) is int and count > 0 and count <= 64, "invalid actor frame count")
            require(clip["directions"] == list(DIRS), "actor directional ordering drift")
            tex = checked_texture(root, (ACTORS / clip["atlas"]).as_posix(),
                                  cell_w * count, cell_h * 4, clip.get("sha256"))
            for direction_index, direction in enumerate(DIRS):
                frames = [frame(tex, [i * cell_w, direction_index * cell_h, cell_w, cell_h])
                          for i in range(count)]
                animations.append(animation(clip_name + "_" + direction, frames,
                                            8.0, count > 1))
        entries.append(dict(kind="actor", id=name, stable_id="ll_actor_" + name,
                            animations=animations, cell=[pivot[0], pivot[1]],
                            pivot=[pivot[2], pivot[3]], start="idle_front",
                            status="technical_candidate", original="preview actor pilot",
                            dimensions_m=[actor.get("height_m", 1.7)]))


def add_prop_source(root, entries):
    manifest = read_manifest(root, PROPS / "manifest.json")
    require(manifest.get("schema_version") == 1, "prop schema not supported")
    for rec in manifest["entries"]:
        name = asset_id(rec["id"])
        cell_w, cell_h = checked_cell(rec["cell_px"], name)
        anchor = checked_anchor(rec["anchor_px"], name)
        count = rec["frame_count"]
        require(type(count) is int and 2 <= count <= 64, "bad prop frame count")
        fps = rec["fps"]
        require(type(fps) in (float, int) and fps > 0, "bad prop fps")
        tex = checked_texture(root, (PROPS / rec["strip"]).as_posix(),
                              cell_w * count, cell_h)
        opening = [frame(tex, [i * cell_w, 0, cell_w, cell_h]) for i in range(count)]
        animations = [animation("open", opening, fps)]
        if rec.get("reverse_for_close", True):
            animations.append(animation("close", list(reversed(opening)), fps))
        animations.append(animation("closed", [opening[0]], 1.0))
        animations.append(animation("opened", [opening[-1]], 1.0))
        entries.append(dict(kind="prop", id=name, stable_id="ll_prop_" + name,
                            animations=animations, cell=[cell_w, cell_h],
                            pivot=anchor, start="closed", status="technical_candidate",
                            event_frame=rec.get("event_frame"),
                            condition=rec.get("condition"), original="hollow Blender prop pilot"))


def vehicle_to_entry(root, name, rec, base_dir, original, selected_sha=None):
    cell_w, cell_h = checked_cell(rec["cell_px"], name)
    anchor = checked_anchor(rec["anchor_px"], name)
    require(rec.get("heading_count") == 16 and rec.get("grid") == [4, 4],
            "vehicle heading count/grid mismatch")
    selected = rec.get("pixel_refined_atlas") or rec["atlas"]
    tex = checked_texture(root, (base_dir / selected).as_posix(),
                          cell_w * 4, cell_h * 4, selected_sha)
    # Source full-color atlas may not be committed for preview-only fleet jobs.
    # If absent, verify the published pixel-refined atlas by the batch report SHA.
    original_atlas = (root / base_dir / rec["atlas"])
    if rec.get("sha256") and original_atlas.is_file():
        checked_texture(root, (base_dir / rec["atlas"]).as_posix(),
                        cell_w * 4, cell_h * 4, rec["sha256"])
    angles = [animation("heading_%02d" % i,
                        [frame(tex, [(i % 4) * cell_w, (i // 4) * cell_h, cell_w, cell_h])],
                        1.0, False) for i in range(16)]
    return dict(kind="vehicle", id=name, stable_id=rec["asset_id"],
                animations=angles, cell=[cell_w, cell_h], pivot=anchor,
                start="heading_00", status="technical_candidate",
                dimensions_m=rec.get("dimensions_m") or rec.get("world_dimensions_m"),
                color=rec.get("paint_hex"), original=original)


def add_vehicles(root, entries):
    m = read_manifest(root, VEHICLES / "manifest.json")
    entries.append(vehicle_to_entry(root, asset_id(m["asset_id"]), m, VEHICLES,
                                    "golden hatchback technical candidate"))
    fleet_report = FLEET / "batch_report.json"
    if (root / fleet_report).is_file():
        data = json.loads((root / fleet_report).read_text())
        for job in sorted(data.get("completed", []), key=lambda j: j["job_id"]):
            name = asset_id(job["job_id"])
            sub_dir = FLEET / name
            rec = read_manifest(root, sub_dir / "manifest.json")
            require(rec.get("job_id") == name, "fleet job ID mismatch")
            entries.append(vehicle_to_entry(root, name, rec, sub_dir,
                                            "fleet smoke technical candidate",
                                            selected_sha=job["atlas_sha256"]))


def add_item_source(root, entries):
    manifest = root / ITEMS / "manifest.json"
    data = read_manifest(root, ITEMS / "manifest.json")
    require(data.get("schema") == 1, "item schema not supported")
    require(bool(data.get("objects")), "empty generated item catalog")
    for item in data["objects"]:
        name = asset_id(item["id"])
        animations = []
        by_mode = defaultdict(list)
        for fr in item["frames"]:
            by_mode[fr["mode"]].append(fr)
        for mode in sorted(by_mode):
            for index, fr in enumerate(sorted(by_mode[mode], key=lambda f: f["angle_degrees"])):
                w, h = checked_cell(fr["size_px"], name + ":" + mode)
                anchor = checked_anchor(fr["anchor_px"], name + ":" + mode)
                tex = checked_texture(root, (ITEMS / fr["file"]).as_posix(), w, h)
                angle = int(fr["angle_degrees"])
                suffix = "_%03d" % angle if len(by_mode[mode]) > 1 else ""
                animations.append(animation(mode + suffix, [frame(tex)], 1.0, False))
        require(animations, "no item sprites: " + name)
        ground = next((fr for fr in item["frames"] if fr["mode"] == "ground"), None)
        require(ground is not None, "item missing world ground sprite: " + name)
        entries.append(dict(kind="item", id=name, stable_id=name,
                            animations=animations, cell=ground["size_px"],
                            pivot=ground["anchor_px"], start="ground",
                            dimensions_m=item.get("dimensions_m"),
                            category=item.get("category"),
                            status="technical_candidate", original="original procedural 300-ID catalog"))


def indent_for_resource(name, refs, atlas_defs):
    """Godot 4 resource text: SpriteFrames with typed AtlasTexture subresources."""
    extern = []
    for i, tex in enumerate(sorted(set(refs)), 1):
        extern.append('[ext_resource type="Texture2D" path=%s id=%s]' %
                      (quote(tex), quote(str(i))))
    ext_ids = {p: str(i) for i, p in enumerate(sorted(set(refs)), 1)}
    subs = []
    animation_chunks = []
    n = 0
    for a in atlas_defs:
        frames = []
        for f in a["frames"]:
            tex = f["texture"]
            if f["region"] is None:
                ref = 'ExtResource(%s)' % quote(ext_ids[tex])
            else:
                n += 1
                sid = "f%05d" % n
                x, y, w, h = f["region"]
                subs.append('[sub_resource type="AtlasTexture" id=%s]\natlas = ExtResource(%s)\nregion = Rect2(%d, %d, %d, %d)' %
                            (quote(sid), quote(ext_ids[tex]), x, y, w, h))
                ref = 'SubResource(%s)' % quote(sid)
            frames.append('{"duration": 1.0, "texture": %s}' % ref)
        animation_chunks.append('{"frames": [%s], "loop": %s, "name": &%s, "speed": %.6f}' %
                                (", ".join(frames), "true" if a["loop"] else "false",
                                 quote(a["name"]), a["speed"]))
    lines = ["[gd_resource type=\"SpriteFrames\" load_steps=%d format=3]" %
             (1 + len(ext_ids) + len(subs)), ""]
    lines.extend(extern)
    lines.append("")
    for sub in subs:
        lines.extend([sub, ""])
    lines.extend(["[resource]", "animations = [%s]" % (",\n".join(animation_chunks)), ""])
    return "\n".join(lines)


def write_updated(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_file() and path.read_text() == content:
        return False
    path.write_text(content)
    return True


def render_scene(resource_path, entry):
    w, h = entry["cell"]
    ax, ay = entry["pivot"]
    # AnimatedSprite2D centered + offset is invariant across a shared crop.
    x = w * .5 - ax
    y = h * .5 - ay
    return ('[gd_scene load_steps=2 format=3]\n\n'
            '[ext_resource type="SpriteFrames" path=%s id="1"]\n\n'
            '[node name=%s type="AnimatedSprite2D"]\n'
            'texture_filter = 1\n'
            'sprite_frames = ExtResource("1")\n'
            'animation = &%s\n'
            'centered = true\n'
            'offset = Vector2(%.5f, %.5f)\n' %
            (quote(resource_path), quote(entry["id"]), quote(entry["start"]), x, y))


def build(root, output, include_fleet=True):
    root = root.resolve()
    output = output.resolve()
    require(output.is_relative_to(root), "Godot output must remain inside project")
    require(output != root and not output.is_relative_to(root / "preview"),
            "do not overwrite source art")
    entries = []
    add_item_source(root, entries)
    add_actor_source(root, entries)
    add_prop_source(root, entries)
    add_vehicles(root, entries)
    if not include_fleet:
        entries = [e for e in entries if e["original"] != "fleet smoke technical candidate"]
    keys = [x["stable_id"] for x in entries]
    require(len(keys) == len(set(keys)), "duplicate asset IDs in master resource catalog")
    produced = 0
    index = []
    for e in sorted(entries, key=lambda x: (x["kind"], x["id"])):
        sub = asset_id(e["kind"])
        basename = asset_id(e["id"])
        rel_res = output.relative_to(root) / "resources" / sub / (basename + ".tres")
        rel_scene = output.relative_to(root) / "scenes" / sub / (basename + ".tscn")
        refs = [f["texture"] for a in e["animations"] for f in a["frames"]]
        generated_res = indent_for_resource(e["id"], refs, e["animations"])
        produced += write_updated(root / rel_res, generated_res)
        produced += write_updated(root / rel_scene,
                                  render_scene("res://" + rel_res.as_posix(), e))
        record = {k: v for k, v in e.items() if k != "animations"}
        record.update(resource_path="res://" + rel_res.as_posix(),
                      scene_path="res://" + rel_scene.as_posix(),
                      animation_names=[a["name"] for a in e["animations"]],
                      frame_count=sum(len(a["frames"]) for a in e["animations"]),
                      spriteframes_sha256=hashlib.sha256(generated_res.encode()).hexdigest(),
                      visual_approved=False, integrated_gameplay=False)
        index.append(record)
    counts = {k: sum(r["kind"] == k for r in index) for k in
              ("item", "actor", "prop", "vehicle")}
    report = dict(schema_version=1, tile_px=[80, 40],
                  pipeline="original art previews -> Godot 4 SpriteFrames+PackedScene",
                  status="RESOURCE_IMPORT_CANDIDATES_NOT_GOLDEN_APPROVED_NOT_GAMEPLAY_INTEGRATED",
                  asset_count=len(index), source_counts=counts,
                  generated_files_changed=produced,
                  resources=index)
    # Avoid writing the volatile count into the cached catalog itself.
    report["generated_files_changed"] = 0
    write_updated(output / "catalog.json", json.dumps(report, indent=2) + "\n")
    print("LL_MASTER_IMPORT_PASS",
          "assets", len(index), "item", counts["item"], "actor", counts["actor"],
          "prop", counts["prop"], "vehicle", counts["vehicle"],
          "changed", produced, flush=True)
    return report


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--project", type=Path, default=Path("."))
    p.add_argument("--output", type=Path, default=GODOT_IMPORT)
    p.add_argument("--exclude-fleet", action="store_true")
    a = p.parse_args()
    root = a.project.resolve()
    out = (root / a.output).resolve()
    build(root, out, not a.exclude_fleet)


if __name__ == "__main__":
    main()
