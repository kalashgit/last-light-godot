extends RefCounted
## Object condition, damage, destruction and environmental effects.
## Public entry points for other workers:
##   apply_damage(id, amount, source)   - zombies (Worker 03), weapons (Worker 02), fire
##   apply_environment(id, effect)      - "flooded" | "burned" | "contaminated" | "dried"
## Environmental effects live in the instance's `env` state; definitions are never modified.

var world


func _init(w) -> void:
	world = w


func max_hp(obj) -> float:
	return float(world.comp(obj, "destructible").get("max_hp", 0.0))


## intact (>75%), worn (>50%), damaged (>0%), broken. Non-destructible objects are always intact.
func condition_of(obj) -> String:
	if obj.state.get("broken", false):
		return "broken"
	var m := max_hp(obj)
	if m <= 0.0:
		return "intact"
	var r := float(obj.state.get("hp", m)) / m
	if r > 0.75:
		return "intact"
	if r > 0.5:
		return "worn"
	return "damaged"


func env_flags(obj) -> Dictionary:
	return obj.state.get("env", {})


## Damage hits barricade layers first. Returns {absorbed_by, hp, broken_now}.
func apply_damage(id: String, amount: float, source: String = "unknown", changes = null) -> Dictionary:
	var obj = world.objects.get(id)
	if obj == null or amount <= 0.0:
		return {"ok": false, "reason": "invalid_target"}
	var layers: Array = obj.state.get("barricade", [])
	if not layers.is_empty():
		var top := layers.size() - 1
		var new_layers := layers.duplicate()
		new_layers[top] = float(new_layers[top]) - amount
		if new_layers[top] <= 0.0:
			new_layers.remove_at(top)
			world.emit({"type": "sound", "object_id": id, "pos": obj.center(), "radius": 10.0, "cue": "barricade_break"})
			world.emit({"type": "barricade_destroyed_layer", "object_id": id, "layers_left": new_layers.size(), "source": source})
		world.set_state(obj, "barricade", new_layers, changes)
		return {"ok": true, "absorbed_by": "barricade", "layers": new_layers.size(), "broken_now": false}
	if not world.has_cap(obj, "destructible") or obj.state.get("broken", false):
		return {"ok": false, "reason": "not_damageable"}
	var before := condition_of(obj)
	var hp := maxf(0.0, float(obj.state["hp"]) - amount)
	world.set_state(obj, "hp", hp, changes)
	world.emit({"type": "sound", "object_id": id, "pos": obj.center(), "radius": 6.0, "cue": "impact_" + str(world.def_of(obj).get("sound_material", "generic"))})
	if hp <= 0.0:
		return {"ok": true, "absorbed_by": "object", "hp": 0.0, "broken_now": true, "result": break_object(obj, source, changes)}
	var after := condition_of(obj)
	if before != after:
		world.emit({"type": "condition_changed", "object_id": id, "from": before, "to": after})
	return {"ok": true, "absorbed_by": "object", "hp": hp, "broken_now": false}


## Apply the definition's on_break behaviour exactly once.
func break_object(obj, source: String, changes = null) -> String:
	var id: String = obj.instance_id
	var mode: String = world.comp(obj, "destructible").get("on_break", "disable")
	world.settle(obj)
	match mode:
		"breach":
			# Doors/lockers: the leaf is gone. No longer lockable, permanently passable.
			world.set_state(obj, "broken", true, changes)
			if obj.state.has("locked"):
				world.set_state(obj, "locked", false, changes)
			if obj.state.has("open"):
				world.set_state(obj, "open", true, changes)
			world.emit({"type": "breach", "object_id": id, "source": source})
			world.emit({"type": "sound", "object_id": id, "pos": obj.center(), "radius": 20.0, "cue": "door_break"})
		"shatter":
			world.set_state(obj, "broken", true, changes)
			world.emit({"type": "sound", "object_id": id, "pos": obj.center(), "radius": float(world.comp(obj, "glass").get("smash_noise_radius", 14.0)), "cue": "glass_break"})
		"destroy_spill", "destroy":
			var pile := ""
			if mode == "destroy_spill" and world.has_cap(obj, "storage"):
				pile = world.storage.spill(obj, changes)
			world.emit({"type": "sound", "object_id": id, "pos": obj.center(), "radius": 12.0, "cue": "furniture_break"})
			world.emit({"type": "object_destroyed", "object_id": id, "source": source, "spill_pile": pile})
			world.remove_object(id, "destroyed")
			return "destroyed"
		_:
			world.set_state(obj, "broken", true, changes)
			if world.has_cap(obj, "generator") and obj.state.get("running", false):
				world.set_state(obj, "running", false, changes)
			world.emit({"type": "object_disabled", "object_id": id, "source": source})
	world.emit({"type": "condition_changed", "object_id": id, "to": "broken"})
	_power_refresh(obj)
	return mode


func apply_environment(id: String, effect: String, changes = null) -> Dictionary:
	var obj = world.objects.get(id)
	if obj == null:
		return {"ok": false, "reason": "invalid_target"}
	world.settle(obj)
	var env: Dictionary = env_flags(obj).duplicate()
	match effect:
		"flooded":
			env["flooded"] = true
		"dried":
			env.erase("flooded")
		"contaminated":
			env["contaminated"] = true
			if world.has_cap(obj, "water_storage"):
				world.set_state(obj, "contaminated", true, changes)
		"burned":
			env["burned"] = true
			world.set_state(obj, "env", env, changes)
			if world.has_cap(obj, "destructible") and not obj.state.get("broken", false):
				apply_damage(id, float(obj.state.get("hp", 0.0)) + 1.0, "fire", changes)
			return {"ok": true}
		_:
			return {"ok": false, "reason": "unknown_effect"}
	world.set_state(obj, "env", env, changes)
	world.emit({"type": "environment_changed", "object_id": id, "effect": effect})
	_power_refresh(obj)
	return {"ok": true}


func _power_refresh(obj) -> void:
	if world.objects.get(obj.instance_id) == null:
		return
	if world.has_cap(obj, "power_consumer"):
		var panel: String = world.power.panel_id_of(obj)
		if not panel.is_empty():
			world.power.recompute(panel)
	elif world.has_cap(obj, "generator"):
		var p: String = obj.state.get("panel", "")
		if not p.is_empty():
			world.power.recompute(p)
