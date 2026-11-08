extends SceneTree
## Real render captures of the integration candidate (main.tscn + UCF street preview).
## Desktop Xvfb renders are emulation, never iPhone/Xogot verification.

var output_dir := "/tmp/last-light-integration-captures"


func _initialize() -> void:
	for argument: String in OS.get_cmdline_user_args():
		if argument.begins_with("--output-dir="):
			output_dir = argument.trim_prefix("--output-dir=")
	call_deferred("capture")


func shot(name: String, size: Vector2i) -> bool:
	await process_frame
	await RenderingServer.frame_post_draw
	var picture := root.get_texture().get_image()
	var path := "%s/%s-%dx%d.png" % [output_dir, name, size.x, size.y]
	if picture.save_png(path) != OK:
		printerr("CAPTURE: failed " + path)
		return false
	print("CAPTURE: " + path)
	return true


func capture() -> void:
	if DisplayServer.get_name() == "headless":
		printerr("CAPTURE: requires a graphical display")
		quit(1)
		return
	DirAccess.make_dir_recursive_absolute(output_dir)
	var game = load("res://main.tscn").instantiate()
	root.add_child(game)
	game.set_process(false)
	game._restart_game()
	game.god_mode = true
	for index in range(game.zombie_health.size()):
		game.zombie_health[index] = 0
	for door: Dictionary in game.doors:
		door.open = true
	for id: String in ["ll_food_bean_tin", "ll_food_water_bottle", "ll_medical_sterile_bandage", "ll_tools_claw_hammer", "ll_household_flashlight"]:
		game.survival.add(id, 1)
	for id: String in game.survival.definitions:
		if id.begins_with("ll_golden_"):
			game.survival.add(id, 1)
			break
	var views := [
		{"name": "portrait-exterior", "size": Vector2i(720, 1152), "position": Vector2(4.9, 9.35)},
		{"name": "portrait-indoor-zoom", "size": Vector2i(720, 1152), "position": Vector2(3.0, 5.0)},
		{"name": "portrait-inventory", "size": Vector2i(720, 1152), "position": Vector2(3.0, 5.0), "inventory": true},
		{"name": "landscape-indoor", "size": Vector2i(1152, 720), "position": Vector2(2.0, 2.7)},
		{"name": "landscape-inventory", "size": Vector2i(1152, 720), "position": Vector2(3.0, 5.0), "inventory": true},
	]
	for view: Dictionary in views:
		game._set_inventory(false)
		root.size = view["size"]
		root.content_scale_size = view["size"]
		await process_frame
		game.player = view["position"]
		game.camera_zoom = game._zoom_target()
		game.message_time = 0
		game._layout_controls()
		if view.get("inventory", false):
			game._set_inventory(true)
		game.queue_redraw()
		if not await shot(view["name"], view["size"]):
			quit(1)
			return
	game.free()
	var size := Vector2i(1152, 720)
	root.size = size
	root.content_scale_size = size
	var street = load("res://scenes/unified_factory_street.tscn").instantiate()
	root.add_child(street)
	if not await shot("ucf001-street-preview", size):
		quit(1)
		return
	street.free()
	quit()
