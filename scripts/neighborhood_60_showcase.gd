extends Node2D
## LAST LIGHT — ALL-60 Neighborhood Showcase V1 (optional, original procedural development art).
## Real 60-archetype semantic coverage; NOT 60 Golden-approved buildings.
## Does not replace main.tscn, change existing save, or integrate unapproved F01–F12 art.
const DATA_PATH := "res://data/neighborhood/showcase_60_v1.json"
const SAVE_PATH := "user://ll_neighborhood_60_showcase_v1.json"
const TX := 40.0
const TY := 20.0
const MOVE_SPEED := 5.8
const SAVE_INTERVAL := 12.0
const ZONES := ["Residential", "Commercial", "Civic / public", "Industrial / utility / rural", "Recreation", "Special"]
const THREE_HOUSES := ["house_small", "house_large", "duplex"]
const ZONE_COLORS := [
    Color("8d9882"), Color("a1947b"), Color("83989e"),
    Color("8b8b86"), Color("789a80"), Color("998877")]
const WORLD_MAX := Vector2(240.0, 220.0)

var neighborhood: Dictionary = {}
var buildings: Array[Dictionary] = []
var player := Vector2(10.0, 20.0)
var active_interor_id := ""
var doors_open: Dictionary = {}
var searched_rooms: Dictionary = {}
var health := 100.0
var supplies := 0
var zombies: Array[Dictionary] = []
var elapsed := 0.0
var save_elapsed := 0.0
var message := "Explore the three-house street. INTERACT at a front door."
var message_timer := 10.0
var joystick_touch := -1
var stick_direction := Vector2.ZERO
var overview := false
var roofs_visible := true
var zoom := 1.0
var test_mode := false
var validation_error := ""

func _ready() -> void:
    var raw := FileAccess.get_file_as_string(DATA_PATH)
    var data: Variant = JSON.parse_string(raw)
    if not data is Dictionary:
        validation_error = "Missing valid 60-building source JSON"
        push_error(validation_error)
        return
    neighborhood = data
    if not _validate_data():
        push_error(validation_error)
        return
    player = _vector(neighborhood.get("player_spawn", [10, 20]))
    for i in range(ZONES.size()):
        var row: int = int(neighborhood["zone_rows"][i]["first_row"])
        var x: float = 16.0 + float((i % 3) * 23)
        var y: float = 21.0 + float(row * 27)
        zombies.append({"pos": Vector2(x, y), "hp": 3, "hittime": 0.0})
    if not test_mode:
        _load_state()
    set_process(true)
    queue_redraw()

func _validate_data() -> bool:
    if neighborhood.get("schema", "") != "last_light.neighborhood_60_prototype.v1":
        validation_error = "Invalid neighborhood schema"
        return false
    var tile_basis: Array = neighborhood.get("tile_pixel_basis", [])
    if tile_basis.size() != 2 or int(tile_basis[0]) != 80 or int(tile_basis[1]) != 40:
        validation_error = "Invalid 80x40 projection"
        return false
    if str(neighborhood.get("status", "")) != "LAYOUT_PROTOTYPE_NO_GOLDEN_ART":
        validation_error = "Preview stage must not claim Golden approval"
        return false
    var source: Array = neighborhood.get("buildings", [])
    if source.size() != 60:
        validation_error = "Expected 60 distinct locations"
        return false
    var known_ids: Dictionary = {}
    var counts: Dictionary = {}
    var blocks: Array[Rect2] = []
    for entry in source:
        if not entry is Dictionary:
            validation_error = "Malformed building entry"
            return false
        var id: String = str(entry.get("archetype_id", ""))
        if id.is_empty() or known_ids.has(id):
            validation_error = "Duplicate/invalid archetype " + id
            return false
        known_ids[id] = true
        var group: String = str(entry.get("group", ""))
        if not ZONES.has(group):
            validation_error = "Unknown district " + group
            return false
        counts[group] = int(counts.get(group, 0)) + 1
        var bounds: Array = entry.get("footprint", [])
        if bounds.size() != 4:
            validation_error = "Malformed footprint " + id
            return false
        var r := _rect(bounds)
        if r.size.x < 5 or r.size.y < 5:
            validation_error = "Invalid footprint " + id
            return false
        for earlier in blocks:
            if r.intersects(earlier):
                validation_error = "Overlapping parcels " + id
                return false
        blocks.append(r)
        buildings.append(entry)
    var expected := [9, 15, 13, 10, 7, 6]
    for i in range(ZONES.size()):
        if int(counts.get(ZONES[i], 0)) != expected[i]:
            validation_error = "District coverage mismatch " + ZONES[i]
            return false
    for i in range(THREE_HOUSES.size()):
        if str(buildings[i].get("archetype_id", "")) != THREE_HOUSES[i]:
            validation_error = "Three house street order incorrect"
            return false
    return true

