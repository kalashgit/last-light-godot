"""Persist a generated world as versioned, chunked, content-hashed JSON (section 14).

Layout of an export directory:
  world_manifest.json      identity, seeds, versions, file index + hashes, save contract
  region_spec.json         region grid (only the compiled slot has local data)
  district_<slug>.json     roads, intersections, road graph, lots, fences, props, spawns
  buildings/<id>.json      world-space building blueprints (rooms, doors, windows, walls, furniture)
  chunks/chunk_<x>_<y>.json terrain rows, transitions, object index, border seam signatures/portals
  validation_report.json   every world/building check with pass/fail
"""
from __future__ import annotations

import hashlib
from pathlib import Path

from .core import (GENERATOR_VERSION, SCHEMA_CHUNK, SCHEMA_DISTRICT, SCHEMA_REPORT, SCHEMA_WORLD_MANIFEST, SEED_SALT,
                   atomic_write, dumps, overlaps, rect_cells, sha256)
from .terrain import CODES, WALKABLE, transition_mask

DEFAULT_CHUNK = 16


def chunk_border(terrain, cx, cy, size, side):
    """Signature of the seam a chunk shares with its neighbour: both sides of the edge, cell by cell."""
    x0, y0 = cx * size, cy * size
    if side == "east":
        pairs = [((x0 + size - 1, y), (x0 + size, y)) for y in range(y0, y0 + size)]
    elif side == "south":
        pairs = [((x, y0 + size - 1), (x, y0 + size)) for x in range(x0, x0 + size)]
    elif side == "west":
        pairs = [((x0 - 1, y), (x0, y)) for y in range(y0, y0 + size)]
    else:
        pairs = [((x, y0 - 1), (x, y0)) for x in range(x0, x0 + size)]
    a = "".join(CODES[terrain[p]] if p in terrain else "_" for p, _ in pairs)
    b = "".join(CODES[terrain[q]] if q in terrain else "_" for _, q in pairs)
    portals, start = [], None
    for i, (p, q) in enumerate(pairs + [(None, None)]):
        ok = p is not None and terrain.get(p) in WALKABLE and terrain.get(q) in WALKABLE
        if ok and start is None:
            start = i
        if not ok and start is not None:
            portals.append([start, i - start])
            start = None
    # pairs always run west->east / north->south, so both neighbours compute the same seam string
    return {"seam": a + "|" + b, "sha256": hashlib.sha256((a + "|" + b).encode()).hexdigest()[:16], "portals": portals}


