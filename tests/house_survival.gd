extends SceneTree
## Independent integration tests against the actual playable main scene.
## Synthetic Godot touch events exercise ownership; they do not verify device hardware.

const BEANS := "ll_food_bean_tin"
const WATER := "ll_food_water_bottle"
const BANDAGE := "ll_medical_sterile_bandage"
const HAMMER := "ll_tools_claw_hammer"
const PLANK := "ll_crafting_pine_plank"
var checks := 0
var failures: Array[String] = []
var game


func _initialize() -> void:
	call_deferred("run")


func check(condition: bool, label: String) -> void:
	checks += 1
	if not condition:
		failures.append(label)
		printerr("FAIL: " + label)


func touch(index: int, point: Vector2, pressed: bool, canceled: bool = false) -> void:
	var event := InputEventScreenTouch.new()
	event.index = index
	event.position = point
	event.pressed = pressed
	event.canceled = canceled
	game._input(event)


func drag(index: int, point: Vector2) -> void:
	var event := InputEventScreenDrag.new()
	event.index = index
	event.position = point
	game._input(event)


func simulate(seconds: float, fps: int = 60) -> void:
	for frame in range(roundi(seconds * fps)):
		game._process(1.0 / float(fps))


func fresh() -> void:
	game._restart_game()
	game.set_process(false)
	game.player = Vector2(-4, -4)
	for index in range(game.zombie_health.size()):
		game.zombie_health[index] = 0
	game._layout_controls()


func button(name: String) -> Vector2:
	return (game.control_rects[name] as Rect2).get_center()


func state() -> Dictionary:
	var door_states: Array = []
	var searched: Array = []
	for door: Dictionary in game.doors:
		door_states.append({"open": door.open, "health": door.health})
	for item: Dictionary in game.items:
		searched.append(item.searched)
	return {
		"player": game.player, "health": game.health, "stamina": game.stamina,
		"hunger": game.hunger, "thirst": game.thirst, "supplies": game.supplies,
		"survival": game.survival.snapshot(), "doors": door_states,
		"searched": searched, "drops": game.drops.duplicate(true),
		"infected": game.infected.duplicate(), "zombie_health": game.zombie_health.duplicate(),
	}


func test_controls() -> void:
	fresh()
	for name: String in ["attack", "interact", "shove", "sprint", "sneak", "inventory", "pause", "quick0", "quick1", "quick2", "quick3"]:
		check(game.control_rects.has(name), "HUD exposes actual " + name + " target")
		if game.control_rects.has(name):
			var rect: Rect2 = game.control_rects[name]
			check(Rect2(Vector2.ZERO, game.get_viewport_rect().size).encloses(rect), "HUD target on screen: " + name)
	var old_dead_zone: float = game.joystick_dead_zone
	game.joystick_dead_zone = .2
	touch(0, game.stick_center + Vector2(game.stick_radius * .1, 0), true)
	check(game.joystick_vector == Vector2.ZERO, "configurable joystick dead zone suppresses drift")
	drag(0, game.stick_center + Vector2(game.stick_radius * 4, 0))
	check(is_equal_approx(game.joystick_vector.length(), 1.0), "circular analog movement clamps outside stick")
	touch(1, button("sprint"), true)
	touch(2, button("attack"), true)
	check(game.joystick_touch == 0 and game.sprint_held and game.attack_cooldown > 0, "three simultaneous fingers preserve move, sprint and attack")
	var after_attack: float = game.stamina
	touch(2, button("attack"), true)
	check(game.stamina == after_attack, "duplicate press cannot repeat attack")
	var position: Vector2 = game.player
	simulate(.2)
	check(game.player.distance_to(position) > .1 and game.sprinting and game.stamina < after_attack, "held sprint moves and consumes live stamina")
	var mouse := InputEventMouseButton.new()
	mouse.device = InputEvent.DEVICE_ID_EMULATION
	mouse.button_index = MOUSE_BUTTON_LEFT
	mouse.position = game.stick_center
	mouse.pressed = true
	game._input(mouse)
	check(game.joystick_touch == 0, "emulated mouse cannot steal real touch ownership")
	touch(1, Vector2(-100, -100), false)
	check(not game.sprint_held and game.joystick_touch == 0, "release outside screen ends sprint and preserves stick")
	touch(2, Vector2.ZERO, false)
	check(game.joystick_touch == 0, "unrelated release preserves movement")
	touch(0, Vector2.ZERO, false, true)
	check(game.joystick_touch == -1 and game.joystick_vector == Vector2.ZERO, "canceled owner clears stick")
	game.joystick_dead_zone = old_dead_zone
	touch(3, game.stick_center + Vector2(game.stick_radius, 0), true)
	touch(4, button("sprint"), true)
	game._set_inventory(true)
	var frozen := state()
	simulate(.5)
	check(game.inventory_open and game.paused and game.joystick_touch == -1 and not game.sprint_held, "inventory clears held pointers and pauses")
	check(state() == frozen, "inventory freezes movement, zombies and survival clocks")
	touch(5, button("attack"), true)
	check(state() == frozen, "action touch behind inventory cannot affect game")
	game._set_inventory(false)
	check(not game.inventory_open and not game.paused and game.joystick_vector == Vector2.ZERO, "closing inventory resumes without stuck movement")
	touch(6, game.stick_center + Vector2(game.stick_radius, 0), true)
	game._notification(Node.NOTIFICATION_APPLICATION_FOCUS_OUT)
	check(game.paused and game.joystick_touch == -1 and game.panel_touches.is_empty(), "focus loss clears all touch ownership and pauses")
	game._set_paused(false)
	print("HOUSE_SURVIVAL: control checks finished")


