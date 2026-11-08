extends SceneTree
## Worker 05 world-simulation regression suite. Deterministic fixtures, temp save paths.
## Run: godot --headless --path . --script tests/world_simulation/test_world_simulation.gd

const B := preload("res://game/world_simulation/world_bootstrap.gd")
const Inv := preload("res://game/world_interactions/actor_inventory_port.gd")
const WorldDefs := preload("res://game/world_simulation/world_defs.gd")

const L := "lab_house_01/"
var failures: Array = []
var passes := 0
var current := ""
var stacks: Array = []
var _req := 0


func _initialize() -> void:
	var tests := [
		"t00_definitions_valid", "t01_door_open_close_collision", "t02_lock_unlock_preconditions",
		"t03_broken_window_access", "t04_barricade_damage", "t05_container_init_once",
		"t06_transfer_no_duplication", "t07_container_save_reload", "t08_power_outage",
		"t09_generator_fuel", "t10_fridge_cooling_dependency", "t11_water_depletion",
		"t12_fixture_fill_drain", "t13_appliance_persistence", "t14_furniture_relocation",
		"t15_destroyed_cleanup", "t16_delta_serialization", "t17_repeated_input_idempotency",
		"t18_invalid_interactions", "t19_budget_and_scale", "t21_environment_effects",
		"t22_offline_bounded", "t23_save_rejects_bad_data",
	]
	for t in tests:
		current = t
		var before := failures.size()
		call(t)
		for s in stacks:
			B.dispose(s)
		stacks.clear()
		print(("PASS " if failures.size() == before else "FAIL ") + t)
	B.release_shared()
	print("WORLD_SIM_TESTS passed_checks=%d failed_checks=%d" % [passes, failures.size()])
	for f in failures:
		print("  FAILED: " + f)
	quit(0 if failures.is_empty() else 1)


# ---------------------------------------------------------------- helpers

func check(cond: bool, msg: String) -> void:
	if cond:
		passes += 1
	else:
		failures.append(current + ": " + msg)


func eq(a, b, msg: String) -> void:
	check(a == b, "%s (got %s, expected %s)" % [msg, str(a), str(b)])


func stack(seed_value: int = 1) -> Dictionary:
	var s := B.create(B.LAB_LAYOUT, seed_value)
	stacks.append(s)
	return s


func actor(s: Dictionary, p: Vector2, items: Dictionary = {}, cap: float = 60.0) -> Dictionary:
	var inv = Inv.new(s.defs, cap)
	for k in items:
		inv.inventory[k] = items[k]
	return {"id": "player", "pos": p, "inventory": inv}


func act(s: Dictionary, a: Dictionary, target: String, action: String, params: Dictionary = {}) -> Dictionary:
	_req += 1
	var r: Dictionary = s.interactions.request({"request_id": "r%d" % _req, "actor": a, "target_id": L + target, "action_id": action, "params": params})
	s.world.advance(0.5)  # step past the per-input debounce window
	return r


func ok(r: Dictionary, msg: String) -> void:
	check(r.ok, msg + " -> " + str(r.failure_reason))


func fails(r: Dictionary, reason: String, msg: String) -> void:
	check(not r.ok and r.failure_reason == reason, "%s (got ok=%s reason=%s, expected %s)" % [msg, str(r.ok), r.failure_reason, reason])


func obj(s: Dictionary, id: String):
	return s.world.objects.get(L + id)


func tmp_path(name: String) -> String:
	return "user://world_sim_test_%s.json" % name


func save_and_reload(s: Dictionary, name: String) -> Dictionary:
	var path := tmp_path(name)
	eq(s.saver.save(s.world, path), OK, "save writes " + path)
	var s2 := stack(s.world.world_seed)
	var err: String = s2.saver.apply(s2.world, s2.saver.read(path))
	eq(err, "", "save applies")
	DirAccess.remove_absolute(ProjectSettings.globalize_path(path))
	DirAccess.remove_absolute(ProjectSettings.globalize_path(path + ".bak"))
	return s2


func events_of(r: Dictionary, type: String) -> Array:
	return r.events.filter(func(e): return e.get("type") == type)


# ---------------------------------------------------------------- tests

func t00_definitions_valid() -> void:
	var d = B.shared_defs()
	eq(d.errors.size(), 0, "shipped definitions validate: " + "; ".join(d.errors))
	check(d.definitions.size() >= 25, "at least 25 archetypes")
	# Negative: a definition exposing an unimplemented / capability-less action is rejected.
	var bad = WorldDefs.new()
	bad.item_weights = d.item_weights
	bad.loot_profiles = d.loot_profiles
	bad.definitions = {"x": {"definition_id": "x", "footprint": {"kind": "cells", "size": [1, 1]}, "capabilities": ["movable"], "components": {"movable": {}}, "actions": ["open", "teleport"]}}
	bad.validate()
	check(bad.errors.size() == 2, "invalid actions reported: " + str(bad.errors))


