extends "res://scripts/neighborhood_survival_v1.gd"
## LAST LIGHT — GM00 World Sandbox (developer build, opt-in scene).
##
## One coherent neighborhood containing all 60 catalog archetypes plus the
## H01/H02/H03 lab fixtures, generated deterministically from
## data/world/gm00_world_recipe_v1.json. Reuses (extends) the existing
## survival pilot: movement, touch routing, inventory, loot, hunger/thirst,
## melee, zombies and fixture search.
##
## Separation of concerns:
##   world layout ........ scripts/world/world_generator.gd
##   touch ownership ..... scripts/input/touch_router.gd
##   save slots/migration  scripts/sandbox/world_save.gd
##   spawn definitions ... scripts/sandbox/spawn_catalog.gd (+ data/sandbox)
##   asset approval ...... scripts/sandbox/asset_pipeline.gd (fail-closed)
##   layout recipes ...... scripts/sandbox/recipe_store.gd
##   developer UI ........ scripts/sandbox/god_mode_panel.gd
## Never replaces res://main.tscn. All art is PROVISIONAL procedural.

const GENERATOR = preload("res://scripts/world/world_generator.gd")
const CATALOG = preload("res://scripts/sandbox/spawn_catalog.gd")
const WORLD_SAVE = preload("res://scripts/sandbox/world_save.gd")
const PIPELINE = preload("res://scripts/sandbox/asset_pipeline.gd")
const RECIPES = preload("res://scripts/sandbox/recipe_store.gd")
const GOD_PANEL = preload("res://scripts/sandbox/god_mode_panel.gd")
const WORLD_RECIPE_PATH := "res://data/world/gm00_world_recipe_v1.json"
const WORLD_RULES_PATH := "res://data/world/gm00_world_rules_v1.json"
const ENTER_REACH := 3.5
const STAIR_REACH := 2.5
const USE_REACH := 2.6

var generator: Variant = GENERATOR.new()
var catalog: Variant = CATALOG.new()
var pipeline: Variant = PIPELINE.new()
var world_rules: Dictionary = {}
var pilot_items: Dictionary = {}
var layout: Dictionary = {}
var world_seed: int = 601109
var world_buildings: Array = []
var vegetation: Array = []
var chunks: Dictionary = {}
var custom_buildings: Array = []
var custom_counter: int = 0
var spawned: Array = []
var spawn_counter: int = 0
var dev_zombie_counter: int = 0
var layout_problems: Array = []
var god: Dictionary = {}
var dev_tainted: bool = false
var time_of_day: float = 9.0
var weather: String = "clear"
var zoom_level: int = 1
var god_panel: Node = null
var perf: Dictionary = {"frames": 0, "process_us": 0.0, "draw_us": 0.0, "max_process_us": 0.0,
    "max_draw_us": 0.0, "drawn_buildings": 0, "drawn_veg": 0}

# ------------------------------------------------------------------ setup

func _ready() -> void:
    world_rules = _read_json(WORLD_RULES_PATH)
    pilot_items = _read_json(str(world_rules.get("items_source", ""))).get("items", {})
    if not generator.load_recipe(WORLD_RECIPE_PATH):
        validation_error = "World recipe invalid: " + str(generator.errors)
    world_seed = int(generator.recipe.get("default_seed", 601109))
    catalog.load_catalog()
    _reset_god()
    super._ready()
    if world_rules.get("schema", "") != "last_light.gm00_world_rules.v1" or pilot_items.is_empty():
        validation_error = "GM00 world rules missing"
    if not validation_error.is_empty():
        push_error("GM00_WORLD_INVALID: " + validation_error)
        return
    god_panel = GOD_PANEL.new()
    god_panel.game = self
    add_child(god_panel)

func _reset_god() -> void:
    god = {"enabled": false, "invulnerable": false, "infinite_stamina": false, "no_needs": false,
        "speed": 1.0, "noclip": false, "pause_ai": false, "show_collision": false,
        "show_building_ids": false, "show_room_ids": false}

func _rules_from_world() -> Dictionary:
    var r: Dictionary = world_rules.duplicate(true)
    r["items"] = pilot_items.duplicate(true)
    return r

## Builds layout + plans for `seed` with the given custom buildings.
## Returns the layout without touching game state (used by validation too).
func _compose_world(seed: int, customs: Array) -> Dictionary:
    var base: Dictionary = generator.generate(seed)
    var problems: Array = generator.validate(base)
    var buildings: Array = base["buildings"].duplicate()
    var plans: Dictionary = base["plans"].duplicate()
    var placed_customs: Array = []
    for c in customs:
        var b: Dictionary = c.duplicate(true)
        var reason: String = _custom_conflict(b, buildings, base)
        if not reason.is_empty():
            problems.append("custom %s dropped: %s" % [b.get("instance_id", "?"), reason])
            continue
        plans.merge(generator._make_plans(b))
        buildings.append(b)
        placed_customs.append(b)
    var veg: Array = []
    for v in base["vegetation"]:
        var keep := true
        for b in placed_customs:
            if GENERATOR.rect_of(b["footprint"]).grow(0.9).has_point(Vector2(float(v["pos"][0]), float(v["pos"][1]))):
                keep = false
        if keep:
            veg.append(v)
    var composed: Dictionary = base.duplicate()
    composed["base_buildings"] = base["buildings"].size()
    composed["buildings"] = buildings
    composed["vegetation"] = veg
    composed["plans"] = plans
    composed["customs"] = placed_customs
    composed["problems"] = problems
    composed["chunks"] = GENERATOR.build_chunk_index(composed)
    return composed

func _apply_world(composed: Dictionary, seed: int) -> void:
    layout = composed
    world_seed = seed
    world_buildings = composed["buildings"]
    vegetation = composed["vegetation"]
    chunks = composed["chunks"]
    room_plans = composed["plans"]
    # custom_buildings stays the AUTHORED list: a building that conflicts with
    # this seed is skipped (reported in layout_problems) but never forgotten.
    layout_problems = composed["problems"]

func restart_pilot() -> void:
    if generator.recipe.is_empty():
        return
    _apply_world(_compose_world(world_seed, custom_buildings), world_seed)
    rules = _rules_from_world()
    mode = "world"
    inside_id = ""
    current_floor = 0
    roof_hidden = false
    overview = false
    _reset_pointers()
    player = _vec(layout["player_spawn"])
    inventory = {}
    for item_id in rules["items"].keys():
        inventory[item_id] = 0
    looted_objects = {}
    fixture_states = {}
    spawned = []
    spawn_counter = 0
    dev_zombie_counter = 0
    zombies = layout["zombies"].duplicate(true)
    for zombie in zombies:
        zombie["attack_cooldown"] = 0.0
    health = 100.0
    stamina = 100.0
    hunger = 100.0
    thirst = 100.0
    world_seconds = 0.0
    time_of_day = float(rules.get("time", {}).get("start_hour", 9.0))
    weather = "clear"
    attack_cooldown = 0.0
    escaped = false
    restart_arm_until_ms = 0
    dev_tainted = bool(god.get("enabled", false))
    message = "Welcome to Oak Lane. 76 buildings, 5 streets. Scavenge, survive, return."
    queue_redraw()

# ---------------------------------------------------------- world queries

func _all_buildings() -> Array:
    return world_buildings

func _bounds() -> Rect2:
    return GENERATOR.rect_of(layout.get("bounds", [0, 0, 240, 220]))

func _is_outdoor(b: Dictionary) -> bool:
    return str(b.get("site_kind", "interior_shell")) == "outdoor"

func _bid(b: Dictionary) -> String:
    return str(b.get("id", b.get("instance_id", "")))

func _selected_building() -> Dictionary:
    if inside_id.is_empty():
        return {}
    return building_by_instance(inside_id)

func building_by_instance(instance_id: String) -> Dictionary:
    for b in world_buildings:
        if str(b["instance_id"]) == instance_id or _bid(b) == instance_id:
            return b
    return {}

func _zoom() -> float:
    if overview:
        var s: Vector2 = get_viewport_rect().size
        var r: Rect2 = _bounds()
        return minf(s.x / ((r.size.x + r.size.y) * TX), (s.y - 260.0) / ((r.size.x + r.size.y) * TY)) * 0.98
    return [0.5, 0.78, 1.05][clampi(zoom_level, 0, 2)]

func _walk_speed() -> float:
    return WALK_SPEED * (float(god["speed"]) if god["enabled"] else 1.0)