def export_world(world, report, out_dir: Path, chunk_size=DEFAULT_CHUNK):
    out_dir = Path(out_dir)
    files = {}

    def put(rel, data):
        raw = dumps(data)
        atomic_write(out_dir / rel, raw)
        files[rel] = sha256(raw)

    W, H = world["bounds"][2], world["bounds"][3]
    t = world["terrain"]
    nx, ny = -(-W // chunk_size), -(-H // chunk_size)
    building_files = []
    for b in world["buildings"]:
        rel = f"buildings/{b['id']}.json"
        put(rel, b)
        chunks = sorted({(c[0] // chunk_size, c[1] // chunk_size) for r in b["footprint"] for c in rect_cells(r)})
        building_files.append({"id": b["id"], "file": rel, "lot_id": b["lot_id"], "program": b["program"],
                               "template": b["template"], "chunks": [list(c) for c in chunks], "footprint": b["footprint"]})
    chunk_index = []
    for cy in range(ny):
        for cx in range(nx):
            x0, y0 = cx * chunk_size, cy * chunk_size
            w, h = min(chunk_size, W - x0), min(chunk_size, H - y0)
            rect = [x0, y0, w, h]
            rows = ["".join(CODES[t[(x, y)]] for x in range(x0, x0 + w)) for y in range(y0, y0 + h)]
            trans = ["".join("%x" % transition_mask(t, x, y) for x in range(x0, x0 + w)) for y in range(y0, y0 + h)]
            border = {s: chunk_border(t, cx, cy, chunk_size, s) for s in ("north", "east", "south", "west")}
            chunk = {"schema": SCHEMA_CHUNK, "world_id": world["world_id"], "chunk": [cx, cy], "rect": rect,
                     "terrain_codes": {v: k for k, v in CODES.items()}, "terrain_rows": rows, "transition_rows": trans,
                     "buildings": [bf["id"] for bf in building_files if [cx, cy] in bf["chunks"]],
                     "props": [p["id"] for p in world["props"] if overlaps(p["rect"], rect)],
                     "fences": [f["id"] for f in world["fences"] if overlaps(fence_rect(f), rect)],
                     "roads": [r["id"] for r in world["roads"] if overlaps(r["rect"], rect)],
                     "neighbors": {"north": [cx, cy - 1] if cy > 0 else None, "south": [cx, cy + 1] if cy < ny - 1 else None,
                                   "west": [cx - 1, cy] if cx > 0 else None, "east": [cx + 1, cy] if cx < nx - 1 else None},
                     "border": border}
            rel = f"chunks/chunk_{cx}_{cy}.json"
            put(rel, chunk)
            chunk_index.append({"chunk": [cx, cy], "file": rel, "rect": rect})
    district_rel = f"district_{world['prefix'].replace('ll.', '')}.json"
    put(district_rel, {"schema": SCHEMA_DISTRICT, "district_id": world["district_id"], "style": world["style_id"],
                       "world_id": world["world_id"], "bounds": world["bounds"], "roads": world["roads"],
                       "intersections": world["intersections"], "road_graph": world["road_graph"], "lots": world["lots"],
                       "fences": world["fences"], "props": world["props"], "curb_cuts": world["curb_cuts"],
                       "spawn": world["spawn"], "spawn_points": world["spawn_points"]})
    put("region_spec.json", world["region"])
    put("validation_report.json", {"schema": SCHEMA_REPORT, "world_id": world["world_id"], **report})
    for rel in [c["file"] for c in chunk_index] + [b["file"] for b in building_files]:
        for entry in chunk_index + building_files:
            if entry["file"] == rel:
                entry["sha256"] = files[rel]
    hashed = sorted((k, v) for k, v in files.items() if k != "validation_report.json")
    blueprint = hashlib.sha256("".join(f"{k}:{v}\n" for k, v in hashed).encode()).hexdigest()
    manifest = {
        "schema": SCHEMA_WORLD_MANIFEST, "world_id": world["world_id"], "name": world["name"],
        "world_seed": world["world_seed"], "generator_version": GENERATOR_VERSION, "seed_salt": SEED_SALT,
        "continent": {"id": "ll.continent.c00", "status": "design_only", "note": "Continental layer is specified in docs/worldgen; not generated yet."},
        "region": {"file": "region_spec.json", "region_id": world["region"]["region_id"], "sha256": files["region_spec.json"]},
        "district": {"file": district_rel, "district_id": world["district_id"], "style": world["style_id"], "sha256": files[district_rel]},
        "bounds": world["bounds"], "tile_units": "1 logical tile = 1 gameplay unit = 80x40 px at 2:1 isometric",
        "chunk_size": chunk_size, "chunk_grid": [nx, ny], "chunks": chunk_index, "buildings": building_files,
        "spawn": world["spawn"], "blueprint_sha256": blueprint, "validation_ok": report["ok"],
        "playable_single_scene": next(c["ok"] for c in report["checks"] if c["check"] == "fits_single_scene_save_bounds"),
        "art_status": "factory sprites (original CC0) for furniture; procedural placeholders for terrain, structure, vegetation and vehicles",
        "save_contract": {
            "blueprint": "Immutable. Runtime copies the manifest set to user:// on first load and never regenerates a visited world.",
            "delta_keys": ["doors[door_id].open", "doors[door_id].health", "containers[item_id].searched", "player", "enemies", "drops"],
            "identity_check": "save delta stores world_id + generator_version + blueprint_sha256 and refuses to apply to a different blueprint"},
    }
    put("world_manifest.json", manifest)
    return manifest


def fence_rect(f):
    (ax, ay), (bx, by) = f["a"], f["b"]
    x0, y0 = int(min(ax, bx)), int(min(ay, by))
    return [x0 - 1, y0 - 1, int(abs(bx - ax)) + 2, int(abs(by - ay)) + 2]
