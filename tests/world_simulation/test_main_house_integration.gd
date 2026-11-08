extends SceneTree
## Regression + integration: the real default scene (main.tscn / scripts/house.gd) still boots
## and plays, and the world simulation drives its doors/containers through the adapter with
## collision, visuals (house dictionaries) and persistence in agreement.
## Run: godot --headless --path . --script tests/world_simulation/test_main_house_integration.gd

const Adapter := preload("res://game/world_interactions/house_world_adapter.gd")
const B := preload("res://game/world_simulation/world_bootstrap.gd")
const SAVE := "user://world_sim_test_main_house.json"

var failures: Array = []
var passes := 0


func check(cond: bool, msg: String) -> void:
	if cond:
		passes += 1
	else:
		failures.append(msg)


func _initialize() -> void:
	_run.call_deferred()


func _frames(n: int) -> void:
	for i in n:
		await process_frame


func _spawn_house() -> Node:
	var scene: PackedScene = load(ProjectSettings.get_setting("application/run/main_scene"))
	var house := scene.instantiate()
	root.add_child(house)
	return house


func _run() -> void:
	check(ProjectSettings.get_setting("application/run/main_scene") == "res://main.tscn", "main scene unchanged")
	var house := _spawn_house()
	await _frames(120)
	# --- Existing gameplay regression (behaviour of house.gd on main) ---
	check(house.doors.size() == 5 and house.items.size() == 4, "house has 5 doors and 4 searchables")
	check(house.health > 0.0, "player alive after 120 frames")
	var start: Vector2 = house.player
	house.joystick_touch = 1
	house.joystick_vector = Vector2(0, -1)
	await _frames(20)
	house.joystick_touch = -1
	house.joystick_vector = Vector2.ZERO
	check(house.player != start, "joystick still moves the player")
	house.player = start

	# --- Bind world simulation ---
	var ad = Adapter.new()
	check(ad.bind(house), "adapter binds to house.gd")
	check(ad.world.objects.size() == 9, "9 world objects (5 doors + 4 containers): %d" % ad.world.objects.size())
	var front_mid: Vector2 = (house.doors[0].a + house.doors[0].b) / 2.0
	check(house._blocked(front_mid) and ad.world.collision.point_blocked(front_mid, house.PLAYER_RADIUS), "closed FRONT blocks in both models")

	# Door: open via world -> house collision + visual dictionary agree.
	house.player = front_mid + Vector2(0, 1.0)
	var r: Dictionary = ad.request("open", "door.front")
	check(r.ok, "open FRONT through world: " + str(r.failure_reason))
	check(house.doors[0].open, "house door dictionary shows open")
	check(not house._blocked(front_mid), "house collision lets player through")
	check(not ad.world.collision.point_blocked(front_mid, house.PLAYER_RADIUS), "world collision agrees")
	ad.tick(0.5)
	r = ad.request("close", "door.front")
	check(r.ok and not house.doors[0].open and house._blocked(front_mid), "close syncs back")

	# Legacy breach path inside house.gd is imported into the world.
	house.doors[1].health = 0.0
	house.doors[1].open = true
	ad.pull_from_house()
	var kitchen = ad.world.objects["main_house/door.kitchen"]
	check(kitchen.state.broken, "legacy zombie breach recorded as broken door")
	ad.push_to_house()
	check(house.doors[1].open and house.doors[1].broken, "broken door stays open in house")

	# Container loop: open, search, take into inventory.
	var counter: Dictionary = house.items[0]
	house.player = counter.pos + counter.size / 2.0 + Vector2(0, 0.9)
	check(ad.request("open", "house.kitchen.counter").ok, "open kitchen counter")
	var s: Dictionary = ad.request("search", "house.kitchen.counter")
	check(s.ok and house.items[0].searched, "search marks house item searched")
	var cab = ad.world.objects["main_house/house.kitchen.counter"]
	var before: int = ad.world.storage.total_items(cab)
	var t: Dictionary = ad.request("take", "house.kitchen.counter")
	check(t.ok, "take first item: " + str(t.failure_reason))
	check(ad.world.storage.total_items(cab) == before - 1 and ad.inventory.quantity(t.data.get("item_id", "")) == 1, "item moved, not copied")

	# Contextual one-button interaction picks a sensible verb.
	house.player = front_mid + Vector2(0, 1.0)
	ad.tick(0.5)
	var c: Dictionary = ad.interact_contextual()
	check(c.ok and c.action_id == "open" and house.doors[0].open, "contextual INTERACT opens nearest door")

	# Save, then a brand-new house instance restores the same world state.
	check(ad.save(SAVE) == OK, "world save written")
	house.queue_free()
	ad.dispose()
	await _frames(2)
	var house2 := _spawn_house()
	await _frames(5)
	var ad2 = Adapter.new()
	check(ad2.bind(house2), "rebind on fresh house")
	check(not house2.doors[0].open, "fresh house starts closed")
	check(ad2.load_save(SAVE) == "", "load world save")
	check(house2.doors[0].open, "FRONT open restored into house.gd")
	check(house2.doors[1].broken and house2.doors[1].open, "breach restored")
	check(house2.items[0].searched, "searched container restored")
	var cab2 = ad2.world.objects["main_house/house.kitchen.counter"]
	check(ad2.world.storage.total_items(cab2) == before - 1, "container contents restored (no reroll, no dup)")

	# Legacy PR #25 save migration: searched containers can never reroll.
	var ad3 = Adapter.new()
	ad3.bind(house2)
	check(ad3.import_legacy_containers({"house.bedroom.bed": true, "house.living.sofa": false}) == 1, "legacy container map migrated")
	var bed = ad3.world.objects["main_house/house.bedroom.bed"]
	check(bed.state.loot_initialized and ad3.world.storage.total_items(bed) == 0, "legacy-searched bed stays empty")

	await _frames(60)
	check(house2.health > 0.0, "game keeps running after integration")
	DirAccess.remove_absolute(ProjectSettings.globalize_path(SAVE))
	DirAccess.remove_absolute(ProjectSettings.globalize_path(SAVE + ".bak"))
	ad2.dispose()
	ad3.dispose()
	house2.queue_free()
	B.release_shared()
	await _frames(2)
	print("MAIN_HOUSE_INTEGRATION passed_checks=%d failed_checks=%d" % [passes, failures.size()])
	for f in failures:
		print("  FAILED: " + f)
	quit(0 if failures.is_empty() else 1)
