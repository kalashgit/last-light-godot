extends RefCounted
## Data-driven item actions: craft, repair, dismantle and wound treatment.
## Recipes live in res://data/recipes.json and may reference only catalog item IDs.
## execute() is atomic: on any failure inventory and vitals are unchanged, and inputs
## are consumed exactly once on success.

const RECIPES_PATH := "res://data/recipes.json"
const KINDS := ["craft", "repair", "dismantle", "treat"]

var recipes: Dictionary = {}
var order: Array[String] = []
var load_errors: Array[String] = []


## `definitions` is the survival item catalog; recipes referencing unknown IDs are rejected.
func _init(definitions: Dictionary = {}) -> void:
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(RECIPES_PATH))
	if not parsed is Dictionary or parsed.get("schema") != 1 or not parsed.get("recipes") is Array:
		load_errors.append("invalid recipe file")
		return
	for raw: Variant in parsed["recipes"]:
		var problem := _check(raw, definitions)
		if not problem.is_empty():
			load_errors.append(problem)
			continue
		recipes[raw["id"]] = raw.duplicate(true)
		order.append(raw["id"])
	for problem: String in load_errors:
		push_error("Recipe rejected: " + problem)


func _check(raw: Variant, definitions: Dictionary) -> String:
	if not raw is Dictionary or not raw.get("id") is String or recipes.has(raw.get("id")):
		return "missing or duplicate id"
	var id: String = raw["id"]
	if not raw.get("kind") in KINDS or not raw.get("inputs") is Array or raw["inputs"].is_empty() or not raw.get("tools") is Array:
		return id + ": kind/inputs/tools"
	var references: Array = []
	for entry: Variant in raw["inputs"]:
		if not entry is Dictionary or not entry.get("id") is String or int(entry.get("count", 0)) < 1:
			return id + ": malformed input"
		references.append(entry["id"])
	references.append_array(raw["tools"])
	for entry: Variant in raw.get("outputs", []):
		if not entry is Dictionary or not entry.get("id") is String or int(entry.get("count", 0)) < 1:
			return id + ": malformed output"
		references.append(entry["id"])
	if raw["kind"] == "repair":
		if not raw.get("target") is String or float(raw.get("repair_amount", 0.0)) <= 0.0:
			return id + ": repair needs target and amount"
		if raw["target"] != "@equipped":
			references.append(raw["target"])
	if raw["kind"] in ["craft", "dismantle"] and raw.get("outputs", []).is_empty():
		return id + ": needs outputs"
	if raw["kind"] == "treat" and not raw.get("effect") is Dictionary:
		return id + ": treat needs effect"
	if not definitions.is_empty():
		for ref: Variant in references:
			if not definitions.has(ref):
				return id + ": unknown item " + str(ref)
	return ""


## Returns {"ok": bool, "reason": String}. Never mutates state.
func check(recipe_id: String, survival, vitals) -> Dictionary:
	if not recipes.has(recipe_id):
		return {"ok": false, "reason": "Unknown recipe"}
	var recipe: Dictionary = recipes[recipe_id]
	if vitals != null and vitals.is_dead():
		return {"ok": false, "reason": "Cannot act"}
	for entry: Dictionary in recipe["inputs"]:
		if int(survival.inventory.get(entry["id"], 0)) < int(entry["count"]):
			return {"ok": false, "reason": "Missing " + survival.name_for(entry["id"])}
	for tool: String in recipe["tools"]:
		if not survival.inventory.has(tool):
			return {"ok": false, "reason": "Needs " + survival.name_for(tool)}
	match recipe["kind"]:
		"repair":
			var target := _target(recipe, survival)
			if target.is_empty():
				return {"ok": false, "reason": "Nothing to repair"}
			if survival.condition(target) >= survival.max_condition(target):
				return {"ok": false, "reason": survival.name_for(target) + " is already in full condition"}
		"treat":
			var effect: Dictionary = recipe["effect"]
			var useful := false
			if effect.has("disinfect") and vitals != null and vitals.contaminated_wound_count() > 0:
				useful = true
			if effect.has("bandage") and vitals != null and vitals.open_wound_count() > 0:
				useful = true
			if not useful:
				return {"ok": false, "reason": "No wound needs this"}
	return {"ok": true, "reason": ""}


## Runs a recipe. Returns {"ok", "reason", "recipe", "outputs", "repaired", "treated"}.
func execute(recipe_id: String, survival, vitals) -> Dictionary:
	var verdict := check(recipe_id, survival, vitals)
	if not verdict.ok:
		return verdict
	var recipe: Dictionary = recipes[recipe_id]
	var before: Dictionary = survival.snapshot()
	var result := {"ok": true, "reason": "", "recipe": recipe_id, "outputs": [], "repaired": 0.0, "treated": 0}
	# Repair target must be resolved before inputs are removed (an input could be the target).
	var target := _target(recipe, survival) if recipe["kind"] == "repair" else ""
	for entry: Dictionary in recipe["inputs"]:
		if not survival.remove(entry["id"], int(entry["count"])):
			survival.restore(before)
			return {"ok": false, "reason": "Could not use " + survival.name_for(entry["id"])}
	match recipe["kind"]:
		"repair":
			result.repaired = survival.repair(target, float(recipe["repair_amount"]))
			if result.repaired <= 0.0:
				survival.restore(before)
				return {"ok": false, "reason": "Repair failed"}
		"treat":
			var effect: Dictionary = recipe["effect"]
			if effect.has("disinfect"):
				result.treated += vitals.disinfect(int(effect["disinfect"]))
			if effect.has("bandage"):
				result.treated += vitals.bandage(int(effect["bandage"]))
		"craft", "dismantle":
			for entry: Dictionary in recipe["outputs"]:
				if not survival.add(entry["id"], int(entry["count"])):
					survival.restore(before)
					return {"ok": false, "reason": "No room for " + survival.name_for(entry["id"])}
				result.outputs.append(entry.duplicate())
	return result


## Recipe IDs whose first input is `item_id`, in file order (drives the inventory Use button).
func recipes_using(item_id: String) -> Array[String]:
	var found: Array[String] = []
	for recipe_id: String in order:
		if recipes[recipe_id]["inputs"][0]["id"] == item_id:
			found.append(recipe_id)
	return found


## First recipe started from `item_id` that can run now, or "".
func first_available(item_id: String, survival, vitals) -> String:
	for recipe_id: String in recipes_using(item_id):
		if check(recipe_id, survival, vitals).ok:
			return recipe_id
	return ""


func _target(recipe: Dictionary, survival) -> String:
	var target: String = recipe.get("target", "")
	if target == "@equipped":
		target = survival.equipped
	if target.is_empty() or not survival.inventory.has(target) or not survival.is_durable(target):
		return ""
	return target