func _chunk_keys_for(rect: Rect2) -> Array:
    var size: float = float(layout.get("chunk_size", 32))
    var keys: Array = []
    for cx in range(int(floor(rect.position.x / size)), int(floor(rect.end.x / size)) + 1):
        for cy in range(int(floor(rect.position.y / size)), int(floor(rect.end.y / size)) + 1):
            keys.append("%d:%d" % [cx, cy])
    return keys

func _veg_near(p: Vector2, radius: float) -> Array:
    var out: Array = []
    for key in _chunk_keys_for(Rect2(p - Vector2(radius, radius), Vector2(radius, radius) * 2.0)):
        for i in chunks.get(key, {}).get("v", []):
            out.append(vegetation[int(i)])
    return out

func _buildings_in(rect: Rect2) -> Array:
    var seen := {}
    var out: Array = []
    for key in _chunk_keys_for(rect):
        for i in chunks.get(key, {}).get("b", []):
            if not seen.has(i):
                seen[i] = true
                out.append(world_buildings[int(i)])
    return out

func _spawned_blocks(point: Vector2, building_id: String, floor_index: int) -> bool:
    for s in spawned:
        if not bool(s.get("solid", false)) or str(s["building_id"]) != building_id or int(s["floor"]) != floor_index:
            continue
        if str(s.get("behavior", "")) == "door" and bool(s.get("state", {}).get("open", false)):
            continue
        var c: Vector2 = _vec(s["pos"])
        var size: Array = s["size"]
        if absf(point.x - c.x) < float(size[0]) / 2.0 + 0.18 and absf(point.y - c.y) < float(size[1]) / 2.0 + 0.18:
            return true
    return false

## Single walkability rule for player AND teleport/spawn validation.
func walkable(point: Vector2, building_id: String, floor_index: int, from_point: Vector2) -> bool:
    if not _bounds().grow(-0.5).has_point(point):
        return false
    if not building_id.is_empty():
        var b: Dictionary = building_by_instance(building_id)
        if b.is_empty() or not _inside_footprint(b, point):
            return false
        if not room_factory.can_move(_plan_for(b, floor_index), from_point, point):
            return false
        return not _spawned_blocks(point, building_id, floor_index)
    for b in _buildings_in(Rect2(point - Vector2(1, 1), Vector2(2, 2))):
        if not _is_outdoor(b) and _inside_footprint(b, point):
            return false
    for v in _veg_near(point, 2.0):
        if bool(v["solid"]) and point.distance_to(_vec(v["pos"])) < float(v["radius"]) + 0.2:
            return false
    return not _spawned_blocks(point, "", 0)

func _can_walk(point: Vector2) -> bool:
    if god["enabled"] and god["noclip"]:
        return _bounds().grow(-0.5).has_point(point)
    return walkable(point, inside_id, current_floor, player)

## Spiral search for the nearest free tile. Used by teleport and spawning so
## nothing is ever placed inside collision.
func find_free_point(target: Vector2, building_id: String = "", floor_index: int = 0, max_radius: float = 12.0) -> Variant:
    var r: float = 0.0
    while r <= max_radius:
        var steps: int = maxi(1, int(r * 8.0))
        for i in range(steps):
            var a: float = TAU * float(i) / float(steps)
            var p: Vector2 = target + Vector2(cos(a), sin(a)) * r
            if walkable(p, building_id, floor_index, p):
                return p
        r += 0.5
    return null

# ------------------------------------------------------- doors and floors

func _path_clear(a: Vector2, b: Vector2, target: Dictionary) -> bool:
    var steps: int = maxi(1, ceili(a.distance_to(b) / 0.25))
    for i in range(1, steps):
        var p: Vector2 = a.lerp(b, float(i) / float(steps))
        for other in _buildings_in(Rect2(p - Vector2(1, 1), Vector2(2, 2))):
            if other == target or _is_outdoor(other):
                continue
            if _inside_footprint(other, p):
                return false
        for v in _veg_near(p, 1.5):
            if bool(v["solid"]) and p.distance_to(_vec(v["pos"])) < float(v["radius"]):
                return false
        if _spawned_blocks(p, "", 0):
            return false
    return true

func _door_candidate() -> Dictionary:
    var nearest: Dictionary = {}
    var best: float = ENTER_REACH
    for b in _buildings_in(Rect2(player - Vector2(8, 8), Vector2(16, 16))):
        var d: float = player.distance_to(_entry(b))
        if d < best and _path_clear(player, _entry(b) + _door_out(b) * 0.3, b):
            best = d
            nearest = b
    return nearest

func interact() -> void:
    var selected: Dictionary = _selected_building()
    if not selected.is_empty():
        if current_floor != 0:
            message = "Take the stairs down first (FLOOR, near the entry)"
            return
        super.interact()
        return
    var nearest: Dictionary = _door_candidate()
    if nearest.is_empty():
        message = "Approach a marked doorway (nothing in the way), then press ENTER"
        return
    if _is_outdoor(nearest):
        var points: int = 0
        for room in _plan_for(nearest, 0).get("rooms", []):
            for f in room["fixtures"]:
                if bool(f["interactive"]):
                    points += 1
        message = "%s — open-air site, %d search points. Walk in and press USE." % [nearest["name"], points]
        return
    var inside_point: Vector2 = _entry(nearest) - _door_out(nearest) * 1.5
    var plan: Dictionary = _plan_for(nearest, 0)
    if not _inside_footprint(nearest, inside_point) or not room_factory.can_move(plan, inside_point, inside_point):
        message = "Doorway of %s is blocked" % nearest.get("name", "building")
        return
    player = inside_point
    inside_id = _bid(nearest)
    current_floor = 0
    var stories: int = int(nearest.get("stories", 1))
    message = "Entered %s%s (provisional interior)" % [nearest["name"], "" if stories == 1 else " — %d floors, stairs at entry" % stories]
    _lock_door()
    queue_redraw()

func toggle_floor() -> void:
    var b: Dictionary = _selected_building()
    if b.is_empty():
        message = "Enter a building to use stairs"
        return
    var stories: int = int(b.get("stories", 1))
    if stories < 2:
        message = str(b["name"]) + " has a single floor"
        return
    var stair: Vector2 = _entry(b) - _door_out(b) * 1.5
    if player.distance_to(stair) > STAIR_REACH:
        message = "Stairs are by the entrance"
        return
    var target_floor: int = (current_floor + 1) % stories
    var plan: Dictionary = _plan_for(b, target_floor)
    var land: Variant = player
    if not walkable(player, _bid(b), target_floor, player):
        # Nearest free tile on the landing (fixtures such as handrails may
        # occupy the exact stair point).
        land = find_free_point(stair, _bid(b), target_floor, STAIR_REACH)
    if land == null:
        message = "Stair landing blocked"
        return
    player = land
    current_floor = target_floor
    message = "%s — floor %d of %d" % [b["name"], current_floor + 1, stories]
    queue_redraw()

func switch_mode() -> void:
    # Top-right button is ZOOM in the world sandbox (no lab/city switching).
    zoom_level = (zoom_level + 1) % 3
    message = "Zoom " + ["far", "normal", "close"][zoom_level]

func _top_button_titles() -> Array:
    return ["ROOF", "FLOOR", "MAP", "ZOOM"]

# ---------------------------------------------------- fixtures and loot

func _context_plans() -> Array:
    var active: Dictionary = _selected_building()
    if not active.is_empty():
        return [_plan_for(active, current_floor)]
    var plans: Array = []
    for b in _buildings_in(Rect2(player - Vector2(2, 2), Vector2(4, 4))):
        if _is_outdoor(b) and _inside_footprint(b, player):
            plans.append(_plan_for(b, 0))
    return plans

func _nearby_fixture() -> Dictionary:
    var closest: Dictionary = {}
    var nearest_distance := USE_REACH
    for plan in _context_plans():
        var occupied: String = room_factory.room_at(plan, player)
        for room in plan.get("rooms", []):
            if str(room["id"]) != occupied:
                continue
            for fixture in room["fixtures"]:
                var d: float = player.distance_to(_vec(fixture["pos"]))
                if d < nearest_distance:
                    closest = fixture.duplicate()
                    closest["room_kind"] = str(room["normalized_type"])
                    nearest_distance = d
    for s in spawned:
        if str(s["building_id"]) != inside_id or int(s["floor"]) != current_floor:
            continue
        var d: float = player.distance_to(_vec(s["pos"]))
        if d < minf(nearest_distance, 1.9):
            closest = {"spawned": s}
            nearest_distance = d
    return closest

func use_nearby_fixture() -> void:
    if health <= 0.0:
        return
    var target: Dictionary = _nearby_fixture()
    if target.is_empty():
        message = "Nothing to search here — stand beside furniture (same room)"
        return
    if target.has("spawned"):
        _use_spawned(target["spawned"])
        return
    super.use_nearby_fixture()

