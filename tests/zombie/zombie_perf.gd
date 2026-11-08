extends SceneTree
## Worker 03 AI timing on this host (NOT an iPhone measurement). Measures
## ZombieDirector.update() wall time for several populations on the house lot with the
## player walking a fixed loop, plus the full main-scene step with the default two zombies.
## Pass/fail gate is only functional (budget respected, no crash); timings are reported.

const Director := preload("res://scripts/zombie/zombie_director.gd")
const Spawner := preload("res://scripts/zombie/zombie_spawner.gd")

var game


func _initialize() -> void:
	call_deferred("run")


func population(n: int) -> Director:
	var d := Director.new()
	d.setup(game)
	var placed := 0
	var k := 0
	while placed < n and k < n * 30:
		var p := Vector2(-6.4 + Spawner.unit(k, "px") * 22.8, -6.4 + Spawner.unit(k, "py") * 22.8)
		k += 1
		if game._blocked(p, .2):
			continue
		d.spawn({"world_seed": 99, "region": "perf", "index": k, "context": "road", "position": p})
		placed += 1
	return d


func run() -> void:
	game = load("res://main.tscn").instantiate()
	root.add_child(game)
	game.set_process(false)
	game._restart_game()
	game.set_process(false)
	for door in game.doors:
		door.open = true
	var ok := true
	print("ZOMBIE_PERF: Godot %s, %s, %d logical CPUs, debug=%s" % [Engine.get_version_info().string, OS.get_name(), OS.get_processor_count(), OS.is_debug_build()])
	print("ZOMBIE_PERF: n | mean_us | p95_us | max_us | full/tick | sight/tick | A*/s | budget")
	for n in [2, 10, 25, 50, 100, 200]:
		var d := population(n)
		var samples: Array[int] = []
		var frames := 60 * 10
		for f in range(frames):
			var t := f / 60.0
			var player := Vector2(4.5, 4.0) + Vector2(cos(t * .4), sin(t * .4)) * 7.0
			d.set_target(player, Vector2(-sin(t * .4), cos(t * .4)) * 2.8, true, false, false, 100)
			if f % 36 == 0:
				d.emit_noise(player, 3.5, "footstep")
			d.update(1.0 / 60.0)
			samples.append(int(d.stats.usec_last))
		samples.sort()
		var mean := 0.0
		for s in samples:
			mean += s
		mean /= samples.size()
		var full := float(d.stats.full_updates) / frames
		if full > d.near_budget + .001:
			ok = false
		print("ZOMBIE_PERF: %d | %.1f | %d | %d | %.1f | %.1f | %.1f | %d" % [n, mean, samples[int(samples.size() * .95)], samples.back(), full, float(d.stats.sight_checks) / frames, float(d.nav.paths_computed) / 10.0, d.near_budget])
	# Main scene: full _process step (player, survival, zombies) with the default pair.
	game._restart_game()
	game.set_process(false)
	game.god_mode = true
	game.player = Vector2(-3, 6)
	var steps: Array[int] = []
	for f in range(600):
		var t0 := Time.get_ticks_usec()
		game._process(1.0 / 60.0)
		steps.append(Time.get_ticks_usec() - t0)
	steps.sort()
	print("ZOMBIE_PERF: main.tscn _process (2 zombies, no draw) median %d us, p95 %d us" % [steps[300], steps[570]])
	print("ZOMBIE_PERF: %s (host timing only; iPhone/Xogot UNVERIFIED)" % ("PASS" if ok else "FAIL"))
	game.free()
	quit(0 if ok else 1)
