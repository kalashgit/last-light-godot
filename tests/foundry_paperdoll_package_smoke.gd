extends SceneTree
## Real Godot test: Python-packaged original transparent layers -> verified atlases -> paperdoll.
const ACTOR = preload("res://scripts/foundry_paperdoll.gd")
const LOADER = preload("res://scripts/foundry_paperdoll_package.gd")
const FOLDER := "res://build/paperdoll_package"

var failures: Array[String] = []
var assertions := 0


func check(ok: bool, description: String) -> void:
	assertions += 1
	if not ok:
		failures.append(description)
		push_error("LL_PAPERDOLL_E2E_FAIL: " + description)


func _init() -> void:
	call_deferred("_run")


func _run() -> void:
	var environment := Node2D.new()
	environment.name = "LayeredActorWorld"
	environment.y_sort_enabled = true
	root.add_child(environment)
	var actor = ACTOR.new()
	actor.position = Vector2(150, 190)
	environment.add_child(actor)
	var equip := {"body": "base", "pants": "jeans", "shirt": "green_shirt", "backpack": "pack"}
	var installed: bool = LOADER.install_package(actor, FOLDER, equip)
	check(installed, "verified atlas install")
	if not installed:
		print("LL_PAPERDOLL_PACKAGE_E2E_ABORT: catalog installation rejected before any layer exists")
		quit(2)
		return
	actor.set_process(false)
	check(actor.equipped_id("body") == "base", "original body ID")
	check(actor.equipped_id("shirt") == "green_shirt", "original shirt ID")
	check(actor.get_child_count() == 4, "four independently composited slots")
	check(actor.layer("body").get_index() < actor.layer("shirt").get_index(), "fixed body/shirt order")
	check(environment.y_sort_enabled and not actor.y_sort_enabled, "actor sorted by ground point")
	check(actor.layer("body").position == Vector2(0, -20), "identical world pivot")

	check(actor.play_anim("walk", 7), "8-heading walk accepted")
	check(actor.seek_frame(2), "animation third frame")
	for slot in ["body", "pants", "shirt", "backpack"]:
		var layer: Sprite2D = actor.layer(slot)
		check(layer.visible, slot + " visible after install")
		check(layer.region_rect == Rect2(64, 336, 32, 48), slot + " exact 8-heading third-frame coordinates")
	var old_coat: Texture2D = actor.layer("shirt").texture
	check(actor.equip("shirt", "blue_shirt"), "swap preverified clothing without rerender")
	check(actor.layer("shirt").texture != old_coat, "new garment texture applied")
	check(actor.layer("body").texture != null, "base remains after shirt swap")
	var before := actor.snapshot_state()
	check(actor.equip("backpack", ""), "optional backpack removed")
	check(not actor.layer("backpack").visible, "backpack hidden")
	check(actor.restore_state(before), "inventory/restored equipment")
	check(actor.layer("backpack").visible, "re-equipped backpack visible")

	var invalid_snapshot := before.duplicate(true)
	invalid_snapshot["equipped"]["shirt"] = "missing_shirt"
	check(not actor.restore_state(invalid_snapshot), "nonexistent wearable save rejected")
	check(actor.equipped_id("shirt") == "blue_shirt", "failed restore is atomic")

	check(not LOADER.install_package(actor, FOLDER + "/../escape", equip), "path escape rejected")
	var invalid_items := equip.duplicate()
	invalid_items["shirt"] = "does_not_exist"
	check(not LOADER.install_package(actor, FOLDER, invalid_items), "unknown item rejected")
	check(actor.equipped_id("shirt") == "blue_shirt", "failed import cannot mutate live actor")

	environment.queue_free()
	if failures.is_empty():
		print("LL_PAPERDOLL_PACKAGE_GODOT_PASS assertions=", assertions,
		      " original layered candidate, verified hashes, 8 headings, inventory swapping")
		quit(0)
	else:
		print("LL_PAPERDOLL_PACKAGE_GODOT_FAIL assertions=", assertions, " defects=", failures)
		quit(2)
