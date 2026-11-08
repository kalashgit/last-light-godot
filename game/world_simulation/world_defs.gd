extends RefCounted
## Immutable world-object archetypes, item weights and loot profiles.
## Loaded once, validated, then treated as read-only. Instances never write here.

const DEFINITIONS_PATH := "res://data/world_objects/definitions_v1.json"
const ITEMS_PATH := "res://data/world_objects/item_refs_v1.json"
const LOOT_PATH := "res://data/world_objects/loot_profiles_v1.json"

## Every capability the runtime understands. Anything else is a validation error.
const KNOWN_CAPABILITIES := [
	"openable", "lockable", "barricadable", "destructible", "glass", "storage", "movable",
	"power_consumer", "power_switch", "breaker_panel", "generator", "fuel_storage", "thermal",
	"room_climate", "water_fixture", "water_storage",
]

var definitions: Dictionary = {}
var item_weights: Dictionary = {}
var loot_profiles: Dictionary = {}
var errors: PackedStringArray = []


func load_default() -> bool:
	return load_from(DEFINITIONS_PATH, ITEMS_PATH, LOOT_PATH)


func load_from(defs_path: String, items_path: String, loot_path: String) -> bool:
	errors.clear()
	definitions.clear()
	item_weights.clear()
	loot_profiles.clear()
	var items = _read_json(items_path)
	if items is Dictionary and items.get("items") is Array:
		for raw in items["items"]:
			if raw is Dictionary and raw.get("id") is String:
				item_weights[raw["id"]] = float(raw.get("weight_kg", 0.0))
	else:
		errors.append("item refs unreadable: " + items_path)
	var loot = _read_json(loot_path)
	if loot is Dictionary and loot.get("profiles") is Dictionary:
		loot_profiles = loot["profiles"]
	else:
		errors.append("loot profiles unreadable: " + loot_path)
	var parsed = _read_json(defs_path)
	if not parsed is Dictionary or parsed.get("schema_version") != 1.0 or not parsed.get("definitions") is Array:
		errors.append("definitions unreadable or wrong schema: " + defs_path)
		return false
	for raw in parsed["definitions"]:
		if not raw is Dictionary or not raw.get("definition_id") is String:
			errors.append("definition without definition_id")
			continue
		var id: String = raw["definition_id"]
		if definitions.has(id):
			errors.append("duplicate definition_id " + id)
			continue
		definitions[id] = raw
	validate()
	return errors.is_empty()


## Static integrity checks (Notion gate A1). Collects every problem rather than stopping at the first.
func validate() -> void:
	for id in definitions:
		var d: Dictionary = definitions[id]
		var caps = d.get("capabilities", [])
		var comps = d.get("components", {})
		var fp = d.get("footprint", {})
		if not fp is Dictionary or not fp.get("kind") in ["edge", "cells"] or not fp.get("size") is Array:
			errors.append(id + ": footprint must be edge|cells with size")
		for cap in caps:
			if not cap in KNOWN_CAPABILITIES:
				errors.append(id + ": unknown capability " + str(cap))
			if cap in ["storage", "movable", "destructible", "generator", "thermal", "water_fixture", "water_storage", "breaker_panel", "barricadable", "fuel_storage", "power_consumer", "room_climate"] and not comps.has(cap):
				errors.append(id + ": capability " + cap + " has no component data")
		for action in d.get("actions", []):
			var spec = ACTION_REQUIREMENTS.get(action)
			if spec == null:
				errors.append(id + ": action " + str(action) + " is not implemented")
				continue
			var ok := false
			for cap in spec:
				if cap in caps:
					ok = true
			if spec.is_empty():
				ok = true
			if not ok:
				errors.append(id + ": action " + action + " lacks capability " + str(spec))
		if "storage" in caps:
			var storage: Dictionary = comps["storage"]
			var profile: String = storage.get("loot_profile", "empty")
			if not loot_profiles.has(profile):
				errors.append(id + ": unknown loot profile " + profile)
			if not storage.get("compartments") is Array or storage["compartments"].is_empty():
				errors.append(id + ": storage needs compartments")
			else:
				for comp in storage["compartments"]:
					if comp.has("loot_profile") and not loot_profiles.has(comp["loot_profile"]):
						errors.append(id + ": unknown compartment loot profile " + str(comp["loot_profile"]))
			if storage.get("door_gated", false) and not "openable" in caps:
				errors.append(id + ": door_gated storage must be openable")
		if "lockable" in caps and not "openable" in caps:
			errors.append(id + ": lockable requires openable")
		if "glass" in caps and fp.get("kind") != "edge":
			errors.append(id + ": glass objects must be edge objects")
	for profile_id in loot_profiles:
		for entry in loot_profiles[profile_id].get("entries", []):
			if not item_weights.has(entry.get("item")):
				errors.append("loot " + profile_id + " references unknown item " + str(entry.get("item")))
			if float(entry.get("weight", 0)) <= 0.0:
				errors.append("loot " + profile_id + " has non-positive weight")


## action -> capabilities, any one of which allows the action. Mirrors interaction_system.gd.
const ACTION_REQUIREMENTS := {
	"inspect": [],
	"open": ["openable"], "close": ["openable"],
	"lock": ["lockable"], "unlock": ["lockable"],
	"barricade": ["barricadable"], "unbarricade": ["barricadable"],
	"smash": ["glass"], "repair": ["destructible"],
	"search": ["storage"], "take": ["storage"], "put": ["storage"],
	"move": ["movable"],
	"switch_on": ["power_switch"], "switch_off": ["power_switch"],
	"connect": ["power_consumer", "generator"], "disconnect": ["power_consumer", "generator"],
	"toggle_breaker": ["breaker_panel"],
	"start": ["generator"], "stop": ["generator"], "refuel": ["generator"],
	"fill": ["water_fixture", "water_storage"], "drink": ["water_fixture", "water_storage"],
	"use": ["water_fixture"], "pour": ["water_storage"], "drain": ["water_storage"], "treat": ["water_storage"],
}


func get_def(id: String) -> Dictionary:
	return definitions.get(id, {})


func has_cap(def_id: String, cap: String) -> bool:
	return cap in definitions.get(def_id, {}).get("capabilities", [])


func component(def_id: String, cap: String) -> Dictionary:
	return definitions.get(def_id, {}).get("components", {}).get(cap, {})


func weight_of(item_id: String) -> float:
	return float(item_weights.get(item_id, -1.0))


func _read_json(path: String) -> Variant:
	if not FileAccess.file_exists(path):
		return null
	return JSON.parse_string(FileAccess.get_file_as_string(path))
