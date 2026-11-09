extends "res://scripts/neighborhood_showcase_v2.gd"
## Opt-in playable LAB-H01/H02/H03 prototype. Never writes the production save.
## Art/loot IDs are explicitly noncanonical until A00 + F01-F12 approval.
const RULES_PATH := "res://data/neighborhood/survival_pilot_v1.json"
const SAVE_PATH := "user://last_light_neighborhood_survival_pilot_v1.json"
const SAVE_SCHEMA := "last_light.neighborhood_survival_save.v1"
const MAX_ATTACK_RANGE := 1.65

var rules: Dictionary = {}
var inventory: Dictionary = {}
var looted_objects: Dictionary = {}
var zombies: Array = []
var health: float = 100.0
var stamina: float = 100.0
var hunger: float = 100.0
var thirst: float = 100.0
var world_seconds: float = 0.0
var attack_cooldown: float = 0.0
var facing: Vector2 = Vector2(0, -1)

func _ready() -> void:
    super._ready()
    rules = _read_json(RULES_PATH)
    if rules.get("schema", "") != "last_light.neighborhood_survival_pilot.v1":
        validation_error = "Survival pilot rules missing or incompatible"
        push_error(validation_error)
        return
    restart_pilot()

func restart_pilot() -> void:
    mode = "lab"
    inside_id = ""
    current_floor = 0
    roof_hidden = false
    overview = false
    motion = Vector2.ZERO
    touch_index = -1
    player = _vec(lab["player_spawn"])
    inventory = {}
    for item_id in rules["items"].keys():
        inventory[item_id] = 0
    looted_objects = {}
    fixture_states = {}
    zombies = rules["zombies"].duplicate(true)
    for zombie in zombies:
        zombie["attack_cooldown"] = 0.0
    health = 100.0
    stamina = 100.0
    hunger = 100.0
    thirst = 100.0
    world_seconds = 0.0
    attack_cooldown = 0.0
    message = "Find food and water. ENTER a house, USE furniture, defend yourself."
    queue_redraw()

func _inventory_count() -> int:
    var count := 0
    for quantity in inventory.values():
        count += int(quantity)
    return count

func _loot_for(fixture: Dictionary, room_kind: String) -> String:
    var pools: Dictionary = rules["loot_by_room"]
    var pool: Array = pools.get(room_kind, pools["generic"])
    # Stable across runs and save/reload; never an unseeded random reroll.
    var index := posmod((str(fixture["id"]) + str(rules["seed"])).hash(), pool.size())
    return str(pool[index])

func _nearby_fixture() -> Dictionary:
    var active: Dictionary = _selected_building()
    if active.is_empty():
        return {}
    var plan: Dictionary = _plan_for(active, current_floor)
    var occupied: String = room_factory.room_at(plan, player)
    var nearest_distance := 2.6
    var closest: Dictionary = {}
    for room in plan["rooms"]:
        if str(room["id"]) != occupied:
            continue
        for fixture in room["fixtures"]:
            var d: float = player.distance_to(_vec(fixture["pos"]))
            if d < nearest_distance:
                closest = fixture.duplicate()
                closest["room_kind"] = str(room["normalized_type"])
                nearest_distance = d
    return closest

func use_nearby_fixture() -> void:
    var fixture: Dictionary = _nearby_fixture()
    if fixture.is_empty():
        message = "Move beside a furnishing to search it (walls block interaction)"
        return
    var key: String = str(fixture["id"])
    if not bool(fixture["interactive"]):
        message = "Inspected " + str(fixture["role"])
        return
    if looted_objects.has(key):
        message = "Already searched: " + str(fixture["role"])
        return
    if _inventory_count() >= int(rules["inventory_capacity"]):
        message = "Backpack full; cannot take more items"
        return
    var item_id: String = _loot_for(fixture, str(fixture["room_kind"]))
    if not inventory.has(item_id):
        message = "Prototype loot definition missing; search cancelled"
        return
    # Search+transfer is a single idempotent transaction in this pilot.
    inventory[item_id] = int(inventory[item_id]) + 1
    looted_objects[key] = item_id
    fixture_states[key] = true
    message = "Found " + str(rules["items"][item_id]["name"]) + " in " + str(fixture["role"])
    queue_redraw()

