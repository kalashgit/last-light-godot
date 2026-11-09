"""District / street network / parcel generation and world validation (W04-D).

Pipeline: style -> road grid -> blocks -> parcels -> zoning -> building
(fixture or procedural) -> frontage paths/driveways -> fences -> vegetation
-> street props -> spawns -> validation. Every stage has its own seed stream.
"""
from __future__ import annotations

import math

from .asset_intake_v2 import bindings, intake
from .buildings import fixture_building, generate_building
from .catalog import catalog
from .core import GENERATOR_VERSION, SCHEMA_RECIPE, GenerationError, Rng, contains, overlaps, r6, rect_cells, seg_key, stream_seed
from .furnish import make_item, roll_loot
from .plan import Frame, transform_building
from .region import pick_slot, region_spec
from .terrain import WALKABLE, adjacency_errors, bank_water, edge_biome
from .validate import DOOR_PASS, NavGrid, door_units, unit_sides, validate_building

PLAYABLE_LIMIT = 100  # gameplay save validation accepts coordinates within [-100, 100]
OUTWARD = {"south": (0, 1), "north": (0, -1), "east": (1, 0), "west": (-1, 0)}


def slug(text):
    return "".join(ch if ch.isalnum() else "_" for ch in text.lower()).strip("_")


def validate_recipe(recipe):
    cat = catalog()
    if not isinstance(recipe, dict) or recipe.get("schema") != SCHEMA_RECIPE:
        raise GenerationError("E_RECIPE_SCHEMA", "expected " + SCHEMA_RECIPE)
    for key in ("world_id", "world_seed", "style"):
        if key not in recipe:
            raise GenerationError("E_RECIPE_FIELD", key)
    if not isinstance(recipe["world_seed"], int) or isinstance(recipe["world_seed"], bool) or recipe["world_seed"] < 0:
        raise GenerationError("E_RECIPE_SEED", repr(recipe["world_seed"]))
    if recipe["style"] not in cat["styles"]["styles"]:
        raise GenerationError("E_RECIPE_STYLE", recipe["style"])
    blocks = recipe.get("blocks")
    if blocks is not None and (not isinstance(blocks, list) or len(blocks) != 2 or not all(isinstance(v, int) and 1 <= v <= 4 for v in blocks)):
        raise GenerationError("E_RECIPE_BLOCKS", repr(blocks))
    for key, ov in recipe.get("lot_overrides", {}).items():
        if not isinstance(ov, dict) or not ({"program", "fixture", "vacant"} & set(ov)):
            raise GenerationError("E_RECIPE_OVERRIDE", key)
        if "program" in ov and ov["program"] not in cat["programs"]:
            raise GenerationError("E_UNKNOWN_PROGRAM", ov["program"])
        if "fixture" in ov and ov["fixture"] not in cat["lab_a"]["buildings"]:
            raise GenerationError("E_UNKNOWN_FIXTURE", ov["fixture"])


def partition(rng, total_hint, lo, hi, n):
    return [rng.randint(lo, hi) for _ in range(n)]


