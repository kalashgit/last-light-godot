"""Building factory (W04-A/B): frozen LAB A fixtures and procedural floor plans.

Every building is produced in a local frame with its front on local south.
Procedural layouts are rejected on any validation error and retried with a
bounded, deterministic attempt counter.
"""
from __future__ import annotations

import copy

from .catalog import catalog
from .core import GENERATOR_VERSION, SCHEMA_BUILDING, GenerationError, Rng, derive_seed, r6
from .furnish import RoomContext, assign_loot, furnish_floor, make_item, place_fixed
from .plan import compile_walls, make_door, make_window, shared_edges
from .validate import validate_building

MAX_ATTEMPTS = 24
SIZE_ORDER = ["living", "kitchen", "den", "bedroom", "office", "utility", "pantry", "bathroom"]
MATERIALS_ROOF = {"gable": "shingle_asphalt", "hip": "shingle_slate", "offset_gable": "shingle_asphalt", "flat": "membrane_tar"}
FLOOR_BY_ROOM = {"kitchen": "tile_ceramic", "bathroom": "tile_ceramic", "restroom": "tile_ceramic", "utility": "concrete_sealed",
                 "garage": "concrete_stained", "bay": "concrete_stained", "stock": "concrete_sealed", "plant": "concrete_sealed",
                 "sales": "vinyl_tile", "front": "vinyl_tile", "work": "concrete_stained", "pantry": "tile_ceramic"}


def subtract_rect(outer, cut):
    """Disjoint rect decomposition of outer minus cut (cut must lie inside outer)."""
    ox, oy, ow, oh = outer
    cx, cy, cw, ch = cut
    parts = [[ox, oy, cx - ox, oh], [cx + cw, oy, ox + ow - cx - cw, oh],
             [cx, oy, cw, cy - oy], [cx, cy + ch, cw, oy + oh - cy - ch]]
    return [p for p in parts if p[2] > 0 and p[3] > 0]


def base_record(building_id, program_id, template, source, seeds, size):
    cat = catalog()
    program = cat["programs"][program_id]
    rec = {"schema": SCHEMA_BUILDING, "generator_version": GENERATOR_VERSION, "id": building_id,
           "program": program_id, "archetype_id": program["archetype_id"], "template": template,
           "layout_source": source, "seeds": seeds, "size": list(size), "stairs": [], "floors": []}
    if "secondary_archetype_id" in program:
        rec["secondary_archetype_id"] = program["secondary_archetype_id"]
    return rec


def finish(rec, loot_seed_fn):
    cat = catalog()
    for floor in rec["floors"]:
        for room in floor["rooms"]:
            room.setdefault("floor_material", FLOOR_BY_ROOM.get(room["type"], "wood_oak"))
            room["essential"] = room["type"] in cat["rules"]["essential_rooms"]
        floor["walls"] = compile_walls(floor)
    assign_loot(cat, rec, loot_seed_fn)
    rec["entrances"] = [{"door_id": d["id"], "kind": d["kind"], "local_side": d.get("local_side")}
                        for d in rec["floors"][0]["doors"] if "exterior" in d["connects"]]
    rec["spawn_zones"] = [{"id": f"{r['id']}.spawn", "room": r["id"], "context": r["type"], "z": f["z"]}
                          for f in rec["floors"] for r in f["rooms"] if r["type"] in ("living", "bedroom", "sales", "bay", "garage", "stock")]
    return rec


