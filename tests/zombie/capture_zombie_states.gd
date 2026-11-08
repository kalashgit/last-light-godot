extends SceneTree
## Worker 03 runtime screenshots of real zombie states in main.tscn (needs a display,
## e.g. xvfb-run). Zombie bodies are PROCEDURAL PLACEHOLDER drawings, not approved art.
## Desktop landscape viewport is emulation, never iPhone/Xogot verification.

var output_dir := "/tmp/last-light-zombie-captures"
var game


func _initialize() -> void:
	for argument: String in OS.get_cmdline_user_args():
		if argument.begins_with("--output-dir="):
			output_dir = argument.trim_prefix("--output-dir=")
	call_deferred("capture")


func sim(seconds: float) -> void:
	for f in range(roundi(seconds * 60.0)):
		game._process(1.0 / 60.0)


func place(i: int, pos: Vector2, facing: Vector2) -> void:
	game.infected[i] = pos
	game.zombie_health[i] = 3
	game.zombies.sync_bodies(game.infected, game.zombie_health)
	game.zombies.agents[i].facing = facing.normalized()
	game.zombies.agents[i].idle_left = 999.0


func shot(name: String) -> bool:
	game.message_time = 0
	game.queue_redraw()
	await process_frame
	await RenderingServer.frame_post_draw
	var picture := root.get_texture().get_image()
	var path := "%s/zombie-%s-1152x720.png" % [output_dir, name]
	if picture.save_png(path) != OK:
		printerr("CAPTURE: failed " + path)
		return false
	var states: Array = []
	for a in game.zombies.agents:
		states.append("%s/%s/%s" % [a.state, a.anim_clip, a.posture])
	print("CAPTURE: %s states=%s" % [path, str(states)])
	return true


func capture() -> void:
	if DisplayServer.get_name() == "headless":
		printerr("CAPTURE: requires a graphical display; no screenshot produced")
		quit(1)
		return
	DirAccess.make_dir_recursive_absolute(output_dir)
	game = load("res://main.tscn").instantiate()
	root.add_child(game)
	root.size = Vector2i(1152, 720)
	root.content_scale_size = Vector2i(1152, 720)
	game.set_process(false)
	game._restart_game()
	game.god_mode = true
	await process_frame
	game._layout_controls()
	var ok := true
	# 1. Pursuit + attack in the yard.
	game.player = Vector2(-3.0, 9.0)
	place(0, Vector2(-3.0, 11.5), Vector2(0, -1))
	place(1, Vector2(-1.2, 12.0), Vector2(-1, -1))
	sim(1.9)
	ok = await shot("pursue") and ok
	# 2. Knockdown and stagger reactions.
	game.zombies.notify_hit(0, "melee", game.player, 2.0, 2)
	game.zombie_health[0] = 2
	game.zombies.notify_hit(0, "shove", game.player, 0.0, 2)
	game.zombies.notify_hit(1, "melee", game.player, 1.0, 2)
	game.zombie_health[1] = 2
	sim(.9)
	ok = await shot("knockdown-stagger") and ok
	# 3. Crawler and corpse.
	game.zombies.agents[0].posture = "crawling"
	game.zombie_health[1] = 0
	sim(2.5)
	ok = await shot("crawler-corpse") and ok
	# 4. Breaching the closed front door after a noise.
	game._restart_game()
	game.god_mode = true
	game.zombie_health[1] = 0
	game.player = Vector2(5.4, 6.6)
	place(0, Vector2(5.4, 9.4), Vector2(0, -1))
	game.doors[0].open = true
	game._toggle_door(0)
	sim(2.5)
	ok = await shot("door-breach") and ok
	game.free()
	quit(0 if ok else 1)
