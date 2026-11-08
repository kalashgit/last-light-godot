"""Floor-plan data structures, structural shell compilation and parcel transforms.

A building is authored in a local frame (front facing local south) on an
integer tile grid. Walls are not authored: they are derived from room
ownership of cells so collision, rendering and validation cannot disagree.
"""
from __future__ import annotations

from .core import GenerationError, interval_overlap, r6, rect_cells, seg_key

SIDES = ("north", "east", "south", "west")


def room_edge(rect, side):
    x, y, w, h = rect
    return {"north": ("h", y, x, x + w), "south": ("h", y + h, x, x + w),
            "west": ("v", x, y, y + h), "east": ("v", x + w, y, y + h)}[side]


def shared_edges(a, b):
    """Axis-aligned segments where two rects touch (0 or 1 for rectangles)."""
    out = []
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    for line_a, line_b in ((ax + aw, bx), (ax, bx + bw)):
        if line_a == line_b:
            lo, hi = max(ay, by), min(ay + ah, by + bh)
            if hi > lo:
                out.append(("v", line_a, lo, hi))
    for line_a, line_b in ((ay + ah, by), (ay, by + bh)):
        if line_a == line_b:
            lo, hi = max(ax, bx), min(ax + aw, bx + bw)
            if hi > lo:
                out.append(("h", line_a, lo, hi))
    return out


def segment_from(axis, line, center, width):
    lo, hi = center - width / 2.0, center + width / 2.0
    if axis == "h":
        return [r6(lo), r6(line)], [r6(hi), r6(line)]
    return [r6(line), r6(lo)], [r6(line), r6(hi)]


def make_door(building_id, floor, door_index, room_a, room_b, center, width, kind="interior", side=None):
    """Place a door on the edge shared by room_a and room_b (or room_a's exterior side)."""
    rooms = {r["code"]: r for r in floor["rooms"]}
    if room_a not in rooms or (room_b != "exterior" and room_b not in rooms):
        raise GenerationError("E_DOOR_UNKNOWN_ROOM", f"{room_a}<->{room_b}")
    if room_b == "exterior":
        if side not in SIDES:
            raise GenerationError("E_DOOR_SIDE", room_a)
        candidates = [room_edge(rooms[room_a]["rect"], side)]
    else:
        candidates = shared_edges(rooms[room_a]["rect"], rooms[room_b]["rect"])
    for axis, line, lo, hi in candidates:
        if lo - 1e-6 <= center - width / 2.0 and center + width / 2.0 <= hi + 1e-6:
            a, b = segment_from(axis, line, center, width)
            target = "exterior" if room_b == "exterior" else rooms[room_b]["id"]
            return {"id": f"{building_id}.f{floor['z']}.d{door_index:02d}", "kind": kind, "a": a, "b": b,
                    "connects": [rooms[room_a]["id"], target], "width": r6(width),
                    "state": {"open": False, "locked": False, "barricade_socket": kind != "opening"}}
    raise GenerationError("E_DOOR_OFF_EDGE", f"{room_a}<->{room_b} center={center} width={width}")


def make_window(building_id, floor, index, room_code, side, center, width, flags=None):
    rooms = {r["code"]: r for r in floor["rooms"]}
    axis, line, lo, hi = room_edge(rooms[room_code]["rect"], side)
    if not (lo + 0.1 <= center - width / 2.0 and center + width / 2.0 <= hi - 0.1):
        raise GenerationError("E_WINDOW_OFF_EDGE", f"{room_code} {side} {center}")
    a, b = segment_from(axis, line, center, width)
    w = {"id": f"{building_id}.f{floor['z']}.w{index:02d}", "room": rooms[room_code]["id"], "a": a, "b": b,
         "side": side, "state": {"broken": False, "boarded": False, "privacy": False}}
    for key, value in (flags or {}).items():
        if key in w["state"]:
            w["state"][key] = bool(value)
    return w


def owner_grid(floor):
    grid = {}
    for room in floor["rooms"]:
        for cell in rect_cells(room["rect"]):
            if cell in grid:
                raise GenerationError("E_ROOM_OVERLAP", f"{room['id']} {cell}")
            grid[cell] = room["id"]
    return grid


def door_intervals(floor, include_openings=True):
    by_line = {}
    for door in floor["doors"]:
        if not include_openings and door["kind"] == "opening":
            continue
        axis, line, lo, hi = seg_key(door["a"], door["b"])
        by_line.setdefault((axis, line), []).append((lo, hi))
    return by_line


