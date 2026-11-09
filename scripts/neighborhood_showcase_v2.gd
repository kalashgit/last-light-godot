extends Node2D
## LAST LIGHT | Isolated 60-Archetype Neighborhood + Three-House Laboratory.
## Original schematic art ONLY, not Golden-approved F01-F12 source or final gameplay.
## Opt-in scene. Never replaces res://main.tscn or the existing save format.
const CITY_PATH := "res://data/neighborhood/showcase_60_v1.json"
const LAB_PATH := "res://data/neighborhood/house_lab_h01_h02_h03_v1.json"
const TX := 40.0
const TY := 20.0
const WALK_SPEED := 5.4

var city: Dictionary = {}
var lab: Dictionary = {}
var mode: String = "lab"
var player: Vector2 = Vector2(12, 22)
var inside_id: String = ""
var current_floor: int = 0
var roof_hidden: bool = false
var overview: bool = false
var motion: Vector2 = Vector2.ZERO
var touch_index: int = -1
var message: String = "Three-house laboratory. Press TAB to tour all 60 types."
var validation_summary: Dictionary = {}
var validation_error: String = ""

func _ready() -> void:
    city = _read_json(CITY_PATH)
    lab = _read_json(LAB_PATH)
    if city.get("schema", "") != "last_light.neighborhood_60_prototype.v1":
        validation_error = "60-type map schema missing"
    elif lab.get("schema", "") != "last_light.house_lab_v1":
        validation_error = "three-house lab schema missing"
    elif city.get("buildings", []).size() != 60 or lab.get("houses", []).size() != 3:
        validation_error = "expected exactly 60 archetypes and 3 distinct house labs"
    else:
        var seen := {}
        for item in city["buildings"]:
            if seen.has(item["archetype_id"]):
                validation_error = "duplicate building type"
            seen[item["archetype_id"]] = true
        var lab_seen := {}
        for house in lab["houses"]:
            lab_seen[house["id"]] = true
        if lab_seen.size() != 3 or lab_seen.keys().has("LAB-H03") == false:
            validation_error = "three LAB-H01/H02/H03 houses not found"
    if not validation_error.is_empty():
        push_error("NEIGHBORHOOD_SHOWCASE_INVALID: " + validation_error)
        return
    player = _vec(lab["player_spawn"])
    validation_summary = {
        "status": "SCHEMATIC_NEIGHBORHOOD_LOADED",
        "catalog_archetypes": city["buildings"].size(),
        "three_house_labs": lab["houses"].size(),
        "golden_approved": false,
        "playable_release_integrated": false,
        "tile_pixel_basis": [80, 40]
    }
    set_process(true)
    queue_redraw()

func _read_json(path: String) -> Dictionary:
    if not FileAccess.file_exists(path):
        return {}
    var data: Variant = JSON.parse_string(FileAccess.get_file_as_string(path))
    return data if data is Dictionary else {}

func _vec(v: Array) -> Vector2:
    return Vector2(float(v[0]), float(v[1]))

func _entry(b: Dictionary) -> Vector2:
    return _vec(b["front_door"])

func _rect(b: Dictionary) -> Rect2:
    var f: Array = b["footprint"]
    return Rect2(float(f[0]), float(f[1]), float(f[2]), float(f[3]))

func _all_buildings() -> Array:
    return lab["houses"] if mode == "lab" else city["buildings"]

func _bounds() -> Rect2:
    return Rect2(0, 0, 96, 46) if mode == "lab" else Rect2(0, 0, 240, 220)

func _iso(point: Vector2) -> Vector2:
    return Vector2((point.x - point.y) * TX, (point.x + point.y) * TY)

func _center() -> Vector2:
    if overview:
        return _bounds().get_center()
    return player

func _zoom() -> float:
    if overview:
        return 0.135 if mode == "lab" else 0.055
    return 0.84 if mode == "lab" else 0.74

func _offset() -> Vector2:
    var s: Vector2 = get_viewport_rect().size
    return s * Vector2(0.50, 0.53) - _iso(_center()) * _zoom()

func _is_cutout(b: Dictionary, point: Vector2) -> bool:
    if not b.has("cutout"):
        return false
    var cut: Array = b["cutout"]
    var r: Rect2 = _rect(b)
    var hole := Rect2(r.position + Vector2(float(cut[0]), float(cut[1])),
        Vector2(float(cut[2]), float(cut[3])))
    return hole.has_point(point)

