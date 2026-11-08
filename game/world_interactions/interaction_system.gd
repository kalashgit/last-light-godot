extends RefCounted
## Universal world-object interaction contract (Worker 05).
##
## ActionRequest (Dictionary):
##   request_id : String   unique per input gesture; repeats return the cached result (idempotent)
##   actor      : {id, pos: Vector2, inventory: Object, strength_kg?: float, occupants?: Array[Vector2]}
##   target_id  : String   world instance id
##   action_id  : String   e.g. "open", "take", "switch_on"
##   params     : Dictionary (action specific)
##
## ActionResult (Dictionary):
##   ok, duplicate, request_id, action_id, actor_id, target_id, failure_reason,
##   state_changes [{object_id, key, from, to}], events [world events raised],
##   animation {clip, event_frame?}, save_delta_ids [ids dirtied], data {action specific}
##
## Actions are only exposed when the target's definition lists them (validated at load
## against capabilities). Preconditions are all checked before any state is written, so a
## failed action never leaves partial changes. Inventory is reached through a duck-typed port
## compatible with Worker 02's survival_state.gd: add(id, n) -> bool, remove(id, n) -> bool,
## plus quantity(id) or an `inventory` Dictionary.

const PLANK := "ll_crafting_pine_plank"
const NAILS := "ll_crafting_nail_box"
const HAMMER := "ll_tools_claw_hammer"
const CROWBAR := "ll_tools_crowbar"
const WRENCH := "ll_tools_adjustable_wrench"
const FUEL_CAN := "ll_household_fuel_can"
const FUEL_CAN_EMPTY := "ll_world_fuel_can_empty"
const FUEL_CAN_L := 10.0
const PURIFIER := "ll_world_purification_tablets"
const WIRING_RANGE := 14.0
const WaterModel := preload("res://game/world_simulation/water_model.gd")

## range in tiles; anim = animation clip id for Worker 07; priority for contextual choice.
const ACTIONS := {
	"inspect": {"range": 4.0, "anim": ""},
	"open": {"range": 1.5, "anim": "interact_open", "event_frame": 7},
	"close": {"range": 1.5, "anim": "interact_close", "event_frame": 7},
	"lock": {"range": 1.3, "anim": "interact_key"},
	"unlock": {"range": 1.3, "anim": "interact_key"},
	"barricade": {"range": 1.3, "anim": "hammer_nail"},
	"unbarricade": {"range": 1.3, "anim": "pry"},
	"smash": {"range": 1.4, "anim": "melee_strike"},
	"repair": {"range": 1.4, "anim": "hammer_nail"},
	"search": {"range": 1.5, "anim": "search_container"},
	"take": {"range": 1.5, "anim": "take_item"},
	"put": {"range": 1.5, "anim": "take_item"},
	"move": {"range": 1.4, "anim": "push_heavy"},
	"switch_on": {"range": 1.5, "anim": "interact_switch"},
	"switch_off": {"range": 1.5, "anim": "interact_switch"},
	"connect": {"range": 1.5, "anim": "interact_plug"},
	"disconnect": {"range": 1.5, "anim": "interact_plug"},
	"toggle_breaker": {"range": 1.3, "anim": "interact_switch"},
	"start": {"range": 1.5, "anim": "pull_start"},
	"stop": {"range": 1.5, "anim": "interact_switch"},
	"refuel": {"range": 1.5, "anim": "pour"},
	"fill": {"range": 1.5, "anim": "fill_container"},
	"drink": {"range": 1.5, "anim": "drink"},
	"use": {"range": 1.5, "anim": "interact_use"},
	"pour": {"range": 1.5, "anim": "pour"},
	"drain": {"range": 1.5, "anim": "interact_use"},
	"treat": {"range": 1.5, "anim": "pour"},
}

var world
## Optional WorldVisualResolver: supplies F12 clip/event-frame contracts for action results.
var visuals = null
var debounce_s: float = 0.25
var history_size: int = 64
var _results_by_request: Dictionary = {}
var _request_order: Array = []
var _last_exec: Dictionary = {}
var _capture = null


func _init(w) -> void:
	world = w
	world.world_event.connect(_on_world_event)


func _on_world_event(event: Dictionary) -> void:
	if _capture != null:
		_capture.append(event)


# ---------------------------------------------------------------- public API

