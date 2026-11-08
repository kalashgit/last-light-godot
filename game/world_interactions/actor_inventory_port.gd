extends RefCounted
## Minimal actor inventory used by tests and the world-simulation lab.
## It implements the same port the interaction system expects from Worker 02's
## scripts/survival_state.gd (add/remove/inventory), so the real inventory can be dropped in.

var inventory: Dictionary = {}
var capacity_kg: float = 20.0
var defs


func _init(definitions = null, capacity: float = 20.0) -> void:
	defs = definitions
	capacity_kg = capacity


func quantity(id: String) -> int:
	return int(inventory.get(id, 0))


func total_weight() -> float:
	var w := 0.0
	for id in inventory:
		w += maxf(0.0, defs.weight_of(id)) * float(inventory[id]) if defs != null else 0.0
	return w


func add(id: String, n: int = 1) -> bool:
	if n < 1:
		return false
	if defs != null:
		var w: float = defs.weight_of(id)
		if w < 0.0 or total_weight() + w * n > capacity_kg + 0.00001:
			return false
	inventory[id] = quantity(id) + n
	return true


func remove(id: String, n: int = 1) -> bool:
	if n < 1 or quantity(id) < n:
		return false
	var left := quantity(id) - n
	if left == 0:
		inventory.erase(id)
	else:
		inventory[id] = left
	return true


func snapshot() -> Dictionary:
	return {"inventory": inventory.duplicate(true)}


func restore(data: Dictionary) -> void:
	inventory.clear()
	for id in data.get("inventory", {}):
		inventory[id] = int(data["inventory"][id])
