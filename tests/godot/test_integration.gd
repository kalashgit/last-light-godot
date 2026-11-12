extends SceneTree
## Cross-system checks: each block proves that one system really changes another.
## godot --headless --path . -s tests/godot/test_integration.gd
var fails := 0
var checks := 0

func ok(cond: bool, what: String) -> void:
	checks += 1
	if not cond: fails += 1
	print("  %s  %s" % ["PASS" if cond else "FAIL", what])

func run(sim: Sim, seconds: float, move := Vector2.ZERO, run_flag := false) -> void:
	var t := 0.0
	while t < seconds:
		sim.tick(1.0 / 30.0, move, run_flag)
		t += 1.0 / 30.0

func quiet(sim: Sim) -> void:
	sim.zombies.list.clear()
	sim.zombies.wander_t = 1e9
	sim.npcs.list.clear()
	sim.settings["god"] = true
	sim.settings["meta"] = false
	sim.settings["flyover"] = 0

## flatten a rectangle into open grass so a scenario does not depend on what the generator put there
func bulldoze(sim: Sim, r: Rect2i) -> void:
	var w: World = sim.world
	for y in range(r.position.y, r.end.y + 1):
		for x in range(r.position.x, r.end.x + 1):
			if w.obj(x, y) != 0: w.set_obj(x, y, 0)
			w.set_wall(x, y, 0, 0)
			w.set_wall(x, y, 1, 0)
			w.set_ground(x, y, Defs.G_DIRT)
	for ch in w.chunks.values():
		var keep: Array = []
		for cp in ch.corpses:
			if not r.has_point(Vector2i(floori(cp["x"]), floori(cp["y"]))):
				keep.append(cp)
		ch.corpses = keep

func place_car(sim: Sim, ax: int, ay: int) -> void:
	for j in range(4):
		for i in range(2):
			sim.world.set_obj(ax + i, ay + j, Defs.ocell(Defs.O_CAR, 0, j * 2 + i))

func opt(opts: Array, starts: String) -> Callable:
	for o in opts:
		if String(o["label"]).begins_with(starts):
			return o["fn"]
	return Callable()

func screen_for(world_dir: Vector2) -> Vector2:
	var best := Vector2.ZERO
	var bd := -9.0
	for a in range(16):
		var v := Vector2(cos(a * TAU / 16.0), sin(a * TAU / 16.0))
		var d: float = Iso.screen_dir_to_world(v).normalized().dot(world_dir)
		if d > bd:
			bd = d
			best = v
	return best