func t01_door_open_close_collision() -> void:
	var s := stack()
	var w = s.world
	var door = obj(s, "door.kitchen")
	var p := Vector2(2.5, 4.0)
	check(w.collision.point_blocked(p, 0.18), "closed door blocks the doorway")
	check(w.collision.segment_blocked_for_sight(Vector2(2.5, 3.0), Vector2(2.5, 5.0)), "closed door blocks sight")
	var nav0: int = w.nav_revision
	var a := actor(s, Vector2(2.5, 4.8))
	var r := act(s, a, "door.kitchen", "open")
	ok(r, "open door")
	check(door.state.open, "door state open")
	check(not w.collision.point_blocked(p, 0.18), "open door is not solid")
	check(not w.collision.segment_blocked_for_sight(Vector2(2.5, 3.0), Vector2(2.5, 5.0)), "open door passes sight")
	check(w.nav_revision > nav0, "navigation revision bumped")
	check(events_of(r, "navigation_changed").size() == 1, "navigation_changed event emitted")
	check(events_of(r, "sound").size() == 1, "door sound event emitted")
	eq(r.animation.get("clip"), "interact_open", "animation event")
	check(r.save_delta_ids.has(L + "door.kitchen"), "save delta lists the door")
	# Can't close while standing in the doorway.
	var in_door := actor(s, Vector2(2.5, 4.05))
	fails(act(s, in_door, "door.kitchen", "close"), "doorway_blocked", "close blocked by actor in doorway")
	ok(act(s, a, "door.kitchen", "close"), "close door")
	check(w.collision.point_blocked(p, 0.18), "closed again blocks")


func t02_lock_unlock_preconditions() -> void:
	var s := stack()
	var outside := actor(s, Vector2(5.0, 8.7))
	fails(act(s, outside, "door.front", "open"), "locked", "locked door won't open")
	fails(act(s, outside, "door.front", "unlock"), "requires_key", "outside unlock needs key")
	var with_key := actor(s, Vector2(5.0, 8.7), {"ll_world_key_lab_front": 1})
	ok(act(s, with_key, "door.front", "unlock"), "unlock with key")
	ok(act(s, with_key, "door.front", "open"), "open after unlock")
	fails(act(s, with_key, "door.front", "lock"), "must_close_first", "cannot lock open door")
	ok(act(s, with_key, "door.front", "close"), "close")
	var inside := actor(s, Vector2(5.0, 7.4))
	ok(act(s, inside, "door.front", "lock"), "inside thumb-turn locks without key")
	fails(act(s, inside, "door.front", "lock"), "already_locked", "double lock rejected")
	ok(act(s, inside, "door.front", "unlock"), "inside unlock without key")
	# Locker has no thumb-turn: key required from any side.
	var at_locker := actor(s, Vector2(9.0, 7.0))
	fails(act(s, at_locker, "living.locker", "unlock"), "requires_key", "locker needs key")
	# A damaged lock can no longer be locked.
	var door = obj(s, "door.front")
	s.world.conditions.apply_damage(door.instance_id, 40.0, "test")
	fails(act(s, inside, "door.front", "lock"), "lock_damaged", "damaged lock fails")


func t03_broken_window_access() -> void:
	var s := stack()
	var w = s.world
	var win = obj(s, "window.west")
	var p := Vector2(0.0, 6.0)
	check(w.collision.point_blocked(p, 0.18), "intact closed window blocks movement")
	check(not w.collision.segment_blocked_for_sight(Vector2(-1, 6), Vector2(1, 6)), "glass is transparent")
	var a := actor(s, Vector2(-0.8, 6.0))
	var r := act(s, a, "window.west", "smash")
	ok(r, "smash window")
	check(win.state.broken, "window broken")
	check(not w.collision.point_blocked(p, 0.18), "broken window is passable")
	var loud := events_of(r, "sound").filter(func(e): return e.cue == "glass_break")
	check(loud.size() == 1 and loud[0].radius >= 14.0, "glass break is loud")
	fails(act(s, a, "window.west", "open"), "broken", "broken window cannot be opened")
	eq(w.collision.sight_block(win), 0.0, "broken window sight")


func t04_barricade_damage() -> void:
	var s := stack()
	var w = s.world
	var door = obj(s, "door.kitchen")
	var bare := actor(s, Vector2(2.5, 4.6))
	fails(act(s, bare, "door.kitchen", "barricade"), "requires_hammer", "barricade needs hammer")
	var a := actor(s, Vector2(2.5, 4.6), {"ll_tools_claw_hammer": 1, "ll_crafting_pine_plank": 2, "ll_crafting_nail_box": 2})
	var r := act(s, a, "door.kitchen", "barricade")
	ok(r, "barricade layer 1")
	ok(act(s, a, "door.kitchen", "barricade"), "barricade layer 2")
	eq(a.inventory.quantity("ll_crafting_pine_plank"), 0, "planks consumed")
	fails(act(s, a, "door.kitchen", "barricade"), "requires_plank_and_nails", "no more planks")
	fails(act(s, a, "door.kitchen", "open"), "barricaded", "barricaded door won't open")
	# Damage: barricade absorbs first.
	var hp0: float = door.state.hp
	w.conditions.apply_damage(door.instance_id, 30.0, "zombie")
	eq(door.state.barricade.size(), 1, "one layer destroyed")
	eq(door.state.hp, hp0, "door hp untouched while barricaded")
	check(w.collision.point_blocked(Vector2(2.5, 4.0), 0.18), "still blocks with one layer")
	var other_side := actor(s, Vector2(2.5, 3.4), {"ll_tools_claw_hammer": 1})
	fails(act(s, other_side, "door.kitchen", "unbarricade"), "wrong_side", "unbarricade from wrong side")
	ok(act(s, a, "door.kitchen", "unbarricade"), "unbarricade from build side")
	eq(a.inventory.quantity("ll_crafting_pine_plank"), 1, "plank recovered")
	# Break the door: breach makes it passable and unlockable.
	var res: Dictionary = w.conditions.apply_damage(door.instance_id, 100.0, "zombie")
	check(res.broken_now, "door broke")
	check(door.state.broken and door.state.open, "broken door is open")
	check(not w.collision.point_blocked(Vector2(2.5, 4.0), 0.18), "breached doorway passable")
	fails(act(s, a, "door.kitchen", "close"), "broken", "broken door cannot close")
	check(w.event_log.any(func(e): return e.type == "breach"), "breach event for Worker 03")