func consume(item_id: String) -> bool:
    if not rules["items"].has(item_id) or int(inventory.get(item_id, 0)) <= 0:
        message = "None in backpack: " + str(rules.get("items", {}).get(item_id, {}).get("name", item_id))
        return false
    var item: Dictionary = rules["items"][item_id]
    if item["kind"] == "medical" and health >= 100.0:
        message = "No injury to bandage"
        return false
    if item["kind"] == "food" and hunger >= 100.0:
        message = "Not hungry"
        return false
    if item["kind"] == "water" and thirst >= 100.0:
        message = "Not thirsty"
        return false
    if item["kind"] == "material":
        message = "Useful scrap requires a future crafting recipe"
        return false
    inventory[item_id] = int(inventory[item_id]) - 1
    hunger = minf(100.0, hunger + float(item["nutrition"]))
    thirst = minf(100.0, thirst + float(item["hydration"]))
    health = minf(100.0, health + float(item["healing"]))
    message = "Used " + str(item["name"])
    queue_redraw()
    return true

func _same_world(zombie: Dictionary) -> bool:
    return mode == "lab" and str(zombie["building_id"]) == inside_id and int(zombie["floor"]) == current_floor

func _can_zombie_walk(zombie: Dictionary, source: Vector2, target: Vector2) -> bool:
    if not _bounds().grow(-0.5).has_point(target):
        return false
    var building_id: String = str(zombie["building_id"])
    if not building_id.is_empty():
        for b in lab["houses"]:
            if str(b["id"]) == building_id:
                return _inside_footprint(b, target) and room_factory.can_move(_plan_for(b, int(zombie["floor"])), source, target)
        return false
    for b in lab["houses"]:
        if _inside_footprint(b, target):
            return false
    return true

func _line_clear(zombie: Dictionary, a: Vector2, b: Vector2) -> bool:
    var steps := maxi(1, ceili(a.distance_to(b) / 0.12))
    var previous: Vector2 = a
    for i in range(1, steps + 1):
        var point: Vector2 = a.lerp(b, float(i) / float(steps))
        if not _can_zombie_walk(zombie, previous, point):
            return false
        previous = point
    return true

func attack() -> void:
    if health <= 0.0 or attack_cooldown > 0.0:
        return
    if stamina < 12.0:
        message = "Too exhausted to swing"
        return
    stamina -= 12.0
    attack_cooldown = 0.55
    var hit := false
    for zombie in zombies:
        if int(zombie["health"]) <= 0 or not _same_world(zombie):
            continue
        var target: Vector2 = _vec(zombie["pos"])
        var delta: Vector2 = target - player
        if delta.length() > MAX_ATTACK_RANGE or (delta.length_squared() > 0.01 and delta.normalized().dot(facing) < -0.15):
            continue
        if not _line_clear(zombie, target, player):
            continue
        zombie["health"] = int(zombie["health"]) - 1
        hit = true
        break
    message = "Hit the infected" if hit else "Swing missed"
    queue_redraw()

func _advance_zombies(dt: float) -> void:
    for zombie in zombies:
        if int(zombie["health"]) <= 0 or not _same_world(zombie):
            continue
        zombie["attack_cooldown"] = maxf(0.0, float(zombie["attack_cooldown"]) - dt)
        var current: Vector2 = _vec(zombie["pos"])
        var distance: float = current.distance_to(player)
        if distance > 9.0:
            continue
        if distance < 0.75 and _line_clear(zombie, current, player):
            if float(zombie["attack_cooldown"]) <= 0.0:
                health = maxf(0.0, health - 9.0)
                zombie["attack_cooldown"] = 1.3
                message = "Infected grabbed you!"
            continue
        if distance <= 0.2:
            continue
        var delta: Vector2 = (player - current).normalized() * float(zombie["speed"]) * dt
        var next: Vector2 = current + Vector2(delta.x, 0.0)
        if _can_zombie_walk(zombie, current, next):
            current = next
        next = current + Vector2(0.0, delta.y)
        if _can_zombie_walk(zombie, current, next):
            current = next
        zombie["pos"] = [current.x, current.y]

