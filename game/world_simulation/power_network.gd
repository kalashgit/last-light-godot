extends RefCounted
## Simplified, event-driven electrical model.
##
## grid (globals.grid_power) ─┐
##                            ├─> breaker panel ─(breaker on?)─> circuit ─> consumer (switched_on, not faulted)
## generator (running, fuel) ─┘
##
## - Grid supply is unlimited. A generator supplies up to capacity_w; if demand exceeds it the
##   generator trips (stops) and the panel goes dark.
## - Fuel burns at base_lph + per_kw_lph * load_kW and is solved analytically; a single
##   "fuel_out" event is scheduled for the exact moment the tank empties.
## - recompute() only runs on changes (switch, breaker, connect, fuel-out, grid change, damage).

var world
var _topology_dirty := true
var _consumers_by_panel: Dictionary = {}


func _init(w) -> void:
	world = w


func mark_topology_dirty() -> void:
	_topology_dirty = true


func _rebuild_topology() -> void:
	_consumers_by_panel.clear()
	for id in world.order:
		var obj = world.objects[id]
		if world.has_cap(obj, "power_consumer"):
			var panel := panel_id_of(obj)
			if not panel.is_empty():
				if not _consumers_by_panel.has(panel):
					_consumers_by_panel[panel] = []
				_consumers_by_panel[panel].append(id)
	_topology_dirty = false


func panel_id_of(consumer) -> String:
	var circuit: String = consumer.state.get("circuit", "")
	var idx := circuit.rfind(":")
	return circuit.substr(0, idx) if idx > 0 else ""


func circuit_name_of(consumer) -> String:
	var circuit: String = consumer.state.get("circuit", "")
	var idx := circuit.rfind(":")
	return circuit.substr(idx + 1) if idx > 0 else ""


func consumers_on(panel_id: String) -> Array:
	if _topology_dirty:
		_rebuild_topology()
	return _consumers_by_panel.get(panel_id, [])


func generators_on(panel_id: String) -> Array:
	var out := []
	for id in world.order:
		var obj = world.objects[id]
		if world.has_cap(obj, "generator") and obj.state.get("panel", "") == panel_id:
			out.append(obj)
	return out


func is_faulted(obj) -> bool:
	if obj.state.get("broken", false):
		return true
	var pc: Dictionary = world.comp(obj, "power_consumer")
	if pc.is_empty():
		pc = world.comp(obj, "generator")
	return pc.get("flood_sensitive", false) and obj.state.get("env", {}).get("flooded", false)


func demand_w(consumer) -> float:
	return float(world.comp(consumer, "power_consumer").get("demand_w", 0.0))


func wants_power(consumer, panel) -> bool:
	if not consumer.state.get("switched_on", false) or is_faulted(consumer):
		return false
	return panel.state.get("breakers", {}).get(circuit_name_of(consumer), false)


func recompute_all() -> void:
	if _topology_dirty:
		_rebuild_topology()
	var seen := {}
	for id in world.order:
		var obj = world.objects[id]
		if world.has_cap(obj, "breaker_panel"):
			recompute(id)
			seen[id] = true
	# Consumers wired to a missing panel are simply unpowered.
	for panel_id in _consumers_by_panel:
		if not seen.has(panel_id):
			for cid in _consumers_by_panel[panel_id]:
				_set_powered(world.objects[cid], false)
	for id in world.order:
		var obj = world.objects[id]
		if world.has_cap(obj, "power_consumer") and panel_id_of(obj).is_empty():
			_set_powered(obj, false)


func recompute(panel_id: String) -> void:
	var panel = world.objects.get(panel_id)
	if panel == null:
		return
	# Freeze time-dependent values under the *old* conditions before anything changes.
	world.settle_all_dynamic()
	var consumers := consumers_on(panel_id)
	var total_load := 0.0
	for cid in consumers:
		var c = world.objects[cid]
		if wants_power(c, panel):
			total_load += demand_w(c)
	var grid: bool = world.globals.get("grid_power", false) and panel.state.get("grid_connected", false)
	var gens := generators_on(panel_id)
	var supplying = null
	if not grid:
		for g in gens:
			if g.state.get("running", false) and float(g.state.get("fuel_l", 0.0)) > 0.0 and not is_faulted(g):
				supplying = g
				break
	var live := grid
	if supplying != null:
		var cap := float(world.comp(supplying, "generator")["capacity_w"])
		if total_load > cap:
			world.set_state(supplying, "running", false)
			world.unschedule(supplying.instance_id, "fuel_out")
			world.emit({"type": "generator_overload", "object_id": supplying.instance_id, "load_w": total_load, "capacity_w": cap})
			supplying = null
		else:
			live = true
	for g in gens:
		var g_load := total_load if g == supplying else 0.0
		if float(g.state.get("load_w", 0.0)) != g_load:
			world.set_state(g, "load_w", g_load)
		_reschedule_fuel(g)
	for cid in consumers:
		var c = world.objects[cid]
		_set_powered(c, live and wants_power(c, panel))
	world.set_state(panel, "live", live)
	world.set_state(panel, "source", "grid" if grid else ("generator" if live else "none"))


func _set_powered(c, value: bool) -> void:
	if c.state.get("powered", false) == value:
		return
	world.set_state(c, "powered", value)
	world.emit({"type": "power_changed", "object_id": c.instance_id, "powered": value})


# ---------------------------------------------------------------- generator fuel

func burn_rate_lph(gen) -> float:
	if not gen.state.get("running", false):
		return 0.0
	var g: Dictionary = world.comp(gen, "generator")
	return float(g["base_lph"]) + float(g["per_kw_lph"]) * float(gen.state.get("load_w", 0.0)) / 1000.0


func settle_generator(gen, dt: float) -> void:
	var rate := burn_rate_lph(gen)
	if rate <= 0.0:
		return
	gen.state["fuel_l"] = maxf(0.0, float(gen.state.get("fuel_l", 0.0)) - rate * dt / 3600.0)


func _reschedule_fuel(gen) -> void:
	var rate := burn_rate_lph(gen)
	if rate <= 0.0:
		world.unschedule(gen.instance_id, "fuel_out")
		return
	var fuel := float(gen.state.get("fuel_l", 0.0))
	world.schedule(world.time_s + fuel / rate * 3600.0, gen.instance_id, "fuel_out")


func on_fuel_out(gen) -> void:
	world.settle(gen)
	gen.state["fuel_l"] = 0.0
	world.set_state(gen, "running", false)
	world.emit({"type": "generator_fuel_out", "object_id": gen.instance_id})
	world.emit({"type": "sound", "object_id": gen.instance_id, "pos": gen.center(), "radius": 4.0, "cue": "generator_sputter"})
	var panel_id: String = gen.state.get("panel", "")
	if not panel_id.is_empty():
		recompute(panel_id)