func movement_distance(fps: int, sprint: bool = false, sneak: bool = false) -> float:
	fresh()
	# This diagonal stays clear of the house and the bounded yard for both speeds.
	game.player = Vector2(-4, 2)
	game.sneaking = sneak
	touch(42, game.stick_center + Vector2(game.stick_radius, 0), true)
	if sprint:
		touch(43, button("sprint"), true)
	var before: Vector2 = game.player
	simulate(2.0, fps)
	return game.player.distance_to(before)


func test_movement_and_geometry() -> void:
	var walk_30 := movement_distance(30)
	var walk_60 := movement_distance(60)
	var walk_120 := movement_distance(120)
	check(absf(walk_30 - walk_60) < .01 and absf(walk_120 - walk_60) < .01, "two-second movement parity at 30/60/120 fps")
	check(walk_60 > 4.0 and walk_60 < 5.0, "walk travels plausible existing two-tile-per-second distance")
	var sprint := movement_distance(60, true)
	check(sprint > walk_60 * 1.25 and game.stamina < 100, "sprint is meaningfully faster and spends stamina")
	var sneak := movement_distance(60, false, true)
	check(sneak < walk_60 * .8 and sneak > 0, "sneak is slower than walk")
	game.joystick_touch = -1
	game.joystick_vector = Vector2.ZERO
	var facing: Vector2 = game.facing
	simulate(.2)
	check(game.facing == facing, "facing remains stable when movement stops")
	game.sneaking = false
	game.stamina = 40.0
	simulate(2.0)
	check(game.stamina > 40 and game.stamina <= 100, "rest regenerates stamina")
	fresh()
	for index in range(game.doors.size()):
		var door: Dictionary = game.doors[index]
		var center: Vector2 = (door.a + door.b) * .5
		var tangent: Vector2 = (door.b - door.a).normalized()
		var normal := Vector2(-tangent.y, tangent.x)
		var start := center + normal * .7
		var goal := center - normal * .7
		door.open = false
		var closed: Vector2 = game._try_move(start, goal - start, .19)
		check(closed.distance_to(goal) > .3, "closed doorway blocks traversal: " + door.label)
		door.open = true
		var opened: Vector2 = game._try_move(start, goal - start, .19)
		check(opened.distance_to(goal) < .04, "furniture leaves full doorway traversable: " + door.label)
		game.player = center
		game._toggle_door(index)
		check(door.open, "occupied doorway cannot close: " + door.label)
	game.player = Vector2(-4, -4)
	for item: Dictionary in game.items:
		if item.get("solid", true):
			check(game._blocked(item.pos + item.size * .5, .19), "solid furniture has collision: " + item.name)
	var slide: Vector2 = game._try_move(Vector2(-.31, 2), Vector2(.6, .8), .19)
	check(slide.x < -.27 and slide.y > 2.5, "movement slides along wall without penetrating")
	print("HOUSE_SURVIVAL: movement/collision checks finished; distances ", [walk_30, walk_60, walk_120, sprint, sneak])