func _process(delta: float) -> void:
    if not validation_error.is_empty():
        return
    if health <= 0.0:
        motion = Vector2.ZERO
        queue_redraw()
        return
    var before: Vector2 = player
    super._process(delta)
    if player.distance_squared_to(before) > .00001:
        facing = (player - before).normalized()
    var dt: float = minf(delta, 0.05)
    world_seconds += dt
    attack_cooldown = maxf(0.0, attack_cooldown - dt)
    hunger = maxf(0.0, hunger - dt * 0.035)
    thirst = maxf(0.0, thirst - dt * 0.055)
    stamina = minf(100.0, stamina + dt * (2.5 if hunger < 15 or thirst < 15 else 7.0))
    if hunger <= 0.0 or thirst <= 0.0:
        health = maxf(0.0, health - dt * 1.5)
    _advance_zombies(dt)
    if health <= 0.0:
        message = "YOU DID NOT SURVIVE — press N for a new run"
    queue_redraw()

func _snapshot() -> Dictionary:
    return {
        "schema": SAVE_SCHEMA, "rules_seed": rules["seed"], "mode": mode,
        "player": [player.x, player.y], "inside_id": inside_id,
        "floor": current_floor, "world_seconds": world_seconds,
        "health": health, "hunger": hunger, "thirst": thirst, "stamina": stamina,
        "inventory": inventory.duplicate(true), "looted_objects": looted_objects.duplicate(true),
        "fixture_states": fixture_states.duplicate(true), "zombies": zombies.duplicate(true)
    }

func _restore_snapshot(data: Dictionary) -> bool:
    if data.get("schema", "") != SAVE_SCHEMA or data.get("rules_seed", "") != rules["seed"]:
        return false
    if data.get("mode", "") not in ["lab", "city"] or not data.get("player") is Array or data["player"].size() != 2:
        return false
    var old_inventory: Dictionary = data.get("inventory", {})
    var old_loot: Dictionary = data.get("looted_objects", {})
    var old_states: Dictionary = data.get("fixture_states", {})
    var old_zombies: Array = data.get("zombies", [])
    if old_inventory.size() != inventory.size() or old_zombies.size() != rules["zombies"].size():
        return false
    var count := 0
    for item_id in rules["items"].keys():
        if not old_inventory.has(item_id) or int(old_inventory[item_id]) < 0:
            return false
        count += int(old_inventory[item_id])
    if count > int(rules["inventory_capacity"]):
        return false
    var valid_fixtures := {}
    for plan in room_plans.values():
        for room in plan["rooms"]:
            for fixture in room["fixtures"]:
                if bool(fixture["interactive"]):
                    valid_fixtures[str(fixture["id"])] = true
    for key in old_loot.keys():
        if not valid_fixtures.has(key) or not rules["items"].has(str(old_loot[key])):
            return false
    for key in old_states.keys():
        if not valid_fixtures.has(key):
            return false
    var incoming_mode: String = str(data["mode"])
    var incoming_inside: String = str(data.get("inside_id", ""))
    var incoming_floor: int = int(data.get("floor", 0))
    var incoming_player: Vector2 = _vec(data["player"])
    if incoming_inside.is_empty():
        var bounds := Rect2(0, 0, 96, 46) if incoming_mode == "lab" else Rect2(0, 0, 240, 220)
        if not bounds.grow(-.5).has_point(incoming_player):
            return false
    else:
        var found := false
        var buildings: Array = lab["houses"] if incoming_mode == "lab" else city["buildings"]
        for building in buildings:
            if str(building.get("id", building.get("instance_id", ""))) != incoming_inside:
                continue
            if incoming_floor < 0 or incoming_floor >= int(building.get("stories", 1)):
                return false
            var plan: Dictionary = _plan_for(building, incoming_floor)
            if not room_factory.can_move(plan, incoming_player, incoming_player):
                return false
            found = true
            break
        if not found:
            return false
    for i in range(old_zombies.size()):
        var z: Dictionary = old_zombies[i]
        if str(z.get("id", "")) != str(rules["zombies"][i]["id"]) or not z.get("pos") is Array or z["pos"].size() != 2:
            return false
        if int(z.get("health", -1)) < 0 or int(z.get("health", -1)) > 3:
            return false
    # Validate all principal fields before applying anything (fail closed).
    for stat in ["health", "hunger", "thirst", "stamina"]:
        if not data.has(stat) or float(data[stat]) < 0.0 or float(data[stat]) > 100.0:
            return false
    mode = incoming_mode
    player = incoming_player
    inside_id = incoming_inside
    current_floor = incoming_floor
    health = float(data["health"])
    hunger = float(data["hunger"])
    thirst = float(data["thirst"])
    stamina = float(data["stamina"])
    world_seconds = maxf(0.0, float(data.get("world_seconds", 0.0)))
    inventory = old_inventory.duplicate(true)
    looted_objects = old_loot.duplicate(true)
    fixture_states = old_states.duplicate(true)
    zombies = old_zombies.duplicate(true)
    for zombie in zombies:
        zombie["attack_cooldown"] = maxf(0.0, float(zombie.get("attack_cooldown", 0.0)))
    motion = Vector2.ZERO
    touch_index = -1
    message = "Loaded pilot world: items and searched furniture preserved"
    queue_redraw()
    return true