func t05_container_init_once() -> void:
	var s := stack(7)
	var cab = obj(s, "kitchen.cabinet")
	var a := actor(s, Vector2(1.7, 1.3))
	fails(act(s, a, "kitchen.cabinet", "search"), "container_closed", "closed cabinet can't be searched")
	check(not cab.state.loot_initialized, "no loot before access")
	ok(act(s, a, "kitchen.cabinet", "open"), "open cabinet")
	check(cab.state.loot_initialized, "loot rolled on first open")
	var first: Dictionary = cab.state.contents.duplicate(true)
	var r := act(s, a, "kitchen.cabinet", "search")
	ok(r, "search")
	check(not r.data.rolled_now, "search does not reroll")
	eq(cab.state.contents, first, "contents unchanged by search")
	check(s.world.storage.ensure_initialized(cab) == false, "explicit init is a no-op")
	var s2 := stack(7)
	var cab2 = obj(s2, "kitchen.cabinet")
	s2.world.storage.ensure_initialized(cab2)
	eq(cab2.state.contents, first, "same seed -> identical loot")
	check(s.world.storage.total_items(cab) >= 1, "cabinet profile produced items")


func _total(s: Dictionary, o, a: Dictionary, item: String) -> int:
	var n: int = a.inventory.quantity(item)
	for c in s.world.storage.compartments(o):
		n += s.world.storage.count(o, c.id, item)
	return n


func t06_transfer_no_duplication() -> void:
	var s := stack(7)
	var cab = obj(s, "kitchen.cabinet")
	var a := actor(s, Vector2(1.7, 1.3))
	act(s, a, "kitchen.cabinet", "open")
	cab.state.contents = {"upper": {"ll_food_bean_tin": 3}, "lower": {}}
	var before := _total(s, cab, a, "ll_food_bean_tin")
	var r := act(s, a, "kitchen.cabinet", "take", {"item_id": "ll_food_bean_tin", "count": 2})
	ok(r, "take 2")
	eq(_total(s, cab, a, "ll_food_bean_tin"), before, "total conserved after take")
	eq(a.inventory.quantity("ll_food_bean_tin"), 2, "inventory has 2")
	fails(act(s, a, "kitchen.cabinet", "take", {"item_id": "ll_food_bean_tin", "count": 2}), "item_not_in_container", "cannot take more than present")
	ok(act(s, a, "kitchen.cabinet", "put", {"item_id": "ll_food_bean_tin", "count": 2, "compartment": "lower"}), "put back")
	eq(_total(s, cab, a, "ll_food_bean_tin"), before, "total conserved after put")
	fails(act(s, a, "kitchen.cabinet", "put", {"item_id": "ll_food_bean_tin", "count": 1}), "not_in_inventory", "cannot put what you lack")
	# Inventory full: container unchanged.
	var tiny := actor(s, Vector2(1.7, 1.3), {}, 0.1)
	var snap: Dictionary = cab.state.contents.duplicate(true)
	fails(act(s, tiny, "kitchen.cabinet", "take", {"item_id": "ll_food_bean_tin"}), "inventory_full", "full inventory rejects")
	eq(cab.state.contents, snap, "container untouched on failed take")
	# Container capacity: upper holds 12 kg.
	var heavy := actor(s, Vector2(1.7, 1.3), {"ll_household_fuel_can": 2})
	fails(act(s, heavy, "kitchen.cabinet", "put", {"item_id": "ll_household_fuel_can", "count": 2, "compartment": "upper"}), "container_full", "weight cap enforced")
	eq(heavy.inventory.quantity("ll_household_fuel_can"), 2, "rejected put leaves inventory intact")


func t07_container_save_reload() -> void:
	var s := stack(11)
	var a := actor(s, Vector2(1.7, 1.3))
	act(s, a, "kitchen.cabinet", "open")
	var cab = obj(s, "kitchen.cabinet")
	cab.state.contents = {"upper": {"ll_food_bean_tin": 2, "ll_world_bottle_empty": 1}, "lower": {}}
	ok(act(s, a, "kitchen.cabinet", "take", {"item_id": "ll_world_bottle_empty"}), "take bottle")
	var s2 := save_and_reload(s, "container")
	var cab2 = obj(s2, "kitchen.cabinet")
	check(cab2.state.loot_initialized, "loot flag persisted")
	eq(s2.world.storage.count(cab2, "upper", "ll_food_bean_tin"), 2, "beans persisted")
	eq(s2.world.storage.count(cab2, "upper", "ll_world_bottle_empty"), 0, "taken bottle not restored")
	check(cab2.state.open, "open state persisted")
	var r := act(s2, actor(s2, Vector2(1.7, 1.3)), "kitchen.cabinet", "search")
	check(r.ok and not r.data.rolled_now, "no reroll after reload")


