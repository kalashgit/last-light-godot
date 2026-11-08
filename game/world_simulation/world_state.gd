extends RefCounted
## Authoritative runtime world-object state.
##
## - Instances come from an immutable layout (Worker 04 data) plus save deltas.
## - Time-dependent values (temperatures, fuel, rain) are solved analytically when an object is
##   "settled", so nothing ticks per frame. Only discrete events (e.g. generator fuel-out) are queued.
## - Every mutation goes through set_state(), which records the change, marks the object dirty for
##   incremental saving and raises navigation/collision events when blocking state changes.

signal world_event(event: Dictionary)

const WorldObject := preload("res://game/world_simulation/world_object.gd")
const CollisionModel := preload("res://game/world_simulation/collision_model.gd")
const StorageModel := preload("res://game/world_simulation/storage_model.gd")
const PowerNetwork := preload("res://game/world_simulation/power_network.gd")
const ThermalModel := preload("res://game/world_simulation/thermal_model.gd")
const WaterModel := preload("res://game/world_simulation/water_model.gd")
const ConditionModel := preload("res://game/world_simulation/condition_model.gd")

const CHUNK := 4.0
## State keys whose change can alter collision, line of sight or navigation.
const COLLISION_KEYS := ["open", "broken", "barricade"]
const EVENT_LOG_MAX := 256
## Upper bound for catch-up after the app was closed (12 in-game hours).
const MAX_OFFLINE_S := 43200.0

var defs
var objects: Dictionary = {}
## Deterministic iteration order (layout order, then spawn order).
var order: Array[String] = []
var layout_id: String = ""
var world_seed: int = 1
var time_s: float = 0.0
## Time owed to the clock because the per-call event budget was exhausted.
var pending_dt: float = 0.0
var globals: Dictionary = {"grid_power": true, "water_mains": true, "ambient_c": 18.0, "raining": false}
var bounds: Rect2 = Rect2(-50, -50, 100, 100)
## Immutable wall segments from the building layout: Array of [Vector2, Vector2].
var static_walls: Array = []
var rooms: Dictionary = {}

var dirty: Dictionary = {}
var modified: Dictionary = {}
var removed_ids: Dictionary = {}
var nav_revision: int = 0
var event_log: Array = []
var dynamic_ids: Dictionary = {}

var _chunks: Dictionary = {}
var _queue: Array = []
var _seq: int = 0
var _spawn_counter: Dictionary = {}

var collision
var storage
var power
var thermal
var water
var conditions


func _init(definitions = null, seed_value: int = 1) -> void:
	defs = definitions
	world_seed = seed_value
	collision = CollisionModel.new(self)
	storage = StorageModel.new(self)
	power = PowerNetwork.new(self)
	thermal = ThermalModel.new(self)
	water = WaterModel.new(self)
	conditions = ConditionModel.new(self)


## Break subsystem back-references (RefCounted cycles) when a world is discarded.
func dispose() -> void:
	for c in world_event.get_connections():
		world_event.disconnect(c["callable"])
	for sub in [collision, storage, power, thermal, water, conditions]:
		if sub != null:
			sub.world = null
	collision = null
	storage = null
	power = null
	thermal = null
	water = null
	conditions = null
	objects.clear()
	order.clear()
	_chunks.clear()
	_queue.clear()


# ---------------------------------------------------------------- layout / instances

func load_layout(layout: Dictionary) -> bool:
	layout_id = str(layout.get("layout_id", "world"))
	if layout.get("bounds") is Array and layout["bounds"].size() == 4:
		var b: Array = layout["bounds"]
		bounds = Rect2(b[0], b[1], b[2], b[3])
	static_walls.clear()
	for w in layout.get("walls", []):
		static_walls.append([Vector2(w[0], w[1]), Vector2(w[2], w[3])])
	rooms.clear()
	var raw_rooms: Dictionary = layout.get("rooms", {})
	for room_id in raw_rooms:
		var r: Array = raw_rooms[room_id]
		rooms[room_id] = Rect2(r[0], r[1], r[2], r[3])
	for g in layout.get("globals", {}):
		globals[g] = layout["globals"][g]
	for raw in layout.get("objects", []):
		var local_id := str(raw.get("id", ""))
		var def_id := str(raw.get("def", ""))
		if local_id.is_empty() or defs.get_def(def_id).is_empty():
			push_error("World layout object invalid: %s (%s)" % [local_id, def_id])
			return false
		var p: Array = raw.get("pos", [0, 0])
		var s = raw.get("size")
		var size_v := Vector2(s[0], s[1]) if s is Array else Vector2.ZERO
		if add_object(layout_id + "/" + local_id, def_id, Vector2(p[0], p[1]), size_v, int(raw.get("rot", 0)), str(raw.get("room", "")), raw.get("state", {}), false) == null:
			return false
	modified.clear()
	dirty.clear()
	power.recompute_all()
	modified.clear()
	dirty.clear()
	return true


