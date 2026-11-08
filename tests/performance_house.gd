extends SceneTree
## Repeatable host-only observations. CPU simulation timings exclude rendering;
## rendered frame wall times include display synchronization. No phone performance claim.


func _initialize() -> void:
	call_deferred("observe")


func percentile(samples: Array[float], portion: float) -> float:
	var ordered := samples.duplicate()
	ordered.sort()
	return ordered[mini(ordered.size() - 1, int(floor(portion * ordered.size())))]


func observe() -> void:
	root.size = Vector2i(1560, 720)
	root.content_scale_size = Vector2i(1560, 720)
	var game = load(OS.get_environment("LL_SCENE") if OS.get_environment("LL_SCENE") != "" else "res://main.tscn").instantiate()
	root.add_child(game)
	game.set_process(false)
	game._restart_game()
	game.god_mode = true
	game.player = Vector2(3, 5)
	for door: Dictionary in game.doors:
		door.open = true
	game._layout_controls()
	var cpu_samples: Array[float] = []
	for frame in range(600):
		var started := Time.get_ticks_usec()
		game._process(1.0 / 60.0)
		cpu_samples.append(float(Time.get_ticks_usec() - started) / 1000.0)
	var metrics := {
		"scope": "host observations, not iPhone or Xogot",
		"engine": Engine.get_version_info()["string"],
		"display": DisplayServer.get_name(),
		"cpu_simulation_samples": cpu_samples.size(),
		"cpu_simulation_ms_p50": percentile(cpu_samples, .5),
		"cpu_simulation_ms_p95": percentile(cpu_samples, .95),
		"cpu_simulation_ms_max": cpu_samples.max(),
		"viewport": [1560, 720],
	}
	if DisplayServer.get_name() != "headless":
		var frame_samples: Array[float] = []
		for frame in range(180):
			var started := Time.get_ticks_usec()
			game._process(1.0 / 60.0)
			game.queue_redraw()
			await process_frame
			await RenderingServer.frame_post_draw
			if frame >= 30:
				frame_samples.append(float(Time.get_ticks_usec() - started) / 1000.0)
		metrics["rendered_frames_after_warmup"] = frame_samples.size()
		metrics["rendered_frame_wall_ms_p50"] = percentile(frame_samples, .5)
		metrics["rendered_frame_wall_ms_p95"] = percentile(frame_samples, .95)
		metrics["draw_calls"] = Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME)
		metrics["texture_memory_bytes"] = Performance.get_monitor(Performance.RENDER_TEXTURE_MEM_USED)
		metrics["video_adapter"] = RenderingServer.get_video_adapter_name()
	else:
		metrics["rendering"] = "UNVERIFIED in headless run"
	print("HOUSE_PERFORMANCE: " + JSON.stringify(metrics))
	game.free()
	quit()
