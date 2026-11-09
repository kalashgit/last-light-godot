extends Node2D
## LAST LIGHT — all 60 original building archetypes + preserved three-house row.
## Separate playable technical showcase: unapproved procedural debug art only.
## An opt-in scene. Does NOT replace main.tscn or modify the survival-house save.
const DATA_PATH := "res://data/generated/all_archetypes_neighborhood_v1.json"
const SAVE_PATH := "user://ll_all_archetypes_neighborhood_v1_save.json"
const TX := 40.0
const TY := 20.0
var neighborhood: Dictionary = {}
var player: Vector2 = Vector2(23, 31)
var move_vector: Vector2 = Vector2.ZERO
var touch_id: int = -1
var touch_start: Vector2 = Vector2.ZERO
var roofs_visible: bool = true
var zoom_factor: float = 1.0
var open_doors: Dictionary = {}
var message: String = "Explore the three-house row or jump to another district"
var save_accumulator: float = 0.0

func _ready() -> void:
    var raw: String = FileAccess.get_file_as_string(DATA_PATH)
    var parsed: Variant = JSON.parse_string(raw)
    if parsed is Dictionary and parsed.get("schema", "") == "last_light.all_archetypes_neighborhood.v1" and parsed.get("buildings", []).size() == 63:
        neighborhood = parsed
        player = _vec(neighborhood.get("player_spawn", [8, 40]))
        _load_game()
    else:
        push_error("Missing valid generated neighborhood JSON: " + DATA_PATH)
    set_process(true)
    queue_redraw()

func _exit_tree() -> void:
    _save_game()

func _vec(arr: Array) -> Vector2:
    return Vector2(float(arr[0]), float(arr[1]))

func _iso(point: Vector2) -> Vector2:
    return Vector2((point.x - point.y) * TX, (point.x + point.y) * TY)

func _camera_offset() -> Vector2:
    var size: Vector2 = get_viewport_rect().size
    return size * Vector2(0.5, 0.52) - _iso(player) * zoom_factor

func _stick_center() -> Vector2:
    var size: Vector2 = get_viewport_rect().size
    return Vector2(108.0, size.y - 130.0)

func _button_center() -> Vector2:
    var size: Vector2 = get_viewport_rect().size
    return Vector2(size.x - 105.0, size.y - 118.0)

func _indoor_building() -> Dictionary:
    for entry in neighborhood.get("buildings", []):
        var b: Dictionary = entry
        var bounds: Array = b["footprint"]
        var origin: Vector2 = Vector2(float(bounds[0]), float(bounds[1]))
        var rect: Rect2 = Rect2(origin, Vector2(float(bounds[2]), float(bounds[3])))
        if b.get("footprint_kind", "structure") != "site" and rect.has_point(player):
            return b
    return {}

func _can_walk_to(point: Vector2) -> bool:
    # UCF-002 gate: building shells are solid. Enter and exit via INTERACT at
    # front doors; this pilot has not yet installed interior partition collision.
    var interior: Dictionary = _indoor_building()
    for b in neighborhood.get("buildings", []):
        if b.get("footprint_kind", "structure") == "site":
            continue
        var bounds: Array = b["footprint"]
        var rect: Rect2 = Rect2(Vector2(float(bounds[0]),float(bounds[1])),Vector2(float(bounds[2]),float(bounds[3])))
        var inside_next: bool = rect.has_point(point)
        if interior.is_empty() and inside_next:
            return false
        if not interior.is_empty() and b["id"] == interior["id"] and not inside_next:
            return false
    return true

func _process(delta: float) -> void:
    if neighborhood.is_empty():
        queue_redraw()
        return
    var direction: Vector2 = Input.get_vector("ui_left", "ui_right", "ui_up", "ui_down")
    if move_vector.length_squared() > 0.001:
        direction = move_vector
    var next: Vector2 = player + direction.normalized() * delta * 4.1
    var bounds: Array = neighborhood["bounds"]
    if next.x >= float(bounds[0]) + 0.5 and next.x <= float(bounds[2]) - 0.5 and next.y >= float(bounds[1]) + 0.5 and next.y <= float(bounds[3]) - 0.5 and _can_walk_to(next):
        player = next
    # Smooth zoom: closer in rooms, farther outside, preserving the old lab controls.
    var wanted_zoom: float = 1.65 if not _indoor_building().is_empty() else 1.0
    zoom_factor = lerpf(zoom_factor, wanted_zoom, 1.0 - exp(-5.0 * minf(delta, 0.15)))
    save_accumulator += delta
    if save_accumulator >= 12.0:
        save_accumulator = 0.0
        _save_game()
    queue_redraw()

