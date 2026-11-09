"""Structural, access and connectivity validation on the logical tile grid.

The same NavGrid powers building-level checks (rooms, doors, furniture,
stairs) and world-level checks (roads, parcels, fences, props). Every
failure carries a stable error code so tools and tests can assert on it.
"""
from __future__ import annotations

import math
from collections import deque

from .core import interval_overlap, rect_cells, seg_key
from .plan import compile_walls, owner_grid

DOOR_PASS = 0.5      # unit edge is traversable when a door covers >= half of it
DOOR_CLEAR = 0.25    # unit edge counts for door clearance when covered >= a quarter
MIN_DOOR_WIDTH = 0.85
TALL_M = 1.2
CIRCULATION = {"hall", "corridor", "landing", "front"}
NEI = ((1, 0), (-1, 0), (0, 1), (0, -1))


def unit_edge(c1, c2):
    (x1, y1), (x2, y2) = c1, c2
    if y1 == y2:
        return ("v", max(x1, x2), y1)
    return ("h", max(y1, y2), x1)


def door_units(door, threshold):
    axis, line, lo, hi = seg_key(door["a"], door["b"])
    line = int(round(line))
    out = []
    for k in range(math.floor(lo), math.ceil(hi)):
        if interval_overlap(k, k + 1, lo, hi) >= threshold - 1e-9:
            out.append((axis, line, k))
    return out


def unit_sides(unit):
    axis, line, k = unit
    return ((k, line - 1), (k, line)) if axis == "h" else ((line - 1, k), (line, k))


class NavGrid:
    def __init__(self):
        self.owner = {}          # cell -> region id (absent = exterior)
        self.blocked = set()     # cells occupied by solids
        self.open_edges = set()  # door/opening unit edges between different owners
        self.fence_edges = set() # unit edges blocked even within one owner

    def own(self, cell):
        return self.owner.get(cell, "exterior")

    def passable(self, a, b):
        if b in self.blocked:
            return False
        e = unit_edge(a, b)
        if e in self.fence_edges:
            return False
        return self.own(a) == self.own(b) or e in self.open_edges

    def flood(self, starts, bounds, extra_blocked=frozenset()):
        x0, y0, x1, y1 = bounds
        seen = set()
        q = deque()
        for s in starts:
            if s not in self.blocked and s not in extra_blocked and s not in seen:
                seen.add(s)
                q.append(s)
        while q:
            c = q.popleft()
            for dx, dy in NEI:
                n = (c[0] + dx, c[1] + dy)
                if n in seen or n in extra_blocked or not (x0 <= n[0] < x1 and y0 <= n[1] < y1):
                    continue
                if self.passable(c, n):
                    seen.add(n)
                    q.append(n)
        return seen


def bbox(rects, grow=1):
    xs0 = min(r[0] for r in rects) - grow
    ys0 = min(r[1] for r in rects) - grow
    xs1 = max(r[0] + r[2] for r in rects) + grow
    ys1 = max(r[1] + r[3] for r in rects) + grow
    return xs0, ys0, xs1, ys1


def floor_navgrid(building, floor, grid=None):
    grid = grid or NavGrid()
    for cell, rid in owner_grid(floor).items():
        grid.owner[cell] = rid
    for door in floor["doors"]:
        grid.open_edges.update(door_units(door, DOOR_PASS))
    for item in floor["furniture"]:
        grid.blocked.update(map(tuple, rect_cells(item["rect"])))
    for stair in building.get("stairs", []):
        grid.blocked.update(map(tuple, rect_cells(stair["rect"])))
    return grid


