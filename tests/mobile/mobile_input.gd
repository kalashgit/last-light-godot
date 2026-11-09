extends SceneTree
## W08 mobile input, HUD and camera regression on the real playable scene.
## Drives InputEventScreenTouch/Drag through _input exactly as iOS delivers them.
## Headless-safe. This is engine-level evidence only, NOT iPhone/Xogot verification.
##   godot --headless --path . --script tests/mobile/mobile_input.gd

var game: Node
var failures: Array[String] = []
var passes := 0

# iPhone landscape logical viewports after canvas_items/expand stretch at 720 px
# height (base project 1152x720): SE 667x375pt, 15/16 852x393pt, Pro Max 932x430pt.
const PHONES := {
	"iphone_se": {"size": Vector2i(1281, 720), "points_h": 375.0},
	"iphone_15": {"size": Vector2i(1561, 720), "points_h": 393.0},
	"iphone_pro_max": {"size": Vector2i(1561, 720), "points_h": 430.0},
}
## Apple HIG minimum hit target is 44x44 pt. We accept >= 40 pt on the smallest
## supported phone for in-game controls and require >= 44 pt on 15-class phones.
const MIN_TARGET_PT_SMALL := 40.0
const MIN_TARGET_PT := 44.0
const PLAY_CONTROLS := ["inventory", "pause", "zoom_in", "zoom_out", "attack", "interact", "shove", "sprint", "sneak", "quick0", "quick1", "quick2", "quick3"]


func _initialize() -> void:
	call_deferred("run")


func check(condition: bool, label: String) -> void:
	if condition:
		passes += 1
	else:
		failures.append(label)
		printerr("FAIL: " + label)


func fresh(size := Vector2i(1561, 720)) -> void:
	if game != null:
		game.free()
	root.size = size
	game = load("res://main.tscn").instantiate()
	root.add_child(game)
	game.set_process(false)
	game._restart_game()
	game.god_mode = true
	game.hud.safe_override = Rect2()
	game.hud.points_override_short = 393.0
	game._layout_controls()


func touch(index: int, position: Vector2, pressed: bool, canceled := false) -> void:
	var event := InputEventScreenTouch.new()
	event.index = index
	event.position = position
	event.pressed = pressed
	event.canceled = canceled
	game._input(event)


func drag(index: int, position: Vector2) -> void:
	var event := InputEventScreenDrag.new()
	event.index = index
	event.position = position
	game._input(event)


func rect(name: String) -> Rect2:
	game._layout_controls()
	return game.control_rects[name]


func step(seconds: float) -> void:
	var frames := int(round(seconds * 60.0))
	for i in range(frames):
		game._process(1.0 / 60.0)


func test_joystick_activation_and_release() -> void:
	fresh()
	var center: Vector2 = game.stick_center
	touch(0, center + Vector2(game.stick_radius * .9, 0), true)
	check(game.joystick_touch == 0, "joystick: touch inside stick area takes ownership")
	check(game.joystick_vector.x > .8, "joystick: right push gives right vector")
	var start: Vector2 = game.player
	step(.5)
	check(game.player.distance_to(start) > .3, "joystick: held stick moves the player")
	drag(0, center + Vector2(0, -game.stick_radius))
	check(game.joystick_vector.y < -.8 and absf(game.joystick_vector.x) < .1, "joystick: drag updates direction smoothly")
	touch(0, center, false)
	check(game.joystick_touch == -1 and game.joystick_vector == Vector2.ZERO, "joystick: release clears ownership and vector")
	var stopped: Vector2 = game.player
	step(.3)
	check(game.player.distance_to(stopped) < .0001, "joystick: release stops movement")
	touch(1, center + Vector2(game.stick_radius * game.joystick_dead_zone * .5, 0), true)
	check(game.joystick_vector == Vector2.ZERO, "joystick: inside dead zone gives no motion")
	touch(1, center, false)


