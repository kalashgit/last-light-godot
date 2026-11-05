"""Static architecture checks for the isolated five-building laboratory.

Run: python tools/validate_building_lab.py
This checks recipe topology and data, not Godot parsing, drawing or touch input.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
from collections import deque

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "assets/buildings/five_building_lab_v2.json"
FLOORS = {"wood_oak", "tile_ceramic", "concrete_stained", "vinyl_check", "asphalt_worn", "grass_sparse", "paver_gray"}
WALLS = {"plaster_cream", "concrete_block", "brick_aged", "metal_panel"}
ROOFS = {"shingle_asphalt", "standing_seam_metal", "flat_membrane"}
LOOT = {item["id"] for item in json.loads((ROOT / "assets/items/lab_items_v1.json").read_text())["items"]}


def box_intersects(a: tuple[float, ...], b: tuple[float, ...]) -> bool:
    return a[0] < b[2] and a[2] > b[0] and a[1] < b[3] and a[3] > b[1]


def box(x: float, y: float, w: float, h: float) -> tuple[float, ...]:
    return (x, y, x + w, y + h)


def require(condition: bool, description: str) -> None:
    if not condition:
        raise AssertionError(description)


def distance_to_segment(px: float, py: float, a: list[float], b: list[float]) -> float:
    dx, dy = b[0]-a[0], b[1]-a[1]
    t = max(0.0, min(1.0, ((px-a[0])*dx + (py-a[1])*dy) / max(dx*dx + dy*dy, .0001)))
    return math.dist((px, py), (a[0]+dx*t, a[1]+dy*t))


def verify_open_door_walkability(building: dict) -> None:
    """Simulate quarter-cell movement through every OPEN door and fixture collision."""
    w, h = building["size"]
    door_start = math.floor(w*.5)-1
    walls = [([0, 0], [w, 0]), ([0, 0], [0, h]), ([w, 0], [w, h])]
    for i in range(int(w)):
        if not door_start <= i < door_start+2:
            walls.append(([i, h], [i+1, h]))
    walls.extend((p["a"], p["b"]) for p in building["partitions"] if p.get("kind") != "door")
    furniture = [box(*f["pos"], *f["size"]) for f in building["fixtures"] if f.get("solid")]
    step = .25
    def walkable(cell: tuple[int, int]) -> bool:
        px, py = ((cell[0]+.5)*step, (cell[1]+.5)*step)
        if px < .27 or py < .27 or px > w-.27 or py > h-.27:
            return False
        if any(distance_to_segment(px, py, a, b) < .27 for a, b in walls):
            return False
        return not any(f[0]-.20 <= px <= f[2]+.20 and f[1]-.20 <= py <= f[3]+.20 for f in furniture)
    start = (round((door_start+1)/step)-2, round((h-.75)/step))
    require(walkable(start), f"{building['id']}: player cannot stand behind entrance")
    found = {start}
    pending = deque([start])
    while pending:
        x, y = pending.popleft()
        for n in ((x+1,y),(x-1,y),(x,y+1),(x,y-1)):
            if n not in found and walkable(n):
                found.add(n)
                pending.append(n)
    interior = [(x,y) for x in range(int(w/step)) for y in range(int(h/step)) if walkable((x,y))]
    require(len(found) >= .8*len(interior), f"{building['id']}: rooms not connected ({len(found)}/{len(interior)})")


def verify() -> None:
    data = json.loads(PATH.read_text())
    require(data.get("schema_version") == 2, "Unexpected recipe schema")
    require(data.get("projection") == "80x40_2to1", "Projection mismatch")
    buildings = data["buildings"]
    require(len(buildings) == 5, "Five distinct prototypes required")
    labels = [b["id"] for b in buildings]
    require(len(labels) == len(set(labels)), "Duplicate building ID")
    require(set(labels) == {"RESIDENTIAL HOUSE", "GARAGE / WORKSHOP", "SMALL SHOP", "GAS STATION", "ABANDONED OUTPOST"}, "Archetype mismatch")
    footprints = []
    solid_count = 0
    door_count = 0
    all_ids = set()
    loot_count = 0
    for building in buildings:
        name = building["id"]
        x, y = building["origin"]
        w, h = building["size"]
        require(w >= 5 and h >= 5, f"{name}: too small for an enterable prototype")
        bounds = box(x, y, w, h)
        require(not any(box_intersects(bounds, other) for other in footprints), f"{name}: overlapping footprint")
        footprints.append(bounds)
        require(building["wall"] in WALLS and building["roof"] in ROOFS, f"{name}: unknown wall or roof")
        require(building["floor"] in FLOORS, f"{name}: unknown floor")
        for zone in building["floor_zones"]:
            zx, zy = zone["pos"]
            zw, zh = zone["size"]
            require(zone["material"] in FLOORS, f"{name}: unknown floor zone")
            require(zx >= 0 and zy >= 0 and zw > 0 and zh > 0 and zx+zw <= w and zy+zh <= h, f"{name}: floor zone outside")
        for segment in building["partitions"]:
            a, b = segment["a"], segment["b"]
            require(all(0 <= p[0] <= w and 0 <= p[1] <= h for p in [a, b]), f"{name}: partition outside")
            require(a != b, f"{name}: zero-length partition")
            require(a[0] == b[0] or a[1] == b[1], f"{name}: diagonal partition unsupported")
            if segment.get("kind") == "door":
                door_count += 1
                require(math.dist(a, b) >= 1.0, f"{name}: interior doorway too narrow")
            else:
                require(segment.get("material", building["wall"]) in WALLS, f"{name}: unknown partition material")
        solid_fixtures = []
        for fixture in building["fixtures"]:
            stable_id = name+"/"+fixture["id"]
            require(stable_id not in all_ids, f"Duplicate stable fixture identity: {stable_id}")
            all_ids.add(stable_id)
            require(fixture["kind"] in {"counter", "bed", "sofa", "shelf", "crate", "storage"}, f"{name}: unsupported fixture type")
            if "loot" in fixture:
                require(fixture["loot"] in LOOT, f"{name}: unknown loot ID")
                require(fixture["kind"] not in {"bed", "sofa"}, f"{name}: rest furniture cannot be used as an item container")
                loot_count += 1
            fx, fy = fixture["pos"]
            fw, fh = fixture["size"]
            require(fw > 0 and fh > 0 and fx >= 0 and fy >= 0 and fx+fw <= w and fy+fh <= h, f"{name}: fixture outside")
            if fixture.get("solid"):
                solid_count += 1
                fbox = box(fx, fy, fw, fh)
                require(not any(box_intersects(fbox, other) for other in solid_fixtures), f"{name}: overlapping solid fixtures")
                solid_fixtures.append(fbox)
        # The center south entrance is generated by _add_structure in Godot.
        entrance_x = math.floor(w * .5)
        door_approach = box(entrance_x-0.5, h-1.5, 2.0, 1.5)
        require(not any(box_intersects(door_approach, f) for f in solid_fixtures), f"{name}: entry path obstructed")
        verify_open_door_walkability(building)
    for fixture in data["exterior_props"]:
        require(fixture["id"] not in all_ids, "Exterior prop identity collision")
        all_ids.add(fixture["id"])
        px, py = fixture["pos"]
        pw, ph = fixture["size"]
        require(not any(box_intersects(box(px, py, pw, ph), bounds) for bounds in footprints), "Exterior prop blocks a building footprint")
    mark_ids: set[str] = set()
    for mark in data.get("ground_marks", []):
        require(mark["id"] not in mark_ids, "Duplicate ground mark identity")
        mark_ids.add(mark["id"])
        require(mark["kind"] in {"road_center", "service_line", "tire_wear", "warning"}, "Invalid ground decal kind")
        require(mark["a"] != mark["b"], "Zero-length ground decal")
        require(all(-5 <= value <= 47 for coord in (mark["a"], mark["b"]) for value in coord), "Ground decal leaves compact lab")
    fences = data["fences"]
    gates = [f for f in fences if f.get("kind") == "gate"]
    require(len(gates) == 1, "Outpost should have one independently operable gate")
    for f in fences:
        a, b = f["a"], f["b"]
        require(a != b and (a[0] == b[0] or a[1] == b[1]), "Invalid fence segment")
    require(math.dist(gates[0]["a"], gates[0]["b"]) >= 2, "Outpost gate cannot be traversed")
    require(door_count >= 5 and solid_count >= 12, "Missing interactions or physical props")
    require(loot_count >= 8, "Too few searchable containers for laboratory survival tests")
    print(f"PASS: {len(buildings)} buildings, {door_count} interior doors, 1 gate, {solid_count} solid fixtures, {len(all_ids)} stable prop IDs, {loot_count} loot containers, {len(mark_ids)} ground decals")


if __name__ == "__main__":
    verify()