func _inside_footprint(b: Dictionary, point: Vector2) -> bool:
    return _rect(b).has_point(point) and not _is_cutout(b, point)

func _is_outdoor(b: Dictionary) -> bool:
    return mode == "city" and b.get("site_kind", "interior_shell") == "outdoor"

func _selected_building() -> Dictionary:
    if inside_id.is_empty():
        return {}
    for b in _all_buildings():
        if str(b.get("instance_id", b.get("id", ""))) == inside_id:
            return b
    return {}

func _can_walk(point: Vector2) -> bool:
    if not _bounds().grow(-0.5).has_point(point):
        return false
    var selected: Dictionary = _selected_building()
    if not selected.is_empty():
        return _inside_footprint(selected, point)
    for b in _all_buildings():
        if not _is_outdoor(b) and _inside_footprint(b, point):
            return false
    return true

func _process(delta: float) -> void:
    if not validation_error.is_empty():
        return
    if not overview:
        var direction: Vector2 = Input.get_vector("ui_left", "ui_right", "ui_up", "ui_down")
        if motion.length_squared() > 0.02:
            direction = motion
        if direction.length_squared() > 0.01:
            # Screen-space input into the same logical world axes as the existing house.
            var world_dir := Vector2(direction.x + direction.y, direction.y - direction.x).normalized()
            var step: Vector2 = world_dir * minf(delta, 0.05) * WALK_SPEED
            if _can_walk(player + Vector2(step.x, 0)):
                player.x += step.x
            if _can_walk(player + Vector2(0, step.y)):
                player.y += step.y
    queue_redraw()

func switch_mode() -> void:
    mode = "city" if mode == "lab" else "lab"
    inside_id = ""
    current_floor = 0
    overview = false
    player = _vec(city["player_spawn"] if mode == "city" else lab["player_spawn"])
    message = "All 60 archetypes — schematic world" if mode == "city" else "Three original LAB-H01/H02/H03 houses"
    queue_redraw()

func toggle_overview() -> void:
    overview = not overview
    message = "District overview" if overview else "Walk and enter buildings"
    queue_redraw()

func toggle_roof() -> void:
    roof_hidden = not roof_hidden
    queue_redraw()

func toggle_floor() -> void:
    var b: Dictionary = _selected_building()
    if b.get("id", "") == "LAB-H02":
        current_floor = 1 - current_floor
        message = "Cedar upstairs" if current_floor == 1 else "Cedar ground floor"
    else:
        message = "Upper floor preview is available inside LAB-H02"
    queue_redraw()

func interact() -> void:
    var selected: Dictionary = _selected_building()
    if not selected.is_empty():
        player = _entry(selected) + Vector2(0, 1.5)
        message = "Exited " + str(selected.get("name", "building"))
        inside_id = ""
        current_floor = 0
        return
    var nearest: Dictionary = {}
    var distance := 3.5
    for b in _all_buildings():
        var d: float = player.distance_to(_entry(b))
        if d < distance:
            nearest = b
            distance = d
    if nearest.is_empty():
        message = "Approach a marked doorway, then press ENTER"
        return
    if _is_outdoor(nearest):
        message = str(nearest["name"]) + " — outdoor site (schematic)"
        return
    var inside_point: Vector2 = _entry(nearest) + Vector2(0, -1.5)
    if not _inside_footprint(nearest, inside_point):
        message = "Invalid doorway for " + str(nearest.get("name", "building"))
        return
    player = inside_point
    inside_id = str(nearest.get("id", nearest.get("instance_id", "")))
    current_floor = 0
    message = "Entered " + str(nearest["name"]) + " / concept rooms"
    queue_redraw()

func _touch_stick_center() -> Vector2:
    var s: Vector2 = get_viewport_rect().size
    return Vector2(98, s.y - 124)

func _enter_center() -> Vector2:
    var s: Vector2 = get_viewport_rect().size
    return Vector2(s.x - 92, s.y - 116)

func _tap(p: Vector2) -> void:
    var s: Vector2 = get_viewport_rect().size
    if p.y < 69:
        if p.x >= s.x - 112:
            switch_mode()
        elif p.x >= s.x - 220:
            toggle_overview()
        elif p.x >= s.x - 328:
            toggle_floor()
        elif p.x >= s.x - 432:
            toggle_roof()
        return
    if p.distance_to(_enter_center()) < 68:
        interact()