func test_combat_and_zombies() -> void:
	fresh()
	game.facing = Vector2.RIGHT
	game.infected[0] = game.player + Vector2(.8, 0)
	game.infected[1] = game.player - Vector2(.8, 0)
	game.zombie_health = [3, 3]
	game._attack()
	check(game.zombie_health[0] < 3 and game.zombie_health[1] == 3, "melee facing hits ahead and excludes enemy behind")
	check(game.zombies_hit_time[0] > 0 and game.stamina < 100, "melee gives hit reaction and costs stamina")
	var life: int = game.zombie_health[0]
	var stamina: float = game.stamina
	game._attack()
	check(game.zombie_health[0] == life and game.stamina == stamina, "melee cooldown prevents duplicate hit and cost")
	game.god_mode = true
	game.attack_cooldown = 0
	touch(10, button("attack"), true)
	var held_life: int = game.zombie_health[0]
	simulate(1.0)
	check(game.zombie_health[0] == held_life, "holding one attack finger past cooldown does not auto-repeat")
	touch(10, Vector2.ZERO, false)
	fresh()
	game.player = Vector2(2, 3.7)
	game.facing = Vector2.DOWN
	game.infected[0] = Vector2(2, 4.3)
	game.zombie_health[0] = 3
	game._attack()
	check(game.zombie_health[0] == 3, "interior wall blocks melee hit")
	fresh()
	game.facing = Vector2.RIGHT
	game.infected[0] = game.player + Vector2(.8, 0)
	game.zombie_health[0] = 3
	game.stamina = 0
	game._attack()
	check(game.zombie_health[0] == 3, "exhaustion prevents free melee damage")
	game.stamina = 100
	game.attack_cooldown = 0
	var before_distance: float = game.player.distance_to(game.infected[0])
	game._shove()
	check(game.player.distance_to(game.infected[0]) > before_distance and game.zombie_health[0] == 3, "shove creates space without weapon damage")
	check(game.stamina < 100 and game.zombies_hit_time[0] > 0, "shove has stamina cost and feedback")
	fresh()
	game.infected[0] = game.player + Vector2(.4, 0)
	game.zombie_health[0] = 3
	simulate(.5)
	check(game.health < 100, "nearby unobstructed zombie damages player")
	fresh()
	game.god_mode = true
	game.player = Vector2(5.4, 7.2)
	game.infected[0] = Vector2(5.4, 8.65)
	game.zombie_health[0] = 3
	game.doors[0].open = false
	simulate(12)
	check(game.doors[0].open and game.doors[0].health <= 0, "pursuing zombie breaches closed front door")
	check(game.infected[0].y < 8, "zombie crosses doorway after breaching")
	fresh()
	game.god_mode = true
	game.player = Vector2(3, 5)
	game.infected[0] = Vector2(.6, 7.6)
	game.zombie_health[0] = 3
	for door: Dictionary in game.doors:
		door.open = true
	var penetration := false
	for frame in range(1200):
		game._process(1.0 / 60.0)
		if game._blocked(game.infected[0], .17):
			penetration = true
	check(not penetration, "zombie pursuit never penetrates solid walls/furniture")
	check(game.player.distance_to(game.infected[0]) < .9, "bounded navigation reaches player around room furniture")
	var zombie_positions: Array[Vector2] = []
	for fps in [30, 60, 120]:
		fresh()
		game.god_mode = true
		game.player = Vector2(-4, 2)
		game.infected[0] = Vector2(-4, 6)
		game.zombie_health[0] = 3
		simulate(2, fps)
		zombie_positions.append(game.infected[0])
	check(zombie_positions[0].distance_to(zombie_positions[1]) < .02 and zombie_positions[1].distance_to(zombie_positions[2]) < .02, "zombie pursuit parity at 30/60/120 fps")
	check(zombie_positions[1].distance_to(Vector2(-4, 6)) > 1.2, "zombie parity fixture actually pursues over meaningful distance")
	print("HOUSE_SURVIVAL: combat/zombie checks finished")