def generate_world(recipe):
    validate_recipe(recipe)
    cat = catalog()
    style_id = recipe["style"]
    style = cat["styles"]["styles"][style_id]
    seed = recipe["world_seed"]
    region = region_spec(seed)
    slot = pick_slot(region, style_id)
    district_id = recipe.get("district_id") or slot["district_id"]
    slot["compiled"] = True
    slot["compiled_district_id"] = district_id
    prefix = "ll." + slug(district_id.replace("ll.", "", 1))
    roads_rng = Rng(stream_seed(seed, "roads", district_id))
    parcel_rng = Rng(stream_seed(seed, "parcel", district_id))
    bx, by = recipe.get("blocks") or style["blocks"]
    per_row = recipe.get("lots_per_row") or style["lots_per_row_hint"]
    sw, rw = style["sidewalk_width"], style["road_width"]
    corridor = rw + 2 * sw
    margin = recipe.get("edge_margin", cat["styles"]["edge_margin"])
    # ---- blocks and parcels
    explicit = recipe.get("lot_widths", {})
    col_rows = {}
    col_width = []
    for i in range(bx):
        widths = {}
        for j in range(by):
            for row in ("n", "s"):
                key = f"{i},{j},{row}"
                widths[(j, row)] = explicit.get(key) or partition(parcel_rng, None, *style["lot_width"], per_row)
        target = max(sum(v) for v in widths.values())
        for k, v in widths.items():
            v = list(v)
            v[-1] += target - sum(v)  # last lot absorbs the remainder so rows align on the block edge
            widths[k] = v
        col_rows[i] = widths
        col_width.append(target)
    row_depth = [recipe.get("lot_depth") or parcel_rng.randint(*style["lot_depth"]) for _ in range(by)]
    xs, x = [], margin
    for i in range(bx + 1):
        xs.append(x)
        x += corridor + (col_width[i] if i < bx else 0)
    ys, y = [], margin
    for j in range(by + 1):
        ys.append(y)
        y += corridor + (2 * row_depth[j] if j < by else 0)
    W, H = x + margin, y + margin
    surface = style["road_surface"]
    terrain = {}
    biome_seed = stream_seed(seed, "terrain", district_id)
    for cy in range(H):
        for cx in range(W):
            terrain[(cx, cy)] = edge_biome(style["edge_biome"], biome_seed, cx, cy)
    roads, intersections = [], []
    road_rects = []
    for k, ry in enumerate(ys):
        rect = [xs[0], ry, xs[-1] + corridor - xs[0], corridor]
        roads.append({"id": f"{prefix}.road.h{k}", "axis": "h", "rect": rect, "surface": surface, "lanes": 2,
                      "sidewalk_width": sw, "curbs": style["curbs"]})
        road_rects.append(rect)
    for k, rx in enumerate(xs):
        rect = [rx, ys[0], corridor, ys[-1] + corridor - ys[0]]
        roads.append({"id": f"{prefix}.road.v{k}", "axis": "v", "rect": rect, "surface": surface, "lanes": 2,
                      "sidewalk_width": sw, "curbs": style["curbs"]})
        road_rects.append(rect)
    # Block interiors are lots: paint them grass before any road surface.
    for i in range(bx):
        for j in range(by):
            for c in rect_cells([xs[i] + corridor, ys[j] + corridor, col_width[i], 2 * row_depth[j]]):
                terrain[tuple(c)] = "grass"
    for road in roads:
        for c in rect_cells(road["rect"]):
            terrain[tuple(c)] = "sidewalk" if sw else surface
    for road in roads:
        x0, y0, w0, h0 = road["rect"]
        band = [x0, y0 + sw, w0, h0 - 2 * sw] if road["axis"] == "h" else [x0 + sw, y0, w0 - 2 * sw, h0]
        for c in rect_cells(band):
            terrain[tuple(c)] = surface
    for i, rx in enumerate(xs):
        for k, ry in enumerate(ys):
            intersections.append({"id": f"{prefix}.isect.{i}_{k}", "rect": [rx, ry, corridor, corridor],
                                  "roads": [f"{prefix}.road.h{k}", f"{prefix}.road.v{i}"]})
    graph = []
    for k in range(len(ys)):
        for i in range(len(xs) - 1):
            graph.append([f"{prefix}.isect.{i}_{k}", f"{prefix}.isect.{i + 1}_{k}", f"{prefix}.road.h{k}"])
    for i in range(len(xs)):
        for k in range(len(ys) - 1):
            graph.append([f"{prefix}.isect.{i}_{k}", f"{prefix}.isect.{i}_{k + 1}", f"{prefix}.road.v{i}"])
    lots = []
    for j in range(by):
        for row in ("n", "s"):
            for i in range(bx):
                x = xs[i] + corridor
                ly = ys[j] + corridor + (0 if row == "n" else row_depth[j])
                widths = col_rows[i][(j, row)]
                for n, lw in enumerate(widths):
                    lot_id = f"{prefix}.lot.{len(lots) + 1:03d}"
                    lots.append({"id": lot_id, "rect": [x, ly, lw, row_depth[j]], "block": [i, j], "row": row,
                                 "front": "north" if row == "n" else "south",
                                 "road_id": f"{prefix}.road.h{j if row == 'n' else j + 1}",
                                 "corner": n == 0 or n == len(widths) - 1})
                    x += lw
    # ---- zoning and buildings
    buildings = []
    overrides = recipe.get("lot_overrides", {})
    for index, lot in enumerate(lots, 1):
        ov = overrides.get(lot["id"]) or overrides.get(str(index)) or {}
        zrng = Rng(stream_seed(seed, "zoning", lot["id"]))
        lot["building_id"] = None
        if ov.get("vacant"):
            lot["zoning"] = "vacant"
            continue
        use_corner = lot["corner"] and zrng.random() < 0.5
        program = ov.get("program") or zrng.weighted(style["corner_zoning"] if use_corner else style["zoning"])
        lx, ly, lw, ld = lot["rect"]
        margin_side = style["side_margin"]
        setback = zrng.randint(*style["front_setback"])
        avail = (lw - 2 * margin_side, ld - setback - 2)
        bid = f"{lot['id']}.b01"
        local, fallback = None, []
        if ov.get("fixture"):
            local = fixture_building(ov["fixture"], bid, seed)
            pad = local.get("vehicle_pad")
            need_w = local["size"][0] + (pad["rect"][2] if pad else 0)
            if need_w > avail[0] or local["size"][1] > avail[1]:
                raise GenerationError("E_FIXTURE_DOES_NOT_FIT", f"{ov['fixture']} in {lot['id']} ({avail})")
        else:
            for pid in [program] + ([] if program == "house_small" else ["house_small"]):
                try:
                    local = generate_building(pid, bid, seed, max_size=avail, style=style)
                    break
                except GenerationError as exc:
                    fallback.append(f"{pid}:{exc.code}")
            if local is None:
                lot["zoning"] = "vacant"
                lot["fallback"] = fallback
                continue
        lot["zoning"] = local["program"]
        if fallback:
            lot["fallback"] = fallback
        bw, bh = local["size"]
        pad = local.get("vehicle_pad")
        pad_w = pad["rect"][2] if pad else 0
        slack = avail[0] - bw - pad_w
        off = margin_side + (slack // 2 + zrng.randint(-1, 1) if slack > 2 else max(0, slack // 2))
        off = max(margin_side, min(off, lw - margin_side - bw - pad_w))
        rotation = 0 if lot["front"] == "south" else 2
        # rotation 2 mirrors x too: keep a vehicle pad inside the lot by offsetting the frame
        ox = lx + off + (pad_w if rotation == 2 and pad else 0)
        oy = ly + ld - setback - bh if lot["front"] == "south" else ly + setback
        b = transform_building(local, Frame((bw, bh), (ox, oy), rotation))
        b["lot_id"] = lot["id"]
        lot["building_id"] = b["id"]
        lot["setback"] = setback
        buildings.append(b)
    world = {"world_id": recipe["world_id"], "name": recipe.get("name", recipe["world_id"]), "world_seed": seed,
             "district_id": district_id, "prefix": prefix, "style_id": style_id, "bounds": [0, 0, W, H],
             "region": region, "roads": roads, "intersections": intersections, "road_graph": graph, "lots": lots,
             "buildings": buildings, "terrain": terrain, "fences": [], "props": [], "curb_cuts": []}
    paint_access(world, style)
    build_fences(world, style)
    place_props(world, style, cat)
    place_spawns(world)
    world["terrain_rows"] = [[terrain[(cx, cy)] for cx in range(W)] for cy in range(H)]
    world["asset_intake"] = intake(world, recipe)
    return world


def door_outside(door, side):
    (ax, ay), (bx, by) = door["a"], door["b"]
    mx, my = (ax + bx) / 2.0, (ay + by) / 2.0
    dx, dy = OUTWARD[side]
    return (int(math.floor(mx + dx * 0.5)), int(math.floor(my + dy * 0.5)))


def door_world_side(b, door):
    """World-facing side of an exterior door, from its segment against the footprint."""
    (ax, ay), (bx, by) = door["a"], door["b"]
    mx, my = (ax + bx) / 2.0, (ay + by) / 2.0
    cells = {tuple(c) for r in b["footprint"] for c in rect_cells(r)}
    if abs(ay - by) < 1e-9:
        return "south" if (int(math.floor(mx)), int(round(my)) - 1) in cells else "north"
    return "east" if (int(round(mx)) - 1, int(math.floor(my))) in cells else "west"


def paint_access(world, style):
    t = world["terrain"]
    lots = {l["id"]: l for l in world["lots"]}
    for b in world["buildings"]:
        for c in {tuple(c) for r in b["footprint"] for c in rect_cells(r)}:
            t[c] = "floor"
        lot = lots[b["lot_id"]]
        front = lot["front"]
        fdx, fdy = OUTWARD[front]
        for door in b["floors"][0]["doors"]:
            if "exterior" not in door["connects"]:
                continue
            side = door_world_side(b, door)
            door["world_side"] = side
            if side != front:
                continue
            (ax, ay), (bx2, by2) = door["a"], door["b"]
            lo, hi = (min(ax, bx2), max(ax, bx2)) if abs(ay - by2) < 1e-9 else (min(ay, by2), max(ay, by2))
            span = range(int(math.floor(lo + 0.25)), int(math.ceil(hi - 0.25)))
            kind = "driveway" if door["kind"] == "garage" else "path"
            ox, oy = door_outside(door, side)
            for k in span:
                cx, cy = (k, oy) if fdy else (ox, k)
                while t.get((cx, cy)) in ("grass", "path", "driveway", "dirt", "gravel", "forest", "field") and \
                        contains(lot["rect"], [cx, cy, 1, 1]):
                    t[(cx, cy)] = kind if t[(cx, cy)] != "driveway" else "driveway"
                    cx, cy = cx + fdx, cy + fdy
                if kind == "driveway":
                    world["curb_cuts"].append({"lot_id": lot["id"], "cell": [cx, cy]})
        pad = b.get("vehicle_pad")
        if pad:
            px, py, pw, ph = pad["rect"]
            for c in rect_cells(pad["rect"]):
                t[tuple(c)] = "driveway"
            cols = range(px, px + pw) if fdy else range(py, py + ph)
            start = (py + ph) if fdy > 0 else (py - 1) if fdy < 0 else None
            for k in cols:
                cx, cy = (k, start) if fdy else ((px + pw) if fdx > 0 else px - 1, k)
                while contains(lot["rect"], [cx, cy, 1, 1]) and t.get((cx, cy)) != "floor":
                    t[(cx, cy)] = "driveway"
                    cx, cy = cx + fdx, cy + fdy


def build_fences(world, style):
    if style["fences"] == "none":
        return
    lines = {}
    bmap = {b["id"]: b for b in world["buildings"]}
    for lot in world["lots"]:
        lx, ly, lw, ld = lot["rect"]
        back_y = ly if lot["front"] == "south" else ly + ld
        lines.setdefault(("h", back_y), []).append((lx, lx + lw))
        if style["fences"] != "side_and_back" or not lot.get("building_id"):
            continue
        b = bmap[lot["building_id"]]
        fys = [r[1] for r in b["footprint"]] + [r[1] + r[3] for r in b["footprint"]]
        if lot["front"] == "south":
            span = (ly, max(fys))
        else:
            span = (min(fys), ly + ld)
        for sx in (lx, lx + lw):
            lines.setdefault(("v", sx), []).append(span)
    n = 0
    for (axis, line) in sorted(lines):
        spans = sorted(lines[(axis, line)])
        merged = []
        for lo, hi in spans:
            if merged and lo <= merged[-1][1]:
                merged[-1][1] = max(merged[-1][1], hi)
            else:
                merged.append([lo, hi])
        for lo, hi in merged:
            n += 1
            a, b = ([lo, line], [hi, line]) if axis == "h" else ([line, lo], [line, hi])
            world["fences"].append({"id": f"{world['prefix']}.fence.{n:03d}", "kind": "fence_wood", "a": a, "b": b})


def world_navgrid(world, include_props=True):
    g = NavGrid()
    for b in world["buildings"]:
        f0 = b["floors"][0]
        for r in f0["rooms"]:
            for c in rect_cells(r["rect"]):
                g.owner[tuple(c)] = r["id"]
        for d in f0["doors"]:
            g.open_edges.update(door_units(d, DOOR_PASS))
        for item in f0["furniture"]:
            g.blocked.update(map(tuple, rect_cells(item["rect"])))
        for s in b.get("stairs", []):
            g.blocked.update(map(tuple, rect_cells(s["rect"])))
    for f in world["fences"]:
        axis, line, lo, hi = seg_key(f["a"], f["b"])
        for k in range(int(lo), int(hi)):
            g.fence_edges.add((axis, int(line), k))
    for c, t in world["terrain"].items():
        if t not in WALKABLE:
            g.blocked.add(c)
    if include_props:
        for p in world["props"]:
            g.blocked.update(map(tuple, rect_cells(p["rect"])))
    return g


def place_props(world, style, cat):
    """Vegetation, street furniture and parked cars; each placement must keep every walkable cell connected."""
    t = world["terrain"]
    W, H = world["bounds"][2], world["bounds"][3]
    bounds = (0, 0, W, H)
    grid = world_navgrid(world)
    start = next(c for c, v in sorted(t.items()) if v in ("sidewalk", "asphalt", "gravel"))
    reach = grid.flood([start], bounds)
    near_building = set()
    for b in world["buildings"]:
        for r in b["footprint"]:
            near_building.update(map(tuple, rect_cells([r[0] - 1, r[1] - 1, r[2] + 2, r[3] + 2])))
    fence_cells = set()
    for f in world["fences"]:
        axis, line, lo, hi = seg_key(f["a"], f["b"])
        for k in range(int(lo), int(hi)):
            fence_cells.update({(k, int(line) - 1), (k, int(line))} if axis == "h" else {(int(line) - 1, k), (int(line), k)})
    counter = [0]
    # Mandatory exits stay clear: no prop on any cell directly outside an exterior door.
    protected = set()
    for b in world["buildings"]:
        footprint = {tuple(c) for r in b["footprint"] for c in rect_cells(r)}
        for d in b["floors"][0]["doors"]:
            if "exterior" in d["connects"]:
                for u in door_units(d, 0.25):
                    protected.update(c for c in unit_sides(u) if c not in footprint)

    def add(ptype, cell, rng_seed):
        nonlocal reach
        f = cat["furniture"][ptype]
        cells = set(map(tuple, rect_cells([cell[0], cell[1], *f["tiles"]])))
        if cells & protected:
            return None
        if any(c in grid.blocked or c not in reach or t.get(c) not in WALKABLE for c in cells):
            return None
        if ptype not in ("vehicle", "vehicle_h") and any(t.get(c) in ("path", "driveway") for c in cells):
            return None
        for c in cells:
            grid.blocked.add(c)
        new_reach = grid.flood([start], bounds)
        if len(new_reach) != len(reach) - len(cells):
            for c in cells:
                grid.blocked.discard(c)
            return None
        reach = new_reach
        counter[0] += 1
        item = make_item(cat, world["prefix"], 0, counter[0], ptype, None, cell)
        item["id"] = f"{world['prefix']}.prop.{counter[0]:04d}"
        item.pop("room")
        if item["container"]:
            item["loot_seed"] = rng_seed
            item["initial_contents"] = roll_loot(cat, item["loot_profile"], rng_seed, None)
        world["props"].append(item)
        return item

    seed = world["world_seed"]
    for lot in world["lots"]:
        vrng = Rng(stream_seed(seed, "vegetation", lot["id"]))
        prng = Rng(stream_seed(seed, "props", lot["id"]))
        lx, ly, lw, ld = lot["rect"]
        yard = [tuple(c) for c in rect_cells(lot["rect"]) if t[tuple(c)] == "grass" and tuple(c) not in near_building]
        for c in vrng.shuffled(sorted(yard))[: int(len(yard) * style["tree_density"])]:
            if c not in fence_cells or vrng.random() < 0.3:
                add("tree", c, 0)
        front_row = ly + ld - 1 if lot["front"] == "south" else ly
        paths = sorted(c for c in rect_cells([lx, front_row, lw, 1]) if t[tuple(c)] == "path")
        if paths and lot.get("building_id"):
            px, py = paths[0]
            for dx in (-1, 1, -2, 2):
                if add("mailbox", (px + dx, py), 0):
                    break
        if lot.get("building_id") and prng.random() < 0.7:
            cands = sorted(c for c in near_building if contains(lot["rect"], [c[0], c[1], 1, 1]) and t[c] == "grass")
            for c in prng.shuffled(cands)[:6]:
                if add("trash_bin", c, stream_seed(seed, "loot", lot["id"], "bin")):
                    break
        if style["street_trees"] and lot["corner"]:
            add("streetlight", (lx + lw // 2, front_row), 0)
        for c in vrng.shuffled(sorted(yard))[: int(len(yard) * style["bush_density"])]:
            add("bush", c, 0)
    # Margins: forests carry dense original placeholder trees, parkland sparse ones.
    mrng = Rng(stream_seed(seed, "vegetation", "margin"))
    margin_cells = sorted(c for c, v in t.items() if v in ("forest", "grass") and not any(
        contains(l["rect"], [c[0], c[1], 1, 1]) for l in world["lots"]) and not any(contains(r["rect"], [c[0], c[1], 1, 1]) for r in world["roads"]))
    for c in margin_cells:
        density = 0.32 if t[c] == "forest" else 0.03
        if mrng.random() < density:
            add("tree", c, 0)
    # Parked/abandoned cars on horizontal roads (outside intersections and curb cuts).
    crng = Rng(stream_seed(seed, "props", "cars"))
    cuts = {tuple(c["cell"]) for c in world["curb_cuts"]}
    sw = style["sidewalk_width"]
    for road in world["roads"]:
        if road["axis"] != "h":
            continue
        x0, y0, w0, h0 = road["rect"]
        lane_y = y0 + sw if crng.random() < 0.5 else y0 + h0 - sw - 2
        for x in range(x0 + 8, x0 + w0 - 10, 9):
            if crng.random() < style["parked_car_chance"]:
                cells = rect_cells([x, lane_y, 4, 2])
                if any(any(contains(i["rect"], [c[0], c[1], 1, 1]) for i in world["intersections"]) for c in cells):
                    continue
                if any((c[0], y0 + k) in cuts for c in cells for k in range(-1, h0 + 1)):
                    continue
                car = add("vehicle_h", (x, lane_y), stream_seed(seed, "loot", road["id"], x))
    for b in world["buildings"]:
        pad = b.get("vehicle_pad")
        if pad:
            px, py, pw, ph = pad["rect"]
            ptype = "vehicle_h" if pw >= 4 else "vehicle"
            lot = next(l for l in world["lots"] if l["id"] == b["lot_id"])
            fdy = OUTWARD[lot["front"]][1]
            for step in range(0, 8):
                if add(ptype, (px, py + fdy * step), stream_seed(seed, "loot", b["id"], "pad")):
                    break


def place_spawns(world):
    t = world["terrain"]
    grid = world_navgrid(world)
    srng = Rng(stream_seed(world["world_seed"], "spawns", world["district_id"]))
    lots = [l for l in world["lots"] if l.get("building_id")]
    first = next((l for l in lots if l["front"] == "south"), lots[0] if lots else None)
    spawn = None
    if first:
        lx, ly, lw, ld = first["rect"]
        ys = range(ly + ld, ly + ld + 3) if first["front"] == "south" else range(ly - 1, ly - 4, -1)
        paths = [c for c in rect_cells(first["rect"]) if t[tuple(c)] == "path"]
        cx = paths[0][0] if paths else lx + lw // 2
        for y in ys:
            if t.get((cx, y)) in ("sidewalk", "asphalt", "gravel") and (cx, y) not in grid.blocked:
                spawn = [cx + 0.5, y + 0.5]
                break
    if spawn is None:
        c = next(c for c, v in sorted(t.items()) if v in ("sidewalk", "asphalt", "gravel") and c not in grid.blocked)
        spawn = [c[0] + 0.5, c[1] + 0.5]
    world["spawn"] = spawn
    points = []
    for b in world["buildings"]:
        f0 = b["floors"][0]
        rooms = {r["id"]: r for r in f0["rooms"]}
        for zone in b["spawn_zones"]:
            if zone["z"] != 0:
                continue
            rx, ry, rw, rh = rooms[zone["room"]]["rect"]
            free = sorted((c for c in rect_cells([rx, ry, rw, rh]) if tuple(c) not in grid.blocked),
                          key=lambda c: (abs(c[0] + 0.5 - rx - rw / 2) + abs(c[1] + 0.5 - ry - rh / 2), c))
            if free:
                points.append({"id": zone["id"], "pos": [free[0][0] + 0.5, free[0][1] + 0.5], "context": zone["context"],
                               "building_id": b["id"], "indoor": True})
    road_cells = sorted(c for c, v in t.items() if v in ("asphalt", "gravel") and c not in grid.blocked
                        and abs(c[0] + 0.5 - spawn[0]) + abs(c[1] + 0.5 - spawn[1]) > 12)
    for n, c in enumerate(srng.shuffled(road_cells)[:6]):
        points.append({"id": f"{world['prefix']}.spawn.street{n:02d}", "pos": [c[0] + 0.5, c[1] + 0.5], "context": "street", "indoor": False})
    order = srng.shuffled(points)
    # Interleave so a small runtime cap still mixes indoor and street infected.
    indoor = [p for p in order if p["indoor"]]
    outdoor = [p for p in order if not p["indoor"]]
    mixed = []
    while indoor or outdoor:
        if outdoor:
            mixed.append(outdoor.pop(0))
        if indoor:
            mixed.append(indoor.pop(0))
    world["spawn_points"] = mixed


# ---------------------------------------------------------------- validation
def validate_world(world):
    cat = catalog()
    checks = []

    def check(name, ok, detail=""):
        checks.append({"check": name, "ok": bool(ok), "detail": detail})

    W, H = world["bounds"][2], world["bounds"][3]
    ids = [world["world_id"], world["district_id"]]
    ids += [r["id"] for r in world["roads"]] + [i["id"] for i in world["intersections"]] + [l["id"] for l in world["lots"]]
    ids += [f["id"] for f in world["fences"]] + [p["id"] for p in world["props"]] + [s["id"] for s in world["spawn_points"]]
    for b in world["buildings"]:
        ids.append(b["id"])
        for f in b["floors"]:
            ids += [r["id"] for r in f["rooms"]] + [d["id"] for d in f["doors"]] + [w["id"] for w in f["windows"]] + [i["id"] for i in f["furniture"]]
        ids += [s["id"] for s in b.get("stairs", [])]
    dup = sorted({i for i in ids if ids.count(i) > 1}) if len(ids) != len(set(ids)) else []
    check("unique_ids", not dup, f"{len(ids)} ids" + (f" duplicates={dup[:5]}" if dup else ""))
    lot_overlap = [(a["id"], b["id"]) for n, a in enumerate(world["lots"]) for b in world["lots"][n + 1:] if overlaps(a["rect"], b["rect"])]
    check("no_overlapping_parcels", not lot_overlap, str(lot_overlap[:3]))
    road_overlap = [l["id"] for l in world["lots"] for r in world["roads"] if overlaps(l["rect"], r["rect"])]
    check("parcels_clear_of_roads", not road_overlap, str(road_overlap[:3]))
    inside = all(contains(world["bounds"], l["rect"]) for l in world["lots"])
    check("parcels_inside_bounds", inside)
    road_ids = {r["id"]: r for r in world["roads"]}
    frontage = []
    for l in world["lots"]:
        x, y, w, h = l["rect"]
        edge = [x, y - 1, w, 1] if l["front"] == "north" else [x, y + h, w, 1]
        if not overlaps(edge, road_ids[l["road_id"]]["rect"]):
            frontage.append(l["id"])
    check("every_parcel_has_road_frontage", not frontage, str(frontage[:3]))
    nodes = {i["id"] for i in world["intersections"]}
    adj = {n: set() for n in nodes}
    for a, b, _ in world["road_graph"]:
        adj[a].add(b)
        adj[b].add(a)
    seen, stack = set(), [sorted(nodes)[0]]
    while stack:
        n = stack.pop()
        if n not in seen:
            seen.add(n)
            stack.extend(adj[n] - seen)
    check("road_network_connected", seen == nodes, f"{len(seen)}/{len(nodes)} intersections")
    lots = {l["id"]: l for l in world["lots"]}
    bad_fit, b_overlap = [], []
    for n, b in enumerate(world["buildings"]):
        lot = lots[b["lot_id"]]
        for r in b["footprint"] + ([b["vehicle_pad"]["rect"]] if b.get("vehicle_pad") else []):
            if not contains(lot["rect"], r):
                bad_fit.append(b["id"])
        for o in world["buildings"][n + 1:]:
            if any(overlaps(r1, r2) for r1 in b["footprint"] for r2 in o["footprint"]):
                b_overlap.append((b["id"], o["id"]))
    check("buildings_inside_parcels", not bad_fit, str(bad_fit[:3]))
    check("no_overlapping_buildings", not b_overlap, str(b_overlap[:3]))
    reports = [validate_building(b, cat["rules"]) for b in world["buildings"]]
    bad = [e for r in reports for e in r["errors"]]
    check("building_structure_world_space", not bad, "; ".join(e["code"] + " " + e["detail"] for e in bad[:4]))
    grid = world_navgrid(world)
    bounds = (0, 0, W, H)
    spawn = (int(world["spawn"][0]), int(world["spawn"][1]))
    check("spawn_walkable", spawn not in grid.blocked and world["terrain"].get(spawn) in WALKABLE, str(spawn))
    reach = grid.flood([spawn], bounds)
    entr = []
    for b in world["buildings"]:
        for d in b["floors"][0]["doors"]:
            if "exterior" in d["connects"]:
                side = d.get("world_side") or "south"
                c = door_outside(d, side)
                if c not in reach:
                    entr.append(d["id"])
    check("building_entrances_reachable", not entr, str(entr[:4]))
    unreachable_rooms, unreachable_items = [], []
    for b in world["buildings"]:
        f0 = b["floors"][0]
        for r in f0["rooms"]:
            if not any(tuple(c) in reach for c in rect_cells(r["rect"])):
                unreachable_rooms.append(r["id"])
        for item in f0["furniture"]:
            cells = set(map(tuple, rect_cells(item["rect"])))
            if not any((c[0] + dx, c[1] + dy) in reach for c in cells for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                unreachable_items.append(item["id"])
    check("all_ground_rooms_reachable_from_spawn", not unreachable_rooms, str(unreachable_rooms[:4]))
    check("all_ground_furniture_and_containers_reachable", not unreachable_items, str(unreachable_items[:4]))
    stairs_ok = all(tuple(s["lower"]["entry"]) in reach for b in world["buildings"] for s in b.get("stairs", []))
    check("stairs_reachable_from_spawn", stairs_ok)
    props_ok = [p["id"] for p in world["props"] if p["container"] and not any(
        (c[0] + dx, c[1] + dy) in reach for c in map(tuple, rect_cells(p["rect"])) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))]
    check("exterior_containers_reachable", not props_ok, str(props_ok[:3]))
    walk = [c for c, v in world["terrain"].items() if v in WALKABLE and c not in grid.blocked]
    lot_cells = set()
    for l in world["lots"]:
        lot_cells.update(map(tuple, rect_cells(l["rect"])))
    road_cells = set()
    for r in world["roads"]:
        road_cells.update(map(tuple, rect_cells(r["rect"])))
    orphan = [c for c in walk if (c in lot_cells or c in road_cells) and c not in reach]
    check("no_walkable_pockets_in_streets_or_parcels", not orphan, f"{len(orphan)} cells e.g. {orphan[:3]}")
    adj_err = adjacency_errors(world["terrain"])
    check("terrain_adjacency_rules", not adj_err, "; ".join(adj_err[:3]))
    refs = []
    room_ids = {r["id"] for b in world["buildings"] for f in b["floors"] for r in f["rooms"]}
    for b in world["buildings"]:
        for f in b["floors"]:
            for d in f["doors"]:
                refs += [x for x in d["connects"] if x != "exterior" and x not in room_ids]
            refs += [i["room"] for i in f["furniture"] if i["room"] not in room_ids]
            refs += [w["room"] for w in f["windows"] if w["room"] not in room_ids]
        door_ids = {d["id"] for f in b["floors"] for d in f["doors"]}
        refs += [e["door_id"] for e in b["entrances"] if e["door_id"] not in door_ids]
        refs += [s[e]["room"] for s in b.get("stairs", []) for e in ("lower", "upper") if s[e]["room"] not in room_ids]
    bids = {b["id"] for b in world["buildings"]}
    refs += [l["building_id"] for l in world["lots"] if l.get("building_id") and l["building_id"] not in bids]
    refs += [s["building_id"] for s in world["spawn_points"] if s.get("building_id") and s["building_id"] not in bids]
    check("no_invalid_cross_references", not refs, str(refs[:4]))
    try:
        bindings()
        check("v2_asset_bindings_valid_no_invented_ids", True)
    except GenerationError as exc:
        check("v2_asset_bindings_valid_no_invented_ids", False, str(exc))
    ai = world.get("asset_intake", {})
    calib = [p["package_id"] for p in ai.get("packages", []) if p["stage"] == "CALIBRATION"]
    check("v2_no_calibration_assets_outside_isolated_fixture", not calib or ai.get("isolated_calibration_fixture") is True, str(calib))
    playable = W <= PLAYABLE_LIMIT and H <= PLAYABLE_LIMIT
    check("fits_single_scene_save_bounds", playable, f"{W}x{H} (limit {PLAYABLE_LIMIT})")
    return {"ok": all(c["ok"] for c in checks), "checks": checks,
            "summary": {"buildings": len(world["buildings"]), "lots": len(world["lots"]), "roads": len(world["roads"]),
                        "rooms": sum(len(f["rooms"]) for b in world["buildings"] for f in b["floors"]),
                        "containers": sum(1 for b in world["buildings"] for f in b["floors"] for i in f["furniture"] if i["container"]),
                        "props": len(world["props"]), "fences": len(world["fences"]), "bounds": [W, H],
                        "generator_version": GENERATOR_VERSION}}