func _vector(a: Array) -> Vector2:
    return Vector2(float(a[0]), float(a[1]))

func _rect(a: Array) -> Rect2:
    return Rect2(float(a[0]), float(a[1]), float(a[2]), float(a[3]))

func _bounds(b: Dictionary) -> Rect2:
    return _rect(b["footprint"])

func _active_building() -> Dictionary:
    if active_interor_id.is_empty():
        return {}
    for b in buildings:
        if str(b["instance_id"]) == active_interor_id:
            return b
    return {}

func _project(p: Vector2, height: float = 0.0) -> Vector2:
    var origin := Vector2((p.x - p.y) * TX, (p.x + p.y) * TY)
    var camera := Vector2((player.x - player.y) * TX, (player.x + player.y) * TY)
    var size := get_viewport_rect().size
    return (origin - camera - Vector2(0, height)) * zoom + size * Vector2(0.50, 0.55)

func _poly(v: PackedVector2Array, color: Color) -> void:
    draw_colored_polygon(v, color)

func _tile(r: Rect2, color: Color, elevation: float = 0.0) -> void:
    var p: Vector2 = r.position
    var s: Vector2 = r.size
    _poly(PackedVector2Array([
        _project(p, elevation), _project(p + Vector2(s.x, 0), elevation),
        _project(p + s, elevation), _project(p + Vector2(0, s.y), elevation)
    ]), color)

func _line(a: Vector2, b: Vector2, color: Color, width: float = 2.0, high: float = 0.0) -> void:
    draw_line(_project(a, high), _project(b, high), color, width, true)

func _label(value: String, point: Vector2, font_size: int = 13, tint: Color = Color("f1e6ca")) -> void:
    draw_string(ThemeDB.fallback_font, point, value, HORIZONTAL_ALIGNMENT_LEFT, -1, font_size, tint)

func _walkable(p: Vector2) -> bool:
    if p.x < 0.8 or p.y < 0.8 or p.x > WORLD_MAX.x - 0.8 or p.y > WORLD_MAX.y - 0.8:
        return false
    if not active_interor_id.is_empty():
        var current := _active_building()
        if current.is_empty():
            return false
        return _bounds(current).grow(-0.32).has_point(p)
    for b in buildings:
        if str(b["site_kind"]) == "interior_shell" and _bounds(b).grow(0.2).has_point(p):
            return false
    return true

func _move(direction: Vector2, dt: float) -> void:
    if direction.length_squared() < 0.01:
        return
    var world_dir := Vector2(direction.x + direction.y, direction.y - direction.x).normalized()
    var delta_pos := world_dir * MOVE_SPEED * dt
    var steps := maxi(1, ceili(delta_pos.length() / 0.18))
    for i in range(steps):
        var step: Vector2 = delta_pos / float(steps)
        var next_x := player + Vector2(step.x, 0)
        if _walkable(next_x):
            player.x = next_x.x
        var next_y := player + Vector2(0, step.y)
        if _walkable(next_y):
            player.y = next_y.y

func _process(delta: float) -> void:
    if buildings.size() != 60:
        return
    var dt: float = minf(delta, 0.06)
    elapsed += dt
    message_timer = maxf(0, message_timer - dt)
    var input_dir := Input.get_vector("ui_left", "ui_right", "ui_up", "ui_down")
    if joystick_touch >= 0:
        input_dir = stick_direction
    _move(input_dir, dt)
    var goal: float = 0.48 if overview else 1.35 if not active_interor_id.is_empty() else 1.0
    zoom = lerpf(zoom, goal, 1.0 - exp(-5 * dt))
    for enemy in zombies:
        if int(enemy["hp"]) <= 0:
            continue
        enemy["hittime"] = maxf(0, float(enemy["hittime"]) - dt)
        if not active_interor_id.is_empty():
            continue
        var position: Vector2 = enemy["pos"]
        if position.distance_to(player) < 7.0:
            var toward: Vector2 = (player - position).normalized()
            var candidate: Vector2 = position + toward * 0.66 * dt
            if _walkable(candidate):
                enemy["pos"] = candidate
        if (enemy["pos"] as Vector2).distance_to(player) < 0.7:
            health = maxf(0, health - dt * 6)
    save_elapsed += dt
    if save_elapsed > SAVE_INTERVAL and not test_mode:
        save_elapsed = 0.0
        _save_state()
    queue_redraw()

