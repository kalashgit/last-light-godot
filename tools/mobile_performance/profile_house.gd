extends SceneTree
## W08 repeatable presentation-layer profiler for the playable house (main.tscn).
## Runs fixed, deterministic scenarios and prints one JSON line per scenario.
## Host/Xvfb numbers are relative comparisons only; they are NOT iPhone results.
##
## Usage (needs a display for render metrics; headless gives CPU-only numbers):
##   xvfb-run -a godot --path . --rendering-driver opengl3 \
##     --script tools/mobile_performance/profile_house.gd -- --frames=120 --size=1334x750

const MobileHUD := preload("res://scripts/mobile_hud.gd")

## HUD stand-in that keeps layout (input rects) but draws nothing, so the
## world's own share of draw calls can be separated from the HUD's share.
class NoDrawHUD extends MobileHUD:
	func draw(_game) -> void:
		pass

var frames := 120
var size := Vector2i(1334, 750)


func _initialize() -> void:
	for argument: String in OS.get_cmdline_user_args():
		if argument.begins_with("--frames="):
			frames = maxi(30, int(argument.trim_prefix("--frames=")))
		elif argument.begins_with("--size="):
			var parts := argument.trim_prefix("--size=").split("x")
			if parts.size() == 2:
				size = Vector2i(int(parts[0]), int(parts[1]))
	call_deferred("run")


func percentile(samples: Array[float], portion: float) -> float:
	if samples.is_empty():
		return 0.0
	var ordered := samples.duplicate()
	ordered.sort()
	return ordered[mini(ordered.size() - 1, int(floor(portion * ordered.size())))]


func fresh_game() -> Node:
	var game: Node = load("res://main.tscn").instantiate()
	root.add_child(game)
	game.set_process(false)
	game._restart_game()
	game.god_mode = true
	game.message_time = 0.0
	return game


func measure(name: String, game: Node) -> Dictionary:
	game._layout_controls()
	game.camera_zoom = game._zoom_target()
	var wall: Array[float] = []
	var draw_calls: Array[float] = []
	var cpu_draw: Array[float] = []
	var visible_sprites := 0
	for frame in range(frames + 20):
		var started := Time.get_ticks_usec()
		game._process(1.0 / 60.0)
		game.queue_redraw()
		await process_frame
		await RenderingServer.frame_post_draw
		if frame < 20:
			continue
		wall.append(float(Time.get_ticks_usec() - started) / 1000.0)
		draw_calls.append(Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME))
		cpu_draw.append(Performance.get_monitor(Performance.TIME_PROCESS) * 1000.0)
	if game.has_method("_visible_sprite_count"):
		visible_sprites = game._visible_sprite_count()
	return {
		"scenario": name,
		"frames": wall.size(),
		"draw_calls_p50": percentile(draw_calls, .5),
		"draw_calls_max": draw_calls.max() if not draw_calls.is_empty() else 0,
		"frame_wall_ms_p50": snappedf(percentile(wall, .5), 0.01),
		"frame_wall_ms_p95": snappedf(percentile(wall, .95), 0.01),
		"frame_wall_ms_p99": snappedf(percentile(wall, .99), 0.01),
		"process_ms_p50": snappedf(percentile(cpu_draw, .5), 0.001),
		"objects_in_frame": Performance.get_monitor(Performance.RENDER_TOTAL_OBJECTS_IN_FRAME),
		"primitives_in_frame": Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME),
		"texture_mem_mb": snappedf(Performance.get_monitor(Performance.RENDER_TEXTURE_MEM_USED) / 1048576.0, 0.01),
		"static_mem_mb": snappedf(Performance.get_monitor(Performance.MEMORY_STATIC) / 1048576.0, 0.01),
		"node_count": Performance.get_monitor(Performance.OBJECT_NODE_COUNT),
	}


func run() -> void:
	root.size = size
	root.content_scale_size = size
	var results: Array[Dictionary] = []
	var load_started := Time.get_ticks_usec()
	var game := fresh_game()
	await process_frame
	var load_ms := float(Time.get_ticks_usec() - load_started) / 1000.0

	# 1. Outdoors at the spawn point (front yard).
	results.append(await measure("outdoor_spawn", game))
	# 2. Indoors, furnished living room, doors open, adaptive indoor zoom.
	game.player = Vector2(3, 5)
	for door: Dictionary in game.doors:
		door.open = true
	results.append(await measure("indoor_furnished", game))
	# 3. Same view with the HUD drawing disabled: world-only share.
	var real_hud = game.hud
	game.hud = NoDrawHUD.new()
	results.append(await measure("indoor_world_only", game))
	game.hud = real_hud
	# 4. Inventory open with supplies (container presentation).
	for id in ["ll_food_bean_tin", "ll_food_water_bottle", "ll_medical_sterile_bandage", "ll_tools_claw_hammer", "ll_tools_hatchet", "ll_crafting_pine_plank"]:
		if game.survival.definitions.has(id):
			game.survival.add(id, 1)
	game.inventory_open = true
	game.paused = true
	results.append(await measure("inventory_open", game))
	game.inventory_open = false
	game.paused = false
	# 5. Doorway transition: walk across the front door threshold and back.
	game.player = Vector2(4.9, 7.6)
	results.append(await measure("doorway_threshold", game))

	var info := {
		"scope": "HOST EMULATION ONLY - not iPhone/Xogot evidence",
		"engine": Engine.get_version_info()["string"],
		"display": DisplayServer.get_name(),
		"adapter": RenderingServer.get_video_adapter_name(),
		"renderer": ProjectSettings.get_setting("rendering/renderer/rendering_method"),
		"viewport": [size.x, size.y],
		"frames_per_scenario": frames,
		"scene_load_ms": snappedf(load_ms, 0.1),
	}
	print("MOBILE_PROFILE_INFO: " + JSON.stringify(info))
	for entry in results:
		print("MOBILE_PROFILE: " + JSON.stringify(entry))
	game.free()
	quit()