func _container_pool(s: Dictionary) -> String:
    var name: String = str(s.get("name", "")).to_lower()
    var mapping: Dictionary = rules.get("container_loot_by_spawn_name", {})
    if mapping.has(name):
        return str(mapping[name])
    return "garage" if str(s["behavior"]) == "vehicle" else "storage"

func _use_spawned(s: Dictionary) -> void:
    var behavior: String = str(s["behavior"])
    var state: Dictionary = s["state"]
    match behavior:
        "pickup", "weapon":
            if _inventory_count() >= int(rules["inventory_capacity"]):
                message = "Backpack full"
                return
            var item_id: String = str(s.get("item_id", s["spawn_id"]))
            inventory[item_id] = int(inventory.get(item_id, 0)) + 1
            spawned.erase(s)
            message = "Picked up " + str(s["name"]) + (" (provisional)" if item_id.begins_with("prov.") else "")
        "container", "vehicle":
            if looted_objects.has(str(s["id"])):
                message = "Already searched: " + str(s["name"])
                return
            if _inventory_count() >= int(rules["inventory_capacity"]):
                message = "Backpack full; cannot take more items"
                return
            var item_id: String = _loot_for({"id": str(s["id"])}, _container_pool(s))
            inventory[item_id] = int(inventory.get(item_id, 0)) + 1
            looted_objects[str(s["id"])] = item_id
            state["searched"] = true
            message = "Found %s in %s" % [rules["items"][item_id]["name"], s["name"]]
        "machine":
            state["on"] = not bool(state.get("on", false))
            message = "%s switched %s" % [s["name"], "ON" if state["on"] else "OFF"]
        "door":
            state["open"] = not bool(state.get("open", false))
            message = "%s %s" % [s["name"], "opened" if state["open"] else "closed"]
        "window":
            state["broken"] = true
            message = s["name"] + " smashed (noise — provisional)"
        "character":
            message = s["name"] + ": provisional survivor (no dialogue system yet)"
        _:
            message = "Inspected %s [%s, provisional art]" % [s["name"], s["spawn_id"]]
    queue_redraw()

# ---------------------------------------------------------- combat / AI

func _same_world(zombie: Dictionary) -> bool:
    return str(zombie["building_id"]) == inside_id and int(zombie["floor"]) == current_floor

func _can_zombie_walk(zombie: Dictionary, source: Vector2, target: Vector2) -> bool:
    return walkable(target, str(zombie["building_id"]), int(zombie["floor"]), source)

func _weapon_damage() -> int:
    var best: int = int(rules.get("base_damage", 1))
    for item_id in inventory.keys():
        if int(inventory[item_id]) > 0:
            var entry: Dictionary = catalog.get_entry(str(item_id))
            if str(entry.get("behavior", "")) == "weapon":
                best = maxi(best, int(entry.get("damage", 1)))
    return best

func attack() -> void:
    var before: Dictionary = {}
    for z in zombies:
        before[str(z["id"])] = int(z["health"])
    super.attack()
    var extra: int = _weapon_damage() - 1
    if extra <= 0:
        return
    for z in zombies:
        if int(before.get(str(z["id"]), int(z["health"]))) > int(z["health"]):
            z["health"] = maxi(0, int(z["health"]) - extra)
            message = "Hit the infected (weapon x%d)" % (extra + 1)

func _advance_zombies(dt: float) -> void:
    if god["enabled"] and god["pause_ai"]:
        return
    var hp: float = health
    super._advance_zombies(dt)
    if god["enabled"] and god["invulnerable"]:
        health = hp

func _process(delta: float) -> void:
    var t0: int = Time.get_ticks_usec()
    if not validation_error.is_empty():
        return
    super._process(delta)
    var dt: float = minf(delta, 0.05)
    if god["enabled"]:
        if god["invulnerable"]:
            health = 100.0
        if god["infinite_stamina"]:
            stamina = 100.0
        if god["no_needs"]:
            hunger = 100.0
            thirst = 100.0
    var per_hour: float = float(rules.get("time", {}).get("real_seconds_per_game_hour", 60.0))
    time_of_day = fposmod(time_of_day + dt / per_hour, 24.0)
    _advance_animals(dt)
    var us: float = float(Time.get_ticks_usec() - t0)
    perf["frames"] = int(perf["frames"]) + 1
    perf["process_us"] = lerpf(float(perf["process_us"]), us, 0.05)
    perf["max_process_us"] = maxf(float(perf["max_process_us"]) * 0.995, us)

func _advance_animals(dt: float) -> void:
    if god["enabled"] and god["pause_ai"]:
        return
    for s in spawned:
        if str(s["behavior"]) != "animal" or str(s["building_id"]) != inside_id:
            continue
        var phase: float = world_seconds * 0.4 + float(str(s["id"]).hash() % 1000)
        var step: Vector2 = Vector2(cos(phase), sin(phase * 0.7)) * 0.6 * dt
        var p: Vector2 = _vec(s["pos"]) + step
        if walkable(p, str(s["building_id"]), int(s["floor"]), _vec(s["pos"])):
            s["pos"] = [p.x, p.y]

# ------------------------------------------------------ God Mode API
# Every state-changing developer action calls _taint(): the run can then
# only be saved to the sandbox slot (scripts/sandbox/world_save.gd).

func _taint(what: String) -> void:
    if not dev_tainted:
        dev_tainted = true
    message = "[DEV] " + what

func god_set(flag: String, value: Variant) -> void:
    if not god.has(flag):
        return
    god[flag] = value
    if flag in ["show_collision", "show_building_ids", "show_room_ids"]:
        message = "[DEV view] %s = %s" % [flag, str(value)]
    else:
        _taint("%s = %s" % [flag, str(value)])
    if flag == "noclip" and not bool(value):
        _unstick_player()
    queue_redraw()

func _unstick_player() -> void:
    if walkable(player, inside_id, current_floor, player):
        return
    var p: Variant = find_free_point(player, inside_id, current_floor)
    if p == null and not inside_id.is_empty():
        var b: Dictionary = _selected_building()
        p = find_free_point(_entry(b) - _door_out(b) * 1.5, inside_id, current_floor)
    if p != null:
        player = p

func god_restore_normal() -> void:
    var keep_views: Dictionary = {"show_collision": god["show_collision"], "show_building_ids": god["show_building_ids"], "show_room_ids": god["show_room_ids"]}
    _reset_god()
    god.merge(keep_views, true)
    _unstick_player()
    message = "Normal survival restored (run stays marked DEV until NEW or a normal load)"

func god_teleport_building(instance_id: String) -> bool:
    var b: Dictionary = building_by_instance(instance_id)
    if b.is_empty():
        message = "Unknown building " + instance_id
        return false
    var p: Variant = find_free_point(_entry(b) + _door_out(b) * 2.0)
    if p == null:
        message = "No free tile near " + str(b["name"])
        return false
    inside_id = ""
    current_floor = 0
    player = p
    _reset_pointers()
    _taint("teleported to " + str(b["name"]))
    return true

func god_teleport_xy(x: float, y: float) -> bool:
    var p: Variant = find_free_point(Vector2(x, y))
    if p == null:
        message = "No free tile near %.1f, %.1f" % [x, y]
        return false
    inside_id = ""
    current_floor = 0
    player = p
    _reset_pointers()
    _taint("teleported to %.1f, %.1f" % [player.x, player.y])
    return true