# ---------------------------------------------------------------- LAB A
def fixture_building(fixture_id, building_id, world_seed=0):
    cat = catalog()
    fx = cat["lab_a"]["buildings"][fixture_id]
    w, h = fx["size"]
    seeds = {"layout": "frozen", "furnish": "frozen", "loot": derive_seed(world_seed, "loot", building_id)}
    rec = base_record(building_id, fx["program"], f"lab_a:{fixture_id}", "lab_a_frozen", seeds, (w, h))
    rec["fixture_version"] = cat["lab_a"]["fixture_version"]
    rec["name"] = fx["name"]
    footprint = [[0, 0, w, h]]
    for f in fx["floors"]:
        for cut in f.get("cutouts", []):
            footprint = [p for part in footprint for p in (subtract_rect(part, cut) if overlaps_inside(part, cut) else [part])]
    rec["footprint"] = footprint
    rec["roof"] = {"profile": fx["roof"], "material": MATERIALS_ROOF[fx["roof"]], "rects": copy.deepcopy(footprint)}
    rec["condition"] = fx["condition"]
    rec["materials"] = {"walls": "plaster_cream", "trim": "timber_painted", "roof": MATERIALS_ROOF[fx["roof"]]}
    if "vehicle_pad" in fx:
        rec["vehicle_pad"] = fx["vehicle_pad"]
    for f in fx["floors"]:
        z = f["z"]
        floor = {"z": z, "rooms": [], "doors": [], "windows": [], "furniture": []}
        for code, (rtype, rect) in f["rooms"].items():
            floor["rooms"].append({"id": f"{building_id}.f{z}.{code}", "code": code, "type": rtype, "rect": list(rect)})
        for i, d in enumerate(f["doors"], 1):
            a, b = d["connects"]
            door = make_door(building_id, floor, i, a, b, d["center"], d["width"], d.get("kind", "interior"), d.get("side"))
            if d.get("side"):
                door["local_side"] = d["side"]
            floor["doors"].append(door)
        for i, wdef in enumerate(f["windows"], 1):
            floor["windows"].append(make_window(building_id, floor, i, wdef["room"], wdef["side"], wdef["center"], wdef["width"],
                                                {k: wdef[k] for k in ("broken", "boarded", "privacy") if k in wdef}))
        rec["floors"].append(floor)
    for s in fx.get("stairs", []):
        rec["stairs"].append({"id": f"{building_id}.{s['id']}", "rect": list(s["rect"]),
                              "lower": {"z": s["lower"]["z"], "room": f"{building_id}.f{s['lower']['z']}.{s['lower']['room']}", "entry": list(s["lower"]["entry"])},
                              "upper": {"z": s["upper"]["z"], "room": f"{building_id}.f{s['upper']['z']}.{s['upper']['room']}", "entry": list(s["upper"]["entry"])}})
    for f, floor in zip(fx["floors"], rec["floors"]):
        owner = {}
        for room in floor["rooms"]:
            x, y, rw, rh = room["rect"]
            for cy in range(y, y + rh):
                for cx in range(x, x + rw):
                    owner[(cx, cy)] = room["id"]
        for i, (ftype, cx, cy) in enumerate(f["furniture"], 1):
            floor["furniture"].append(make_item(cat, building_id, f["z"], i, ftype, owner.get((cx, cy), "?"), (cx, cy)))
    finish(rec, lambda oid: derive_seed(world_seed, "loot", oid))
    report = validate_building(rec, cat["rules"])
    if not report["ok"]:
        raise GenerationError("E_FIXTURE_INVALID", "; ".join(e["code"] + " " + e["detail"] for e in report["errors"][:6]))
    return rec


def overlaps_inside(part, cut):
    return (cut[0] >= part[0] and cut[1] >= part[1] and cut[0] + cut[2] <= part[0] + part[2]
            and cut[1] + cut[3] <= part[1] + part[3])


# ---------------------------------------------------------------- procedural helpers
def split_span(rng, start, length, parts, minimum):
    """Split [start, start+length) into `parts` integer spans each >= minimum."""
    if parts * minimum > length:
        raise GenerationError("E_SPLIT", f"{length}/{parts}")
    cuts = []
    remaining = length
    pos = start
    for i in range(parts - 1):
        left = parts - i - 1
        hi = remaining - left * minimum
        size = rng.randint(minimum, hi) if rng.random() < 0.7 else max(minimum, min(hi, round(remaining / (left + 1))))
        cuts.append((pos, size))
        pos += size
        remaining -= size
    cuts.append((pos, remaining))
    return cuts


def door_centers(seg, width, avoid_cells):
    """Half- and whole-tile door centres on a segment whose clearance cells avoid `avoid_cells`."""
    axis, line, lo, hi = seg
    half = width / 2.0
    candidates = [k + 0.5 for k in range(int(lo), int(hi))] + [float(k) for k in range(int(lo) + 1, int(hi))]
    out = []
    for c in candidates:
        if not (lo + half - 1e-9 <= c <= hi - half + 1e-9):
            continue
        cells = set()
        for k in range(int(lo), int(hi)):
            if min(k + 1, c + half) - max(k, c - half) >= 0.25:
                cells.update(edge_side_cells(axis, line, k))
        if not cells & avoid_cells:
            out.append(c)
    return sorted(set(out))