func save_game() -> bool:
    var temporary := SAVE_PATH + ".tmp"
    var file := FileAccess.open(temporary, FileAccess.WRITE)
    if file == null:
        message = "Cannot write pilot save"
        return false
    file.store_string(JSON.stringify(_snapshot()))
    file.flush()
    file.close()
    var error: Error = DirAccess.rename_absolute(ProjectSettings.globalize_path(temporary), ProjectSettings.globalize_path(SAVE_PATH))
    if error != OK:
        message = "Pilot save could not be finalized"
        return false
    message = "Game saved — experimental isolated slot"
    return true

func load_game() -> bool:
    if not FileAccess.file_exists(SAVE_PATH):
        message = "No pilot save yet"
        return false
    var data: Variant = JSON.parse_string(FileAccess.get_file_as_string(SAVE_PATH))
    if not data is Dictionary or not _restore_snapshot(data):
        message = "Save rejected: invalid or incompatible prototype state"
        return false
    return true

func _button_hit(point: Vector2, center: Vector2) -> bool:
    return point.distance_to(center) < 41.0

func _game_button_center(index: int) -> Vector2:
    var s: Vector2 = get_viewport_rect().size
    match index:
        0: return Vector2(s.x - 95, s.y - 377) # Attack
        1: return Vector2(s.x - 185, s.y - 377) # Food
        2: return Vector2(s.x - 275, s.y - 377) # Water
        3: return Vector2(s.x - 365, s.y - 377) # Bandage
        4: return Vector2(s.x - 196, 150) # Save
        _: return Vector2(s.x - 95, 150) # Load

func _handle_game_button(p: Vector2) -> bool:
    for i in range(6):
        if not _button_hit(p, _game_button_center(i)):
            continue
        match i:
            0: attack()
            1: consume("proto.food_tin")
            2: consume("proto.water_bottle")
            3: consume("proto.bandage")
            4: save_game()
            5: load_game()
        return true
    return false