## Returns the new stable instance id, or "" on failure.
func god_spawn(spawn_id: String) -> String:
    var entry: Dictionary = catalog.get_entry(spawn_id)
    if entry.is_empty():
        message = "Unknown spawn id " + spawn_id
        return ""
    var behavior: String = str(entry["behavior"])
    var around: Vector2 = player + facing.normalized() * 1.5
    if behavior == "zombie":
        var zp: Variant = find_free_point(around, inside_id, current_floor, 6.0)
        if zp == null:
            message = "No free tile to spawn " + str(entry["name"])
            return ""
        spawn_counter += 1
        var zid: String = "z.spawn.%06d" % spawn_counter
        zombies.append({"id": zid, "pos": [zp.x, zp.y], "building_id": inside_id, "floor": current_floor,
            "health": 3, "speed": 0.8, "attack_cooldown": 0.0, "spawn_id": spawn_id})
        _taint("spawned %s as %s" % [entry["name"], zid])
        return zid
    var size: Array = entry.get("size", [0.6, 0.6])
    var p: Variant = null
    var r: float = 0.0
    # Free spot whose whole footprint is walkable and clear of the player.
    while r <= 6.0 and p == null:
        var steps: int = maxi(1, int(r * 8.0))
        for i in range(steps):
            var a: float = TAU * float(i) / float(steps)
            var c: Vector2 = around + Vector2(cos(a), sin(a)) * r
            var ok: bool = true
            for corner in [Vector2(-1, -1), Vector2(1, -1), Vector2(1, 1), Vector2(-1, 1), Vector2.ZERO]:
                var q: Vector2 = c + corner * Vector2(float(size[0]), float(size[1])) * 0.5
                if not walkable(q, inside_id, current_floor, q):
                    ok = false
                    break
            if ok and bool(entry.get("solid", false)) and absf(c.x - player.x) < float(size[0]) / 2.0 + 0.5 and absf(c.y - player.y) < float(size[1]) / 2.0 + 0.5:
                ok = false
            if ok:
                p = c
                break
        r += 0.5
    if p == null:
        message = "No free space to spawn " + str(entry["name"])
        return ""
    spawn_counter += 1
    var iid: String = "sp.%06d" % spawn_counter
    var inst: Dictionary = {"id": iid, "spawn_id": spawn_id, "name": str(entry["name"]), "behavior": behavior,
        "category": str(entry["category"]), "pos": [p.x, p.y], "size": size.duplicate(),
        "solid": bool(entry.get("solid", false)), "building_id": inside_id, "floor": current_floor,
        "state": {}, "art_status": "PROVISIONAL_PROCEDURAL"}
    if entry.get("gameplay_item_id") != null:
        inst["item_id"] = str(entry["gameplay_item_id"])
    spawned.append(inst)
    _taint("spawned %s as %s" % [entry["name"], iid])
    return iid

func god_set_time(hour: float) -> void:
    time_of_day = fposmod(hour, 24.0)
    _taint("time set to %05.2f" % time_of_day)

func god_set_weather(kind: String) -> void:
    if kind in rules.get("weather", []):
        weather = kind
        _taint("weather " + kind)

## Sets the number of extra developer zombies (base world zombies untouched).
func god_set_zombie_extra(count: int) -> void:
    var keep: Array = []
    var existing: int = 0
    for z in zombies:
        if str(z["id"]).begins_with("z.dev."):
            existing += 1
            if existing > count:
                continue
        keep.append(z)
    zombies = keep
    var rng := RandomNumberGenerator.new()
    rng.seed = (str(world_seed) + ":dev:" + str(dev_zombie_counter)).hash()
    var attempts: int = 0
    while existing < count and attempts < count * 20 + 40:
        attempts += 1
        var p: Variant = find_free_point(player + Vector2(rng.randf_range(-14, 14), rng.randf_range(-14, 14)), "", 0, 4.0)
        if p == null or p.distance_to(player) < 4.0:
            continue
        dev_zombie_counter += 1
        zombies.append({"id": "z.dev.%05d" % dev_zombie_counter, "pos": [p.x, p.y], "building_id": "", "floor": 0,
            "health": 3, "speed": snappedf(rng.randf_range(0.6, 1.05), 0.01), "attack_cooldown": 0.0})
        existing += 1
    _taint("developer zombies: %d of %d requested" % [existing, count])

func god_reset_building(instance_id: String) -> bool:
    var b: Dictionary = building_by_instance(instance_id)
    if b.is_empty():
        return false
    var key: String = _bid(b)
    var prefix: String = key + "/floor/"
    for k in looted_objects.keys():
        if str(k).begins_with(prefix):
            looted_objects.erase(k)
    for k in fixture_states.keys():
        if str(k).begins_with(prefix):
            fixture_states.erase(k)
    var kept: Array = []
    for s in spawned:
        if str(s["building_id"]) != key:
            kept.append(s)
    spawned = kept
    var base_z: Dictionary = {}
    for z in layout["zombies"]:
        base_z[str(z["id"])] = z
    var z_kept: Array = []
    for z in zombies:
        if str(z["building_id"]) == key:
            continue
        z_kept.append(z)
    for z in layout["zombies"]:
        if str(z["building_id"]) == key:
            var fresh: Dictionary = z.duplicate(true)
            fresh["attack_cooldown"] = 0.0
            z_kept.append(fresh)
    zombies = z_kept
    _taint("reset " + str(b["name"]))
    return true

func god_reload_seed(seed: int) -> Array:
    world_seed = seed
    var keep_customs: Array = custom_buildings.duplicate(true)
    custom_buildings = keep_customs
    restart_pilot()
    _taint("world reloaded with seed %d (%d problems)" % [seed, layout_problems.size()])
    return layout_problems

func inspect_nearest() -> Dictionary:
    var target: Dictionary = _nearby_fixture()
    if target.has("spawned"):
        var s: Dictionary = target["spawned"]
        var info: Dictionary = s.duplicate(true)
        info["asset_chain"] = pipeline.chain_for(str(s["spawn_id"]), catalog.get_entry(str(s["spawn_id"])))
        return info
    if not target.is_empty():
        var info: Dictionary = target.duplicate(true)
        info["searched_item"] = looted_objects.get(str(target["id"]), null)
        info["state_open"] = fixture_states.get(str(target["id"]), false)
        info["asset_chain"] = pipeline.chain_for(str(target["role"]), {"solid": target.get("solid", true), "behavior": "searchable" if target["interactive"] else "inspect"})
        return info
    var best: Dictionary = {}
    var best_d: float = 4.0
    for z in zombies:
        if _same_world(z) and player.distance_to(_vec(z["pos"])) < best_d:
            best = z
            best_d = player.distance_to(_vec(z["pos"]))
    if not best.is_empty():
        return best.duplicate(true)
    var b: Dictionary = _selected_building()
    if b.is_empty():
        b = _door_candidate()
    if not b.is_empty():
        var info: Dictionary = {}
        for k in ["instance_id", "archetype_id", "name", "group", "district", "street", "footprint", "front_door", "rotation", "stories", "site_kind", "source", "art_status"]:
            info[k] = b.get(k)
        var room: String = room_factory.room_at(_plan_for(b, current_floor), player) if not inside_id.is_empty() else ""
        info["player_room_id"] = room
        return info
    return {"player": [snappedf(player.x, 0.01), snappedf(player.y, 0.01)], "inside": inside_id, "floor": current_floor}

func perf_stats() -> Dictionary:
    var alive: int = 0
    for z in zombies:
        if int(z["health"]) > 0:
            alive += 1
    return {"fps": Engine.get_frames_per_second(),
        "process_ms_avg": snappedf(float(perf["process_us"]) / 1000.0, 0.001),
        "process_ms_peak": snappedf(float(perf["max_process_us"]) / 1000.0, 0.001),
        "draw_ms_avg": snappedf(float(perf["draw_us"]) / 1000.0, 0.001),
        "draw_ms_peak": snappedf(float(perf["max_draw_us"]) / 1000.0, 0.001),
        "buildings": world_buildings.size(), "drawn_buildings": perf["drawn_buildings"],
        "vegetation": vegetation.size(), "drawn_vegetation": perf["drawn_veg"],
        "zombies_alive": alive, "zombies_total": zombies.size(), "spawned": spawned.size(),
        "room_plans": room_plans.size(), "chunks": chunks.size(),
        "draw_calls": Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME),
        "static_memory_mb": snappedf(Performance.get_monitor(Performance.MEMORY_STATIC) / 1048576.0, 0.1)}

# ------------------------------------------------------ builder / recipes

func _custom_conflict(b: Dictionary, buildings: Array, base: Dictionary) -> String:
    var r: Rect2 = GENERATOR.rect_of(b["footprint"])
    if not GENERATOR.rect_of(base["bounds"]).grow(-1.0).encloses(r):
        return "outside world bounds"
    for road in base["roads"]:
        if r.intersects(GENERATOR.rect_of(road)):
            return "overlaps a road"
    for other in buildings:
        if str(other["instance_id"]) != str(b["instance_id"]) and r.grow(0.9).intersects(GENERATOR.rect_of(other["footprint"])):
            return "overlaps " + str(other["name"])
    return ""

