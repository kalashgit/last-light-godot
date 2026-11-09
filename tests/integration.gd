extends SceneTree
## Integration-candidate regression: checks the pieces brought together from
## PR #18, #19, #25 and #26 work in one build. Synthetic input only; iPhone/Xogot UNVERIFIED.

var checks := 0
var failures: Array[String] = []


func _initialize() -> void:
	call_deferred("run")


func check(condition: bool, label: String) -> void:
	checks += 1
	if not condition:
		failures.append(label)
		printerr("FAIL: " + label)


func touch(game, index: int, point: Vector2, pressed: bool) -> void:
	var event := InputEventScreenTouch.new()
	event.index = index
	event.position = point
	event.pressed = pressed
	game._input(event)


func make_game(size: Vector2i):
	root.size = size
	root.content_scale_size = size
	var game = load("res://main.tscn").instantiate()
	root.add_child(game)
	game.set_process(false)
	game._restart_game()
	game.set_process(false)
	for index in range(game.zombie_health.size()):
		game.zombie_health[index] = 0
	game._layout_controls()
	return game


func test_layout(size: Vector2i, label: String) -> void:
	var game = make_game(size)
	var screen := Rect2(Vector2.ZERO, Vector2(size))
	var stick: Rect2 = game.control_rects.joystick_rect
	check(screen.encloses(stick), label + ": joystick fully on screen")
	for name: String in ["attack", "interact", "shove", "sprint", "sneak", "inventory", "pause", "zoom_in", "zoom_out", "quick0", "quick1", "quick2", "quick3"]:
		var rect: Rect2 = game.control_rects[name]
		check(screen.encloses(rect), label + ": on screen " + name)
		check(not stick.intersects(rect), label + ": joystick does not overlap " + name)
	var prompt: Rect2 = game.control_rects.context_prompt
	check(screen.encloses(prompt), label + ": context prompt on screen")
	check(not stick.intersects(prompt), label + ": context prompt does not cover joystick")
	for name: String in ["quick0", "quick3", "interact", "attack"]:
		check(not prompt.intersects(game.control_rects[name]), label + ": context prompt does not cover " + name)
	if size.y > size.x:
		var safe: Rect2 = game.control_rects.safeRect
		check(game.stick_center.is_equal_approx(Vector2(safe.position.x + 215.0, safe.end.y - 345.0)), label + ": founder-marked portrait stick position")
	# Stick input moves the player.
	game.player = Vector2(-4, 2)
	var before: Vector2 = game.player
	touch(game, 7, game.stick_center + Vector2(game.stick_radius, 0), true)
	for i in range(60):
		game._process(1.0 / 60.0)
	touch(game, 7, game.stick_center, false)
	check(game.player.distance_to(before) > .5, label + ": joystick drives movement")
	game.free()


func test_inventory_icons() -> void:
	var game = make_game(Vector2i(720, 1152))
	var legacy := 0
	var golden := 0
	for id: String in game.survival.definitions:
		var icon: Texture2D = game._item_icon(id)
		check(icon != null, "inventory thumbnail exists for " + id)
		if id.begins_with("ll_golden_"):
			golden += 1
		else:
			legacy += 1
	check(legacy == 8, "8 legacy survival items have factory thumbnails (got %d)" % legacy)
	check(golden == 40, "40 Golden items keep their icons (got %d)" % golden)
	check(game._item_icon("does_not_exist") == null, "unknown id gives no icon without crashing")
	game.survival.add("ll_food_bean_tin", 1)
	game._set_inventory(true)
	game.queue_redraw()
	game._set_inventory(false)
	game.free()


func test_street_preview() -> void:
	var scene: PackedScene = load("res://scenes/unified_factory_street.tscn")
	check(scene != null, "UCF-001 street preview scene loads")
	if scene == null:
		return
	var street = scene.instantiate()
	root.add_child(street)
	check(street.district.get("schema", "") == "last_light.unified_world.v1", "UCF-001 street JSON loads with expected schema")
	check((street.district.get("buildings", []) as Array).size() == 3, "UCF-001 street has three houses")
	street.free()


func run() -> void:
	check(ProjectSettings.get_setting("application/run/main_scene") == "res://main.tscn", "main scene is still res://main.tscn")
	test_layout(Vector2i(720, 1152), "portrait 720x1152")
	test_layout(Vector2i(1152, 720), "landscape 1152x720")
	test_inventory_icons()
	test_street_preview()
	print("INTEGRATION: %d checks, %d failures (synthetic input; iPhone/Xogot UNVERIFIED)" % [checks, failures.size()])
	if failures.is_empty():
		print("INTEGRATION PASS")
	quit(0 if failures.is_empty() else 1)
