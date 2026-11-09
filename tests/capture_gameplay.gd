extends SceneTree
## Renders the real main scene with Worker 02 gameplay state (wounds, worn weapon,
## recipe action) for visual evidence. Desktop emulation only, not iPhone evidence.
## Usage: xvfb-run godot --path . --script tests/capture_gameplay.gd -- --output-dir=DIR

var output_dir := "/tmp/last-light-gameplay-captures"


func _initialize() -> void:
	for argument: String in OS.get_cmdline_user_args():
		if argument.begins_with("--output-dir="):
			output_dir = argument.trim_prefix("--output-dir=")
	call_deferred("capture")


func shot(name: String) -> void:
	for i in range(4):
		await process_frame
	await RenderingServer.frame_post_draw
	var image := root.get_texture().get_image()
	image.save_png(output_dir.path_join(name))
	print("CAPTURE: ", output_dir.path_join(name), " ", image.get_size())


func capture() -> void:
	if DisplayServer.get_name() == "headless":
		printerr("CAPTURE: requires a graphical display")
		quit(1)
		return
	DirAccess.make_dir_recursive_absolute(output_dir)
	root.size = Vector2i(1152, 720)
	var game = load("res://main.tscn").instantiate()
	root.add_child(game)
	game.set_process(false)
	game._restart_game()
	game.set_process(false)
	for door: Dictionary in game.doors:
		door.open = true
	game.player = Vector2(1.8, 5.95)
	game.zombie_health[1] = 0
	game.infected[0] = Vector2(2.6, 5.9)
	game.survival.add("ll_tools_claw_hammer")
	game.survival.equip("ll_tools_claw_hammer")
	game.survival.instances["ll_tools_claw_hammer"][0].condition = 21.0
	game.survival.add("ll_crafting_pine_plank", 2)
	game.survival.add("ll_medical_sterile_bandage", 2)
	game.vitals.add_wound("laceration", true)
	game.health = 64.0
	game.fatigue = 55.0
	game._announce("Laceration — bleeding! Bandage it")
	game.queue_redraw()
	await shot("gameplay-wounded-hud.png")
	game._set_inventory(true)
	game.queue_redraw()
	await shot("gameplay-inventory-repair.png")
	game.free()
	quit()