## Places a catalog archetype so its door is just in front of the player.
func god_place_building(archetype_id: String, rotation: int = 0) -> String:
    var item: Dictionary = generator._catalog_entry(archetype_id)
    if item.is_empty():
        message = "Unknown archetype " + archetype_id
        return ""
    if not inside_id.is_empty():
        message = "Leave the building before placing a new one"
        return ""
    custom_counter += 1
    var b: Dictionary = generator._template_from_catalog(item, "ll.custom.%04d.%s" % [custom_counter, archetype_id], "custom", {"id": "custom"})
    var w: float = float(b["size"][0])
    var h: float = float(b["size"][1])
    var rot: int = 180 if rotation == 180 else 0
    b["rotation"] = rot
    b["door_out"] = [0, 1] if rot == 0 else [0, -1]
    b["street"] = "custom"
    var x: float = snappedf(player.x - w / 2.0, 0.5)
    var y: float = snappedf(player.y - 1.0 - h, 0.5) if rot == 0 else snappedf(player.y + 1.0, 0.5)
    b["footprint"] = [x, y, w, h]
    var reason: String = _custom_conflict(b, world_buildings, layout)
    if reason.is_empty() and _inside_footprint(b, player):
        reason = "would trap the player"
    if not reason.is_empty():
        custom_counter -= 1
        message = "Cannot place %s here: %s" % [item["name"], reason]
        return ""
    var plans: Dictionary = generator._make_plans(b)
    if not generator._find_door(b, plans.get(str(b["instance_id"]) + "/0", {})):
        custom_counter -= 1
        message = "No valid doorway for " + str(item["name"])
        return ""
    b.erase("size")
    custom_buildings.append(b)
    _apply_world(_compose_world(world_seed, custom_buildings), world_seed)
    _unstick_player()
    _taint("placed %s (%s)" % [item["name"], b["instance_id"]])
    return str(b["instance_id"])

func layout_recipe() -> Dictionary:
    return {"base_recipe_id": str(generator.recipe["recipe_id"]), "seed": world_seed,
        "custom_buildings": custom_buildings.duplicate(true), "custom_counter": custom_counter,
        "spawned": spawned.duplicate(true), "spawn_counter": spawn_counter,
        "fixture_states": fixture_states.duplicate(true), "approval": "PROVISIONAL_SANDBOX",
        "art_status": "PROVISIONAL_PROCEDURAL"}

func god_save_recipe(name: String) -> String:
    var err: String = RECIPES.save_recipe(name, layout_recipe())
    message = ("Recipe saved: " + name) if err.is_empty() else ("Recipe not saved: " + err)
    return err

## Applies a layout recipe deterministically (base seed + authored deltas).
func apply_layout_recipe(recipe: Dictionary, seed_override: int = -1) -> Array:
    if str(recipe.get("base_recipe_id", "")) != str(generator.recipe["recipe_id"]):
        return ["recipe targets a different base world"]
    var seed: int = int(recipe.get("seed", world_seed)) if seed_override < 0 else seed_override
    world_seed = seed
    custom_buildings = recipe.get("custom_buildings", []).duplicate(true)
    restart_pilot()
    custom_counter = int(recipe.get("custom_counter", custom_buildings.size()))
    var dropped: Array = layout_problems.duplicate()
    for s in recipe.get("spawned", []):
        var inst: Dictionary = s.duplicate(true)
        var bid: String = str(inst.get("building_id", ""))
        var at: Vector2 = _vec(inst["pos"])
        if (not bid.is_empty() and building_by_instance(bid).is_empty()) or not walkable(at, bid, int(inst.get("floor", 0)), at):
            dropped.append("spawn %s dropped (position no longer free)" % inst.get("id", "?"))
            continue
        spawned.append(inst)
    spawn_counter = int(recipe.get("spawn_counter", spawned.size()))
    for key in recipe.get("fixture_states", {}).keys():
        fixture_states[key] = recipe["fixture_states"][key]
    dev_tainted = true
    message = "[DEV] layout recipe applied (seed %d, %d dropped)" % [seed, dropped.size()]
    return dropped

func god_load_recipe(name: String) -> Array:
    var res: Dictionary = RECIPES.load_recipe(name)
    if not res["ok"]:
        message = str(res["error"])
        return [res["error"]]
    return apply_layout_recipe(res["data"])

func god_generate_variation(name: String, seed: int, allow_provisional: bool) -> Array:
    var res: Dictionary = RECIPES.load_recipe(name) if not name.is_empty() else {"ok": true, "data": layout_recipe()}
    if not res["ok"]:
        message = str(res["error"])
        return [res["error"]]
    if not RECIPES.may_vary(res["data"], allow_provisional):
        message = "Variation needs a FOUNDER_APPROVED recipe (or allow provisional)"
        return ["not approved"]
    var dropped: Array = apply_layout_recipe(res["data"], seed)
    message = "[DEV] PROVISIONAL variation seed %d from %s (%d dropped)" % [seed, name if not name.is_empty() else "current layout", dropped.size()]
    return dropped

# ------------------------------------------------------------ save/load

func _snapshot() -> Dictionary:
    var snap: Dictionary = {
        "schema": WORLD_SAVE.SCHEMA, "schema_version": WORLD_SAVE.VERSION,
        "recipe_id": str(generator.recipe.get("recipe_id", "")), "rules_seed": str(rules.get("seed", "")),
        "seed": world_seed, "layout_hash": str(layout.get("layout_hash", "")),
        "custom_buildings": custom_buildings.duplicate(true), "custom_counter": custom_counter,
        "player": [player.x, player.y], "inside_id": inside_id, "floor": current_floor,
        "world_seconds": world_seconds, "time_of_day": time_of_day, "weather": weather,
        "health": health, "hunger": hunger, "thirst": thirst, "stamina": stamina,
        "inventory": inventory.duplicate(true), "looted_objects": looted_objects.duplicate(true),
        "fixture_states": fixture_states.duplicate(true), "zombies": zombies.duplicate(true),
        "spawned": spawned.duplicate(true), "spawn_counter": spawn_counter,
        "dev_zombie_counter": dev_zombie_counter, "dev_tainted": dev_tainted}
    if dev_tainted:
        snap["god"] = god.duplicate(true)
    return snap

func _restore_snapshot(data: Dictionary) -> bool:
    var migrated: Dictionary = WORLD_SAVE.migrate(data)
    if not migrated["ok"]:
        message = "Save rejected: " + str(migrated["error"])
        return false
    data = migrated["data"]
    if str(data.get("recipe_id", "")) != str(generator.recipe["recipe_id"]) or str(data.get("rules_seed", "")) != str(world_rules.get("seed", "")):
        message = "Save rejected: different world recipe or rules"
        return false
    var composed: Dictionary = _compose_world(int(data.get("seed", -1)), data.get("custom_buildings", []))
    if str(composed["layout_hash"]) != str(data.get("layout_hash", "")):
        message = "Save rejected: base layout does not reproduce (hash mismatch)"
        return false
    for stat in ["health", "hunger", "thirst", "stamina"]:
        if not data.has(stat) or float(data[stat]) < 0.0 or float(data[stat]) > 100.0:
            message = "Save rejected: invalid " + stat
            return false
    var inv: Dictionary = data.get("inventory", {})
    var count: int = 0
    for item_id in inv.keys():
        if int(inv[item_id]) < 0 or (not pilot_items.has(item_id) and catalog.get_entry(str(item_id)).is_empty()):
            message = "Save rejected: unknown inventory item " + str(item_id)
            return false
        count += int(inv[item_id])
    if count > int(world_rules["inventory_capacity"]):
        message = "Save rejected: backpack over capacity"
        return false
    var spawned_ids := {}
    for s in data.get("spawned", []):
        if not s is Dictionary or catalog.get_entry(str(s.get("spawn_id", ""))).is_empty() or spawned_ids.has(str(s.get("id", ""))):
            message = "Save rejected: invalid spawned object"
            return false
        spawned_ids[str(s["id"])] = true
    var fixture_ids := {}
    for plan in composed["plans"].values():
        for room in plan["rooms"]:
            for f in room["fixtures"]:
                if bool(f["interactive"]):
                    fixture_ids[str(f["id"])] = true
    for key in data.get("looted_objects", {}).keys():
        var looted_item: String = str(data["looted_objects"][key])
        if not pilot_items.has(looted_item):
            message = "Save rejected: invalid loot record"
            return false
        if not fixture_ids.has(key) and not str(key).begins_with("sp."):
            message = "Save rejected: loot record for unknown object " + str(key)
            return false
    var base_zombies := {}
    for z in composed["zombies"]:
        base_zombies[str(z["id"])] = true
    for z in data.get("zombies", []):
        var zid: String = str(z.get("id", ""))
        if not (base_zombies.has(zid) or zid.begins_with("z.dev.") or zid.begins_with("z.spawn.")):
            message = "Save rejected: unknown zombie " + zid
            return false
        if not z.get("pos") is Array or int(z.get("health", -1)) < 0 or int(z.get("health", 99)) > 3:
            message = "Save rejected: invalid zombie state"
            return false
    var incoming_inside: String = str(data.get("inside_id", ""))
    var incoming_floor: int = int(data.get("floor", 0))
    var p: Array = data.get("player", [])
    if p.size() != 2:
        return false
    # Fully validated: commit (fail-closed above; nothing was mutated).
    custom_buildings = data.get("custom_buildings", []).duplicate(true)
    _apply_world(composed, int(data["seed"]))
    var incoming_player: Vector2 = _vec(p)
    if not incoming_inside.is_empty():
        var b: Dictionary = building_by_instance(incoming_inside)
        if b.is_empty() or incoming_floor < 0 or incoming_floor >= int(b.get("stories", 1)):
            incoming_inside = ""
            incoming_floor = 0
    inside_id = incoming_inside
    current_floor = incoming_floor
    player = incoming_player
    custom_counter = int(data.get("custom_counter", custom_buildings.size()))
    health = float(data["health"])
    hunger = float(data["hunger"])
    thirst = float(data["thirst"])
    stamina = float(data["stamina"])
    world_seconds = maxf(0.0, float(data.get("world_seconds", 0.0)))
    time_of_day = fposmod(float(data.get("time_of_day", 9.0)), 24.0)
    weather = str(data.get("weather", "clear"))
    inventory = {}
    for item_id in pilot_items.keys():
        inventory[item_id] = 0
    for item_id in inv.keys():
        inventory[item_id] = int(inv[item_id])
    looted_objects = data.get("looted_objects", {}).duplicate(true)
    fixture_states = data.get("fixture_states", {}).duplicate(true)
    zombies = data.get("zombies", []).duplicate(true)
    for zombie in zombies:
        zombie["health"] = int(zombie["health"])
        zombie["floor"] = int(zombie.get("floor", 0))
        zombie["attack_cooldown"] = maxf(0.0, float(zombie.get("attack_cooldown", 0.0)))
    spawned = data.get("spawned", []).duplicate(true)
    for s in spawned:
        s["floor"] = int(s.get("floor", 0))
    spawn_counter = int(data.get("spawn_counter", 0))
    dev_zombie_counter = int(data.get("dev_zombie_counter", 0))
    dev_tainted = bool(data.get("dev_tainted", false))
    _reset_god()
    if dev_tainted and data.get("god") is Dictionary:
        for k in data["god"].keys():
            if god.has(k):
                god[k] = data["god"][k]
    mode = "world"
    escaped = false
    _reset_pointers()
    if not (god["enabled"] and god["noclip"]):
        _unstick_player()
    message = "Loaded %s world: searched furniture, items and zombies restored" % ("DEV sandbox" if dev_tainted else "survival")
    queue_redraw()
    return true

