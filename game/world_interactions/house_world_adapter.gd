extends RefCounted
## Bridges the current playable house (scripts/house.gd in main.tscn) to the world simulation
## WITHOUT modifying house.gd. Worker 01 owns the final wiring; see
## docs/world_simulation/WORKER01_HANDOFF.md for the exact call sites.
##
## - bind(house): builds a world layout from house.walls / house.doors / house.items.
## - World state is authoritative for doors and containers once bound. push_to_house() writes
##   it back into the dictionaries house.gd already reads for collision and drawing, so
##   visuals, collision and persistence agree.
## - pull_from_house() imports changes made by legacy house.gd code paths (its own door toggle
##   and the zombie breach in _process) so nothing is lost while both paths coexist.
##
## Instance ids reuse the PR #25 house_layout ids (house.kitchen.counter, ...) so its save
## `containers` map can be migrated with import_legacy_containers().

const B := preload("res://game/world_simulation/world_bootstrap.gd")
const Inv := preload("res://game/world_interactions/actor_inventory_port.gd")

const LAYOUT_ID := "main_house"
const SAVE_PATH := "user://last_light_world_main_house.json"
## house.gd item name -> [instance id (PR #25 layout id), definition]
const ITEM_MAP := {
	"KITCHEN COUNTER": ["house.kitchen.counter", "ll.furniture.kitchen_cabinet_pair"],
	"BED": ["house.bedroom.bed", "ll.furniture.single_bed"],
	"SOFA": ["house.living.sofa", "ll.furniture.sofa_two_seat"],
	"MEDICINE CABINET": ["house.bathroom.medicine", "ll.furniture.medicine_cabinet"],
}

var house: Node
var stack: Dictionary = {}
var world
var interactions
var inventory
var door_ids: Array = []
var item_ids: Array = []
var _req := 0
var _ticked := false
var _last_ms := 0


func bind(target: Node, seed_value: int = 1) -> bool:
	house = target
	if house == null or not "doors" in house or not "items" in house or not "walls" in house:
		push_error("HouseWorldAdapter: target is not scripts/house.gd")
		return false
	stack = B.create(build_layout(), seed_value)
	if stack.is_empty():
		return false
	world = stack.world
	interactions = stack.interactions
	inventory = Inv.new(stack.defs, 20.0)
	pull_from_house()
	world.dirty.clear()
	world.modified.clear()
	push_to_house()
	return true


func dispose() -> void:
	B.dispose(stack)
	world = null
	interactions = null
	house = null


func build_layout() -> Dictionary:
	var walls := []
	for w in house.walls:
		walls.append([w.a.x, w.a.y, w.b.x, w.b.y])
	var objects := []
	door_ids.clear()
	item_ids.clear()
	var home: Rect2 = house.HOME
	for d in house.doors:
		var a: Vector2 = d.a
		var b: Vector2 = d.b
		var horizontal: bool = absf(a.y - b.y) < 0.001
		var id := "door." + str(d.label).to_lower()
		var front: bool = d.label == "FRONT"
		var entry := {"id": id, "def": "ll.fixture.door.exterior_wood" if front else "ll.fixture.door.interior_wood",
			"pos": [(a.x + b.x) * 0.5, (a.y + b.y) * 0.5], "size": [a.distance_to(b), 0.0], "rot": 0 if horizontal else 1, "state": {}}
		if front:
			# Inside = the side facing the house centre (thumb-turn lock side).
			var dir := (b - a).normalized() if horizontal else Vector2.DOWN
			var e0: Vector2 = Vector2(entry.pos[0], entry.pos[1]) - dir * a.distance_to(b) * 0.5
			entry.state["inside_side"] = 1 if dir.cross(home.get_center() - e0) > 0.0 else -1
		objects.append(entry)
		door_ids.append(LAYOUT_ID + "/" + id)
	for it in house.items:
		var mapped: Array = ITEM_MAP.get(it.name, ["house.item." + str(it.name).to_lower().replace(" ", "_"), "ll.container.wooden_crate"])
		objects.append({"id": mapped[0], "def": mapped[1], "pos": [it.pos.x, it.pos.y], "size": [it.size.x, it.size.y]})
		item_ids.append(LAYOUT_ID + "/" + mapped[0])
	return {"schema": "last-light.world-layout.v1", "layout_id": LAYOUT_ID, "bounds": [-10, -8, 30, 26],
		"walls": walls, "objects": objects, "globals": {"grid_power": false, "water_mains": true, "ambient_c": 17.0}}