func _input(event: InputEvent) -> void:
    if event is InputEventScreenTouch and event.pressed and _handle_game_button(event.position):
        return
    if event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT and event.pressed and _handle_game_button(event.position):
        return
    if event is InputEventKey and event.pressed and not event.echo:
        match event.keycode:
            KEY_J: attack()
            KEY_1: consume("proto.food_tin")
            KEY_2: consume("proto.water_bottle")
            KEY_3: consume("proto.bandage")
            KEY_K: save_game()
            KEY_L: load_game()
            KEY_N: restart_pilot()
    super._input(event)

func _draw_hud() -> void:
    super._draw_hud()
    var s: Vector2 = get_viewport_rect().size
    draw_rect(Rect2(10, 109, minf(452.0, s.x - 20.0), 117), Color(0.06, 0.13, 0.11, .89))
    var stats := "HP %d  ST %d  FOOD %d  WATER %d" % [int(health), int(stamina), int(hunger), int(thirst)]
    draw_string(ThemeDB.fallback_font, Vector2(19, 134), stats,
        HORIZONTAL_ALIGNMENT_LEFT, -1, 16, Color("f3d1aa"))
    var item_text := "BAG %d/%d | TIN %d  WATER %d  MED %d  SCRAP %d" % [
        _inventory_count(), int(rules["inventory_capacity"]),
        int(inventory.get("proto.food_tin", 0)), int(inventory.get("proto.water_bottle", 0)),
        int(inventory.get("proto.bandage", 0)), int(inventory.get("proto.scrap", 0))]
    draw_string(ThemeDB.fallback_font, Vector2(19, 157), item_text,
        HORIZONTAL_ALIGNMENT_LEFT, -1, 12, Color("cddfb7"))
    draw_string(ThemeDB.fallback_font, Vector2(19, 179), "E: enter | Q: search | J: hit | 1/2/3: use | K/L: save/load | N: reset",
        HORIZONTAL_ALIGNMENT_LEFT, -1, 11, Color("e4dcba"))
    draw_string(ThemeDB.fallback_font, Vector2(19, 205), "NONCANONICAL PILOT ART · iPhone QA required",
        HORIZONTAL_ALIGNMENT_LEFT, -1, 11, Color("d7a98c"))
    var labels := ["HIT", "EAT", "DRINK", "MED", "SAVE", "LOAD"]
    for i in range(labels.size()):
        var center: Vector2 = _game_button_center(i)
        draw_circle(center, 39.0, Color("8f5750") if i == 0 else Color("566f66"))
        draw_arc(center, 39.0, 0, TAU, 32, Color("e5d0a1"), 2.0)
        draw_string(ThemeDB.fallback_font, center + Vector2(-24, 5), labels[i],
            HORIZONTAL_ALIGNMENT_LEFT, -1, 13, Color("f7e9cf"))
    if health <= 0.0:
        draw_rect(Rect2(s * Vector2(.11, .45), s * Vector2(.78, .12)), Color(0.1, 0.03, 0.03, .9))
        draw_string(ThemeDB.fallback_font, s * Vector2(.18, .51), "YOU DIED — press N to restart",
            HORIZONTAL_ALIGNMENT_LEFT, -1, 23, Color("f0b4a6"))

func _draw() -> void:
    super._draw()
    if validation_error != "" or overview or mode != "lab":
        return
    draw_set_transform(_offset(), 0.0, Vector2.ONE * _zoom())
    for zombie in zombies:
        if int(zombie["health"]) <= 0 or not _same_world(zombie):
            continue
        var at: Vector2 = _iso(_vec(zombie["pos"]))
        draw_circle(at + Vector2(0, 1), 9.0, Color(0, 0, 0, 0.4))
        draw_rect(Rect2(at + Vector2(-6, -25), Vector2(12, 19)), Color("865351"))
        draw_circle(at + Vector2(0, -28), 6, Color("a3ae8a"))
        draw_string(ThemeDB.fallback_font, at - Vector2(18, 39), "Z" + str(zombie["health"]),
            HORIZONTAL_ALIGNMENT_LEFT, -1, 12, Color("e9bc9d"))
    draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)