func test_multitouch_ownership() -> void:
	fresh()
	var center: Vector2 = game.stick_center
	touch(0, center + Vector2(game.stick_radius, 0), true)
	touch(1, center + Vector2(-game.stick_radius, 0), true)
	check(game.joystick_touch == 0 and game.joystick_vector.x > .8, "multi-touch: second finger cannot steal the stick")
	drag(1, center + Vector2(0, game.stick_radius))
	check(game.joystick_vector.x > .8, "multi-touch: other finger's drag is ignored by the stick")
	touch(1, center, false)
	check(game.joystick_touch == 0, "multi-touch: other finger release keeps stick ownership")
	# Hold sprint with a second finger while steering with the first.
	touch(2, rect("sprint").get_center(), true)
	check(game.sprint_held, "multi-touch: sprint held while steering")
	step(.2)
	check(game.sprinting, "multi-touch: sprint + stick sprints")
	drag(0, center + Vector2(0, -game.stick_radius))
	check(game.sprint_held and game.joystick_vector.y < -.8, "multi-touch: steering does not release sprint")
	touch(2, rect("sprint").get_center(), false)
	check(not game.sprint_held, "multi-touch: sprint release ends sprint")
	touch(0, center, false)


func test_touch_cancellation_and_interruption() -> void:
	fresh()
	var center: Vector2 = game.stick_center
	touch(0, center + Vector2(game.stick_radius, 0), true)
	touch(1, rect("sprint").get_center(), true)
	touch(0, center, false, true)
	check(game.joystick_touch == -1 and game.joystick_vector == Vector2.ZERO, "cancel: canceled touch releases stick")
	touch(1, rect("sprint").get_center(), false, true)
	check(not game.sprint_held, "cancel: canceled touch releases sprint")
	touch(0, center + Vector2(game.stick_radius, 0), true)
	touch(1, rect("sprint").get_center(), true)
	game._notification(Node.NOTIFICATION_APPLICATION_FOCUS_OUT)
	check(game.paused and game.joystick_touch == -1 and not game.sprint_held, "interrupt: app focus loss pauses and releases held inputs")
	game._set_paused(false)
	# A finger dragged off-screen is a release.
	touch(3, center + Vector2(game.stick_radius, 0), true)
	drag(3, Vector2(-50, center.y))
	check(game.joystick_touch == -1, "cancel: drag off-screen releases the stick")


func test_direction_mapping() -> void:
	fresh()
	# Screen-up on the stick must move the player's projected position up the screen.
	for direction in [Vector2.UP, Vector2.DOWN, Vector2.LEFT, Vector2.RIGHT, Vector2(1, -1).normalized()]:
		var world: Vector2 = game._screen_direction_to_world(direction)
		var projected: Vector2 = game._iso(world) - game._iso(Vector2.ZERO)
		check(projected.normalized().dot(direction) > .999, "mapping: stick %s moves the same way on screen" % [direction])


func test_attack_isolation() -> void:
	fresh()
	game.selected_target = {}
	touch(0, rect("attack").get_center(), true)
	check(game.attack_cooldown > 0, "attack: attack button attacks")
	check(game.joystick_touch == -1, "attack: attack button never grabs the stick")
	touch(0, rect("attack").get_center(), false)
	game.attack_cooldown = 0.0
	# A tap on open world selects a target but never attacks.
	var world_point: Vector2 = game._world_to_view(game.player + Vector2(1, -1))
	touch(1, world_point, true)
	check(game.attack_cooldown == 0.0, "attack: world tap does not attack")
	touch(1, world_point, false)
	# Stick and attack together: attack with the right thumb while moving.
	touch(0, game.stick_center + Vector2(game.stick_radius, 0), true)
	touch(1, rect("attack").get_center(), true)
	check(game.attack_cooldown > 0 and game.joystick_touch == 0, "attack: attacking while steering keeps both")