func _input(event: InputEvent) -> void:
    if event is InputEventScreenTouch:
        if event.pressed:
            if event.position.distance_to(_touch_stick_center()) < 100 and touch_index < 0:
                touch_index = event.index
                motion = (event.position - _touch_stick_center()).limit_length(65.0) / 65.0
            else:
                _tap(event.position)
        elif event.index == touch_index:
            touch_index = -1
            motion = Vector2.ZERO
    elif event is InputEventScreenDrag and event.index == touch_index:
        motion = (event.position - _touch_stick_center()).limit_length(65.0) / 65.0
    elif event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT:
        if event.pressed:
            if event.position.distance_to(_touch_stick_center()) < 100:
                touch_index = 999
                motion = (event.position - _touch_stick_center()).limit_length(65.0) / 65.0
            else:
                _tap(event.position)
        elif touch_index == 999:
            touch_index = -1
            motion = Vector2.ZERO
    elif event is InputEventMouseMotion and touch_index == 999:
        motion = (event.position - _touch_stick_center()).limit_length(65.0) / 65.0
    elif event is InputEventKey and event.pressed and not event.echo:
        match event.keycode:
            KEY_TAB: switch_mode()
            KEY_M: toggle_overview()
            KEY_R: toggle_roof()
            KEY_F: toggle_floor()
            KEY_E, KEY_SPACE: interact()

func _poly_world(points: Array, height: float, color: Color) -> void:
    var verts := PackedVector2Array()
    for p in points:
        verts.append(_iso(p) - Vector2(0, height))
    draw_colored_polygon(verts, color)

func _quad_world(rect: Rect2, color: Color, height: float = 0.0) -> void:
    var p: Vector2 = rect.position
    var sz: Vector2 = rect.size
    _poly_world([p, p + Vector2(sz.x, 0), p + sz,
        p + Vector2(0, sz.y)], height, color)

func _shape(b: Dictionary) -> Array:
    var r: Rect2 = _rect(b)
    var x: float = r.position.x
    var y: float = r.position.y
    var w: float = r.size.x
    var h: float = r.size.y
    if b.has("cutout"):
        var c: Array = b["cutout"]
        # H03 north-east missing corner; keep garage attached in south-east.
        return [Vector2(x,y),Vector2(x+w-float(c[2]),y),
            Vector2(x+w-float(c[2]),y+float(c[3])),
            Vector2(x+w,y+float(c[3])),Vector2(x+w,y+h),Vector2(x,y+h)]
    return [Vector2(x,y),Vector2(x+w,y),Vector2(x+w,y+h),Vector2(x,y+h)]

func _palette(group: String) -> Color:
    match group:
        "Residential": return Color("526b65")
        "Commercial": return Color("717269")
        "Civic / public": return Color("637788")
        "Industrial / utility / rural": return Color("716759")
        "Recreation": return Color("56744e")
        "Special": return Color("675b70")
        _: return Color("686860")

func _draw_roof(b: Dictionary, roof_color: Color) -> void:
    var points: Array = _shape(b)
    _poly_world(points, 49.0, roof_color)
    for i in range(points.size()):
        var a: Vector2 = points[i]
        var bb: Vector2 = points[(i + 1) % points.size()]
        draw_line(_iso(a) - Vector2(0, 49), _iso(bb) - Vector2(0, 49),
            roof_color.lightened(0.17), 2)
    # Wall face = two visible exterior vertical edges, not final roof art.
    var r: Rect2 = _rect(b)
    var front_a: Vector2 = Vector2(r.position.x, r.end.y)
    var front_b: Vector2 = Vector2(r.end.x, r.end.y)
    draw_line(_iso(front_a), _iso(front_a) - Vector2(0, 49), Color("81908a"), 3)
    draw_line(_iso(front_b), _iso(front_b) - Vector2(0, 49), Color("81908a"), 3)