func t08_power_outage() -> void:
	var s := stack()
	var w = s.world
	w.set_global("grid_power", true)
	var fridge = obj(s, "kitchen.fridge")
	var light = obj(s, "kitchen.light")
	check(fridge.state.powered, "fridge powered from grid")
	check(not light.state.powered, "light off until switched")
	var a := actor(s, Vector2(2.5, 2.4))
	var r := act(s, a, "kitchen.light", "switch_on")
	ok(r, "switch light on")
	check(light.state.powered and r.data.powered, "light lit")
	var pa := actor(s, Vector2(9.7, 4.9))
	ok(act(s, pa, "living.panel", "toggle_breaker", {"circuit": "kitchen"}), "kitchen breaker off")
	check(not fridge.state.powered, "breaker off cuts fridge")
	check(light.state.powered, "other circuit unaffected")
	ok(act(s, pa, "living.panel", "toggle_breaker", {"circuit": "kitchen"}), "breaker back on")
	check(fridge.state.powered, "fridge back")
	w.set_global("grid_power", false)
	check(not fridge.state.powered and not light.state.powered, "grid outage kills everything")
	check(w.event_log.any(func(e): return e.type == "power_changed" and e.object_id == fridge.instance_id and not e.powered), "power_changed event")


func t09_generator_fuel() -> void:
	var s := stack()
	var w = s.world
	var gen = obj(s, "yard.generator")
	var fridge = obj(s, "kitchen.fridge")
	var a := actor(s, Vector2(11.8, 6.9), {"ll_household_fuel_can": 1})
	fails(act(s, a, "yard.generator", "start"), "no_fuel", "no fuel no start")
	var r := act(s, a, "yard.generator", "refuel")
	ok(r, "refuel from can")
	eq(gen.state.fuel_l, 10.0, "10 L added")
	eq(a.inventory.quantity("ll_world_fuel_can_empty"), 1, "empty can returned")
	ok(act(s, a, "yard.generator", "refuel", {"source": L + "yard.fuel_drum"}), "top up from drum")
	eq(gen.state.fuel_l, 20.0, "tank full")
	eq(obj(s, "yard.fuel_drum").state.fuel_l, 30.0, "drum drawn")
	ok(act(s, a, "yard.generator", "connect"), "connect to panel")
	ok(act(s, a, "yard.generator", "start"), "start")
	check(fridge.state.powered, "generator powers fridge")
	eq(gen.state.load_w, 150.0, "load = fridge demand")
	var t0: float = w.time_s
	w.advance(3600.0)
	w.settle(gen)
	var expected: float = 20.0 - (0.4 + 0.35 * 0.15) * (w.time_s - t0) / 3600.0
	check(absf(gen.state.fuel_l - expected) < 0.01, "fuel burn %.3f ~ %.3f" % [gen.state.fuel_l, expected])
	var q: Array = w.queued_events()
	check(q.size() == 1 and q[0].kind == "fuel_out", "fuel-out scheduled")
	var due: float = q[0].t
	w.advance(due - w.time_s + 1.0)
	check(not gen.state.running, "generator stopped at empty")
	eq(gen.state.fuel_l, 0.0, "tank empty")
	check(not fridge.state.powered, "fridge lost power")
	var out = w.event_log.filter(func(e): return e.type == "generator_fuel_out")
	check(out.size() == 1 and absf(out[0].t - due) < 0.001, "fuel_out fired exactly at scheduled time")
	# Overload trips the generator.
	var s2 := stack()
	var g2 = obj(s2, "yard.generator")
	g2.state.fuel_l = 20.0
	var a2 := actor(s2, Vector2(11.8, 6.9))
	act(s2, a2, "yard.generator", "connect")
	act(s2, a2, "yard.generator", "start")
	act(s2, actor(s2, Vector2(3.9, 1.3)), "kitchen.stove", "switch_on")
	check(g2.state.running, "fridge+stove (2150 W) within 3 kW")
	act(s2, actor(s2, Vector2(3.8, 5.3)), "living.heater", "switch_on")
	check(not g2.state.running, "3650 W trips the 3 kW generator")
	check(s2.world.event_log.any(func(e): return e.type == "generator_overload"), "overload event")