func _announce(value: String) -> void:
    message = value
    message_timer = 5.0

func _room_rects(b: Dictionary) -> Array[Dictionary]:
    var modules: Array = b.get("room_modules", [])
    var count := mini(6, modules.size())
    var area := _bounds(b).grow(-0.6)
    var room_rows := maxi(1, ceili(float(count) / 2.0))
    var results: Array[Dictionary] = []
    for i in range(count):
        var col: int = i % 2
        var row: int = i / 2
        var r := Rect2(area.position + Vector2(col * area.size.x / 2.0, row * area.size.y / float(room_rows)),
            Vector2(area.size.x / 2.0, area.size.y / float(room_rows)))
        results.append({"name": str(modules[i]), "rect": r, "index": i})
    return results

func _interact() -> void:
    if not active_interor_id.is_empty():
        var current := _active_building()
        if current.is_empty():
            _announce("Current building lost")
            return
        var door: Vector2 = _vector(current["front_door"])
        if player.distance_to(door) < 2.6:
            active_interor_id = ""
            player = door + Vector2(0, 1.25)
            _announce("Exited " + str(current["name"]))
            _save_state()
            return
        for room in _room_rects(current):
            if (room["rect"] as Rect2).has_point(player):
                var key := str(current["instance_id"]) + ":room:" + str(room["index"])
                if not searched_rooms.has(key):
                    searched_rooms[key] = true
                    supplies += 1
                    _announce("Searched " + str(room["name"]) + " (test supplies +1)")
                else:
                    _announce("Room already searched. Return to entrance to exit.")
                _save_state()
                return
        _announce("Move toward a room or the entry door.")
        return
    var closest: Dictionary = {}
    var nearest := 2.7
    for b in buildings:
        var door: Vector2 = _vector(b["front_door"])
        var distance: float = player.distance_to(door)
        if distance < nearest:
            nearest = distance
            closest = b
    if closest.is_empty():
        _announce("Approach an entrance or use the district tabs.")
        return
    if str(closest["site_kind"]) == "outdoor":
        _announce("Outdoor site: " + str(closest["name"]) + " (prototype layout)")
        return
    var door_pos: Vector2 = _vector(closest["front_door"])
    active_interor_id = str(closest["instance_id"])
    doors_open[active_interor_id] = true
    player = door_pos + Vector2(0, -1.3)
    _announce("Entered " + str(closest["name"]) + " — rooms are test layouts.")
    _save_state()

func _attack() -> void:
    for z in zombies:
        if int(z["hp"]) > 0 and (z["pos"] as Vector2).distance_to(player) < 1.5 and active_interor_id.is_empty():
            z["hp"] = int(z["hp"]) - 1
            z["hittime"] = 0.24
            _announce("Infected struck (prototype combat)")
            return
    _announce("No infected within reach")

func _jump_to_zone(index: int) -> void:
    if index < 0 or index >= ZONES.size():
        return
    active_interor_id = ""
    for b in buildings:
        if str(b["group"]) == ZONES[index]:
            player = _vector(b["front_door"]) + Vector2(0, 2.0)
            _announce("District: " + ZONES[index])
            _save_state()
            return

func _save_state() -> void:
    if test_mode or buildings.size() != 60:
        return
    var record := {
        "schema": "last_light.neighborhood_60_save.v1",
        "seed": int(neighborhood["seed"]),
        "player": [player.x, player.y],
        "interior": active_interor_id,
        "doors_open": doors_open,
        "searched_rooms": searched_rooms,
        "health": health,
        "supplies": supplies
    }
    var file := FileAccess.open(SAVE_PATH, FileAccess.WRITE)
    if file != null:
        file.store_string(JSON.stringify(record))
        file.close()

