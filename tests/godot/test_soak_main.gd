extends SceneTree
## Full-stack soak: the real main scene driven by a bot for ~2.5 simulated minutes
## (movement, combat, interaction, every panel, sleep, save). Fails on any script error.
## godot --headless --fixed-fps 30 --path . -s tests/godot/test_soak_main.gd
var main: Node
var frame := 0
var t0 := -1
var rng := RandomNumberGenerator.new()
var dir := Vector2.RIGHT
var worst_ms := 0.0
var total_ms := 0.0

func _initialize() -> void:
	rng.seed = 12345
	main = load("res://main.tscn").instantiate()
	root.add_child(main)

func _process(_dt: float) -> bool:
	frame += 1
	if main.state == "title" and t0 < 0:
		main.new_game(2024, "officer", {"zombies": 1.7})
		main.sim.settings["god"] = true
		t0 = frame
		return false
	if main.state != "play":
		return false
	var f: int = frame - t0
	var sim: Sim = main.sim
	var p: Player = sim.player
	var hud: Hud = main.hud
	var st: int = Time.get_ticks_usec()
	if f % 90 == 0:
		var a: float = rng.randf() * TAU
		dir = Vector2(cos(a), sin(a))
		hud.run_on = rng.randf() < 0.6
		p.sneaking = (not hud.run_on) and rng.randf() < 0.3
	# the bot steers through the HUD's own input path
	hud._stick_touch = 99
	hud._stick_vec = dir
	if f % 7 == 0:
		p.try_attack()
	if f % 61 == 0:
		Actions.interact(sim, rng.randf() < 0.5)
	if f % 200 == 50:
		main.open_panel(["inv", "char", "craft", "map", "pause"][(f / 200) % 5])
	if f % 200 == 60 and main.panels.is_open():
		main.panels.close()
	if main.panels.current == "menu":
		# pick a random context option like a player would
		var opts: Array = main.panels._menu_opts
		main.panels.close()
		if opts.size() > 0:
			(opts[rng.randi() % opts.size()]["fn"] as Callable).call()
	if f == 1500:
		p.fatigue = 80.0
		p.panic = 0.0
		sim.zombies.list.clear()
		sim.start_sleep(1.0)
	if f == 1560:
		sim.wake("soak wake")
	if f % 700 == 699:
		main.save_now()
	if f == 2400:
		# teleport far away to force heavy streaming, then come back
		p.pos += Vector2(160, 40)
	var ms: float = (Time.get_ticks_usec() - st) / 1000.0
	if f >= 4500:
		var states := {}
		for z in sim.zombies.list:
			states[Zombie.STATE_NAMES[z.state]] = states.get(Zombie.STATE_NAMES[z.state], 0) + 1
		print("soak: frames=", f, " day=", sim.day(), " hour=", snappedf(sim.hour_of_day(), 0.1), " kills=", p.kills, " zombies=", sim.zombies.list.size(), " ", states)
		print("soak: chunks=", sim.world.chunks.size(), " views=", main.view._chunks.size(), " zviews=", main.view._zviews.size(), " explored=", sim.world.explored.size(), " inv=", p.inv.size(), " hp=", snappedf(p.hp, 0.1))
		print("soak: main frame avg=", snappedf(main.frame_ms, 0.01), " ms  sim avg=", snappedf(main.sim_ms, 0.01), " ms")
		var okv: bool = sim.world.chunks.size() <= 81 and main.view._chunks.size() == sim.world.chunks.size() and p.alive
		print("RESULT: soak ", "ok" if okv else "FAILED")
		print("  %s  chunk views match loaded chunks and stay bounded" % ("PASS" if okv else "FAIL"))
		SaveGame.delete(main.SLOT)
		quit(0 if okv else 1)
	return false