func save_game() -> bool:
    var slot: String = WORLD_SAVE.slot_for(dev_tainted)
    var err: String = WORLD_SAVE.write(slot, _snapshot())
    if not err.is_empty():
        message = "Save failed: " + err
        return false
    message = "Saved to %s slot" % ("SANDBOX (dev run)" if dev_tainted else "survival")
    return true

## Loads the slot matching the current run type (dev runs -> sandbox slot).
func load_game() -> bool:
    return load_slot(WORLD_SAVE.slot_for(dev_tainted))

func load_slot(slot: String) -> bool:
    var res: Dictionary = WORLD_SAVE.read(slot)
    if not res["ok"]:
        message = "Load failed: " + str(res["error"])
        return false
    return _restore_snapshot(res["data"])

# ---------------------------------------------------------------- input

func _key(keycode: int) -> void:
    match keycode:
        KEY_G:
            if god_panel != null:
                god_panel.toggle()
        KEY_TAB:
            switch_mode()
        _:
            super._key(keycode)

# -------------------------------------------------------------- drawing

func _screen_to_world(s: Vector2) -> Vector2:
    var iso: Vector2 = (s - _offset()) / _zoom()
    var a: float = iso.x / TX
    var b: float = iso.y / TY
    return Vector2((a + b) / 2.0, (b - a) / 2.0)

func _view_rect() -> Rect2:
    var s: Vector2 = get_viewport_rect().size
    var pts: Array = [_screen_to_world(Vector2.ZERO), _screen_to_world(Vector2(s.x, 0)),
        _screen_to_world(s), _screen_to_world(Vector2(0, s.y))]
    var r := Rect2(pts[0], Vector2.ZERO)
    for p in pts:
        r = r.expand(p)
    return r.grow(4.0).intersection(_bounds().grow(2.0))

func _draw_ground_view(view: Rect2) -> void:
    _quad_world(_bounds(), Color("344e3e"))
    if overview or _zoom() < 0.4:
        return
    for yy in range(maxi(0, int(view.position.y)), mini(int(_bounds().end.y), int(view.end.y))):
        for xx in range(maxi(0, int(view.position.x)), mini(int(_bounds().end.x), int(view.end.x))):
            var k: int = posmod(xx * 31 + yy * 19 + xx * yy * 3, 6)
            if k > 2:
                _quad_world(Rect2(xx, yy, 1, 1), Color("3a5944").lightened(float(k) * .017))

func _draw_roads(view: Rect2) -> void:
    for r in layout.get("sidewalks", []):
        var rect: Rect2 = GENERATOR.rect_of(r).intersection(view)
        if rect.size.x > 0 and rect.size.y > 0:
            _quad_world(rect, Color("8c8a80"))
    for r in layout.get("roads", []):
        var rect: Rect2 = GENERATOR.rect_of(r).intersection(view)
        if rect.size.x > 0 and rect.size.y > 0:
            _quad_world(rect, Color("45494c"))
    if overview:
        return
    for street in layout.get("streets", []):
        var y: float = float(street["road_y"]) + float(generator.recipe["street"]["road_width"]) / 2.0
        if y < view.position.y or y > view.end.y:
            continue
        var x: float = maxf(0.0, floor(view.position.x / 4.0) * 4.0)
        while x < minf(view.end.x, _bounds().end.x):
            draw_line(_iso(Vector2(x, y)), _iso(Vector2(x + 2.0, y)), Color("c9b56f"), 2.0)
            x += 4.0
    for path in layout.get("paths", []):
        var a: Vector2 = _vec(path[0])
        if view.has_point(a):
            draw_line(_iso(a), _iso(_vec(path[1])), Color("a99d85"), 6.0)

func _occludes_player(b: Dictionary) -> bool:
    if not inside_id.is_empty() or _is_outdoor(b):
        return false
    var r: Rect2 = _rect(b)
    # Building is in front of the player (closer to camera) and overlaps on screen.
    if r.get_center().x + r.get_center().y <= player.x + player.y:
        return false
    var sp: Vector2 = _iso(player)
    var poly := PackedVector2Array()
    for p in _shape(b):
        poly.append(_iso(p) - Vector2(0, 49))
    for p in _shape(b):
        poly.append(_iso(p))
    var hull: PackedVector2Array = Geometry2D.convex_hull(poly)
    return Geometry2D.is_point_in_polygon(sp - Vector2(0, 14), hull)

func _draw_tree(v: Dictionary) -> void:
    var at: Vector2 = _iso(_vec(v["pos"]))
    var kind: String = str(v["kind"])
    if kind == "bush":
        draw_circle(at + Vector2(0, -4), 9, Color("3f6b3f"))
        draw_circle(at + Vector2(5, -7), 6, Color("4d7d48"))
        return
    var big: float = 1.25 if kind == "tree_yard" else 1.0
    draw_circle(at + Vector2(0, 2), 10 * big, Color(0, 0, 0, 0.3))
    draw_rect(Rect2(at + Vector2(-2.5, -20 * big), Vector2(5, 20 * big)), Color("5d4634"))
    draw_circle(at + Vector2(0, -30 * big), 15 * big, Color("2f5a37"))
    draw_circle(at + Vector2(-7, -24 * big), 10 * big, Color("3b6a40"))
    draw_circle(at + Vector2(7, -36 * big), 9 * big, Color("467a49"))

func _spawn_color(behavior: String) -> Color:
    match behavior:
        "pickup": return Color("e2c46a")
        "weapon": return Color("d0846a")
        "container": return Color("9a825f")
        "vehicle": return Color("6c7f99")
        "machine": return Color("75848a")
        "animal": return Color("b49a74")
        "character": return Color("6095a5")
        "tree": return Color("2f5a37")
        "plant": return Color("4d7d48")
        "wall", "door", "window": return Color("8f8b7e")
        _: return Color("a99574")

