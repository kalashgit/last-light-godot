extends RefCounted
## Deterministic module composition. Does not mint A00 IDs or approve any artwork.
const KITS_PATH := "res://data/neighborhood/modular_room_kits_v1.json"

var kits: Dictionary = {}

func _init() -> void:
    var data: Variant = JSON.parse_string(FileAccess.get_file_as_string(KITS_PATH))
    if data is Dictionary and data.get("schema", "") == "last_light.modular_room_kits.v1":
        kits = data

func _building_id(building: Dictionary) -> String:
    return str(building.get("id", building.get("instance_id", "")))

func _kind(raw: String) -> String:
    var name: String = raw.strip_edges().to_lower()
    var normalized: String = str(kits.get("aliases", {}).get(name, name))
    if kits.get("rooms", {}).has(normalized):
        return normalized
    for keyword in ["shop", "cashier", "retail", "shelf", "counter", "checkout"]:
        if keyword in name:
            return "retail"
    for keyword in ["medical", "hospital", "patient", "surgery", "pharmacy"]:
        if keyword in name:
            return "medical"
    for keyword in ["kitchen", "cook", "food"]:
        if keyword in name:
            return "kitchen"
    for keyword in ["dining", "cafe", "bar", "restaurant"]:
        if keyword in name:
            return "food_service"
    for keyword in ["power", "pump", "engine", "mechanic", "plant", "warehouse", "machine", "industrial", "generator", "mechanical"]:
        if keyword in name:
            return "industrial"
    for keyword in ["school", "class", "lecture", "training"]:
        if keyword in name:
            return "classroom"
    for keyword in ["bed", "sleep", "hotel", "motel"]:
        if keyword in name:
            return "bedroom"
    for keyword in ["office", "admin", "desk"]:
        if keyword in name:
            return "office"
    for keyword in ["bath", "toilet", "washroom"]:
        if keyword in name:
            return "bathroom"
    for keyword in ["storage", "locker", "closet", "stock"]:
        if keyword in name:
            return "storage"
    for keyword in ["lobby", "corridor", "entry", "hall", "vestibule"]:
        if keyword in name:
            return "hall"
    return "generic"

func _rooms_for(building: Dictionary, is_lab: bool, floor_index: int) -> Array:
    var rooms: Array = []
    var foot: Array = building["footprint"]
    var origin := Vector2(float(foot[0]), float(foot[1]))
    if is_lab:
        var source: Array = building.get("upper_rooms", []) if floor_index > 0 else building.get("rooms", [])
        for room in source:
            var dims: Array = room["rect"]
            rooms.append({"id": str(room["id"]), "type": str(room["type"]),
                "rect": [origin.x + float(dims[0]), origin.y + float(dims[1]), float(dims[2]), float(dims[3])]})
        return rooms
    var modules: Array = building.get("room_modules", [])
    if modules.is_empty():
        modules = ["generic"]
    var cols: int = 2 if modules.size() > 1 else 1
    var rows: int = ceili(float(modules.size()) / float(cols))
    var row_height: float = float(foot[3]) / float(rows)
    for i in range(modules.size()):
        var row_idx: int = int(i / cols)
        var row_start: int = row_idx * cols
        var row_count: int = mini(cols, modules.size() - row_start)
        var column: int = i - row_start
        var width: float = float(foot[2]) / float(row_count)
        rooms.append({"id": _building_id(building) + "/room/" + str(i),
            "type": str(modules[i]),
            "rect": [origin.x + width * column, origin.y + row_height * row_idx, width, row_height]})
    return rooms

func _as_rect(room: Dictionary) -> Rect2:
    var a: Array = room["rect"]
    return Rect2(float(a[0]), float(a[1]), float(a[2]), float(a[3]))

