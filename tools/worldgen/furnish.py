"""Contextual furniture placement and initial container contents (W04-C).

Worker 05 owns object behaviour; this module only places *defined* catalog
instances with footprint, clearance, utility and container metadata.
"""
from __future__ import annotations

from collections import deque

from .core import GenerationError, Rng, r6, rect_cells
from .validate import DOOR_CLEAR, NEI, TALL_M, door_units, unit_sides


def make_item(cat, building_id, z, index, ftype, room_id, cell):
    if ftype not in cat["furniture"]:
        raise GenerationError("E_UNKNOWN_FURNITURE", ftype)
    f = cat["furniture"][ftype]
    w, h = f["tiles"]
    x, y = cell
    inset = f.get("solid_inset", 0.08)
    item = {"id": f"{building_id}.f{z}.o{index:03d}", "type": ftype, "room": room_id, "rect": [x, y, w, h],
            "solid_rect": [r6(x + inset), r6(y + inset), r6(w - 2 * inset), r6(h - 2 * inset)],
            "asset_id": f.get("asset_id"), "art": f.get("art", "factory_sprite"), "label": f["label"],
            "height_m": f["height_m"], "container": bool(f.get("container")), "utility": list(f.get("utility", []))}
    if item["container"]:
        item["loot_profile"] = f["loot_profile"]
    return item


def roll_loot(cat, profile, seed, condition):
    rng = Rng(seed)
    scale = {"looted": 0.35, "damaged": 0.8, "boarded": 0.9}.get(condition, 1.0)
    out = {}
    for item_id, lo, hi, chance in cat["loot"][profile]:
        if rng.random() < chance * scale:
            count = rng.randint(max(1, lo), max(1, hi))
            out[item_id] = out.get(item_id, 0) + count
    return out


class RoomContext:
    """Per-floor occupancy used while furnishing one room at a time."""

    def __init__(self, building, floor):
        self.floor = floor
        self.room_cells = {}
        for room in floor["rooms"]:
            self.room_cells[room["id"]] = set(map(tuple, rect_cells(room["rect"])))
        self.occupied = set()
        for item in floor["furniture"]:
            self.occupied.update(map(tuple, rect_cells(item["rect"])))
        self.stairs = set()
        for s in building.get("stairs", []):
            self.stairs.update(map(tuple, rect_cells(s["rect"])))
        self.clear = set()
        self.door_cells = {}
        all_cells = set().union(*self.room_cells.values()) if self.room_cells else set()
        for d in floor["doors"]:
            for u in door_units(d, DOOR_CLEAR):
                for c in unit_sides(u):
                    if c in all_cells:
                        self.clear.add(c)
                        self.door_cells.setdefault(c, d["id"])
        self.window_cells = set()
        for w in floor["windows"]:
            ax, ay = w["a"]
            bx, by = w["b"]
            if abs(ay - by) < 1e-9:
                for x in range(int(min(ax, bx)), int(max(ax, bx) + 0.999)):
                    self.window_cells.update({(x, int(ay) - 1), (x, int(ay))})
            else:
                for y in range(int(min(ay, by)), int(max(ay, by) + 0.999)):
                    self.window_cells.update({(int(ax) - 1, y), (int(ax), y)})

    def room_ok(self, room_id, extra):
        """Room stays one connected free region touching every door; every item keeps access."""
        cells = self.room_cells[room_id]
        blocked = (self.occupied | extra | self.stairs) & cells
        free = cells - blocked
        entries = [c for c in cells if c in self.clear]
        if not entries:
            entries = sorted(free)[:1]
        if any(e in blocked for e in entries):
            return False
        seen = set(entries[:1])
        q = deque(entries[:1])
        while q:
            c = q.popleft()
            for dx, dy in NEI:
                n = (c[0] + dx, c[1] + dy)
                if n in free and n not in seen:
                    seen.add(n)
                    q.append(n)
        if seen != free or any(e not in seen for e in entries):
            return False
        items = [set(map(tuple, rect_cells(i["rect"]))) for i in self.floor["furniture"] if i["room"] == room_id]
        if extra:
            items.append(extra)
        for icells in items:
            if not any((c[0] + dx, c[1] + dy) in seen for c in icells for dx, dy in NEI):
                return False
        return True


def candidate_cells(room_rect, tiles, anchor):
    rx, ry, rw, rh = room_rect
    w, h = tiles
    out = []
    for y in range(ry, ry + rh - h + 1):
        for x in range(rx, rx + rw - w + 1):
            touches = [x == rx, y == ry, x + w == rx + rw, y + h == ry + rh]
            n = sum(touches)
            if anchor == "wall" and n == 0:
                continue
            if anchor == "corner" and not ((touches[0] or touches[2]) and (touches[1] or touches[3])):
                continue
            if anchor == "center" and n > 0:
                continue
            out.append((x, y))
    return out


def try_place(cat, building, ctx, room, ftype, anchor, rng, max_candidates=80):
    f = cat["furniture"][ftype]
    cands = rng.shuffled(candidate_cells(room["rect"], f["tiles"], anchor))[:max_candidates]
    for cell in cands:
        cells = set(map(tuple, rect_cells([cell[0], cell[1], *f["tiles"]])))
        if cells & (ctx.occupied | ctx.clear | ctx.stairs):
            continue
        if f["height_m"] >= TALL_M and cells & ctx.window_cells:
            continue
        if not ctx.room_ok(room["id"], cells):
            continue
        z = ctx.floor["z"]
        item = make_item(cat, building["id"], z, len(ctx.floor["furniture"]) + 1, ftype, room["id"], cell)
        ctx.floor["furniture"].append(item)
        ctx.occupied |= cells
        return item
    return None


def place_fixed(cat, building, ctx, room, ftype, cell):
    """Strategy-mandated placement (aisle shelving, parked vehicle). Validated like any other."""
    f = cat["furniture"][ftype]
    cells = set(map(tuple, rect_cells([cell[0], cell[1], *f["tiles"]])))
    if not cells <= ctx.room_cells[room["id"]] or cells & (ctx.occupied | ctx.clear | ctx.stairs):
        return None
    if not ctx.room_ok(room["id"], cells):
        return None
    item = make_item(cat, building["id"], ctx.floor["z"], len(ctx.floor["furniture"]) + 1, ftype, room["id"], cell)
    ctx.floor["furniture"].append(item)
    ctx.occupied |= cells
    return item


def furnish_floor(cat, building, floor, rng):
    ctx = RoomContext(building, floor)
    rules = cat["rules"]["rooms"]
    for room in floor["rooms"]:
        area = room["rect"][2] * room["rect"][3]
        for rule in rules.get(room["type"], []):
            if area < rule.get("min_area", 0):
                continue
            n = 1 if rule.get("required") else rng.randint(*rule.get("count", [0, 1]))
            for _ in range(n):
                placed = None
                for ftype in rule.get("any_of", [rule.get("type")]):
                    placed = try_place(cat, building, ctx, room, ftype, rule["anchor"], rng)
                    if placed:
                        break
                if not placed and rule.get("required"):
                    raise GenerationError("E_FURNITURE_MANDATORY", f"{room['id']}:{rule.get('type') or rule['any_of']}")
    return ctx


def assign_loot(cat, building, loot_seed_fn):
    for floor in building["floors"]:
        for item in floor["furniture"]:
            if item["container"]:
                item["loot_seed"] = loot_seed_fn(item["id"])
                item["initial_contents"] = roll_loot(cat, item["loot_profile"], item["loot_seed"], building.get("condition"))