func add_object(id: String, def_id: String, p: Vector2, size_override: Vector2, rot: int, room_id: String, overrides: Dictionary, is_spawned: bool):
	if objects.has(id):
		push_error("Duplicate world instance id " + id)
		return null
	var d: Dictionary = defs.get_def(def_id)
	if d.is_empty():
		return null
	var obj = WorldObject.new()
	obj.instance_id = id
	obj.definition_id = def_id
	obj.is_edge = d["footprint"]["kind"] == "edge"
	var fs: Array = d["footprint"]["size"]
	obj.size = size_override if size_override != Vector2.ZERO else Vector2(fs[0], fs[1])
	obj.pos = p
	obj.rotation = posmod(rot, 4)
	obj.room = room_id if not room_id.is_empty() else _room_at(obj.center())
	obj.spawned = is_spawned
	obj.state = _default_state(d)
	for k in overrides:
		obj.state[k] = overrides[k]
	obj.state["sim_t"] = time_s
	objects[id] = obj
	order.append(id)
	_index(obj)
	var caps: Array = d.get("capabilities", [])
	if "thermal" in caps or "generator" in caps or "water_storage" in caps:
		dynamic_ids[id] = true
	if is_spawned:
		_touch(obj)
	return obj


func spawn_object(parent_id: String, suffix: String, def_id: String, p: Vector2, overrides: Dictionary = {}):
	## Deterministic id: parent + suffix (+ counter only if reused).
	var base := parent_id + "~" + suffix
	var id := base
	var n: int = _spawn_counter.get(base, 0)
	while objects.has(id) or removed_ids.has(id):
		n += 1
		id = base + str(n)
	_spawn_counter[base] = n
	return add_object(id, def_id, p, Vector2.ZERO, 0, "", overrides, true)


func remove_object(id: String, reason: String) -> bool:
	var obj = objects.get(id)
	if obj == null or obj.removed:
		return false
	var old_rect: Rect2 = collision.bounds_of(obj)
	_unindex(obj)
	obj.removed = true
	objects.erase(id)
	order.erase(id)
	dynamic_ids.erase(id)
	unschedule(id, "")
	if obj.spawned:
		modified.erase(id)
		dirty[id] = true
	else:
		removed_ids[id] = true
		modified.erase(id)
		dirty[id] = true
	nav_revision += 1
	emit({"type": "object_removed", "object_id": id, "reason": reason})
	emit({"type": "navigation_changed", "object_id": id, "rect": old_rect, "nav_revision": nav_revision})
	if defs.has_cap(obj.definition_id, "power_consumer") or defs.has_cap(obj.definition_id, "generator"):
		power.mark_topology_dirty()
		power.recompute_all()
	return true


func get_obj(id: String):
	return objects.get(id)


func def_of(obj) -> Dictionary:
	return defs.get_def(obj.definition_id)


func has_cap(obj, cap: String) -> bool:
	return defs.has_cap(obj.definition_id, cap)


func comp(obj, cap: String) -> Dictionary:
	return defs.component(obj.definition_id, cap)


