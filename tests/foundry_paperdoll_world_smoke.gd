extends SceneTree
## Real LAST LIGHT main.tscn compatibility fixture for verified paperdoll atlases.
## Headless simulation of 100 noncanonical actors; NOT a visual/phone GPU benchmark.
const ACTOR = preload("res://scripts/foundry_paperdoll.gd")
const IMPORTER = preload("res://scripts/foundry_paperdoll_package.gd")
const PACKAGE_DIR := "res://build/paperdoll_package"

var failures: Array[String] = []
var assertions := 0


func check(ok: bool, message: String) -> void:
	assertions += 1
	if not ok:
		failures.append(message)
		push_error("LL_PAPERDOLL_WORLD_FAIL: " + message)


func _init() -> void:
	call_deferred("_run")


func _run() -> void:
	var packed := load("res://main.tscn") as PackedScene
	check(packed != null, "main gameplay scene loads")
	if packed == null:
		quit(2)
		return
	var game = packed.instantiate()
	root.add_child(game)
	game.set_process(false)
	# The canonical main.tscn is currently house.gd's single-house slice.
	# Its _ready() initializes the five door records on add_child().
	check(game.doors.size() >= 5, "single-house world door graph initialized")
	var world := Node2D.new()
	world.name = "TechnicalPaperdollOverlay_YSorted"
	world.y_sort_enabled = true
	game.add_child(world)

	var inventory = {"body": "base", "pants": "jeans",
	                 "shirt": "green_shirt", "backpack": "pack"}
	var first = ACTOR.new()
	world.add_child(first)
	var accepted: bool = IMPORTER.install_package(first, PACKAGE_DIR, inventory)
	check(accepted, "verified layered character imported into playable game")
	if not accepted:
		quit(2)
		return
	first.set_process(false)
	first.position = game._screen(game.player, 0.0)
	check(first.position.is_finite(), "world to screen projection finite")
	check(world.y_sort_enabled and not first.y_sort_enabled,
	      "actor layer sorting remains subordinate to native world Y sort")

	var from: Vector2 = game._screen(game.player + Vector2(0.25, 0.25), 0.0)
	var to: Vector2 = game._screen(game.player + Vector2(0.65, 0.25), 0.0)
	var delta_pixels: float = from.distance_to(to)
	check(delta_pixels > 5 and delta_pixels < 50,
	      "actor movement projects onto calibrated 80x40 isometric world")
	check(first.play_anim("walk", 0), "front walk works inside playable game")
	first.advance(0.26)
	check(first.frame == 2, "real world walking animation advances shared outfit")
	check(first.equip("shirt", "blue_shirt"), "real world garment swaps");
	check(first.layer("shirt").visible, "new garment remains visible")

	# Door collision correctness is inherited from the untouched canonical map.
	if game.doors.size() > 0:
		var original_open: bool = bool(game.doors[0].open)
		game.doors[0].open = false
		var blocked: Vector2 = game._try_move(Vector2(5.4, 8.5), Vector2(0, -1), 0.19)
		game.doors[0].open = true
		var traversed: Vector2 = game._try_move(Vector2(5.4, 8.5), Vector2(0, -1), 0.19)
		check(blocked.y > traversed.y, "door open/close traversal not regressed")
		game.doors[0].open = original_open

	var actors: Array = [first]
	for i in range(1, 100):
		var actor = ACTOR.new()
		actor.position = game._screen(game.player + Vector2(i % 12, i / 12), 0.0)
		world.add_child(actor)
		if not IMPORTER.install_package(actor, PACKAGE_DIR, inventory):
			check(false, "shared manifest imported into actor " + str(i))
			break
		actor.set_process(false)
		actor.play_anim("walk", i % 8)
		actors.append(actor)
	check(actors.size() == 100, "100 candidate actors spawned from one atlas library")
	for actor in actors:
		actor.advance(0.125)
	check(actors.size() == 100 and actors[99].layer("body").texture != null,
	      "100 actors retain shared animation layers")
	check(actors[0].z_index == 0 and actors[99].z_index == 0,
	      "actor roots preserve Y-sorting with no global Z override")

	var state: Dictionary = first.snapshot_state()
	var json_roundtrip = JSON.parse_string(JSON.stringify(state))
	check(json_roundtrip is Dictionary and first.restore_state(json_roundtrip),
	      "real game staged clothing/inventory save round-trip")

	game.queue_free()
	if failures.is_empty():
		print("LL_PAPERDOLL_WORLD_PASS assertions=", assertions,
		      " characters=", actors.size(),
		      " scope=playable-main-scene-plus-headless-100-actor-simulation",
		      " golden=false iphone_fps_unverified=true")
		quit(0)
	else:
		print("LL_PAPERDOLL_WORLD_FAIL assertions=", assertions,
		      " characters=", actors.size(), " defects=", failures)
		quit(2)