func _portals(rooms: Array) -> Array:
    var result: Array = []
    for i in range(rooms.size()):
        var a: Rect2 = _as_rect(rooms[i])
        for j in range(i + 1, rooms.size()):
            var b: Rect2 = _as_rect(rooms[j])
            var point := Vector2.ZERO
            var axis := ""
            if absf(a.end.x - b.position.x) < .01 or absf(b.end.x - a.position.x) < .01:
                var low: float = maxf(a.position.y, b.position.y)
                var high: float = minf(a.end.y, b.end.y)
                if high - low >= 1.5:
                    point = Vector2(b.position.x if absf(a.end.x - b.position.x) < .01 else a.position.x, (low + high) / 2.0)
                    axis = "vertical"
            elif absf(a.end.y - b.position.y) < .01 or absf(b.end.y - a.position.y) < .01:
                var low: float = maxf(a.position.x, b.position.x)
                var high: float = minf(a.end.x, b.end.x)
                if high - low >= 1.5:
                    point = Vector2((low + high) / 2.0, b.position.y if absf(a.end.y - b.position.y) < .01 else a.position.y)
                    axis = "horizontal"
            if not axis.is_empty():
                result.append({"a": rooms[i]["id"], "b": rooms[j]["id"], "axis": axis,
                    "point": [point.x, point.y], "half_width": 0.8})
    return result

func make_plan(building: Dictionary, is_lab: bool, floor_index: int = 0) -> Dictionary:
    var rooms: Array = _rooms_for(building, is_lab, floor_index)
    var fixture_count: int = 0
    for room in rooms:
        var rect: Rect2 = _as_rect(room)
        var role: String = _kind(str(room["type"]))
        var fixtures: Array = []
        var definitions: Array = kits.get("rooms", {}).get(role, [])
        for slot in range(definitions.size()):
            var definition: Dictionary = definitions[slot]
            var at: Array = definition["at"]
            var sizes: Array = definition["size"]
            var sx: float = minf(float(sizes[0]), maxf(.5, rect.size.x - .8))
            var sy: float = minf(float(sizes[1]), maxf(.5, rect.size.y - .8))
            var x: float = clampf(rect.position.x + rect.size.x * float(at[0]), rect.position.x + sx / 2.0 + .15, rect.end.x - sx / 2.0 - .15)
            var y: float = clampf(rect.position.y + rect.size.y * float(at[1]), rect.position.y + sy / 2.0 + .15, rect.end.y - sy / 2.0 - .15)
            fixtures.append({"id": _building_id(building) + "/floor/" + str(floor_index) + "/" + str(room["id"]) + "/" + str(slot),
                "role": str(definition["role"]), "family": str(definition["family"]),
                "pos": [x, y], "size": [sx, sy], "interactive": bool(definition.get("interactive", false)),
                "room_id": str(room["id"])})
        room["fixtures"] = fixtures
        room["normalized_type"] = role
        fixture_count += fixtures.size()
    return {"building_id": _building_id(building), "floor": floor_index, "rooms": rooms,
        "portals": _portals(rooms), "fixture_count": fixture_count}

func room_at(plan: Dictionary, position: Vector2) -> String:
    for room in plan.get("rooms", []):
        if _as_rect(room).has_point(position):
            return str(room["id"])
    return ""

func can_move(plan: Dictionary, from: Vector2, destination: Vector2) -> bool:
    var to_room: String = room_at(plan, destination)
    if to_room.is_empty():
        return false
    var from_room: String = room_at(plan, from)
    if from_room != to_room:
        var doorway_open := false
        for portal in plan.get("portals", []):
            if (portal["a"] == from_room and portal["b"] == to_room) or (portal["b"] == from_room and portal["a"] == to_room):
                var point: Vector2 = Vector2(float(portal["point"][0]), float(portal["point"][1]))
                if portal["axis"] == "vertical" and absf(destination.y - point.y) <= float(portal["half_width"]):
                    doorway_open = true
                elif portal["axis"] == "horizontal" and absf(destination.x - point.x) <= float(portal["half_width"]):
                    doorway_open = true
        if not doorway_open:
            return false
    for room in plan["rooms"]:
        if room["id"] != to_room:
            continue
        for fixture in room["fixtures"]:
            var p: Vector2 = Vector2(float(fixture["pos"][0]), float(fixture["pos"][1]))
            var size: Array = fixture["size"]
            if absf(destination.x - p.x) < float(size[0]) / 2.0 + .18 and absf(destination.y - p.y) < float(size[1]) / 2.0 + .18:
                return false
    return true
