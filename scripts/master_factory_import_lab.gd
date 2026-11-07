extends Node2D
## LAST LIGHT Master Factory Import Lab V1
## A single 2.5D integration TEST map. It is not the finished survival game.
## This script intentionally does not replace res://main.tscn or gameplay saves.
const CATALOG := "res://assets/generated/master_import_v1/catalog.json"

var catalog: Dictionary = {}
var records: Dictionary = {}
var instances: Dictionary = {}
var container_open: Dictionary = {}
var visible_container_item: AnimatedSprite2D
var messages: Label
var imported_count := 0
var vehicle_keys: Array[String] = []

func _ready() -> void:
    y_sort_enabled = true
    var layer := CanvasLayer.new()
    layer.name = "TestStatusUI"
    add_child(layer)
    messages = Label.new()
    messages.position = Vector2(22, 15)
    messages.add_theme_font_size_override("font_size", 19)
    layer.add_child(messages)
    if not FileAccess.file_exists(CATALOG):
        messages.text = "Import lab: run tools/unified_factory/import_godot.py first"
        return
    var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(CATALOG))
    if not parsed is Dictionary:
        push_error("Master factory catalog is invalid")
        return
    catalog = parsed
    var resources: Array = catalog.get("resources", [])
    for entry in resources:
        if not entry is Dictionary:
            push_error("Malformed factory catalog entry")
            return
        var key: String = str(entry["kind"]) + ":" + str(entry["id"])
        if records.has(key):
            push_error("Duplicated imported catalog resource: " + key)
            return
        records[key] = entry
    imported_count = resources.size()
    # Zone landmarks are coherent 2.5D ground-grid positions, not new 3D engines.
    _spawn("actor", "human_worker_crowbar", Vector2(390, 340), "walk_front")
    _spawn("actor", "zombie_hospital", Vector2(660, 360), "shamble_front")
    _spawn("actor", "zombie_construction", Vector2(760, 410), "idle_front")
    _spawn("actor", "human_underwear", Vector2(290, 355), "idle_front")
    _spawn("prop", "refrigerator_main_open", Vector2(325, 245), "closed")
    _spawn("prop", "refrigerator_freezer_open", Vector2(490, 245), "closed")
    _spawn("prop", "cabinet_pair_open", Vector2(145, 285), "closed")
    var vehicle_records: Array = resources.filter(func(r: Dictionary) -> bool:
        return r.get("kind") == "vehicle")
    vehicle_records.sort_custom(func(a: Dictionary, b: Dictionary) -> bool:
        return str(a["id"]) < str(b["id"]))
    var positions := [Vector2(220, 580), Vector2(560, 570), Vector2(895, 545)]
    for i in mini(vehicle_records.size(), positions.size()):
        var ident: String = str(vehicle_records[i]["id"])
        var key: String = "vehicle:" + ident
        vehicle_keys.append(key)
        _spawn("vehicle", ident, positions[i], "heading_%02d" % ((i * 5) % 16))
    # Inventory item shown only when fridge storage is revealed.
    visible_container_item = _spawn("item", "ll_food_bean_tin",
                                    Vector2(310, 217), "ground")
    if visible_container_item != null:
        visible_container_item.visible = false
    container_open["refrigerator_main_open"] = false
    container_open["refrigerator_freezer_open"] = false
    container_open["cabinet_pair_open"] = false
    messages.text = "MASTER IMPORT LAB | %d resources | tap: open fridge + rotate cars | NOT LIVE GAME" % imported_count
    queue_redraw()

func _spawn(kind: String, id: String, at: Vector2, anim: String) -> AnimatedSprite2D:
    var key := kind + ":" + id
    if not records.has(key):
        push_error("Missing generated import catalog entry: " + key)
        return null
    var path: String = str(records[key]["scene_path"])
    var packed: PackedScene = load(path)
    if packed == null:
        push_error("Generated Godot scene does not load: " + path)
        return null
    var actor := packed.instantiate() as AnimatedSprite2D
    if actor == null:
        push_error("Generated actor scene root is not AnimatedSprite2D: " + key)
        return null
    actor.position = at
    if actor.sprite_frames.has_animation(anim):
        actor.animation = anim
        if actor.sprite_frames.get_frame_count(anim) > 1:
            actor.play(anim)
    else:
        push_error("Missing generated animation " + anim + " on " + key)
    add_child(actor)
    instances[key] = actor
    return actor

func set_container_state(id: String, opened: bool) -> void:
    var key: String = "prop:" + id
    if not instances.has(key):
        return
    var sprite: AnimatedSprite2D = instances[key]
    sprite.stop()
    sprite.animation = "opened" if opened else "closed"
    sprite.frame = 0
    container_open[id] = opened
    if id == "refrigerator_main_open" and visible_container_item != null:
        visible_container_item.visible = opened

func play_container_action(id: String) -> void:
    var key: String = "prop:" + id
    if not instances.has(key):
        return
    var sprite: AnimatedSprite2D = instances[key]
    var opening := not bool(container_open.get(id, false))
    sprite.play("open" if opening else "close")
    # Render animation runs before the compartment state is committed.
    # Real gameplay must additionally perform reach/timed-action/inventory checks.
    sprite.animation_finished.connect(func() -> void:
        set_container_state(id, opening), CONNECT_ONE_SHOT)

func set_vehicle_heading(key: String, heading: int) -> void:
    if not instances.has(key):
        return
    var sprite: AnimatedSprite2D = instances[key]
    sprite.stop()
    sprite.animation = "heading_%02d" % posmod(heading, 16)
    sprite.frame = 0

func _unhandled_input(event: InputEvent) -> void:
    var tapped := false
    if event is InputEventScreenTouch:
        tapped = event.pressed
    elif event is InputEventMouseButton:
        tapped = event.button_index == MOUSE_BUTTON_LEFT and event.pressed
    if not tapped:
        return
    play_container_action("refrigerator_main_open")
    for key in vehicle_keys:
        var sprite: AnimatedSprite2D = instances[key]
        var old: int = int(String(sprite.animation).trim_prefix("heading_"))
        set_vehicle_heading(key, old + 1)

func _draw() -> void:
    var top := Vector2(530, 56)
    var size := 40.0
    for x in range(13):
        for y in range(9):
            var center := top + Vector2((x-y) * size, (x+y) * size*.5)
            var road := (x+y > 12 and x+y < 19)
            var grass := x < 5 or y > 6
            var shade := Color(0.32, 0.36, 0.32) if grass else Color(0.47, 0.46, 0.41)
            if road:
                shade = Color(0.28, 0.30, 0.30)
            var corners := PackedVector2Array([
                center+Vector2(0,-size*.5),
                center+Vector2(size,0),
                center+Vector2(0,size*.5),
                center+Vector2(-size,0)
            ])
            draw_colored_polygon(corners, shade)
            draw_polyline(PackedVector2Array([corners[0],corners[1],corners[2],
                                              corners[3],corners[0]]),
                          Color(0.21, 0.24, 0.22), 1.0)