func request(req: Dictionary) -> Dictionary:
	var request_id := str(req.get("request_id", ""))
	if not request_id.is_empty() and _results_by_request.has(request_id):
		var cached: Dictionary = _results_by_request[request_id].duplicate(true)
		cached["duplicate"] = true
		cached["state_changes"] = []
		cached["events"] = []
		cached["save_delta_ids"] = []
		return cached
	var actor: Dictionary = req.get("actor", {})
	var action_id := str(req.get("action_id", ""))
	var target_id := str(req.get("target_id", ""))
	var params: Dictionary = req.get("params", {})
	var result := {
		"ok": false, "duplicate": false, "request_id": request_id, "action_id": action_id,
		"actor_id": str(actor.get("id", "")), "target_id": target_id, "failure_reason": "",
		"state_changes": [], "events": [], "animation": {}, "save_delta_ids": [], "data": {},
	}
	var reason := _validate_common(actor, target_id, action_id)
	if reason.is_empty():
		var debounce_key := "%s|%s|%s" % [actor.get("id", ""), target_id, action_id]
		if _last_exec.has(debounce_key) and world.time_s - float(_last_exec[debounce_key]) < debounce_s:
			result["duplicate"] = true
			reason = "duplicate_input"
		else:
			var obj = world.objects[target_id]
			world.settle(obj)
			var changes: Array = []
			_capture = []
			reason = _dispatch(action_id, obj, actor, params, changes, result["data"])
			result["events"] = _capture
			_capture = null
			result["state_changes"] = changes
			if reason.is_empty():
				_last_exec[debounce_key] = world.time_s
	result["failure_reason"] = reason
	result["ok"] = reason.is_empty()
	if result["ok"]:
		var spec: Dictionary = ACTIONS[action_id]
		if not str(spec.get("anim", "")).is_empty():
			result["animation"] = {"clip": spec["anim"], "event_frame": spec.get("event_frame", -1)}
		var tgt = world.objects.get(target_id)
		if visuals != null and tgt != null:
			var obj_anim: Dictionary = visuals.action_animation(tgt.definition_id, action_id)
			if not obj_anim.is_empty():
				result["animation"]["object"] = obj_anim
		var ids := {}
		for c in result["state_changes"]:
			ids[c["object_id"]] = true
		result["save_delta_ids"] = ids.keys()
		world.emit({"type": "action_completed", "action_id": action_id, "actor_id": result["actor_id"], "object_id": target_id})
	elif not result["state_changes"].is_empty():
		push_error("Action %s failed after writing state: %s" % [action_id, reason])
	if not request_id.is_empty():
		_results_by_request[request_id] = result.duplicate(true)
		_request_order.append(request_id)
		if _request_order.size() > history_size:
			_results_by_request.erase(_request_order.pop_front())
	return result


## Actions the definition exposes for this target (only implemented ones).
func supported_actions(target_id: String) -> Array:
	var obj = world.objects.get(target_id)
	if obj == null:
		return []
	return world.def_of(obj).get("actions", []).duplicate()


## Best single verb for a one-button mobile control, by object state. The request is still
## fully validated when executed.
func suggested_action(target_id: String, actor: Dictionary) -> String:
	var obj = world.objects.get(target_id)
	if obj == null:
		return ""
	var s: Dictionary = obj.state
	var acts: Array = supported_actions(target_id)
	var family: String = world.def_of(obj).get("family", "")
	if "unlock" in acts and s.get("locked", false):
		return "unlock"
	if "open" in acts and not s.get("open", false) and not s.get("broken", false):
		if s.get("barricade", []).size() > 0:
			return "unbarricade"
		return "open"
	if "search" in acts and not s.get("searched", false):
		return "search"
	if "take" in acts and world.storage.total_items(obj) > 0:
		return "take"
	if "start" in acts:
		if s.get("running", false):
			return "stop"
		return "refuel" if float(s.get("fuel_l", 0.0)) <= 0.0 else "start"
	if "switch_on" in acts:
		return "switch_off" if s.get("switched_on", false) else "switch_on"
	if "drink" in acts:
		return "drink"
	if "use" in acts:
		return "use"
	if "close" in acts and s.get("open", false) and not s.get("broken", false) and family != "":
		return "close"
	return "inspect"


## Nearest object within reach and its suggested verb. {} when nothing is in reach.
func contextual(actor: Dictionary, reach: float = 1.5) -> Dictionary:
	var p: Vector2 = actor.get("pos", Vector2.ZERO)
	var best := {}
	var best_d := INF
	for id in world.query_rect(Rect2(p - Vector2(reach, reach), Vector2(reach, reach) * 2.0)):
		var obj = world.objects[id]
		var d: float = p.distance_to(obj.closest_point(p))
		if d <= reach and d < best_d:
			best_d = d
			best = {"target_id": id, "action_id": suggested_action(id, actor), "distance": d}
	return best


