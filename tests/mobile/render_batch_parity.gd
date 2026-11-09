extends SceneTree
## W08: the draw-call batcher must not visibly change the world. Renders the same
## frame with batching off and on and compares pixels. Needs a real display
## (xvfb-run is fine); exits 0 with SKIP under --headless because nothing renders.
##   xvfb-run -a godot --path . --rendering-driver opengl3 --script tests/mobile/render_batch_parity.gd

const MAX_MEAN_DELTA := 1.5    # mean absolute channel difference, 0..255
const MAX_CHANGED_RATIO := 0.03 # share of pixels differing by more than 24 levels
var output_dir := ""


func _initialize() -> void:
	for argument: String in OS.get_cmdline_user_args():
		if argument.begins_with("--output-dir="):
			output_dir = argument.trim_prefix("--output-dir=")
	call_deferred("run")


func frame(game: Node) -> Image:
	game.queue_redraw()
	await process_frame
	await RenderingServer.frame_post_draw
	game.queue_redraw()
	await process_frame
	await RenderingServer.frame_post_draw
	return root.get_texture().get_image()


func compare(a: Image, b: Image) -> Dictionary:
	var total := 0.0
	var changed := 0
	for y in range(0, a.get_height(), 2):
		for x in range(0, a.get_width(), 2):
			var ca := a.get_pixel(x, y)
			var cb := b.get_pixel(x, y)
			var d := (absf(ca.r - cb.r) + absf(ca.g - cb.g) + absf(ca.b - cb.b)) / 3.0 * 255.0
			total += d
			if d > 24.0:
				changed += 1
	var count := float(ceili(a.get_width() / 2.0) * ceili(a.get_height() / 2.0))
	return {"mean_delta": total / count, "changed_ratio": changed / count}


func run() -> void:
	if DisplayServer.get_name() == "headless":
		print("RENDER BATCH PARITY: SKIP (headless display renders nothing)")
		quit(0)
		return
	root.size = Vector2i(1334, 750)
	var game: Node = load("res://main.tscn").instantiate()
	root.add_child(game)
	game.set_process(false)
	game._restart_game()
	game.message_time = 0.0
	var failures: Array[String] = []
	var report: Array[String] = []
	for scenario in [["outdoor", Vector2(4.9, 9.35)], ["indoor", Vector2(3, 5)]]:
		game.player = scenario[1]
		for door: Dictionary in game.doors:
			door.open = scenario[0] == "indoor"
		game.camera_zoom = game._zoom_target()
		game.art.batching_enabled = false
		var reference: Image = await frame(game)
		var unbatched_calls := Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME)
		game.art.batching_enabled = true
		var batched: Image = await frame(game)
		var batched_calls := Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME)
		var result := compare(reference, batched)
		report.append("%s mean=%.3f changed=%.4f draw_calls %d->%d" % [scenario[0], result.mean_delta, result.changed_ratio, unbatched_calls, batched_calls])
		if not output_dir.is_empty():
			reference.save_png("%s/%s_unbatched.png" % [output_dir, scenario[0]])
			batched.save_png("%s/%s_batched.png" % [output_dir, scenario[0]])
		if result.mean_delta > MAX_MEAN_DELTA or result.changed_ratio > MAX_CHANGED_RATIO:
			failures.append(scenario[0] + " differs visibly")
		if batched_calls >= unbatched_calls:
			failures.append(scenario[0] + " batching did not reduce draw calls")
	game.free()
	for line in report:
		print("RENDER BATCH PARITY: " + line)
	if failures.is_empty():
		print("RENDER BATCH PARITY: PASS")
		quit(0)
	else:
		printerr("RENDER BATCH PARITY: FAIL " + ", ".join(failures))
		quit(1)
