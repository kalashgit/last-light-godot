extends RefCounted
## Container instances: compartments, capacity (weight + slots), deterministic one-time loot.
## Contents shape in object state: {"contents": {compartment_id: {item_id: count}}}.
## Worker 02 owns *player* inventory rules; this file owns the container side only.

var world


func _init(w) -> void:
	world = w


func compartments(obj) -> Array:
	return world.comp(obj, "storage").get("compartments", [])


func compartment_spec(obj, comp_id: String) -> Dictionary:
	for c in compartments(obj):
		if c["id"] == comp_id:
			return c
	return {}


func default_compartment(obj) -> String:
	var list := compartments(obj)
	return list[0]["id"] if not list.is_empty() else ""


## Roll loot exactly once per instance. Returns true only on the call that actually rolled.
## Seed = hash("<world_seed>:<instance_id>:<compartment>") so rerolls are impossible and
## identical seeds reproduce identical contents.
func ensure_initialized(obj, changes = null) -> bool:
	if obj.state.get("loot_initialized", false):
		return false
	var storage: Dictionary = world.comp(obj, "storage")
	var contents := {}
	for c in compartments(obj):
		var comp_items := {}
		var profile: Dictionary = world.defs.loot_profiles.get(c.get("loot_profile", storage.get("loot_profile", "empty")), {})
		var rng := RandomNumberGenerator.new()
		rng.seed = hash("%d:%s:%s" % [world.world_seed, obj.instance_id, c["id"]])
		var rolls_range: Array = profile.get("rolls", [0, 0])
		var rolls := rng.randi_range(int(rolls_range[0]), int(rolls_range[1]))
		var entries: Array = profile.get("entries", [])
		var total_w := 0.0
		for e in entries:
			total_w += float(e["weight"])
		for i in rolls:
			if total_w <= 0.0:
				break
			var pick := rng.randf() * total_w
			for e in entries:
				pick -= float(e["weight"])
				if pick <= 0.0:
					var cnt := rng.randi_range(int(e["count"][0]), int(e["count"][1]))
					var item: String = e["item"]
					# Respect capacity at generation time too.
					while cnt > 0 and not _fits(c, comp_items, item, cnt):
						cnt -= 1
					if cnt > 0:
						comp_items[item] = int(comp_items.get(item, 0)) + cnt
					break
		contents[c["id"]] = comp_items
	world.set_state(obj, "contents", contents, changes)
	world.set_state(obj, "loot_initialized", true, changes)
	world.emit({"type": "loot_initialized", "object_id": obj.instance_id, "item_count": total_items(obj)})
	return true


func items_in(obj, comp_id: String) -> Dictionary:
	return obj.state.get("contents", {}).get(comp_id, {})


func count(obj, comp_id: String, item_id: String) -> int:
	return int(items_in(obj, comp_id).get(item_id, 0))


func total_items(obj) -> int:
	var n := 0
	for comp_id in obj.state.get("contents", {}):
		for item in obj.state["contents"][comp_id]:
			n += int(obj.state["contents"][comp_id][item])
	return n


func weight(obj, comp_id: String = "") -> float:
	var total := 0.0
	var contents: Dictionary = obj.state.get("contents", {})
	for c in contents:
		if not comp_id.is_empty() and c != comp_id:
			continue
		for item in contents[c]:
			total += world.defs.weight_of(item) * float(contents[c][item])
	return total


func _fits(spec: Dictionary, comp_items: Dictionary, item_id: String, n: int) -> bool:
	var w: float = world.defs.weight_of(item_id)
	if w < 0.0:
		return false
	var current := 0.0
	for it in comp_items:
		current += world.defs.weight_of(it) * float(comp_items[it])
	if current + w * n > float(spec.get("capacity_kg", 0.0)) + 0.00001:
		return false
	if not comp_items.has(item_id) and comp_items.size() >= int(spec.get("slots", 0)):
		return false
	return true


## "" when `n` of item fits into the compartment, else a failure reason.
func can_add(obj, comp_id: String, item_id: String, n: int) -> String:
	var spec := compartment_spec(obj, comp_id)
	if spec.is_empty():
		return "unknown_compartment"
	if world.defs.weight_of(item_id) < 0.0:
		return "unknown_item"
	if not _fits(spec, items_in(obj, comp_id), item_id, n):
		return "container_full"
	return ""


func add(obj, comp_id: String, item_id: String, n: int, changes = null) -> bool:
	if not can_add(obj, comp_id, item_id, n).is_empty():
		return false
	var contents: Dictionary = obj.state.get("contents", {}).duplicate(true)
	var comp_items: Dictionary = contents.get(comp_id, {})
	comp_items[item_id] = int(comp_items.get(item_id, 0)) + n
	contents[comp_id] = comp_items
	world.set_state(obj, "contents", contents, changes)
	return true


func remove(obj, comp_id: String, item_id: String, n: int, changes = null) -> bool:
	if n <= 0 or count(obj, comp_id, item_id) < n:
		return false
	var contents: Dictionary = obj.state.get("contents", {}).duplicate(true)
	var left := int(contents[comp_id][item_id]) - n
	if left == 0:
		contents[comp_id].erase(item_id)
	else:
		contents[comp_id][item_id] = left
	world.set_state(obj, "contents", contents, changes)
	return true


## Move all contents to a deterministic ground pile next to the object (destroyed storage).
## Returns the pile id or "" when there was nothing to spill. Exactly-once is guaranteed by
## the caller removing the source object in the same step.
func spill(obj, changes = null) -> String:
	ensure_initialized(obj, changes)
	if total_items(obj) == 0:
		return ""
	var merged := {}
	var contents: Dictionary = obj.state["contents"]
	for c in contents:
		for item in contents[c]:
			merged[item] = int(merged.get(item, 0)) + int(contents[c][item])
	var pile = world.spawn_object(obj.instance_id, "spill", "ll.world.ground_pile", obj.rect().get_center() - Vector2(0.25, 0.25),
		{"loot_initialized": true, "searched": true, "contents": {"ground": merged}})
	world.set_state(obj, "contents", {}, changes)
	world.emit({"type": "contents_spilled", "object_id": obj.instance_id, "pile_id": pile.instance_id})
	return pile.instance_id