# ---------------------------------------------------------------- validation helpers

func _validate_common(actor: Dictionary, target_id: String, action_id: String) -> String:
	if not ACTIONS.has(action_id):
		return "unknown_action"
	if not actor.get("pos") is Vector2 or str(actor.get("id", "")).is_empty():
		return "invalid_actor"
	var obj = world.objects.get(target_id)
	if obj == null:
		return "target_missing"
	if not action_id in world.def_of(obj).get("actions", []):
		return "action_not_supported"
	var p: Vector2 = actor["pos"]
	if p.distance_to(obj.closest_point(p)) > float(ACTIONS[action_id]["range"]):
		return "out_of_range"
	return ""


func _qty(actor: Dictionary, item_id: String) -> int:
	var inv = actor.get("inventory")
	if inv == null:
		return 0
	if inv.has_method("quantity"):
		return int(inv.quantity(item_id))
	if "inventory" in inv:
		return int(inv.inventory.get(item_id, 0))
	return 0


func _swap_items(actor: Dictionary, remove_id: String, add_id: String) -> bool:
	## Atomic inventory exchange used by fill/pour/refuel.
	var inv = actor.get("inventory")
	if inv == null or not inv.remove(remove_id, 1):
		return false
	if not inv.add(add_id, 1):
		inv.add(remove_id, 1)
		return false
	return true


func _sound(obj, radius: float, cue: String) -> void:
	world.emit({"type": "sound", "object_id": obj.instance_id, "pos": obj.center(), "radius": radius, "cue": cue})


func _side_ok(obj, actor: Dictionary, required: int) -> bool:
	return required == 0 or not obj.is_edge or obj.edge_side(actor["pos"]) == required


func _doorway_occupied(obj, actor: Dictionary) -> bool:
	var e: Array = obj.edge_points()
	var points: Array = actor.get("occupants", []).duplicate()
	points.append(actor["pos"])
	for p in points:
		if Geometry2D.get_closest_point_to_segment(p, e[0], e[1]).distance_to(p) < 0.32:
			return true
	return false


# ---------------------------------------------------------------- dispatch

func _dispatch(action_id: String, obj, actor: Dictionary, params: Dictionary, ch: Array, data: Dictionary) -> String:
	match action_id:
		"inspect": return _inspect(obj, data)
		"open": return _open(obj, ch)
		"close": return _close(obj, actor, ch)
		"lock", "unlock": return _lock(obj, actor, action_id == "lock", ch)
		"barricade": return _barricade(obj, actor, ch, data)
		"unbarricade": return _unbarricade(obj, actor, ch)
		"smash": return _smash(obj, ch)
		"repair": return _repair(obj, actor, ch)
		"search": return _search(obj, ch, data)
		"take": return _take(obj, actor, params, ch, data)
		"put": return _put(obj, actor, params, ch)
		"move": return _move(obj, actor, params, ch)
		"switch_on", "switch_off": return _switch(obj, action_id == "switch_on", ch, data)
		"connect": return _connect(obj, params, ch)
		"disconnect": return _disconnect(obj, ch)
		"toggle_breaker": return _toggle_breaker(obj, params, ch)
		"start", "stop": return _start_stop(obj, action_id == "start", ch)
		"refuel": return _refuel(obj, actor, params, ch, data)
		"fill": return _fill(obj, actor, params, ch, data)
		"drink": return _drink(obj, actor, ch, data)
		"use": return _use(obj, ch, data)
		"pour": return _pour(obj, actor, params, ch)
		"drain": return _drain(obj, ch)
		"treat": return _treat(obj, actor, ch)
	return "unknown_action"


func describe(obj) -> Dictionary:
	var d: Dictionary = world.def_of(obj)
	var out := {"name": d.get("canonical_name", obj.definition_id), "condition": world.conditions.condition_of(obj), "state": obj.state.duplicate(true)}
	if world.has_cap(obj, "thermal"):
		var temps := {}
		for zone in world.comp(obj, "thermal")["zones"]:
			temps[zone] = snappedf(world.thermal.temperature(obj, zone), 0.1)
		out["temperatures_c"] = temps
	if world.has_cap(obj, "storage"):
		out["items"] = world.storage.total_items(obj) if obj.state.get("loot_initialized", false) else -1
	return out


func _inspect(obj, data: Dictionary) -> String:
	data.merge(describe(obj), true)
	return ""


# ---------------------------------------------------------------- doors, windows, locks, barricades