func _init() -> void:
	seed(77001)
	var slot := "test_integration"
	SaveGame.delete(slot)
	var sim := Sim.new(9001)
	sim.new_game("burglar", [], "house")
	var p: Player = sim.player
	var w: World = sim.world
	quiet(sim)
	sim.weather["rain"] = 0.0
	var home: Vector2 = p.pos
	var fx0: int = floori(home.x) + 6
	var fy0: int = floori(home.y) - 4
	var field := Rect2i(fx0, fy0, 12, 44)
	w.stream(Vector2(fx0 + 6, fy0 + 22), 4, 999)
	sim._process_world_events()
	bulldoze(sim, field)
	quiet(sim)

	print("== vehicles: hotwire, battery, fuel, driving, impacts, storage, persistence")
	var ax: int = fx0 + 5
	var ay: int = fy0 + 2
	place_car(sim, ax, ay)
	var e: Dictionary = Vehicle.car_ent(sim, ax, ay)
	e["key"] = 0; e["hot"] = 0; e["bat"] = 0; e["fuel"] = 0; e["eng"] = 0.8; e["tire"] = 1.0
	w.chunk_at(ax, ay).containers[World.idx(ax, ay)] = [Items.make("toy", 1)]
	p.pos = Vector2(ax - 0.5, ay + 1.5)
	p.facing = Vector2(1, 0)
	var ts: Array = Actions.targets(sim)
	ok(ts.size() > 0 and ts[0]["kind"] == "obj" and Defs.o_id(w.obj(ts[0]["x"], ts[0]["y"])) == Defs.O_CAR, "USE targets the car beside you")
	var co: Array = Actions._car_options(sim, ax, ay)
	ok(opt(co, "Hotwire").is_valid() and not opt(co, "Drive").is_valid(), "a car without a key offers hotwiring, not driving")
	var tries := 0
	while int(e["hot"]) == 0 and tries < 12:
		Actions._hotwire(sim, e)
		run(sim, 6.5)
		tries += 1
	ok(int(e["hot"]) == 1, "a burglar hotwires it (%d tries)" % tries)
	opt(Actions._car_options(sim, ax, ay), "Drive").call()
	ok(sim.vehicle == null, "it will not start with a dead battery")
	Inv.add_new(p.inv, "car_battery", 1)
	opt(Actions._car_options(sim, ax, ay), "Install").call()
	run(sim, 5.5)
	ok(int(e["bat"]) == 1 and Inv.count(p.inv, "car_battery") == 0, "fitting a battery consumes it and powers the car")
	var can: Dictionary = Items.make("gas_can", 1)
	can["u"] = 6
	Inv.add(p.inv, can)
	opt(Actions._car_options(sim, ax, ay), "Refuel").call()
	run(sim, 4.5)
	ok(absf(float(e["fuel"]) - 6.0) < 0.01 and int(can["u"]) == 0, "refuelling moves fuel from the can to the tank (%.1f)" % float(e["fuel"]))
	opt(Actions._car_options(sim, ax, ay), "Drive").call()
	var v: Vehicle = sim.vehicle
	ok(v != null and w.obj(ax, ay) == 0 and w.obj(ax + 1, ay + 3) == 0, "getting in lifts the parked car out of the map")
	ok(v != null and v.trunk.size() == 1 and v.trunk[0]["id"] == "toy", "the boot contents travel with it")
	var fwd: Vector2 = screen_for(Vector2(0, 1))
	var y0: float = v.pos.y
	var fuel0: float = v.ent["fuel"]
	sim.noises.clear()
	run(sim, 2.5, fwd)
	ok(v.pos.y - y0 > 3.0 and v.speed > 2.0, "the stick accelerates it forward (%.1f tiles, %.1f t/s)" % [v.pos.y - y0, v.speed])
	ok(p.pos.distance_to(v.pos) < 0.01, "the driver moves with the car")
	ok(float(v.ent["fuel"]) < fuel0, "driving burns fuel (%.3f -> %.3f)" % [fuel0, float(v.ent["fuel"])])
	var loud := 0.0
	for n in sim.noises: loud = maxf(loud, float(n[1]))
	ok(loud >= 12.0, "a running engine is loud (radius %.0f)" % loud)
	# the noise pulls in something that cannot see the car
	var zl: Zombie = sim.zombies.spawn(v.pos + Vector2(-4.5, 6.0), 0)
	zl.dir = Vector2(-1, 0)
	var zr: Zombie = sim.zombies.spawn(v.pos + Vector2(0.0, 5.0), 0)
	zr.hp = 60.0
	var eng0: float = v.ent["eng"]
	run(sim, 1.6, fwd)
	ok(not sim.zombies.list.has(zr) or zr.hp < 60.0 or zr.state == Zombie.DOWN, "driving into one of them hurts it")
	ok(float(v.ent["eng"]) < eng0, "and the impact costs engine condition (%.3f -> %.3f)" % [eng0, float(v.ent["eng"])])
	ok(zl.state == Zombie.INVESTIGATE or zl.state == Zombie.CHASE, "engine noise draws the infected (%s)" % Zombie.STATE_NAMES[zl.state])
	sim.zombies.list.clear()
	sim.brake = true
	run(sim, 1.5, fwd)
	ok(absf(v.speed) < 0.05, "BRAKE stops the car (%.2f)" % v.speed)
	sim.brake = false
	# a quarter turn, then a wall
	var h0: int = v.heading
	run(sim, 0.8, fwd)
	run(sim, 0.6, screen_for(Vector2(1, 0)))
	ok(v.heading != h0, "steering across the heading turns the car (heading %d -> %d)" % [h0, v.heading])
	sim.brake = true
	run(sim, 1.5)
	sim.brake = false
	var front: Vector2 = v.pos + Vehicle.DIRS[v.heading] * 5.0
	for k in range(-2, 3):
		var side: Vector2 = Vector2(Vehicle.DIRS[v.heading].y, Vehicle.DIRS[v.heading].x) * k
		w.set_obj(floori(front.x + side.x), floori(front.y + side.y), Defs.ocell(Defs.O_FRIDGE, 0, 0))
	eng0 = v.ent["eng"]
	sim.settings["god"] = false
	var hp0: float = p.hp
	run(sim, 3.0, screen_for(Vehicle.DIRS[v.heading]))
	ok((front - v.pos).dot(Vehicle.DIRS[v.heading]) > 1.9, "solid objects stop it")
	ok(float(v.ent["eng"]) < eng0, "a crash damages the engine (%.2f -> %.2f)" % [eng0, float(v.ent["eng"])])
	sim.settings["god"] = true
	p.hp = 100.0
	# an attacker mostly hits the bodywork
	var prot := 0
	sim.settings["god"] = false
	var zt: Zombie = sim.zombies.spawn(p.pos + Vector2(9, 9), 0)
	for i in range(200):
		p.hp = 100.0
		p.wounds.clear()
		var h1: float = p.hp
		p.take_zombie_hit(zt)
		if p.hp >= h1 and p.wounds.is_empty(): prot += 1
	sim.settings["god"] = true
	p.hp = 100.0
	p.wounds.clear()
	p.infection = -1.0
	sim.zombies.list.clear()
	ok(prot > 140, "the car body shields the driver (%d of 200 attacks stopped)" % prot)
	sim.brake = true
	run(sim, 1.5)
	sim.brake = false
	ok(SaveGame.save(sim, slot), "saving while driving")
	var s2: Sim = SaveGame.load_game(slot)
	ok(s2 != null and s2.vehicle != null and s2.vehicle.pos.distance_to(v.pos) < 0.01 and s2.vehicle.heading == v.heading, "the driven car is restored where it was")
	ok(s2 != null and s2.vehicle != null and s2.vehicle.trunk.size() == 1 and absf(float(s2.vehicle.ent["fuel"]) - float(v.ent["fuel"])) < 0.001, "with its fuel and boot contents")
	Actions.interact(sim)
	ok(sim.vehicle == null, "USE gets out")
	var pa: Vector2i = Vector2i(roundi(v.anchor_f().x), roundi(v.anchor_f().y))
	ok(Defs.o_id(w.obj(pa.x, pa.y)) == Defs.O_CAR and Defs.o_rot(w.obj(pa.x, pa.y)) == v.heading, "the car is parked back into the world")
	ok(w.container_at(pa.x, pa.y).size() == 1 and absf(float(w.ent(pa.x, pa.y).get("fuel", -1.0)) - float(v.ent["fuel"])) < 0.001, "its boot and tank state stay with it")
	ok(not w.blocked(p.pos.x, p.pos.y, Player.R * 0.9), "the driver steps out onto free ground")
	ok(SaveGame.save(sim, slot), "saving after parking")
	s2 = SaveGame.load_game(slot)
	ok(s2 != null and Defs.o_id(s2.world.obj(pa.x, pa.y)) == Defs.O_CAR and int(s2.world.ent(pa.x, pa.y).get("hot", 0)) == 1, "the parked car and its hotwired ignition persist")

	print("== fire: spread, damage, burn-out, persistence")
	var fr := Rect2i(fx0, fy0 + 30, 10, 10)
	bulldoze(sim, fr)
	var bx: int = fx0 + 3
	var by: int = fy0 + 34
	for k in range(4):
		w.set_obj(bx + k, by, Defs.ocell(Defs.O_BOOKSHELF, 0, 0))
	ok(sim.flammability(bx, by) > 0.4 and sim.flammability(bx, by + 3) == 0.0, "furniture burns, bare dirt does not")
	sim.weather["rain"] = 1.0
	ok(w.bld(bx, by) != 0 or sim.flammability(bx, by) < 0.2, "rain makes things outdoors hard to light")
	sim.weather["rain"] = 0.0
	p.pos = Vector2(bx - 4.5, by + 4.5)
	sim.ignite(bx, by)
	ok(sim.burning.has(Vector2i(bx, by)), "a tile can be set alight")
	var zf: Zombie = sim.zombies.spawn(Vector2(bx + 0.5, by + 0.5), 0)
	zf.hp = 300.0
	var spread := false
	var t := 0.0
	while t < 60.0 and not spread:
		run(sim, 1.0)
		zf.pos = Vector2(bx + 0.5, by + 0.5)
		t += 1.0
		spread = sim.burning.has(Vector2i(bx + 1, by)) or w.obj(bx + 1, by) == 0
	ok(spread, "fire spreads to the furniture beside it (%.0f s)" % t)
	ok(zf.hp < 300.0 or not sim.zombies.list.has(zf), "whatever stands in the flames burns")
	sim.zombies.list.clear()
	ok(sim.fires.size() > 0, "burning tiles light the night")
	p.pos = Vector2(bx - 1.5, by + 2.5)
	ok(sim.threatened(), "fire nearby counts as danger (fast-forward is refused)")
	ok(SaveGame.save(sim, slot), "saving mid-fire")
	s2 = SaveGame.load_game(slot)
	ok(s2 != null and s2.burning.size() == sim.burning.size() and s2.burning.size() > 0, "the fire is still burning after a reload (%d tiles)" % sim.burning.size())
	sim.settings["god"] = false
	p.hp = 100.0
	var bt: Vector2i = sim.burning.keys()[0]
	p.pos = Vector2(bt.x + 0.5, bt.y + 0.5)
	sim.burning[bt] = 20.0
	run(sim, 3.2)
	ok(p.hp < 100.0, "standing in fire hurts (%.0f hp)" % p.hp)
	sim.settings["god"] = true
	p.hp = 100.0
	p.wounds.clear()
	p.pos = Vector2(bx - 4.5, by + 4.5)
	t = 0.0
	while t < 140.0 and not sim.burning.is_empty():
		run(sim, 1.0)
		t += 1.0
	ok(sim.burning.is_empty(), "the fire burns itself out on bare ground (%.0f s)" % t)
	ok(w.obj(bx, by) == 0 and w.obj(bx + 1, by) == 0, "what burned is gone")

	print("== survivors: talk, follow, fight, trade, hostility, persistence")
	bulldoze(sim, Rect2i(fx0, fy0 + 30, 10, 10))
	p.pos = Vector2(fx0 + 2.5, fy0 + 32.5)
	p.facing = Vector2(1, 0)
	var friend = sim.npcs.spawn(p.pos + Vector2(1.2, 0.0), false)
	ts = Actions.targets(sim)
	var has_npc := false
	for tt in ts:
		if tt["kind"] == "npc": has_npc = true
	ok(has_npc, "a survivor beside you can be addressed with USE")
	var no: Array = sim.npcs.options(friend)
	opt(no, "Talk").call()
	ok(friend.met, "talking introduces you")
	opt(no, "\"Come").call()
	ok(friend.state == NpcSim.FOLLOW, "they agree to follow")
	p.pos += Vector2(6.0, 5.0)
	run(sim, 5.0)
	ok(friend.pos.distance_to(p.pos) < 3.2, "and keep up when you move (%.1f tiles away)" % friend.pos.distance_to(p.pos))
	var zn: Zombie = sim.zombies.spawn(friend.pos + Vector2(0.9, 0.0), 0)
	zn.hp = 50.0
	var k0: int = p.kills
	t = 0.0
	while t < 12.0 and sim.zombies.list.has(zn):
		zn.pos = friend.pos + Vector2(0.9, 0.0)
		friend.hp = 100.0
		run(sim, 0.5)
		t += 0.5
	ok(not sim.zombies.list.has(zn), "a companion kills the infected next to them (%.1f s)" % t)
	ok(p.kills == k0, "their kills are not counted as yours")
	sim.zombies.list.clear()
	friend.hunger = 70.0
	Inv.add_new(p.inv, "cooked_egg", 1, sim.hour)
	var inv0: int = Inv.count(p.inv, "cooked_egg")
	var give: Callable = opt(sim.npcs.options(friend), "Give")
	ok(give.is_valid(), "food you carry can be offered")
	if give.is_valid(): give.call()
	ok(friend.hunger < 70.0 and Inv.count(p.inv, "cooked_egg") == inv0 - 1 and friend.gift, "feeding them consumes the food and earns something back")
	friend.hunger = 100.0
	run(sim, 0.3)
	ok(friend.state == NpcSim.STAY, "a starving companion stops following")
	friend.hunger = 10.0
	friend.state = NpcSim.FOLLOW
	ok(SaveGame.save(sim, slot), "saving with a companion")
	s2 = SaveGame.load_game(slot)
	ok(s2 != null and s2.npcs.list.size() == 1 and s2.npcs.list[0].state == NpcSim.FOLLOW and s2.npcs.list[0].name == friend.name and s2.npcs.list[0].gift, "the companion and their memory of you persist")
	# betrayal
	p.weapon = {}
	Inv.add_new(p.inv, "baseball_bat", 1)
	p.equip(Inv.find(p.inv, "baseball_bat"))
	friend.pos = p.pos + Vector2(0.8, 0.0)
	p.facing = Vector2(1, 0)
	friend.state = NpcSim.STAY
	var fhp: float = friend.hp
	p.attack_cd = 0.0
	p.try_attack()
	run(sim, 1.2)
	ok(friend.hp < fhp and friend.state == NpcSim.HOSTILE, "hitting a survivor hurts them and turns them on you")
	sim.settings["god"] = false
	p.hp = 100.0
	t = 0.0
	while t < 10.0 and p.hp >= 100.0:
		run(sim, 0.5)
		t += 0.5
	ok(p.hp < 100.0, "a hostile survivor attacks (%.0f hp after %.1f s)" % [p.hp, t])
	sim.settings["god"] = true
	ok(sim.threatened(), "a hostile survivor counts as danger")
	sim.npcs.damage(friend, 500.0, true)
	var body := false
	for ch in w.chunks.values():
		for cp in ch.corpses:
			if Vector2(cp["x"], cp["y"]).distance_to(friend.pos) < 0.1 and int(cp.get("perm", 0)) == 1: body = true
	ok(sim.npcs.list.is_empty() and body, "killing them leaves a body")
	p.hp = 100.0
	p.wounds.clear()

	print("== shove, call-out, bodies")
	bulldoze(sim, Rect2i(fx0, fy0 + 30, 10, 10))
	p.pos = Vector2(fx0 + 4.5, fy0 + 34.5)
	p.facing = Vector2(1, 0)
	var zs: Zombie = sim.zombies.spawn(p.pos + Vector2(0.8, 0.0), 0)
	zs.hp = 100.0
	p.attack_cd = 0.0
	p.swing_t = 0.0
	ok(p.try_shove(), "SHOVE works with a weapon in hand")
	run(sim, 0.8)
	ok(zs.pos.distance_to(p.pos) > 1.0 or zs.state == Zombie.STAGGER or zs.state == Zombie.DOWN, "it pushes the infected back (%.2f tiles, %s)" % [zs.pos.distance_to(p.pos), Zombie.STATE_NAMES[zs.state]])
	ok(zs.hp > 60.0, "without doing weapon damage (%.0f hp)" % zs.hp)
	sim.zombies.list.clear()
	var zc: Zombie = sim.zombies.spawn(p.pos + Vector2(0.0, 16.0), 0)
	zc.dir = Vector2(0, 1)
	var keep: Vector2 = p.pos
	p.sneaking = true
	p.call_out(false)
	p.pos = Vector2(-9999, -9999)
	for i in range(20): sim.zombies.update(1.0 / 30.0)
	ok(zc.state == Zombie.IDLE or zc.state == Zombie.WANDER, "a whisper does not carry 16 tiles")
	p.pos = keep
	p.call_out(true)
	p.pos = Vector2(-9999, -9999)
	for i in range(20): sim.zombies.update(1.0 / 30.0)
	p.pos = keep
	p.sneaking = false
	ok(zc.state == Zombie.INVESTIGATE, "a shout does (%s)" % Zombie.STATE_NAMES[zc.state])
	sim.zombies.list.clear()
	sim.noises.clear()
	var cch: Chunk = w.chunk_at(floori(p.pos.x), floori(p.pos.y))
	var corpse := {"x": p.pos.x + 0.6, "y": p.pos.y, "d": 0, "l": [0, 0, 0, 0], "h": sim.hour, "perm": 1}
	cch.corpses.append(corpse)
	var cops: Array = Actions.options(sim, {"kind": "corpse", "corpse": corpse, "x": floori(p.pos.x), "y": floori(p.pos.y)})
	opt(cops, "Drag").call()
	ok(not p.dragging.is_empty() and not cch.corpses.has(corpse), "a body can be picked up and dragged")
	var d0: Vector2 = p.pos
	run(sim, 1.0, Vector2(1, 0))
	var slow: float = p.pos.distance_to(d0)
	Actions.interact(sim)
	ok(p.dragging.is_empty(), "USE lets go of it")
	d0 = p.pos
	run(sim, 1.0, Vector2(-1, 0))
	ok(slow < p.pos.distance_to(d0) * 0.75, "dragging slows you down (%.2f vs %.2f tiles/s)" % [slow, p.pos.distance_to(d0)])
	var near: Dictionary = {}
	for ch in w.chunks.values():
		for cp in ch.corpses:
			if Vector2(cp["x"], cp["y"]).distance_to(p.pos) < 3.0: near = cp
	ok(not near.is_empty(), "the body lies where it was dropped")
	if not near.is_empty():
		Inv.add_new(p.inv, "shovel", 1)
		p.pos = Vector2(float(near["x"]) + 0.7, float(near["y"]))
		opt(Actions.options(sim, {"kind": "corpse", "corpse": near, "x": 0, "y": 0}), "Bury").call()
		run(sim, 9.5)
		ok(Defs.o_id(w.obj(floori(near["x"]), floori(near["y"]))) == Defs.O_GRAVE, "burying it leaves a grave")
	# rotting bodies make the place unhealthy
	for i in range(12):
		cch.corpses.append({"x": p.pos.x + 0.3 * i - 1.5, "y": p.pos.y + 1.0, "d": 0, "l": [0, 0, 0, 0], "h": sim.hour - 30.0, "perm": 1})
	var sick0: float = p.corpse_exp
	sim.settings["god"] = false
	for i in range(40):
		sim._slow_tick(0.25)
		p.tick_needs(0.25)
	sim.settings["god"] = true
	ok(p.corpses_near >= 10 and p.corpse_exp > sick0, "living among corpses makes you ill (%d bodies, exposure %.1f -> %.1f)" % [p.corpses_near, sick0, p.corpse_exp])
	p.corpse_exp = 0.0
	p.hp = 100.0

	print("== chicken coop")
	bulldoze(sim, Rect2i(fx0, fy0 + 30, 10, 10))
	var cx: int = fx0 + 6
	var cy: int = fy0 + 36
	w.set_obj(cx, cy, Defs.ocell(Defs.O_COOP, 0, 0))
	p.pos = Vector2(cx - 0.5, cy + 0.5)
	var oo: Array = Actions.options(sim, {"kind": "obj", "x": cx, "y": cy})
	ok(opt(oo, "Collect").is_valid() and opt(oo, "Take a hen").is_valid(), "a coop offers eggs and hens")
	var ce: Dictionary = w.ent(cx, cy)
	ce["hens"] = 3; ce["eggs"] = 0.0; ce["fed"] = 100.0
	var cchunk: Chunk = w.chunk_at(cx, cy)
	for i in range(48): sim._sim_ents(cchunk, 1.0, false)
	ok(float(ce["eggs"]) >= 5.0 and float(ce["fed"]) < 60.0, "fed hens lay over time and eat their feed (%.1f eggs)" % float(ce["eggs"]))
	var axp: float = p.skills["animal_care"]
	opt(Actions.options(sim, {"kind": "obj", "x": cx, "y": cy}), "Collect").call()
	run(sim, 3.0)
	ok(Inv.count(p.inv, "egg") >= 5 and float(p.skills["animal_care"]) > axp, "collecting eggs fills the bag and trains Animal Care")
	ce["fed"] = 0.0
	for i in range(80): sim._sim_ents(cchunk, 1.0, false)
	ok(int(ce["hens"]) == 2, "unfed hens start to die")
	Inv.add_new(p.inv, "seeds_carrot", 1)
	opt(Actions.options(sim, {"kind": "obj", "x": cx, "y": cy}), "Feed").call()
	ok(float(ce["fed"]) > 50.0 and Inv.count(p.inv, "seeds_carrot") == 0, "seed is consumed as feed")
	Inv.add_new(p.inv, "kitchen_knife", 1)
	var bxp: float = p.skills["butchering"]
	opt(Actions.options(sim, {"kind": "obj", "x": cx, "y": cy}), "Take a hen").call()
	run(sim, 6.5)
	ok(int(ce["hens"]) == 1 and Inv.count(p.inv, "raw_chicken") >= 1 and float(p.skills["butchering"]) > bxp, "butchering a hen gives meat and trains Butchering")

	print("== upper floors")
	var st_lot: Dictionary = {}
	var st_plan: LotBuilder.LotPlan = null
	var two := 0
	var houses := 0
	for rx in range(-1, 2):
		for ry in range(-1, 2):
			for lot in w.gen.region(rx, ry)["lots"]:
				if lot["k"] != "house": continue
				houses += 1
				var plan: LotBuilder.LotPlan = w.gen.lot_plan(lot)
				if plan.stairs.x >= 0:
					two += 1
					if st_lot.is_empty():
						st_lot = lot
						st_plan = plan
	ok(two > 2, "some houses have a second storey (%d of %d)" % [two, houses])
	if st_plan != null:
		var lr: Rect2i = st_lot["r"]
		var sx: int = lr.position.x + st_plan.stairs.x
		var sy: int = lr.position.y + st_plan.stairs.y
		p.pos = Vector2(sx + 0.5, sy + 0.5)
		w.stream(p.pos, 2, 999)
		sim._process_world_events()
		quiet(sim)
		ok(Defs.o_id(w.obj(sx, sy)) == Defs.O_STAIRS, "the staircase stands inside the house")
		var so: Array = Actions.options(sim, {"kind": "obj", "x": sx, "y": sy})
		opt(so, "Go upstairs").call()
		run(sim, 2.0)
		ok(World.level(p.pos.y) == 2, "the stairs lead to the upper floor")
		ok(not w.blocked(p.pos.x, p.pos.y, Player.R) and w.bld(floori(p.pos.x), floori(p.pos.y)) != 0, "which is a walkable indoor room")
		ok(not sim.underground() and sim.daylight() > 0.0, "it is not treated as a cellar")
		var floor_n := 0
		var furn := 0
		for ch in w.chunks.values():
			if World.level(ch.cy * 16.0) != 2: continue
			for i in range(256):
				if ch.ground[i] != Defs.G_VOID:
					floor_n += 1
					if ch.obj[i] != 0: furn += 1
		ok(floor_n >= 12 and furn >= 2, "the storey has a floor plan and furniture (%d tiles, %d objects)" % [floor_n, furn])
		# walk around upstairs: must stay on the floor
		var fell := false
		for d in [Vector2(1, 0), Vector2(0, 1), Vector2(-1, 0), Vector2(0, -1)]:
			run(sim, 1.5, d, true)
			if w.blocked(p.pos.x, p.pos.y, Player.R * 0.9) or World.level(p.pos.y) != 2: fell = true
		ok(not fell, "walls keep you on the upper floor")
		ok(SaveGame.save(sim, slot), "saving upstairs")
		s2 = SaveGame.load_game(slot)
		ok(s2 != null and World.level(s2.player.pos.y) == 2 and not s2.world.blocked(s2.player.pos.x, s2.player.pos.y, Player.R), "a save made upstairs loads upstairs")
		p.pos = Vector2(sx + 0.5, sy + World.UNDER * 2 + 0.5)
		opt(Actions.options(sim, {"kind": "obj", "x": sx, "y": sy + World.UNDER * 2}), "Go downstairs").call()
		run(sim, 2.0)
		ok(World.level(p.pos.y) == 0 and w.bld(floori(p.pos.x), floori(p.pos.y)) == st_plan.bld_id, "and back down into the same house")

	print("== causal links")
	p.pos = Vector2(fx0 + 4.5, fy0 + 34.5)
	w.stream(p.pos, 3, 999)
	sim._process_world_events()
	quiet(sim)
	bulldoze(sim, Rect2i(fx0, fy0 + 26, 12, 18))
	# wound -> movement
	p.wounds.clear()
	p.endurance = 100.0
	p.pos = Vector2(fx0 + 2.5, fy0 + 30.5)
	var a0: Vector2 = p.pos
	run(sim, 1.5, screen_for(Vector2(0, 1)))
	var healthy: float = p.pos.distance_to(a0)
	p.pos = Vector2(fx0 + 2.5, fy0 + 30.5)
	var leg := -1
	for i in range(Player.PARTS.size()):
		if Player.is_leg(i) and leg < 0: leg = i
	p.add_wound(leg, "fracture", "test")
	a0 = p.pos
	run(sim, 1.5, screen_for(Vector2(0, 1)))
	var hurt: float = p.pos.distance_to(a0)
	ok(hurt < healthy * 0.85, "a broken leg slows walking (%.2f vs %.2f tiles)" % [hurt, healthy])
	p.wounds.clear()
	p.hp = 100.0
	# clothing -> wounds
	sim.settings["god"] = false
	var zb: Zombie = sim.zombies.spawn(p.pos + Vector2(20, 0), 0)
	var bare := 0
	p.worn = {}
	p.gear = {}
	for i in range(300):
		p.hp = 100.0
		p.wounds.clear()
		p.infection = -1.0
		p.take_zombie_hit(zb)
		bare += p.wounds.size()
	Inv.add_new(p.inv, "leather_jacket", 1)
	p.equip(Inv.find(p.inv, "leather_jacket"))
	var clothed := 0
	for i in range(300):
		p.hp = 100.0
		p.wounds.clear()
		p.infection = -1.0
		if not p.worn.is_empty(): p.worn["c"] = 1.0
		p.take_zombie_hit(zb)
		clothed += p.wounds.size()
	sim.settings["god"] = true
	p.hp = 100.0
	p.wounds.clear()
	p.infection = -1.0
	p.panic = 0.0
	p.stress = 0.0
	sim.zombies.list.clear()
	ok(not p.worn.is_empty() and clothed < bare * 0.9, "a leather jacket stops some attacks (%d wounds vs %d bare, of 300)" % [clothed, bare])
	# gunshot -> hearing
	var zg: Zombie = sim.zombies.spawn(p.pos + Vector2(0.0, 22.0), 0)
	zg.dir = Vector2(0, 1)
	Inv.add_new(p.inv, "pistol", 1)
	Inv.add_new(p.inv, "ammo_9mm", 12)
	p.equip(Inv.find(p.inv, "pistol"))
	p.reload()
	run(sim, 3.5)
	p.facing = Vector2(0, -1)
	p.attack_cd = 0.0
	sim.noises.clear()
	p.try_attack()
	var shot_r := 0.0
	for n in sim.noises: shot_r = maxf(shot_r, float(n[1]))
	keep = p.pos
	p.pos = Vector2(-9999, -9999)
	for i in range(20): sim.zombies.update(1.0 / 30.0)
	p.pos = keep
	ok(shot_r >= 22.0 and zg.state == Zombie.INVESTIGATE, "a gunshot is heard 22 tiles away and investigated (radius %.0f, %s)" % [shot_r, Zombie.STATE_NAMES[zg.state]])
	sim.zombies.list.clear()
	# utilities -> appliances
	var px: int = floori(home.x)
	var py: int = floori(home.y)
	sim.power_off_h = sim.hour + 100.0
	var pow_on: bool = sim.has_power(px, py)
	sim.power_off_h = sim.hour - 1.0
	ok(pow_on and not sim.has_power(px, py), "when the grid fails, the house loses power")
	sim.water_off_h = sim.hour - 1.0
	ok(not sim.has_water(), "and the taps run dry when the water fails")
	# time control
	sim.speed = 4
	var zt2: Zombie = sim.zombies.spawn(p.pos + Vector2(3.0, 0.0), 0)
	zt2.state = Zombie.CHASE
	ok(sim.threatened(), "a chasing infected is a threat (fast-forward drops out)")
	sim.zombies.list.clear()
	ok(not sim.threatened(), "no threat once it is gone")
	sim.speed = 1

	print("== death, a new survivor in the same world")
	pa = Vector2i(fx0 + 1, fy0 + 2)       # a car left behind by the first survivor
	p.pos = Vector2(pa.x - 1.5, pa.y + 0.5)
	w.stream(p.pos, 2, 999)
	sim._process_world_events()
	bulldoze(sim, Rect2i(pa.x - 2, pa.y - 1, 5, 6))
	place_car(sim, pa.x, pa.y)
	Vehicle.car_ent(sim, pa.x, pa.y)["fuel"] = 3.5
	Inv.add_new(p.inv, "toy", 3)
	var died_at: Vector2 = p.pos
	var hour_d: float = sim.hour
	sim.settings["god"] = false
	p.hurt(999.0, "Test death")
	run(sim, 0.2)
	ok(not p.alive and sim.dead, "the survivor dies")
	sim.new_survivor("farmer", [], "farm")
	var q: Player = sim.player
	ok(q != p and q.alive and not sim.dead and sim.lives == 1, "a new survivor takes over")
	ok(q.pos.distance_to(died_at) > 30.0 and not w.blocked(q.pos.x, q.pos.y, Player.R), "somewhere else in the same world (%.0f tiles away)" % q.pos.distance_to(died_at))
	ok(sim.hour >= hour_d and Inv.count(q.inv, "toy") == 0, "time carries on; the new survivor starts with their own kit")
	q.pos = died_at
	w.stream(q.pos, 2, 999)
	sim._process_world_events()
	var found_toy := false
	for ch in w.chunks.values():
		for cp in ch.corpses:
			if cp.has("loot") and Inv.count(cp["loot"], "toy") == 3: found_toy = true
	for z in sim.zombies.list:
		if Inv.count(z.loot, "toy") == 3: found_toy = true
	ok(found_toy, "the old body (or what it became) still carries the old gear")
	q.pos = Vector2(pa.x - 1.5, pa.y + 0.5)
	w.stream(q.pos, 2, 999)
	sim._process_world_events()
	ok(Defs.o_id(w.obj(pa.x, pa.y)) == Defs.O_CAR and absf(float(w.ent(pa.x, pa.y).get("fuel", 0.0)) - 3.5) < 0.01, "a car the first survivor left is still there, fuel and all")

	print("== stuck: sealed rooms and the way out")
	var sx0: int = fx0 + 2
	var sy0: int = fy0 + 2
	bulldoze(sim, Rect2i(sx0 - 3, sy0 - 3, 12, 12))
	for k in range(0, 5):
		w.set_wall(sx0 + k, sy0, 0, Defs.wall(Defs.WM_PLASTER_CREAM, Defs.WS_SOLID))
		w.set_wall(sx0 + k, sy0 + 4, 0, Defs.wall(Defs.WM_PLASTER_CREAM, Defs.WS_SOLID))
		w.set_wall(sx0, sy0 + k, 1, Defs.wall(Defs.WM_PLASTER_CREAM, Defs.WS_SOLID))
		w.set_wall(sx0 + 5, sy0 + k, 1, Defs.wall(Defs.WM_PLASTER_CREAM, Defs.WS_SOLID))
	for k in range(sx0, sx0 + 5):
		for l in range(sy0, sy0 + 4):
			w.chunk_at(k, l).bld[World.idx(k, l)] = 424242
	var inside_p := Vector2(sx0 + 2.5, sy0 + 2.5)
	ok(not sim.can_escape(inside_p), "a room with no door is detected as a trap")
	w.set_wall(sx0 + 2, sy0 + 4, 0, Defs.wall(Defs.WM_PLASTER_CREAM, Defs.WS_WINDOW))
	ok(not sim.can_escape(inside_p), "a window is not a way out")
	w.set_wall(sx0 + 2, sy0 + 4, 0, Defs.wall(Defs.WM_PLASTER_CREAM, Defs.WS_DOOR))
	w.set_edge_state(sx0 + 2, sy0 + 4, 0, 1 << Defs.ES_PLANK_SHIFT)
	ok(not sim.can_escape(inside_p), "a barricaded door is not a way out")
	w.set_edge_state(sx0 + 2, sy0 + 4, 0, 0)
	ok(sim.can_escape(inside_p), "a plain door is")
	w.set_wall(sx0 + 2, sy0 + 4, 0, Defs.wall(Defs.WM_PLASTER_CREAM, Defs.WS_SOLID))
	var np: Player = sim.player
	np.pos = inside_p
	sim.unstick()
	ok(w.bld(floori(np.pos.x), floori(np.pos.y)) == 0 and not w.blocked(np.pos.x, np.pos.y, Player.R) and np.pos.distance_to(inside_p) > 1.0, "'Stuck? Move me outside' puts you on open ground (%.1f tiles away)" % np.pos.distance_to(inside_p))
	var trapped_starts := 0
	for sd in range(40):
		var ts2 := Sim.new(1000 + sd * 31)
		ts2.new_game("hunter", [], ["house", "farm", "cabin", "downtown"][sd % 4])
		if not ts2.can_escape(ts2.player.pos): trapped_starts += 1
	ok(trapped_starts == 0, "40 different new games, none starts sealed in")

	print("== saves: backup, corruption, repeated cycles")
	quiet(sim)
	ok(SaveGame.save(sim, slot) and SaveGame.save(sim, slot), "two saves in a row")
	var meta_path: String = SaveGame.dir_for(slot) + "/meta.sav"
	ok(FileAccess.file_exists(meta_path + ".bak"), "the previous save is kept as a backup")
	var f := FileAccess.open(meta_path, FileAccess.WRITE)
	f.store_string("this is not a save file")
	f.close()
	var rec0: int = SaveGame.recovered
	s2 = SaveGame.load_game(slot)
	ok(s2 != null and SaveGame.recovered > rec0, "a corrupted save is detected and the backup loads instead")
	ok(s2 != null and s2.lives == 1 and s2.player.occupation == "farmer", "the recovered game is the right one")
	var bytes: PackedByteArray = FileAccess.get_file_as_bytes(meta_path + ".bak")
	f = FileAccess.open(meta_path, FileAccess.WRITE)
	f.store_buffer(bytes.slice(0, bytes.size() / 2))
	f.close()
	s2 = SaveGame.load_game(slot)
	ok(s2 != null, "a half-written save (interrupted write) also falls back to the backup")
	f = FileAccess.open(meta_path, FileAccess.WRITE)
	f.store_string("x")
	f.close()
	f = FileAccess.open(meta_path + ".bak", FileAccess.WRITE)
	f.store_string("y")
	f.close()
	ok(SaveGame.load_game(slot) == null, "with both copies destroyed, loading fails cleanly instead of crashing")
	ok(SaveGame.save(sim, slot), "saving over a destroyed slot works")
	var cur: Sim = sim
	var stable := true
	var sig0: String = ""
	for i in range(6):
		ok(SaveGame.save(cur, slot), "cycle %d: save" % i) if false else SaveGame.save(cur, slot)
		var nx: Sim = SaveGame.load_game(slot)
		if nx == null:
			stable = false
			break
		nx.settings["god"] = true
		var sig: String = "%s|%.3f|%d|%d|%d|%d|%.4f" % [str(nx.player.pos), nx.player.hp, nx.player.inv.size(), nx.zombies.list.size(), nx.lives, nx.world.chunks.size(), nx.hour]
		if i == 0: sig0 = sig
		elif sig != sig0: stable = false
		cur = nx
	ok(stable, "six save/load cycles in a row reproduce the same state")
	var m: Dictionary = SaveGame.migrate({"v": 1, "seed": 5, "player": {}, "settings": {}})
	ok(int(m.get("v", 0)) == SaveGame.SCHEMA, "a schema 1 save migrates to the current schema (%d)" % SaveGame.SCHEMA)
	SaveGame.delete(slot)
	ok(not SaveGame.exists(slot), "deleting the slot removes the backup too")

	print("RESULT: %d checks, %d failed" % [checks, fails])
	quit(1 if fails > 0 else 0)