def edge_side_cells(axis, line, k):
    return [(k, line - 1), (k, line)] if axis == "h" else [(line - 1, k), (line, k)]


def add_door(bid, floor, rng, code_a, code_b, avoid=frozenset(), kind="interior", side=None, width=None, prefer_center=False):
    rooms = {r["code"]: r for r in floor["rooms"]}
    if code_b == "exterior":
        from .plan import room_edge
        segs = [room_edge(rooms[code_a]["rect"], side)]
    else:
        segs = shared_edges(rooms[code_a]["rect"], rooms[code_b]["rect"])
    for seg in segs:
        length = seg[3] - seg[2]
        w = width or (1.2 if length >= 1.6 else 0.9)
        if length < w:
            continue
        centers = door_centers(seg, w, set(avoid))
        if not centers:
            continue
        if prefer_center:
            mid = (seg[2] + seg[3]) / 2.0
            center = min(centers, key=lambda c: (abs(c - mid), c))
        else:
            center = rng.choice(centers)
        door = make_door(bid, floor, len(floor["doors"]) + 1, code_a, code_b, center, w, kind, side)
        if side:
            door["local_side"] = side
        floor["doors"].append(door)
        return door
    return None


def connect_rooms(bid, floor, rng, hub_codes, avoid=frozenset()):
    """Door every room to a hub if adjacent, otherwise to an already-connected neighbour."""
    rooms = {r["code"]: r for r in floor["rooms"]}
    connected = set(hub_codes)
    pending = [c for c in rooms if c not in connected]
    for _ in range(len(pending) + 2):
        progress = False
        for code in list(pending):
            hubs = [h for h in hub_codes if shared_edges(rooms[code]["rect"], rooms[h]["rect"])]
            neighbours = hubs or sorted(
                (c for c in connected if shared_edges(rooms[code]["rect"], rooms[c]["rect"])),
                key=lambda c: (rooms[c]["type"] == "bedroom", rooms[c]["type"] == "bathroom", c))
            for other in neighbours:
                if add_door(bid, floor, rng, code, other, avoid):
                    connected.add(code)
                    pending.remove(code)
                    progress = True
                    break
        if not pending or not progress:
            break
    if pending:
        raise GenerationError("E_ROOM_DISCONNECTED", ",".join(sorted(pending)))


def windows_for(bid, floor, rng, footprint_size, skip_types=("hall", "corridor", "landing", "stock", "plant")):
    from .plan import room_edge
    w_total, h_total = footprint_size
    door_spans = {}
    for d in floor["doors"]:
        (ax, ay), (bx, by) = d["a"], d["b"]
        key = ("h", ay) if abs(ay - by) < 1e-9 else ("v", ax)
        door_spans.setdefault(key, []).append((min(ax, bx) if key[0] == "h" else min(ay, by), max(ax, bx) if key[0] == "h" else max(ay, by)))
    occupied = {(c[0], c[1]) for r in floor["rooms"] for c in [(x, y) for y in range(r["rect"][1], r["rect"][1] + r["rect"][3]) for x in range(r["rect"][0], r["rect"][0] + r["rect"][2])]}
    for room in floor["rooms"]:
        if room["type"] in skip_types:
            continue
        for side in rng.shuffled(["north", "south", "east", "west"])[: 2 if room["type"] not in ("bathroom", "restroom") else 1]:
            axis, line, lo, hi = room_edge(room["rect"], side)
            outward = (0, -1) if side == "north" else (0, 1) if side == "south" else (-1, 0) if side == "west" else (1, 0)
            # exterior only: every unit along the edge must face outside the building
            ok_units = []
            for k in range(lo, hi):
                cell = (k, line - 1) if axis == "h" else (line - 1, k)
                if side in ("north", "west"):
                    cell = (k, line) if axis == "h" else (line, k)
                out = (cell[0] + outward[0], cell[1] + outward[1])
                ok_units.append(out not in occupied)
            spans, start = [], None
            for i, ok in enumerate(ok_units + [False]):
                if ok and start is None:
                    start = i
                elif not ok and start is not None:
                    spans.append((lo + start, lo + i))
                    start = None
            spans = [s for s in spans if s[1] - s[0] >= 2]
            if not spans:
                continue
            s_lo, s_hi = max(spans, key=lambda s: (s[1] - s[0], s[0]))
            width = 1.0 if room["type"] in ("bathroom", "restroom") else min(2.0, round((s_hi - s_lo) * 0.4 * 2) / 2 or 1.0)
            center = (s_lo + s_hi) / 2.0
            blocked = any(lo_d - 0.2 < center + width / 2 and center - width / 2 < hi_d + 0.2
                          for lo_d, hi_d in door_spans.get((axis, float(line)), []))
            if blocked or center - width / 2 < s_lo + 0.1 or center + width / 2 > s_hi - 0.1:
                continue
            floor["windows"].append(make_window(bid, floor, len(floor["windows"]) + 1, room["code"], side, center, width,
                                                {"privacy": room["type"] in ("bathroom", "restroom")}))