func _draw_spawned(s: Dictionary) -> void:
    var c: Vector2 = _vec(s["pos"])
    var size: Vector2 = _vec(s["size"])
    var behavior: String = str(s["behavior"])
    var col: Color = _spawn_color(behavior)
    var tex: Dictionary = pipeline.texture_for(str(s["spawn_id"]))
    if not tex.is_empty():
        draw_texture(tex["texture"], _iso(c) - tex["pivot"])
        return
    if behavior in ["pickup", "weapon"]:
        draw_circle(_iso(c) + Vector2(0, -4), 6, col)
        draw_arc(_iso(c) + Vector2(0, -4), 8, 0, TAU, 16, Color("fff3c4"), 1.5)
    elif behavior in ["character", "animal"]:
        var at: Vector2 = _iso(c)
        draw_circle(at + Vector2(0, 2), 8, Color(0, 0, 0, .35))
        draw_rect(Rect2(at + Vector2(-5, -20 if behavior == "character" else -10), Vector2(10, 18 if behavior == "character" else 9)), col)
        draw_circle(at + Vector2(0, -24 if behavior == "character" else -12), 6 if behavior == "character" else 4, Color("d8baa1") if behavior == "character" else col.lightened(.2))
    elif behavior == "tree":
        _draw_tree({"pos": s["pos"], "kind": "tree_yard"})
    else:
        var h: float = 4.0 if behavior in ["floor", "prop", "plant"] else (22.0 if behavior == "vehicle" else 14.0)
        if behavior == "door" and bool(s["state"].get("open", false)):
            h = 3.0
        var r := Rect2(c - size / 2.0, size)
        var p: Vector2 = r.position
        draw_colored_polygon(PackedVector2Array([_iso(p + Vector2(0, size.y)), _iso(p + size), _iso(p + size) - Vector2(0, h), _iso(p + Vector2(0, size.y)) - Vector2(0, h)]), col.darkened(.3))
        draw_colored_polygon(PackedVector2Array([_iso(p + Vector2(size.x, 0)), _iso(p + size), _iso(p + size) - Vector2(0, h), _iso(p + Vector2(size.x, 0)) - Vector2(0, h)]), col.darkened(.2))
        _quad_world(r, col, h)
        if behavior in ["container", "vehicle"]:
            draw_circle(_iso(c) - Vector2(0, h + 3), 4.0, Color("8edaac") if looted_objects.has(str(s["id"])) else Color("eec977"))
        if behavior == "machine" and bool(s["state"].get("on", false)):
            draw_circle(_iso(c) - Vector2(0, h + 5), 4.0, Color("8ef0ff"))
    if _zoom() > 0.6:
        draw_string(ThemeDB.fallback_font, _iso(c) + Vector2(-30, 14), "PROV " + str(s["name"]).substr(0, 14), HORIZONTAL_ALIGNMENT_LEFT, -1, 10, Color("f0d9a0"))

func _draw_zombie(zombie: Dictionary) -> void:
    var at: Vector2 = _iso(_vec(zombie["pos"]))
    draw_circle(at + Vector2(0, 1), 9.0, Color(0, 0, 0, 0.4))
    draw_rect(Rect2(at + Vector2(-6, -25), Vector2(12, 19)), Color("865351"))
    draw_circle(at + Vector2(0, -28), 6, Color("a3ae8a"))
    draw_string(ThemeDB.fallback_font, at - Vector2(18, 39), "Z" + str(zombie["health"]),
        HORIZONTAL_ALIGNMENT_LEFT, -1, 12, Color("e9bc9d"))

func _draw_player() -> void:
    var at: Vector2 = _iso(player)
    draw_circle(at + Vector2(0, 2), 9, Color(0, 0, 0, .45))
    draw_rect(Rect2(at + Vector2(-5, -23), Vector2(10, 20)), Color("6095a5") if not (god["enabled"] and god["invulnerable"]) else Color("d6b44a"))
    draw_circle(at + Vector2(0, -27), 7, Color("d8baa1"))
    draw_line(at + Vector2(0, -12), at + Vector2(0, -12) + _iso(facing.normalized()).normalized() * 14, Color("f3e3bd"), 2)

func _draw_debug_overlays(view: Rect2, visible: Array) -> void:
    if god["show_collision"]:
        for b in visible:
            if not _is_outdoor(b):
                var pts: Array = _shape(b)
                for i in range(pts.size()):
                    draw_line(_iso(pts[i]), _iso(pts[(i + 1) % pts.size()]), Color(1, .25, .2, .9), 2)
            draw_circle(_iso(_entry(b)), 6, Color(.3, 1, .4, .9))
        var b2: Dictionary = _selected_building()
        if not b2.is_empty():
            for room in _plan_for(b2, current_floor)["rooms"]:
                for f in room["fixtures"]:
                    if bool(f.get("solid", true)):
                        var sz: Vector2 = _vec(f["size"]) + Vector2(.36, .36)
                        var rr := Rect2(_vec(f["pos"]) - sz / 2.0, sz)
                        var q: Array = [rr.position, Vector2(rr.end.x, rr.position.y), rr.end, Vector2(rr.position.x, rr.end.y)]
                        for i in range(4):
                            draw_line(_iso(q[i]), _iso(q[(i + 1) % 4]), Color(1, .4, .2, .8), 1.5)
        for key in _chunk_keys_for(view):
            for i in chunks.get(key, {}).get("v", []):
                var v: Dictionary = vegetation[int(i)]
                if bool(v["solid"]):
                    draw_arc(_iso(_vec(v["pos"])), (float(v["radius"]) + .2) * TX * .7, 0, TAU, 16, Color(1, .3, .2, .8), 1.5)
        for s in spawned:
            if bool(s["solid"]) and str(s["building_id"]) == inside_id:
                draw_circle(_iso(_vec(s["pos"])), 4, Color(1, .3, .2))
    if god["show_building_ids"]:
        for b in visible:
            draw_string(ThemeDB.fallback_font, _iso(_rect(b).get_center()) - Vector2(70, 84), str(b["instance_id"]),
                HORIZONTAL_ALIGNMENT_LEFT, -1, 11, Color("9cf0ff"))
    if god["show_room_ids"]:
        var b3: Dictionary = _selected_building()
        if not b3.is_empty():
            for room in _plan_for(b3, current_floor)["rooms"]:
                draw_string(ThemeDB.fallback_font, _iso(GENERATOR.rect_of(room["rect"]).get_center()) + Vector2(-50, 32), str(room["id"]),
                    HORIZONTAL_ALIGNMENT_LEFT, -1, 10, Color("ffd38a"))

func _draw_overview_labels() -> void:
    for street in layout.get("streets", []):
        var p: Vector2 = _offset() + _iso(Vector2(6.0, float(street["road_y"]))) * _zoom()
        draw_string(ThemeDB.fallback_font, p + Vector2(-8, -4), str(street["name"]), HORIZONTAL_ALIGNMENT_LEFT, -1, 12, Color("f3dfb5"))
    var pp: Vector2 = _offset() + _iso(player) * _zoom()
    draw_circle(pp, 6, Color("ff6a4a"))
    draw_string(ThemeDB.fallback_font, pp + Vector2(8, 4), "YOU", HORIZONTAL_ALIGNMENT_LEFT, -1, 12, Color("ffd0b0"))

func _draw_atmosphere() -> void:
    var s: Vector2 = get_viewport_rect().size
    var h: float = time_of_day
    var dark: float = 0.0
    if h < 5.0 or h >= 21.0:
        dark = 0.55
    elif h < 7.0:
        dark = 0.55 * (7.0 - h) / 2.0
    elif h >= 19.0:
        dark = 0.55 * (h - 19.0) / 2.0
    if weather in ["overcast", "rain", "storm"]:
        dark += 0.12
    if dark > 0.0:
        draw_rect(Rect2(Vector2.ZERO, s), Color(0.03, 0.05, 0.12, minf(dark, 0.7)))
    if weather == "fog":
        draw_rect(Rect2(Vector2.ZERO, s), Color(0.78, 0.8, 0.8, 0.28))
    if weather in ["rain", "storm"]:
        var drops: int = 90 if weather == "rain" else 160
        for i in range(drops):
            var x: float = fposmod(float(i * 97) + world_seconds * 60.0, s.x)
            var y: float = fposmod(float(i * 211) + world_seconds * (520.0 + float(i % 7) * 30.0), s.y)
            draw_line(Vector2(x, y), Vector2(x - 4, y + 14), Color(0.7, 0.8, 0.95, 0.45), 1.0)
        if weather == "storm" and fposmod(world_seconds, 7.0) < 0.12:
            draw_rect(Rect2(Vector2.ZERO, s), Color(1, 1, 1, 0.35))