func _input(event: InputEvent) -> void:
    if event is InputEventScreenTouch:
        var p: Vector2 = event.position
        if event.pressed:
            if p.y >= 95.0 and p.y <= 140.0 and p.x >= 12.0 and p.x < get_viewport_rect().size.x - 12.0:
                var tab_width: float = (get_viewport_rect().size.x - 24.0) / 6.0
                _jump_to_district(int((p.x - 12.0) / tab_width))
                return
            if p.distance_to(_stick_center()) <= 105.0 and touch_id == -1:
                touch_id = event.index
                touch_start = _stick_center()
                move_vector = (p - touch_start).limit_length(64.0) / 64.0
            elif p.distance_to(_button_center()) <= 92.0:
                _interact()
        elif event.index == touch_id:
            touch_id = -1
            move_vector = Vector2.ZERO
    elif event is InputEventScreenDrag:
        if event.index == touch_id:
            move_vector = (event.position - touch_start).limit_length(64.0) / 64.0
    elif event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
        if event.position.y >= 95.0 and event.position.y <= 140.0:
            _jump_to_district(int((event.position.x - 12.0) / ((get_viewport_rect().size.x - 24.0) / 6.0)))
        elif event.position.distance_to(_button_center()) < 100.0:
            _interact()
    elif event is InputEventKey and event.pressed and not event.echo:
        if event.keycode == KEY_E or event.keycode == KEY_SPACE:
            _interact()
        elif event.keycode == KEY_R:
            roofs_visible = not roofs_visible
        elif event.keycode >= KEY_1 and event.keycode <= KEY_6:
            _jump_to_district(int(event.keycode - KEY_1))

func _interact() -> void:
    if neighborhood.is_empty():
        return
    var interior: Dictionary = _indoor_building()
    if not interior.is_empty():
        var entry: Vector2 = _vec(interior["entry"]["pos"])
        player = entry + Vector2(0.0, 1.2)
        message = "Exited " + str(interior["id"])
        _save_game()
        return
    var nearest: Dictionary = {}
    var nearest_distance: float = 3.4
    for b in neighborhood["buildings"]:
        var entry: Vector2 = _vec(b["entry"]["pos"])
        var distance: float = entry.distance_to(player)
        if distance < nearest_distance:
            nearest = b
            nearest_distance = distance
    if not nearest.is_empty() and nearest.get("footprint_kind", "structure") != "site":
        var entry: Vector2 = _vec(nearest["entry"]["pos"])
        player = entry + Vector2(0.0, -1.5)
        open_doors[str(nearest["entry"]["id"])] = true
        message = "Entered " + str(nearest["id"])
        _save_game()
    else:
        message = "Move to a front door"

func _save_game() -> void:
    if neighborhood.is_empty():
        return
    var payload: Dictionary = {
        "schema": "last_light.neighborhood_showcase_save.v1",
        "seed": neighborhood["seed"],
        "position": [player.x, player.y],
        "doors_open": open_doors
    }
    var file: FileAccess = FileAccess.open(SAVE_PATH, FileAccess.WRITE)
    if file != null:
        file.store_string(JSON.stringify(payload))
        file.close()

func _load_game() -> void:
    if not FileAccess.file_exists(SAVE_PATH):
        return
    var payload: Variant = JSON.parse_string(FileAccess.get_file_as_string(SAVE_PATH))
    if payload is Dictionary and payload.get("schema", "") == "last_light.neighborhood_showcase_save.v1" and payload.get("seed", -1) == neighborhood["seed"]:
        var p: Variant = payload.get("position", [])
        if p is Array and p.size() == 2:
            var point: Vector2 = _vec(p)
            if point.x >= 0 and point.x <= 420 and point.y >= 0 and point.y <= 610:
                player = point
        if payload.get("doors_open", {}) is Dictionary:
            open_doors = payload["doors_open"]

