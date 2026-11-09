extends SceneTree
## Xvfb captures of the playable scene at iPhone logical sizes for review.
## Desktop software rendering: NOT iPhone/Xogot evidence.
##   xvfb-run -a godot --path . --rendering-driver opengl3 \
##     --script tests/mobile/capture_mobile_hud.gd -- --output-dir=/tmp/out

var output_dir := "/tmp/last-light-mobile-captures"


func _initialize() -> void:
	for argument: String in OS.get_cmdline_user_args():
		if argument.begins_with("--output-dir="):
			output_dir = argument.trim_prefix("--output-dir=")
	call_deferred("capture")


func shot(game: Node, name: String) -> void:
	for i in range(3):
		game.queue_redraw()
		await process_frame
		await RenderingServer.frame_post_draw
	var path := "%s/%s.png" % [output_dir, name]
	root.get_texture().get_image().save_png(path)
	print("CAPTURE: " + path)


func capture() -> void:
	if DisplayServer.get_name() == "headless":
		printerr("CAPTURE: requires a display")
		quit(1)
		return
	DirAccess.make_dir_recursive_absolute(output_dir)
	root.size = Vector2i(1561, 720)
	var game: Node = load("res://main.tscn").instantiate()
	root.add_child(game)
	game.set_process(false)
	game._restart_game()
	game.message_time = 0.0
	if "safe_override" in game.hud:
		# iPhone 15 landscape: 59 pt side insets, 21 pt home indicator.
		var k := 720.0 / 393.0
		game.hud.safe_override = Rect2(Vector2(59 * k, 0), Vector2(1561 - 118 * k, 720 - 21 * k))
	game._layout_controls()
	if game.has_method("_snap_camera"):
		game._snap_camera()
	else:
		game.camera_zoom = game._zoom_target()
	await shot(game, "1_outdoor")
	game.player = Vector2(3, 5)
	for door: Dictionary in game.doors:
		door.open = true
	if game.has_method("_snap_camera"):
		game._snap_camera()
	else:
		game.camera_zoom = game._zoom_target()
	await shot(game, "2_indoor")
	for id in ["ll_food_bean_tin", "ll_food_water_bottle", "ll_medical_sterile_bandage", "ll_tools_claw_hammer", "ll_tools_hatchet"]:
		game.survival.add(id, 1)
	game._set_inventory(true)
	await shot(game, "3_backpack")
	game._set_inventory(false)
	game._set_paused(true)
	await shot(game, "4_pause")
	game.free()
	quit()