func _default_state(d: Dictionary) -> Dictionary:
	var caps: Array = d.get("capabilities", [])
	var c: Dictionary = d.get("components", {})
	var s := {}
	if "openable" in caps:
		s["open"] = false
	if "lockable" in caps:
		s["locked"] = false
		s["key_id"] = ""
	if "destructible" in caps:
		s["hp"] = float(c["destructible"]["max_hp"])
		s["broken"] = false
	if "glass" in caps:
		s["broken"] = false
	if "barricadable" in caps:
		s["barricade"] = []
		s["barricade_side"] = 0
	if "storage" in caps:
		s["loot_initialized"] = false
		s["searched"] = false
		s["contents"] = {}
	if "power_consumer" in caps:
		s["circuit"] = ""
		s["switched_on"] = bool(c["power_consumer"].get("always_on", false))
		s["powered"] = false
	if "generator" in caps:
		s["running"] = false
		s["fuel_l"] = 0.0
		s["panel"] = ""
		s["load_w"] = 0.0
	if "breaker_panel" in caps:
		var breakers := {}
		for circuit in c["breaker_panel"]["circuits"]:
			breakers[circuit] = true
		s["breakers"] = breakers
		s["grid_connected"] = true
	if "fuel_storage" in caps:
		s["fuel_l"] = float(c["fuel_storage"]["capacity_l"])
	if "thermal" in caps:
		var temps := {}
		for zone in c["thermal"]["zones"]:
			temps[zone] = float(globals.get("ambient_c", 18.0))
		s["temps"] = temps
	if "water_fixture" in caps:
		s["supply"] = "mains"
		if c["water_fixture"].has("cistern_l"):
			s["cistern_l"] = float(c["water_fixture"]["cistern_l"])
	if "water_storage" in caps:
		s["water_l"] = 0.0
		s["contaminated"] = bool(c["water_storage"].get("default_contaminated", false))
	return s


func _room_at(p: Vector2) -> String:
	for room_id in rooms:
		if rooms[room_id].has_point(p):
			return room_id
	return ""


# ---------------------------------------------------------------- mutation + events

## The single write path for mutable object state. `changes` (optional) collects
## {object_id, key, from, to} for ActionResult.state_changes.
func set_state(obj, key: String, value, changes = null) -> void:
	var old = obj.state.get(key)
	if typeof(old) == typeof(value) and old == value and not (value is Array or value is Dictionary):
		return
	obj.state[key] = value
	_touch(obj)
	if changes is Array:
		changes.append({"object_id": obj.instance_id, "key": key, "from": old, "to": value})
	if key in COLLISION_KEYS:
		_collision_changed(obj)


func set_placement(obj, new_pos: Vector2, new_rot: int, changes = null) -> void:
	var old_rect: Rect2 = collision.bounds_of(obj)
	_unindex(obj)
	var old_pos: Vector2 = obj.pos
	obj.pos = new_pos
	obj.rotation = posmod(new_rot, 4)
	obj.room = _room_at(obj.center())
	_index(obj)
	_touch(obj)
	if changes is Array:
		changes.append({"object_id": obj.instance_id, "key": "pos", "from": [old_pos.x, old_pos.y], "to": [new_pos.x, new_pos.y]})
	nav_revision += 1
	emit({"type": "navigation_changed", "object_id": obj.instance_id, "rect": old_rect.merge(collision.bounds_of(obj)), "nav_revision": nav_revision})


func _touch(obj) -> void:
	obj.revision += 1
	modified[obj.instance_id] = true
	dirty[obj.instance_id] = true


func _collision_changed(obj) -> void:
	nav_revision += 1
	emit({"type": "navigation_changed", "object_id": obj.instance_id, "rect": collision.bounds_of(obj), "nav_revision": nav_revision,
		"blocks_movement": collision.blocks_movement(obj), "sight_block": collision.sight_block(obj)})


func set_global(key: String, value) -> void:
	if globals.get(key) == value:
		return
	settle_all_dynamic()
	globals[key] = value
	emit({"type": "global_changed", "key": key, "value": value})
	if key == "grid_power":
		power.recompute_all()


func emit(event: Dictionary) -> void:
	event["t"] = time_s
	event_log.append(event)
	if event_log.size() > EVENT_LOG_MAX:
		event_log.pop_front()
	world_event.emit(event)


# ---------------------------------------------------------------- time

## Bring an object's time-dependent values up to the current clock.
func settle(obj) -> void:
	var dt: float = time_s - float(obj.state.get("sim_t", time_s))
	if dt <= 0.0:
		obj.state["sim_t"] = time_s
		return
	var caps: Array = def_of(obj).get("capabilities", [])
	if "generator" in caps:
		power.settle_generator(obj, dt)
	if "thermal" in caps:
		thermal.settle(obj, dt)
	if "water_storage" in caps:
		water.settle_tank(obj, dt)
	obj.state["sim_t"] = time_s
	if modified.has(obj.instance_id):
		dirty[obj.instance_id] = true