def mirror_x(rec, width):
    def px(p):
        return [r6(width - p[0]), p[1]]
    for floor in rec["floors"]:
        for room in floor["rooms"]:
            x, y, w, h = room["rect"]
            room["rect"] = [width - x - w, y, w, h]
        for d in floor["doors"]:
            d["a"], d["b"] = sorted([px(d["a"]), px(d["b"])])
            if d.get("local_side") in ("east", "west"):
                d["local_side"] = "west" if d["local_side"] == "east" else "east"
        for w in floor["windows"]:
            w["a"], w["b"] = sorted([px(w["a"]), px(w["b"])])
            if w["side"] in ("east", "west"):
                w["side"] = "west" if w["side"] == "east" else "east"
    for s in rec["stairs"]:
        x, y, w, h = s["rect"]
        s["rect"] = [width - x - w, y, w, h]
        for end in ("lower", "upper"):
            ex, ey = s[end]["entry"]
            s[end]["entry"] = [width - 1 - ex, ey]
    rec["footprint"] = [[width - x - w, y, w, h] for x, y, w, h in rec["footprint"]]
    rec["mirrored"] = not rec.get("mirrored", False)


def assign_rooms(rng, zones, room_types):
    """Pair zones with room types by size; kitchen prefers the rear (north) edge."""
    zs = sorted(zones, key=lambda z: (-(z[2] * z[3]), z[1], z[0]))
    types = sorted(room_types, key=lambda t: (SIZE_ORDER.index(t) if t in SIZE_ORDER else 99, t))
    pairs = list(zip(types, zs))
    mins = catalog()["rules"]["min_room_cells"]
    for t, z in pairs:
        mw, mh = mins.get(t, [2, 2])
        if min(z[2], z[3]) < min(mw, mh) or max(z[2], z[3]) < max(mw, mh):
            raise GenerationError("E_ROOM_TOO_SMALL", f"{t} {z}")
    return pairs


