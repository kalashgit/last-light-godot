extends RefCounted
## Pure inventory state. Health, hunger, thirst and save-file I/O belong to the game.
## Art identity is independent of inventory identity: saves contain stable item IDs only.
## Durable items (weapons/tools) additionally carry per-instance condition with stable
## instance IDs ("it_<n>"). instances[id] always has exactly inventory[id] entries; the
## equipped instance is instances[id][0]. Stackable consumables have no instance records.

const DEFINITIONS_PATH := "res://data/survival_items.json"
const RULES_PATH := "res://data/gameplay_rules.json"

var definitions: Dictionary = {}
var inventory: Dictionary = {}
var equipped: String = ""
var capacity_kg: float = 20.0
var instances: Dictionary = {}
var next_uid: int = 1
var default_weapon_durability: float = 30.0


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
	_load_golden40()
	var rules: Variant = JSON.parse_string(FileAccess.get_file_as_string(RULES_PATH))
	if rules is Dictionary and rules.get("combat") is Dictionary:
		default_weapon_durability = float(rules["combat"].get("default_weapon_durability", 30.0))


## Maximum condition for a durable definition; 0 means the item has no condition.
func max_condition(id: String) -> float:
	if not definitions.has(id):
		return 0.0
	var definition: Dictionary = definitions[id]
	if definition.has("durability"):
		return float(definition["durability"])
	return default_weapon_durability if definition.get("kind") == "weapon" else 0.0


func is_durable(id: String) -> bool:
	return max_condition(id) > 0.0


## Add items. For durable items, `carried` may supply existing instance records
## (e.g. from a world drop) so condition survives pickup; otherwise new full-condition
## instances are created.
func add(id: String, count: Variant = 1, carried: Array = []) -> bool:
	if not definitions.has(id) or not _valid_count(count):
		return false
	var next_count: int = int(inventory.get(id, 0)) + int(count)
	if next_count > int(definitions[id]["stack_max"]):
		return false
	if total_weight() + float(definitions[id]["weight_kg"]) * float(count) > capacity_kg + 0.00001:
		return false
	if is_durable(id):
		if not carried.is_empty() and not _valid_instances(id, carried, int(count)):
			return false
		var list: Array = instances.get(id, [])
		for i in range(int(count)):
			if carried.is_empty():
				list.append({"uid": "it_%d" % next_uid, "condition": max_condition(id)})
				next_uid += 1
			else:
				list.append({"uid": str(carried[i]["uid"]), "condition": float(carried[i]["condition"])})
		instances[id] = list
	inventory[id] = next_count
	return true


func remove(id: String, count: Variant = 1) -> bool:
	return not take(id, count).is_empty()


## Remove items and return removed instance records (durable) or [{}...] placeholders
## for stackables. Returns [] on failure. Durable removals come from the end so the
## equipped instance (index 0) is the last to go.
func take(id: String, count: Variant = 1) -> Array:
	if not inventory.has(id) or not _valid_count(count) or int(count) > int(inventory[id]):
		return []
	var removed: Array = []
	if is_durable(id):
		var list: Array = instances.get(id, [])
		for i in range(int(count)):
			removed.append(list.pop_back())
		if list.is_empty():
			instances.erase(id)
	else:
		for i in range(int(count)):
			removed.append({})
	var remaining: int = int(inventory[id]) - int(count)
	if remaining == 0:
		inventory.erase(id)
		if equipped == id:
			equipped = ""
	else:
		inventory[id] = remaining
	return removed


## Condition of the active (index 0) instance; -1 when the item has no condition.
func condition(id: String) -> float:
	if not is_durable(id) or not instances.has(id):
		return -1.0
	return float(instances[id][0]["condition"])


## Wear the active instance. Returns {"condition": float, "broken": bool}. A broken
## instance is removed; if it was the last one, the item is unequipped.
func wear(id: String, amount: float) -> Dictionary:
	if not is_durable(id) or not instances.has(id) or amount <= 0.0 or not is_finite(amount):
		return {}
	var active: Dictionary = instances[id][0]
	active["condition"] = maxf(0.0, float(active["condition"]) - amount)
	if active["condition"] > 0.0:
		return {"condition": active["condition"], "broken": false, "uid": active["uid"]}
	var list: Array = instances[id]
	list.remove_at(0)
	var remaining: int = int(inventory[id]) - 1
	if remaining == 0:
		inventory.erase(id)
		instances.erase(id)
		if equipped == id:
			equipped = ""
	else:
		inventory[id] = remaining
	return {"condition": 0.0, "broken": true, "uid": active["uid"]}


## Restore condition on the active instance, clamped to the maximum. Returns amount restored.
func repair(id: String, amount: float) -> float:
	if not is_durable(id) or not instances.has(id) or amount <= 0.0 or not is_finite(amount):
		return 0.0
	var active: Dictionary = instances[id][0]
	var restored := minf(max_condition(id) - float(active["condition"]), amount)
	active["condition"] = float(active["condition"]) + restored
	return restored


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
	return {"inventory": inventory.duplicate(true), "equipped": equipped, "instances": instances.duplicate(true), "next_uid": next_uid}