func t10_fridge_cooling_dependency() -> void:
	var s := stack()
	var w = s.world
	var fridge = obj(s, "kitchen.fridge")
	w.advance(3 * 3600.0)
	check(absf(w.thermal.temperature(fridge, "fridge") - 21.0) < 0.01, "unpowered fridge stays at ambient")
	eq(w.thermal.preservation_factor(fridge, "fridge"), 1.0, "no preservation without power")
	w.set_global("grid_power", true)
	w.advance(4 * 3600.0)
	var tf: float = w.thermal.temperature(fridge, "fridge")
	var tz: float = w.thermal.temperature(fridge, "freezer")
	check(tf < 4.0, "powered fridge cools (%.2f C)" % tf)
	check(tz < -15.0, "freezer freezes (%.2f C)" % tz)
	eq(w.thermal.preservation_factor(fridge, "fridge"), 0.25, "chilled preservation")
	eq(w.thermal.preservation_factor(fridge, "freezer"), 0.0, "frozen preservation")
	# Door left open warms the fridge even when powered.
	var a := actor(s, Vector2(0.6, 1.3))
	act(s, a, "kitchen.fridge", "open")
	w.advance(3600.0)
	check(w.thermal.temperature(fridge, "fridge") > 8.0, "open door warms fridge")
	act(s, a, "kitchen.fridge", "close")
	w.advance(4 * 3600.0)
	check(w.thermal.temperature(fridge, "fridge") < 4.0, "recovers once closed")
	w.set_global("grid_power", false)
	w.advance(12 * 3600.0)
	var warm: float = w.thermal.temperature(fridge, "fridge")
	check(warm > 5.0 and warm < 21.0, "outage: insulated fridge warms gradually (%.2f C)" % warm)
	eq(w.thermal.preservation_factor(fridge, "fridge"), 1.0, "preservation lost after outage")
	# Determinism: the same schedule in one big step gives the same answer.
	var s2 := stack()
	s2.world.set_global("grid_power", true)
	s2.world.advance(3600.0)
	var x: float = s2.world.thermal.temperature(obj(s2, "kitchen.fridge"), "fridge")
	var s3 := stack()
	s3.world.set_global("grid_power", true)
	for i in 60:
		s3.world.advance(60.0)
	check(absf(s3.world.thermal.temperature(obj(s3, "kitchen.fridge"), "fridge") - x) < 0.001, "step size independent")


func t11_water_depletion() -> void:
	var s := stack()
	var w = s.world
	var barrel = obj(s, "yard.rain_barrel")
	var a := actor(s, Vector2(11.5, 4.3), {"ll_household_bucket": 1}, 80.0)
	var filled := 0
	for i in 8:
		var r := act(s, a, "yard.rain_barrel", "fill")
		if not r.ok:
			fails(r, "tank_empty", "barrel exhausts")
			break
		filled += 1
		eq(r.data.filled_item, "ll_world_bucket_water_tainted", "untreated barrel water is tainted")
		a.inventory.remove("ll_world_bucket_water_tainted", 1)
		a.inventory.add("ll_household_bucket", 1)
	eq(filled, 6, "60 L barrel fills six 10 L buckets")
	eq(barrel.state.water_l, 0.0, "barrel empty")
	fails(act(s, a, "yard.rain_barrel", "drink"), "tank_empty", "nothing left to drink")
	# Mains shut-off.
	var sink_actor := actor(s, Vector2(2.9, 1.3), {"ll_world_bottle_empty": 1})
	w.set_global("water_mains", false)
	fails(act(s, sink_actor, "kitchen.sink", "fill"), "water_shut_off", "no mains no water")
	# Rain refills an outdoor barrel deterministically.
	w.set_global("raining", true)
	w.advance(5 * 3600.0)
	w.settle(barrel)
	check(absf(barrel.state.water_l - 10.0) < 0.01, "5 h rain at 2 L/h -> 10 L (%.2f)" % barrel.state.water_l)


func t12_fixture_fill_drain() -> void:
	var s := stack()
	var w = s.world
	var a := actor(s, Vector2(2.9, 1.3), {"ll_world_bottle_empty": 1, "ll_world_bucket_water": 1, "ll_world_purification_tablets": 1}, 80.0)
	var r := act(s, a, "kitchen.sink", "fill")
	ok(r, "fill bottle at sink")
	eq(a.inventory.quantity("ll_food_water_bottle"), 1, "clean water bottle")
	eq(a.inventory.quantity("ll_world_bottle_empty"), 0, "empty bottle consumed")
	var d := act(s, a, "kitchen.sink", "drink")
	ok(d, "drink from tap")
	var h := events_of(d, "hydration")
	check(h.size() == 1 and not h[0].contaminated and h[0].litres == 0.25, "hydration event for Worker 02")
	# Toilet: flush uses cistern, refills from mains; with mains off only one flush.
	var t := actor(s, Vector2(9.4, 1.3))
	ok(act(s, t, "bathroom.toilet", "use"), "flush 1")
	w.set_global("water_mains", false)
	ok(act(s, t, "bathroom.toilet", "use"), "flush 2 empties cistern")
	fails(act(s, t, "bathroom.toilet", "use"), "cistern_empty", "no refill without mains")
	# Barrel: pour, treat, drain.
	var barrel = obj(s, "yard.rain_barrel")
	var b := a.duplicate()
	b.pos = Vector2(11.5, 4.3)
	ok(act(s, b, "yard.rain_barrel", "pour"), "pour bucket into barrel")
	eq(barrel.state.water_l, 70.0, "barrel +10 L")
	ok(act(s, b, "yard.rain_barrel", "treat"), "treat barrel")
	check(not barrel.state.contaminated, "treated water clean")
	eq(b.inventory.quantity("ll_world_purification_tablets"), 0, "tablet consumed")
	fails(act(s, b, "yard.rain_barrel", "treat"), "already_clean", "no double treat")
	var dr := act(s, b, "yard.rain_barrel", "drain")
	ok(dr, "drain barrel")
	eq(barrel.state.water_l, 0.0, "drained")
	check(events_of(dr, "water_spilled").size() == 1, "spill event")
	fails(act(s, b, "yard.rain_barrel", "drain"), "already_empty", "drain empty rejected")