## Write authoritative world state into the dictionaries house.gd uses for collision + drawing.
func push_to_house() -> void:
	for i in door_ids.size():
		var o = world.objects.get(door_ids[i])
		if o == null:
			continue
		var passable: bool = (o.state.get("open", false) or o.state.get("broken", false)) and o.state.get("barricade", []).is_empty()
		house.doors[i].open = passable
		house.doors[i].health = float(o.state.get("hp", house.doors[i].health))
		house.doors[i]["locked"] = o.state.get("locked", false)
		house.doors[i]["broken"] = o.state.get("broken", false)
		house.doors[i]["barricade_layers"] = o.state.get("barricade", []).size()
	for i in item_ids.size():
		var o = world.objects.get(item_ids[i])
		house.items[i].searched = o == null or o.state.get("searched", false)
		if o != null:
			house.items[i]["open"] = o.state.get("open", false)
			house.items[i]["item_count"] = world.storage.total_items(o) if o.state.get("loot_initialized", false) else -1
	if house.has_method("queue_redraw"):
		house.queue_redraw()


## Import door changes made by legacy house.gd code (toggle, zombie breach).
func pull_from_house() -> void:
	for i in door_ids.size():
		var o = world.objects.get(door_ids[i])
		if o == null:
			continue
		var hd: Dictionary = house.doors[i]
		var world_open: bool = o.state.get("open", false) or o.state.get("broken", false)
		if float(hd.health) <= 0.0 and not o.state.get("broken", false):
			world.conditions.break_object(o, "legacy_zombie")
		elif float(hd.health) < float(o.state.get("hp", hd.health)):
			world.set_state(o, "hp", maxf(0.0, float(hd.health)))
		if bool(hd.open) != world_open and not o.state.get("broken", false):
			world.set_state(o, "open", bool(hd.open))
			if hd.open and o.state.get("locked", false):
				world.set_state(o, "locked", false)


## Advance the world clock; call from house._process(delta). Until it is called, request()
## falls back to real elapsed time so debounce and timers still progress.
func tick(dt: float) -> void:
	_ticked = true
	world.advance(dt)


func _advance_fallback() -> void:
	var now := Time.get_ticks_msec()
	if not _ticked and _last_ms > 0:
		world.advance(float(now - _last_ms) / 1000.0)
	_last_ms = now


func actor() -> Dictionary:
	return {"id": "player", "pos": house.player, "inventory": inventory}


## Execute a world action as the house player and sync the result back to house.gd.
func request(action_id: String, target_id: String, params: Dictionary = {}, request_id: String = "") -> Dictionary:
	_advance_fallback()
	pull_from_house()
	if request_id.is_empty():
		_req += 1
		request_id = "house-%d" % _req
	var full_id := target_id if target_id.begins_with(LAYOUT_ID + "/") else LAYOUT_ID + "/" + target_id
	var r: Dictionary = interactions.request({"request_id": request_id, "actor": actor(), "target_id": full_id, "action_id": action_id, "params": params})
	push_to_house()
	return r


## One-button contextual action for the existing INTERACT control.
func interact_contextual(request_id: String = "") -> Dictionary:
	_advance_fallback()
	pull_from_house()
	var c: Dictionary = interactions.contextual(actor(), 1.9)
	if c.is_empty():
		return {"ok": false, "failure_reason": "nothing_in_reach"}
	return request(c.action_id, c.target_id, {}, request_id)


func save(path: String = SAVE_PATH) -> Error:
	pull_from_house()
	return stack.saver.save(world, path)


func load_save(path: String = SAVE_PATH) -> String:
	var data = stack.saver.read(path)
	if data == null:
		return "no_save"
	var err: String = stack.saver.apply(world, data)
	if err.is_empty():
		push_to_house()
	return err


## Migrate PR #25 survival save v2 `containers` {layout_id: searched_bool}. A container that was
## searched under the old model was already emptied, so it becomes initialized-and-empty:
## loot can never be rolled again for it.
func import_legacy_containers(containers: Dictionary) -> int:
	var migrated := 0
	for legacy_id in containers:
		var o = world.objects.get(LAYOUT_ID + "/" + str(legacy_id))
		if o == null or not containers[legacy_id] is bool:
			continue
		if containers[legacy_id]:
			var contents := {}
			for c in world.storage.compartments(o):
				contents[c.id] = {}
			world.set_state(o, "contents", contents)
			world.set_state(o, "loot_initialized", true)
			world.set_state(o, "searched", true)
			migrated += 1
	push_to_house()
	return migrated