func _quad(rect: Array, color: Color) -> void:
    var x: float = float(rect[0]); var y: float = float(rect[1])
    var w: float = float(rect[2]); var h: float = float(rect[3])
    draw_colored_polygon(PackedVector2Array([
        _iso(Vector2(x,y)), _iso(Vector2(x+w,y)),
        _iso(Vector2(x+w,y+h)), _iso(Vector2(x,y+h))]), color)

func _line(a: Vector2, b: Vector2, color: Color, width: float = 3.0) -> void:
    draw_line(_iso(a), _iso(b), color, width, true)

func _draw_house(b: Dictionary) -> void:
    var bounds: Array = b["footprint"]
    var x: float = float(bounds[0]); var y: float = float(bounds[1])
    var w: float = float(bounds[2]); var h: float = float(bounds[3])
    var outdoor_site: bool = b.get("footprint_kind", "structure") == "site"
    var floor_tint: Color = Color("6f846e") if outdoor_site else Color(str(b.get("color", "#9b947f")))
    _quad(bounds, floor_tint)
    for room in b["rooms"]:
        var tint: Color = Color("a8997b")
        match str(room["type"]):
            "kitchen": tint = Color("a7aaa0")
            "bedroom": tint = Color("a8927d")
            "living": tint = Color("9e947d")
            "bathroom": tint = Color("9caeaf")
        _quad(room["rect"],tint)
    _quad(b["hall"]["rect"],Color("c4bca6"))
    for f in b["furnishings"]:
        var p: Vector2 = _vec(f["pos"])
        _quad([p.x,p.y,0.7,0.7], Color("5a5145"))
    var wall: Color = Color("d1ccba")
    match str(b.get("materials", {}).get("wall", "")):
        "brick_aged": wall = Color("a37669")
        "metal_panel": wall = Color("788c94")
        "concrete_block": wall = Color("9ba4a3")
        "timber_siding": wall = Color("a8875d")
    if not outdoor_site:
        _line(Vector2(x,y),Vector2(x+w,y),wall,5)
        _line(Vector2(x,y),Vector2(x,y+h),wall,5)
        _line(Vector2(x+w,y),Vector2(x+w,y+h),wall,5)
    var entry: Vector2 = _vec(b["entry"]["pos"])
    if not outdoor_site:
        _line(Vector2(x,y+h),entry-Vector2(0.6,0),wall,5)
        _line(entry+Vector2(0.6,0),Vector2(x+w,y+h),wall,5)
    draw_circle(_iso(entry),5,Color("eac27e"))
    for door in b["interior_doors"]:
        draw_circle(_iso(_vec(door["pos"])),4,Color("e4bd83"))
    if not outdoor_site and roofs_visible and _indoor_building().get("id","") != b["id"]:
        var roof: Color = Color("5d686b")
        match str(b.get("materials", {}).get("roof", "")):
            "shingle_asphalt": roof = Color("505e66")
            "green_metal": roof = Color("4d6555")
            "standing_seam_metal": roof = Color("646e73")
            "flat_membrane": roof = Color("746a6c")
        roof.a = 0.94
        _quad(bounds,roof)
        _line(Vector2(x,y),Vector2(x+w,y+h),Color("889597"),2)
    var id_label: String = str(b.get("display_name", b.get("archetype_id", "BUILDING")))
    draw_string(ThemeDB.fallback_font, _iso(Vector2(x+w*0.5,y+h*0.5))-Vector2(0,9), id_label,
                HORIZONTAL_ALIGNMENT_CENTER, -1, 10, Color("f6edce"))

func _near_player(b: Dictionary) -> bool:
    var foot: Array = b["footprint"]
    var center: Vector2 = Vector2(float(foot[0])+float(foot[2])*0.5,float(foot[1])+float(foot[3])*0.5)
    return absf(center.x-player.x) <= float(foot[2])*0.5+25.0 and absf(center.y-player.y) <= float(foot[3])*0.5+25.0

func _jump_to_district(index: int) -> void:
    if neighborhood.is_empty():
        return
    var zones: Array = neighborhood.get("districts", [])
    if index < 0 or index >= zones.size():
        return
    var point: Vector2 = _vec(zones[index]["access_point"])
    player = point
    message = "Technical fast travel: " + str(zones[index]["name"])
    _save_game()
    queue_redraw()