func _load_state() -> void:
    if not FileAccess.file_exists(SAVE_PATH):
        return
    var data: Variant = JSON.parse_string(FileAccess.get_file_as_string(SAVE_PATH))
    if not data is Dictionary or data.get("schema") != "last_light.neighborhood_60_save.v1":
        return
    if int(data.get("seed", -1)) != int(neighborhood["seed"]):
        return
    var saved: Array = data.get("player", [])
    if saved.size() != 2:
        return
    var location := _vector(saved)
    if location.x < 0 or location.y < 0 or location.x > WORLD_MAX.x or location.y > WORLD_MAX.y:
        return
    var inside: String = str(data.get("interior", ""))
    if not inside.is_empty():
        var found := false
        for b in buildings:
            if str(b["instance_id"]) == inside and str(b["site_kind"]) == "interior_shell" and _bounds(b).has_point(location):
                found = true
                break
        if not found:
            return
    player = location
    active_interor_id = inside
    if data.get("doors_open", {}) is Dictionary:
        doors_open = data["doors_open"]
    if data.get("searched_rooms", {}) is Dictionary:
        searched_rooms = data["searched_rooms"]
    health = clampf(float(data.get("health", 100)), 0, 100)
    supplies = maxi(0, int(data.get("supplies", 0)))

func _exit_tree() -> void:
    if not test_mode:
        _save_state()

func _zone_index(group: String) -> int:
    return ZONES.find(group)

func _draw_roads() -> void:
    for row in range(8):
        var y := 18.0 + row * 27.0
        _tile(Rect2(0, y, 240, 8), Color("4c5151"))
        _tile(Rect2(0, y - 1.5, 240, 1.1), Color("929087"))
        _tile(Rect2(0, y + 8, 240, 1.0), Color("8c8d82"))
        for col in range(12):
            _line(Vector2(col * 20 + 5, y + 4.0), Vector2(col * 20 + 14, y + 4.0), Color("b7ad85"), 1.3)
    for col in range(10):
        var x := 19.0 + col * 23.0
        _tile(Rect2(x, 0, 5, 220), Color("505654"))