func test_ui_input_does_not_leak() -> void:
	fresh()
	touch(0, rect("inventory").get_center(), true)
	touch(0, rect("inventory").get_center(), false)
	check(game.inventory_open and game.paused, "inventory: button opens backpack and pauses world")
	game.attack_cooldown = 0.0
	touch(1, rect("attack").get_center(), true)
	touch(1, rect("attack").get_center(), false)
	check(game.attack_cooldown == 0.0, "leak: attack position does not attack while backpack open")
	touch(2, game.stick_center, true)
	check(game.joystick_touch == -1, "leak: stick does not activate while backpack open")
	touch(2, game.stick_center, false)
	touch(0, rect("inventory").get_center(), true)
	touch(0, rect("inventory").get_center(), false)
	check(not game.inventory_open and not game.paused, "inventory: close button closes and resumes")
	game._set_paused(true)
	touch(3, rect("attack").get_center(), true)
	check(game.attack_cooldown == 0.0, "leak: no attack while paused")
	touch(3, rect("attack").get_center(), false)


func test_inventory_thumbnails() -> void:
	fresh()
	var with_icons := 0
	var checked := 0
	for id in game.survival.definitions.keys():
		var definition: Dictionary = game.survival.definitions[id]
		var icon: Texture2D = game._item_icon(id)
		checked += 1
		if icon != null:
			with_icons += 1
			check(icon.get_width() >= 32 and icon.get_height() >= 32, "thumbnail: %s icon is at least 32px" % id)
		elif str(id).begins_with("ll_golden_") or not str(definition.get("icon_path", "")).is_empty():
			check(false, "thumbnail: %s has approved icon art but none resolved" % id)
	check(with_icons == checked, "thumbnail: every inventory item resolves an image (%d/%d)" % [with_icons, checked])


func test_camera_doorway() -> void:
	fresh()
	game.zoom_adjust = 0.0
	game.player = Vector2(4.9, 9.35)
	game._snap_camera()
	check(is_equal_approx(game.camera_zoom, 1.0) and not game.camera_indoor, "camera: outdoor framing at spawn")
	# Walk inside: zoom eases in and finishes at the indoor target.
	game.player = Vector2(4.9, 6.0)
	var previous_zoom: float = game.camera_zoom
	var previous_pivot: float = game.camera_pivot_y
	var max_zoom_step := 0.0
	var max_pivot_step := 0.0
	for i in range(90):
		game._process(1.0 / 60.0)
		max_zoom_step = maxf(max_zoom_step, absf(game.camera_zoom - previous_zoom))
		max_pivot_step = maxf(max_pivot_step, absf(game.camera_pivot_y - previous_pivot))
		previous_zoom = game.camera_zoom
		previous_pivot = game.camera_pivot_y
	check(is_equal_approx(game.camera_zoom, game.INDOOR_ZOOM), "camera: indoor zoom reached")
	check(is_equal_approx(game.camera_pivot_y, game.PIVOT_INDOOR), "camera: indoor framing reached")
	check(max_zoom_step <= .051, "camera: zoom eases (max %.3f per frame)" % max_zoom_step)
	check(max_pivot_step <= .02, "camera: framing pivot eases, no jump (max %.4f per frame)" % max_pivot_step)
	# Pace back and forth across the threshold inside the hysteresis band.
	var flips := 0
	var last: bool = game.camera_indoor
	for i in range(40):
		game.player = Vector2(5.3, 8.0 + (0.2 if i % 2 == 0 else -0.2))
		game._process(1.0 / 60.0)
		if game.camera_indoor != last:
			flips += 1
			last = game.camera_indoor
	check(flips == 0, "camera: no oscillation when pacing on the doorway (%d flips)" % flips)
	# Leave the house: outdoor zoom is restored.
	game.player = Vector2(4.9, 9.35)
	step(1.5)
	check(is_equal_approx(game.camera_zoom, 1.0) and is_equal_approx(game.camera_pivot_y, game.PIVOT_OUTDOOR), "camera: outdoor zoom restored")
	# Steady follow: the player stays at the same screen spot while walking.
	game.player = Vector2(4.9, 11.0)
	game._snap_camera()
	var anchor: Vector2 = game._world_to_view(game.player)
	var drift := 0.0
	touch(0, game.stick_center + Vector2(game.stick_radius, 0), true)
	for i in range(60):
		game._process(1.0 / 60.0)
		drift = maxf(drift, game._world_to_view(game.player).distance_to(anchor))
	touch(0, game.stick_center, false)
	check(drift < .01, "camera: no follow jitter outdoors (drift %.4f px)" % drift)