func _open(obj, ch: Array) -> String:
	if obj.state.get("open", false):
		return "already_open"
	if obj.state.get("broken", false):
		return "broken"
	if obj.state.get("locked", false):
		return "locked"
	if obj.state.get("barricade", []).size() > 0:
		return "barricaded"
	world.set_state(obj, "open", true, ch)
	_sound(obj, float(world.comp(obj, "openable").get("noise_radius", 1.0)), "open_" + str(world.def_of(obj).get("family", "")))
	if world.has_cap(obj, "storage"):
		world.storage.ensure_initialized(obj, ch)
	return ""


func _close(obj, actor: Dictionary, ch: Array) -> String:
	if not obj.state.get("open", false):
		return "already_closed"
	if obj.state.get("broken", false):
		return "broken"
	if obj.is_edge and _doorway_occupied(obj, actor):
		return "doorway_blocked"
	world.set_state(obj, "open", false, ch)
	_sound(obj, float(world.comp(obj, "openable").get("noise_radius", 1.0)), "close_" + str(world.def_of(obj).get("family", "")))
	return ""


func _lock(obj, actor: Dictionary, lock: bool, ch: Array) -> String:
	if obj.state.get("broken", false):
		return "broken"
	if lock and obj.state.get("open", false):
		return "must_close_first"
	if obj.state.get("locked", false) == lock:
		return "already_locked" if lock else "already_unlocked"
	var dest: Dictionary = world.comp(obj, "destructible")
	if lock and not dest.is_empty() and float(obj.state.get("hp", 1.0)) / float(dest["max_hp"]) < float(dest.get("lock_fails_below", 0.0)):
		return "lock_damaged"
	var thumbturn: bool = world.comp(obj, "lockable").get("inside_thumbturn", false)
	var inside := int(obj.state.get("inside_side", 0))
	var from_inside: bool = thumbturn and obj.is_edge and inside != 0 and obj.edge_side(actor["pos"]) == inside
	if not from_inside:
		var key: String = obj.state.get("key_id", "")
		if key.is_empty() or _qty(actor, key) < 1:
			return "requires_key"
	world.set_state(obj, "locked", lock, ch)
	_sound(obj, 1.0, "lock_click")
	return ""


func _barricade(obj, actor: Dictionary, ch: Array, data: Dictionary) -> String:
	if obj.state.get("open", false):
		return "must_close_first"
	var spec: Dictionary = world.comp(obj, "barricadable")
	var layers: Array = obj.state.get("barricade", [])
	if layers.size() >= int(spec["max_layers"]):
		return "barricade_full"
	var side: int = obj.edge_side(actor["pos"])
	if side == 0:
		return "stand_to_one_side"
	if int(obj.state.get("barricade_side", 0)) != 0 and side != int(obj.state["barricade_side"]):
		return "wrong_side"
	if _qty(actor, HAMMER) < 1:
		return "requires_hammer"
	if _qty(actor, PLANK) < 1 or _qty(actor, NAILS) < 1:
		return "requires_plank_and_nails"
	var inv = actor["inventory"]
	if not inv.remove(PLANK, 1):
		return "requires_plank_and_nails"
	if not inv.remove(NAILS, 1):
		inv.add(PLANK, 1)
		return "requires_plank_and_nails"
	var new_layers := layers.duplicate()
	new_layers.append(float(spec["layer_hp"]))
	world.set_state(obj, "barricade", new_layers, ch)
	world.set_state(obj, "barricade_side", side, ch)
	_sound(obj, 12.0, "hammer_nail")
	data["layers"] = new_layers.size()
	data["consumed"] = {PLANK: 1, NAILS: 1}
	return ""


func _unbarricade(obj, actor: Dictionary, ch: Array) -> String:
	var layers: Array = obj.state.get("barricade", [])
	if layers.is_empty():
		return "not_barricaded"
	if not _side_ok(obj, actor, int(obj.state.get("barricade_side", 0))):
		return "wrong_side"
	if _qty(actor, HAMMER) < 1 and _qty(actor, CROWBAR) < 1:
		return "requires_hammer_or_crowbar"
	var new_layers := layers.duplicate()
	new_layers.pop_back()
	world.set_state(obj, "barricade", new_layers, ch)
	if new_layers.is_empty():
		world.set_state(obj, "barricade_side", 0, ch)
	# The plank is recovered when there is room; otherwise it is lost (reported).
	var recovered: bool = actor["inventory"].add(PLANK, 1)
	world.emit({"type": "barricade_removed", "object_id": obj.instance_id, "plank_recovered": recovered})
	_sound(obj, 8.0, "pry_plank")
	return ""