def validate_building(b, rules):
    """Validate one (local or world-space) building blueprint. Returns a report dict."""
    errors = []

    def err(code, detail):
        errors.append({"code": code, "detail": f"{b['id']}: {detail}"})

    exterior_ok = set(rules["exterior_door_rooms"])
    floors = {f["z"]: f for f in b["floors"]}
    stats = {"rooms": 0, "doors": 0, "windows": 0, "furniture": 0, "containers": 0, "walls": 0}
    footprint_cells = set()
    for rect in b["footprint"]:
        footprint_cells.update(map(tuple, rect_cells(rect)))
    for f in b["floors"]:
        z = f["z"]
        try:
            grid_owner = owner_grid(f)
        except ValueError as exc:
            err("E_ROOM_OVERLAP", str(exc))
            continue
        rooms = {r["id"]: r for r in f["rooms"]}
        room_cells = set(grid_owner)
        cut = set()
        for rect in f.get("cutouts", []):
            cut.update(map(tuple, rect_cells(rect)))
        if room_cells != footprint_cells - cut:
            err("E_FOOTPRINT_COVERAGE", f"z{z} rooms do not tile footprint ({len(room_cells)} vs {len(footprint_cells - cut)})")
        stats["rooms"] += len(rooms)
        stats["doors"] += len(f["doors"])
        stats["windows"] += len(f["windows"])
        stats["furniture"] += len(f["furniture"])
        # ---- doors
        door_lines = {}
        clear_cells = set()
        for d in f["doors"]:
            axis, line, lo, hi = seg_key(d["a"], d["b"])
            if d["kind"] not in ("interior", "exterior", "garage", "opening"):
                err("E_DOOR_KIND", d["id"])
            if hi - lo < MIN_DOOR_WIDTH - 1e-9:
                err("E_DOOR_TOO_NARROW", d["id"])
            for other in door_lines.get((axis, line), []):
                if interval_overlap(lo, hi, *other) > 0:
                    err("E_DOOR_OVERLAP", d["id"])
            door_lines.setdefault((axis, line), []).append((lo, hi))
            units = door_units(d, DOOR_PASS)
            if not units:
                err("E_DOOR_OFF_GRID", d["id"])
            want = set(d["connects"])
            for unit in units:
                s1, s2 = unit_sides(unit)
                got = {grid_owner.get(s1, "exterior"), grid_owner.get(s2, "exterior")}
                if got != want:
                    err("E_DOOR_WRONG_ROOMS", f"{d['id']} joins {sorted(got)} not {sorted(want)}")
                    break
            if "exterior" in want:
                inner = rooms.get(next((x for x in want if x != "exterior"), ""), {})
                if inner and inner["type"] not in exterior_ok:
                    err("E_EXTERIOR_DOOR_ROOM", f"{d['id']} opens into {inner['type']}")
                if z != 0:
                    err("E_UPPER_EXTERIOR_DOOR", d["id"])
            for unit in door_units(d, DOOR_CLEAR):
                clear_cells.update(c for c in unit_sides(unit) if c in grid_owner)
        if z == 0 and not any("exterior" in d["connects"] and d["kind"] != "opening" for d in f["doors"]):
            err("E_NO_EXTERIOR_EXIT", "ground floor has no exterior door")
        # ---- windows
        window_cells = set()
        for w in f["windows"]:
            axis, line, lo, hi = seg_key(w["a"], w["b"])
            for other in door_lines.get((axis, line), []):
                if interval_overlap(lo, hi, *other) > 0:
                    err("E_WINDOW_ON_DOOR", w["id"])
            for k in range(math.floor(lo), math.ceil(hi)):
                if interval_overlap(k, k + 1, lo, hi) <= 0:
                    continue
                s1, s2 = unit_sides((axis, int(round(line)), k))
                owners = [grid_owner.get(s1), grid_owner.get(s2)]
                if sorted(owners, key=str) != sorted([w["room"], None], key=str):
                    err("E_WINDOW_NOT_EXTERIOR", w["id"])
                    break
                window_cells.update(c for c in (s1, s2) if c in grid_owner)
        # ---- walls: no duplicates/overlaps, no gaps, never across doors
        walls = f.get("walls") or compile_walls(f)
        stats["walls"] += len(walls)
        wall_lines = {}
        for wall in walls:
            axis, line, lo, hi = seg_key(wall["a"], wall["b"])
            for other in wall_lines.get((axis, line), []):
                if interval_overlap(lo, hi, *other) > 1e-6:
                    err("E_WALL_OVERLAP", f"{axis}{line} {lo}-{hi}")
            for other in door_lines.get((axis, line), []):
                if interval_overlap(lo, hi, *other) > 1e-6:
                    err("E_WALL_ACROSS_DOOR", f"{axis}{line} {lo}-{hi}")
            wall_lines.setdefault((axis, line), []).append((lo, hi))
        for (cx, cy), owner in grid_owner.items():
            for dx, dy in NEI:
                n = (cx + dx, cy + dy)
                if grid_owner.get(n) == owner:
                    continue
                axis, line, k = unit_edge((cx, cy), n)
                covered = sum(interval_overlap(k, k + 1, lo, hi) for lo, hi in wall_lines.get((axis, line), []))
                covered += sum(interval_overlap(k, k + 1, lo, hi) for lo, hi in door_lines.get((axis, line), []))
                if covered < 1 - 1e-6:
                    err("E_WALL_GAP", f"z{z} edge {axis}{line}@{k}")
        # ---- furniture placement
        nav = floor_navgrid(b, f)
        stair_cells = set()
        for s in b.get("stairs", []):
            stair_cells.update(map(tuple, rect_cells(s["rect"])))
        occupied = {}
        for item in f["furniture"]:
            cells = list(map(tuple, rect_cells(item["rect"])))
            room = rooms.get(item["room"])
            if not room or any(grid_owner.get(c) != item["room"] for c in cells):
                err("E_FURNITURE_OUTSIDE_ROOM", item["id"])
            for c in cells:
                if c in occupied:
                    err("E_FURNITURE_OVERLAP", f"{item['id']} vs {occupied[c]}")
                occupied[c] = item["id"]
                if c in clear_cells:
                    err("E_FURNITURE_BLOCKS_DOOR", item["id"])
                if c in stair_cells:
                    err("E_FURNITURE_ON_STAIR", item["id"])
                if c in window_cells and item.get("height_m", 0) >= TALL_M:
                    err("E_TALL_FURNITURE_AT_WINDOW", item["id"])
            if item.get("container"):
                stats["containers"] += 1
        # ---- connectivity
        cells_all = list(grid_owner)
        if not cells_all:
            err("E_EMPTY_FLOOR", f"z{z}")
            continue
        bounds = bbox([[c[0], c[1], 1, 1] for c in cells_all], grow=2)
        if z == 0:
            starts = [(x, y) for x in range(bounds[0], bounds[2]) for y in range(bounds[1], bounds[3])
                      if (x, y) not in grid_owner and (x, y) not in nav.blocked]
        else:
            starts = [tuple(s["upper"]["entry"]) for s in b.get("stairs", []) if s["upper"]["z"] == z]
            if not starts:
                err("E_FLOOR_NO_STAIR", f"z{z}")
        reach = nav.flood(starts, bounds)
        for cell, owner in grid_owner.items():
            if cell not in nav.blocked and cell not in reach:
                err("E_UNREACHABLE_CELL", f"z{z} {cell} in {owner}")
                break
        for room in f["rooms"]:
            if not any(c in reach for c in map(tuple, rect_cells(room["rect"]))):
                err("E_UNREACHABLE_ROOM", room["id"])
        for d in f["doors"]:
            if not any(all(s in reach for s in unit_sides(u)) or
                       ("exterior" in d["connects"] and any(s in reach for s in unit_sides(u)))
                       for u in door_units(d, DOOR_PASS)):
                err("E_BLOCKED_DOOR", d["id"])
        for item in f["furniture"]:
            cells = set(map(tuple, rect_cells(item["rect"])))
            access = [(c[0] + dx, c[1] + dy) for c in cells for dx, dy in NEI]
            if not any(a in reach and a not in cells and grid_owner.get(a) == item["room"] for a in access):
                err("E_UNREACHABLE_FURNITURE", item["id"])
        for s in b.get("stairs", []):
            for end in ("lower", "upper"):
                if s[end]["z"] != z:
                    continue
                entry = tuple(s[end]["entry"])
                rid = rooms.get(s[end]["room"]) and s[end]["room"]
                srect = s["rect"]
                adjacent = any((entry[0] + dx, entry[1] + dy) in set(map(tuple, rect_cells(srect))) for dx, dy in NEI)
                if not rid or grid_owner.get(entry) != s[end]["room"] or not adjacent:
                    err("E_STAIR_ENTRY", f"{s['id']} {end}")
                elif entry not in reach:
                    err("E_STAIR_UNREACHABLE", f"{s['id']} {end}")
                if not all(grid_owner.get(c) == s[end]["room"] for c in map(tuple, rect_cells(srect))):
                    err("E_STAIR_MISALIGNED", f"{s['id']} {end} rect not inside {s[end]['room']}")
        # ---- privacy: bedrooms are never mandatory passages
        if z == 0:
            entry_doors = [d for d in f["doors"] if "exterior" in d["connects"]]
            start_room = next((x for x in entry_doors[0]["connects"] if x != "exterior"), None) if entry_doors else None
        else:
            start_room = next((s["upper"]["room"] for s in b.get("stairs", []) if s["upper"]["z"] == z), None)
        if start_room:
            bedrooms = set()
            for room in f["rooms"]:
                if room["type"] == "bedroom" and room["id"] != start_room:
                    bedrooms.update(map(tuple, rect_cells(room["rect"])))
            outside = {(x, y) for x in range(bounds[0], bounds[2]) for y in range(bounds[1], bounds[3]) if (x, y) not in grid_owner}
            inner = nav.flood([c for c in map(tuple, rect_cells(rooms[start_room]["rect"])) if c not in nav.blocked],
                              bounds, frozenset(bedrooms | outside))
            for room in f["rooms"]:
                if room["type"] != "bedroom" and not any(c in inner for c in map(tuple, rect_cells(room["rect"]))):
                    has_own_exit = any(room["id"] in d["connects"] and "exterior" in d["connects"] for d in f["doors"])
                    if not has_own_exit:
                        err("E_PRIVATE_PASSAGE", f"{room['id']} only reachable through a bedroom")
    for s in b.get("stairs", []):
        if s["lower"]["z"] not in floors or s["upper"]["z"] not in floors or s["upper"]["z"] != s["lower"]["z"] + 1:
            err("E_STAIR_FLOORS", s["id"])
    ids = [b["id"]]
    for f in b["floors"]:
        ids += [r["id"] for r in f["rooms"]] + [d["id"] for d in f["doors"]] + [w["id"] for w in f["windows"]] + [i["id"] for i in f["furniture"]]
    ids += [s["id"] for s in b.get("stairs", [])]
    if len(ids) != len(set(ids)):
        err("E_DUPLICATE_ID", "building-local IDs collide")
    return {"building_id": b["id"], "ok": not errors, "errors": errors, "stats": stats}