func _draw_lab_rooms(b: Dictionary) -> void:
    var rooms: Array = b.get("upper_rooms", []) if current_floor == 1 else b["rooms"]
    for room in rooms:
        var dims: Array = room["rect"]
        var pos: Vector2 = _rect(b).position
        var floor_rect := Rect2(pos + Vector2(float(dims[0]),float(dims[1])),
            Vector2(float(dims[2]),float(dims[3])))
        var tint: Color = Color("8f8570")
        match str(room["type"]):
            "kitchen": tint = Color("8e9a93")
            "bathroom": tint = Color("75939a")
            "bedroom": tint = Color("9c7c71")
            "hall", "stairs": tint = Color("b8aa8d")
            "garage": tint = Color("666967")
            "utility", "storage", "pantry": tint = Color("887e6c")
        _quad_world(floor_rect, tint)
        var center: Vector2 = floor_rect.get_center()
        if _zoom() > 0.3:
            draw_string(ThemeDB.fallback_font, _iso(center),
                str(room["type"]), HORIZONTAL_ALIGNMENT_CENTER, -1, 12, Color("f3e7c8"))
    if b.get("id", "") == "LAB-H02" and current_floor == 0:
        var s: Array = b["stairwell"]
        var pos: Vector2 = _rect(b).position
        _quad_world(Rect2(pos + Vector2(float(s[0]),float(s[1])),
            Vector2(float(s[2]),float(s[3]))),Color("cfbd82"))

func _draw_city_rooms(b: Dictionary) -> void:
    var modules: Array = b.get("room_modules", [])
    var r: Rect2 = _rect(b)
    var count: int = mini(4, modules.size())
    if count < 1:
        return
    var cw: float = r.size.x / 2.0
    var ch: float = r.size.y / 2.0
    for i in range(count):
        var part := Rect2(r.position + Vector2(float(i % 2)*cw, float(i / 2)*ch),
            Vector2(cw,ch))
        _quad_world(part,Color("9f9784") if i % 2 == 0 else Color("8c9185"))
        if _zoom() > .3:
            draw_string(ThemeDB.fallback_font,_iso(part.get_center()),str(modules[i]),
                HORIZONTAL_ALIGNMENT_CENTER,-1,11,Color("e2dac2"))

func _draw_building(b: Dictionary) -> void:
    var r: Rect2 = _rect(b)
    var at: Vector2 = r.get_center()
    if not overview and at.distance_to(player) > (44.0 if mode == "lab" else 45.0):
        return
    var group: String = "Residential" if mode == "lab" else str(b["group"])
    var col: Color = _palette(group)
    var outdoor: bool = _is_outdoor(b)
    _poly_world(_shape(b),0,col.darkened(.2) if outdoor else Color("807c6e"))
    if outdoor:
        var points: Array = _shape(b)
        _poly_world(points, 0, col.lightened(.13))
        draw_circle(_iso(r.get_center()), 7, Color("b0a47a"))
    else:
        var active: bool = str(b.get("id",b.get("instance_id",""))) == inside_id
        if active or roof_hidden:
            if mode == "lab":
                _draw_lab_rooms(b)
            else:
                _draw_city_rooms(b)
        else:
            _draw_roof(b,col.darkened(.18))
    var door: Vector2 = _entry(b)
    if not outdoor:
        draw_circle(_iso(door) - Vector2(0,0 if roof_hidden or not inside_id.is_empty() else 48), 5,Color("e7ca83"))
    if _zoom() > 0.29:
        var label: String = str(b.get("name","Unknown"))
        draw_string(ThemeDB.fallback_font,_iso(at)-Vector2(0,68),
            label,HORIZONTAL_ALIGNMENT_CENTER,-1,13,Color("f3dfb5"))

func _draw_streets() -> void:
    var bounds: Rect2 = _bounds()
    if mode == "lab":
        _quad_world(Rect2(0,22,96,7),Color("454c4c"))
        draw_line(_iso(Vector2(0,25.5)),_iso(Vector2(96,25.5)),Color("b0a580"),2)
        for b in lab["houses"]:
            var door: Vector2 = _entry(b)
            draw_line(_iso(door),_iso(Vector2(door.x,22)),Color("b4b0a0"),8)
    else:
        for col in range(10):
            _quad_world(Rect2(19+23*col,0,5,220),Color("4a4d51"))
        for row in range(8):
            _quad_world(Rect2(0,21+27*row,240,7),Color("4a4d51"))
        for row in range(8):
            draw_line(_iso(Vector2(0,24.5+27*row)),_iso(Vector2(240,24.5+27*row)),
                Color("887f66"),1.5)
        # A street-side approach to each real doorway.
        for b in city["buildings"]:
            if overview or _rect(b).get_center().distance_to(player) < 43:
                var door: Vector2 = _entry(b)
                draw_line(_iso(door),_iso(door + Vector2(0,2.0)),Color("a99d85"),4)