func _smash(obj, ch: Array) -> String:
	if obj.state.get("broken", false):
		return "already_broken"
	var r: Dictionary = world.conditions.apply_damage(obj.instance_id, float(obj.state.get("hp", 1.0)) + float(world.comp(obj, "destructible").get("max_hp", 1.0)), "smash", ch)
	if not r.get("ok", false):
		return str(r.get("reason", "cannot_smash"))
	if not r.get("broken_now", false):
		return ""  # a barricade absorbed the blow; still a valid action
	return ""


func _repair(obj, actor: Dictionary, ch: Array) -> String:
	var m: float = world.conditions.max_hp(obj)
	var flooded: bool = world.conditions.env_flags(obj).get("flooded", false)
	if float(obj.state.get("hp", m)) >= m and not obj.state.get("broken", false) and not flooded:
		return "not_damaged"
	if world.def_of(obj).get("sound_material", "") == "wood":
		if _qty(actor, HAMMER) < 1:
			return "requires_hammer"
		if _qty(actor, PLANK) < 1 or _qty(actor, NAILS) < 1:
			return "requires_plank_and_nails"
		var inv = actor["inventory"]
		inv.remove(PLANK, 1)
		if not inv.remove(NAILS, 1):
			inv.add(PLANK, 1)
			return "requires_plank_and_nails"
	elif _qty(actor, WRENCH) < 1:
		return "requires_wrench"
	world.set_state(obj, "hp", minf(m, float(obj.state.get("hp", 0.0)) + m * 0.5), ch)
	if obj.state.get("broken", false):
		world.set_state(obj, "broken", false, ch)
	if flooded:
		var env: Dictionary = world.conditions.env_flags(obj).duplicate()
		env.erase("flooded")
		world.set_state(obj, "env", env, ch)
	_sound(obj, 8.0, "repair")
	world.conditions._power_refresh(obj)
	return ""


# ---------------------------------------------------------------- containers

func _access(obj) -> String:
	if world.comp(obj, "storage").get("door_gated", false) and not obj.state.get("open", false):
		return "container_closed"
	return ""


func _search(obj, ch: Array, data: Dictionary) -> String:
	var r := _access(obj)
	if not r.is_empty():
		return r
	var rolled: bool = world.storage.ensure_initialized(obj, ch)
	world.set_state(obj, "searched", true, ch)
	data["rolled_now"] = rolled
	data["contents"] = obj.state["contents"].duplicate(true)
	world.emit({"type": "container_searched", "object_id": obj.instance_id, "items": world.storage.total_items(obj)})
	return ""


func _find_compartment(obj, item_id: String, n: int) -> String:
	for c in world.storage.compartments(obj):
		if world.storage.count(obj, c["id"], item_id) >= n:
			return c["id"]
	return ""


func _take(obj, actor: Dictionary, params: Dictionary, ch: Array, data: Dictionary) -> String:
	var r := _access(obj)
	if not r.is_empty():
		return r
	world.storage.ensure_initialized(obj, ch)
	var item_id := str(params.get("item_id", ""))
	var n := int(params.get("count", 1))
	if item_id.is_empty():
		# Contextual take: first item in deterministic order.
		for c in world.storage.compartments(obj):
			var ids: Array = world.storage.items_in(obj, c["id"]).keys()
			ids.sort()
			if not ids.is_empty():
				item_id = ids[0]
				break
	if item_id.is_empty():
		return "container_empty"
	if n < 1:
		return "invalid_count"
	var comp_id := str(params.get("compartment", ""))
	if comp_id.is_empty():
		comp_id = _find_compartment(obj, item_id, n)
	if comp_id.is_empty() or world.storage.count(obj, comp_id, item_id) < n:
		return "item_not_in_container"
	var inv = actor.get("inventory")
	if inv == null or not inv.add(item_id, n):
		return "inventory_full"
	if not world.storage.remove(obj, comp_id, item_id, n, ch):
		inv.remove(item_id, n)
		return "item_not_in_container"
	data["item_id"] = item_id
	data["count"] = n
	world.emit({"type": "item_transferred", "from": obj.instance_id, "to": actor["id"], "item_id": item_id, "count": n})
	if world.comp(obj, "storage").get("remove_when_empty", false) and world.storage.total_items(obj) == 0:
		world.remove_object(obj.instance_id, "emptied")
	return ""