func _draw() -> void:
    var viewport: Vector2 = get_viewport_rect().size
    draw_rect(Rect2(Vector2.ZERO,viewport),Color("15231d"))
    if neighborhood.is_empty():
        draw_string(ThemeDB.fallback_font, Vector2(20,45), "Generated neighborhood data missing", HORIZONTAL_ALIGNMENT_LEFT,-1,22,Color.WHITE)
        return
    draw_set_transform(_camera_offset(),0,Vector2.ONE * zoom_factor)
    # Low-cost ground cell rendering within a radius of the player.
    for yy in range(maxi(0,int(player.y)-19),mini(610,int(player.y)+19)):
        for xx in range(maxi(0,int(player.x)-19),mini(420,int(player.x)+19)):
            var variation: int = posmod((xx*37+yy*19+xx*yy*7),5)
            var tint: Color = Color("456249").lightened(float(variation)*0.025)
            _quad([xx,yy,1,1],tint)
    for rd in neighborhood["roads"]:
        _quad(rd["rect"],Color("4c5052"))
        var road: Array = rd["rect"]
        if str(rd.get("kind","")) == "connector":
            if float(road[2]) > float(road[3]):
                for i in range(int(road[0])+2,int(road[0])+int(road[2]),9):
                    _line(Vector2(i,float(road[1])+float(road[3])*0.5),Vector2(i+3,float(road[1])+float(road[3])*0.5),Color("b1a97d"),2)
            else:
                for i in range(int(road[1])+2,int(road[1])+int(road[3]),9):
                    _line(Vector2(float(road[0])+float(road[2])*0.5,i),Vector2(float(road[0])+float(road[2])*0.5,i+3),Color("b1a97d"),2)
    for b in neighborhood["buildings"]:
        if not _near_player(b):
            continue
        var path: Array = b["road_access_path"]
        _line(_vec(path[0]),_vec(path[1]),Color("a6a18a"),12)
        _draw_house(b)
    var p: Vector2 = _iso(player)
    draw_circle(p+Vector2(0,4),7,Color(0,0,0,0.6))
    draw_rect(Rect2(p+Vector2(-4,-18),Vector2(8,17)),Color("6898ab"))
    draw_circle(p+Vector2(0,-22),6,Color("d8bfa0"))
    draw_set_transform(Vector2.ZERO,0,Vector2.ONE)
    draw_circle(_stick_center(),70,Color(0.08,0.14,0.12,0.7))
    draw_arc(_stick_center(),70,0.0,TAU,40,Color("b8c9ac"),3,true)
    draw_circle(_stick_center()+move_vector*52.0,23,Color("d6bd84"))
    draw_circle(_button_center(),58,Color("d1b481"))
    draw_string(ThemeDB.fallback_font,_button_center()+Vector2(-36,6),"ENTER",HORIZONTAL_ALIGNMENT_LEFT,-1,17,Color("1b2923"))
    draw_string(ThemeDB.fallback_font,Vector2(16,32),"LAST LIGHT / ALL 60 ARCHETYPES + 3 HOUSE STYLES",HORIZONTAL_ALIGNMENT_LEFT,-1,16,Color("ebead9"))
    draw_string(ThemeDB.fallback_font,Vector2(16,55),"63 prototypes / 6 districts / not Golden art",HORIZONTAL_ALIGNMENT_LEFT,-1,13,Color("c2c7b9"))
    draw_string(ThemeDB.fallback_font,Vector2(16,78),message,HORIZONTAL_ALIGNMENT_LEFT,-1,14,Color("efcb8b"))
    var zones: Array = neighborhood.get("districts", [])
    var tab_width: float = (viewport.x - 24.0) / 6.0
    for z in range(mini(6,zones.size())):
        var rect := Rect2(Vector2(12.0 + float(z)*tab_width, 95.0), Vector2(tab_width-2.0, 42.0))
        var active: bool = player.distance_to(_vec(zones[z]["access_point"])) < 24.0
        draw_rect(rect, Color("738676") if active else Color("394b43"), true)
        draw_rect(rect, Color("afc0ac"), false, 1.0)
        draw_string(ThemeDB.fallback_font, rect.position+Vector2(5,25), str(zones[z]["tab"]),HORIZONTAL_ALIGNMENT_LEFT,-1,12,Color("f2e9d6"))