func _draw_ground() -> void:
    var bounds: Rect2 = _bounds()
    _quad_world(bounds, Color("344e3e"))
    if overview:
        return
    var xx0: int = maxi(0,int(player.x)-25)
    var yy0: int = maxi(0,int(player.y)-25)
    var xx1: int = mini(int(bounds.end.x),int(player.x)+25)
    var yy1: int = mini(int(bounds.end.y),int(player.y)+25)
    for yy in range(yy0,yy1):
        for xx in range(xx0,xx1):
            var k: int = posmod(xx*31+yy*19+xx*yy*3,6)
            _quad_world(Rect2(xx,yy,1,1),Color("3a5944").lightened(float(k)*.017))

func _draw_hud() -> void:
    var s: Vector2 = get_viewport_rect().size
    draw_rect(Rect2(0,0,s.x,102),Color("14201b"))
    draw_string(ThemeDB.fallback_font,Vector2(17,26),"LAST LIGHT / NEIGHBORHOOD SHOWCASE",
        HORIZONTAL_ALIGNMENT_LEFT,-1,17,Color("eadab5"))
    var caption: String = "THREE HOUSE LAB | H01 • H02 • H03" if mode=="lab" else "ALL 60 TYPES | ORIGINAL PROTOTYPE"
    draw_string(ThemeDB.fallback_font,Vector2(17,49),caption,
        HORIZONTAL_ALIGNMENT_LEFT,-1,13,Color("b9cdb8"))
    draw_string(ThemeDB.fallback_font,Vector2(17,78),message,
        HORIZONTAL_ALIGNMENT_LEFT,-1,12,Color("ecd293"))
    var titles: Array = ["ROOF", "FLOOR", "MAP", "CITY" if mode == "lab" else "LAB"]
    for i in range(4):
        var x: float = s.x - 432 + i*108
        draw_rect(Rect2(x,9,99,36),Color("58655a"))
        draw_string(ThemeDB.fallback_font,Vector2(x+15,32),titles[i],
            HORIZONTAL_ALIGNMENT_LEFT,-1,13,Color("f5ecd6"))
    var stick: Vector2 = _touch_stick_center()
    draw_circle(stick,67,Color(0.07,0.13,0.11,.82))
    draw_arc(stick,67,0,TAU,36,Color("aeb59d"),2)
    draw_circle(stick+motion*44,25,Color("d4b682"))
    draw_string(ThemeDB.fallback_font,stick+Vector2(-22,84),"MOVE",
        HORIZONTAL_ALIGNMENT_LEFT,-1,13,Color("e4d1a8"))
    var enter: Vector2 = _enter_center()
    draw_circle(enter,55,Color("d3b883"))
    draw_string(ThemeDB.fallback_font,enter+Vector2(-26,6),
        "EXIT" if not inside_id.is_empty() else "ENTER",
        HORIZONTAL_ALIGNMENT_LEFT,-1,15,Color("273027"))
    draw_string(ThemeDB.fallback_font,Vector2(16,s.y-23),
        "TAB: city/lab | M: map | E: enter/exit | R: roof | F: floor | debug art / unapproved",
        HORIZONTAL_ALIGNMENT_LEFT,-1,12,Color("e3cd99"))

func _draw() -> void:
    var s: Vector2 = get_viewport_rect().size
    draw_rect(Rect2(Vector2.ZERO,s),Color("121d19"))
    if not validation_error.is_empty():
        draw_string(ThemeDB.fallback_font,Vector2(14,60),validation_error,
            HORIZONTAL_ALIGNMENT_LEFT,-1,15,Color("ef9c94"))
        return
    draw_set_transform(_offset(),0,Vector2.ONE*_zoom())
    _draw_ground()
    _draw_streets()
    for b in _all_buildings():
        _draw_building(b)
    if not overview:
        var at: Vector2 = _iso(player)
        draw_circle(at+Vector2(0,2),9,Color(0,0,0,.45))
        draw_rect(Rect2(at+Vector2(-5,-23),Vector2(10,20)),Color("6095a5"))
        draw_circle(at+Vector2(0,-27),7,Color("d8baa1"))
    draw_set_transform(Vector2.ZERO,0,Vector2.ONE)
    _draw_hud()
