"""Rebuild an in-memory world from exported files and verify integrity.

This is the same data path the Godot runtime uses, so verify() proves the
exported blueprint alone (not generator memory) is valid and seam-consistent.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

from .core import SCHEMA_WORLD_MANIFEST, GenerationError, load_json, sha256
from .export import chunk_border


def load_export(out_dir):
    out_dir = Path(out_dir)
    manifest = load_json(out_dir / "world_manifest.json")
    if manifest.get("schema") != SCHEMA_WORLD_MANIFEST:
        raise GenerationError("E_MANIFEST_SCHEMA", str(manifest.get("schema")))
    district = load_json(out_dir / manifest["district"]["file"])
    region = load_json(out_dir / manifest["region"]["file"])
    terrain, chunks = {}, {}
    for entry in manifest["chunks"]:
        c = load_json(out_dir / entry["file"])
        chunks[tuple(c["chunk"])] = c
        x0, y0, w, h = c["rect"]
        codes = c["terrain_codes"]
        for dy, row in enumerate(c["terrain_rows"]):
            for dx, ch in enumerate(row):
                terrain[(x0 + dx, y0 + dy)] = codes[ch]
    buildings = [load_json(out_dir / b["file"]) for b in manifest["buildings"]]
    world = {"world_id": manifest["world_id"], "name": manifest["name"], "world_seed": manifest["world_seed"],
             "district_id": district["district_id"], "style_id": district["style"], "bounds": manifest["bounds"],
             "region": region, "roads": district["roads"], "intersections": district["intersections"],
             "road_graph": district["road_graph"], "lots": district["lots"], "buildings": buildings, "terrain": terrain,
             "fences": district["fences"], "props": district["props"], "curb_cuts": district["curb_cuts"],
             "spawn": district["spawn"], "spawn_points": district["spawn_points"],
             "prefix": "ll." + Path(manifest["district"]["file"]).stem.replace("district_", ""),
             "asset_intake": manifest.get("asset_intake", {})}
    W, H = world["bounds"][2], world["bounds"][3]
    world["terrain_rows"] = [[terrain[(x, y)] for x in range(W)] for y in range(H)]
    return manifest, world, chunks


def verify_export(out_dir):
    """Hash, schema, chunk-seam and reference integrity of an export directory."""
    out_dir = Path(out_dir)
    manifest, world, chunks = load_export(out_dir)
    problems = []
    hashed = []
    for entry in manifest["chunks"] + manifest["buildings"]:
        actual = sha256((out_dir / entry["file"]).read_bytes())
        if actual != entry["sha256"]:
            problems.append(f"hash mismatch {entry['file']}")
    for key in ("district", "region"):
        if sha256((out_dir / manifest[key]["file"]).read_bytes()) != manifest[key]["sha256"]:
            problems.append(f"hash mismatch {manifest[key]['file']}")
    for p in sorted(out_dir.rglob("*.json")):
        rel = p.relative_to(out_dir).as_posix()
        if rel not in ("world_manifest.json", "validation_report.json"):
            hashed.append((rel, sha256(p.read_bytes())))
    blueprint = hashlib.sha256("".join(f"{k}:{v}\n" for k, v in sorted(hashed)).encode()).hexdigest()
    if blueprint != manifest["blueprint_sha256"]:
        problems.append("blueprint hash mismatch (files added, removed or edited)")
    size = manifest["chunk_size"]
    for (cx, cy), c in chunks.items():
        for side, (dx, dy), opposite in (("east", (1, 0), "west"), ("south", (0, 1), "north")):
            n = chunks.get((cx + dx, cy + dy))
            if n is None:
                continue
            if c["border"][side]["sha256"] != n["border"][opposite]["sha256"] or c["border"][side]["portals"] != n["border"][opposite]["portals"]:
                problems.append(f"seam mismatch {c['chunk']} {side}")
            recomputed = chunk_border(world["terrain"], cx, cy, size, side)
            if recomputed["sha256"] != c["border"][side]["sha256"]:
                problems.append(f"stored seam differs from terrain {c['chunk']} {side}")
        ids = set(c["buildings"])
        known = {b["id"] for b in world["buildings"]}
        if ids - known:
            problems.append(f"chunk {c['chunk']} references unknown buildings {sorted(ids - known)}")
        props = {p["id"] for p in world["props"]}
        if set(c["props"]) - props:
            problems.append(f"chunk {c['chunk']} references unknown props")
    return manifest, world, problems