func _put(obj, actor: Dictionary, params: Dictionary, ch: Array) -> String:
	var r := _access(obj)
	if not r.is_empty():
		return r
	world.storage.ensure_initialized(obj, ch)
	var item_id := str(params.get("item_id", ""))
	var n := int(params.get("count", 1))
	if item_id.is_empty() or n < 1:
		return "invalid_item"
	if _qty(actor, item_id) < n:
		return "not_in_inventory"
	var comp_id := str(params.get("compartment", world.storage.default_compartment(obj)))
	var why: String = world.storage.can_add(obj, comp_id, item_id, n)
	if not why.is_empty():
		return why
	if not actor["inventory"].remove(item_id, n):
		return "not_in_inventory"
	world.storage.add(obj, comp_id, item_id, n, ch)
	world.emit({"type": "item_transferred", "from": actor["id"], "to": obj.instance_id, "item_id": item_id, "count": n})
	return ""


# ---------------------------------------------------------------- furniture

func _move(obj, actor: Dictionary, params: Dictionary, ch: Array) -> String:
	var spec: Dictionary = world.comp(obj, "movable")
	var to_raw = params.get("to")
	var to: Vector2 = to_raw if to_raw is Vector2 else (Vector2(to_raw[0], to_raw[1]) if to_raw is Array else obj.pos)
	var rot := int(params.get("rotation", obj.rotation))
	if spec.get("requires_disconnect", false) and (not str(obj.state.get("circuit", "")).is_empty() or not str(obj.state.get("panel", "")).is_empty()):
		return "disconnect_first"
	if obj.state.get("running", false):
		return "stop_first"
	var mass: float = float(spec.get("mass_kg", 0.0)) + (world.storage.weight(obj) if world.has_cap(obj, "storage") else 0.0)
	if mass > float(actor.get("strength_kg", 70.0)):
		return "too_heavy"
	if to.distance_to(obj.pos) > float(spec.get("max_step_tiles", 1.0)) + 0.001:
		return "too_far"
	var old_rot: int = obj.rotation
	var old_pos: Vector2 = obj.pos
	obj.rotation = posmod(rot, 4)
	obj.pos = to
	var new_rect: Rect2 = obj.rect()
	obj.rotation = old_rot
	obj.pos = old_pos
	var blocker: String = world.collision.rect_blocker(new_rect, obj.instance_id)
	if not blocker.is_empty():
		return "placement_blocked"
	var people: Array = actor.get("occupants", []).duplicate()
	people.append(actor["pos"])
	for p in people:
		if new_rect.grow(0.15).has_point(p):
			return "placement_occupied"
	world.set_placement(obj, to, rot, ch)
	_sound(obj, 6.0, "furniture_drag")
	return ""


# ---------------------------------------------------------------- power

func _refresh_power(obj) -> void:
	var panel: String = world.power.panel_id_of(obj) if world.has_cap(obj, "power_consumer") else str(obj.state.get("panel", ""))
	if not panel.is_empty():
		world.power.recompute(panel)
	elif world.has_cap(obj, "generator"):
		# Running unconnected: idles at base burn rate.
		world.set_state(obj, "load_w", 0.0)
		world.power._reschedule_fuel(obj)


func _switch(obj, on: bool, ch: Array, data: Dictionary) -> String:
	if obj.state.get("switched_on", false) == on:
		return "already_on" if on else "already_off"
	world.set_state(obj, "switched_on", on, ch)
	_refresh_power(obj)
	data["powered"] = obj.state.get("powered", false)
	_sound(obj, 1.0, "switch_click")
	return ""


func _nearest_panel(p: Vector2, max_d: float) -> String:
	var best := ""
	var best_d := max_d
	for id in world.order:
		var o = world.objects[id]
		if world.has_cap(o, "breaker_panel") and o.center().distance_to(p) <= best_d:
			best_d = o.center().distance_to(p)
			best = id
	return best


func _connect(obj, params: Dictionary, ch: Array) -> String:
	if world.has_cap(obj, "generator"):
		if not str(obj.state.get("panel", "")).is_empty():
			return "already_connected"
		var reach := float(world.comp(obj, "generator").get("connect_range", 6.0))
		var panel_id := str(params.get("panel", _nearest_panel(obj.center(), reach)))
		var panel = world.objects.get(panel_id)
		if panel == null or not world.has_cap(panel, "breaker_panel"):
			return "no_panel_in_range"
		if panel.center().distance_to(obj.center()) > reach:
			return "panel_out_of_range"
		world.set_state(obj, "panel", panel_id, ch)
		world.power.recompute(panel_id)
		return ""
	if not str(obj.state.get("circuit", "")).is_empty():
		return "already_connected"
	var pid := str(params.get("panel", _nearest_panel(obj.center(), WIRING_RANGE)))
	var p = world.objects.get(pid)
	if p == null or not world.has_cap(p, "breaker_panel"):
		return "no_panel_in_range"
	if p.center().distance_to(obj.center()) > WIRING_RANGE:
		return "panel_out_of_range"
	var circuit := str(params.get("circuit", "general"))
	if not p.state.get("breakers", {}).has(circuit):
		return "unknown_circuit"
	world.set_state(obj, "circuit", pid + ":" + circuit, ch)
	world.power.mark_topology_dirty()
	world.power.recompute(pid)
	return ""


