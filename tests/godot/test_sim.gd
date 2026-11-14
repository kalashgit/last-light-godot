extends SceneTree
## Headless gameplay regression test.  godot --headless --path . -s tests/godot/test_sim.gd
var fails := 0
var checks := 0

func ok(cond: bool, what: String) -> void:
	checks += 1
	if cond:
		print("  PASS  ", what)
	else:
		fails += 1
		print("  FAIL  ", what)

func run(sim: Sim, seconds: float, move := Vector2.ZERO, run_flag := false) -> void:
	var t := 0.0
	while t < seconds:
		sim.tick(1.0 / 30.0, move, run_flag)
		t += 1.0 / 30.0

func _init() -> void:
	seed(20261112)      # the game uses the global RNG for combat rolls: make the run repeatable
	print("== new game")
	var sim := Sim.new(4242)
	sim.new_game("builder")
	var p: Player = sim.player
	var w: World = sim.world
	ok(w.bld(floori(p.pos.x), floori(p.pos.y)) != 0, "spawn is indoors")
	ok(not w.blocked(p.pos.x, p.pos.y, Player.R), "spawn is not blocked")
	ok(w.chunks.size() >= 25, "chunks streamed around spawn (%d)" % w.chunks.size())
	ok(p.skill_level("carpentry") == 3, "occupation skills applied")
	ok(Inv.count(p.inv, "nails") == 30 and not p.weapon.is_empty(), "occupation items + weapon equipped")
	var zc := sim.zombies.list.size()
	var near := 0
	for z in sim.zombies.list:
		if z.pos.distance_to(p.pos) < 12.0:
			near += 1
	ok(zc > 0, "zombies populated loaded area (%d)" % zc)
	ok(near == 0, "no zombies inside the safe start radius")

	print("== movement & collision")
	var start := p.pos
	run(sim, 2.0, Vector2(1, 0))
	ok(p.pos.distance_to(start) > 0.3, "player moves with joystick input (%.2f tiles)" % p.pos.distance_to(start))
	# walk into every direction for a while: must never end inside something solid
	var stuck_inside := false
	for d in [Vector2(1, 0), Vector2(0, 1), Vector2(-1, 0), Vector2(0, -1), Vector2(1, 1), Vector2(-1, 1)]:
		run(sim, 1.5, d, true)
		if w.blocked(p.pos.x, p.pos.y, Player.R * 0.9):
			stuck_inside = true
	ok(not stuck_inside, "collision never leaves the player inside a wall")
	ok(p.endurance < 100.0, "running drains endurance (%.0f)" % p.endurance)

	print("== doors")
	# find a door edge in the start building and operate it through the public API
	var found := Vector3i(-1, -1, -1)
	var px := floori(p.pos.x)
	var py := floori(p.pos.y)
	for y in range(py - 12, py + 12):
		for x in range(px - 12, px + 12):
			for s in range(2):
				var wid := w.wall(x, y, s)
				if wid != 0 and (wid & 3) == Defs.WS_DOOR and not Defs.wall_is_fence(wid) and found.x < 0 and (w.bld(x, y) == sim.safe_bld or w.bld(x - (1 if s == 1 else 0), y - (1 if s == 0 else 0)) == sim.safe_bld):
					found = Vector3i(x, y, s)
	ok(found.x >= 0, "start house has a door")
	if found.x >= 0:
		w.set_edge_state(found.x, found.y, found.z, 0)
		ok(w.edge_blocks(found.x, found.y, found.z), "closed door blocks movement")
		ok(w.edge_opaque(found.x, found.y, found.z), "closed door blocks sight")
		p.pos = Vector2(found.x + 0.5, found.y + 0.5)
		p.facing = Vector2(0, -1) if found.z == 0 else Vector2(-1, 0)
		Actions.interact(sim)
		ok(not w.edge_blocks(found.x, found.y, found.z), "INTERACT opens the door")
		Actions.interact(sim)
		ok(w.edge_blocks(found.x, found.y, found.z), "INTERACT closes it again")
		# barricade
		Inv.add_new(p.inv, "plank", 2)
		var opts: Array = Actions.options(sim, {"kind": "edge", "x": found.x, "y": found.y, "side": found.z})
		var did := false
		for o in opts:
			if String(o["label"]).begins_with("Barricade"):
				(o["fn"] as Callable).call()
				did = true
		run(sim, 4.0)
		var planks := (w.edge_state(found.x, found.y, found.z) & Defs.ES_PLANK_MASK) >> Defs.ES_PLANK_SHIFT
		ok(did and planks == 1, "barricading adds a plank (%d)" % planks)
		ok(Inv.count(p.inv, "nails") == 28, "barricade consumed nails")
		var broke := false
		for i in range(40):
			if w.damage_edge(found.x, found.y, found.z, 10.0):
				broke = true
				break
		ok(broke, "planks can be broken by damage")

	print("== combat")
	var open := _find_open(sim)
	p.pos = open
	sim.zombies.list.clear()
	sim.zombies.wander_t = 99999.0
	var z1: Zombie = sim.zombies.spawn(p.pos + Vector2(0.9, 0.0), 0)
	z1.hp = 60.0
	p.facing = Vector2(1, 0)
	var kills0 := p.kills
	var swings := 0
	while z1.hp > 0.0 and swings < 40:
		z1.pos = p.pos + Vector2(0.9, 0.0)
		z1.state = Zombie.IDLE
		p.try_attack()
		run(sim, 1.0)
		swings += 1
	ok(p.kills == kills0 + 1, "melee kills a zombie (%d swings)" % swings)
	ok(p.skills["short_blunt"] > Player.XP_LEVELS[2], "combat grants weapon XP")
	var corpse_found := false
	var cc: Chunk = w.chunk_at(floori(p.pos.x), floori(p.pos.y))
	for ch in w.chunks.values():
		if ch.corpses.size() > 0:
			corpse_found = true
	ok(corpse_found, "kill leaves a corpse")
	# zombie attacks player
	var z2: Zombie = sim.zombies.spawn(p.pos + Vector2(3.0, 0.0), 0)
	z2.dir = Vector2(-1, 0)
	var hp0 := p.hp
	var t := 0.0
	while t < 12.0 and p.hp >= hp0:
		sim.tick(1.0 / 30.0)
		t += 1.0 / 30.0
	ok(z2.state >= Zombie.CHASE or p.hp < hp0, "zombie notices and chases the player")
	ok(p.hp < hp0, "zombie attack damages the player (%.0f -> %.0f)" % [hp0, p.hp])
	ok(p.wounds.size() > 0, "attack leaves a wound")
	sim.zombies.list.erase(z2)
	# hearing
	var z3: Zombie = sim.zombies.spawn(p.pos + Vector2(0.0, 3.0), 0)      # near enough that walls in between cannot swallow it
	z3.dir = Vector2(0, 1)
	sim.settings["god"] = true
	var saved_pos := p.pos
	p.pos = Vector2(-9999, -9999)   # out of sight; only the noise remains
	sim.noise(saved_pos, 20.0)
	for i in range(30):
		sim.zombies.update(1.0 / 30.0)
	p.pos = saved_pos
	ok(z3.state == Zombie.INVESTIGATE, "zombie investigates a noise it cannot see (state %s)" % Zombie.STATE_NAMES[z3.state])
	sim.zombies.list.erase(z3)
	sim.settings["god"] = false

	print("== firearms")
	Inv.add_new(p.inv, "pistol", 1)
	Inv.add_new(p.inv, "ammo_9mm", 24)
	var pistol: Dictionary = Inv.find(p.inv, "pistol")
	p.weapon = pistol
	p.try_attack()            # empty -> reload
	run(sim, 3.0 * p.hand_factor())      # the wound from the attack above slows hands
	ok(int(pistol["u"]) == 12, "reload fills the magazine (%d)" % int(pistol["u"]))
	p.panic = 0.0
	var z4: Zombie = sim.zombies.spawn(p.pos + Vector2(4.0, 0.0), 0)
	z4.hp = 40.0
	p.facing = Vector2(1, 0)
	var shots := 0
	while sim.zombies.list.has(z4) and shots < 12:
		z4.state = Zombie.IDLE
		p.try_attack()
		run(sim, 0.6)
		shots += 1
	ok(not sim.zombies.list.has(z4), "pistol kills at range (%d shots)" % shots)
	ok(int(pistol["u"]) < 12, "shots consume ammunition")
	sim.zombies.list.clear()
	ok(p.alive, "player survived the combat tests (hp %.0f)" % p.hp)

	print("== wounds & medicine")
	p.wounds.clear()
	p.add_wound(2, "laceration")
	var hp1 := p.hp
	p.tick_needs(1.0)
	ok(p.hp < hp1, "open wound bleeds over time")
	Inv.add_new(p.inv, "bandage", 1)
	p.use_med(Inv.find(p.inv, "bandage"), p.wounds[0])
	run(sim, 4.0)
	ok(p.wounds[0]["band"], "bandage applied to wound")
	var hp2 := p.hp
	p.hunger = 10.0
	p.thirst = 10.0
	p.tick_needs(1.0)
	ok(p.hp >= hp2, "bandaged wound stops bleeding")

	print("== needs & food")
	p.hunger = 60.0
	Inv.add_new(p.inv, "canned_beans", 1)
	Inv.add_new(p.inv, "can_opener", 1)
	p.consume(Inv.find(p.inv, "canned_beans"))
	run(sim, 3.5)
	ok(p.hunger < 40.0, "eating reduces hunger (%.0f)" % p.hunger)
	ok(Inv.count(p.inv, "empty_can") == 1, "eating a can leaves an empty tin")
	var h0 := p.hunger
	p.tick_needs(6.0)
	ok(p.hunger > h0 + 10.0, "hunger grows with time")
	var old := Items.make("bread", 1, sim.hour - 200.0)
	ok(Items.fresh_state(old, sim.hour) == 2, "perishable food rots")

	print("== looting")
	var cont: Array = Actions.nearby_containers(sim)
	ok(cont.size() >= 1 and cont[0]["label"] == "Ground", "ground container always available")
	var total_loot := 0
	var containers := 0
	for ch in w.chunks.values():
		for i in range(256):
			var d: Dictionary = Defs.obj(ch.obj[i] & 1023)
			if d.has("c") and d["c"] != "" and ch.bld[i] != 0 and Defs.o_part(ch.obj[i]) == 0:
				var items: Array = w.container_at(ch.cx * 16 + (i & 15), ch.cy * 16 + (i >> 4))
				containers += 1
				for it in items:
					total_loot += int(it["n"])
	ok(containers > 20 and total_loot > containers, "containers hold generated loot (%d items in %d containers)" % [total_loot, containers])

	print("== crafting & building")
	Inv.add_new(p.inv, "sheet", 1)
	ok(Actions.craft(sim, Recipes.by_id("rip_sheet")), "craft: rip sheet starts")
	run(sim, 3.0)
	ok(Inv.count(p.inv, "rag") == 4, "craft produced 4 rags")
	Inv.add_new(p.inv, "plank", 6)
	# stand somewhere open and build a wall + crate
	sim.zombies.list.clear()
	sim.settings["god"] = true
	p.pos = open
	p.facing = Vector2(1, 0)
	var e: Vector3i = p.front_edge()
	ok(Actions.craft(sim, Recipes.by_id("wall")), "build: wooden wall starts")
	run(sim, 8.0)
	ok(w.wall(e.x, e.y, e.z) == Defs.wall(Defs.WM_BUILT_PLANK), "wall placed on the facing edge")
	ok(w.edge_blocks(e.x, e.y, e.z), "built wall blocks movement")
	p.facing = Vector2(0, 1)
	var ft: Vector2i = p.front_tile()
	ok(Actions.craft(sim, Recipes.by_id("crate")), "build: crate starts")
	run(sim, 7.0)
	ok(Defs.o_id(w.obj(ft.x, ft.y)) == Defs.O_WOOD_CRATE, "crate placed in front")

	print("== farming")
	Inv.add_new(p.inv, "trowel", 1)
	Inv.add_new(p.inv, "seeds_potato", 2)
	p.facing = Vector2(-1, 0)
	var soil: Vector2i = p.front_tile()
	ok(Actions.craft(sim, Recipes.by_id("till")), "till soil starts")
	run(sim, 5.0)
	ok(w.ground(soil.x, soil.y) == Defs.G_SOIL, "ground tilled")
	var so: Array = Actions.options(sim, {"kind": "soil", "x": soil.x, "y": soil.y})
	(so[0]["fn"] as Callable).call()
	run(sim, 3.0)
	ok(Defs.o_id(w.obj(soil.x, soil.y)) == Defs.O_CROP_POTATO, "seed planted")
	var ent: Dictionary = w.ent(soil.x, soil.y)
	ent["w"] = 70.0
	var cchunk: Chunk = w.chunk_at(soil.x, soil.y)
	for i in range(120):
		ent["w"] = 70.0          # watered, but not waterlogged (standing water breeds mildew)
		sim._sim_ents(cchunk, 1.0, false)
	ok(int(ent["s"]) == 3 and Defs.o_part(w.obj(soil.x, soil.y)) == 3, "crop grows to maturity (stage %d)" % int(ent["s"]))
	var co: Array = Actions.options(sim, {"kind": "obj", "x": soil.x, "y": soil.y})
	(co[0]["fn"] as Callable).call()
	run(sim, 3.5)
	ok(Inv.count(p.inv, "potato") >= 3, "harvest yields potatoes (%d)" % Inv.count(p.inv, "potato"))

	print("== pathfinding")
	var goal := sim.safe_pos
	var path := Pathfinder.find(w, floori(p.pos.x), floori(p.pos.y), floori(goal.x), floori(goal.y), 1500, 14.0)
	ok(path.size() > 0, "A* finds a route back to the start house (%d steps, %d iterations)" % [path.size(), Pathfinder.iterations])

	print("== time, weather, utilities")
	var hour0 := sim.hour
	run(sim, 10.0)
	ok(sim.hour > hour0, "clock advances (%.3f h in 10 s)" % (sim.hour - hour0))
	ok(sim.has_power(0, 0), "power is on at the start")
	sim.hour = sim.power_off_h + 1.0
	ok(not sim.has_power(0, 0), "power fails after the shutoff day (day %d)" % int(sim.power_off_h / 24.0 + 1))
	sim.hour = hour0 + 0.01

	print("== save / load")
	p.wounds.clear()
	p.hp = 77.0
	var marker := Items.make("toy", 1)
	w.drop_item(floori(p.pos.x), floori(p.pos.y), marker)
	var slot := "test_slot"
	SaveGame.delete(slot)
	var zcount := sim.zombies.list.size()
	var kills := p.kills
	var inv_count := p.inv.size()
	var ppos := p.pos
	ok(SaveGame.save(sim, slot), "save succeeds")
	ok(SaveGame.exists(slot), "save file exists")
	var sim2: Sim = SaveGame.load_game(slot)
	ok(sim2 != null, "load succeeds")
	if sim2 != null:
		var p2: Player = sim2.player
		ok(p2.pos.distance_to(ppos) < 0.001 and absf(p2.hp - 77.0) < 0.001, "player position and health restored")
		ok(p2.inv.size() == inv_count and p2.kills == kills, "inventory and kill count restored")
		ok(not p2.weapon.is_empty() and p2.weapon["id"] == "pistol", "equipped weapon restored")
		ok(p2.skill_level("carpentry") >= 3, "skills restored")
		ok(sim2.world.wall(e.x, e.y, e.z) == Defs.wall(Defs.WM_BUILT_PLANK), "built wall persisted")
		ok(Defs.o_id(sim2.world.obj(ft.x, ft.y)) == Defs.O_WOOD_CRATE, "built crate persisted")
		ok(Inv.count(sim2.world.items_at(floori(ppos.x), floori(ppos.y)), "toy") == 1, "dropped item persisted")
		ok(absf(sim2.hour - sim.hour) < 0.001, "clock restored")
		ok(absi(sim2.zombies.list.size() - zcount) <= 2, "zombie population restored (%d vs %d)" % [sim2.zombies.list.size(), zcount])
		var corpses2 := 0
		for ch in sim2.world.chunks.values():
			corpses2 += ch.corpses.size()
		ok(corpses2 >= 2, "corpses persisted (%d)" % corpses2)
		# travel far and come back: world must stay consistent
		var far: Vector2 = p2.pos + Vector2(200, 0)
		sim2.settings["god"] = true
		p2.pos = far
		for i in range(80):
			sim2.world.stream(p2.pos, 3, 4)
			sim2._process_world_events()
		p2.pos = ppos
		for i in range(80):
			sim2.world.stream(p2.pos, 3, 4)
			sim2._process_world_events()
		ok(sim2.world.wall(e.x, e.y, e.z) == Defs.wall(Defs.WM_BUILT_PLANK), "changes survive chunk unload / reload")
		ok(SaveGame.save(sim2, slot), "second save (with unloaded chunk store) succeeds")
	SaveGame.delete(slot)

	print("== long soak (zombie AI, streaming, 3 simulated minutes)")
	var sim3 := Sim.new(99)
	sim3.new_game("athlete")
	sim3.settings["god"] = true
	var t0 := Time.get_ticks_msec()
	var worst := 0
	var frames := 0
	var dirs := [Vector2(1, 0), Vector2(0.7, 0.7), Vector2(0, 1), Vector2(-0.7, 0.7), Vector2(-1, 0), Vector2(0, -1)]
	for i in range(30 * 180):
		var d: Vector2 = dirs[(i / 240) % dirs.size()]
		var f0 := Time.get_ticks_usec()
		sim3.tick(1.0 / 30.0, d, true)
		worst = maxi(worst, Time.get_ticks_usec() - f0)
		frames += 1
	var ms := Time.get_ticks_msec() - t0
	var states := {}
	for z in sim3.zombies.list:
		states[Zombie.STATE_NAMES[z.state]] = states.get(Zombie.STATE_NAMES[z.state], 0) + 1
	print("  soak: ", frames, " ticks in ", ms, " ms (avg ", snappedf(float(ms) / frames, 0.001), " ms, worst ", worst / 1000.0, " ms), zombies=", sim3.zombies.list.size(), " ", states, " chunks=", sim3.world.chunks.size(), " stored=", sim3.world.store.size())
	ok(float(ms) / frames < 8.0, "average sim tick under 8 ms")
	ok(sim3.world.chunks.size() <= 81, "chunk streaming unloads distant chunks")

	print("")
	print("RESULT: %d checks, %d failed" % [checks, fails])
	quit(1 if fails > 0 else 0)

func _find_open(sim: Sim) -> Vector2:
	var w: World = sim.world
	var c := sim.safe_pos
	for r in range(3, 60):
		for a in range(16):
			var q: Vector2 = c + Vector2(cos(a / 16.0 * TAU), sin(a / 16.0 * TAU)) * r
			var x := floori(q.x)
			var y := floori(q.y)
			var good := w.bld(x, y) == 0 and Defs.ground_is_natural(w.ground(x, y))
			for dy in range(-1, 2):
				for dx in range(-1, 6):      # 3x3 to build in plus a clear lane to the east for approaching zombies
					if w.obj(x + dx, y + dy) != 0 or w.tile_blocked(x + dx, y + dy) or w.wall(x + dx, y + dy, 0) != 0 or w.wall(x + dx, y + dy, 1) != 0 or not Defs.ground_is_natural(w.ground(x + dx, y + dy)):
						good = false
			if good:
				return Vector2(x + 0.5, y + 0.5)
	print("  FAIL  no open test area found near the start")
	return c