func overlaps(a: Rect2, b: Rect2) -> bool:
	return a.intersects(b) and a.intersection(b).get_area() > 1.0


func test_safe_area_and_targets() -> void:
	for phone in PHONES.keys():
		var spec: Dictionary = PHONES[phone]
		fresh(spec.size)
		var viewport := Vector2(spec.size)
		var px_per_pt: float = viewport.y / float(spec.points_h)
		# Emulate the landscape notch/Dynamic Island and home indicator insets.
		var inset_side := (59.0 if phone != "iphone_se" else 0.0) * px_per_pt
		var inset_bottom := (21.0 if phone != "iphone_se" else 0.0) * px_per_pt
		var safe := Rect2(Vector2(inset_side, 0), viewport - Vector2(inset_side * 2.0, inset_bottom))
		game.hud.safe_override = safe
		game.hud.points_override_short = spec.points_h
		game._layout_controls()
		var minimum := MIN_TARGET_PT_SMALL if phone == "iphone_se" else MIN_TARGET_PT
		for name in PLAY_CONTROLS + ["joystick_rect"]:
			var r: Rect2 = game.control_rects[name]
			check(safe.encloses(r), "%s: %s inside safe area" % [phone, name])
			var short_side_pt: float = minf(r.size.x, r.size.y) / px_per_pt
			check(short_side_pt >= minimum - .01, "%s: %s target %.1f pt >= %.0f pt" % [phone, name, short_side_pt, minimum])
		for i in range(PLAY_CONTROLS.size()):
			for j in range(i + 1, PLAY_CONTROLS.size()):
				var a: Rect2 = game.control_rects[PLAY_CONTROLS[i]]
				var b: Rect2 = game.control_rects[PLAY_CONTROLS[j]]
				check(not overlaps(a, b), "%s: %s and %s do not overlap" % [phone, PLAY_CONTROLS[i], PLAY_CONTROLS[j]])
			check(not overlaps(game.control_rects[PLAY_CONTROLS[i]], game.control_rects.joystick_rect), "%s: %s clear of joystick" % [phone, PLAY_CONTROLS[i]])
		# The developer loot-builder launcher swallows touches; it must not cover controls.
		game.loot_builder._reflow()
		var launcher: Rect2 = game.loot_builder.launcher.get_global_rect()
		for name in PLAY_CONTROLS + ["joystick_rect"]:
			check(not overlaps(launcher, game.control_rects[name]), "%s: loot-builder launcher clear of %s" % [phone, name])
		# The player must stay visible between the thumb clusters.
		var player_view: Vector2 = game._world_to_view(game.player)
		for name in PLAY_CONTROLS + ["joystick_rect"]:
			check(not game.control_rects[name].has_point(player_view), "%s: %s does not cover the player" % [phone, name])
		# Backpack rows fit and keep usable targets.
		for i in range(game.INVENTORY_PAGE_SIZE):
			for kind in ["modal_use_%d", "modal_drop_%d"]:
				var r: Rect2 = game.control_rects[kind % i]
				check(game.control_rects.inventory_panel.encloses(r), "%s: %s inside backpack" % [phone, kind % i])
				check(minf(r.size.x, r.size.y) / px_per_pt >= minimum - .01, "%s: %s target >= %.0f pt" % [phone, kind % i, minimum])


func run() -> void:
	test_joystick_activation_and_release()
	test_multitouch_ownership()
	test_touch_cancellation_and_interruption()
	test_direction_mapping()
	test_attack_isolation()
	test_ui_input_does_not_leak()
	test_inventory_thumbnails()
	test_camera_doorway()
	test_safe_area_and_targets()
	game.free()
	if failures.is_empty():
		print("MOBILE INPUT: %d checks PASS (engine-level; not iPhone-verified)" % passes)
		quit(0)
	else:
		printerr("MOBILE INPUT: %d FAILED of %d" % [failures.size(), failures.size() + passes])
		quit(1)