func _disconnect(obj, ch: Array) -> String:
	if world.has_cap(obj, "generator"):
		var panel_id: String = obj.state.get("panel", "")
		if panel_id.is_empty():
			return "not_connected"
		world.set_state(obj, "panel", "", ch)
		world.power.recompute(panel_id)
		_refresh_power(obj)
		return ""
	var pid: String = world.power.panel_id_of(obj)
	if pid.is_empty():
		return "not_connected"
	world.settle_all_dynamic()
	world.set_state(obj, "circuit", "", ch)
	world.power.mark_topology_dirty()
	world.power.recompute(pid)
	if obj.state.get("powered", false):
		world.set_state(obj, "powered", false, ch)
		world.emit({"type": "power_changed", "object_id": obj.instance_id, "powered": false})
	return ""


func _toggle_breaker(obj, params: Dictionary, ch: Array) -> String:
	var circuit := str(params.get("circuit", ""))
	var breakers: Dictionary = obj.state.get("breakers", {}).duplicate()
	if not breakers.has(circuit):
		return "unknown_circuit"
	breakers[circuit] = not breakers[circuit]
	world.set_state(obj, "breakers", breakers, ch)
	world.power.recompute(obj.instance_id)
	_sound(obj, 1.0, "breaker_clack")
	return ""


func _start_stop(obj, start: bool, ch: Array) -> String:
	if obj.state.get("running", false) == start:
		return "already_running" if start else "already_stopped"
	if start:
		if obj.state.get("broken", false) or world.power.is_faulted(obj):
			return "generator_damaged"
		if float(obj.state.get("fuel_l", 0.0)) <= 0.0:
			return "no_fuel"
	world.settle_all_dynamic()
	world.set_state(obj, "running", start, ch)
	_refresh_power(obj)
	if start and not obj.state.get("running", false):
		return ""  # tripped immediately on overload: action happened, event reports it
	_sound(obj, float(world.comp(obj, "generator").get("noise_radius", 20.0)) if start else 2.0, "generator_start" if start else "generator_stop")
	return ""


func _refuel(obj, actor: Dictionary, params: Dictionary, ch: Array, data: Dictionary) -> String:
	var cap := float(world.comp(obj, "generator")["fuel_capacity_l"])
	var fuel := float(obj.state.get("fuel_l", 0.0))
	var space := cap - fuel
	if space <= 0.001:
		return "tank_full"
	var source := str(params.get("source", "item"))
	var added := 0.0
	if source == "item":
		if space < FUEL_CAN_L:
			return "not_enough_space_for_can"
		if _qty(actor, FUEL_CAN) < 1:
			return "requires_fuel_can"
		if not _swap_items(actor, FUEL_CAN, FUEL_CAN_EMPTY):
			return "inventory_full"
		added = FUEL_CAN_L
	else:
		var drum = world.objects.get(source)
		if drum == null or not world.has_cap(drum, "fuel_storage"):
			return "invalid_fuel_source"
		if drum.closest_point(actor["pos"]).distance_to(actor["pos"]) > 2.0:
			return "fuel_source_out_of_range"
		var available := float(drum.state.get("fuel_l", 0.0))
		if available <= 0.0:
			return "fuel_source_empty"
		added = minf(space, available)
		world.set_state(drum, "fuel_l", available - added, ch)
	world.settle_all_dynamic()
	world.set_state(obj, "fuel_l", fuel + added, ch)
	data["added_l"] = added
	_refresh_power(obj)
	return ""


# ---------------------------------------------------------------- water

