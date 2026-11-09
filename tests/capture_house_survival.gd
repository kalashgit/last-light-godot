extends SceneTree
## Actual main-scene rendering evidence. Outputs remain outside the source tree by default.
## Desktop landscape viewports are emulation, never iPhone/Xogot verification.

var output_dir := "/tmp/last-light-house-captures"


func _initialize() -> void:
	for argument: String in OS.get_cmdline_user_args():
		if argument.begins_with("--output-dir="):
			output_dir = argument.trim_prefix("--output-dir=")
	call_deferred("capture")


func capture() -> void:
	if DisplayServer.get_name() == "headless":
		printerr("CAPTURE: requires a graphical display; no screenshot produced")
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
	var views := [
		{"name": "desktop-exterior", "size": Vector2i(1280, 800), "position": Vector2(4.9, 9.35)},
		{"name": "desktop-kitchen", "size": Vector2i(1280, 800), "position": Vector2(2.0, 2.7)},
		{"name": "desktop-bedroom", "size": Vector2i(1280, 800), "position": Vector2(6.2, 2.5)},
		{"name": "desktop-living", "size": Vector2i(1280, 800), "position": Vector2(3.0, 5.0)},
		{"name": "desktop-bathroom", "size": Vector2i(1280, 800), "position": Vector2(6.2, 5.7)},
		{"name": "landscape-hud", "size": Vector2i(1152, 720), "position": Vector2(3.0, 5.0)},
		{"name": "wide-landscape-hud", "size": Vector2i(1560, 720), "position": Vector2(3.0, 5.0)},
		{"name": "wide-landscape-inventory", "size": Vector2i(1560, 720), "position": Vector2(3.0, 5.0), "inventory": true},
		{"name": "landscape-equipped-hammer", "size": Vector2i(1152, 720), "position": Vector2(3.0, 5.0), "equipped": "ll_tools_claw_hammer"},
		{"name": "landscape-pause-settings", "size": Vector2i(1152, 720), "position": Vector2(3.0, 5.0), "paused": true},
	]
	for view: Dictionary in views:
		# Each view enters its real modal state independently of the preceding view.
		game._set_inventory(false)
		game._set_paused(false)
		game.survival.equip("")
		root.size = view["size"]
		root.content_scale_size = view["size"]
		await process_frame
		game.player = view["position"]
		game.message_time = 0
		game._layout_controls()
		if view.get("inventory", false):
			for id: String in ["ll_food_bean_tin", "ll_food_water_bottle", "ll_medical_sterile_bandage", "ll_tools_claw_hammer"]:
				game.survival.add(id, 1)
			game._set_inventory(true)
		if view.has("equipped"):
			var equipped_id: String = view["equipped"]
			if not game.survival.inventory.has(equipped_id):
				game.survival.add(equipped_id)
			if not game.survival.equip(equipped_id):
				printerr("CAPTURE: could not equip owned weapon")
				game.free()
				quit(1)
				return
			game.facing = Vector2.RIGHT
		if view.get("paused", false):
			game._set_paused(true)
		game.queue_redraw()
		await process_frame
		await RenderingServer.frame_post_draw
		var picture := root.get_texture().get_image()
		var path := "%s/%s-%dx%d.png" % [output_dir, view["name"], view["size"].x, view["size"].y]
		var error := picture.save_png(path)
		if error != OK:
			printerr("CAPTURE: failed %s: %s" % [path, error_string(error)])
			game.free()
			quit(1)
			return
		print("CAPTURE: %s (%dx%d)" % [path, picture.get_width(), picture.get_height()])
	game.free()
	quit()