func test_inventory_and_survival() -> void:
	fresh()
	game.player = Vector2(2.8, 1.9)
	game.selected_target = {"kind": "container", "index": 0}
	check(game._resolve_target() == game.selected_target, "explicit usable selected container wins targeting")
	check("Search" in game._context_prompt(), "context prompt describes searchable container")
	game._interact()
	check(game.items[0].searched and not game.survival.inventory.is_empty(), "search transfers real items into inventory")
	var contents: Dictionary = game.survival.snapshot()
	game._interact()
	check(game.survival.snapshot() == contents, "searched container cannot duplicate loot")
	game.player = Vector2(5.4, 8.8)
	game.selected_target = {"kind": "door", "index": 0}
	check("Open" in game._context_prompt(), "context follows selected closed door")
	game._interact()
	check(game.doors[0].open and "Close" in game._context_prompt(), "context changes after door opens")
	game.selected_target = {"kind": "container", "index": 999}
	check(game._resolve_target().get("kind") == "door", "invalid explicit target falls back to valid nearby target")
	game.player = Vector2(-4, -4)
	game.selected_target = {}
	check(game._resolve_target().is_empty(), "no nearby object yields no invented interaction")
	game.survival.inventory.clear()
	game.survival.add(BEANS, 2)
	game.survival.add(WATER, 2)
	game.survival.add(BANDAGE, 2)
	game.survival.add(HAMMER)
	game.hunger = 60
	game.thirst = 60
	game.health = 50
	check(game._use_item(BEANS) and game.hunger < 60 and game.survival.inventory[BEANS] == 1, "eat consumes one food and reduces hunger")
	check(game._use_item(WATER) and game.thirst < 60 and game.survival.inventory[WATER] == 1, "drink consumes one water and reduces thirst")
	check(game._use_item(BANDAGE) and game.health > 50 and game.health <= 100, "bandage consumes medical item and heals")
	check(game._use_item(HAMMER) and game.survival.equipped == HAMMER, "supported tool equips from inventory")
	var identity: Dictionary = game.survival.snapshot()
	var original_art: String = game.survival.definitions[HAMMER].art_id
	game.survival.definitions[HAMMER].art_id = "test_visual_swap_only"
	check(game.survival.snapshot() == identity and game.survival.equipped == HAMMER, "visual change preserves gameplay identity and equipment")
	game.survival.definitions[HAMMER].art_id = original_art
	touch(12, button("quick0"), true)
	touch(12, Vector2.ZERO, false)
	check(game.survival.equipped.is_empty(), "weapon quick slot switches equipped tool to hands")
	touch(12, button("quick0"), true)
	touch(12, Vector2.ZERO, false)
	check(game.survival.equipped == HAMMER, "weapon quick slot equips supported owned weapon")
	check(game._drop_item(HAMMER) and not game.survival.inventory.has(HAMMER) and game.survival.equipped.is_empty(), "drop removes owned equipped item safely")
	check(game.drops.size() == 1 and game.drops[0].id == HAMMER and not game._blocked(game.drops[0].pos, .1), "dropped object has stable identity and accessible location")
	game.selected_target = {"kind": "drop", "index": 0}
	check("Pick" in game._context_prompt(), "drop produces actual pickup prompt")
	game._interact()
	check(game.drops.is_empty() and game.survival.inventory.has(HAMMER), "pickup restores dropped object without duplication")
	game.health = 100
	var bandages: int = game.survival.inventory.get(BANDAGE, 0)
	touch(13, button("quick1"), true)
	touch(13, Vector2.ZERO, false)
	check(game.survival.inventory.get(BANDAGE, 0) == bandages, "medical quick slot preserves bandage at full health")
	game.health = 65
	touch(13, button("quick1"), true)
	touch(13, Vector2.ZERO, false)
	check(game.health > 65 and game.survival.inventory.get(BANDAGE, 0) == bandages - 1, "medical quick slot applies one available bandage")
	game.thirst = 60
	var waters: int = game.survival.inventory.get(WATER, 0)
	touch(14, button("quick3"), true)
	touch(14, Vector2.ZERO, false)
	check(game.thirst < 60 and game.survival.inventory.get(WATER, 0) == waters - 1, "food/water quick slot drinks when thirsty")
	game.thirst = 0
	game.hunger = 60
	var foods: int = game.survival.inventory.get(BEANS, 0)
	touch(14, button("quick3"), true)
	touch(14, Vector2.ZERO, false)
	check(game.hunger < 60 and game.survival.inventory.get(BEANS, 0) == foods - 1, "food/water quick slot eats when hungry and not thirsty")
	var utility_before := state()
	touch(15, button("quick2"), true)
	touch(15, Vector2.ZERO, false)
	check(state() == utility_before, "unimplemented utility quick slot cannot alter gameplay")
	var before: Dictionary = game.survival.snapshot()
	check(not game._use_item("unknown") and not game._drop_item("unknown") and game.survival.snapshot() == before, "unknown item actions cannot mutate inventory")
	var hunger: float = game.hunger
	var thirst: float = game.thirst
	simulate(2)
	check(game.hunger > hunger and game.thirst > thirst, "live survival clocks increase hunger and thirst")
	game._set_paused(true)
	var frozen := state()
	simulate(1)
	check(state() == frozen, "pause freezes all integrated survival state")
	game._set_paused(false)
	print("HOUSE_SURVIVAL: inventory/survival checks finished")