func _fill(obj, actor: Dictionary, params: Dictionary, ch: Array, data: Dictionary) -> String:
	var item_id := str(params.get("item_id", ""))
	if item_id.is_empty():
		for k in WaterModel.FILLABLE:
			if _qty(actor, k) > 0:
				item_id = k
				break
	if not WaterModel.FILLABLE.has(item_id):
		return "requires_empty_container"
	if _qty(actor, item_id) < 1:
		return "requires_empty_container"
	var spec: Array = WaterModel.FILLABLE[item_id]
	var litres := float(spec[2])
	var src: Dictionary = world.water.supply_of(obj)
	if not src["ok"]:
		return src["reason"]
	if float(src["litres"]) < litres:
		return "not_enough_water"
	var filled: String = spec[1] if src["contaminated"] else spec[0]
	if not _swap_items(actor, item_id, filled):
		return "inventory_full"
	world.water.draw(obj, litres, ch)
	data["filled_item"] = filled
	data["litres"] = litres
	world.emit({"type": "water_drawn", "object_id": obj.instance_id, "source_id": src["source_id"], "litres": litres, "contaminated": src["contaminated"]})
	return ""


func _drink(obj, actor: Dictionary, ch: Array, data: Dictionary) -> String:
	var spec: Dictionary = world.comp(obj, "water_fixture") if world.has_cap(obj, "water_fixture") else world.comp(obj, "water_storage")
	var litres := float(spec.get("drink_l", 0.25))
	if litres <= 0.0:
		return "not_drinkable"
	var src: Dictionary = world.water.supply_of(obj)
	if not src["ok"]:
		return src["reason"]
	world.water.draw(obj, litres, ch)
	data["litres"] = litres
	data["contaminated"] = src["contaminated"]
	# Worker 02 applies thirst/sickness from this event.
	world.emit({"type": "hydration", "actor_id": actor["id"], "litres": litres, "contaminated": src["contaminated"], "object_id": obj.instance_id})
	return ""


func _use(obj, ch: Array, data: Dictionary) -> String:
	var spec: Dictionary = world.comp(obj, "water_fixture")
	var verb: String = spec.get("use_verb", "use")
	data["verb"] = verb
	if spec.has("cistern_l"):
		var cistern := float(obj.state.get("cistern_l", 0.0))
		if cistern < float(spec["cistern_l"]) - 0.001:
			return "cistern_empty"
		var src: Dictionary = world.water.supply_of(obj)
		var refill := 0.0
		if src["ok"]:
			refill = minf(float(spec["cistern_l"]), float(src["litres"]))
			world.water.draw(obj, refill, ch)
		world.set_state(obj, "cistern_l", refill, ch)
		data["refilled_l"] = refill
		_sound(obj, 4.0, "toilet_flush")
		return ""
	var litres := float(spec.get("use_l", 0.0))
	var s: Dictionary = world.water.supply_of(obj)
	if not s["ok"]:
		return s["reason"]
	if float(s["litres"]) < litres:
		return "not_enough_water"
	world.water.draw(obj, litres, ch)
	data["litres"] = litres
	world.emit({"type": "water_used", "object_id": obj.instance_id, "verb": verb, "litres": litres})
	return ""


func _pour(obj, actor: Dictionary, params: Dictionary, ch: Array) -> String:
	var item_id := str(params.get("item_id", ""))
	if item_id.is_empty():
		for k in WaterModel.POURABLE:
			if _qty(actor, k) > 0:
				item_id = k
				break
	if not WaterModel.POURABLE.has(item_id) or _qty(actor, item_id) < 1:
		return "requires_water_container"
	var spec: Array = WaterModel.POURABLE[item_id]
	var cap := float(world.comp(obj, "water_storage")["capacity_l"])
	var level := float(obj.state.get("water_l", 0.0))
	if level + float(spec[1]) > cap + 0.001:
		return "tank_full"
	if not _swap_items(actor, item_id, spec[0]):
		return "inventory_full"
	world.set_state(obj, "water_l", level + float(spec[1]), ch)
	if spec[2] and not obj.state.get("contaminated", false):
		world.set_state(obj, "contaminated", true, ch)
	return ""


func _drain(obj, ch: Array) -> String:
	var level := float(obj.state.get("water_l", 0.0))
	if level <= 0.0:
		return "already_empty"
	world.set_state(obj, "water_l", 0.0, ch)
	world.emit({"type": "water_spilled", "object_id": obj.instance_id, "litres": level, "pos": obj.center()})
	return ""


func _treat(obj, actor: Dictionary, ch: Array) -> String:
	if not obj.state.get("contaminated", false):
		return "already_clean"
	if float(obj.state.get("water_l", 0.0)) <= 0.0:
		return "tank_empty"
	if _qty(actor, PURIFIER) < 1:
		return "requires_purification_tablets"
	if not actor["inventory"].remove(PURIFIER, 1):
		return "requires_purification_tablets"
	world.set_state(obj, "contaminated", false, ch)
	return ""
