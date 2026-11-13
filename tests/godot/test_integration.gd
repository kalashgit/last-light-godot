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
	sim.ignite(bx, by, 3.0)          # a well-fed fire: 30-66 s, long enough that spreading is not left to luck
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
	friend.trust = 10.0
	opt(sim.npcs.options(friend), "\"Come").call()
	ok(friend.state == NpcSim.STAY, "a stranger who does not trust you will not follow")
	friend.trust = 50.0
	friend.temper = "brave"
	opt(sim.npcs.options(friend), "\"Come").call()
	ok(friend.state == NpcSim.FOLLOW, "with some trust they agree to follow")
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
	friend.stock = []
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

	print("== mechanics bible: time, reports, drag-down, jams, notes, barter, rest")
	var fresh := Sim.new(31337)
	ok(absf(float(fresh.settings["day_min"]) - 60.0) < 0.01 and fresh.settings["respawn"] == false, "defaults: one real hour is one game day; cleared areas stay cleared")
	fresh.new_game("unemployed", [], "house")
	quiet(fresh)
	var fh0: float = fresh.hour
	run(fresh, 60.0)
	ok(absf((fresh.hour - fh0) - 0.4) < 0.02, "60 real seconds pass 24 game minutes (%.3f h)" % (fresh.hour - fh0))
	fresh.player.fatigue = 80.0
	fresh.start_sleep(1.0)
	ok(absf(fresh.time_scale - 20.0) < 0.01, "sleep runs the world at 20x")
	fresh.wake("test")
	# exact reports
	sim.settings["god"] = false
	p.worn = {}
	p.gear = {}
	var seen_s := false
	var seen_l := false
	var seen_b := false
	var bite_always := true
	var zrep: Zombie = sim.zombies.spawn(p.pos + Vector2(30, 0), 0)
	for i in range(400):
		p.hp = 100.0
		p.wounds.clear()
		p.infection = -1.0
		sim.log.clear()
		p.take_zombie_hit(zrep)
		var msg: String = String(sim.log[sim.log.size() - 1][0]) if sim.log.size() > 0 else ""
		if msg.begins_with("Scratched"): seen_s = true
		if msg.begins_with("Deep laceration"): seen_l = true
		if msg.begins_with("BITTEN"):
			seen_b = true
			if p.infection < 0.0: bite_always = false
	ok(seen_s and seen_l and seen_b, "every hit says what it was: scratch, laceration or bite")
	ok(bite_always, "a bite that breaks the skin always infects")
	Inv.add_new(p.inv, "leather_jacket", 1)
	p.equip(Inv.find(p.inv, "leather_jacket"))
	var blocked_msg := false
	for i in range(300):
		p.hp = 100.0
		p.wounds.clear()
		p.infection = -1.0
		if not p.worn.is_empty(): p.worn["c"] = 1.0
		sim.log.clear()
		p.take_zombie_hit(zrep)
		if sim.log.size() > 0 and String(sim.log[sim.log.size() - 1][0]).contains("skin not broken") and p.infection < 0.0 and p.wounds.is_empty(): blocked_msg = true
	ok(blocked_msg, "a blocked attack is reported as blocked, with no wound and no infection")
	# drag-down
	var ring: Array = []
	for k in range(3):
		var zr2: Zombie = sim.zombies.spawn(p.pos + Vector2(0.7, 0).rotated(k * 2.1), 0)
		zr2.state = Zombie.CHASE
		ring.append(zr2)
	var dragged := false
	for i in range(80):
		p.hp = 100.0
		p.wounds.clear()
		p.infection = -1.0
		if not p.worn.is_empty(): p.worn["c"] = 1.0
		for k in range(3): (ring[k] as Zombie).pos = p.pos + Vector2(0.7, 0).rotated(k * 2.1)
		sim.log.clear()
		p.take_zombie_hit(ring[0])
		if sim.log.size() > 0 and String(sim.log[sim.log.size() - 1][0]).begins_with("DRAGGED DOWN"):
			dragged = p.hp <= 65.0 and p.infection >= 0.0
			break
	ok(dragged, "three at once drag you down through any clothing: heavy damage and a certain bite")
	sim.zombies.list.clear()
	sim.settings["god"] = true
	p.hp = 100.0
	p.wounds.clear()
	p.infection = -1.0
	p.panic = 0.0
	p.alive = true
	# jams
	p.equip(Inv.find(p.inv, "pistol")) if (p.weapon.is_empty() or p.weapon["id"] != "pistol") else null
	Inv.add_new(p.inv, "ammo_9mm", 30)
	p.weapon["c"] = 0.08
	p.weapon["u"] = 12
	var jammed := false
	for i in range(40):
		p.attack_cd = 0.0
		p.swing_t = 0.0
		p.try_attack()
		if int(p.weapon.get("jam", 0)) == 1:
			jammed = true
			break
		if int(p.weapon["u"]) <= 0: p.weapon["u"] = 12
	ok(jammed, "a worn-out gun jams")
	var u_j: int = p.weapon["u"]
	p.attack_cd = 0.0
	p.swing_t = 0.0
	p.try_attack()
	ok(int(p.weapon["u"]) == u_j, "a jammed gun does not fire")
	p.cancel_action()
	p.reload()
	run(sim, 2.6)
	ok(not p.weapon.has("jam"), "LOAD clears the jam")
	p.weapon["c"] = 1.0
	# notes and markers
	p.markers.clear()
	ok(not sim.write_note(), "writing needs a pencil and a notebook")
	Inv.add_new(p.inv, "pencil", 1)
	Inv.add_new(p.inv, "notebook", 1)
	ok(sim.write_note() and sim.write_note(), "with both, notes can be written")
	var notes: Array = []
	for it in p.inv:
		if it["id"] == "note": notes.append(it)
	ok(notes.size() == 2 and int(Inv.find(p.inv, "notebook")["u"]) == 8, "each note is its own item and uses a page")
	if notes.size() > 0:
		sim.read_note(notes[0])
		ok(p.markers.size() == 1 and int(p.markers[0][0]) == floori(p.pos.x), "reading a note marks its place on the reader's map")
	var found: Dictionary = Items.make("survivor_note", 1, sim.hour)
	sim.read_note(found)
	ok(String(found.get("txt", "")).length() > 10, "a found note has something written on it")
	var with_sketch := 0
	for k in range(30):
		var fn2: Dictionary = Items.make("survivor_note", 1, sim.hour)
		sim.hour += 1.0
		sim._fill_found_note(fn2)
		if fn2.has("mx"): with_sketch += 1
	ok(with_sketch > 0, "some found notes point at a real place (%d of 30)" % with_sketch)
	# barter
	var trader = sim.npcs.spawn(p.pos + Vector2(1.0, 0.0), false)
	trader.met = true
	trader.stock = ["nails", "duct_tape", "matches"]
	Inv.add_new(p.inv, "canned_beans", 1, sim.hour)
	var beans0: int = Inv.count(p.inv, "canned_beans")
	var nails0: int = Inv.count(p.inv, "nails")
	var tr: Callable = Callable()
	for o in sim.npcs.options(trader):
		if String(o["label"]).begins_with("Trade your") and String(o["label"]).ends_with("Nails"): tr = o["fn"]
	ok(tr.is_valid(), "a survivor you have met offers a trade")
	if tr.is_valid():
		var gave_id := ""
		var before: Dictionary = {}
		for it in p.inv: before[it["id"]] = int(before.get(it["id"], 0)) + int(it["n"])
		tr.call()
		for k2 in before.keys():
			if Inv.count(p.inv, k2) < int(before[k2]): gave_id = k2
		ok(Inv.count(p.inv, "nails") == nails0 + 1 and gave_id != "" and trader.stock.has(gave_id) and not trader.stock.has("nails"), "barter moves one item each way and nothing is duplicated (gave %s)" % gave_id)
	sim.npcs.list.clear()
	# rest
	p.endurance = 20.0
	Actions._rest(sim)
	run(sim, 8.5)
	ok(p.endurance > 70.0, "sitting down restores stamina (%.0f)" % p.endurance)
	ok(absf(Opts.cycle(1.0, [0.85, 1.0, 1.1]) - 1.1) < 0.001 and Opts.dead > 0.0, "device settings cycle through their steps")

	print("== moving furniture")
	bulldoze(sim, Rect2i(fx0, fy0 + 30, 10, 10))
	sim.zombies.list.clear()
	p.cancel_action()
	p.pos = Vector2(fx0 + 4.5, fy0 + 34.5)
	p.facing = Vector2(1, 0)
	p.weapon = {}
	var wx: int = fx0 + 5
	var wy: int = fy0 + 34
	w.set_obj(wx, wy, Defs.ocell(Defs.O_WARDROBE, 1, 0))
	w.chunk_at(wx, wy).containers[World.idx(wx, wy)] = [Items.make("toy", 2), Items.make("nails", 7)]
	var fo: Array = Actions.options(sim, {"kind": "obj", "x": wx, "y": wy})
	var labels: Array = []
	for o9 in fo: labels.append(o9["label"])
	ok(opt(fo, "Pick up").is_valid() and opt(fo, "Turn it").is_valid(), "furniture offers to be carried or turned")
	opt(fo, "Turn it").call()
	ok(Defs.o_rot(w.obj(wx, wy)) == 2, "turning it changes which way it faces")
	opt(Actions.options(sim, {"kind": "obj", "x": wx, "y": wy}), "Pick up").call()
	run(sim, 2.3)
	ok(w.obj(wx, wy) == 0 and int(p.carrying.get("o", 0)) == Defs.O_WARDROBE and w.items_at(wx, wy).is_empty(), "lifting removes it from the floor without spilling what is inside")
	ok(not p.try_attack(), "you cannot swing with your arms full")
	var c0: Vector2 = p.pos
	run(sim, 1.0, screen_for(Vector2(0, 1)))
	var carry_d: float = p.pos.distance_to(c0)
	ok(carry_d > 0.3 and carry_d < 2.6, "you can walk with it, slowly (%.2f tiles/s)" % carry_d)
	p.carrying["rot"] = 3
	p.facing = Vector2(0, 1)
	var dest: Vector2i = p.front_tile()
	Actions.interact(sim)
	ok(p.carrying.is_empty() and Defs.o_id(w.obj(dest.x, dest.y)) == Defs.O_WARDROBE and Defs.o_rot(w.obj(dest.x, dest.y)) == 3, "USE sets it down in front of you, facing the way you chose")
	var moved: Array = w.container_at(dest.x, dest.y)
	ok(Inv.count(moved, "toy") == 2 and Inv.count(moved, "nails") == 7 and moved.size() == 2, "its contents arrive with it: nothing lost, nothing duplicated")
	w.set_obj(wx + 2, wy, Defs.ocell(Defs.O_FRIDGE, 0, 0))
	p.pos = Vector2(wx + 1.5, wy + 0.5)
	p.skills["strength"] = 0.0
	Actions._pick_up(sim, wx + 2, wy)
	run(sim, 4.5)
	ok(p.carrying.is_empty() and Defs.o_id(w.obj(wx + 2, wy)) == Defs.O_FRIDGE, "a refrigerator is too heavy to lift alone")
	var helper = sim.npcs.spawn(p.pos + Vector2(0.0, 1.2), false)
	helper.state = NpcSim.FOLLOW
	helper.trust = 80.0
	Actions._pick_up(sim, wx + 2, wy)
	run(sim, 4.5)
	ok(int(p.carrying.get("o", 0)) == Defs.O_FRIDGE, "with a companion on the other end it comes up")
	ok(SaveGame.save(sim, slot), "saving with furniture in your arms")
	s2 = SaveGame.load_game(slot)
	ok(s2 != null and int(s2.player.carrying.get("o", 0)) == Defs.O_FRIDGE, "what you are carrying survives a reload")
	p.facing = Vector2(0, 1)
	Actions.interact(sim)
	sim.npcs.list.clear()
	ok(p.carrying.is_empty(), "and can be set down again")

	print("== construction")
	bulldoze(sim, Rect2i(fx0, fy0 + 30, 10, 10))
	p.pos = Vector2(fx0 + 4.5, fy0 + 34.5)
	p.facing = Vector2(1, 0)
	p.skills["carpentry"] = Player.XP_LEVELS[4]
	p.skills["metalworking"] = Player.XP_LEVELS[2]
	for it in [["plank", 40], ["nails", 120], ["scrap_metal", 12], ["wire", 6], ["stone", 6], ["hammer", 1], ["saw", 1], ["wrench", 1]]:
		Inv.add_new(p.inv, it[0], it[1])
	var planks0: int = Inv.count(p.inv, "plank")
	var rt: Vector2i = p.front_tile()
	var roof_r: Dictionary = Recipes.by_id("roof")
	ok(not Actions.build_target(sim, roof_r)["ok"], "a roof with nothing to rest on is refused, with a reason")
	ok(Actions.craft(sim, Recipes.by_id("metal_wall")), "a sheet-metal wall can be started")
	run(sim, 10.0)
	var me: Vector3i = p.front_edge()
	ok(Defs.wall_mat(w.wall(me.x, me.y, me.z)) == Defs.WM_METAL and w.edge_blocks(me.x, me.y, me.z), "the metal wall stands and blocks movement")
	ok(Actions.build_target(sim, roof_r)["ok"], "beside a wall, a roof can be built")
	Actions.craft(sim, roof_r)
	run(sim, 7.0)
	ok(w.bld(rt.x, rt.y) == World.PLAYER_BLD and Inv.count(p.inv, "plank") == planks0 - 2, "the roofed tile counts as indoors and the planks are spent")
	p.facing = Vector2(0, 1)
	var st2: Vector2i = p.front_tile()
	ok(Actions.craft(sim, Recipes.by_id("spikes")), "a spike trap can be set")
	run(sim, 7.0)
	ok(Defs.o_id(w.obj(st2.x, st2.y)) == Defs.O_SPIKES and not w.tile_blocked(st2.x, st2.y), "spikes lie on the ground and can be walked over")
	sim._slow_tick(0.01)
	var zsp: Zombie = sim.zombies.spawn(Vector2(st2.x + 0.5, st2.y + 0.5), 0)
	zsp.hp = 500.0
	for i in range(60):
		zsp.pos = Vector2(st2.x + 0.5, st2.y + 0.5)
		if zsp.state == Zombie.DOWN: zsp.state = Zombie.IDLE
		sim._tick_spikes(0.5)
	ok(zsp.hp < 500.0, "an infected standing on them is torn up (%.0f hp left)" % zsp.hp)
	ok(w.obj(st2.x, st2.y) == 0, "and the trap wears out with use")
	sim.zombies.list.clear()
	p.facing = Vector2(-1, 0)
	var sg: Vector2i = p.front_tile()
	Actions.craft(sim, Recipes.by_id("signpost"))
	run(sim, 5.0)
	Inv.add_new(p.inv, "pencil", 1) if Inv.find(p.inv, "pencil").is_empty() else null
	opt(Actions.options(sim, {"kind": "obj", "x": sg.x, "y": sg.y}), "Write").call()
	p.markers.clear()
	opt(Actions.options(sim, {"kind": "obj", "x": sg.x, "y": sg.y}), "Read the sign").call()
	ok(p.markers.size() == 1 and String(w.ent(sg.x, sg.y).get("txt", "")) != "", "a sign can be put up, written on, and read by whoever comes later")
	for rid in ["chair", "counter", "wardrobe", "bookshelf", "workbench", "bench", "nightstand", "chain_fence", "gravel"]:
		ok(not Recipes.by_id(rid).is_empty(), "recipe exists: %s" % rid) if Recipes.by_id(rid).is_empty() else null
	# sheet-metal barricade
	p.facing = Vector2(0, -1)
	Actions.craft(sim, Recipes.by_id("door"))
	run(sim, 10.0)
	var de: Vector3i = p.front_edge()
	var mb: Callable = opt(Actions.options(sim, {"kind": "edge", "x": de.x, "y": de.y, "side": de.z}), "Barricade with sheet metal")
	ok(mb.is_valid(), "a built door accepts a sheet-metal barricade")
	if mb.is_valid():
		mb.call()
		run(sim, 6.5)
		ok(((w.edge_state(de.x, de.y, de.z) & Defs.ES_PLANK_MASK) >> Defs.ES_PLANK_SHIFT) == 4 and w.edge_blocks(de.x, de.y, de.z), "sheet metal seals it in one go")
	# plumbing
	sim.water_off_h = sim.hour - 1.0
	var kx: int = fx0 + 2
	var ky: int = fy0 + 37
	w.set_obj(kx, ky, Defs.ocell(Defs.O_SINK_COUNTER, 0, 0))
	w.set_obj(kx + 1, ky, Defs.ocell(Defs.O_RAIN_BARREL, 0, 0))
	w.set_ent(kx + 1, ky, {"k": "barrel", "w": 20.0})
	p.pos = Vector2(kx + 0.5, ky - 0.5)
	p.thirst = 60.0
	var pl: Callable = opt(Actions.options(sim, {"kind": "obj", "x": kx, "y": ky}), "Plumb")
	ok(pl.is_valid(), "with the mains off, a sink beside a rain collector can be plumbed")
	if pl.is_valid():
		pl.call()
		run(sim, 9.5)
		opt(Actions.options(sim, {"kind": "obj", "x": kx, "y": ky}), "Drink (piped").call()
		run(sim, 4.0)
		ok(p.thirst < 60.0 and float(w.ent(kx + 1, ky)["w"]) < 20.0, "the tap now draws clean water out of the collector (%.0f left)" % float(w.ent(kx + 1, ky)["w"]))

	print("== survivor depth: needs, routine, trust, fear, jobs")
	bulldoze(sim, Rect2i(fx0, fy0 + 30, 10, 10))
	sim.zombies.list.clear()
	sim.npcs.list.clear()
	p.pos = Vector2(fx0 + 2.5, fy0 + 31.5)
	p.wounds.clear()
	var sv = sim.npcs.spawn(Vector2(fx0 + 6.5, fy0 + 35.5), false)
	sv.temper = "cautious"
	sv.job = "medic"
	sv.trust = 30.0
	sv.stock = ["canned_beans", "water_bottle", "nails"]
	sv.hunger = 70.0
	sv.thirst = 70.0
	sim.npcs._needs(sv, 0.1)
	ok(sv.hunger < 40.0 and sv.thirst < 40.0 and not sv.stock.has("canned_beans") and sv.stock.has("empty_bottle"), "a hungry, thirsty survivor eats and drinks from what they carry")
	sv.hunger = 100.0
	sv.thirst = 100.0
	sv.stock = []
	sim.water_off_h = sim.hour - 1.0
	var shp: float = sv.hp
	sim.npcs._needs(sv, 2.0)
	ok(sv.hp < shp, "with nothing left, hunger and thirst wear them down")
	sv.hunger = 50.0
	sv.thirst = 10.0
	sv.hp = 100.0
	# routine: scavenge a nearby container, physically
	var bxx: int = fx0 + 3
	var byy: int = fy0 + 36
	w.set_obj(bxx, byy, Defs.ocell(Defs.O_WOOD_CRATE, 0, 0))
	w.chunk_at(bxx, byy).containers[World.idx(bxx, byy)] = [Items.make("canned_beans", 3, sim.hour)]
	sim.hour = floorf(sim.hour / 24.0) * 24.0 + 24.0 + 10.0
	sv.task = "scavenge"
	sv.task_pos = Vector2(bxx + 0.5, byy + 0.5)
	sv.task_t = 25.0
	var tt2 := 0.0
	while tt2 < 20.0 and sv.task == "scavenge":
		sim.npcs.routine(sv, 1.0 / 30.0)
		tt2 += 1.0 / 30.0
	ok(sv.stock.has("canned_beans") and Inv.count(w.container_at(bxx, byy), "canned_beans") == 2, "by day they scavenge: one tin leaves the crate and is now theirs")
	sim.hour = floorf(sim.hour / 24.0) * 24.0 + 23.5
	sv.task = ""
	sv.home = sv.pos
	sv.fatigue = 70.0
	sim.npcs.routine(sv, 0.1)
	ok(sv.task == "sleep", "at night they sleep where they live")
	ok(opt(sim.npcs.options(sv), "(asleep").is_valid(), "and you are told they are asleep")
	sim.hour = floorf(sim.hour / 24.0) * 24.0 + 24.0 + 9.0
	sv.fatigue = 10.0
	sim.npcs.routine(sv, 0.1)
	ok(sv.task != "sleep", "and get up in the morning")
	# trust
	sv.task = ""
	sv.pos = p.pos + Vector2(1.5, 0.0)
	sv.home = sv.pos
	sv.met = true
	sim.npcs.update(1.0 / 30.0, 0.0)
	var t0x: float = sv.trust
	p.kills += 2
	sim.npcs.update(1.0 / 30.0, 0.0)
	ok(sv.trust > t0x, "killing the infected in front of them earns trust (%.0f -> %.0f)" % [t0x, sv.trust])
	sv.trust = 60.0
	p.add_wound(7, "laceration", "test")
	var heal: Callable = opt(sim.npcs.options(sv), "\"Can you look")
	ok(heal.is_valid(), "a medic who trusts you offers to treat a wound")
	if heal.is_valid():
		heal.call()
		ok(p.wounds[0]["band"] == true, "and dresses it")
	p.markers.clear()
	var tip: Callable = opt(sim.npcs.options(sv), "\"What do you know")
	ok(tip.is_valid(), "at higher trust they share what they know")
	if tip.is_valid():
		tip.call()
		ok(not opt(sim.npcs.options(sv), "\"What do you know").is_valid(), "once")
	Inv.add_new(p.inv, "crowbar", 1)
	var gw: Callable = opt(sim.npcs.options(sv), "Give them your spare")
	ok(gw.is_valid(), "a spare weapon can be handed over")
	if gw.is_valid():
		gw.call()
		ok(sv.wpn != "", "and they keep it (%s)" % sv.wpn)
	# fear
	sv.wpn = ""
	sv.hp = 100.0
	sv.state = NpcSim.STAY
	var fz: Array = []
	for k in range(3):
		var zz2: Zombie = sim.zombies.spawn(sv.pos + Vector2(2.5, -1.0 + k), 0)
		zz2.state = Zombie.IDLE
		fz.append(zz2)
	var f0: Vector2 = sv.pos
	for i in range(45):
		for zz3 in fz: (zz3 as Zombie).state = Zombie.IDLE
		sim.npcs.update(1.0 / 30.0, 0.0)
	ok(sv.pos.distance_to((fz[1] as Zombie).pos) > f0.distance_to((fz[1] as Zombie).pos) + 2.0, "an unarmed, cautious survivor runs from a group instead of fighting (moved %.1f tiles)" % f0.distance_to(sv.pos))
	# bitten to death -> gets back up with their things
	sv.stock = ["nails", "toy"]
	sv.hp = 0.5
	for zz4 in fz: (zz4 as Zombie).pos = sv.pos + Vector2(0.3, 0.0)
	var zn0: int = sim.zombies.list.size()
	sim.npcs.update(0.5, 0.0)
	var risen := false
	for z5 in sim.zombies.list:
		if Inv.count(z5.loot, "toy") == 1 and Inv.count(z5.loot, "nails") == 1: risen = true
	ok(not sim.npcs.list.has(sv) and sim.zombies.list.size() == zn0 + 1 and risen, "a survivor killed by the infected rises as one of them, still carrying their things")
	sim.zombies.list.clear()
	# persistence of the new fields
	var keepn = sim.npcs.spawn(p.pos + Vector2(1.0, 1.0), false)
	keepn.trust = 77.0
	keepn.job = "farmer"
	keepn.temper = "wary"
	keepn.wpn = "crowbar"
	keepn.thirst = 42.0
	ok(SaveGame.save(sim, slot), "saving survivors")
	s2 = SaveGame.load_game(slot)
	var kn = s2.npcs.list[0] if s2 != null and s2.npcs.list.size() == 1 else null
	ok(kn != null and absf(kn.trust - 77.0) < 0.01 and kn.job == "farmer" and kn.temper == "wary" and kn.wpn == "crowbar" and absf(kn.thirst - 42.0) < 0.01, "trust, job, temperament, weapon and needs persist")
	sim.npcs.list.clear()
	p.wounds.clear()
	p.hp = 100.0

	print("== sound through walls, doors, floors and rain")
	bulldoze(sim, Rect2i(fx0, fy0 + 26, 12, 18))
	sim.zombies.list.clear()
	sim.npcs.list.clear()
	sim.weather["rain"] = 0.0
	var sa := Vector2(fx0 + 3.5, fy0 + 34.5)
	var sb := Vector2(fx0 + 9.5, fy0 + 34.5)
	ok(absf(w.sound_pass(sa, sb) - 1.0) < 0.001, "in the open, sound carries its full distance")
	for yy in range(fy0 + 28, fy0 + 41):
		w.set_wall(fx0 + 6, yy, 1, Defs.wall(Defs.WM_BRICK_RED, Defs.WS_SOLID))
	var through: float = w.sound_pass(sa, sb)
	ok(through < 0.6, "a brick wall in the way cuts it (x%.2f)" % through)
	w.set_wall(fx0 + 6, fy0 + 34, 1, Defs.wall(Defs.WM_PLASTER_CREAM, Defs.WS_DOOR))
	var shut: float = w.sound_pass(sa, sb)
	w.set_edge_state(fx0 + 6, fy0 + 34, 1, Defs.ES_OPEN)
	var open_d: float = w.sound_pass(sa, sb)
	ok(shut < 1.0 and shut > through and absf(open_d - 1.0) < 0.001, "a shut door muffles less than a wall (x%.2f); an open one not at all" % shut)
	w.set_wall(fx0 + 6, fy0 + 34, 1, Defs.wall(Defs.WM_BRICK_RED, Defs.WS_SOLID))
	var zh: Zombie = sim.zombies.spawn(sb, 0)
	zh.dir = Vector2(1, 0)
	keep = p.pos
	p.pos = Vector2(-9999, -9999)
	sim.noises.clear()
	sim.noise(sa, 9.0)
	for i in range(20): sim.zombies.update(1.0 / 30.0)
	ok(zh.state == Zombie.IDLE or zh.state == Zombie.WANDER, "a noise that would reach 9 tiles is not heard 6 tiles away behind brick")
	sim.noises.clear()
	sim.noise(sa, 20.0)
	for i in range(20): sim.zombies.update(1.0 / 30.0)
	ok(zh.state == Zombie.INVESTIGATE, "a loud enough one still is")
	sim.zombies.list.clear()
	sim.noises.clear()
	ok(w.sound_pass(sa, Vector2(sa.x + 2.0, sa.y + World.UNDER)) <= 0.4, "the floor between storeys muffles heavily")
	ok(w.heard(sa, 12.0, Vector2(sa.x + 2.0, sa.y + World.UNDER)) and not w.heard(sa, 4.0, Vector2(sa.x + 2.0, sa.y + World.UNDER)), "a crash upstairs carries down; footsteps do not")
	sim.weather["rain"] = 1.0
	var outp := Vector2(fx0 + 1.5, fy0 + 27.5)
	for yy2 in range(fy0 + 27, fy0 + 43):
		if w.bld(fx0 + 1, yy2) == 0: outp = Vector2(fx0 + 1.5, yy2 + 0.5)
	sim.noise(outp, 20.0)
	ok(float(sim.noises[sim.noises.size() - 1][1]) < 16.0, "heavy rain shortens how far outdoor noise carries (%.0f of 20)" % float(sim.noises[sim.noises.size() - 1][1]))
	sim.weather["rain"] = 0.0
	sim.noises.clear()
	p.pos = keep

	print("== factions and settlements")
	bulldoze(sim, Rect2i(fx0, fy0 + 26, 12, 18))
	var F: Factions = sim.factions
	var home_site: Dictionary = F.site_for(0, 0)
	ok(not home_site.is_empty() and Factions.kind(int(home_site["f"])) != Factions.RAIDER, "the starting region has a settlement, and it is not a raider camp (%s)" % (Factions.fname(int(home_site["f"])) if not home_site.is_empty() else "none"))
	var some := 0
	for rx in range(-2, 3):
		for ry in range(-2, 3):
			if not F.site_for(rx, ry).is_empty(): some += 1
	ok(some >= 8 and some < 25, "settlements are scattered across regions, not everywhere (%d of 25)" % some)
	F.sites.clear()
	F.tasks.clear()
	F.rep.clear()
	var key1 := Vector2i(50, 50)
	var s1: Dictionary = F.found(key1, Vector2i(fx0 + 5, fy0 + 34), 2, 3)      # The Wardens
	var members: Array = []
	for k in range(3):
		var mem = sim.npcs.spawn(Vector2(fx0 + 4.5 + k, fy0 + 33.5), false)
		F.enlist(mem, 2, key1)
		mem.temper = "brave"
		mem.stock = []
		members.append(mem)
	p.pos = Vector2(fx0 + 5.5, fy0 + 35.5)
	p.markers.clear()
	var m0 = members[0]
	var mo: Array = sim.npcs.options(m0)
	ok(s1["met"] and p.markers.size() == 1, "meeting a member puts the settlement on your map")
	ok(opt(mo, "Ask about").is_valid() and opt(mo, "\"Is there anything").is_valid() and opt(mo, "\"Could I sleep").is_valid(), "members speak for the settlement: news, work, shelter")
	opt(mo, "\"Is there anything").call()
	var task: Dictionary = F.open_task(key1)
	ok(not task.is_empty() and absf(float(task["due"]) - sim.hour - 72.0) < 0.01, "asking for work creates a task with a three-day deadline")
	if not task.is_empty(): Inv.take(p.inv, task["want"], Inv.count(p.inv, task["want"]))      # start with none of it
	ok(not opt(sim.npcs.options(m0), "Hand over").is_valid(), "it cannot be handed in without the goods")
	Inv.add_new(p.inv, task["want"], int(task["n"]) + 1, sim.hour)
	var have0: int = Inv.count(p.inv, task["want"])
	var rep0: float = F.rep_of(2)
	opt(sim.npcs.options(m0), "Hand over").call()
	ok(task["state"] == "done" and Inv.count(p.inv, task["want"]) == have0 - int(task["n"]) and F.rep_of(2) >= rep0 + 15.0, "delivering it spends the goods and raises your standing with the whole faction (%.0f)" % F.rep_of(2))
	opt(sim.npcs.options(m0), "\"Is there anything").call()
	var task2: Dictionary = F.open_task(key1)
	sim.hour += 80.0
	var rep1: float = F.rep_of(2)
	F.tick(0.1)
	ok(task2["state"] == "expired" and F.rep_of(2) < rep1, "a task left too long expires and costs you standing")
	# the ledger
	s1["food"] = 3.0
	var food_a: float = s1["food"]
	F.tick(24.0)
	ok(float(s1["food"]) < food_a, "a settlement eats through its stores (%.1f -> %.1f)" % [food_a, float(s1["food"])])
	Inv.add_new(p.inv, "cooked_egg", 1, sim.hour)
	var food_b: float = s1["food"]
	var gv: Callable = Callable()
	for o8 in sim.npcs.options(m0):
		if String(o8["label"]).ends_with("to their stores"): gv = o8["fn"]
	ok(gv.is_valid(), "food can be given to the stores")
	if gv.is_valid():
		gv.call()
		ok(float(s1["food"]) > food_b, "and goes into the ledger")
	members[1].hunger = 80.0
	s1["food"] = 5.0
	sim.npcs._needs(members[1], 0.01)
	ok(members[1].hunger < 50.0 and float(s1["food"]) < 5.0, "members eat from the settlement's stores")
	# raiders and other people
	var key2 := Vector2i(51, 50)
	var s3: Dictionary = F.found(key2, Vector2i(fx0 + 9, fy0 + 40), 3, 2)       # Harrow Road Crew
	var raider = sim.npcs.spawn(Vector2(fx0 + 6.5, fy0 + 36.5), true)
	F.enlist(raider, 3, key2)
	raider.hp = 60.0
	members[2].pos = raider.pos + Vector2(0.8, 0.0)
	members[2].hp = 100.0
	sim.settings["god"] = true
	p.pos = Vector2(fx0 + 1.5, fy0 + 27.5)
	var tt3 := 0.0
	while tt3 < 20.0 and sim.npcs.list.has(raider) and sim.npcs.list.has(members[2]):
		sim.npcs.update(1.0 / 30.0, 0.0)
		tt3 += 1.0 / 30.0
	ok(members[2].hp < 100.0 or not sim.npcs.list.has(raider), "a raider attacks other survivors, and they fight back (%.1f s)" % tt3)
	s1["food"] = 40.0
	s3["food"] = 2.0
	s1["met"] = true
	F._raid()
	ok(float(s1["food"]) < 40.0 and float(s3["food"]) > 2.0, "raiders take from the nearest settlement while you are away (%.0f left)" % float(s1["food"]))
	# violence against a member
	p.pos = members[0].pos + Vector2(-0.8, 0.0)
	var repv: float = F.rep_of(2)
	sim.npcs.damage(members[0], 10.0, true)
	ok(F.rep_of(2) <= repv - 25.0, "striking one of them is held against you by all of them (%.0f)" % F.rep_of(2))
	F.rep[2] = -30.0
	sim.npcs.update(1.0 / 30.0, 0.0)
	var all_hostile := true
	for mem2 in members:
		if sim.npcs.list.has(mem2) and mem2.state != NpcSim.HOSTILE: all_hostile = false
	ok(all_hostile, "with standing that low, every member is hostile on sight")
	ok(SaveGame.save(sim, slot), "saving factions")
	s2 = SaveGame.load_game(slot)
	ok(s2 != null and s2.factions.sites.has(key1) and absf(s2.factions.rep_of(2) + 30.0) < 0.01 and s2.factions.tasks.size() == 2, "settlements, standing and tasks persist")
	var facs_ok := s2 != null
	if s2 != null:
		for nn2 in s2.npcs.list:
			if nn2.fac != 2 and nn2.fac != 3: facs_ok = false
	ok(facs_ok, "members keep their allegiance across a reload")
	# collapse
	F.rep[2] = 0.0
	s1["met"] = true
	var open_before := 0
	opt(F.options(members[1], 60.0), "\"Is there anything").call() if sim.npcs.list.has(members[1]) else null
	for mem3 in members:
		if sim.npcs.list.has(mem3): sim.npcs.damage(mem3, 999.0, false)
	ok(s1["fallen"] and F.open_task(key1).is_empty(), "when the last member dies the settlement falls and its work is void")
	sim.npcs.list.clear()
	F.sites.clear()
	F.tasks.clear()
	F.rep.clear()
	# and for real: walking into the region's site finds people living there
	var real_site: Dictionary = F.site_for(0, 0)
	var rc: Vector2i = real_site["c"]
	keep = p.pos
	p.pos = Vector2(rc.x + 0.5, rc.y + 0.5)
	w.stream(p.pos, 2, 999)
	sim._process_world_events()
	var living := 0
	for nn3 in sim.npcs.list:
		if nn3.fac == int(real_site["f"]): living += 1
	ok(F.sites.has(Vector2i(0, 0)) and living >= 3, "the generated settlement is populated when you first reach it (%d people of %s)" % [living, Factions.fname(int(real_site["f"]))])
	p.pos = keep
	w.stream(p.pos, 3, 999)
	sim._process_world_events()
	quiet(sim)
	bulldoze(sim, Rect2i(fx0, fy0 + 26, 12, 18))

	print("== wildlife, hunting, butchering, preserving")
	bulldoze(sim, Rect2i(fx0, fy0 + 26, 12, 18))
	sim.zombies.list.clear()
	sim.npcs.list.clear()
	sim.animals.list.clear()
	sim.noises.clear()
	var AS: AnimalSim = sim.animals
	# populations come from the land: the wild has animals, town does not
	var wild := 0
	var town := 0
	for cx3 in range(40):
		var ch3 := Chunk.new(1000 + cx3, 1000)
		ch3.zone = 0
		for i3 in range(256): ch3.ground[i3] = Defs.G_GRASS
		var n0: int = AS.list.size()
		AS.on_chunk_loaded(ch3, true)
		wild += AS.list.size() - n0
		var ch4 := Chunk.new(2000 + cx3, 1000)
		ch4.zone = 3
		for i4 in range(256): ch4.ground[i4] = Defs.G_GRASS
		n0 = AS.list.size()
		AS.on_chunk_loaded(ch4, true)
		town += AS.list.size() - n0
	ok(wild >= 15 and town == 0, "animals live in the wild, not in town (%d in 40 wild chunks, %d in town)" % [wild, town])
	AS.list.clear()
	p.pos = Vector2(fx0 + 2.5, fy0 + 30.5)
	p.sneaking = false
	var rab: AnimalSim.Animal = AS.spawn("rabbit", p.pos + Vector2(3.0, 0.0))
	AS.update(1.0 / 30.0)
	ok(rab.state == AnimalSim.FLEE, "a rabbit that sees you bolts")
	var r0: Vector2 = rab.pos
	for i in range(30): AS.update(1.0 / 30.0)
	ok(rab.pos.distance_to(p.pos) > r0.distance_to(p.pos), "away from you")
	AS.list.clear()
	p.sneaking = true
	var deer: AnimalSim.Animal = AS.spawn("deer", p.pos + Vector2(6.0, 0.0))
	AS.update(1.0 / 30.0)
	ok(deer.state == AnimalSim.IDLE, "sneaking, you can get within six tiles of a deer without spooking it")
	sim.noise(p.pos, 12.0)
	AS.update(1.0 / 30.0)
	ok(deer.state == AnimalSim.FLEE, "a noise sends it running")
	sim.noises.clear()
	p.sneaking = false
	AS.list.clear()
	# tracking
	var far_deer: AnimalSim.Animal = AS.spawn("deer", p.pos + Vector2(0.0, 18.0))
	var trk: String = AS.track(p.pos, 0)
	ok(trk.begins_with("Deer sign") and trk.contains("paces"), "tracking reads the nearest animal's direction and distance (\"%s\")" % trk)
	AS.list.clear()
	ok(AS.track(p.pos, 0) == "", "and finds nothing where nothing lives")
	# melee kill -> carcass -> butcher with skill-scaled yield
	sim.settings["god"] = true
	var r2: AnimalSim.Animal = AS.spawn("rabbit", p.pos + Vector2(0.8, 0.0))
	p.facing = Vector2(1, 0)
	p.weapon = {}
	Inv.add_new(p.inv, "kitchen_knife", 1)
	p.equip(Inv.find(p.inv, "kitchen_knife"))
	var swings2 := 0
	while AS.list.has(r2) and swings2 < 10:
		p.attack_cd = 0.0
		p.swing_t = 0.0
		p.try_attack()
		for fr_i in range(24):
			r2.pos = p.pos + Vector2(0.8, 0.0)      # a snared rabbit cannot run
			r2.state = AnimalSim.IDLE
			sim.tick(1.0 / 30.0)
		swings2 += 1
	var carcass: Array = w.items_at(floori(p.pos.x + 0.8), floori(p.pos.y))
	ok(not AS.list.has(r2) and Inv.count(carcass, "carcass_rabbit") == 1, "a rabbit can be killed with a knife and leaves a carcass (%d swings)" % swings2)
	Inv.add_new(p.inv, "carcass_rabbit", 1, sim.hour)
	p.skills["butchering"] = 0.0
	Actions.craft(sim, Recipes.by_id("butcher_rabbit"))
	run(sim, 5.5)
	var novice: int = Inv.count(p.inv, "raw_rabbit")
	Inv.take(p.inv, "raw_rabbit", novice)
	Inv.add_new(p.inv, "carcass_deer", 1, sim.hour)
	p.skills["butchering"] = Player.XP_LEVELS[6]
	Actions.craft(sim, Recipes.by_id("butcher_deer"))
	run(sim, 12.5)
	ok(novice >= 1 and Inv.count(p.inv, "raw_venison") >= 7 and Inv.count(p.inv, "leather") >= 2, "butchering gives meat and hide, more for a practised hand (novice rabbit %d, skilled deer %d)" % [novice, Inv.count(p.inv, "raw_venison")])
	# a shotgun at range
	var dg: AnimalSim.Animal = AS.spawn("deer", p.pos + Vector2(3.0, 0.0))
	dg.hp = 400.0
	Inv.add_new(p.inv, "shotgun", 1)
	Inv.add_new(p.inv, "shells", 10)
	p.equip(Inv.find(p.inv, "shotgun"))
	p.weapon["u"] = 4
	p.weapon["c"] = 1.0
	p.facing = Vector2(1, 0)
	var hp_d: float = dg.hp
	sim.zombies.list.clear()
	for i in range(4):
		dg.pos = p.pos + Vector2(3.0, 0.0)
		dg.state = AnimalSim.IDLE
		p.attack_cd = 0.0
		p.swing_t = 0.0
		p.try_attack()
	ok(dg.hp < hp_d, "a gun hits game at range (%.0f -> %.0f)" % [hp_d, dg.hp])
	AS.list.clear()
	# a boar fights back
	sim.settings["god"] = false
	p.hp = 100.0
	var boar: AnimalSim.Animal = AS.spawn("boar", p.pos + Vector2(2.0, 0.0))
	var tb := 0.0
	while tb < 6.0 and p.hp >= 100.0:
		AS.update(1.0 / 30.0)
		tb += 1.0 / 30.0
	ok(boar.state == AnimalSim.CHARGE and p.hp < 100.0, "a boar you get close to charges and gores you (%.0f hp)" % p.hp)
	sim.settings["god"] = true
	p.hp = 100.0
	p.wounds.clear()
	AS.list.clear()
	# overhunting
	var hc := Chunk.new(3000, 3000)
	hc.zone = 0
	for i5 in range(256): hc.ground[i5] = Defs.G_GRASS
	var seedhunt := 0
	for k5 in range(60):
		hc.cx = 3000 + k5
		var n1: int = AS.list.size()
		AS.on_chunk_loaded(hc, true)
		if AS.list.size() > n1:
			seedhunt = k5
			break
	AS.list.clear()                        # every animal there is shot
	hc.an_h = sim.hour
	AS.on_chunk_loaded(hc, false)
	ok(AS.list.is_empty(), "hunted out, an area stays empty when you come straight back")
	hc.an_h = sim.hour - 100.0
	AS.on_chunk_loaded(hc, false)
	ok(AS.list.size() == 1, "after four days one animal has wandered back in")
	AS.list.clear()
	# preservation
	p.weapon = {}
	sim.hour = floorf(sim.hour)
	Inv.add_new(p.inv, "branch", 4)
	var fire_x: int = floori(p.pos.x) + 1
	var fire_y: int = floori(p.pos.y)
	w.set_obj(fire_x, fire_y, Defs.ocell(Defs.O_CAMPFIRE, 0, 0))
	w.set_ent(fire_x, fire_y, {"k": "fire", "fuel": 10.0, "lit": true})
	sim._slow_tick(0.01)
	var v0: int = Inv.count(p.inv, "raw_venison")
	p.skills["cooking"] = Player.XP_LEVELS[6]      # nobody burns it at this level
	print("    smoke missing: ", Recipes.missing(Recipes.by_id("smoke_venison"), p, sim.near_heat(p.pos), false, []))
	ok(Actions.craft(sim, Recipes.by_id("smoke_venison")), "venison can be smoked over a fire")
	sim.zombies.list.clear()
	run(sim, 10.5)
	ok(Inv.count(p.inv, "smoked_meat") >= 2 and Inv.count(p.inv, "raw_venison") == v0 - 2, "smoking turns raw meat into smoked meat")
	var sm: Dictionary = Inv.find(p.inv, "smoked_meat")
	var rv: Dictionary = Inv.find(p.inv, "raw_venison")
	ok(Items.fresh_state(rv, sim.hour + 100.0) == 2 and Items.fresh_state(sm, sim.hour + 100.0) == 0, "four days later the raw meat has rotted and the smoked meat has not")
	Inv.add_new(p.inv, "salt", 1)
	ok(Actions.craft(sim, Recipes.by_id("jerky_venison")), "salt and a knife make jerky")
	run(sim, 9.5)
	ok(Inv.count(p.inv, "jerky") >= 2 and int(Inv.find(p.inv, "salt").get("u", 0)) == 5, "salt is used a pinch at a time")
	w.remove_object(fire_x, fire_y)
	# persistence
	var keep_a: AnimalSim.Animal = AS.spawn("fox", p.pos + Vector2(3.0, 3.0))
	keep_a.hp = 7.0
	ok(SaveGame.save(sim, slot), "saving wildlife")
	s2 = SaveGame.load_game(slot)
	var fox_back := false
	if s2 != null:
		for a6 in s2.animals.list:
			if a6.kind == "fox" and absf(a6.hp - 7.0) < 0.01: fox_back = true
	ok(fox_back, "a wounded fox is still wounded after a reload")
	AS.list.clear()

	print("== vehicle types, parts, towing, sleeping in a car")
	sim.zombies.list.clear()
	sim.npcs.list.clear()
	sim.animals.list.clear()
	bulldoze(sim, Rect2i(fx0, fy0, 12, 44))
	for yy3 in range(fy0, fy0 + 44):
		for xx3 in range(fx0, fx0 + 12):
			w.set_ground(xx3, yy3, Defs.G_ASPHALT)
	sim.settings["god"] = true
	var tops: Dictionary = {}
	for vt in [Defs.O_CAR, Defs.O_VAN, Defs.O_PICKUP, Defs.O_MOTORBIKE, Defs.O_BICYCLE]:
		var vx: int = fx0 + 5
		var vy: int = fy0 + 2
		var fsv: Vector2i = Defs.obj_size(vt, 0)
		for jj in range(fsv.y):
			for ii in range(fsv.x):
				w.set_obj(vx + ii, vy + jj, Defs.ocell(vt, 0, jj * fsv.x + ii))
		var ve: Dictionary = Vehicle.car_ent(sim, vx, vy)
		ve["key"] = 1; ve["bat"] = 1; ve["eng"] = 1.0; ve["tire"] = 1.0
		if vt != Defs.O_BICYCLE: ve["fuel"] = Vehicle.tank_of(vt)
		p.pos = Vector2(vx - 0.5, vy + 1.5)
		p.endurance = 100.0
		var co2: Array = Actions._car_options(sim, vx, vy)
		var go: Callable = Callable()
		for o in co2:
			if String(o["label"]).begins_with("Drive") or String(o["label"]).begins_with("Ride"): go = o["fn"]
		ok(go.is_valid(), "%s can be driven or ridden" % Defs.obj(vt)["n"])
		go.call()
		var vv: Vehicle = sim.vehicle
		ok(vv != null and vv.oid == vt and vv.size() == Vector2(fsv), "you are on the %s" % Defs.obj(vt)["n"].to_lower())
		var top := 0.0
		var t9 := 0.0
		while t9 < 4.0:
			sim.tick(1.0 / 30.0, screen_for(Vector2(0, 1)), false)
			top = maxf(top, vv.speed)
			t9 += 1.0 / 30.0
		tops[vt] = top
		if vt == Defs.O_BICYCLE:
			ok(p.endurance < 100.0 and float(vv.ent.get("fuel", 0.0)) == 0.0, "pedalling uses your stamina, not fuel (%.0f left)" % p.endurance)
			sim.noises.clear()
			run(sim, 1.0, screen_for(Vector2(0, 1)))
			var loudest := 0.0
			for nz in sim.noises: loudest = maxf(loudest, float(nz[1]))
			ok(loudest < 4.0, "a bicycle is nearly silent (%.1f)" % loudest)
		sim.brake = true
		run(sim, 2.0)
		sim.brake = false
		Actions.exit_vehicle(sim)
		ok(sim.vehicle == null, "and get off again")
		var pa2: Vector2i = Vector2i(roundi(vv.anchor_f().x), roundi(vv.anchor_f().y))
		w.remove_object(pa2.x, pa2.y)
	ok(tops[Defs.O_MOTORBIKE] > tops[Defs.O_CAR] and tops[Defs.O_CAR] > tops[Defs.O_VAN] and tops[Defs.O_BICYCLE] < tops[Defs.O_VAN], "they differ: motorcycle %.1f > car %.1f > van %.1f > bicycle %.1f tiles/s" % [tops[Defs.O_MOTORBIKE], tops[Defs.O_CAR], tops[Defs.O_VAN], tops[Defs.O_BICYCLE]])
	# protection by type and by glass
	sim.settings["god"] = false
	var zp: Zombie = sim.zombies.spawn(p.pos + Vector2(20, 0), 0)
	var moto := Vehicle.new()
	moto.sim = sim
	moto.oid = Defs.O_MOTORBIKE
	moto.ent = {"win": 1.0}
	sim.vehicle = moto
	var bike_hits := 0
	for i in range(100):
		p.hp = 100.0
		p.wounds.clear()
		p.infection = -1.0
		p.take_zombie_hit(zp)
		if not p.wounds.is_empty() or p.hp < 99.0: bike_hits += 1
	var vn := Vehicle.new()
	vn.sim = sim
	vn.oid = Defs.O_VAN
	vn.ent = {"win": 1.0}
	sim.vehicle = vn
	var van_hits := 0
	for i in range(100):
		p.hp = 100.0
		p.wounds.clear()
		p.infection = -1.0
		p.take_zombie_hit(zp)
		if not p.wounds.is_empty() or p.hp < 99.0: van_hits += 1
	vn.ent["win"] = 0.0
	var broken_hits := 0
	for i in range(100):
		p.hp = 100.0
		p.wounds.clear()
		p.infection = -1.0
		p.take_zombie_hit(zp)
		if not p.wounds.is_empty() or p.hp < 99.0: broken_hits += 1
	sim.vehicle = null
	sim.zombies.list.clear()
	sim.settings["god"] = true
	p.hp = 100.0
	p.wounds.clear()
	p.infection = -1.0
	ok(bike_hits > 85 and van_hits < 25 and broken_hits > van_hits + 15, "a motorcycle protects nothing (%d/100 got through), a van a lot (%d), a van with smashed windows less (%d)" % [bike_hits, van_hits, broken_hits])
	# crash damage to parts, then repairs
	var cx2: int = fx0 + 5
	var cy2: int = fy0 + 2
	place_car(sim, cx2, cy2)
	var ce2: Dictionary = Vehicle.car_ent(sim, cx2, cy2)
	ce2["key"] = 1; ce2["bat"] = 1; ce2["eng"] = 1.0; ce2["tire"] = 1.0; ce2["win"] = 1.0; ce2["lit"] = 1; ce2["fuel"] = 10.0
	p.pos = Vector2(cx2 - 0.5, cy2 + 1.5)
	sim.vehicle = Vehicle.enter(sim, cx2, cy2)
	var cv: Vehicle = sim.vehicle
	seed(5)
	for i in range(6): cv.crash(9.0)
	ok(float(cv.ent["tire"]) < 1.0 and float(cv.ent["win"]) < 1.0 and int(cv.ent["lit"]) == 0 and float(cv.ent["eng"]) < 1.0, "hard crashes damage tyres, windows, lights and the engine (%s)" % Actions.condition_text(cv.ent, Defs.O_CAR))
	p.hp = 100.0
	p.wounds.clear()
	cv.ent["tire"] = 0.1
	var vmax_flat := 0.0
	cv.speed = 0.0
	for i in range(90):
		cv.update(1.0 / 30.0, screen_for(Vector2(0, 1)), false)
		vmax_flat = maxf(vmax_flat, cv.speed)
	ok(vmax_flat < tops[Defs.O_CAR] * 0.45, "on flat tyres it crawls (%.1f tiles/s)" % vmax_flat)
	cv.speed = 0.0
	Actions.exit_vehicle(sim)
	var pa3: Vector2i = Vector2i(roundi(cv.anchor_f().x), roundi(cv.anchor_f().y))
	var pe: Dictionary = w.ent(pa3.x, pa3.y)
	Inv.add_new(p.inv, "duct_tape", 1)
	Inv.add_new(p.inv, "glass_pane", 3)
	Inv.add_new(p.inv, "wire", 1)
	p.skills["electrical"] = Player.XP_LEVELS[1]
	p.pos = Vector2(pa3.x - 0.5, pa3.y + 1.5)
	for lbl in ["Patch the tyres", "Fit a new window", "Rewire the headlights"]:
		var fnr: Callable = opt(Actions._car_options(sim, pa3.x, pa3.y), lbl)
		ok(fnr.is_valid(), "repair offered: %s" % lbl)
		if fnr.is_valid():
			fnr.call()
			run(sim, 7.5)
	ok(float(pe["tire"]) > 0.35 and float(pe["tire"]) <= 0.85 and float(pe["win"]) > 0.3 and int(pe["lit"]) == 1, "each part is repaired with its own materials (%s)" % Actions.condition_text(pe, Defs.O_CAR))
	# towing a wreck off the road
	w.remove_object(pa3.x, pa3.y)
	var tx2: int = fx0 + 5
	var ty2: int = fy0 + 10
	place_car(sim, tx2, ty2)
	var te: Dictionary = Vehicle.car_ent(sim, tx2, ty2)
	te["key"] = 1; te["bat"] = 1; te["eng"] = 1.0; te["tire"] = 1.0; te["fuel"] = 12.0
	for jj2 in range(4):
		for ii2 in range(2):
			w.set_obj(tx2 + ii2, ty2 - 4 + jj2, Defs.ocell(Defs.O_CAR_WRECK, 0, jj2 * 2 + ii2))
	w.chunk_at(tx2, ty2 - 4).containers[World.idx(tx2, ty2 - 4)] = [Items.make("toy", 1)]
	p.pos = Vector2(tx2 - 0.5, ty2 + 1.5)
	sim.vehicle = Vehicle.enter(sim, tx2, ty2)
	var tv: Vehicle = sim.vehicle
	var hm: Callable = opt(Actions.vehicle_menu(sim), "Hitch")
	ok(hm.is_valid(), "a wreck right behind you can be hitched")
	if hm.is_valid(): hm.call()
	ok(not tv.tow.is_empty() and w.obj(tx2, ty2 - 4) == 0, "hitched: it leaves the road")
	var fuel_t0: float = tv.ent["fuel"]
	var y_t0: float = tv.pos.y
	var top_t := 0.0
	for i in range(120):
		sim.tick(1.0 / 30.0, screen_for(Vector2(0, 1)), false)
		top_t = maxf(top_t, tv.speed)
	ok(tv.pos.y > y_t0 + 6.0 and top_t < tops[Defs.O_CAR] * 0.7, "towing is slower (%.1f vs %.1f tiles/s)" % [top_t, tops[Defs.O_CAR]])
	ok(SaveGame.save(sim, slot), "saving mid-tow")
	s2 = SaveGame.load_game(slot)
	ok(s2 != null and s2.vehicle != null and int(s2.vehicle.tow.get("o", 0)) == Defs.O_CAR_WRECK, "the tow survives a reload")
	sim.brake = true
	run(sim, 2.0)
	sim.brake = false
	var ua: Callable = opt(Actions.vehicle_menu(sim), "Unhitch")
	ok(ua.is_valid(), "and can be unhitched")
	if ua.is_valid(): ua.call()
	var tanc: Vector2i = tv.tow_anchor(roundi(tv.anchor_f().x), roundi(tv.anchor_f().y))
	ok(tv.tow.is_empty() and Defs.o_id(w.obj(tanc.x, tanc.y)) == Defs.O_CAR_WRECK and Inv.count(w.container_at(tanc.x, tanc.y), "toy") == 1, "dropped behind you with its contents")
	ok(w.obj(tx2, ty2 - 4) == 0, "the road where it stood is clear")
	# sleep in the seat
	p.fatigue = 75.0
	var sl: Callable = opt(Actions.vehicle_menu(sim), "Sleep in the seat")
	ok(sl.is_valid(), "a stopped car can be slept in")
	if sl.is_valid():
		sl.call()
		ok(p.sleeping and sim.vehicle != null, "you sleep in it")
		sim.wake("test")
	Actions.exit_vehicle(sim)
	ok(not opt(Actions._car_options(sim, 0, 0), "Sleep").is_valid(), "(not offered on foot)")

	print("== power: loads, switches, generators, batteries, solar")
	sim.zombies.list.clear()
	sim.npcs.list.clear()
	sim.animals.list.clear()
	bulldoze(sim, Rect2i(fx0, fy0, 12, 44))
	sim.power_off_h = sim.hour - 1.0
	sim.water_off_h = sim.hour - 1.0
	sim.weather["rain"] = 0.0
	sim.weather["temp"] = 15.0
	var gx: int = fx0 + 2
	var gy: int = fy0 + 20
	var fridge_x: int = fx0 + 5
	var fridge_y: int = fy0 + 20
	var base_load: int = sim.loads_near(fx0 + 2, fy0 + 20, Sim.GEN_RANGE)      # whatever the nearby houses already have plugged in
	w.set_obj(fridge_x, fridge_y, Defs.ocell(Defs.O_FRIDGE, 0, 0))
	sim._slow_tick(0.01)
	ok(not sim.has_power(fridge_x, fridge_y), "with the grid down, a fridge is dead")
	w.set_obj(gx, gy, Defs.ocell(Defs.O_GENERATOR, 0, 0))
	w.set_ent(gx, gy, {"k": "gen", "fuel": 40.0, "on": true, "c": 1.0})
	sim._slow_tick(0.01)
	ok(sim.has_power(fridge_x, fridge_y) and sim.loads_near(gx, gy, Sim.GEN_RANGE) == base_load + 1, "a running generator powers it (load %d)" % (base_load + 1))
	var ge2: Dictionary = w.ent(gx, gy)
	var f_one: float = ge2["fuel"]
	sim._slow_tick(1.0)
	var burn_one: float = f_one - float(ge2["fuel"])
	var fe: Callable = opt(Actions.options(sim, {"kind": "obj", "x": fridge_x, "y": fridge_y}), "Switch off")
	ok(fe.is_valid(), "an appliance can be switched off at the switch")
	fe.call()
	ok(not sim.has_power(fridge_x, fridge_y) and sim.loads_near(gx, gy, Sim.GEN_RANGE) == base_load, "switched off it draws nothing and runs nothing")
	opt(Actions.options(sim, {"kind": "obj", "x": fridge_x, "y": fridge_y}), "Switch on").call()
	for k6 in range(9):
		w.set_obj(fx0 + 1 + k6, fy0 + 24, Defs.ocell(Defs.O_LAMP, 0, 0))
	var f_many: float = ge2["fuel"]
	var c_many: float = ge2["c"]
	sim._slow_tick(1.0)
	ok(f_many - float(ge2["fuel"]) > burn_one * 1.5, "more appliances burn more fuel (%.2f vs %.2f per hour)" % [f_many - float(ge2["fuel"]), burn_one])
	ok(c_many - float(ge2["c"]) > 0.05, "too many for one generator wears it hard (%d of %d)" % [int(ge2.get("load", 0)), Sim.GEN_CAP])
	var tripped := false
	for i in range(30):
		ge2["on"] = true
		ge2["c"] = 1.0
		sim._slow_tick(0.5)
		if not ge2["on"]:
			tripped = true
			break
	ok(tripped, "and sooner or later it trips")
	for k7 in range(9):
		w.remove_object(fx0 + 1 + k7, fy0 + 24)
	ge2["on"] = true
	ge2["c"] = 1.0
	sim.weather["rain"] = 1.0
	var c_dry: float = 1.0
	for i in range(60):
		ge2["on"] = true                      # keep it running: we are testing the rain, not tripping
		sim._slow_tick(0.5)
		if float(ge2["c"]) < c_dry - 0.2: break
	ok(float(ge2["c"]) < c_dry - 0.2, "a generator left out in the rain shorts and wears (%d%%)" % int(float(ge2["c"]) * 100.0))
	sim.weather["rain"] = 0.0
	ge2["on"] = false
	w.remove_object(gx, gy)
	# battery bank + solar
	p.skills["electrical"] = Player.XP_LEVELS[3]
	Inv.add_new(p.inv, "car_battery", 2)
	Inv.add_new(p.inv, "wire", 5)
	Inv.add_new(p.inv, "glass_pane", 1)
	Inv.add_new(p.inv, "scrap_metal", 2)
	Inv.add_new(p.inv, "screwdriver", 1)
	p.pos = Vector2(fridge_x + 0.5, fridge_y + 2.5)
	p.facing = Vector2(-1, 0)
	var bt2: Vector2i = p.front_tile()
	ok(Actions.craft(sim, Recipes.by_id("battery_bank")), "a battery bank can be wired from car batteries")
	run(sim, 10.5)
	ok(Defs.o_id(w.obj(bt2.x, bt2.y)) == Defs.O_BATTERY_BANK and Inv.count(p.inv, "car_battery") == 0, "it is built from the batteries you carried")
	sim._slow_tick(0.01)
	var bank_e: Dictionary = w.ent(bt2.x, bt2.y)
	ok(not sim.has_power(fridge_x, fridge_y), "an empty bank powers nothing")
	p.facing = Vector2(0, 1)
	var sol: Vector2i = p.front_tile()
	ok(Actions.craft(sim, Recipes.by_id("solar_panel")), "a solar panel can be assembled")
	run(sim, 12.5)
	ok(Defs.o_id(w.obj(sol.x, sol.y)) == Defs.O_SOLAR, "and stands where you built it")
	sim.hour = floorf(sim.hour / 24.0) * 24.0 + 24.0 + 12.0
	sim.weather["cloud"] = 0.0
	bank_e = w.ent(bt2.x, bt2.y)
	var ch0: float = float(bank_e.get("w", 0.0))
	for i in range(8): sim._slow_tick(1.0)
	bank_e = w.ent(bt2.x, bt2.y)
	var ch1: float = float(bank_e.get("w", 0.0))
	ok(ch1 > ch0 + 5.0, "noon sun charges the bank (%.0f -> %.0f)" % [ch0, ch1])
	sim._slow_tick(0.01)
	ok(sim.has_power(fridge_x, fridge_y), "and a charged bank runs the fridge silently")
	sim.noises.clear()
	sim._slow_tick(0.01)
	var hum := false
	for nz2 in sim.noises:
		if (nz2[0] as Vector2).distance_to(Vector2(bt2.x + 0.5, bt2.y + 0.5)) < 1.0: hum = true
	ok(not hum, "a battery bank makes no noise")
	sim.hour = floorf(sim.hour / 24.0) * 24.0 + 24.0 + 1.0
	var night0: float = float(w.ent(bt2.x, bt2.y)["w"])
	for i in range(4): sim._slow_tick(1.0)
	ok(float(w.ent(bt2.x, bt2.y)["w"]) < night0, "at night it runs down (%.0f -> %.0f)" % [night0, float(w.ent(bt2.x, bt2.y)["w"])])
	w.remove_object(fridge_x, fridge_y)
	w.remove_object(bt2.x, bt2.y)
	w.remove_object(sol.x, sol.y)
	sim._slow_tick(0.01)

	print("== water: pipes, freezing, washing")
	var hb: int = sim.safe_bld
	sim.pipes.clear()
	var left0: int = sim.pipe_water(hb)
	ok(left0 >= 12 and left0 < 26, "after the mains fail a house's pipes still hold some water (%d)" % left0)
	var sx2: int = fx0 + 3
	var sy2: int = fy0 + 30
	w.set_obj(sx2, sy2, Defs.ocell(Defs.O_SINK_COUNTER, 0, 0))
	w.chunk_at(sx2, sy2).bld[World.idx(sx2, sy2)] = hb
	p.pos = Vector2(sx2 + 0.5, sy2 - 0.5)
	p.thirst = 70.0
	var dp2: Callable = opt(Actions.options(sim, {"kind": "obj", "x": sx2, "y": sy2}), "Drink what is left")
	ok(dp2.is_valid(), "the tap offers what is left in the pipes")
	if dp2.is_valid():
		dp2.call()
		run(sim, 2.5)
	ok(p.thirst < 70.0 and sim.pipe_water(hb) == left0 - 1, "drinking takes from it")
	sim.pipes[hb] = 0
	ok(not opt(Actions.options(sim, {"kind": "obj", "x": sx2, "y": sy2}), "Drink what is left").is_valid(), "and once it is gone, it is gone")
	w.chunk_at(sx2, sy2).bld[World.idx(sx2, sy2)] = 0
	w.remove_object(sx2, sy2)
	var rbx: int = fx0 + 6
	var rby: int = fy0 + 30
	w.set_obj(rbx, rby, Defs.ocell(Defs.O_RAIN_BARREL, 0, 0))
	w.chunk_at(rbx, rby).bld[World.idx(rbx, rby)] = 0          # out in the open
	w.set_ent(rbx, rby, {"k": "barrel", "w": 20.0})
	sim.weather["temp"] = -6.0
	sim._sim_ents(w.chunk_at(rbx, rby), 0.5, false)
	var ro: Array = Actions.options(sim, {"kind": "obj", "x": rbx, "y": rby})
	ok(opt(ro, "Frozen solid").is_valid() and not opt(ro, "Drink rainwater").is_valid(), "in a hard frost the rain collector freezes")
	sim.weather["temp"] = 8.0
	sim._sim_ents(w.chunk_at(rbx, rby), 0.5, false)
	ok(opt(Actions.options(sim, {"kind": "obj", "x": rbx, "y": rby}), "Drink rainwater").is_valid(), "and thaws when it warms")
	p.grime = 0.0
	p.wounds.clear()
	sim.player.tick_needs(30.0)
	ok(p.grime > 10.0, "days without washing leave you dirty (%.0f)" % p.grime)
	p.grime = 90.0
	ok(p.moodles().any(func(m): return m[0] == "dirty"), "and filthy shows up as a moodle")
	p.add_wound(9, "laceration", "test")
	p.wounds[0]["band"] = true
	var dirty_fast: float = 0.0
	var wcopy: Dictionary = p.wounds[0]
	wcopy["dirty"] = 0.0
	p.tick_needs(4.0)
	dirty_fast = float(wcopy["dirty"])
	var wv2: Callable = opt(Actions.options(sim, {"kind": "obj", "x": rbx, "y": rby}), "Wash yourself")
	ok(wv2.is_valid(), "you can wash at a rain collector")
	wv2.call()
	run(sim, 7.0)
	ok(p.grime < 10.0 and float(w.ent(rbx, rby)["w"]) <= 17.0, "washing uses water and gets you clean (grime %.0f)" % p.grime)
	wcopy["dirty"] = 0.0
	p.tick_needs(4.0)
	ok(float(wcopy["dirty"]) < dirty_fast, "a clean body keeps a dressing clean longer (%.1f vs %.1f)" % [float(wcopy["dirty"]), dirty_fast])
	p.wounds.clear()
	p.hp = 100.0
	w.remove_object(rbx, rby)
	ok(SaveGame.save(sim, slot), "saving power and water state")
	s2 = SaveGame.load_game(slot)
	ok(s2 != null and s2.pipes.has(hb) and int(s2.pipes[hb]) == 0 and absf(s2.player.grime - p.grime) < 0.01, "emptied pipes and grime persist")

	print("== the infected: who they were, feeding, trapped, scent, stairs; hiding, peeking, binoculars, footsteps")
	sim.zombies.list.clear()
	sim.npcs.list.clear()
	sim.animals.list.clear()
	sim.noises.clear()
	bulldoze(sim, Rect2i(fx0, fy0, 12, 44))
	sim.settings["god"] = true
	var roles: Dictionary = {}
	for i_ia in range(400):
		var zr_ia: Zombie = sim.zombies.spawn(Vector2(fx0 + 5.5, fy0 + 30.5), 0)
		roles[zr_ia.role] = int(roles.get(zr_ia.role, 0)) + 1
	ok(roles.size() >= 5 and int(roles.get("civilian", 0)) > 200, "most were ordinary people; some were police, medics, builders, soldiers (%s)" % str(roles))
	sim.zombies.list.clear()
	var cop: Zombie = sim.zombies.spawn(Vector2(fx0 + 5.5, fy0 + 30.5), 0)
	sim.zombies._apply_role(cop, "police")
	var civ: Zombie = sim.zombies.spawn(Vector2(fx0 + 6.5, fy0 + 30.5), 0)
	cop.hp = 100.0
	civ.hp = 100.0
	sim.zombies.damage(cop, 40.0, Vector2(fx0, fy0), 0.0, false, false)
	sim.zombies.damage(civ, 40.0, Vector2(fx0, fy0), 0.0, false, false)
	ok(cop.hp > civ.hp, "a vest still turns part of a blow (police %.0f hp vs civilian %.0f)" % [cop.hp, civ.hp])
	var looted := 0
	for i_ia in range(60):
		var zm: Zombie = sim.zombies.spawn(Vector2(fx0 + 5.5, fy0 + 31.5), 0)
		zm.loot = []
		sim.zombies._apply_role(zm, "medic")
		if Inv.count(zm.loot, "bandage") + Inv.count(zm.loot, "painkillers") + Inv.count(zm.loot, "disinfectant") + Inv.count(zm.loot, "suture_kit") > 0: looted += 1
	ok(looted > 20, "they carry what their work gave them: %d of 60 medics had medical supplies" % looted)
	sim.zombies.list.clear()
	# feeding
	p.pos = Vector2(fx0 + 2.5, fy0 + 30.5)
	var fz2: Zombie = sim.zombies.spawn(Vector2(fx0 + 8.5, fy0 + 30.5), 0)
	fz2.dir = Vector2(-1, 0)
	var fcc: Chunk = w.chunk_at(floori(fz2.pos.x), floori(fz2.pos.y))
	fcc.corpses.append({"x": fz2.pos.x + 0.5, "y": fz2.pos.y, "d": 0, "l": [0, 0, 0, 0], "h": sim.hour})
	var sr2: float = sim.zombies.sight_range()
	ok(sim.zombies._sees_player(fz2, sr2), "(control) a standing one 6 tiles away sees you in daylight")
	var watch_from: Vector2 = p.pos
	p.pos = Vector2(-9999, -9999)            # it settles to feed while nobody is in sight
	for i_ia in range(40):
		if fz2.feeding: break
		fz2.state = Zombie.IDLE
		sim.zombies._think(fz2, sr2)
	p.pos = watch_from
	ok(fz2.feeding and not sim.zombies._sees_player(fz2, sr2), "one bent over a body does not look up at 6 tiles")
	sim.noises.clear()
	sim.noise(p.pos, 7.0)
	fz2.state = Zombie.IDLE
	sim.zombies._think(fz2, sr2)
	ok(fz2.feeding, "nor for a small noise")
	sim.noise(p.pos, 30.0)
	sim.zombies._think(fz2, sr2)
	ok(not fz2.feeding and fz2.state == Zombie.INVESTIGATE, "but a loud one gets its attention")
	sim.zombies.list.clear()
	sim.noises.clear()
	fcc.corpses.clear()
	# trapped
	var tz: Zombie = sim.zombies.spawn(Vector2(fx0 + 4.5, fy0 + 30.5), 0)
	tz.trapped = true
	tz.state = Zombie.CHASE
	tz.goal = p.pos
	tz.has_goal = true
	var tz0: Vector2 = tz.pos
	for i_ia in range(60): sim.zombies._update_z(tz, 1.0 / 30.0, sr2, true)
	ok(tz.pos.distance_to(tz0) < 0.01, "a trapped one reaches for you but cannot come")
	var spawned_trapped := 0
	sim.zombies.list.clear()
	# scent
	var sz: Zombie = sim.zombies.spawn(Vector2(fx0 + 3.5, fy0 + 30.5), 0)
	p.trail.clear()
	for k8 in range(8): p.trail.append([Vector2(fx0 + 4.5 + k8, fy0 + 33.5), sim.hour + k8 * 0.001])
	p.pos = Vector2(fx0 + 11.5, fy0 + 40.5)
	sz.state = Zombie.CHASE
	sz.alert = 0.1
	sz.give_up = 10.0
	sim.zombies._think(sz, sr2)
	ok(sz.scent and sz.has_goal and sz.goal.distance_to(sz.pos) < 5.1 and sz.goal.x > sz.pos.x, "losing sight of you, it follows your trail (goal %s)" % str(sz.goal))
	sim.weather["rain"] = 1.0
	w.chunk_at(floori(p.pos.x), floori(p.pos.y)).bld[World.idx(floori(p.pos.x), floori(p.pos.y))] = 0
	var t_before: int = p.trail.size()
	for i_ia in range(10):
		p._trail_t = 0.0
		p.update(0.05, Vector2.ZERO, false)
	sim.weather["rain"] = 0.0
	ok(p.trail.size() < t_before, "heavy rain washes the trail out (%d -> %d marks)" % [t_before, p.trail.size()])
	sim.zombies.list.clear()
	# stairs
	if st_plan != null:
		var lr2: Rect2i = st_lot["r"]
		var sx3: int = lr2.position.x + st_plan.stairs.x
		var sy3: int = lr2.position.y + st_plan.stairs.y
		p.pos = Vector2(sx3 + 0.5, sy3 + 0.5)
		w.stream(p.pos, 2, 999)
		sim._process_world_events()
		quiet(sim)
		var chaser: Zombie = sim.zombies.spawn(p.pos + Vector2(0.0, 0.0), 0)
		chaser.state = Zombie.CHASE
		for dd2 in [Vector2(1, 0), Vector2(-1, 0), Vector2(0, 1), Vector2(0, -1), Vector2(1, 1)]:
			if not w.blocked(p.pos.x + dd2.x * 2.0, p.pos.y + dd2.y * 2.0, 0.3):
				chaser.pos = p.pos + dd2 * 2.0
				break
		Actions._use_stairs(sim, World.UNDER * 2, "up")
		run(sim, 2.0)
		ok(World.level(chaser.pos.y) == 2 and sim.zombies.list.has(chaser), "it saw you take the stairs and comes up after you")
		var tt4 := 0.0
		while tt4 < 3.0:
			sim.tick(1.0 / 30.0)
			tt4 += 1.0 / 30.0
		ok(World.level(chaser.pos.y) == 2 and (chaser.state == Zombie.CHASE or chaser.state == Zombie.ATTACK or chaser.state == Zombie.INVESTIGATE), "and is hunting you upstairs (%s)" % Zombie.STATE_NAMES[chaser.state])
		sim.zombies.list.clear()
		p.pos = Vector2(sx3 + 0.5, sy3 + 0.5)
		w.stream(p.pos, 3, 999)
		sim._process_world_events()
		quiet(sim)
	# hiding
	p.pos = Vector2(fx0 + 2.5, fy0 + 30.5)
	w.stream(p.pos, 2, 999)
	sim._process_world_events()
	quiet(sim)
	bulldoze(sim, Rect2i(fx0, fy0 + 26, 12, 18))
	var hx2: int = fx0 + 3
	var hy2: int = fy0 + 30
	w.set_obj(hx2, hy2, Defs.ocell(Defs.O_WARDROBE, 0, 0))
	var ho: Callable = opt(Actions.options(sim, {"kind": "obj", "x": hx2, "y": hy2}), "Hide inside")
	ok(ho.is_valid(), "a wardrobe offers a place to hide")
	ho.call()
	run(sim, 1.5)
	ok(p.hidden, "you squeeze in")
	var hz: Zombie = sim.zombies.spawn(p.pos + Vector2(3.0, 0.0), 0)
	hz.dir = (p.pos - hz.pos).normalized()
	ok(not sim.zombies._sees_player(hz, sr2), "one passing three tiles away cannot see you")
	var hp0x: Vector2 = p.pos
	run(sim, 0.5, Vector2(1, 0))
	ok(p.pos.distance_to(hp0x) < 0.01, "you cannot walk while hidden")
	Actions.interact(sim)
	ok(not p.hidden, "USE brings you out")
	sim.zombies.list.clear()
	# peeking through a door
	w.set_wall(fx0 + 6, fy0 + 30, 1, Defs.wall(Defs.WM_PLASTER_CREAM, Defs.WS_DOOR))
	for yy4 in range(fy0 + 26, fy0 + 40):
		if yy4 != fy0 + 30: w.set_wall(fx0 + 6, yy4, 1, Defs.wall(Defs.WM_BRICK_RED, Defs.WS_SOLID))
	var behind_z: Zombie = sim.zombies.spawn(Vector2(fx0 + 8.5, fy0 + 30.5), 0)
	p.pos = Vector2(fx0 + 5.5, fy0 + 30.5)
	p.facing = Vector2(1, 0)
	sim.zombies._update_seen(behind_z, behind_z.pos.distance_squared_to(p.pos))
	ok(not behind_z.seen, "a closed door hides what is behind it")
	var pk: Callable = opt(Actions.options(sim, {"kind": "edge", "x": fx0 + 6, "y": fy0 + 30, "side": 1}), "Peek")
	ok(pk.is_valid(), "a closed door can be peeked through")
	sim.log.clear()
	pk.call()
	run(sim, 3.0)
	sim.zombies._update_seen(behind_z, behind_z.pos.distance_squared_to(p.pos))
	ok(behind_z.seen and sim.log.size() > 0 and String(sim.log[sim.log.size() - 1][0]).contains("1 of them"), "peeking shows it without opening the door")
	ok(w.edge_blocks(fx0 + 6, fy0 + 30, 1), "and the door is still shut")
	sim.zombies.list.clear()
	for yy5 in range(fy0 + 26, fy0 + 40): w.set_wall(fx0 + 6, yy5, 1, 0)
	# binoculars
	p.pos = Vector2(fx0 + 5.5, fy0 + 30.5)
	w.stream(p.pos + Vector2(0, 16), 3, 999)
	sim._process_world_events()
	quiet(sim)
	bulldoze(sim, Rect2i(fx0 + 3, fy0 + 30, 5, 34))
	var far_z: Zombie = sim.zombies.spawn(p.pos + Vector2(0.0, 30.0), 0)
	Inv.add_new(p.inv, "binoculars", 1)
	p.facing = Vector2(0, 1)
	sim.log.clear()
	Actions.use_binoculars(sim)
	run(sim, 3.5)
	var lens_msg: String = String(sim.log[sim.log.size() - 1][0]) if sim.log.size() > 0 else ""
	ok(far_z.peeked > 0.0 and lens_msg.begins_with("Through the lenses: infected"), "binoculars pick out an infected 30 tiles off (\"%s\")" % lens_msg)
	sim.zombies.list.clear()
	# footsteps
	p.gear.erase("feet")
	w.set_ground(floori(p.pos.x), floori(p.pos.y), Defs.G_CARPET_RED)
	var carpet_k: float = p.surface_noise()
	w.set_ground(floori(p.pos.x), floori(p.pos.y), Defs.G_GRAVEL)
	var gravel_k: float = p.surface_noise()
	Inv.add_new(p.inv, "boots", 1)
	p.equip(Inv.find(p.inv, "boots"))
	var boots_k: float = p.surface_noise()
	ok(carpet_k < 0.75 and gravel_k > 1.0 and boots_k > gravel_k, "footsteps: carpet x%.2f, gravel barefoot x%.2f, gravel in boots x%.2f" % [carpet_k, gravel_k, boots_k])
	ok(SaveGame.save(sim, slot), "saving roles and states")
	var rz: Zombie = sim.zombies.spawn(p.pos + Vector2(4, 4), 0)
	sim.zombies._apply_role(rz, "military")
	rz.trapped = true
	var rz_save: Array = rz.save()
	var rz2: Zombie = Zombie.from_save(rz_save)
	ok(rz2.role == "military" and rz2.trapped and absf(rz2.armor - 0.6) < 0.01, "role, armour and being trapped survive saving")
	sim.zombies.list.clear()

	print("== crops, seasons, fish stocks")
	sim.zombies.list.clear()
	bulldoze(sim, Rect2i(fx0, fy0 + 26, 12, 18))
	ok(Farming.GROW_HOURS.size() >= 12, "%d crops can be grown" % Farming.GROW_HOURS.size())
	var all_ok := true
	for crop in Farming.GROW_HOURS.keys():
		if Items.def("seeds_" + crop).is_empty() or Items.def(crop).is_empty() or Defs.obj(int(Farming.CROP_OBJ[crop])).get("crop", "") != crop:
			all_ok = false
			print("    missing piece for ", crop)
		for st3 in range(5):
			if Art.obj_spr.get(Defs.ocell(int(Farming.CROP_OBJ[crop]), 0, st3), -1) < 0 and Engine.has_singleton("never"):
				all_ok = false
	ok(all_ok, "every crop has seeds, produce and a plant")
	var bx3: int = fx0 + 3
	var by3: int = fy0 + 30
	var cch3: Chunk = w.chunk_at(bx3, by3)
	var plant := func(crop: String, x: int, y: int) -> Dictionary:
		w.set_ground(x, y, Defs.G_SOIL)
		w.chunk_at(x, y).bld[World.idx(x, y)] = 0
		w.set_obj(x, y, Defs.ocell(int(Farming.CROP_OBJ[crop]), 0, 0))
		var e3: Dictionary = {"k": "crop", "t": crop, "s": 0, "g": 0.0, "w": 60.0}
		w.set_ent(x, y, e3)
		return e3
	# a cool spring day: lettuce grows, corn waits
	sim.weather["temp"] = 6.0
	sim.weather["rain"] = 0.0
	var let_e: Dictionary = plant.call("lettuce", bx3, by3)
	var corn_e: Dictionary = plant.call("corn", bx3 + 2, by3)
	for i_b in range(20):
		let_e["w"] = 60.0
		corn_e["w"] = 60.0
		sim._sim_ents(cch3, 1.0, false)
	ok(float(let_e["g"]) > 15.0 and float(corn_e["g"]) < 1.0, "at 6 degrees lettuce grows (%.0f h) and corn does not (%.0f h)" % [float(let_e["g"]), float(corn_e["g"])])
	# frost kills tender plants, not hardy ones
	var on_e: Dictionary = plant.call("onion", bx3 + 4, by3)
	sim.weather["temp"] = -3.0
	for i_b in range(30):
		corn_e["w"] = 60.0
		on_e["w"] = 60.0
		sim._sim_ents(cch3, 1.0, false)
	ok(int(corn_e["s"]) == 4 and int(on_e["s"]) != 4, "a hard frost withers the corn and spares the onions")
	sim.weather["temp"] = 15.0
	# lettuce rots in sodden ground sooner than potatoes
	var wet_l := 0
	var wet_p := 0
	for trial in range(60):
		var le2: Dictionary = {"k": "crop", "t": "lettuce", "s": 0, "g": 0.0, "w": 80.0}
		var pe2: Dictionary = {"k": "crop", "t": "potato", "s": 0, "g": 0.0, "w": 80.0}
		w.set_obj(bx3, by3 + 2, Defs.ocell(int(Farming.CROP_OBJ["lettuce"]), 0, 0))
		w.set_ent(bx3, by3 + 2, le2)
		w.set_obj(bx3 + 2, by3 + 2, Defs.ocell(int(Farming.CROP_OBJ["potato"]), 0, 0))
		w.set_ent(bx3 + 2, by3 + 2, pe2)
		for i_c in range(10):
			le2["w"] = 80.0
			pe2["w"] = 80.0
			sim._sim_ents(cch3, 1.0, false)
		if le2.get("ill", 0) == 1: wet_l += 1
		if pe2.get("ill", 0) == 1: wet_p += 1
	ok(wet_l > 0 and wet_p == 0, "kept at 80%% water, lettuce gets mildew (%d of 60) and potatoes do not (%d)" % [wet_l, wet_p])
	# harvest a new crop and cook with it
	w.set_ent(bx3, by3, {})
	var ripe: Dictionary = plant.call("wheat", bx3, by3)
	ripe["s"] = 3
	ripe["g"] = 999.0
	w.set_obj(bx3, by3, Defs.ocell(int(Farming.CROP_OBJ["wheat"]), 0, 3))
	p.pos = Vector2(bx3 - 0.5, by3 + 0.5)
	var wheat0: int = Inv.count(p.inv, "wheat")
	opt(Actions.options(sim, {"kind": "obj", "x": bx3, "y": by3}), "Harvest").call()
	run(sim, 3.5)
	ok(Inv.count(p.inv, "wheat") >= wheat0 + 3, "wheat can be harvested (%d)" % (Inv.count(p.inv, "wheat") - wheat0))
	Inv.add_new(p.inv, "wheat", 6)
	Inv.add_new(p.inv, "stone", 1)
	Actions.craft(sim, Recipes.by_id("grind_flour"))
	run(sim, 9.0)
	Actions.craft(sim, Recipes.by_id("grind_flour"))
	run(sim, 9.0)
	ok(Inv.count(p.inv, "flour") >= 2 and Inv.count(p.inv, "stone") >= 1, "ground into flour, the stone kept")
	Inv.add_new(p.inv, "water_bottle", 1)
	var fire_x2: int = bx3 + 1
	w.set_obj(fire_x2, by3 + 4, Defs.ocell(Defs.O_CAMPFIRE, 0, 0))
	w.set_ent(fire_x2, by3 + 4, {"k": "fire", "fuel": 10.0, "lit": true})
	p.pos = Vector2(fire_x2 + 0.5, by3 + 3.5)
	sim._slow_tick(0.01)
	ok(Actions.craft(sim, Recipes.by_id("bake_bread")), "and baked into bread over a fire")
	run(sim, 11.0)
	ok(Inv.count(p.inv, "bread") >= 1, "bread (%d)" % Inv.count(p.inv, "bread"))
	w.remove_object(fire_x2, by3 + 4)
	# fish stocks
	sim.fish.clear()
	var fx9: int = fx0 + 100
	var fy9: int = fy0 + 100
	ok(absf(sim.fish_stock(fx9, fy9) - 1.0) < 0.001, "untouched water is full of fish")
	for k9 in range(6): sim.take_fish(fx9, fy9)
	var after6: float = sim.fish_stock(fx9, fy9)
	ok(after6 < 0.35, "six fish from one spot and it is fished out (%.2f)" % after6)
	sim.hour += 24.0 * 10.0
	ok(sim.fish_stock(fx9, fy9) > after6 + 0.25, "ten days later it has partly recovered (%.2f)" % sim.fish_stock(fx9, fy9))
	# seasons for animals
	sim.weather["temp"] = 15.0
	var summer := 0
	var winter := 0
	for k10 in range(40):
		var chs := Chunk.new(5000 + k10, 3000)
		chs.zone = 0
		for i10 in range(256): chs.ground[i10] = Defs.G_GRASS
		var n0s: int = sim.animals.list.size()
		sim.animals.on_chunk_loaded(chs, true)
		summer += sim.animals.list.size() - n0s
	sim.weather["temp"] = -5.0
	for k11 in range(40):
		var chw := Chunk.new(5000 + k11, 3000)
		chw.zone = 0
		for i11 in range(256): chw.ground[i11] = Defs.G_GRASS
		var n0w: int = sim.animals.list.size()
		sim.animals.on_chunk_loaded(chw, true)
		winter += sim.animals.list.size() - n0w
	sim.weather["temp"] = 15.0
	sim.animals.list.clear()
	ok(winter < summer, "the same woods hold fewer animals in winter (%d vs %d)" % [winter, summer])

	print("== weather hazards: snow, ice, storms, fallen trees, floods, smoke")
	sim.zombies.list.clear()
	bulldoze(sim, Rect2i(fx0, fy0 + 26, 12, 18))
	p.pos = Vector2(fx0 + 5.5, fy0 + 30.5)
	w.chunk_at(floori(p.pos.x), floori(p.pos.y)).bld[World.idx(floori(p.pos.x), floori(p.pos.y))] = 0
	p.bld = 0
	sim.snow_cover = 0.0
	sim.weather["temp"] = -4.0
	sim.weather["rain"] = 0.8
	sim.weather["snow"] = 0.8
	for i_w in range(10): sim._weather_hazards(1.0)
	ok(sim.snow_cover > 0.5, "snow settles while it falls (%.2f)" % sim.snow_cover)
	var sf_snow: float = p.speed_factor()
	ok(sf_snow < 0.9, "deep snow slows you (x%.2f)" % sf_snow)
	ok(sim.icy(floori(p.pos.x), floori(p.pos.y)), "and below freezing the ground is treacherous")
	sim.settings["god"] = false
	p.hp = 100.0
	var slipped := false
	for i_w in range(300):
		p._step_t = 0.0
		p.update(1.0 / 30.0, Vector2(1, 0), true)
		if p.slow_t > 0.5:
			slipped = true
			break
		if i_w % 40 == 39: p.pos = Vector2(fx0 + 2.5, fy0 + 30.5)
	sim.settings["god"] = true
	ok(slipped, "running on ice, you go down sooner or later")
	sim.weather["temp"] = 10.0
	sim.weather["snow"] = 0.0
	sim.weather["rain"] = 0.0
	for i_w in range(20): sim._weather_hazards(1.0)
	ok(sim.snow_cover < 0.3 and not sim.icy(floori(p.pos.x), floori(p.pos.y)), "a thaw melts it (%.2f)" % sim.snow_cover)
	sim.snow_cover = 0.0
	p.hp = 100.0
	p.wounds.clear()
	p.slow_t = 0.0
	# storms: a stand of trees around you, then a few hundred gusts and strikes
	bulldoze(sim, Rect2i(fx0, fy0, 12, 44))
	for yy11 in range(fy0 + 1, fy0 + 43, 3):
		for xx11 in range(fx0 + 1, fx0 + 11, 3):
			w.set_obj(xx11, yy11, Defs.ocell(Defs.O_TREE_OAK, 0, 0))
	p.pos = Vector2(fx0 + 5.5, fy0 + 20.5)
	var fell := false
	var struck := false
	sim.rng.seed = 4242
	for k12 in range(600):
		sim._storm_event()
		if not sim.burning.is_empty():
			struck = true
			sim.burning.clear()
			sim.fires.clear()
		if struck and fell: break
		for yy12 in range(fy0, fy0 + 44):
			for xx12 in range(fx0, fx0 + 12):
				if Defs.o_id(w.obj(xx12, yy12)) == Defs.O_FALLEN_TREE: fell = true
	ok(struck, "lightning can set a tree alight")
	ok(fell, "and a storm can blow one down across the ground beside it")
	ok(sim.lightning > 0.0, "a strike lights the sky")
	var fa2 := Vector2i(-1, -1)
	for yy13 in range(fy0, fy0 + 44):
		for xx13 in range(fx0, fx0 + 12):
			if fa2.x < 0 and Defs.o_id(w.obj(xx13, yy13)) == Defs.O_FALLEN_TREE:
				fa2 = w.anchor_of(xx13, yy13)
	ok(fa2.x >= 0 and w.tile_blocked(fa2.x, fa2.y) and w.tile_blocked(fa2.x + 1, fa2.y), "a fallen tree blocks the way")
	if fa2.x >= 0:
		p.pos = Vector2(fa2.x + 0.5, fa2.y - 0.5)
		if w.blocked(p.pos.x, p.pos.y, Player.R): p.pos = Vector2(fa2.x + 0.5, fa2.y + 1.5)
		Inv.add_new(p.inv, "axe", 1)
		var logs0: int = Inv.count(p.inv, "log")
		var co9: Array = Actions.options(sim, {"kind": "obj", "x": fa2.x, "y": fa2.y})
		opt(co9, "Cut it up").call()
		run(sim, 20.0)
		ok(w.obj(fa2.x, fa2.y) == 0 and Inv.count(p.inv, "log") == logs0 + 2, "an axe clears it and gives you the wood")
	bulldoze(sim, Rect2i(fx0, fy0, 12, 44))
	# floods
	sim.flooded.clear()
	var wx2: int = fx0 + 9
	for yy7 in range(fy0 + 28, fy0 + 40):
		w.set_ground(wx2, yy7, Defs.G_WATER)
		w.set_ground(wx2 - 1, yy7, Defs.G_ASPHALT)
		w.chunk_at(wx2 - 1, yy7).bld[World.idx(wx2 - 1, yy7)] = 0
	p.pos = Vector2(fx0 + 5.5, fy0 + 33.5)
	sim._wet_h = 10.0
	sim.weather["rain"] = 1.0
	var road_wet := false
	for i_w in range(400):
		sim._flood_step()
		for yy8 in range(fy0 + 28, fy0 + 40):
			if sim.flooded.has(Vector2i(wx2 - 1, yy8)): road_wet = true
		if road_wet: break
	ok(sim.flooded.size() > 0 and road_wet, "a long downpour floods the road beside the river (%d tiles)" % sim.flooded.size())
	var flood_t: Vector2i = Vector2i(-1, -1)
	for k13 in sim.flooded.keys():
		if k13.x == wx2 - 1: flood_t = k13
	ok(flood_t.x >= 0 and Defs.ground_is_water(w.ground(flood_t.x, flood_t.y)), "the water is really there")
	ok(SaveGame.save(sim, slot), "saving mid-flood")
	s2 = SaveGame.load_game(slot)
	ok(s2 != null and s2.flooded.size() == sim.flooded.size(), "floods persist")
	sim._wet_h = 0.0
	sim.weather["rain"] = 0.0
	for i_w in range(500):
		if sim.flooded.is_empty(): break
		sim._recede_step()
	ok(sim.flooded.is_empty() and w.ground(flood_t.x, flood_t.y) == Defs.G_ASPHALT, "and recede, giving the road back")
	# smoke
	var room_b: int = 777001
	for yy9 in range(fy0 + 28, fy0 + 33):
		for xx9 in range(fx0 + 1, fx0 + 6):
			w.chunk_at(xx9, yy9).bld[World.idx(xx9, yy9)] = room_b
			w.set_ground(xx9, yy9, Defs.G_WOOD)
	p.pos = Vector2(fx0 + 1.5, fy0 + 28.5)
	p.bld = room_b
	sim.burning[Vector2i(fx0 + 5, fy0 + 32)] = 50.0
	sim.settings["god"] = false
	p.hp = 100.0
	for i_w in range(5):
		sim._smoke_t = 0.0
		sim._tick_smoke(1.0)
	sim.settings["god"] = true
	ok(p.hp < 100.0, "smoke from a fire in the same room hurts (%.0f hp)" % p.hp)
	sim.burning.clear()
	for yy9 in range(fy0 + 28, fy0 + 33):
		for xx9 in range(fx0 + 1, fx0 + 6):
			w.chunk_at(xx9, yy9).bld[World.idx(xx9, yy9)] = 0
	p.hp = 100.0

	print("== your shelter: recruits, jobs, stores, time away; traders")
	sim.zombies.list.clear()
	sim.npcs.list.clear()
	sim.animals.list.clear()
	bulldoze(sim, Rect2i(fx0, fy0, 12, 44))
	var hb2: int = 888001
	for yy14 in range(fy0 + 20, fy0 + 30):
		for xx14 in range(fx0 + 1, fx0 + 11):
			w.chunk_at(xx14, yy14).bld[World.idx(xx14, yy14)] = hb2
			w.set_ground(xx14, yy14, Defs.G_WOOD)
	w.set_obj(fx0 + 2, fy0 + 21, Defs.ocell(Defs.O_BED, 0, 0))
	w.set_obj(fx0 + 2, fy0 + 22, Defs.ocell(Defs.O_BED, 0, 1))
	w.set_obj(fx0 + 8, fy0 + 21, Defs.ocell(Defs.O_WOOD_CRATE, 0, 0))
	var store: Array = w.container_at(fx0 + 8, fy0 + 21)
	store.clear()
	for k14 in range(4): Inv.add_new(store, "canned_beans", 1, sim.hour)
	p.pos = Vector2(fx0 + 3.5, fy0 + 22.5)
	sim.home = {}
	var mk: Callable = opt(Actions.options(sim, {"kind": "obj", "x": fx0 + 2, "y": fy0 + 21}), "Make this place your shelter")
	ok(mk.is_valid(), "a bed offers to make the place your shelter")
	mk.call()
	ok(not sim.home.is_empty() and int(sim.home["b"]) == hb2, "it is now home")
	ok(sim.home_stores().size() == 1, "and its crate counts as the shelter's stores")
	# a companion moves in
	var rec = sim.npcs.spawn(p.pos + Vector2(1.0, 0.0), false)
	rec.state = NpcSim.FOLLOW
	rec.job = "guard"
	rec.trust = 40.0
	rec.stock = []
	var mv: Callable = opt(sim.npcs.options(rec), "\"Come and live")
	ok(mv.is_valid(), "a companion can be asked to live there")
	mv.call()
	ok(not rec.recruit, "not before they trust you")
	rec.trust = 70.0
	opt(sim.npcs.options(rec), "\"Come and live").call()
	ok(rec.recruit and rec.state == NpcSim.STAY and rec.work == "guard" and rec.home.distance_to(sim.home_pos()) < 3.0, "with trust they move in and take up their old trade (%s)" % rec.work)
	# they eat from the stores, physically
	rec.hunger = 80.0
	sim.npcs._needs(rec, 0.01)
	ok(rec.hunger < 50.0 and Inv.count(store, "canned_beans") == 3, "a hungry recruit eats a tin from the stores (3 left)")
	# jobs
	opt(sim.npcs.options(rec), "Ask them to tend the crops").call()
	ok(rec.work == "farm", "you can give them another job")
	var cpx: int = fx0 + 6
	var cpy: int = fy0 + 30
	w.set_ground(cpx, cpy, Defs.G_SOIL)
	w.set_obj(cpx, cpy, Defs.ocell(int(Farming.CROP_OBJ["potato"]), 0, 1))
	w.set_ent(cpx, cpy, {"k": "crop", "t": "potato", "s": 1, "g": 30.0, "w": 10.0})
	w.set_ground(cpx + 2, cpy, Defs.G_SOIL)
	w.set_obj(cpx + 2, cpy, Defs.ocell(int(Farming.CROP_OBJ["carrot"]), 0, 3))
	w.set_ent(cpx + 2, cpy, {"k": "crop", "t": "carrot", "s": 3, "g": 999.0, "w": 40.0})
	sim.hour = floorf(sim.hour / 24.0) * 24.0 + 24.0 + 10.0
	for k15 in range(12):
		rec._work_t = 0.0
		sim.npcs._work(rec, 0.1)
	ok(float(w.ent(cpx, cpy)["w"]) > 50.0, "a farmer waters dry plants")
	ok(Inv.count(store, "carrot") >= 2 and int(w.ent(cpx + 2, cpy)["s"]) == 0, "and harvests ripe ones into the stores, sowing again (%d carrots)" % Inv.count(store, "carrot"))
	# scavenging trip
	rec.work = "scavenge"
	rec.leave_h = -100.0
	rec.wpn = "crowbar"
	sim.npcs._work(rec, 0.1)
	ok(rec.away_until > sim.hour, "a scavenger heads out in the morning")
	ok(sim.npcs.nearest(rec.pos, 3.0) == null, "and is not around while gone")
	var items_before: int = store.size()
	var beans_before: int = Inv.count(store, "canned_beans")
	sim.hour = rec.away_until + 0.1
	seed(3)
	sim.npcs.update(1.0 / 30.0, 0.0)
	ok(rec.away_until == 0.0 and (not sim.npcs.list.has(rec) or store.size() > items_before or Inv.count(store, "canned_beans") > beans_before), "and comes back with something for the stores — or does not come back")
	if not sim.npcs.list.has(rec):
		rec = sim.npcs.spawn(p.pos + Vector2(1.0, 0.0), false)
		rec.trust = 80.0
		sim.npcs.recruit_to_home(rec)
	# nursing
	rec.work = "nurse"
	rec.pos = p.pos + Vector2(1.0, 0.0)
	Inv.add_new(store, "bandage", 1)
	var band0: int = Inv.count(store, "bandage")
	p.wounds.clear()
	p.add_wound(9, "laceration", "test")
	rec._work_t = 0.0
	sim.npcs._work(rec, 0.1)
	ok(p.wounds[0]["band"] and Inv.count(store, "bandage") == band0 - 1, "a nurse dresses your bleeding wound from the stores")
	p.wounds.clear()
	# cook
	rec.work = "cook"
	Inv.add_new(store, "raw_venison", 1, sim.hour)
	w.set_obj(fx0 + 5, fy0 + 25, Defs.ocell(Defs.O_CAMPFIRE, 0, 0))
	w.set_ent(fx0 + 5, fy0 + 25, {"k": "fire", "fuel": 10.0, "lit": true})
	sim._slow_tick(0.01)
	rec.pos = Vector2(fx0 + 5.5, fy0 + 24.5)
	rec._work_t = 0.0
	sim.npcs._work(rec, 0.1)
	ok(Inv.count(store, "raw_venison") == 0 and Inv.count(store, "cooked_venison") == 1, "a cook turns raw food in the stores into a meal")
	w.remove_object(fx0 + 5, fy0 + 25)
	# time away
	rec.work = "guard"
	store.clear()
	Inv.add_new(store, "canned_beans", 6, sim.hour)
	rec.hunger = 10.0
	sim.npcs._catch_up_recruit(rec, 48.0)
	ok(Inv.count(store, "canned_beans") < 6 and rec.hunger < 60.0, "while you are away for two days they eat from the stores (%d tins left)" % Inv.count(store, "canned_beans"))
	store.clear()
	rec.hunger = 10.0
	sim.npcs._catch_up_recruit(rec, 72.0)
	ok(rec.hunger >= 90.0, "with nothing in the stores they go hungry")
	rec.trust = 10.0
	rec.hp = 40.0
	sim.npcs._needs(rec, 1.0)
	ok(not rec.recruit, "and in the end they leave")
	# guard warns
	rec.recruit = true
	rec.work = "guard"
	rec.trust = 80.0
	rec.hunger = 10.0
	var gz: Zombie = sim.zombies.spawn(sim.home_pos() + Vector2(5.0, 0.0), 0)
	sim.log.clear()
	rec._work_t = 0.0
	sim.npcs._work(rec, 0.1)
	ok(sim.log.size() > 0 and String(sim.log[sim.log.size() - 1][0]).contains("Coming in from the"), "a guard calls out when something comes near the shelter")
	sim.zombies.list.clear()
	ok(SaveGame.save(sim, slot), "saving the shelter")
	s2 = SaveGame.load_game(slot)
	var rec_back := false
	if s2 != null:
		for n5 in s2.npcs.list:
			if n5.recruit and n5.work == "guard": rec_back = true
	ok(s2 != null and int(s2.home.get("b", 0)) == hb2 and rec_back, "your shelter and the people in it persist")
	sim.npcs.list.clear()
	# traders
	p.pos = Vector2(fx0 + 5.5, fy0 + 10.5)
	w.stream(p.pos, 3, 999)
	sim._process_world_events()
	quiet(sim)
	sim.npcs.send_trader()
	var tr2 = null
	for n6 in sim.npcs.list:
		if n6.trader: tr2 = n6
	ok(tr2 != null and tr2.stock.size() == 8, "a trader arrives with a loaded cart")
	if tr2 != null:
		var to0: float = tr2.pos.distance_to(p.pos)
		for k16 in range(300): sim.npcs.update(1.0 / 30.0, 0.0)
		ok(tr2.pos.distance_to(p.pos) < to0 - 3.0, "and walks toward you")
		Inv.add_new(p.inv, "hammer", 1)
		var tr_opt: Callable = Callable()
		for o in sim.npcs.options(tr2):
			if String(o["label"]).begins_with("Trade your"): tr_opt = o["fn"]
		ok(tr_opt.is_valid(), "they will trade without needing to know you")
		sim.hour = tr2.leave_h + 1.0
		for k17 in range(900):
			sim.npcs.update(1.0 / 30.0, 0.0)
			if not sim.npcs.list.has(tr2): break
		ok(not sim.npcs.list.has(tr2), "and after a few hours they move on")
	sim.npcs.list.clear()
	sim.home = {}
	bulldoze(sim, Rect2i(fx0, fy0, 12, 44))
	for yy15 in range(fy0 + 20, fy0 + 30):
		for xx15 in range(fx0 + 1, fx0 + 11):
			w.chunk_at(xx15, yy15).bld[World.idx(xx15, yy15)] = 0

	print("== interface and documents: choosing a target, inspecting, names, diaries, bulletins, maps, radio, teaching")
	sim.zombies.list.clear()
	sim.npcs.list.clear()
	bulldoze(sim, Rect2i(fx0, fy0 + 26, 12, 18))
	p.pos = Vector2(fx0 + 5.5, fy0 + 30.5)
	p.facing = Vector2(1, 0)
	w.set_obj(fx0 + 6, fy0 + 30, Defs.ocell(Defs.O_WARDROBE, 0, 0))
	w.set_obj(fx0 + 5, fy0 + 31, Defs.ocell(Defs.O_CRATE, 0, 0))
	w.chunk_at(fx0 + 5, fy0 + 31).containers[World.idx(fx0 + 5, fy0 + 31)] = []
	cch3 = w.chunk_at(floori(p.pos.x), floori(p.pos.y))
	cch3.corpses.append({"x": p.pos.x - 0.6, "y": p.pos.y, "d": 0, "l": [0, 0, 0, 0], "h": sim.hour, "perm": 1})
	sim.ui_events.clear()
	Actions.interact(sim, true)
	var first_menu: Dictionary = sim.ui_events[0] if sim.ui_events.size() > 0 else {}
	ok(first_menu.get("title", "") == "What do you want to use?" and first_menu["options"].size() >= 3, "holding USE among several things asks which one (%d choices)" % (first_menu.get("options", []) as Array).size())
	if not first_menu.is_empty():
		var lbls2: Array = []
		for o in first_menu["options"]: lbls2.append(o["label"])
		ok(lbls2.any(func(l): return String(l).begins_with("Corpse")) and lbls2.any(func(l): return String(l).begins_with("Wardrobe")) and lbls2.any(func(l): return String(l).begins_with("Crate")), "listing each one (%s)" % str(lbls2))
		sim.ui_events.clear()
		for o in first_menu["options"]:
			if String(o["label"]).begins_with("Crate"): (o["fn"] as Callable).call()
		ok(sim.ui_events.size() == 1 and String(sim.ui_events[0]["title"]) == "Crate", "choosing one shows its options")
	sim.ui_events.clear()
	cch3.corpses.clear()
	w.remove_object(fx0 + 6, fy0 + 30)
	w.remove_object(fx0 + 5, fy0 + 31)
	# inspect
	var kn2: Dictionary = Items.make("kitchen_knife", 1)
	kn2["c"] = 0.5
	var insp: String = Items.inspect_text(kn2, sim.hour)
	ok(insp.contains("condition 50%") and insp.contains("damage") and insp.contains("kg"), "inspecting an item tells you its weight, condition and what it does (\"%s\")" % insp)
	# name
	var named := Sim.new(777)
	named.settings["pname"] = "Ada Kowal"
	named.new_game("unemployed", [], "house")
	ok(named.player.pname == "Ada Kowal", "the survivor has the name you gave them")
	ok(SaveGame.save(named, slot), "saving a named survivor")
	var nl2: Sim = SaveGame.load_game(slot)
	ok(nl2 != null and nl2.player.pname == "Ada Kowal", "the name persists")
	ok(SaveGame.save(sim, slot), "(restoring the main test save)")
	# documents
	p.markers.clear()
	var bul: Dictionary = Items.make("bulletin", 1, sim.hour)
	sim.pending_sites.clear()
	sim.read_note(bul)
	ok(String(bul.get("txt", "")).begins_with("EMERGENCY BULLETIN") and p.markers.size() == 1, "an emergency bulletin names a place and marks it")
	var bsite := Vector2i(int(bul["mx"]), int(bul["my"]))
	ok(sim.pending_sites.has(bsite), "what is really there was decided when it was printed")
	var outcome: String = sim.pending_sites[bsite]
	var zbefore: int = sim.zombies.list.size()
	var fake := Chunk.new(bsite.x >> 4, bsite.y >> 4)
	w.stream(Vector2(bsite.x + 0.5, bsite.y + 0.5), 1, 999)
	sim._process_world_events()
	ok(not sim.pending_sites.has(bsite), "reaching the place settles it")
	var crates := 0
	for dd5 in [Vector2i(0, 0), Vector2i(2, 0), Vector2i(0, 2), Vector2i(2, 2), Vector2i(-2, 0)]:
		if Defs.o_id(w.obj(bsite.x + dd5.x, bsite.y + dd5.y)) == Defs.O_CRATE: crates += 1
	var zthere := 0
	for zq in sim.zombies.list:
		if zq.pos.distance_to(Vector2(bsite)) < 6.0: zthere += 1
	ok((outcome == "supply" and crates > 0) or (outcome == "overrun" and zthere >= 5), "it was %s (%d crates, %d infected nearby)" % [outcome, crates, zthere])
	var supplies_seen := false
	var overrun_seen := false
	for k18 in range(40):
		sim.hour += 1.3
		var b2: Dictionary = Items.make("bulletin", 1, sim.hour)
		sim._fill_document(b2)
		var st4 = sim.pending_sites.get(Vector2i(int(b2["mx"]), int(b2["my"])), "")
		if st4 == "supply": supplies_seen = true
		if st4 == "overrun": overrun_seen = true
	ok(supplies_seen and overrun_seen, "some bulletins still hold true and some are out of date")
	sim.pending_sites.clear()
	p.pos = Vector2(fx0 + 5.5, fy0 + 30.5)
	w.stream(p.pos, 3, 999)
	sim._process_world_events()
	quiet(sim)
	var known0: int = w.explored.size()
	var lm: Dictionary = Items.make("local_map", 1, sim.hour)
	sim.read_note(lm)
	ok(w.explored.size() > known0 + 50, "a local map fills in the streets around you (%d -> %d blocks)" % [known0, w.explored.size()])
	var dia: Dictionary = Items.make("diary", 1, sim.hour)
	sim.read_note(dia)
	ok(String(dia.get("txt", "")).begins_with("Someone's diary."), "a diary has entries in it")
	# radio
	sim.log.clear()
	sim.factions.sites.clear()
	sim.factions.found(Vector2i(70, 70), Vector2i(fx0 + 60, fy0 + 60), 0, 4)
	var heard_sett := false
	var forecast := false
	for k19 in range(12):
		sim.log.clear()
		sim.radio_report()
		for ln in sim.log:
			if String(ln[0]).begins_with("\"Tomorrow:"): forecast = true
			if String(ln[0]).contains("we have walls"): heard_sett = true
	ok(forecast, "the radio gives tomorrow's weather")
	ok(heard_sett, "and sometimes a settlement calling out on the frequency")
	sim.factions.sites.clear()
	# teaching
	var tch = sim.npcs.spawn(p.pos + Vector2(1.0, 0.0), false)
	tch.job = "medic"
	tch.trust = 60.0
	var fa0: float = p.skills["first_aid"]
	var tc: Callable = opt(sim.npcs.options(tch), "\"Teach me")
	ok(tc.is_valid(), "a survivor who trusts you offers to teach their trade")
	if tc.is_valid():
		tc.call()
		var dur_t: float = float(p.action.get("dur", 20.0))
		run(sim, dur_t + 1.0)
		ok(float(p.skills["first_aid"]) > fa0 + 100.0, "you learn from them (first aid +%.0f xp)" % (float(p.skills["first_aid"]) - fa0))
		ok(not opt(sim.npcs.options(tch), "\"Teach me").is_valid(), "once")
	sim.npcs.list.clear()

	print("== bulk and wet things")
	var inv_keep: Array = p.inv.duplicate()
	var bag_keep: Dictionary = p.bag
	p.inv.clear()
	p.bag = {}
	ok(Items.vol(Items.make("plank", 1)) > Items.vol(Items.make("nails", 50)), "a plank takes more room than fifty nails")
	Inv.add_new(p.inv, "plank", 6)
	var cap_v: float = p.vol_capacity()
	ok(p.over_volume() > 0.0 and p.carried() < p.capacity(), "six planks are light enough but too bulky for pockets (%.0f bulk of %.0f)" % [Inv.volume(p.inv), cap_v])
	var sf_bulk: float = p.speed_factor()
	Inv.add_new(p.inv, "backpack", 1)
	p.bag = Inv.find(p.inv, "backpack")
	ok(p.vol_capacity() > cap_v + 20.0 and p.over_volume() == 0.0 and p.speed_factor() > sf_bulk, "a backpack makes room for them (speed x%.2f -> x%.2f)" % [sf_bulk, p.speed_factor()])
	# rain
	p.bag = {}
	p.inv.clear()
	Inv.add_new(p.inv, "matches", 1)
	Inv.add_new(p.inv, "novel", 1)
	var flour: Dictionary = Items.make("flour", 1, sim.hour)
	p.inv.append(flour)
	var t_fl: float = flour["t"]
	p.pos = Vector2(fx0 + 5.5, fy0 + 30.5)
	w.chunk_at(floori(p.pos.x), floori(p.pos.y)).bld[World.idx(floori(p.pos.x), floori(p.pos.y))] = 0
	p.bld = 0
	sim.weather["rain"] = 1.0
	for i_x in range(30): p._soak_items(0.2)
	var m3: Dictionary = Inv.find(p.inv, "matches")
	ok(float(m3.get("wet", 0.0)) > 0.0 and float(Inv.find(p.inv, "novel").get("wet", 0.0)) > 0.0, "out in the rain without a bag, paper and matches get soaked")
	ok(not Inv.has_tag(p.inv, "fire"), "soaked matches will not strike")
	ok(float(flour["t"]) < t_fl, "and wet flour starts to spoil")
	sim.log.clear()
	p.read_item(Inv.find(p.inv, "novel"))
	ok(p.action.is_empty() and sim.log.size() > 0 and String(sim.log[sim.log.size() - 1][0]).contains("soaked"), "a soaked book cannot be read")
	# a bag keeps most of it dry
	for it6 in p.inv: it6.erase("wet")
	Inv.add_new(p.inv, "backpack", 1)
	p.bag = Inv.find(p.inv, "backpack")
	var soaked_bag := 0
	for trial2 in range(20):
		for it7 in p.inv: it7.erase("wet")
		for i_x in range(5): p._soak_items(0.2)
		if float(Inv.find(p.inv, "matches").get("wet", 0.0)) > 0.0: soaked_bag += 1
	ok(soaked_bag < 15, "in a bag they mostly stay dry (%d of 20 soaked)" % soaked_bag)
	# drying out
	sim.weather["rain"] = 0.0
	Inv.find(p.inv, "matches")["wet"] = 6.0
	var dfx: int = floori(p.pos.x) + 1
	w.set_obj(dfx, floori(p.pos.y), Defs.ocell(Defs.O_CAMPFIRE, 0, 0))
	w.set_ent(dfx, floori(p.pos.y), {"k": "fire", "fuel": 10.0, "lit": true})
	sim._slow_tick(0.01)
	for i_x in range(10): p._soak_items(0.2)
	ok(not Inv.find(p.inv, "matches").has("wet") and Inv.has_tag(p.inv, "fire"), "by a fire they dry out and strike again")
	w.remove_object(dfx, floori(p.pos.y))
	p.inv = inv_keep
	p.bag = bag_keep if inv_keep.has(bag_keep) else {}

	print("== big vehicles, sirens, mufflers, passengers")
	sim.zombies.list.clear()
	sim.npcs.list.clear()
	bulldoze(sim, Rect2i(fx0, fy0, 12, 44))
	for yy16 in range(fy0, fy0 + 44):
		for xx16 in range(fx0, fx0 + 12):
			w.set_ground(xx16, yy16, Defs.G_ASPHALT)
	var place_v := func(vt: int, ax: int, ay: int) -> Dictionary:
		var fsv: Vector2i = Defs.obj_size(vt, 0)
		for jj in range(fsv.y):
			for ii in range(fsv.x):
				w.set_obj(ax + ii, ay + jj, Defs.ocell(vt, 0, jj * fsv.x + ii))
		var e7: Dictionary = Vehicle.car_ent(sim, ax, ay)
		e7["key"] = 1; e7["bat"] = 1; e7["eng"] = 1.0; e7["tire"] = 1.0; e7["fuel"] = Vehicle.tank_of(vt); e7["muf"] = 1
		return e7
	var vx2: int = fx0 + 5
	var vy2: int = fy0 + 2
	for vt2 in [Defs.O_TRUCK, Defs.O_BUS, Defs.O_AMBULANCE, Defs.O_POLICE_CAR]:
		place_v.call(vt2, vx2, vy2)
		p.pos = Vector2(vx2 - 0.5, vy2 + 1.5)
		var go2: Callable = opt(Actions._car_options(sim, vx2, vy2), "Drive")
		ok(go2.is_valid(), "a %s can be driven" % Defs.obj(vt2)["n"].to_lower())
		go2.call()
		ok(sim.vehicle != null and sim.vehicle.oid == vt2 and sim.vehicle.size() == Vector2(Defs.obj_size(vt2, 0)), "(it is %dx%d)" % [Defs.obj_size(vt2, 0).x, Defs.obj_size(vt2, 0).y])
		run(sim, 1.5, screen_for(Vector2(0, 1)))
		sim.brake = true
		run(sim, 2.0)
		sim.brake = false
		ok(Actions.exit_vehicle(sim), "and parked again")
		var pa5: Vector2i = Vector2i(roundi(sim.vehicle.anchor_f().x), roundi(sim.vehicle.anchor_f().y)) if sim.vehicle != null else Vector2i.ZERO
		for yy17 in range(fy0, fy0 + 44):
			for xx17 in range(fx0, fx0 + 12):
				if Vehicle.is_vehicle(Defs.o_id(w.obj(xx17, yy17))): w.set_obj(xx17, yy17, 0)
	ok(Inv.count(Loot.roll("medical", "", sim.rng, sim.hour, 1.0), "bandage") >= 0 and Defs.obj(Defs.O_AMBULANCE)["c"] == "medical" and Defs.obj(Defs.O_POLICE_CAR)["c"] == "locker_police", "an ambulance carries medical supplies, a police car what police carry")
	# siren
	var pe3: Dictionary = place_v.call(Defs.O_POLICE_CAR, vx2, vy2)
	p.pos = Vector2(vx2 - 0.5, vy2 + 1.5)
	opt(Actions._car_options(sim, vx2, vy2), "Drive").call()
	sim.noises.clear()
	sim.vehicle.horn()
	var siren: float = 0.0
	for nz3 in sim.noises: siren = maxf(siren, float(nz3[1]))
	ok(siren >= 70.0, "a police siren carries much further than a horn (%.0f)" % siren)
	# muffler
	sim.noises.clear()
	sim.vehicle._noise_t = 0.0
	sim.vehicle.speed = 3.0
	sim.vehicle.update(1.0 / 30.0, screen_for(Vector2(0, 1)), false)
	var quiet_r: float = 0.0
	for nz4 in sim.noises: quiet_r = maxf(quiet_r, float(nz4[1]))
	sim.vehicle.ent["muf"] = 0
	sim.noises.clear()
	sim.vehicle._noise_t = 0.0
	sim.vehicle.update(1.0 / 30.0, screen_for(Vector2(0, 1)), false)
	var loud_r: float = 0.0
	for nz5 in sim.noises: loud_r = maxf(loud_r, float(nz5[1]))
	ok(loud_r > quiet_r * 1.5, "with the muffler holed the engine is far louder (%.0f vs %.0f)" % [loud_r, quiet_r])
	sim.brake = true
	run(sim, 2.0)
	sim.brake = false
	var vpos: Vector2 = sim.vehicle.anchor_f()
	Actions.exit_vehicle(sim)
	var pa6: Vector2i = Vector2i(roundi(vpos.x), roundi(vpos.y))
	Inv.add_new(p.inv, "scrap_metal", 1)
	Inv.add_new(p.inv, "wrench", 1)
	p.pos = Vector2(pa6.x - 0.5, pa6.y + 1.5)
	var mf: Callable = opt(Actions._car_options(sim, pa6.x, pa6.y), "Patch the muffler")
	ok(mf.is_valid(), "a holed muffler can be patched")
	if mf.is_valid():
		mf.call()
		run(sim, 7.0)
		ok(int(w.ent(pa6.x, pa6.y).get("muf", 0)) == 1, "and is quiet again")
	# passengers
	var c1 = sim.npcs.spawn(p.pos + Vector2(-1.0, 0.0), false)
	var c2 = sim.npcs.spawn(p.pos + Vector2(-1.0, 1.0), false)
	c1.state = NpcSim.FOLLOW
	c2.state = NpcSim.FOLLOW
	c1.name = "Wren"
	opt(Actions._car_options(sim, pa6.x, pa6.y), "Drive").call()
	ok(sim.vehicle != null and sim.vehicle.passengers.size() == 2 and not sim.npcs.list.has(c1), "companions climb in with you")
	run(sim, 2.0, screen_for(Vector2(0, 1)))
	sim.brake = true
	run(sim, 2.0)
	sim.brake = false
	ok(SaveGame.save(sim, slot), "saving with passengers")
	s2 = SaveGame.load_game(slot)
	ok(s2 != null and s2.vehicle != null and s2.vehicle.passengers.size() == 2, "passengers persist")
	var vpos2: Vector2 = sim.vehicle.pos
	Actions.exit_vehicle(sim)
	var back := 0
	for n7 in sim.npcs.list:
		if n7.state == NpcSim.FOLLOW and n7.pos.distance_to(vpos2) < 4.0: back += 1
	ok(back == 2, "and get out beside the car when you do")
	sim.npcs.list.clear()
	for yy18 in range(fy0, fy0 + 44):
		for xx18 in range(fx0, fx0 + 12):
			if Vehicle.is_vehicle(Defs.o_id(w.obj(xx18, yy18))) and Defs.o_part(w.obj(xx18, yy18)) == 0: w.remove_object(xx18, yy18)
	bulldoze(sim, Rect2i(fx0, fy0, 12, 44))

	print("== odds and ends: looking closer, taught recipes, gun care, stray shots, lunges, stuck doors, sorting, theft, frozen pipes, mud, raids, footsteps")
	sim.zombies.list.clear()
	sim.npcs.list.clear()
	bulldoze(sim, Rect2i(fx0, fy0 + 26, 12, 18))
	p.pos = Vector2(fx0 + 5.5, fy0 + 30.5)
	w.set_obj(fx0 + 6, fy0 + 30, Defs.ocell(Defs.O_WOOD_CRATE, 0, 0))
	w.chunk_at(fx0 + 6, fy0 + 30).containers[World.idx(fx0 + 6, fy0 + 30)] = [Items.make("toy", 1), Items.make("nails", 4)]
	var lc: String = Actions.look_closer(sim, fx0 + 6, fy0 + 30)
	ok(lc.contains("Wooden crate") and lc.contains("2 things inside"), "looking closer at a crate says what is in it (\"%s\")" % lc)
	ok(opt(Actions.options(sim, {"kind": "obj", "x": fx0 + 6, "y": fy0 + 30}), "Look closer").is_valid(), "every object can be looked at closely")
	w.remove_object(fx0 + 6, fy0 + 30)
	# taught recipes
	p.known.clear()
	Inv.add_new(p.inv, "rag", 2)
	Inv.add_new(p.inv, "disinfectant", 1)
	var fd: Dictionary = Recipes.by_id("field_dressing")
	ok(Recipes.missing(fd, p, false, false, []).begins_with("someone has to show you"), "some things can only be learned from someone")
	p.known["medic"] = true
	ok(Recipes.missing(fd, p, false, false, []) == "", "once a medic has taught you, you can make field dressings")
	# gun care
	var gun9: Dictionary = Items.make("pistol", 1)
	gun9["c"] = 0.4
	gun9["jam"] = 1
	p.inv.append(gun9)
	Inv.add_new(p.inv, "gun_oil", 1)
	p.clean_gun(gun9)
	run(sim, float(p.action.get("dur", 8.0)) + 0.5)
	ok(float(gun9["c"]) > 0.7 and not gun9.has("jam") and Inv.find(p.inv, "gun_oil").get("u", 5) == 4, "cleaning and oiling a gun restores it, clears a jam, and uses some oil")
	p.inv.erase(gun9)
	# stray shots
	var by2 = sim.npcs.spawn(p.pos + Vector2(2.0, 0.0), false)
	by2.hp = 100.0
	var zb2: Zombie = sim.zombies.spawn(p.pos + Vector2(5.0, 0.0), 0)
	zb2.hp = 999.0
	Inv.add_new(p.inv, "pistol", 1)
	p.equip(Inv.find(p.inv, "pistol"))
	p.weapon["u"] = 12
	p.weapon["c"] = 1.0
	p.facing = Vector2(1, 0)
	var hit_friend := false
	for i_s in range(12):
		p.attack_cd = 0.0
		p.swing_t = 0.0
		by2.pos = p.pos + Vector2(2.0, 0.0)
		zb2.pos = p.pos + Vector2(5.0, 0.0)
		p.try_attack()
		if by2.hp < 100.0:
			hit_friend = true
			break
	ok(hit_friend, "firing past someone can hit them instead")
	ok(not sim.npcs.list.has(by2) or by2.state == NpcSim.HOSTILE, "and they take it badly")
	sim.npcs.list.clear()
	sim.zombies.list.clear()
	# lunges
	sim.settings["god"] = false
	var lz: Zombie = sim.zombies.spawn(p.pos + Vector2(0.8, 0.0), 0)
	lz.state = Zombie.CLIMB
	lz.t = 1.0
	lz.atk_cd = 0.0
	lz.climb_to = p.pos + Vector2(0.2, 0.0)
	p.slow_t = 0.0
	sim.zombies._update_z(lz, 1.0 / 30.0, 10.0, true)
	ok(p.slow_t > 1.0, "one coming through a window grabs your ankle if you stand too close")
	sim.settings["god"] = true
	sim.zombies.list.clear()
	p.slow_t = 0.0
	p.hp = 100.0
	p.wounds.clear()
	p.infection = -1.0
	# stuck doors
	var jam_found := Vector3i(-99999, 0, 0)
	for yy19 in range(fy0 + 27, fy0 + 43):
		for xx19 in range(fx0 + 1, fx0 + 11):
			for side3 in range(2):
				if jam_found.x == -99999 and Rng.h2(xx19 * 2 + side3, yy19, sim.seed_v + 4401) % 100 < 6:
					jam_found = Vector3i(xx19, yy19, side3)
	w.chunk_at(jam_found.x, jam_found.y).bld[World.idx(jam_found.x, jam_found.y)] = 991
	sim.unjammed.clear()
	ok(sim.door_jammed(jam_found.x, jam_found.y, jam_found.z), "some doors are stuck in their frames")
	Inv.add_new(p.inv, "crowbar", 1)
	w.set_wall(jam_found.x, jam_found.y, jam_found.z, Defs.wall(Defs.WM_PLASTER_CREAM, Defs.WS_DOOR))
	p.pos = Vector2(jam_found.x + 0.5, jam_found.y + 0.5)
	var fo2: Callable = opt(Actions.options(sim, {"kind": "edge", "x": jam_found.x, "y": jam_found.y, "side": jam_found.z}), "Force the stuck door")
	ok(fo2.is_valid(), "a stuck door can be forced")
	if fo2.is_valid():
		fo2.call()
		run(sim, 2.5)
		ok(not sim.door_jammed(jam_found.x, jam_found.y, jam_found.z) and not w.edge_blocks(jam_found.x, jam_found.y, jam_found.z), "with a crowbar it gives and opens")
	w.chunk_at(jam_found.x, jam_found.y).bld[World.idx(jam_found.x, jam_found.y)] = 0
	w.set_wall(jam_found.x, jam_found.y, jam_found.z, 0)
	# frozen pipes
	sim.water_off_h = sim.hour + 500.0
	var skx: int = fx0 + 3
	var sky: int = fy0 + 36
	w.set_obj(skx, sky, Defs.ocell(Defs.O_SINK_COUNTER, 0, 0))
	sim.weather["temp"] = -12.0
	sim.fires.clear()
	var so2: Array = Actions.options(sim, {"kind": "obj", "x": skx, "y": sky})
	ok(opt(so2, "The pipes have frozen").is_valid() and not opt(so2, "Drink").is_valid(), "in a deep frost an unheated house's pipes freeze")
	sim.weather["temp"] = 5.0
	ok(opt(Actions.options(sim, {"kind": "obj", "x": skx, "y": sky}), "Drink").is_valid(), "and run again in a thaw")
	w.remove_object(skx, sky)
	sim.water_off_h = sim.hour - 1.0
	# mud
	w.set_ground(fx0 + 1, fy0 + 40, Defs.G_DIRT)
	w.chunk_at(fx0 + 1, fy0 + 40).bld[World.idx(fx0 + 1, fy0 + 40)] = 0
	sim._wet_h = 4.0
	ok(sim.muddy(fx0 + 1, fy0 + 40), "after long rain bare earth is mud")
	p.pos = Vector2(fx0 + 1.5, fy0 + 40.5)
	p.bld = 0
	var sf_mud: float = p.speed_factor()
	sim._wet_h = 0.0
	ok(sf_mud < p.speed_factor(), "and slower going (x%.2f)" % sf_mud)
	# raids on the shelter
	sim.factions.sites.clear()
	var rkey := Vector2i(WorldGen.fdiv(fx0, WorldGen.REGION), WorldGen.fdiv(fy0, WorldGen.REGION))
	sim.factions.found(rkey, Vector2i(fx0 + 100, fy0 + 100), 3, 4)
	sim.set_home(Vector2(fx0 + 5.5, fy0 + 30.5))
	sim.home["b"] = 0
	w.set_obj(fx0 + 6, fy0 + 31, Defs.ocell(Defs.O_WOOD_CRATE, 0, 0))
	var hstore: Array = w.container_at(fx0 + 6, fy0 + 31)
	hstore.clear()
	for k20 in range(10): Inv.add_new(hstore, "canned_beans", 1, sim.hour)
	p.pos = Vector2(fx0 + 5.5, fy0 + 200.5) if false else p.pos
	var saved_p: Vector2 = p.pos
	p.pos = Vector2(-99999, -99999)
	sim.rng.seed = 11
	var res: String = sim.factions.raid_shelter(rkey)
	p.pos = saved_p
	ok(res == "robbed" and Inv.count(hstore, "canned_beans") < 10, "raiders strip an unguarded shelter's stores (%d of 10 tins left)" % Inv.count(hstore, "canned_beans"))
	for k21 in range(4):
		var gd = sim.npcs.spawn(sim.home_pos() + Vector2(k21, 1), false)
		gd.recruit = true
		gd.work = "guard"
	var held_n := 0
	for k22 in range(20):
		sim.rng.seed = 100 + k22
		if sim.factions.raid_shelter(rkey) == "held": held_n += 1
	ok(held_n >= 18, "four guards drive them off (%d of 20 raids held)" % held_n)
	sim.npcs.list.clear()
	sim.factions.sites.clear()
	sim.home = {}
	w.remove_object(fx0 + 6, fy0 + 31)
	# footsteps by surface
	var sfx_t := Sfx.new()
	w.set_ground(fx0 + 2, fy0 + 30, Defs.G_WOOD)
	w.set_ground(fx0 + 3, fy0 + 30, Defs.G_GRAVEL)
	w.set_ground(fx0 + 4, fy0 + 30, Defs.G_GRASS)
	ok(sfx_t._step_for(sim, Vector2(fx0 + 2.5, fy0 + 30.5)) == "step_wood" and sfx_t._step_for(sim, Vector2(fx0 + 3.5, fy0 + 30.5)) == "step_gravel" and sfx_t._step_for(sim, Vector2(fx0 + 4.5, fy0 + 30.5)) == "step_grass", "footsteps sound like the ground: wood, gravel, grass")
	sfx_t.free()
	sim._dawn_day = -1
	sim.hour = floorf(sim.hour / 24.0) * 24.0 + 24.0 + 6.0
	sim.fx.clear()
	sim._weather_hazards(0.01)
	var dawn := false
	for f9 in sim.fx:
		if f9["k"] == "music_dawn": dawn = true
	ok(dawn, "a few quiet notes at dawn")
	sim.fx.clear()

	print("== special sites, attics, overloaded generators, laundry, travelling settlers")
	var cps: Array = []
	var qcs: Array = []
	var attics: Array = []
	for rx3 in range(-3, 4):
		for ry3 in range(-3, 4):
			for lot3 in w.gen.region(rx3, ry3)["lots"]:
				if lot3["k"] == "checkpoint": cps.append(lot3)
				elif lot3["k"] == "quarantine": qcs.append(lot3)
				elif lot3["k"] == "house" and attics.size() < 3 and rx3 == 0 and ry3 == 0:
					var pl3: LotBuilder.LotPlan = w.gen.lot_plan(lot3)
					if pl3.attic: attics.append([lot3, pl3])
	ok(cps.size() > 0 and qcs.size() > 0, "the countryside has military checkpoints (%d) and quarantine camps (%d)" % [cps.size(), qcs.size()])
	if cps.size() > 0:
		var cpl: LotBuilder.LotPlan = w.gen.lot_plan(cps[0])
		var sand := 0
		var crates2 := 0
		for oi in range(cpl.obj.size()):
			var oid2: int = Defs.o_id(cpl.obj[oi])
			if oid2 == Defs.O_SANDBAG: sand += 1
			if oid2 == Defs.O_MIL_CRATE: crates2 += 1
		ok(sand >= 10 and crates2 >= 2 and cpl.zspawn.size() >= 4 and cpl.corpses.size() >= 2, "a checkpoint: sandbags (%d), military crates (%d), dead soldiers, and the infected (%d)" % [sand, crates2, cpl.zspawn.size()])
	if qcs.size() > 0:
		var qpl: LotBuilder.LotPlan = w.gen.lot_plan(qcs[0])
		var tents := 0
		for oi2 in range(qpl.obj.size()):
			if Defs.o_id(qpl.obj[oi2]) == Defs.O_TENT and Defs.o_part(qpl.obj[oi2]) == 0: tents += 1
		ok(tents >= 6 and qpl.zspawn.size() >= 9, "a quarantine camp: rows of tents (%d) and many of the infected (%d)" % [tents, qpl.zspawn.size()])
	var mil: Array = Loot.roll("military", "", sim.rng, sim.hour, 1.0)
	ok(mil.size() >= 2, "military crates hold military supplies (%s)" % str(mil.map(func(it): return it["id"])))
	bulldoze(sim, Rect2i(fx0, fy0 + 26, 12, 18))
	w.set_obj(fx0 + 6, fy0 + 30, Defs.ocell(Defs.O_SANDBAG, 0, 0))
	var mils := 0
	for k23 in range(40):
		var zm2: Zombie = sim.zombies.spawn(Vector2(fx0 + 4.5, fy0 + 30.5), 0)
		if zm2.role == "military": mils += 1
	ok(mils > 20, "the infected found at sandbag lines were mostly soldiers (%d of 40)" % mils)
	sim.zombies.list.clear()
	w.remove_object(fx0 + 6, fy0 + 30)
	# attics
	ok(attics.size() > 0, "some houses have an attic ladder instead of stairs")
	if attics.size() > 0:
		var alot: Dictionary = attics[0][0]
		var apl: LotBuilder.LotPlan = attics[0][1]
		var ar: Rect2i = alot["r"]
		var ax3: int = ar.position.x + apl.stairs.x
		var ay3: int = ar.position.y + apl.stairs.y
		p.pos = Vector2(ax3 + 0.5, ay3 + 0.5)
		w.stream(p.pos, 2, 999)
		sim._process_world_events()
		quiet(sim)
		ok(Defs.o_id(w.obj(ax3, ay3)) == Defs.O_ATTIC_LADDER, "the ladder hangs in the house")
		var al: Callable = opt(Actions.options(sim, {"kind": "obj", "x": ax3, "y": ay3}), "Climb into the attic")
		ok(al.is_valid(), "and leads up into the attic")
		al.call()
		run(sim, 2.0)
		ok(World.level(p.pos.y) == 2 and w.btype_at(floori(p.pos.x), floori(p.pos.y)) == "attic", "where it is an attic")
		var boxes := 0
		var attic_loot := 0
		for yy20 in range(floori(p.pos.y) - 14, floori(p.pos.y) + 15):
			for xx20 in range(floori(p.pos.x) - 14, floori(p.pos.x) + 15):
				if Defs.o_id(w.obj(xx20, yy20)) == Defs.O_BOXES and w.bld(xx20, yy20) == w.bld(floori(p.pos.x), floori(p.pos.y)):
					boxes += 1
					attic_loot += w.container_at(xx20, yy20).size()
		ok(boxes > 0 and attic_loot > 0, "full of boxed-up things (%d boxes, %d items)" % [boxes, attic_loot])
		p.pos = Vector2(ax3 + 0.5, ay3 + World.UNDER * 2 + 0.5)
		opt(Actions.options(sim, {"kind": "obj", "x": ax3, "y": ay3 + World.UNDER * 2}), "Climb down").call()
		run(sim, 2.0)
		ok(World.level(p.pos.y) == 0, "and back down")
	p.pos = Vector2(fx0 + 5.5, fy0 + 30.5)
	w.stream(p.pos, 3, 999)
	sim._process_world_events()
	quiet(sim)
	bulldoze(sim, Rect2i(fx0, fy0 + 26, 12, 18))
	# overloaded generator fires
	sim.power_off_h = sim.hour - 1.0
	var gx3: int = fx0 + 2
	var gy3: int = fy0 + 30
	w.set_obj(gx3, gy3, Defs.ocell(Defs.O_GENERATOR, 0, 0))
	for k24 in range(12): w.set_obj(fx0 + k24 % 10 + 1, fy0 + 34 + k24 / 10, Defs.ocell(Defs.O_LAMP, 0, 0))
	sim.burning.clear()
	var burned := false
	sim.rng.seed = 77
	seed(77)
	for k25 in range(200):
		w.set_ent(gx3, gy3, {"k": "gen", "fuel": 40.0, "on": true, "c": 1.0})
		sim._sim_ents(w.chunk_at(gx3, gy3), 0.5, false)
		if sim.burning.has(Vector2i(gx3, gy3)):
			burned = true
			break
	ok(burned, "a badly overloaded generator can catch fire")
	sim.burning.clear()
	sim.fires.clear()
	bulldoze(sim, Rect2i(fx0, fy0 + 26, 12, 18))
	# laundry
	p.cloth_dirt = 80.0
	p.grime = 0.0
	p.tick_needs(0.1)
	ok(p.grime >= 30.0, "filthy clothes make you filthy again (grime %.0f)" % p.grime)
	var wlx: int = fx0 + 6
	var wly: int = fy0 + 32
	w.set_obj(wlx, wly, Defs.ocell(Defs.O_WELL, 0, 0))
	p.pos = Vector2(wlx - 0.5, wly + 0.5)
	var wet0: float = p.wet
	var lnd: Callable = opt(Actions.options(sim, {"kind": "obj", "x": wlx, "y": wly}), "Wash your clothes")
	ok(lnd.is_valid(), "clothes can be washed at a well")
	lnd.call()
	run(sim, float(p.action.get("dur", 10.0)) + 0.5)
	ok(p.cloth_dirt < 10.0 and p.wet > wet0 + 30.0, "and come out clean, and damp")
	w.remove_object(wlx, wly)
	p.cloth_dirt = 0.0
	p.grime = 0.0
	p.wet = 0.0
	# travellers from settlements
	sim.factions.sites.clear()
	sim.factions.found(Vector2i(80, 80), Vector2i(fx0 + 80, fy0 + 80), 0, 4)
	var with_fac := 0
	for k26 in range(12):
		sim.npcs.list.clear()
		sim.npcs.send_trader()
		for n8 in sim.npcs.list:
			if n8.trader and n8.fac == 0: with_fac += 1
	ok(with_fac > 0, "many travellers on the road belong to a settlement (%d of 12)" % with_fac)
	sim.npcs.list.clear()
	sim.factions.sites.clear()

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
	ok(q.markers.is_empty() and sim.world.explored.size() < 60, "the dead survivor's map knowledge is gone (%d chunks known)" % sim.world.explored.size())
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
