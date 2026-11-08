extends RefCounted
## Deterministic zombie spawn definitions (Worker 03).
## Identical inputs (world seed, region, building, room, spawn index) always produce the
## same instance ID, profile, appearance and loot, on every platform. Appearance and loot
## come from one loadout record so they cannot disagree.
## Clothing IDs are gameplay tags only: no clothing art exists yet (see docs/zombie).

const Profiles := preload("res://scripts/zombie/zombie_profiles.gd")

## Location context -> weighted profile table, clothing pool and contextual loot pool.
## Loot IDs must exist in res://data/survival_items.json (Worker 02 item definitions).
const CONTEXTS := {
	"residential": {
		"profiles": [["civilian", 6], ["shambler", 3], ["injured", 2], ["crawler", 1]],
		"clothing": [["casual_tshirt", "jeans"], ["pyjamas"], ["hoodie", "track_pants"], ["cardigan", "slacks"]],
		"loot": [["ll_food_bean_tin", 3], ["ll_food_water_bottle", 3], ["ll_household_flashlight", 1], ["", 4]],
	},
	"hospital": {
		"profiles": [["medical_orderly", 5], ["injured", 3], ["crawler", 2], ["shambler", 1]],
		"clothing": [["scrubs"], ["scrubs", "lab_coat"], ["hospital_gown"]],
		"loot": [["ll_medical_sterile_bandage", 4], ["ll_medical_first_aid_case", 1], ["", 3]],
	},
	"workshop": {
		"profiles": [["worker", 5], ["shambler", 2], ["stagger_prone", 1]],
		"clothing": [["hi_vis_vest", "work_trousers"], ["overalls"], ["work_jacket", "jeans"]],
		"loot": [["ll_tools_claw_hammer", 2], ["ll_tools_hatchet", 1], ["ll_crafting_pine_plank", 2], ["", 3]],
	},
	"shop": {
		"profiles": [["civilian", 4], ["shambler", 3], ["fast_shambler", 1], ["security_guard", 1]],
		"clothing": [["shop_uniform"], ["casual_tshirt", "jeans"], ["security_uniform"]],
		"loot": [["ll_food_bean_tin", 3], ["ll_food_water_bottle", 2], ["", 3]],
	},
	"road": {
		"profiles": [["shambler", 4], ["civilian", 3], ["fast_shambler", 1], ["stagger_prone", 2], ["worker", 1], ["injured", 1]],
		"clothing": [["casual_tshirt", "jeans"], ["jacket", "slacks"], ["hi_vis_vest", "work_trousers"], ["hoodie", "track_pants"]],
		"loot": [["ll_food_water_bottle", 2], ["ll_food_bean_tin", 1], ["", 5]],
	},
}


## 32-bit FNV-1a. Pure integer math, stable across runs and platforms.
static func h32(text: String) -> int:
	var h := 2166136261
	for byte in text.to_utf8_buffer():
		h = ((h ^ byte) * 16777619) & 0xffffffff
	return h


static func unit(seed: int, salt: String) -> float:
	return float(h32(str(seed) + ":" + salt)) / 4294967296.0


static func _pick(table: Array, roll: float) -> Variant:
	var total := 0.0
	for row: Array in table:
		total += float(row[1])
	var cursor := roll * total
	for row: Array in table:
		cursor -= float(row[1])
		if cursor < 0.0:
			return row[0]
	return table[table.size() - 1][0]


## spawn: {world_seed:int, region, building, room, index:int, context, position:Vector2,
##         profile (optional override), facing (optional Vector2)}
static func make(spawn: Dictionary) -> Dictionary:
	var key := "%d/%s/%s/%s/%d" % [int(spawn.get("world_seed", 0)), spawn.get("region", ""), spawn.get("building", ""), spawn.get("room", ""), int(spawn.get("index", 0))]
	var seed := h32(key)
	var context_id: String = spawn.get("context", "road")
	if not CONTEXTS.has(context_id):
		context_id = "road"
	var context: Dictionary = CONTEXTS[context_id]
	var profile_id: String = spawn.get("profile", "")
	if profile_id == "" or not Profiles.has(profile_id):
		profile_id = _pick(context.profiles, unit(seed, "profile"))
	var clothing: Array = context.clothing[int(unit(seed, "clothing") * context.clothing.size()) % context.clothing.size()].duplicate()
	var inventory := {}
	for slot in range(2):
		var id: String = _pick(context.loot, unit(seed, "loot%d" % slot))
		if id != "":
			inventory[id] = int(inventory.get(id, 0)) + 1
	var angle := unit(seed, "facing") * TAU
	return {
		"id": "z%08x" % seed,
		"seed": seed,
		"spawn_key": key,
		"context": context_id,
		"profile": profile_id,
		"position": spawn.get("position", Vector2.ZERO),
		"facing": spawn.get("facing", Vector2.from_angle(angle)),
		"loadout": {"clothing": clothing, "inventory": inventory},
		"gait_phase": unit(seed, "gait"),
	}
