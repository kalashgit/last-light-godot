extends SceneTree
## Exhaustive "use everything" sweep in the real main scene. It does not judge outcomes: it calls every
## interaction, item action, recipe, event, survivor and faction option, panel and save path it can reach,
## and the runner then fails the build if the engine logged any SCRIPT ERROR while doing so.
## Each step prints "@@ <what>" first so an error can be traced to the call that caused it.
## godot --headless --fixed-fps 30 --path . -s tests/godot/test_fuzz.gd
var main: Node
var frame := 0
var done := false
var calls := 0

func _initialize() -> void:
	main = load("res://main.tscn").instantiate()
	root.add_child(main)

func mark(what: String) -> void:
	print("@@ " + what)

func settle(sim: Sim, seconds: float) -> void:
	var t := 0.0
	while t < seconds:
		sim.tick(1.0 / 30.0)
		t += 1.0 / 30.0
	_reset_player(sim)

func _reset_player(sim: Sim) -> void:
	var p: Player = sim.player
	if sim.vehicle != null:
		Actions.exit_vehicle(sim)
		sim.vehicle = null
	p.sleeping = false
	p.hidden = false
	p.grabbed_by = -1
	p.hp = 100.0
	p.wounds.clear()
	p.cancel_action()
	p.carrying = {}
	p.dragging = {}
	p.alive = true
	sim.dead = false
	sim.time_scale = 1.0

func kit(sim: Sim) -> void:
	var p: Player = sim.player
	for id in ["hammer", "saw", "screwdriver", "wrench", "pliers", "crowbar", "axe", "shovel", "kitchen_knife", "needle_thread", "scissors",
			"lighter", "cooking_pot", "gas_can", "watering_can", "whetstone", "water_filter", "fire_extinguisher", "pencil", "notebook", "radio",
			"binoculars", "compass", "flashlight", "car_keys", "multitool", "trowel", "fishing_rod", "bucket"]:
		if Items.DB.has(id): Inv.add_new(p.inv, id, 1, sim.hour)
	for id2 in ["plank", "nails", "scrap_metal", "wire", "sheet", "rag", "bandage", "disinfectant", "water_bottle", "canned_beans", "duct_tape",
			"glue", "metal_bar", "rope", "stone", "branch", "log", "glass_pane", "car_battery", "tyre_kit", "seeds_potato", "plastic_sheet", "screws", "twine"]:
		if Items.DB.has(id2): Inv.add_new(p.inv, id2, 10, sim.hour)
	for sk in Player.SKILLS: p.skills[sk] = 3000.0

func sweep_world(sim: Sim, tag: String) -> void:
	var p: Player = sim.player
	var home: Vector2 = p.pos
	var spots: Array = [home]
	for k in range(14):
		spots.append(home + Vector2(randf_range(-22, 22), randf_range(-22, 22)))
	for si in range(spots.size()):
		var sp: Vector2 = spots[si]
		for facing in [Vector2(1, 0), Vector2(-1, 0), Vector2(0, 1), Vector2(0, -1)]:
			_reset_player(sim)
			p.pos = sp
			sim.world.stream(p.pos, 3, 999)
			if sim.world.blocked(p.pos.x, p.pos.y, Player.R): continue
			p.facing = facing
			var targets: Array = Actions.targets(sim)
			for t in targets:
				var opts: Array = Actions.options(sim, t)
				for o in opts:
					mark("%s spot %d facing %s target %s option '%s'" % [tag, si, str(facing), t.get("kind", "?"), o["label"]])
					p.pos = sp
					p.facing = facing
					o["fn"].call()
					calls += 1
					settle(sim, 3.0)
					sim.world.stream(sp, 3, 999)
	p.pos = home
	sim.world.stream(home, 3, 999)

func sweep_recipes(sim: Sim) -> void:
	var p: Player = sim.player
	var home: Vector2 = p.pos
	for r in Recipes.LIST:
		_reset_player(sim)
		for inp in r.get("in", []):
			if Items.DB.has(String(inp[0])): Inv.add_new(p.inv, String(inp[0]), int(inp[1]) + 1, sim.hour)
		if r.has("learn"): p.known[String(r["learn"])] = true
		for k in range(8):
			p.pos = home + Vector2(randf_range(-10, 10), randf_range(-10, 10))
			if not sim.world.blocked(p.pos.x, p.pos.y, Player.R): break
		p.facing = Vector2(1, 0)
		mark("recipe %s" % r.get("id", r["n"]))
		Actions.craft(sim, r)
		calls += 1
		settle(sim, float(r.get("time", 3.0)) + 1.0)
	p.pos = home