func _draw_building(b: Dictionary) -> void:
    var r := _bounds(b)
    var center := _project(r.get_center())
    var view := get_viewport_rect().size
    if center.x < -1500 or center.x > view.x + 1500 or center.y < -1000 or center.y > view.y + 1000:
        return
    var group: String = str(b["group"])
    var idx := maxi(0, _zone_index(group))
    var base: Color = ZONE_COLORS[idx]
    var outside_site := str(b["site_kind"]) == "outdoor"
    var inside := active_interor_id == str(b["instance_id"])
    var p := r.position
    var w := r.size.x
    var h := r.size.y
    if outside_site:
        _tile(r, base.darkened(0.25))
        for k in range(3):
            var lx := p.x + 1.0 + k * maxf(1.0, w / 4.0)
            _line(Vector2(lx, p.y + 1), Vector2(lx, p.y + h - 1), base.lightened(0.2), 2)
    else:
        _tile(r, base.darkened(0.36))
        var wall_height := 56.0
        var wall: Color = base.lightened(0.14)
        var dark_wall: Color = base.darkened(0.20)
        var a := p
        var bx := p + Vector2(w, 0)
        var c := p + Vector2(w, h)
        var d := p + Vector2(0, h)
        _poly(PackedVector2Array([_project(d), _project(c), _project(c, wall_height), _project(d, wall_height)]), wall)
        _poly(PackedVector2Array([_project(bx), _project(c), _project(c, wall_height), _project(bx, wall_height)]), dark_wall)
        _line(d, c, Color("262f2d"), 2)
        if inside:
            for room in _room_rects(b):
                var room_rect: Rect2 = room["rect"]
                var room_tint: Color = base.lightened(0.07) if int(room["index"]) % 2 == 0 else base.darkened(0.07)
                _tile(room_rect, room_tint)
                var room_point := _project(room_rect.get_center(), 2)
                _label(str(room["name"]).substr(0, 17), room_point + Vector2(-35, 2), 11, Color("191e1a"))
                var key := str(b["instance_id"]) + ":room:" + str(room["index"])
                if not searched_rooms.has(key):
                    draw_circle(room_point + Vector2(0, -17), 5, Color("e7ce76"))
        elif roofs_visible:
            var roof: Color = base.darkened(0.28)
            var roof_high: float = 72.0
            var style: String = str(b["roof_style"])
            if style == "flat":
                _tile(r, roof, roof_high)
            elif style == "duplex_split":
                var left := Rect2(p, Vector2(w / 2.0, h))
                var right := Rect2(p + Vector2(w / 2.0, 0), Vector2(w / 2.0, h))
                _tile(left, roof.lightened(0.05), roof_high)
                _tile(right, roof.darkened(0.06), roof_high + 11)
                _line(p + Vector2(w / 2.0, 0), p + Vector2(w / 2.0, h), Color("ded9c1"), 2, roof_high)
            elif style == "hip":
                var tip := _project(p + Vector2(w * 0.5, h * 0.50), 102)
                _poly(PackedVector2Array([_project(a, roof_high), _project(bx, roof_high), tip]), roof.lightened(0.14))
                _poly(PackedVector2Array([_project(bx, roof_high), _project(c, roof_high), tip]), roof.darkened(0.10))
                _poly(PackedVector2Array([_project(c, roof_high), _project(d, roof_high), tip]), roof)
                _poly(PackedVector2Array([_project(d, roof_high), _project(a, roof_high), tip]), roof.lightened(0.07))
            else:
                var ridge_a := _project(p + Vector2(w * 0.5, 0), 100)
                var ridge_b := _project(p + Vector2(w * 0.5, h), 100)
                _poly(PackedVector2Array([_project(a, roof_high), ridge_a, ridge_b, _project(d, roof_high)]), roof.lightened(0.10))
                _poly(PackedVector2Array([ridge_a, _project(bx, roof_high), _project(c, roof_high), ridge_b]), roof.darkened(0.10))
        if str(b["condition"]) == "damaged":
            _line(p + Vector2(1, 1), p + Vector2(w - 1, h - 1), Color("544037"), 2, wall_height + 1)
    var door_pos := _vector(b["front_door"])
    var marker := _project(door_pos)
    draw_circle(marker, 6 if inside else 5, Color("e3cd8b") if inside else Color("b7d7bf"))
    if ZONE_COLORS[idx] == base and (inside or player.distance_to(door_pos) < 22.0):
        _label(str(b["name"]).substr(0, 28), _project(r.get_center(), 93) + Vector2(-55, 0), 12,
            Color("f2e7c8") if inside else Color("d7d2b8"))
    if THREE_HOUSES.has(str(b["archetype_id"])):
        _label(str(b["archetype_id"]).replace("_", " ").to_upper(), _project(door_pos) + Vector2(-24, 17), 11, Color("f0e2b3"))

func _draw_player() -> void:
    var at := _project(player)
    draw_circle(at + Vector2(0, 4), 8 * zoom, Color(0, 0, 0, 0.46))
    draw_rect(Rect2(at + Vector2(-5, -21) * zoom, Vector2(10, 20) * zoom), Color("497d91"))
    draw_circle(at + Vector2(0, -26) * zoom, 6 * zoom, Color("cbb19b"))
    _label("YOU", at + Vector2(-15, -37) * zoom, 12, Color("f2e8b9"))

func _draw_zombies() -> void:
    for enemy in zombies:
        if int(enemy["hp"]) < 1:
            continue
        var at := _project(enemy["pos"])
        var col: Color = Color("a96359") if float(enemy["hittime"]) > 0 else Color("65786a")
        draw_circle(at + Vector2(0, -13 * zoom), 6 * zoom, col)
        _label("!", at + Vector2(-3, -24) * zoom, 12, Color("efa39b"))