func write_json(path: String, data: Variant) -> void:
	var file := FileAccess.open(path, FileAccess.WRITE)
	file.store_string(JSON.stringify(data))
	file.close()


func test_saves() -> void:
	fresh()
	check(game._load_game("res://tests/fixtures/house_v1.json") == OK, "real schema-one fixture migrates")
	check(game.player == Vector2(3, 5) and game.health == 73 and game.supplies == 2, "migration preserves legacy player progress")
	check(game.items[0].searched and game.items[2].searched and not game.items[1].searched and game.zombie_health[0] == 0 and game.doors[0].open, "migration preserves four legacy containers, zombies and doors")
	check(game.stamina >= 0 and game.stamina <= 100 and game.hunger >= 0 and game.hunger <= 100 and game.thirst >= 0 and game.thirst <= 100, "migration supplies valid survival defaults")
	game.stamina = 47
	game.hunger = 39
	game.thirst = 63
	game.survival.add(HAMMER)
	game.survival.equip(HAMMER)
	game.survival.add(PLANK)
	game._drop_item(PLANK)
	var saved := state()
	var path := "user://house-survival-roundtrip.json"
	var invalid_path := "user://house-survival-invalid.json"
	check(game._save_game(path) == OK, "version-three atomic save succeeds")
	var payload: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(path))
	check(payload.version == 3, "save has explicit schema-three version")
	game._restart_game()
	check(game._load_game(path) == OK and state() == saved, "schema-two round trip restores survival, inventory, drops and legacy world")
	var invalids: Array[Dictionary] = []
	var future: Dictionary = payload.duplicate(true)
	future.version = 999
	invalids.append(future)
	for key: String in ["health", "stamina", "hunger", "thirst"]:
		var negative: Dictionary = payload.duplicate(true)
		negative[key] = -1
		invalids.append(negative)
		var wrong_type: Dictionary = payload.duplicate(true)
		wrong_type[key] = "50"
		invalids.append(wrong_type)
	var bad_position: Dictionary = payload.duplicate(true)
	bad_position.player = [null, 5]
	invalids.append(bad_position)
	var missing: Dictionary = payload.duplicate(true)
	missing.erase("stamina")
	invalids.append(missing)
	for bad_inventory: Dictionary in [
		{"inventory": {"unknown": 1}, "equipped": ""},
		{"inventory": {BEANS: -1}, "equipped": ""},
		{"inventory": {BEANS: 1.25}, "equipped": ""},
		{"inventory": {}, "equipped": HAMMER},
		{"inventory": {BEANS: 1}, "equipped": BEANS},
	]:
		var changed: Dictionary = payload.duplicate(true)
		changed.survival = bad_inventory
		invalids.append(changed)
	for bad_drop: Dictionary in [
		{"id": "unknown", "count": 1, "x": 1, "y": 1},
		{"id": PLANK, "count": -1, "x": 1, "y": 1},
		{"id": PLANK, "count": 1.5, "x": 1, "y": 1},
		{"id": PLANK, "count": 1, "x": "1", "y": 1},
	]:
		var changed: Dictionary = payload.duplicate(true)
		changed.drops = [bad_drop]
		invalids.append(changed)
	var bad_flags: Dictionary = payload.duplicate(true)
	bad_flags.containers[game.items[0].id] = not bad_flags.searched[0]
	invalids.append(bad_flags)
	for index in range(invalids.size()):
		write_json(invalid_path, invalids[index])
		check(game._load_game(invalid_path) != OK and state() == saved, "invalid schema-two save rejected atomically: case %d" % index)
	var truncated := FileAccess.open(invalid_path, FileAccess.WRITE)
	truncated.store_string('{"version":2,')
	truncated.close()
	check(game._load_game(invalid_path) != OK and state() == saved, "truncated save cannot erase current state")
	var original_corrupt := FileAccess.get_file_as_string(invalid_path)
	check(game._save_game(invalid_path) != OK and FileAccess.get_file_as_string(invalid_path) == original_corrupt, "writing over corrupt existing save is refused without altering bytes")
	var legacy_path := "user://house-survival-legacy.json"
	var original_legacy := FileAccess.get_file_as_string("res://tests/fixtures/house_v1.json")
	var legacy := FileAccess.open(legacy_path, FileAccess.WRITE)
	legacy.store_string(original_legacy)
	legacy.close()
	check(game._load_game(legacy_path) == OK and game._save_game(legacy_path) == OK, "legacy file upgrades after successful load")
	check(FileAccess.get_file_as_string(legacy_path + ".schema1.bak") == original_legacy, "migration archive preserves exact original schema-one bytes")
	var moved_fixture: Dictionary = JSON.parse_string(original_legacy)
	moved_fixture.player = [3.4, 2.8]
	write_json(invalid_path, moved_fixture)
	check(game._load_game(invalid_path) == OK and not game._blocked(game.player), "legacy position inside newly added furniture relocates to clear ground")
	game._restart_game()
	check(game.health == 100 and game.stamina == 100 and game.hunger == 0 and game.thirst == 0 and game.survival.inventory.is_empty() and game.drops.is_empty(), "restart resets complete new survival loop")
	var future_slot := FileAccess.open(game.SAVE_PATH, FileAccess.WRITE)
	var future_text := '{"version":999,"progress":"retain these exact bytes"}'
	future_slot.store_string(future_text)
	future_slot.close()
	var recovered = load("res://main.tscn").instantiate()
	root.add_child(recovered)
	recovered.set_process(false)
	check(recovered.save_blocked and recovered.paused, "unsupported startup save blocks simulation and automatic overwrites")
	check(recovered._save_game() != OK and FileAccess.get_file_as_string(game.SAVE_PATH) == future_text, "automatic save preserves unknown future-schema progress")
	recovered._restart_game()
	check(FileAccess.get_file_as_string(game.SAVE_PATH + ".rejected.bak") == future_text, "explicit fresh restart archives rejected original progress")
	check(recovered._load_game(game.SAVE_PATH, true) == OK, "fresh restart after rejected save persists a valid new game")
	recovered.free()
	for filename: String in [path, invalid_path, legacy_path, legacy_path + ".schema1.bak"]:
		DirAccess.remove_absolute(ProjectSettings.globalize_path(filename))
	print("HOUSE_SURVIVAL: save/migration checks finished")