func t13_appliance_persistence() -> void:
	var s := stack()
	var w = s.world
	var gen = obj(s, "yard.generator")
	gen.state.fuel_l = 15.0
	var a := actor(s, Vector2(11.8, 6.9))
	act(s, a, "yard.generator", "connect")
	act(s, a, "yard.generator", "start")
	act(s, actor(s, Vector2(3.9, 1.3)), "kitchen.stove", "switch_on")
	w.advance(1800.0)
	var fridge = obj(s, "kitchen.fridge")
	var t_before: float = w.thermal.temperature(fridge, "fridge")
	w.settle(gen)
	var fuel_before: float = gen.state.fuel_l
	var due_before: float = w.queued_events()[0].t
	var s2 := save_and_reload(s, "appliance")
	var w2 = s2.world
	var gen2 = obj(s2, "yard.generator")
	check(gen2.state.running, "generator still running")
	check(absf(gen2.state.fuel_l - fuel_before) < 0.0001, "fuel persisted")
	check(obj(s2, "kitchen.stove").state.switched_on and obj(s2, "kitchen.stove").state.powered, "stove on and powered")
	check(absf(w2.thermal.temperature(obj(s2, "kitchen.fridge"), "fridge") - t_before) < 0.001, "fridge temperature persisted")
	var q: Array = w2.queued_events()
	check(q.size() == 1 and absf(q[0].t - due_before) < 0.01, "fuel-out reschedules identically")
	eq(w2.time_s, w.time_s, "world clock persisted")


func t14_furniture_relocation() -> void:
	var s := stack()
	var w = s.world
	var chair = obj(s, "living.chair")
	var a := actor(s, Vector2(3.6, 7.5))
	var old_p: Vector2 = chair.rect().get_center()
	check(w.collision.point_blocked(old_p, 0.1), "chair blocks its footprint")
	var nav0: int = w.nav_revision
	ok(act(s, a, "living.chair", "move", {"to": Vector2(4.4, 6.6)}), "move chair")
	check(not w.collision.point_blocked(old_p, 0.1), "old footprint freed")
	check(w.collision.point_blocked(chair.rect().get_center(), 0.1), "new footprint blocks")
	check(w.nav_revision > nav0, "nav updated")
	fails(act(s, a, "living.chair", "move", {"to": Vector2(4.4, 3.8)}), "placement_blocked", "cannot move into a wall")
	fails(act(s, a, "living.chair", "move", {"to": Vector2(9.6, 6.6)}), "too_far", "max step enforced")
	var near_sofa := actor(s, Vector2(3.9, 7.6))
	ok(act(s, near_sofa, "living.chair", "move", {"to": Vector2(3.0, 6.6)}), "move chair next to sofa")
	fails(act(s, near_sofa, "living.chair", "move", {"to": Vector2(2.2, 6.9)}), "placement_blocked", "cannot overlap sofa")
	fails(act(s, actor(s, Vector2(3.4, 6.2)), "living.chair", "move", {"to": Vector2(3.2, 6.0)}), "placement_occupied", "cannot drop on the actor")
	var weak := actor(s, Vector2(7.8, 5.2))
	weak["strength_kg"] = 30.0
	fails(act(s, weak, "living.wardrobe", "move", {"to": Vector2(7.6, 4.6)}), "too_heavy", "wardrobe too heavy")
	var fa := actor(s, Vector2(0.6, 1.3))
	fails(act(s, fa, "kitchen.fridge", "move", {"to": Vector2(0.25, 0.6)}), "disconnect_first", "fridge wired in")
	var s2 := save_and_reload(s, "furniture")
	var chair2 = obj(s2, "living.chair")
	eq(chair2.pos, chair.pos, "relocation persisted")
	check(s2.world.collision.point_blocked(chair2.rect().get_center(), 0.1), "collision rebuilt after load")
	check(not s2.world.collision.point_blocked(old_p, 0.1), "original spot free after load")