## Call before any change to shared conditions (power, ambient, room climate). Objects are
## settled under the old conditions and marked modified, because their trajectory now
## diverges from the layout baseline.
func settle_all_dynamic() -> void:
	for id in dynamic_ids:
		var obj = objects.get(id)
		if obj != null:
			settle(obj)
			if not modified.has(id):
				_touch(obj)


## Settle only already-modified dynamic objects (for saving). Untouched baseline objects are
## reproduced exactly by settling from the layout baseline after load, so they stay out of the delta.
func settle_for_save() -> void:
	for id in dynamic_ids:
		if modified.has(id):
			settle(objects[id])


func schedule(at: float, id: String, kind: String) -> void:
	unschedule(id, kind)
	_seq += 1
	var ev := {"t": at, "seq": _seq, "id": id, "kind": kind}
	var i := _queue.size()
	while i > 0 and (_queue[i - 1]["t"] > at):
		i -= 1
	_queue.insert(i, ev)


func unschedule(id: String, kind: String) -> void:
	for i in range(_queue.size() - 1, -1, -1):
		if _queue[i]["id"] == id and (kind.is_empty() or _queue[i]["kind"] == kind):
			_queue.remove_at(i)


func queued_events() -> Array:
	return _queue.duplicate(true)


## Advance the world clock. Processes at most `max_events` scheduled events; if the budget
## runs out the remaining time is carried over so the clock never skips an unprocessed event.
func advance(dt: float, max_events: int = 64) -> Dictionary:
	var target := time_s + pending_dt + maxf(dt, 0.0)
	pending_dt = 0.0
	var processed := 0
	while not _queue.is_empty() and float(_queue[0]["t"]) <= target:
		if processed >= max_events:
			pending_dt = target - time_s
			return {"processed": processed, "deferred_s": pending_dt}
		var ev: Dictionary = _queue.pop_front()
		time_s = maxf(time_s, float(ev["t"]))
		_handle_event(ev)
		processed += 1
	time_s = target
	return {"processed": processed, "deferred_s": 0.0}


## Apply elapsed real time while the game was closed, bounded to MAX_OFFLINE_S.
func advance_offline(seconds: float) -> Dictionary:
	var applied := clampf(seconds, 0.0, MAX_OFFLINE_S)
	var result := advance(applied, 100000)
	result["applied_s"] = applied
	result["requested_s"] = seconds
	settle_all_dynamic()
	return result


func _handle_event(ev: Dictionary) -> void:
	var obj = objects.get(ev["id"])
	if obj == null:
		return
	match ev["kind"]:
		"fuel_out":
			power.on_fuel_out(obj)


# ---------------------------------------------------------------- spatial index

func _chunk_keys(r: Rect2) -> Array:
	var keys := []
	var x0 := int(floor(r.position.x / CHUNK))
	var y0 := int(floor(r.position.y / CHUNK))
	var x1 := int(floor(r.end.x / CHUNK))
	var y1 := int(floor(r.end.y / CHUNK))
	for y in range(y0, y1 + 1):
		for x in range(x0, x1 + 1):
			keys.append(Vector2i(x, y))
	return keys


func _index(obj) -> void:
	for k in _chunk_keys(collision.bounds_of(obj)):
		if not _chunks.has(k):
			_chunks[k] = []
		_chunks[k].append(obj.instance_id)


func _unindex(obj) -> void:
	for k in _chunk_keys(collision.bounds_of(obj)):
		if _chunks.has(k):
			_chunks[k].erase(obj.instance_id)


## Object ids whose bounds touch `r`. Cost scales with the area, not the world size.
func query_rect(r: Rect2) -> Array:
	var seen := {}
	var out := []
	for k in _chunk_keys(r):
		for id in _chunks.get(k, []):
			if seen.has(id):
				continue
			seen[id] = true
			var obj = objects.get(id)
			if obj != null and collision.bounds_of(obj).grow(0.001).intersects(r):
				out.append(id)
	return out


## Low-frequency refresh of time-dependent state near the player (spatial activation zone).
## Touches at most `budget` dynamic objects per call; returns how many were settled.
func tick_active_zone(center_p: Vector2, radius: float, budget: int = 32) -> int:
	var count := 0
	for id in query_rect(Rect2(center_p - Vector2(radius, radius), Vector2(radius, radius) * 2.0)):
		if count >= budget:
			break
		if dynamic_ids.has(id):
			settle(objects[id])
			count += 1
	return count