# ---------------------------------------------------------------- strategies
def residential_spine(bid, program, rng, max_size):
    floors_n = program["floors"]
    gw = gd = 0
    if "garage" in program:
        gw, gd = 5, rng.randint(*program["garage"])
    W = min(rng.randint(*program["footprint_w"]), max_size[0] - gw)
    H = min(rng.randint(*program["footprint_h"]), max_size[1])
    if W < program["footprint_w"][0] or H < program["footprint_h"][0]:
        raise GenerationError("E_PARCEL_TOO_SMALL", f"{W}x{H}")
    hw = program["hall_width"]
    optional = [t for t in program.get("optional_rooms", []) if rng.random() < 0.5]
    types = list(program["rooms"]) + optional
    strip = floors_n == 1 and H >= 10 and rng.random() < 0.45 and len(types) >= 4
    lw = rng.randint(3, W - hw - 3)
    if W - lw - hw < 3:
        raise GenerationError("E_SPLIT", "right zone")
    y0 = rng.randint(3, 4) if strip else 0
    zones = []
    if strip:
        sx = rng.randint(4, W - 4)
        zones += [[0, 0, sx, y0], [sx, 0, W - sx, y0]]
    side_n = len(types) - (2 if strip else 0)
    left_n = max(1, min(2, side_n // 2 + (1 if rng.random() < 0.3 else 0)))
    right_n = side_n - left_n
    if right_n < 1 or right_n > 3:
        raise GenerationError("E_SPLIT", f"right_n={right_n}")
    for y, hh in split_span(rng, y0, H - y0, left_n, 3):
        zones.append([0, y, lw, hh])
    for y, hh in split_span(rng, y0, H - y0, right_n, 2 if right_n == 3 else 3):
        zones.append([lw + hw, y, W - lw - hw, hh])
    pairs = assign_rooms(rng, zones, types)
    # kitchens want the rear wall for a service door; swap with a rear living-type zone if needed
    kit = next((i for i, (t, z) in enumerate(pairs) if t == "kitchen"), None)
    if kit is not None and pairs[kit][1][1] != 0:
        for j, (t, z) in enumerate(pairs):
            if z[1] == 0 and t in ("living", "den", "bedroom") and min(pairs[kit][1][2:]) >= 3:
                pairs[kit], pairs[j] = (pairs[kit][0], z), (t, pairs[kit][1])
                break
    rec = {"floors": [], "stairs": []}
    floor = {"z": 0, "rooms": [{"id": f"{bid}.f0.HAL", "code": "HAL", "type": "hall", "rect": [lw, y0, hw, H - y0]}],
             "doors": [], "windows": [], "furniture": []}
    for i, (t, z) in enumerate(sorted(pairs, key=lambda p: (p[1][1], p[1][0])), 1):
        floor["rooms"].append({"id": f"{bid}.f0.R{i:02d}", "code": f"R{i:02d}", "type": t, "rect": list(z)})
    stair_cells = set()
    if floors_n == 2:
        sw, sh = program["stair"]
        srect = [lw + hw - sw, y0, sw, sh]
        entry = [lw + hw - sw, y0 + sh]
        stair_cells = {(x, y) for x in range(srect[0], srect[0] + sw) for y in range(srect[1], srect[1] + sh)}
        rec["stairs"].append({"id": f"{bid}.STAIR", "rect": srect,
                              "lower": {"z": 0, "room": f"{bid}.f0.HAL", "entry": entry},
                              "upper": {"z": 1, "room": f"{bid}.f1.CORR", "entry": list(entry)}})
    footprint = [[0, 0, W, H]]
    if gw:
        g = [W, H - gd, gw, gd]
        floor["rooms"].append({"id": f"{bid}.f0.GAR", "code": "GAR", "type": "garage", "rect": g})
        footprint.append(g)
    add_door(bid, floor, rng, "HAL", "exterior", stair_cells, "exterior", "south", 1.2,
             prefer_center=floors_n == 1)
    hubs = ["HAL"]
    codes = {r["code"]: r for r in floor["rooms"]}
    connect_rooms(bid, {**floor, "rooms": [r for r in floor["rooms"] if r["code"] != "GAR"]} | {"doors": floor["doors"]}, rng, hubs, stair_cells)
    for a in [r for r in floor["rooms"] if r["type"] == "living"]:
        for b in [r for r in floor["rooms"] if r["type"] == "kitchen"]:
            already = any({a["id"], b["id"]} == set(d["connects"]) for d in floor["doors"])
            edge = shared_edges(a["rect"], b["rect"])
            if edge and not already and edge[0][3] - edge[0][2] >= 2:
                add_door(bid, floor, rng, a["code"], b["code"], stair_cells)
    for k in [r for r in floor["rooms"] if r["type"] == "kitchen" and r["rect"][1] == 0]:
        add_door(bid, floor, rng, k["code"], "exterior", stair_cells, "exterior", "north", 1.2)
    if gw:
        inner = [r for r in floor["rooms"] if r["code"] not in ("GAR",) and r["type"] not in ("bedroom", "bathroom")
                 and shared_edges(r["rect"], codes["GAR"]["rect"])]
        if not inner or not add_door(bid, floor, rng, "GAR", rng.choice(sorted(r["code"] for r in inner))):
            raise GenerationError("E_GARAGE_ACCESS", "no non-private room touches the garage")
        if not add_door(bid, floor, rng, "GAR", "exterior", frozenset(), "garage", "south", 3.0, prefer_center=True):
            raise GenerationError("E_GARAGE_DOOR", "garage too narrow")
    rec["floors"].append(floor)
    if floors_n == 2:
        up_types = list(program["upper_rooms"]) + [t for t in program.get("upper_optional_rooms", []) if rng.random() < 0.4][:1]
        upper = {"z": 1, "rooms": [{"id": f"{bid}.f1.CORR", "code": "CORR", "type": "corridor", "rect": [lw, 0, hw, H]}],
                 "doors": [], "windows": [], "furniture": []}
        n_left = max(1, min(2, len(up_types) // 2))
        zones = [[0, y, lw, hh] for y, hh in split_span(rng, 0, H, n_left, 3)]
        zones += [[lw + hw, y, W - lw - hw, hh] for y, hh in split_span(rng, 0, H, len(up_types) - n_left, 3)]
        for i, (t, z) in enumerate(sorted(assign_rooms(rng, zones, up_types), key=lambda p: (p[1][1], p[1][0])), 1):
            upper["rooms"].append({"id": f"{bid}.f1.U{i:02d}", "code": f"U{i:02d}", "type": t, "rect": list(z)})
        connect_rooms(bid, upper, rng, ["CORR"], stair_cells)
        rec["floors"].append(upper)
    rec["footprint"] = footprint
    rec["size"] = [W + gw, H]
    return rec


def retail_front_back(bid, program, rng, max_size):
    W = min(rng.randint(*program["footprint_w"]), max_size[0])
    H = min(rng.randint(*program["footprint_h"]), max_size[1])
    if W < program["footprint_w"][0] or H < program["footprint_h"][0]:
        raise GenerationError("E_PARCEL_TOO_SMALL", f"{W}x{H}")
    sw, fd = rng.randint(5, 6), rng.randint(3, 4)
    mw, rw = W - sw, (sw) // 2
    rooms = [("SALES", "sales", [0, 0, mw, H - fd]), ("FRONT", "front", [0, H - fd, mw, fd]),
             ("STOCK", "stock", [mw, 0, sw, H - 3]), ("REST", "restroom", [mw, H - 3, rw, 3]),
             ("OFFICE", "office", [mw + rw, H - 3, sw - rw, 3])]
    floor = {"z": 0, "rooms": [{"id": f"{bid}.f0.{c}", "code": c, "type": t, "rect": r} for c, t, r in rooms],
             "doors": [], "windows": [], "furniture": []}
    add_door(bid, floor, rng, "FRONT", "exterior", kind="exterior", side="south", width=1.6, prefer_center=True)
    floor["doors"].append(make_door(bid, floor, len(floor["doors"]) + 1, "FRONT", "SALES", mw / 2.0, mw - 2.0, "opening"))
    for a, b in (("SALES", "STOCK"), ("STOCK", "REST"), ("STOCK", "OFFICE"), ("FRONT", "REST")):
        if not add_door(bid, floor, rng, a, b) and a != "FRONT":
            raise GenerationError("E_ROOM_DISCONNECTED", f"{a}-{b}")
    add_door(bid, floor, rng, "STOCK", "exterior", kind="exterior", side="north", width=1.2)
    return {"floors": [floor], "stairs": [], "footprint": [[0, 0, W, H]], "size": [W, H], "_sales": (mw, H - fd)}


def workshop_bay(bid, program, rng, max_size):
    W = min(rng.randint(*program["footprint_w"]), max_size[0])
    H = min(rng.randint(*program["footprint_h"]), max_size[1])
    if W < program["footprint_w"][0] or H < program["footprint_h"][0]:
        raise GenerationError("E_PARCEL_TOO_SMALL", f"{W}x{H}")
    bw = rng.randint(7, min(8, W - 5))
    rw, wh = W - bw, rng.randint(4, 5)
    rooms = [("BAY", "bay", [0, 0, bw, H]), ("WORK", "work", [bw, 0, rw, wh]),
             ("STOCK", "stock", [bw, wh, rw - 2, H - wh]), ("PLANT", "plant", [W - 2, wh, 2, H - wh])]
    floor = {"z": 0, "rooms": [{"id": f"{bid}.f0.{c}", "code": c, "type": t, "rect": r} for c, t, r in rooms],
             "doors": [], "windows": [], "furniture": []}
    add_door(bid, floor, rng, "BAY", "exterior", kind="garage", side="south", width=3.0, prefer_center=True)
    for a, b in (("BAY", "WORK"), ("BAY", "STOCK"), ("WORK", "STOCK"), ("STOCK", "PLANT")):
        if not add_door(bid, floor, rng, a, b):
            raise GenerationError("E_ROOM_DISCONNECTED", f"{a}-{b}")
    add_door(bid, floor, rng, "PLANT", "exterior", kind="exterior", side="east", width=1.2)
    return {"floors": [floor], "stairs": [], "footprint": [[0, 0, W, H]], "size": [W, H], "_bay": bw}


STRATEGIES = {"residential_spine": residential_spine, "retail_front_back": retail_front_back, "workshop_bay": workshop_bay}


def special_furniture(cat, rec, ctx, rng, plan):
    floor = rec["floors"][0]
    rooms = {r["code"]: r for r in floor["rooms"]}
    if "_sales" in plan:
        # Aisle runs: 1-tile shelves with >= 2 walkable tiles between faces (LAB A S01 rule).
        sx, sy, sw, sh = rooms["SALES"]["rect"]
        spacing = rng.choice([3, 4])
        x = sx + 2
        while x <= sx + sw - 3:
            for y in range(sy + 2, sy + sh - 2):
                place_fixed(cat, rec, ctx, rooms["SALES"], "retail_shelf", (x, y))
            x += spacing
    if "_bay" in plan:
        bay = rooms["BAY"]
        bx = bay["rect"][0] + (bay["rect"][2] - 2) // 2
        place_fixed(cat, rec, ctx, bay, "vehicle", (bx, 2))
    if "GAR" in rooms:
        g = rooms["GAR"]
        place_fixed(cat, rec, ctx, g, "vehicle", (g["rect"][0] + 2, g["rect"][1] + 1)) or \
            place_fixed(cat, rec, ctx, g, "vehicle", (g["rect"][0] + 1, g["rect"][1] + 1))


def generate_building(program_id, building_id, world_seed, max_size=(99, 99), style=None):
    """Generate a validated procedural building; bounded deterministic retries."""
    cat = catalog()
    if program_id not in cat["programs"]:
        raise GenerationError("E_UNKNOWN_PROGRAM", program_id)
    program = cat["programs"][program_id]
    rejected = []
    for attempt in range(MAX_ATTEMPTS):
        layout_seed = derive_seed(world_seed, "layout", building_id, attempt)
        rng = Rng(layout_seed)
        try:
            plan = STRATEGIES[program["strategy"]](building_id, program, rng, max_size)
            seeds = {"layout": layout_seed, "furnish": derive_seed(world_seed, "furnish", building_id, attempt),
                     "loot": derive_seed(world_seed, "loot", building_id)}
            rec = base_record(building_id, program_id, f"proc:{program_id}", "procedural", seeds, plan["size"])
            rec["floors"], rec["stairs"], rec["footprint"] = plan["floors"], plan["stairs"], plan["footprint"]
            profile = rng.choice(program["roof"])
            rec["roof"] = {"profile": profile, "material": MATERIALS_ROOF[profile], "rects": [list(r) for r in rec["footprint"]]}
            styles = (style or {}).get("materials", ["plaster_cream"])
            rec["materials"] = {"walls": rng.choice(styles), "trim": "timber_painted", "roof": MATERIALS_ROOF[profile]}
            cond = program["condition"]
            bias = (style or {}).get("condition_bias")
            rec["condition"] = bias if bias in cond and rng.random() < 0.5 else rng.choice(cond)
            if rng.random() < 0.5:
                mirror_x(rec, plan["size"][0])
            frng = Rng(seeds["furnish"])
            for floor in rec["floors"]:
                windows_for(building_id, floor, frng, plan["size"])
                if rec["condition"] in ("boarded", "damaged"):
                    for w in floor["windows"]:
                        w["state"]["boarded" if rec["condition"] == "boarded" else "broken"] = frng.random() < 0.6
            ctx = RoomContext(rec, rec["floors"][0])
            special_furniture(cat, rec, ctx, frng, plan)
            for floor in rec["floors"]:
                furnish_floor(cat, rec, floor, frng)
            finish(rec, lambda oid: derive_seed(world_seed, "loot", oid))
            report = validate_building(rec, cat["rules"])
            if report["ok"]:
                rec["generation"] = {"attempt": attempt, "rejected": rejected}
                return rec
            rejected.append(report["errors"][0]["code"])
        except GenerationError as exc:
            rejected.append(exc.code)
    raise GenerationError("E_LAYOUT_EXHAUSTED", f"{building_id} {program_id}: {rejected}")