func _draw_hud() -> void:
    var size := get_viewport_rect().size
    draw_rect(Rect2(0, 0, size.x, 150), Color("15241f"))
    _label("L A S T   L I G H T  /  60-LOCATION DISTRICT", Vector2(14, 24), 19)
    _label("PROTOTYPE ONLY  |  HP %d  |  SUPPLIES %d  |  3-HOUSE STREET" % [int(health), supplies],
        Vector2(14, 45), 12, Color("c7c8af"))
    for i in range(ZONES.size()):
        var c := i % 3
        var row := i / 3
        var bw := (size.x - 28) / 3
        var rr := Rect2(10 + c * bw, 58 + row * 37, bw - 5, 32)
        draw_rect(rr, ZONE_COLORS[i].darkened(0.28))
        var display: String = str(["HOUSES", "SHOPS", "CIVIC", "INDUSTRIAL", "RECREATION", "SPECIAL"][i])
        _label(display, rr.position + Vector2(8, 21), 13, Color("f3edd8"))
    if message_timer > 0:
        draw_rect(Rect2(7, 153, size.x - 14, 32), Color("15241f"))
        _label(message.substr(0, 93), Vector2(14, 175), 12)
    var stick := Vector2(90, size.y - 108)
    draw_circle(stick, 58, Color("223d38"))
    draw_arc(stick, 58, 0, TAU, 32, Color("a7baac"), 2)
    draw_circle(stick + stick_direction * 33, 23, Color("cdb88a"))
    var interact := Vector2(size.x - 88, size.y - 106)
    var attack := Vector2(size.x - 199, size.y - 95)
    draw_circle(interact, 48, Color("c5b58c"))
    draw_circle(attack, 38, Color("a57868"))
    _label("INTERACT", interact + Vector2(-39, 4), 12, Color("202a25"))
    _label("HIT", attack + Vector2(-10, 4), 14, Color("202a25"))
    draw_rect(Rect2(size.x - 112, 8, 103, 31), Color("3c5546"))
    _label("MAP" if not overview else "STREET", Vector2(size.x - 101, 29), 12)
    _label("E enter/search  M map  R roof  1–6 districts", Vector2(14, size.y - 18), 11, Color("b4c6b8"))

func _draw() -> void:
    var size := get_viewport_rect().size
    draw_rect(Rect2(Vector2.ZERO, size), Color("27382d"))
    if buildings.size() != 60:
        _label("Neighborhood unavailable: " + validation_error, Vector2(20, 80))
        return
    _tile(Rect2(0, 0, WORLD_MAX.x, WORLD_MAX.y), Color("506749"))
    _draw_roads()
    for b in buildings:
        _draw_building(b)
    _draw_zombies()
    _draw_player()
    _draw_hud()

func _button_hit(pos: Vector2) -> bool:
    var size := get_viewport_rect().size
    if pos.y >= 58 and pos.y <= 132:
        var row := int((pos.y - 58.0) / 37.0)
        var col := int((pos.x - 10.0) / ((size.x - 28.0) / 3.0))
        if row >= 0 and row < 2 and col >= 0 and col < 3:
            _jump_to_zone(row * 3 + col)
            return true
    if pos.y < 44 and pos.x > size.x - 125:
        overview = not overview
        _announce("Overview" if overview else "Street camera")
        return true
    if pos.distance_to(Vector2(size.x - 88, size.y - 106)) < 54:
        _interact()
        return true
    if pos.distance_to(Vector2(size.x - 199, size.y - 95)) < 44:
        _attack()
        return true
    return false

func _handle_touch(pos: Vector2, pressed: bool, index: int) -> void:
    var size := get_viewport_rect().size
    var stick := Vector2(90, size.y - 108)
    if pressed:
        if pos.distance_to(stick) < 94 and joystick_touch < 0:
            joystick_touch = index
            stick_direction = (pos - stick).limit_length(58) / 58
        else:
            _button_hit(pos)
    elif index == joystick_touch:
        joystick_touch = -1
        stick_direction = Vector2.ZERO

func _input(event: InputEvent) -> void:
    if event is InputEventScreenTouch:
        _handle_touch(event.position, event.pressed, event.index)
    elif event is InputEventScreenDrag and event.index == joystick_touch:
        var stick := Vector2(90, get_viewport_rect().size.y - 108)
        stick_direction = (event.position - stick).limit_length(58) / 58
    elif event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT:
        _handle_touch(event.position, event.pressed, 1000)
    elif event is InputEventMouseMotion and joystick_touch == 1000:
        var center := Vector2(90, get_viewport_rect().size.y - 108)
        stick_direction = (event.position - center).limit_length(58) / 58
    elif event is InputEventKey and event.pressed and not event.echo:
        if event.keycode == KEY_E or event.keycode == KEY_ENTER:
            _interact()
        elif event.keycode == KEY_SPACE:
            _attack()
        elif event.keycode == KEY_M:
            overview = not overview
        elif event.keycode == KEY_R:
            roofs_visible = not roofs_visible
        elif event.keycode >= KEY_1 and event.keycode <= KEY_6:
            _jump_to_zone(event.keycode - KEY_1)
