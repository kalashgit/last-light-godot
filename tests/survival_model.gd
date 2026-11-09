extends SceneTree

const Model = preload("res://scripts/survival_state.gd")
const BEANS := "ll_food_bean_tin"
const WATER := "ll_food_water_bottle"
const BANDAGE := "ll_medical_sterile_bandage"
const HAMMER := "ll_tools_claw_hammer"
const PLANK := "ll_crafting_pine_plank"

var failures: Array[String] = []
var checks: int = 0


func _initialize() -> void:
	var model = Model.new()
	check(model.definitions.size() == 48, "eight original items plus forty Golden 40 test items")
	var manifest: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://assets/generated/factory/manifest.json"))
	var art_ids: Dictionary = {}
	for entry: Dictionary in manifest["objects"]:
		art_ids[entry["id"]] = true
	for id: String in [BEANS, WATER, BANDAGE, HAMMER, PLANK, "ll_medical_first_aid_case", "ll_tools_hatchet", "ll_household_flashlight"]:
		check(art_ids.has(model.definitions[id]["art_id"]), "factory art reference " + id)
		check(model.definitions[id]["id"] == id, "stable definition ID " + id)
	check(model.add(BEANS, 2), "add beans")
	check(model.add(BEANS, 1) and model.inventory[BEANS] == 3, "merge stacks")
	for bad: Variant in [-1, 0, 1.5, NAN, INF, true, "1", null, 1000000000]:
		check(not model.add(BEANS, bad), "reject invalid add " + str(bad))
		check(not model.remove(BEANS, bad), "reject invalid remove " + str(bad))
	check(not model.add("unknown", 1), "reject unknown ID")
	check(not model.add(BEANS, 20), "enforce stack limit")
	check(not model.remove(BEANS, 4), "reject excess removal")
	check(model.add(HAMMER) and model.equip(HAMMER), "equip owned weapon")
	check(model.action(HAMMER) == "Unequip", "equipped weapon action")
	check(not model.equip(BEANS), "food cannot equip")
	check(not model.equip("ll_tools_hatchet"), "cannot equip absent weapon")
	check(model.action(BEANS) == "Eat", "food action")
	check(model.consume(BEANS) == {"kind": "food", "amount": 28.0}, "food effect")
	check(model.inventory[BEANS] == 2, "consume exactly one")
	check(model.consume(HAMMER).is_empty() and model.inventory[HAMMER] == 1, "weapon is not consumable")
	check(model.add(WATER) and model.consume(WATER) == {"kind": "drink", "amount": 35.0}, "drink effect")
	check(model.add(BANDAGE) and model.consume(BANDAGE) == {"kind": "heal", "amount": 22.0}, "bandage effect")
	check(not model.inventory.has(WATER) and not model.inventory.has(BANDAGE), "consumed final items removed")
	var before: Dictionary = model.snapshot()
	var separate: Dictionary = model.snapshot()
	separate["inventory"][BEANS] = 10
	check(model.inventory[BEANS] == 2, "snapshot has independent storage")
	var invalids: Array = [
		{}, {"inventory": {}, "equipped": "", "extra": 1},
		{"inventory": {BEANS: 0}, "equipped": ""},
		{"inventory": {BEANS: -1}, "equipped": ""},
		{"inventory": {BEANS: 1.5}, "equipped": ""},
		{"inventory": {BEANS: NAN}, "equipped": ""},
		{"inventory": {BEANS: INF}, "equipped": ""},
		{"inventory": {BEANS: true}, "equipped": ""},
		{"inventory": {"unknown": 1}, "equipped": ""},
		{"inventory": {BEANS: 21}, "equipped": ""},
		{"inventory": {BEANS: 1}, "equipped": BEANS},
		{"inventory": {}, "equipped": HAMMER},
		{"inventory": [], "equipped": ""},
		{"inventory": {}, "equipped": 1},
		{"inventory": {PLANK: 10, BEANS: 20}, "equipped": ""}
	]
	for state: Variant in invalids:
		check(not model.validate(state), "reject invalid saved inventory")
		check(not model.restore(state) and model.snapshot() == before, "failed restore is atomic")
	var encoded: String = JSON.stringify(before)
	check(model.restore(JSON.parse_string(encoded)) and model.snapshot() == before, "JSON save round trip")
	model.definitions[BEANS]["art_id"] = "reskinned_bean_tin"
	check(model.snapshot() == before and model.name_for(BEANS) == "Bean tin", "changing art preserves gameplay identity")
	check(model.rows().size() == 2 and model.rows()[0].has_all(["id", "name", "count", "action"]), "inventory UI rows")
	check(model.remove(HAMMER) and model.equipped == "", "last equipped weapon removal clears equipment")
	check(model.equip(""), "bare hands supported")
	var heavy = Model.new()
	check(heavy.add(PLANK, 10) and heavy.add(WATER, 9), "weight below capacity")
	check(not heavy.add(WATER) and heavy.total_weight() <= 20.0, "reject overweight addition")
	print("SURVIVAL_MODEL: %d checks, %d failures" % [checks, failures.size()])
	for failure: String in failures:
		printerr("FAIL: " + failure)
	quit(0 if failures.is_empty() else 1)


func check(condition: bool, label: String) -> void:
	checks += 1
	if not condition:
		failures.append(label)