func t15_destroyed_cleanup() -> void:
	var s := stack(3)
	var w = s.world
	var crate = obj(s, "yard.crate")
	var center: Vector2 = crate.rect().get_center()
	w.storage.ensure_initialized(crate)
	crate.state.contents = {"main": {"ll_crafting_pine_plank": 2}}
	var res: Dictionary = w.conditions.apply_damage(crate.instance_id, 999.0, "test")
	check(res.broken_now, "crate destroyed")
	check(obj(s, "yard.crate") == null, "crate removed from world")
	check(w.query_rect(Rect2(center, Vector2.ZERO).grow(0.3)).filter(func(i): return i == L + "yard.crate").is_empty(), "removed from spatial index")
	check(not w.collision.point_blocked(center + Vector2(0.3, 0.3), 0.05), "footprint no longer solid")
	var pile = obj(s, "yard.crate~spill")
	check(pile != null, "spill pile spawned")
	eq(w.storage.count(pile, "ground", "ll_crafting_pine_plank"), 2, "contents spilled once")
	check(w.conditions.apply_damage(L + "yard.crate", 10.0).ok == false, "destroyed object cannot be damaged again")
	var s2 := save_and_reload(s, "destroyed")
	check(obj(s2, "yard.crate") == null, "destroyed crate stays gone")
	var pile2 = obj(s2, "yard.crate~spill")
	check(pile2 != null and s2.world.storage.count(pile2, "ground", "ll_crafting_pine_plank") == 2, "pile persisted without duplication")
	var a := actor(s2, pile2.rect().get_center() + Vector2(0.6, 0))
	ok(act(s2, a, "yard.crate~spill", "take", {"item_id": "ll_crafting_pine_plank", "count": 2}), "pick up spill")
	check(obj(s2, "yard.crate~spill") == null, "empty pile cleaned up")
	var s3 := save_and_reload(s2, "destroyed2")
	check(obj(s3, "yard.crate~spill") == null and obj(s3, "yard.crate") == null, "nothing reappears")


func t16_delta_serialization() -> void:
	var s := stack()
	var w = s.world
	var d0: Dictionary = s.saver.build(w)
	eq(d0.objects.size(), 0, "untouched world has an empty delta")
	eq(d0.removed.size(), 0, "nothing removed")
	act(s, actor(s, Vector2(2.5, 4.8)), "door.kitchen", "open")
	var d1: Dictionary = s.saver.build(w)
	eq(d1.objects.keys(), [L + "door.kitchen"], "only the changed door is saved")
	eq(s.saver.last_reserialized, 1, "one record serialized")
	var d2: Dictionary = s.saver.build(w)
	eq(s.saver.last_reserialized, 0, "no dirty objects -> nothing re-serialized")
	eq(d2.objects.size(), 1, "record kept in delta")
	eq(d1.schema, "last-light.world-delta", "schema tag")
	eq(d1.version, 1, "version")
	var json := JSON.stringify(d1)
	check(json.length() < 2000, "compact delta (%d bytes)" % json.length())


func t17_repeated_input_idempotency() -> void:
	var s := stack()
	var door = obj(s, "door.kitchen")
	var a := actor(s, Vector2(2.5, 4.8))
	var req := {"request_id": "touch-42", "actor": a, "target_id": L + "door.kitchen", "action_id": "open"}
	var r1: Dictionary = s.interactions.request(req)
	var rev: int = door.revision
	var r2: Dictionary = s.interactions.request(req)
	ok(r1, "first touch")
	check(r2.ok and r2.duplicate, "same request id returns cached result")
	eq(r2.state_changes.size(), 0, "duplicate reports no new changes")
	eq(door.revision, rev, "no second mutation")
	# Touch + emulated mouse in the same frame: distinct ids, same verb -> debounced.
	var r3: Dictionary = s.interactions.request({"request_id": "touch-43", "actor": a, "target_id": L + "door.kitchen", "action_id": "close"})
	var r4: Dictionary = s.interactions.request({"request_id": "mouse-43", "actor": a, "target_id": L + "door.kitchen", "action_id": "close"})
	ok(r3, "close")
	check(r4.duplicate and r4.failure_reason == "duplicate_input", "second close in same frame debounced")
	var r5: Dictionary = s.interactions.request({"request_id": "touch-44", "actor": a, "target_id": L + "door.kitchen", "action_id": "open"})
	var r6: Dictionary = s.interactions.request({"request_id": "mouse-44", "actor": a, "target_id": L + "door.kitchen", "action_id": "open"})
	fails(r5, "duplicate_input", "re-open within debounce window rejected")
	check(r6.duplicate or r6.failure_reason == "duplicate_input", "ghost input rejected")
	s.world.advance(0.3)
	ok(s.interactions.request({"request_id": "touch-45", "actor": a, "target_id": L + "door.kitchen", "action_id": "open"}), "after window: allowed")


func t18_invalid_interactions() -> void:
	var s := stack()
	var w = s.world
	var a := actor(s, Vector2(2.5, 4.8))
	w.dirty.clear()
	fails(act(s, a, "door.kitchen", "teleport"), "unknown_action", "unknown action")
	fails(act(s, a, "door.kitchen", "switch_on"), "action_not_supported", "door has no switch")
	fails(act(s, a, "kitchen.fridge", "open"), "out_of_range", "fridge too far")
	fails(act(s, a, "no.such.object", "open"), "target_missing", "missing target")
	fails(s.interactions.request({"actor": {"id": "", "pos": 3}, "target_id": L + "door.kitchen", "action_id": "open"}), "invalid_actor", "bad actor")
	var g := actor(s, Vector2(11.8, 6.9))
	fails(act(s, g, "yard.generator", "start"), "no_fuel", "start without fuel")
	var pa := actor(s, Vector2(9.7, 4.9))
	fails(act(s, pa, "living.panel", "toggle_breaker", {"circuit": "nope"}), "unknown_circuit", "unknown circuit")
	var ta := actor(s, Vector2(8.6, 7.9))
	fails(act(s, ta, "living.toolbox", "take"), "container_closed", "closed toolbox")
	eq(w.dirty.size(), 0, "rejected actions changed nothing")
	eq(s.interactions.supported_actions(L + "door.kitchen").has("switch_on"), false, "only supported actions exposed")