func sweep_events(sim: Sim) -> void:
	for k in Sim.EVENTS:
		mark("event %s" % k)
		sim.world_event(String(k))
		calls += 1
		settle(sim, 2.0)
		sim._check_objectives()
	sim.objectives.clear()
	sim.zombies.list.clear()
	sim.burning.clear()

func sweep_npcs(sim: Sim) -> void:
	var p: Player = sim.player
	for ji in range(NpcSim.JOBS.size()):
		_reset_player(sim)
		var n = sim.npcs.spawn(p.pos + Vector2(1.0, 0.0), false)
		n.job = NpcSim.JOBS[ji]
		n.temper = NpcSim.TEMPERS[ji % NpcSim.TEMPERS.size()]
		n.trust = [10.0, 40.0, 70.0, 95.0][ji % 4]
		n.fac = (ji % 8) if ji % 3 == 0 else -1
		n.stock = ["bandage", "canned_beans", "battery"]
		for o in sim.npcs.options(n):
			if not sim.npcs.list.has(n): break
			mark("npc job %s temper %s option '%s'" % [n.job, n.temper, o["label"]])
			o["fn"].call()
			calls += 1
			settle(sim, 1.0)
		sim.npcs.update(0.5, 0.2)
	sim.npcs.list.clear()

func sweep_items(sim: Sim) -> void:
	var p: Player = sim.player
	var panels = main.panels
	var ids: Array = Items.DB.keys()
	for id in ids:
		_reset_player(sim)
		Inv.add_new(p.inv, String(id), 2, sim.hour)
		var it: Dictionary = Inv.find(p.inv, String(id))
		if it.is_empty(): continue
		var conts: Array = Actions.nearby_containers(sim)
		mark("item sheet %s" % id)
		panels.open("inv")
		panels._item_sheet(it, conts[0])
		var opts: Array = panels.last_opts.duplicate()
		for o in opts:
			if not p.inv.has(it): break
			mark("item %s action '%s'" % [id, o[0]])
			panels.open("inv")
			panels._item_sheet(it, Actions.nearby_containers(sim)[0])
			(o[1] as Callable).call()
			calls += 1
			panels.close()
			settle(sim, 6.0)
		panels.close()

func sweep_panels(sim: Sim) -> void:
	for pn in ["inv", "char", "craft", "map", "journal", "settings", "pause", "help", "import"]:
		mark("panel %s" % pn)
		main.panels.open(pn)
		main.panels.close()
		calls += 1

func _process(_dt: float) -> bool:
	frame += 1
	if done:
		return true
	if main.state == "title" and frame > 2:
		seed(31337)
		main.new_game(4242, "builder", {})
		var sim: Sim = main.sim
		sim.settings["god"] = true
		sim.settings["meta"] = false
		sim.zombies.wander_t = 1e9
		kit(sim)
		mark("panels")
		sweep_panels(sim)
		mark("npcs")
		sweep_npcs(sim)
		mark("events")
		sweep_events(sim)
		mark("world: house start")
		sweep_world(sim, "house")
		mark("recipes")
		sweep_recipes(sim)
		mark("items")
		sweep_items(sim)
		mark("save and load after everything")
		var ok_save: bool = SaveGame.save(sim, "fuzz_slot")
		var back: Sim = SaveGame.load_game("fuzz_slot")
		print("save ", ok_save, " load ", back != null)
		SaveGame.delete("fuzz_slot")
		for sk in ["farm", "cabin", "downtown"]:
			var s2 := Sim.new(500 + sk.length())
			s2.new_game("builder", [], sk)
			s2.settings["god"] = true
			s2.settings["meta"] = false
			s2.zombies.wander_t = 1e9
			kit(s2)
			sweep_world(s2, sk)
		print("FUZZ DONE: %d calls" % calls)
		done = true
		quit(0)
	return false