def compile_walls(floor):
    """Derive wall segments from room ownership minus door/opening intervals."""
    grid = owner_grid(floor)
    units = {}
    for (cx, cy), owner in grid.items():
        for dx, dy, axis, line, k in ((0, -1, "h", cy, cx), (0, 1, "h", cy + 1, cx),
                                      (-1, 0, "v", cx, cy), (1, 0, "v", cx + 1, cy)):
            other = grid.get((cx + dx, cy + dy))
            if other != owner:
                key = (axis, line, k)
                pair = tuple(sorted(x for x in (owner, other) if x))
                units[key] = {"exterior": other is None, "rooms": pair}
    merged = []
    for key in sorted(units):
        axis, line, k = key
        info = units[key]
        if merged and merged[-1]["axis"] == axis and merged[-1]["line"] == line and merged[-1]["hi"] == k \
                and merged[-1]["exterior"] == info["exterior"]:
            merged[-1]["hi"] = k + 1
        else:
            merged.append({"axis": axis, "line": line, "lo": k, "hi": k + 1, "exterior": info["exterior"]})
    cuts = door_intervals(floor)
    walls = []
    for seg in merged:
        pieces = [(float(seg["lo"]), float(seg["hi"]))]
        for lo, hi in sorted(cuts.get((seg["axis"], seg["line"]), [])):
            nxt = []
            for p_lo, p_hi in pieces:
                if interval_overlap(p_lo, p_hi, lo, hi) <= 0:
                    nxt.append((p_lo, p_hi))
                    continue
                if lo > p_lo:
                    nxt.append((p_lo, lo))
                if hi < p_hi:
                    nxt.append((hi, p_hi))
            pieces = nxt
        for lo, hi in pieces:
            if hi - lo < 0.02:
                continue
            if seg["axis"] == "h":
                a, b = [r6(lo), r6(seg["line"])], [r6(hi), r6(seg["line"])]
            else:
                a, b = [r6(seg["line"]), r6(lo)], [r6(seg["line"]), r6(hi)]
            walls.append({"a": a, "b": b, "exterior": seg["exterior"]})
    return walls


# ---------------------------------------------------------------- transforms
class Frame:
    """Local building frame -> world. r rotates clockwise in 90 degree steps."""

    FRONT = {0: "south", 1: "west", 2: "north", 3: "east"}

    def __init__(self, size, origin, rotation):
        self.w, self.h = size
        self.ox, self.oy = origin
        self.r = rotation % 4

    @property
    def world_size(self):
        return (self.h, self.w) if self.r % 2 else (self.w, self.h)

    def point(self, p):
        x, y = p
        if self.r == 1:
            x, y = self.h - y, x
        elif self.r == 2:
            x, y = self.w - x, self.h - y
        elif self.r == 3:
            x, y = y, self.w - x
        return [r6(x + self.ox), r6(y + self.oy)]

    def rect(self, rect):
        x, y, w, h = rect
        a, b = self.point((x, y)), self.point((x + w, y + h))
        x0, y0, x1, y1 = min(a[0], b[0]), min(a[1], b[1]), max(a[0], b[0]), max(a[1], b[1])
        return [int(round(x0)), int(round(y0)), int(round(x1 - x0)), int(round(y1 - y0))]

    def cell(self, c):
        p = self.point((c[0] + 0.5, c[1] + 0.5))
        return [int(p[0] // 1), int(p[1] // 1)]

    def side(self, local_side):
        order = ["south", "west", "north", "east"]
        return order[(order.index(local_side) + self.r) % 4]


def transform_building(local, frame):
    """Return a deep-transformed copy of a local building blueprint in world space."""
    out = {k: v for k, v in local.items() if k not in ("floors", "stairs", "footprint", "vehicle_pad")}
    out["frame"] = {"origin": [frame.ox, frame.oy], "rotation": frame.r, "local_size": [frame.w, frame.h],
                    "front": frame.side("south")}
    out["footprint"] = [frame.rect(r) for r in local["footprint"]]
    if local.get("vehicle_pad"):
        out["vehicle_pad"] = {"side": frame.side(local["vehicle_pad"]["side"]), "rect": frame.rect(local["vehicle_pad"]["rect"])}
    out["stairs"] = []
    for s in local.get("stairs", []):
        t = dict(s)
        t["rect"] = frame.rect(s["rect"])
        t["lower"] = dict(s["lower"], entry=frame.cell(s["lower"]["entry"]))
        t["upper"] = dict(s["upper"], entry=frame.cell(s["upper"]["entry"]))
        out["stairs"].append(t)
    floors = []
    for f in local["floors"]:
        g = {"z": f["z"], "cutouts": [frame.rect(r) for r in f.get("cutouts", [])]}
        g["rooms"] = [dict(r, rect=frame.rect(r["rect"])) for r in f["rooms"]]
        g["doors"] = [dict(d, a=frame.point(d["a"]), b=frame.point(d["b"])) for d in f["doors"]]
        g["windows"] = [dict(w, a=frame.point(w["a"]), b=frame.point(w["b"]), side=frame.side(w["side"])) for w in f["windows"]]
        g["furniture"] = []
        for item in f["furniture"]:
            t = dict(item, rect=frame.rect(item["rect"]))
            if "solid_rect" in item:
                sx, sy, sw, sh = item["solid_rect"]
                a, b = frame.point((sx, sy)), frame.point((sx + sw, sy + sh))
                t["solid_rect"] = [min(a[0], b[0]), min(a[1], b[1]), r6(abs(b[0] - a[0])), r6(abs(b[1] - a[1]))]
            g["furniture"].append(t)
        g["walls"] = compile_walls(g)
        floors.append(g)
    out["floors"] = floors
    return out