func t19_budget_and_scale() -> void:
	# Event budget: 100 generators all running out at different times inside one frame.
	var layout := {"layout_id": "bench", "bounds": [0, 0, 200, 200], "objects": []}
	for i in 100:
		layout.objects.append({"id": "gen%d" % i, "def": "ll.machine.generator_portable", "pos": [i % 10 * 2.0, int(i / 10) * 2.0], "state": {"fuel_l": 0.01 + i * 0.0001, "running": true}})
	var s := B.create(layout, 1)
	stacks.append(s)
	var w = s.world
	for id in w.order:
		w.power._reschedule_fuel(w.objects[id])
	eq(w.queued_events().size(), 100, "100 fuel events queued")
	var r: Dictionary = w.advance(3600.0, 8)
	eq(r.processed, 8, "budget caps events per call")
	check(r.deferred_s > 0.0, "remaining time deferred, not skipped")
	var frames := 1
	while not w.queued_events().is_empty() and frames < 50:
		w.advance(0.0, 8)
		frames += 1
	eq(frames, 13, "all events drained across frames")
	check(absf(w.time_s - 3600.0) < 0.001, "clock catches up exactly")
	var stopped := 0
	for id in w.order:
		if not w.objects[id].state.running:
			stopped += 1
	eq(stopped, 100, "every generator stopped")
	# Spatial query cost is local: 5000 objects, query touches only nearby chunks.
	var big := {"layout_id": "big", "bounds": [0, 0, 400, 400], "objects": []}
	for i in 5000:
		big.objects.append({"id": "c%d" % i, "def": "ll.container.wooden_crate", "pos": [(i % 100) * 3.5 + 0.5, int(i / 100) * 3.5 + 0.5]})
	var sb := B.create(big, 1)
	stacks.append(sb)
	var hits: Array = sb.world.query_rect(Rect2(10, 10, 3, 3))
	check(hits.size() <= 4, "local query returns few objects (%d)" % hits.size())
	var t0 := Time.get_ticks_usec()
	for i in 1000:
		sb.world.advance(1.0 / 60.0)
	var per_frame_us := float(Time.get_ticks_usec() - t0) / 1000.0
	check(per_frame_us < 200.0, "idle advance per frame %.1f us with 5000 objects" % per_frame_us)


func t21_environment_effects() -> void:
	var s := stack()
	var w = s.world
	w.set_global("grid_power", true)
	var fridge = obj(s, "kitchen.fridge")
	check(fridge.state.powered, "powered before flood")
	w.conditions.apply_environment(fridge.instance_id, "flooded")
	check(not fridge.state.powered, "flooded appliance faults")
	var a := actor(s, Vector2(0.6, 1.3), {"ll_tools_adjustable_wrench": 1})
	ok(act(s, a, "kitchen.fridge", "repair"), "service flooded fridge")
	check(fridge.state.powered, "repaired fridge powered again")
	var sofa = obj(s, "living.sofa")
	w.storage.ensure_initialized(sofa)
	w.conditions.apply_environment(sofa.instance_id, "burned")
	check(obj(s, "living.sofa") == null, "burned sofa destroyed")
	var barrel = obj(s, "yard.rain_barrel")
	barrel.state.contaminated = false
	w.conditions.apply_environment(barrel.instance_id, "contaminated")
	check(barrel.state.contaminated, "contamination flag reaches water")
	check(w.defs.get_def("ll.furniture.sofa_two_seat").has("components"), "definition not modified by effects")


func t22_offline_bounded() -> void:
	var s := stack()
	var w = s.world
	w.set_global("grid_power", true)
	var r: Dictionary = w.advance_offline(10 * 24 * 3600.0)
	eq(r.applied_s, w.MAX_OFFLINE_S, "offline catch-up bounded to 12 h")
	eq(w.time_s, w.MAX_OFFLINE_S, "clock advanced by the bound only")


func t23_save_rejects_bad_data() -> void:
	var s := stack()
	var w = s.world
	eq(s.saver.apply(w, {"schema": "nope"}), "not_a_world_delta", "wrong schema")
	eq(s.saver.apply(w, {"schema": "last-light.world-delta", "version": 99, "layout_id": w.layout_id, "objects": {}, "removed": []}), "unsupported_version", "future version")
	eq(s.saver.apply(w, {"schema": "last-light.world-delta", "version": 1, "layout_id": "other", "objects": {}, "removed": []}), "layout_mismatch", "layout mismatch")
	var bad := {"schema": "last-light.world-delta", "version": 1, "layout_id": w.layout_id, "removed": [],
		"objects": {L + "door.kitchen": {"def": "ll.fixture.door.interior_wood", "pos": [2.5, 4], "state": {"open": true}}, "ghost": {"def": "ll.does.not.exist", "pos": [0, 0], "state": {}}}}
	check(s.saver.apply(w, bad).begins_with("unknown_definition"), "unknown definition rejected")
	check(not obj(s, "door.kitchen").state.open, "rejected save left world untouched")