## Accepts the schema-2 two-key form (no conditions; durable items restore at full
## condition) or the schema-3 four-key form with instance records.
func validate(data: Variant) -> bool:
	if not data is Dictionary or not data.has("inventory") or not data.has("equipped"):
		return false
	if data.size() == 4:
		if not data.has("instances") or not data.has("next_uid") or not _valid_instance_map(data):
			return false
	elif data.size() != 2:
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
	var restored_instances: Dictionary = {}
	var uid_counter: int = int(data["next_uid"]) if data.size() == 4 else 1
	for id: String in data["inventory"]:
		restored[id] = int(data["inventory"][id])
		if not is_durable(id):
			continue
		var list: Array = []
		if data.size() == 4:
			for record: Dictionary in data["instances"][id]:
				list.append({"uid": str(record["uid"]), "condition": float(record["condition"])})
		else:
			for i in range(restored[id]):
				list.append({"uid": "it_%d" % uid_counter, "condition": max_condition(id)})
				uid_counter += 1
		restored_instances[id] = list
	inventory = restored
	instances = restored_instances
	next_uid = uid_counter
	equipped = data["equipped"]
	return true


func _valid_instance_map(data: Dictionary) -> bool:
	var counter: Variant = data["next_uid"]
	if not _valid_uid_counter(counter) or not data["instances"] is Dictionary or not data["inventory"] is Dictionary:
		return false
	var map: Dictionary = data["instances"]
	var seen: Dictionary = {}
	for id: Variant in data["inventory"]:
		if not id is String or not definitions.has(id):
			return false
		if is_durable(id) != map.has(id):
			return false
	for id: Variant in map:
		if not id is String or not data["inventory"].has(id) or not _valid_count(data["inventory"][id]):
			return false
		if not _valid_instances(id, map[id], int(data["inventory"][id])):
			return false
		for record: Dictionary in map[id]:
			var number: int = int(str(record["uid"]).substr(3))
			if seen.has(record["uid"]) or number >= int(counter):
				return false
			seen[record["uid"]] = true
	return true


func _valid_instances(id: String, list: Variant, count: int) -> bool:
	if not list is Array or list.size() != count:
		return false
	var limit := max_condition(id)
	var seen: Dictionary = {}
	for record: Variant in list:
		if not record is Dictionary or record.size() != 2 or not record.get("uid") is String:
			return false
		var uid: String = record["uid"]
		if not uid.begins_with("it_") or not uid.substr(3).is_valid_int() or int(uid.substr(3)) < 1 or seen.has(uid):
			return false
		seen[uid] = true
		var value: Variant = record.get("condition")
		if (typeof(value) != TYPE_INT and typeof(value) != TYPE_FLOAT) or not is_finite(float(value)) or float(value) <= 0.0 or float(value) > limit:
			return false
	return true


## Public check used by save loading for dropped durable items.
func valid_instances(id: String, list: Variant, count: int) -> bool:
	return is_durable(id) and _valid_instances(id, list, count)


func _valid_uid_counter(value: Variant) -> bool:
	if typeof(value) != TYPE_INT and typeof(value) != TYPE_FLOAT:
		return false
	var number: float = float(value)
	return is_finite(number) and number >= 1.0 and number <= 1000000000.0 and floor(number) == number


func _valid_count(value: Variant) -> bool:
	# JSON numbers arrive as floats; reject booleans, NaN, fractions and unbounded conversions.
	if typeof(value) != TYPE_INT and typeof(value) != TYPE_FLOAT:
		return false
	var number: float = float(value)
	return is_finite(number) and number >= 1.0 and number <= 1000.0 and floor(number) == number

# Golden 40 icon-only loot catalog. Keep the same tab indentation as the base script.
func _load_golden40() -> void:
	const GOLDEN_PATH := "res://data/golden40_items.json"
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(GOLDEN_PATH))
	if not parsed is Dictionary:
		push_error("Invalid Golden 40 catalog: expected Dictionary")
		return
	if parsed.get("schema", 0) != 1 or not parsed.get("items") is Array:
		push_error("Invalid Golden 40 catalog schema/items")
		return
	for raw: Variant in parsed["items"]:
		if not raw is Dictionary:
			push_error("Invalid Golden 40 item entry")
			return
		var record: Dictionary = raw
		if not record.get("id") is String or not record.get("icon_path") is String:
			push_error("Incomplete Golden 40 item identity")
			return
		var item_id: String = str(record["id"])
		if definitions.has(item_id):
			push_error("Duplicate Golden 40 item ID: " + item_id)
			return
		definitions[item_id] = record.duplicate(true)
