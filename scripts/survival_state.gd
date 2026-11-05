extends RefCounted
## Pure inventory state. Health, hunger, thirst and save-file I/O belong to the game.
## Art identity is independent of inventory identity: saves contain stable item IDs only.

const DEFINITIONS_PATH := "res://data/survival_items.json"

var definitions: Dictionary = {}
var inventory: Dictionary = {}
var equipped: String = ""
var capacity_kg: float = 20.0


func _init() -> void:
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(DEFINITIONS_PATH))
	if not parsed is Dictionary or parsed.get("schema") != 1 or not parsed.get("items") is Array:
		push_error("Invalid survival item definitions: " + DEFINITIONS_PATH)
		return
	for raw: Variant in parsed["items"]:
		if not raw is Dictionary or not raw.get("id") is String:
			definitions.clear()
			push_error("Malformed survival item definition")
			return
		var id: String = raw["id"]
		if definitions.has(id):
			definitions.clear()
			push_error("Duplicate survival item ID: " + id)
			return
		definitions[id] = raw.duplicate(true)


func add(id: String, count: Variant = 1) -> bool:
	if not definitions.has(id) or not _valid_count(count):
		return false
	var next_count: int = int(inventory.get(id, 0)) + int(count)
	if next_count > int(definitions[id]["stack_max"]):
		return false
	if total_weight() + float(definitions[id]["weight_kg"]) * float(count) > capacity_kg + 0.00001:
		return false
	inventory[id] = next_count
	return true


func remove(id: String, count: Variant = 1) -> bool:
	if not inventory.has(id) or not _valid_count(count) or int(count) > int(inventory[id]):
		return false
	var remaining: int = int(inventory[id]) - int(count)
	if remaining == 0:
		inventory.erase(id)
		if equipped == id:
			equipped = ""
	else:
		inventory[id] = remaining
	return true


func equip(id: String) -> bool:
	if id.is_empty():
		equipped = ""
		return true
	if not inventory.has(id) or not definitions.has(id) or definitions[id]["kind"] != "weapon":
		return false
	equipped = id
	return true


func consume(id: String) -> Dictionary:
	if not inventory.has(id) or not definitions.has(id):
		return {}
	var definition: Dictionary = definitions[id]
	if definition["kind"] not in ["food", "drink", "heal"]:
		return {}
	var effect: Dictionary = {"kind": definition["kind"], "amount": float(definition["amount"])}
	if not remove(id, 1):
		return {}
	return effect


func action(id: String) -> String:
	if not definitions.has(id) or not inventory.has(id):
		return ""
	match definitions[id]["kind"]:
		"food": return "Eat"
		"drink": return "Drink"
		"heal": return str(definitions[id].get("action", "Heal"))
		"weapon": return "Unequip" if equipped == id else "Equip"
	# Utility/material objects can be carried and dropped; no flashlight/crafting simulation is claimed.
	return "Inspect"


func name_for(id: String) -> String:
	return str(definitions.get(id, {}).get("name", "Unknown object"))


func rows() -> Array[Dictionary]:
	var result: Array[Dictionary] = []
	var ids: Array = inventory.keys()
	ids.sort()
	for id: String in ids:
		result.append({"id": id, "name": name_for(id), "count": int(inventory[id]), "action": action(id)})
	return result


func total_weight() -> float:
	var result: float = 0.0
	for id: String in inventory:
		result += float(definitions[id]["weight_kg"]) * float(inventory[id])
	return result


func snapshot() -> Dictionary:
	return {"inventory": inventory.duplicate(true), "equipped": equipped}


func validate(data: Variant) -> bool:
	if not data is Dictionary or data.size() != 2 or not data.has("inventory") or not data.has("equipped"):
		return false
	if not data["inventory"] is Dictionary or not data["equipped"] is String:
		return false
	var candidate: Dictionary = data["inventory"]
	var weight: float = 0.0
	for id: Variant in candidate:
		if not id is String or not definitions.has(id) or not _valid_count(candidate[id]):
			return false
		if int(candidate[id]) > int(definitions[id]["stack_max"]):
			return false
		weight += float(candidate[id]) * float(definitions[id]["weight_kg"])
	if not is_finite(weight) or weight > capacity_kg + 0.00001:
		return false
	var weapon: String = data["equipped"]
	return weapon.is_empty() or (candidate.has(weapon) and definitions[weapon]["kind"] == "weapon")


func restore(data: Variant) -> bool:
	if not validate(data):
		return false
	var restored: Dictionary = {}
	for id: String in data["inventory"]:
		restored[id] = int(data["inventory"][id])
	inventory = restored
	equipped = data["equipped"]
	return true


func _valid_count(value: Variant) -> bool:
	# JSON numbers arrive as floats; reject booleans, NaN, fractions and unbounded conversions.
	if typeof(value) != TYPE_INT and typeof(value) != TYPE_FLOAT:
		return false
	var number: float = float(value)
	return is_finite(number) and number >= 1.0 and number <= 1000.0 and floor(number) == number