func _draw() -> void:
    var t0: int = Time.get_ticks_usec()
    var s: Vector2 = get_viewport_rect().size
    draw_rect(Rect2(Vector2.ZERO, s), Color("121d19"))
    if not validation_error.is_empty():
        draw_string(ThemeDB.fallback_font, Vector2(14, 60), validation_error, HORIZONTAL_ALIGNMENT_LEFT, -1, 15, Color("ef9c94"))
        return
    var view: Rect2 = _view_rect()
    draw_set_transform(_offset(), 0, Vector2.ONE * _zoom())
    _draw_ground_view(view)
    _draw_roads(view)
    var visible: Array = _buildings_in(view)
    visible.sort_custom(func(a: Dictionary, b: Dictionary) -> bool:
        return _rect(a).get_center().x + _rect(a).get_center().y < _rect(b).get_center().x + _rect(b).get_center().y)
    var actors: Array = []
    var veg_count: int = 0
    if not overview:
        for key in _chunk_keys_for(view):
            for i in chunks.get(key, {}).get("v", []):
                actors.append({"k": 1, "d": vegetation[int(i)]})
                veg_count += 1
        for sp in spawned:
            if str(sp["building_id"]) == "" or (str(sp["building_id"]) == inside_id and int(sp["floor"]) == current_floor):
                if str(sp["building_id"]) == inside_id and inside_id == "" and not view.has_point(_vec(sp["pos"])):
                    continue
                actors.append({"k": 2, "d": sp})
        for z in zombies:
            if int(z["health"]) > 0 and _same_world(z) and view.has_point(_vec(z["pos"])):
                actors.append({"k": 3, "d": z})
        actors.append({"k": 4, "d": {"pos": [player.x, player.y]}})
    # One painter's sort for buildings + vegetation + props + actors.
    var drawables: Array = []
    for b in visible:
        drawables.append({"k": 0, "d": b, "depth": _rect(b).get_center().x + _rect(b).get_center().y})
    for a in actors:
        var pos: Array = a["d"]["pos"]
        a["depth"] = float(pos[0]) + float(pos[1])
        # Actors inside the active building always draw above its interior.
        if not inside_id.is_empty() and a["k"] != 1:
            a["depth"] += 1000.0
        drawables.append(a)
    drawables.sort_custom(func(a: Dictionary, b: Dictionary) -> bool: return float(a["depth"]) < float(b["depth"]))
    for item in drawables:
        match int(item["k"]):
            0:
                var b: Dictionary = item["d"]
                var cut: bool = _occludes_player(b)
                var keep_roof: bool = roof_hidden
                if cut:
                    roof_hidden = true
                _draw_building(b)
                roof_hidden = keep_roof
            1:
                if inside_id.is_empty():
                    _draw_tree(item["d"])
            2:
                _draw_spawned(item["d"])
            3:
                _draw_zombie(item["d"])
            4:
                _draw_player()
    _draw_debug_overlays(view, visible)
    draw_set_transform(Vector2.ZERO, 0, Vector2.ONE)
    if overview:
        _draw_overview_labels()
    _draw_atmosphere()
    perf["drawn_buildings"] = visible.size()
    perf["drawn_veg"] = veg_count
    _draw_hud()
    var us: float = float(Time.get_ticks_usec() - t0)
    perf["draw_us"] = lerpf(float(perf["draw_us"]), us, 0.05)
    perf["max_draw_us"] = maxf(float(perf["max_draw_us"]) * 0.995, us)

func _round_button(center: Vector2, radius: float, label: String, fill: Color, text_col: Color, size: int = 14) -> void:
    draw_circle(center, radius, fill)
    draw_arc(center, radius, 0, TAU, 32, Color("e5d0a1"), 2.0)
    draw_string(ThemeDB.fallback_font, center + Vector2(-radius, 5), label, HORIZONTAL_ALIGNMENT_CENTER, radius * 2.0, size, text_col)

func _draw_hud() -> void:
    var safe: Rect2 = _safe_rect()
    var top: float = safe.position.y
    var s: Vector2 = safe.end
    draw_rect(Rect2(0, 0, get_viewport_rect().size.x, top + 102), Color("14201b"))
    draw_string(ThemeDB.fallback_font, Vector2(safe.position.x + 14, top + 26), "LAST LIGHT · GM00 WORLD", HORIZONTAL_ALIGNMENT_LEFT, -1, 16, Color("eadab5"))
    var where: String = "Outdoors"
    var b: Dictionary = _selected_building()
    if not b.is_empty():
        where = "%s · F%d/%d" % [b["name"], current_floor + 1, int(b.get("stories", 1))]
    draw_string(ThemeDB.fallback_font, Vector2(safe.position.x + 14, top + 48), where.substr(0, 34), HORIZONTAL_ALIGNMENT_LEFT, -1, 12, Color("b9cdb8"))
    draw_string(ThemeDB.fallback_font, Vector2(safe.position.x + 14, top + 72), message.substr(0, 78), HORIZONTAL_ALIGNMENT_LEFT, safe.size.x - 28, 12, Color("ecd293"))
    var flags: String = "%02d:%02d %s" % [int(time_of_day), int(fposmod(time_of_day, 1.0) * 60.0), weather.to_upper()]
    if dev_tainted:
        flags += "  · DEV RUN (sandbox save slot)"
    if god["enabled"]:
        flags += "  · GOD"
    draw_string(ThemeDB.fallback_font, Vector2(safe.position.x + 14, top + 94), flags, HORIZONTAL_ALIGNMENT_LEFT, -1, 11, Color("ffb38a") if dev_tainted else Color("b4ba9f"))
    var titles: Array = _top_button_titles()
    for i in range(4):
        var x: float = s.x - 432 + i * 108
        draw_rect(Rect2(x, top + 9, 99, 36), Color("58655a"))
        draw_string(ThemeDB.fallback_font, Vector2(x, top + 32), titles[i], HORIZONTAL_ALIGNMENT_CENTER, 99, 13, Color("f5ecd6"))
    # Survival status
    draw_rect(Rect2(safe.position.x + 10, top + 109, 250, 64), Color(0.06, 0.13, 0.11, .89))
    draw_string(ThemeDB.fallback_font, Vector2(safe.position.x + 18, top + 131), "HP %d  ST %d  FOOD %d  H2O %d" % [int(health), int(stamina), int(hunger), int(thirst)], HORIZONTAL_ALIGNMENT_LEFT, -1, 13, Color("f3d1aa"))
    var bag: String = "BAG %d/%d · TIN %d WTR %d MED %d SCR %d" % [_inventory_count(), int(rules.get("inventory_capacity", 0)),
        int(inventory.get("proto.food_tin", 0)), int(inventory.get("proto.water_bottle", 0)), int(inventory.get("proto.bandage", 0)), int(inventory.get("proto.scrap", 0))]
    draw_string(ThemeDB.fallback_font, Vector2(safe.position.x + 18, top + 151), bag, HORIZONTAL_ALIGNMENT_LEFT, -1, 11, Color("cddfb7"))
    draw_string(ThemeDB.fallback_font, Vector2(safe.position.x + 18, top + 167), "Weapon x%d · provisional art" % _weapon_damage(), HORIZONTAL_ALIGNMENT_LEFT, -1, 10, Color("d7a98c"))
    var labels := ["HIT", "EAT", "DRINK", "MED", "SAVE", "LOAD", "NEW"]
    for i in range(labels.size()):
        _round_button(_game_button_center(i), 39.0, labels[i], Color("8f5750") if i == 0 else Color("566f66"), Color("f7e9cf"), 13)
    var stick: Vector2 = _touch_stick_center()
    draw_circle(stick, 67, Color(0.07, 0.13, 0.11, .82))
    draw_arc(stick, 67, 0, TAU, 36, Color("aeb59d"), 2)
    draw_circle(stick + motion * 44, 25, Color("d4b682"))
    _round_button(_enter_center(), 55.0, "EXIT" if not inside_id.is_empty() else "ENTER", Color("d3b883"), Color("273027"), 15)
    _round_button(_use_center(), 46.0, "USE", Color("7c9a87"), Color("10251b"), 16)
    if health <= 0.0:
        draw_rect(Rect2(get_viewport_rect().size * Vector2(.11, .45), get_viewport_rect().size * Vector2(.78, .1)), Color(0.1, 0.03, 0.03, .9))
        draw_string(ThemeDB.fallback_font, get_viewport_rect().size * Vector2(.11, .51), "YOU DIED — tap NEW", HORIZONTAL_ALIGNMENT_CENTER, get_viewport_rect().size.x * .78, 22, Color("f0b4a6"))