func test_camera_and_zoom() -> void:
	fresh()
	game.zoom_adjust=0.0
	game.player=Vector2(4.9,9.35)
	game.camera_zoom=game._zoom_target()
	check(is_equal_approx(game.camera_zoom,1.0),"outside baseline is 100%")
	game.player=Vector2(2.0,2.0)
	game.camera_zoom=game._zoom_target()
	check(game.camera_zoom >= 2.0,"automatic indoor zoom is substantially closer")
	var tile := Vector2(3.25,2.2)
	var projected: Vector2=game._world_to_view(tile)
	check(game._view_to_world(projected).distance_to(tile)<.001,"tap/placement uses zoom-corrected world coordinates")
	var initial: float=game.camera_zoom
	game._tap(button("zoom_in"))
	check(game.camera_zoom>initial,"touch zoom in increases world magnification")
	game._tap(button("zoom_out"))
	check(is_equal_approx(game.camera_zoom,initial),"touch zoom out restores magnification")
	var saved_gameplay: Dictionary=state()
	game._tap(button("zoom_in"))
	check(state()==saved_gameplay,"zoom changes no gameplay/persistent world state")
	for i in range(20): game._adjust_zoom(game.ZOOM_STEP)
	check(game.camera_zoom<=game.MAX_ZOOM,"max zoom clamped")
	for i in range(30): game._adjust_zoom(-game.ZOOM_STEP)
	check(game.camera_zoom>=game.MIN_ZOOM,"min zoom clamped")
	game.zoom_adjust=0.0
	game.camera_zoom=game._zoom_target()
	game._save_controls()
	for name in ["zoom_in","zoom_out"]:
		check(game.control_rects.has(name),"Zoom HUD contains "+name)
		check(game.get_viewport_rect().has_point(game.control_rects[name].get_center()),"Zoom controls are on screen")
	print("HOUSE_SURVIVAL: adaptive camera and larger touch controls PASS")


func run() -> void:
	root.size = Vector2i(1152, 720)
	root.content_scale_size = Vector2i(1152, 720)
	game = load("res://main.tscn").instantiate()
	root.add_child(game)
	game.set_process(false)
	test_controls()
	test_camera_and_zoom()
	test_movement_and_geometry()
	test_combat_and_zombies()
	test_inventory_and_survival()
	test_saves()
	print("HOUSE_SURVIVAL: %d checks, %d failures (synthetic engine input; actual iPhone/Xogot UNVERIFIED)" % [checks, failures.size()])
	game.free()
	quit(0 if failures.is_empty() else 1)
