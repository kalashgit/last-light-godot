extends SceneTree
## Fast headless checks for the systems added from the A–Z design archive (grapples, fire fighting,
## witnessed reputation, the journal, safe placement, world events, new content).
## godot --headless --path . -s tests/godot/test_systems.gd
var fails := 0
var checks := 0

func ok(cond: bool, what: String) -> void:
	checks += 1
	if not cond: fails += 1
	print("  %s  %s" % ["PASS" if cond else "FAIL", what])

func run(sim: Sim, seconds: float, move := Vector2.ZERO) -> void:
	var t := 0.0
	while t < seconds:
		sim.tick(1.0 / 30.0, move, false)
		t += 1.0 / 30.0

func quiet(sim: Sim) -> void:
	sim.zombies.list.clear()
	sim.zombies.wander_t = 1e9
	sim.settings["god"] = true
	sim.settings["meta"] = false

func clear_area(sim: Sim, c: Vector2i, r: int) -> void:
	var w: World = sim.world
	for y in range(c.y - r, c.y + r + 1):
		for x in range(c.x - r, c.x + r + 1):
			if w.obj(x, y) != 0: w.set_obj(x, y, 0)
			w.set_wall(x, y, 0, 0)
			w.set_wall(x, y, 1, 0)
			w.set_ground(x, y, Defs.G_DIRT)

func _init() -> void:
	seed(9090)
	var sim := Sim.new(777)
	sim.new_game("unemployed", [], "house")
	var p: Player = sim.player
	quiet(sim)
	var here := Vector2i(floori(p.pos.x), floori(p.pos.y))
	clear_area(sim, here, 8)
	p.pos = Vector2(here) + Vector2(0.5, 0.5)

	print("== grapples")
	var z: Zombie = sim.zombies.spawn(p.pos + Vector2(0.8, 0.0), 0)
	z.state = Zombie.ATTACK
	p.grabbed_by = z.id
	var p0: Vector2 = p.pos
	run(sim, 0.6, Vector2(-1, 0))
	ok(p.pos.distance_to(p0) < 0.05, "while held you cannot walk away (moved %.2f)" % p.pos.distance_to(p0))
	var presses := 0
	while p.grabbed_by >= 0 and presses < 20:
		p.attack_cd = 0.0
		p.try_shove()
		presses += 1
		run(sim, 0.05)
	ok(p.grabbed_by == -1 and presses >= 3, "repeated shoves tear you free (%d presses)" % presses)
	ok(z.state == Zombie.STAGGER, "breaking free staggers the infected")
	var weak := Sim.new(778)
	weak.new_game("unemployed", ["frail"], "house")
	var strong := Sim.new(778)
	strong.new_game("unemployed", ["strong"], "house")
	var counts: Array = []
	for s in [weak, strong]:
		quiet(s)
		var zz: Zombie = s.zombies.spawn(s.player.pos + Vector2(0.8, 0), 0)
		zz.state = Zombie.ATTACK
		s.player.grabbed_by = zz.id
		var n := 0
		while s.player.grabbed_by >= 0 and n < 30:
			s.player.struggle()
			n += 1
		counts.append(n)
	ok(int(counts[1]) <= int(counts[0]), "a strong survivor breaks free in no more presses than a weak one (%d vs %d)" % [counts[1], counts[0]])
	# real grabs happen from real hits
	sim.settings["god"] = false
	var grabs := 0
	for k in range(60):
		p.hp = 100.0
		p.wounds.clear()
		p.grabbed_by = -1
		p.take_zombie_hit(z)
		if p.grabbed_by == z.id: grabs += 1
	ok(grabs > 3 and grabs < 30, "some infected hits turn into a grab (%d of 60)" % grabs)
	p.grabbed_by = -1
	p.hp = 100.0
	p.wounds.clear()
	sim.settings["god"] = true
	sim.zombies.list.clear()
	p.grabbed_by = 12345
	run(sim, 0.1)
	ok(p.grabbed_by == -1, "a grab ends if the infected is gone")
	p.grabbed_by = 54321
	Inv.add_new(p.inv, "pistol", 1)
	Inv.add_new(p.inv, "ammo_9mm", 12)
	p.weapon = Inv.find(p.inv, "pistol")
	p.weapon["u"] = 0
	p.try_attack()
	run(sim, 3.0)
	ok(p.grabbed_by == -1 and int(p.weapon.get("u", 0)) == 12, "a stale grab does not swallow your next press (reloaded %d)" % int(p.weapon.get("u", 0)))
	p.weapon = {}
	Inv.take(p.inv, "pistol", 1)

	print("== fire fighting and smoke")
	var ft := here + Vector2i(1, 0)
	sim.burning[ft] = 20.0
	var tg: Array = Actions.targets(sim)
	var fire_t: Dictionary = {}
	for t in tg:
		if t["kind"] == "fire_tile": fire_t = t
	ok(not fire_t.is_empty(), "a burning tile within reach is something you can act on")
	Inv.add_new(p.inv, "water_bottle", 1)
	var labels: Array = []
	for o in Actions.options(sim, fire_t): labels.append(o["label"])
	ok(labels.has("Douse it with water (2)"), "with water you can douse it (%s)" % str(labels))
	for o in Actions.options(sim, fire_t):
		if o["label"].begins_with("Douse"): o["fn"].call()
	ok(not sim.burning.has(ft), "dousing puts the tile out")
	Inv.add_new(p.inv, "fire_extinguisher", 1)
	for dx in range(-1, 2): sim.burning[ft + Vector2i(dx + 1, 0)] = 60.0
	var ext: Dictionary = Inv.find(p.inv, "fire_extinguisher")
	var u0: int = int(ext.get("u", 0))
	for t in Actions.targets(sim):
		if t["kind"] == "fire_tile":
			for o in Actions.options(sim, t):
				if o["label"].begins_with("Spray"): o["fn"].call()
			break
	ok(sim.burning.size() <= 1 and int(ext.get("u", 0)) == u0 - 1, "an extinguisher clears a patch of fire and uses a charge (%d left burning)" % sim.burning.size())
	sim.burning.clear()
	Inv.add_new(p.inv, "sheet", 1)
	sim.burning[ft] = 10.0
	for t in Actions.targets(sim):
		if t["kind"] == "fire_tile":
			for o in Actions.options(sim, t):
				if o["label"].begins_with("Smother"): o["fn"].call()
	ok(not sim.burning.has(ft) and Inv.count(p.inv, "sheet") == 0, "a small fire can be smothered with a sheet, which is lost")
	ok(Loot.T.has("kitchen") and str(Loot.T["kitchen"]).contains("fire_extinguisher"), "extinguishers turn up in kitchens")
	# ventilation: build a closed room with fire in it, then open a window
	var rx := here.x + 20
	var ry := here.y
	var w: World = sim.world
	clear_area(sim, Vector2i(rx + 2, ry + 2), 5)
	var bid := 4242
	for y in range(ry, ry + 5):
		for x in range(rx, rx + 5):
			var bc: Chunk = w.chunk(x >> 4, y >> 4)
			bc.bld[((y & 15) << 4) | (x & 15)] = bid
			w.set_ground(x, y, Defs.G_WOOD)
	var solid: int = Defs.wall(Defs.WM_PLASTER_CREAM, Defs.WS_SOLID)
	for i in range(5):
		w.set_wall(rx + i, ry, 0, solid)
		w.set_wall(rx + i, ry + 5, 0, solid)
		w.set_wall(rx, ry + i, 1, solid)
		w.set_wall(rx + 5, ry + i, 1, solid)
	w.set_wall(rx + 2, ry, 0, Defs.wall(Defs.WM_PLASTER_CREAM, Defs.WS_WINDOW))
	p.pos = Vector2(rx + 2.5, ry + 2.5)
	ok(not sim._room_vented(bid), "a sealed room has no ventilation")
	w.set_edge_state(rx + 2, ry, 0, Defs.ES_OPEN)
	ok(sim._room_vented(bid), "an open window ventilates the room")
	sim.settings["god"] = false
	var hurt := [0.0, 0.0]
	for pass_i in range(2):
		w.set_edge_state(rx + 2, ry, 0, Defs.ES_OPEN if pass_i == 1 else 0)
		sim.burning.clear()
		for k in range(4): sim.burning[Vector2i(rx + 4, ry + k)] = 999.0
		p.hp = 100.0
		for s2 in range(5):
			sim._smoke_t = 0.0
			sim._tick_smoke(1.0)
		hurt[pass_i] = 100.0 - p.hp
	ok(hurt[1] < hurt[0] and hurt[1] > 0.0, "smoke still hurts with a window open, but less (%.1f vs %.1f)" % [hurt[1], hurt[0]])
	sim.settings["god"] = true
	sim.burning.clear()
	p.hp = 100.0
	p.pos = Vector2(here) + Vector2(0.5, 0.5)

	print("== reputation travels by witness or rumour")
	var f_open := 0
	var a = sim.npcs.spawn(p.pos + Vector2(1.0, 0.0), false)
	a.fac = f_open
	var r0: float = sim.factions.rep_of(f_open)
	sim.factions.rumors.clear()
	sim.npcs.damage(a, 999.0, true)
	ok(absf(sim.factions.rep_of(f_open) - r0) < 0.01, "killing a member nobody saw changes nothing at once")
	var tries := 1
	while sim.factions.rumors.is_empty() and tries < 20:
		var a2 = sim.npcs.spawn(p.pos + Vector2(1.0, 0.0), false)
		a2.fac = f_open
		sim.npcs.damage(a2, 999.0, true)
		tries += 1
	ok(not sim.factions.rumors.is_empty(), "…but word may get out later (a rumour is queued)")
	var due: float = float(sim.factions.rumors[0][2])
	ok(due - sim.hour >= 12.0 and due - sim.hour <= 48.0, "the rumour reaches them in 12–48 h (%.0f h)" % (due - sim.hour))
	r0 = sim.factions.rep_of(f_open)
	sim.hour = due + 0.1
	sim.factions.tick(0.1)
	ok(sim.factions.rep_of(f_open) < r0, "when it arrives, the faction thinks less of you (%.0f -> %.0f)" % [r0, sim.factions.rep_of(f_open)])
	sim.factions.rumors.clear()
	var victim = sim.npcs.spawn(p.pos + Vector2(1.0, 0.0), false)
	var watcher = sim.npcs.spawn(p.pos + Vector2(0.0, 3.0), false)
	victim.fac = f_open
	watcher.fac = f_open
	ok(sim.factions.witnessed(victim), "another member in sight is a witness")
	r0 = sim.factions.rep_of(f_open)
	sim.npcs.damage(victim, 999.0, true)
	ok(sim.factions.rep_of(f_open) <= r0 - 40.0, "killing in front of a witness costs you at once (%.0f -> %.0f)" % [r0, sim.factions.rep_of(f_open)])
	var hurt_one = sim.npcs.spawn(p.pos + Vector2(1.0, 0.0), false)
	hurt_one.fac = 1
	sim.npcs.list.erase(watcher)
	r0 = sim.factions.rep_of(1)
	sim.npcs.damage(hurt_one, 1.0, true)
	ok(sim.factions.rep_of(1) < r0, "a member you hurt but leave alive tells the others")
	sim.npcs.list.clear()
	sim.factions.rumors = [[1, -5.0, sim.hour + 20.0]]
	var fsave: Dictionary = sim.factions.save()
	sim.factions.rumors = []
	sim.factions.load(fsave)
	ok(sim.factions.rumors.size() == 1, "pending rumours survive a save")

	print("== the journal")
	p.markers.clear()
	sim.add_marker(here.x + 200, here.y, "Far farm")
	sim.add_marker(here.x + 3, here.y, "Shed")
	ok(not p.markers[0][3] and p.markers[1][3], "a place far away is only rumoured; one in view is known")
	p.pos = Vector2(here.x + 195, here.y)
	sim._update_markers()
	ok(p.markers[0][3], "going there turns a rumour into a known place")
	p.pos = Vector2(here) + Vector2(0.5, 0.5)
	sim.read_note({"txt": "Gone to the river. — J"})
	ok(p.journal.size() == 1 and String(p.journal[0][1]).contains("river"), "notes you read are written in the journal")
	SaveGame.delete("sys_slot")
	ok(SaveGame.save(sim, "sys_slot"), "save with journal")
	var l: Sim = SaveGame.load_game("sys_slot")
	ok(l != null and l.player.journal.size() == 1 and l.player.markers.size() == 2 and l.player.markers[0][3], "journal and known places restored")
	SaveGame.delete("sys_slot")

	print("== building placement respects whoever is standing there")
	sim.zombies.list.clear()
	p.facing = Vector2(1, 0)
	var camp: Dictionary = Recipes.by_id("campfire")
	ok(Actions.build_target(sim, camp)["ok"], "an empty tile can be built on")
	var zb: Zombie = sim.zombies.spawn(Vector2(p.front_tile()) + Vector2(0.5, 0.5), 0)
	var bt: Dictionary = Actions.build_target(sim, camp)
	ok(not bt["ok"] and String(bt["why"]).contains("standing"), "not on top of an infected (%s)" % bt.get("why", ""))
	sim.zombies.list.erase(zb)
	var ns = sim.npcs.spawn(Vector2(p.front_tile()) + Vector2(0.5, 0.5), false)
	ok(not Actions.build_target(sim, camp)["ok"], "not on top of a survivor")
	ns.state = NpcSim.FOLLOW
	p.carrying = {"o": Defs.O_WARDROBE, "rot": 0, "items": []}
	ok(Actions.build_target(sim, Actions.carry_recipe(p))["ok"], "a companion helping you carry steps aside when you set it down")
	p.carrying = {}
	sim.npcs.list.erase(ns)

	print("== the event director")
	sim.zombies.list.clear()
	sim.npcs.list.clear()
	p.markers.clear()
	sim.objectives.clear()
	p.pos = Vector2(here) + Vector2(0.5, 0.5)
	ok(sim.world_event("distress"), "a distress call can come in")
	var dob: Dictionary = sim.objectives[0]
	var dat := Vector2(float(dob["x"]) + 0.5, float(dob["y"]) + 0.5)
	ok(dob["state"] == "open" and dat.distance_to(p.pos) > 50.0 and p.markers.size() == 1 and not p.markers[0][3], "it is far off, on the map as a place you have only heard of (%.0f tiles)" % dat.distance_to(p.pos))
	ok(not sim.world_event("distress"), "only one call at a time")
	p.pos = dat + Vector2(10.0, 0.0)
	sim.world.stream(p.pos, 3, 99)
	sim._check_objectives()
	ok(dob["spawned"] and sim.npcs.list.size() == 1 and sim.zombies.list.size() >= 3, "arriving, you find a survivor with the infected closing in (%d)" % sim.zombies.list.size())
	var caller = sim.npcs.list[0]
	sim._check_objectives()
	ok(dob["state"] == "open", "not answered while they are still surrounded")
	sim.zombies.list.clear()
	p.pos = caller.pos + Vector2(2.0, 0.0)
	var inv0: int = p.inv.size()
	var tr0: float = caller.trust
	sim._check_objectives()
	ok(dob["state"] == "done" and caller.trust > tr0 and p.inv.size() > inv0, "clearing them off earns trust and a gift")
	ok(String(p.journal[p.journal.size() - 1][1]).contains("owes me"), "and it goes in the journal")
	sim.npcs.list.clear()
	sim.objectives.clear()
	sim.world_event("distress")
	sim.hour += 31.0
	sim._check_objectives()
	ok(sim.objectives[0]["state"] == "failed", "ignore a call long enough and it goes quiet")
	p.pos = Vector2(here) + Vector2(0.5, 0.5)
	sim.world.stream(p.pos, 3, 99)
	sim.zombies.list.clear()
	sim.npcs.list.clear()
	ok(sim.world_event("fleeing"), "a survivor can come running")
	var runner = sim.npcs.list[0] if not sim.npcs.list.is_empty() else null
	var rd0: float = runner.pos.distance_to(p.pos) if runner != null else 0.0
	ok(runner != null and sim.zombies.list.size() >= 2, "with infected behind them (%d)" % sim.zombies.list.size())
	for zz in sim.zombies.list: zz.pos += (zz.pos - p.pos).normalized() * 6.0      # give them room
	run(sim, 2.0)
	ok(runner != null and runner.pos.distance_to(p.pos) < rd0 - 3.0, "they run toward you (%.1f -> %.1f)" % [rd0, runner.pos.distance_to(p.pos) if runner != null else 0.0])
	sim.zombies.list.clear()
	sim.npcs.list.clear()
	ok(sim.world_event("horde"), "a migrating horde can come through")
	var hz: int = sim.zombies.list.size()
	var all_goal := true
	for zz in sim.zombies.list:
		if not zz.has_goal or zz.state != Zombie.INVESTIGATE: all_goal = false
	ok(hz >= 6 and all_goal, "%d infected, all moving with somewhere to go" % hz)
	sim.zombies.list.clear()
	sim.weather["rain"] = 0.0
	sim.weather["temp"] = 24.0
	sim.snow_cover = 0.0
	sim.burning.clear()
	var wf: bool = sim.world_event("wildfire")
	ok(not wf or not sim.burning.is_empty(), "a dry day can start a wildfire nearby (%s)" % ("started" if wf else "nothing flammable here"))
	sim.burning.clear()
	sim.weather["rain"] = 0.8
	ok(not sim.world_event("wildfire"), "not in the rain")
	sim.weather["rain"] = 0.0
	var nz0: int = sim.noises.size()
	ok(sim.world_event("crash") and sim.noises.size() > nz0, "a car crash is loud enough to draw them")
	var crash_loot := false
	for ch in sim.world.chunks.values():
		for cp in ch.corpses:
			if cp.has("loot") and absf(float(cp["h"]) - sim.hour) < 0.01: crash_loot = true
	ok(crash_loot, "and leaves a body with something on it")
	sim.burning.clear()
	var tkey := Vector2i(WorldGen.fdiv(floori(p.pos.x), WorldGen.REGION), WorldGen.fdiv(floori(p.pos.y), WorldGen.REGION))
	var saved_sites: Dictionary = sim.factions.sites
	sim.factions.sites = {tkey: {"f": 0, "fallen": false, "name": "Test camp", "pop": 5, "morale": 50.0, "food": 50.0, "met": false}}
	sim.factions.rep[0] = 0.0
	ok(sim.world_event("patrol"), "a faction patrol can pass by")
	var pm = sim.npcs.list[sim.npcs.list.size() - 1] if not sim.npcs.list.is_empty() else null
	ok(pm != null and pm.fac == 0 and pm.site == tkey and pm.task == "travel", "patrol members belong to the nearby settlement and are going somewhere")
	var pm0: Vector2 = pm.pos if pm != null else Vector2.ZERO
	for i2 in range(90): sim.npcs.update(1.0 / 30.0, 0.0)
	ok(pm != null and pm.pos.distance_to(pm0) > 1.5, "they walk on (%.1f tiles)" % (pm.pos.distance_to(pm0) if pm != null else 0.0))
	sim.npcs.list.clear()
	sim.factions.rep[0] = -80.0
	sim.world_event("patrol")
	var hm = sim.npcs.list[0] if not sim.npcs.list.is_empty() else null
	var hm0: Vector2 = hm.pos if hm != null else Vector2.ZERO
	for i3 in range(90): sim.npcs.update(1.0 / 30.0, 0.0)
	ok(hm != null and hm.state == NpcSim.HOSTILE and hm.pos.distance_to(hm0) > 1.5, "a patrol from people who hate you is hostile, and still on the move")
	sim.factions.sites = saved_sites
	sim.npcs.list.clear()
	# the director itself, left alone for a few game days
	var ds := Sim.new(31337)
	ds.new_game("unemployed", [], "house")
	ds.settings["god"] = true
	ds._event_h = 0.0
	var before_log: int = ds.log.size()
	ds._director(0.1)
	ok(ds._event_h > 5.0, "after an event the director waits hours before the next (%.0f h)" % ds._event_h)
	ds.settings["events"] = 0.0
	ds._event_h = 0.0
	ds._director(0.1)
	ok(ds._event_h <= 0.0, "events can be switched off in the settings")
	SaveGame.delete("sys_slot2")
	sim.objectives = [{"kind": "distress", "x": 1, "y": 2, "state": "open", "due": 99.0, "spawned": false, "npc": -1, "text": "x"}]
	SaveGame.save(sim, "sys_slot2")
	var l2: Sim = SaveGame.load_game("sys_slot2")
	ok(l2 != null and l2.objectives.size() == 1 and l2.objectives[0]["kind"] == "distress", "open objectives survive a save")
	SaveGame.delete("sys_slot2")

	print("== wildlife")
	var ws := Sim.new(4141)
	ws.new_game("unemployed", [], "cabin")
	quiet(ws)
	var wp: Player = ws.player
	var wt := Vector2i(floori(wp.pos.x), floori(wp.pos.y))
	clear_area(ws, wt, 10)
	wp.pos = Vector2(wt) + Vector2(0.5, 0.5)
	ws.animals.list.clear()
	for k in ["squirrel", "duck", "turkey", "crow", "rat", "dog", "snake"]:
		ok(AnimalSim.SPECIES.has(k) and Items.DB.has(AnimalSim.SPECIES[k]["drop"]), "%s exists and leaves a carcass" % k)
	var butch := 0
	for k2 in ["carcass_squirrel", "carcass_duck", "carcass_turkey", "carcass_crow", "carcass_rat", "carcass_dog", "carcass_snake"]:
		for r in Recipes.LIST:
			if (r.get("in", []) as Array).size() > 0 and r["in"][0][0] == k2: butch += 1
	ok(butch == 7, "every new carcass can be butchered (%d/7)" % butch)
	# snake: holds its ground and bites
	ws.settings["god"] = false
	var sn = ws.animals.spawn("snake", wp.pos + Vector2(0.7, 0.0))
	wp.sneaking = false
	var sick0: float = wp.sick
	var hp0: float = wp.hp
	wp.gear.clear()
	wp.worn = {}
	var bitten := false
	for k3 in range(20):
		sn.atk = 0.0
		ws.animals.update(1.0 / 30.0)
		if wp.sick > sick0: bitten = true
		if bitten: break
	ok(bitten and wp.hp < hp0, "step next to a snake and it bites; the venom makes you sick (sick %.0f)" % wp.sick)
	ok(ws.animals.list.has(sn) and sn.pos.distance_to(wp.pos) < 1.0, "it does not run")
	wp.sick = 0.0
	ws.animals.list.clear()
	sn = ws.animals.spawn("snake", wp.pos + Vector2(0.7, 0.0))
	wp.sneaking = true
	var s0: float = wp.sick
	for k4 in range(30): ws.animals.update(1.0 / 30.0)
	ok(wp.sick == s0, "creep past slowly and it leaves you be")
	wp.sneaking = false
	ws.animals.list.clear()
	# feral dogs hunt as a pack
	var pack: Array = []
	for k5 in range(3):
		pack.append(ws.animals.spawn("dog", wp.pos + Vector2(7.0, -1.0 + k5)))
	ws.hour = floorf(ws.hour / 24.0) * 24.0 + 23.0      # night
	wp.hp = 100.0
	for k6 in range(60): ws.animals.update(1.0 / 30.0)
	var charging := 0
	for dg in pack:
		if dg.state == AnimalSim.CHARGE: charging += 1
	ok(charging == 3, "a pack that sees you at night comes for you all together (%d of 3)" % charging)
	var hp1: float = wp.hp
	wp.wounds.clear()
	for k7 in range(150): ws.animals.update(1.0 / 30.0)
	ok(wp.hp < hp1 and not wp.wounds.is_empty(), "and they bite (hp %.0f, %d wounds)" % [wp.hp, wp.wounds.size()])
	ws.animals.damage(pack[0], 25.0, wp.pos)
	for k8 in range(5): ws.animals.update(1.0 / 30.0)
	ok(pack[0].state == AnimalSim.FLEE or pack[0].state == AnimalSim.IDLE, "a badly hurt dog breaks off")
	ws.animals.list.clear()
	ws.settings["god"] = true
	wp.hp = 100.0
	wp.wounds.clear()
	# crows are loud when they go up
	var cr = ws.animals.spawn("crow", wp.pos + Vector2(3.0, 0.0))
	ws.noises.clear()
	var nn0: int = 0
	ws.animals._scare(cr, wp.pos)
	var loud := 0.0
	for nz in ws.noises: loud = maxf(loud, float(nz[1]))
	ok(ws.noises.size() > nn0 and loud >= 14.0, "crows breaking cover make a racket the infected can hear (%.0f)" % loud)
	ws.animals.list.clear()
	# rats eat stored food but not tins
	var cx2 := Vector2i(floori(wp.pos.x) + 2, floori(wp.pos.y))
	ws.world.set_obj(cx2.x, cx2.y, Defs.ocell(Defs.O_CRATE, 0, 0))
	var box: Array = ws.world.container_at(cx2.x, cx2.y)
	box.clear()
	box.append(Items.make("bread", 2))
	box.append(Items.make("canned_beans", 1))
	var rt = ws.animals.spawn("rat", Vector2(cx2) + Vector2(0.5, 1.5))
	ws.animals.nibble(rt)
	ok(Inv.count(box, "bread") == 1 and Inv.count(box, "canned_beans") == 1, "a rat gets into the bread, not the tins")
	ws.animals.list.clear()
	ok(ws.animals._fit_kind("snake", wp.pos) == ("snake" if float(ws.weather["temp"]) >= 12.0 else "rabbit"), "snakes only come out when it is warm")

	print("== new gear")
	Inv.add_new(wp.inv, "canteen", 1)
	var cn: Dictionary = Inv.find(wp.inv, "canteen")
	for k9 in range(10): Inv.use_charge(wp.inv, cn)
	ok(wp.inv.has(cn) and int(cn["u"]) == 0, "an empty canteen is kept, not thrown away")
	Actions._fill(ws, false, 20)
	ok(int(cn["u"]) == 10, "and can be refilled")
	Inv.add_new(wp.inv, "kevlar_vest", 1)
	Inv.add_new(wp.inv, "jacket", 1)
	wp.equip(Inv.find(wp.inv, "jacket"))
	var d_jacket: float = wp.clothing_def(2)
	wp.equip(Inv.find(wp.inv, "kevlar_vest"))
	ok(wp.clothing_def(2) > d_jacket + 0.4 and not wp.worn.is_empty(), "a kevlar vest under a jacket protects the chest (%.2f vs %.2f)" % [wp.clothing_def(2), d_jacket])
	Inv.add_new(wp.inv, "compass", 1)
	ws.set_home(wp.pos + Vector2(30, 0))
	var lg0: int = ws.log.size()
	ws.take_bearing()
	ok(ws.log.size() > lg0 and String(ws.log[ws.log.size() - 1][0]).contains("home"), "a compass gives the bearing home")
	var ex0: int = ws.world.explored.size()
	Inv.add_new(wp.inv, "road_atlas", 1)
	var added: int = ws.read_atlas(Inv.find(wp.inv, "road_atlas"))
	ok(added > 100 and ws.world.explored.size() >= ex0 + added, "a road atlas fills in the district map (%d blocks)" % added)
	# car keys
	var car := Vector2i(floori(wp.pos.x) + 3, floori(wp.pos.y) + 3)
	clear_area(ws, car + Vector2i(1, 2), 3)
	for j in range(4):
		for i in range(2):
			ws.world.set_obj(car.x + i, car.y + j, Defs.ocell(Defs.O_CAR, 0, j * 2 + i))
	if true:
		var e: Dictionary = Vehicle.car_ent(ws, car.x, car.y)
		e["key"] = 0
		e["hot"] = 0
		Inv.add_new(wp.inv, "car_keys", 1)
		var labels2: Array = []
		for o in Actions._car_options(ws, car.x, car.y): labels2.append(o["label"])
		ok(labels2.has("Try the car keys you found"), "found keys can be tried on a car")
		var fit := false
		for t in range(30):
			if Actions.try_keys(ws, e, car.x, car.y):
				fit = true
				break
		var ky: Dictionary = Inv.find(wp.inv, "car_keys")
		ok((fit and e["key"] == 1 and ky.get("car", "") == "%d,%d" % [car.x, car.y]) or (not fit and (ky.get("no", []) as Array).size() == 1), "keys either fit (and are remembered) or are known not to")
		if fit:
			e["key"] = 0
			ok(Actions.try_keys(ws, e, car.x, car.y), "a key that fitted once always fits that car")
		else:
			var labels3: Array = []
			for o in Actions._car_options(ws, car.x, car.y): labels3.append(o["label"])
			ok(not labels3.has("Try the car keys you found"), "keys that did not fit are not offered again for that car")
	else:
		ok(true, "no car near this start (skipped)")
	ok(Loot.T.has("nightstand") and str(Loot.T["nightstand"]).contains("car_keys") and str(Loot.T["military"]).contains("kevlar_vest"), "new gear is in the loot tables")

	print("== substations")
	var ss := Sim.new(5151)
	ss.new_game("unemployed", [], "house")
	quiet(ss)
	var sp: Player = ss.player
	var st := Vector2i(floori(sp.pos.x) + 2, floori(sp.pos.y))
	clear_area(ss, st, 3)
	ss.world.set_obj(st.x, st.y, Defs.ocell(Defs.O_SUBSTATION, 0, 0))
	sp.pos = Vector2(st) + Vector2(-0.5, 0.5)
	sp.facing = Vector2(1, 0)
	var far := Vector2i(st.x + 30, st.y + 10)
	ss.power_off_h = ss.hour + 10.0
	var so: Array = Actions._obj_options(ss, {"kind": "obj", "x": st.x, "y": st.y})
	ok(String(so[0]["label"]).contains("grid is still up"), "while the grid runs, a substation needs nothing")
	ss.power_off_h = ss.hour - 1.0
	ok(not ss.has_power(far.x, far.y), "after the grid fails, the streets are dark")
	so = Actions._obj_options(ss, {"kind": "obj", "x": st.x, "y": st.y})
	var rep_fn: Callable
	for o in so:
		if String(o["label"]).begins_with("Repair the substation"): rep_fn = o["fn"]
	ok(rep_fn.is_valid(), "a dead substation offers a repair")
	rep_fn.call()
	ok(sp.action.is_empty(), "without Electrical 3 and parts you cannot start")
	sp.skills["electrical"] = 500.0
	Inv.add_new(sp.inv, "wire", 4)
	Inv.add_new(sp.inv, "scrap_metal", 2)
	Inv.add_new(sp.inv, "pliers", 1)
	rep_fn.call()
	ok(not sp.action.is_empty(), "with the skill, wire, scrap and pliers the repair begins")
	run(ss, 42.0)
	ok(Inv.count(sp.inv, "wire") == 0 and ss.has_power(far.x, far.y), "once rewired, buildings for blocks around have power again")
	ok(not ss.has_power(st.x + 200, st.y), "but not across the whole map")
	var se: Dictionary = ss.world.ent(st.x, st.y)
	ok(float(se.get("until", 0.0)) - ss.hour > 24.0 * 4.0, "it holds for days (%.0f h)" % (float(se.get("until", 0.0)) - ss.hour))
	var hum := false
	ss._slow_tick(0.01)
	for nz in ss.noises:
		if Vector2(nz[0]).distance_to(Vector2(st) + Vector2(0.5, 0.5)) < 0.1: hum = true
	ok(hum, "a running substation hums, and the infected hear it")
	ss.hour = float(se["until"]) + 1.0
	ss._slow_tick(0.01)
	ok(not ss.has_power(far.x, far.y), "then it fails again")
	var found_sub := false
	for sd2 in range(60):
		var pl = BuildGen.gen("warehouse", 24, 20, 0, 9000 + sd2, 1)
		for cell in pl.obj:
			if Defs.o_id(cell) == Defs.O_SUBSTATION: found_sub = true
	ok(found_sub, "substations stand in the yards of some industrial lots")

	print("== hurt hands, harder conversations")
	var hs := Sim.new(6161)
	hs.new_game("unemployed", [], "house")
	quiet(hs)
	var hp_: Player = hs.player
	hp_.wounds.clear()
	hp_.start_action("Test", 10.0, func(): pass)
	var d0: float = float(hp_.action["dur"])
	hp_.cancel_action()
	hp_.add_wound(10, "laceration", "test")
	hp_.start_action("Test", 10.0, func(): pass)
	ok(float(hp_.action["dur"]) > d0 * 1.2, "a cut hand makes work slower (%.1f s vs %.1f s)" % [float(hp_.action["dur"]), d0])
	hp_.cancel_action()
	hp_.wounds.clear()
	hp_.add_wound(13, "laceration", "test")
	hp_.start_action("Test", 10.0, func(): pass)
	ok(absf(float(hp_.action["dur"]) - d0) < 0.01, "a leg wound does not")
	hp_.cancel_action()
	hp_.wounds.clear()
	var nb = hs.npcs.spawn(hp_.pos + Vector2(1.0, 0.0), false)
	nb.trust = 70.0
	nb.temper = "generous"
	var labs: Array = []
	for o in hs.npcs.options(nb): labs.append(String(o["label"]))
	ok(str(labs).contains("Help me for a few hours"), "a survivor who trusts you can be asked for help")
	ok(hs.npcs.ask_help(nb) and nb.state == NpcSim.FOLLOW, "they come with you")
	hs.hour += 6.5
	hs.npcs.update(0.1, 0.0)
	ok(nb.state == NpcSim.STAY and nb.help_until == 0.0, "and go home when the hours are up")
	Inv.add_new(hp_.inv, "kitchen_knife", 1)
	hp_.weapon = Inv.find(hp_.inv, "kitchen_knife")
	var outcomes: Dictionary = {}
	for k in range(40):
		var v = hs.npcs.spawn(hp_.pos + Vector2(1.0, 0.0), false)
		v.temper = ["brave", "cautious", "generous", "wary"][k % 4]
		v.stock = ["bandage", "battery"]
		var t0: float = v.trust
		var res: String = hs.npcs.threaten(v)
		outcomes[res] = int(outcomes.get(res, 0)) + 1
		if v.trust > maxf(0.0, t0 - 40.0) + 0.01: outcomes["bad"] = 1
	ok(outcomes.has("gave") and outcomes.has("fight") and not outcomes.has("bad"), "threatened survivors give in, run or fight, and trust you far less (%s)" % str(outcomes))
	var bitter = hs.npcs.spawn(hp_.pos + Vector2(1.0, 0.0), false)
	bitter.trust = 10.0
	Inv.add_new(hp_.inv, "granola_bar", 1)
	labs = []
	for o in hs.npcs.options(bitter): labs.append(String(o["label"]))
	ok(labs.any(func(l): return l.contains("sorry")), "someone who distrusts you can be offered an apology")
	var food_n0: int = 0
	for it in hp_.inv:
		if Items.def(it["id"]).get("cat", "") == "food": food_n0 += int(it.get("n", 1))
	var st0: int = bitter.stock.size()
	var ap: bool = hs.npcs.apologize(bitter)
	var food_n1: int = 0
	for it in hp_.inv:
		if Items.def(it["id"]).get("cat", "") == "food": food_n1 += int(it.get("n", 1))
	ok(ap and bitter.trust > 10.0 and food_n1 == food_n0 - 1 and bitter.stock.size() == st0 + 1, "one food goes from you to them and some trust comes back (%.0f)" % bitter.trust)
	labs = []
	for o in hs.npcs.options(bitter): labs.append(String(o["label"]))
	ok(not labs.any(func(l): return l.contains("sorry")), "but not twice in one day")
	var sv_rec: Array = NpcSim._ser(nb)
	nb.help_until = 99.0
	sv_rec = NpcSim._ser(nb)
	ok(hs.npcs._de(sv_rec).help_until == 99.0, "an agreed favour survives a save")
	hs.npcs.list.clear()

	print("== wiring and pumps")
	var es := Sim.new(7171)
	es.new_game("unemployed", [], "house")
	quiet(es)
	var ep: Player = es.player
	var e0 := Vector2i(floori(ep.pos.x), floori(ep.pos.y))
	clear_area(es, e0 + Vector2i(10, 0), 12)
	es.power_off_h = es.hour - 1.0
	var gpos := e0 + Vector2i(0, 0)
	var lamp := e0 + Vector2i(20, 0)
	es.world.set_obj(lamp.x, lamp.y, Defs.ocell(Defs.O_LAMP, 0, 0))
	es.generators = [gpos]
	ok(not es.has_power(lamp.x, lamp.y), "a lamp twenty tiles from a generator is dark")
	var cabl: Array = []
	for cx in range(1, 20):
		es.world.set_obj(e0.x + cx, e0.y, Defs.ocell(Defs.O_CABLE, 0, 0))
		cabl.append(Vector2i(e0.x + cx, e0.y))
	es._cable_network(cabl)
	ok(es.has_power(lamp.x, lamp.y), "a cable run from the generator carries power to it")
	var cut: Array = cabl.duplicate()
	cut.remove_at(14)
	es._cable_network(cut)
	ok(not es.has_power(lamp.x, lamp.y), "cut the run and the far end goes dark")
	es.generators = []
	es._cable_network(cabl)
	ok(not es.has_power(lamp.x, lamp.y), "no source, no power")
	ok(not Recipes.by_id("power_cable").is_empty(), "cable can be laid from wire")
	# strip an appliance
	var tv := e0 + Vector2i(4, 3)
	es.world.set_obj(tv.x, tv.y, Defs.ocell(Defs.O_TV, 0, 0))
	Inv.add_new(ep.inv, "screwdriver", 1)
	var w0: int = Inv.count(ep.inv, "wire")
	Actions._strip_wiring(es, tv.x, tv.y)
	run(es, 9.0)
	ok(Inv.count(ep.inv, "wire") > w0 and es.world.ent(tv.x, tv.y).get("stripped", false), "a dead appliance can be stripped for wire")
	var tvl: Array = []
	for o in Actions._obj_options(es, {"kind": "obj", "x": tv.x, "y": tv.y}): tvl.append(String(o["label"]))
	ok(str(tvl).contains("stripped") and not str(tvl).contains("Switch"), "and never runs again")
	# a pump on a well
	var wl := e0 + Vector2i(6, 5)
	es.world.set_obj(wl.x, wl.y, Defs.ocell(Defs.O_WELL, 0, 0))
	ep.pos = Vector2(wl.x + 1.5, wl.y + 2.5)
	ep.facing = Vector2(0, -1)
	var pr: Dictionary = Recipes.by_id("well_pump")
	ok(Actions.build_target(es, pr)["ok"], "a pump can go beside a well")
	ep.pos = Vector2(wl.x + 6.5, wl.y + 6.5)
	ok(not Actions.build_target(es, pr)["ok"], "but not away from one")
	var pmp := Vector2i(wl.x + 1, wl.y + 1)
	es.world.set_obj(pmp.x, pmp.y, Defs.ocell(Defs.O_PUMP, 0, 0))
	es.water_off_h = es.hour - 1.0
	var snk := pmp + Vector2i(3, 0)
	es.world.set_obj(snk.x, snk.y, Defs.ocell(Defs.O_SINK_COUNTER, 0, 0))
	es.pumps = [pmp]
	es.generators = []
	ok(not es.pumped(snk.x, snk.y), "an unpowered pump gives nothing")
	es.generators = [pmp + Vector2i(0, 2)]
	ok(es.pumped(snk.x, snk.y), "powered, it sends well water to the taps")
	var sl: Array = []
	for o in Actions._obj_options(es, {"kind": "obj", "x": snk.x, "y": snk.y}): sl.append(String(o["label"]))
	ok(sl.has("Drink") and sl.has("Fill water containers"), "a sink nearby runs again after the mains are gone (%s)" % str(sl))
	ok(es.loads_near(pmp.x, pmp.y, 2) >= 1, "and the pump is a load on the generator")

	print("== masks and fumes")
	var ms := Sim.new(8181)
	ms.new_game("unemployed", [], "house")
	quiet(ms)
	ms.settings["god"] = false
	var mp: Player = ms.player
	var mt := Vector2i(floori(mp.pos.x) + 30, floori(mp.pos.y))
	var mw: World = ms.world
	clear_area(ms, mt + Vector2i(2, 2), 5)
	for y in range(mt.y, mt.y + 5):
		for x in range(mt.x, mt.x + 5):
			mw.chunk(x >> 4, y >> 4).bld[((y & 15) << 4) | (x & 15)] = 5151
	var wall_s: int = Defs.wall(Defs.WM_PLASTER_CREAM, Defs.WS_SOLID)
	for i in range(5):
		mw.set_wall(mt.x + i, mt.y, 0, wall_s)
		mw.set_wall(mt.x + i, mt.y + 5, 0, wall_s)
		mw.set_wall(mt.x, mt.y + i, 1, wall_s)
		mw.set_wall(mt.x + 5, mt.y + i, 1, wall_s)
	mp.pos = Vector2(mt.x + 2.5, mt.y + 2.5)
	var smoke_hurt := [0.0, 0.0]
	for pass_m in range(2):
		if pass_m == 1:
			Inv.add_new(mp.inv, "gas_mask", 1)
			mp.equip(Inv.find(mp.inv, "gas_mask"))
		ms.burning.clear()
		for k in range(4): ms.burning[Vector2i(mt.x + 4, mt.y + k)] = 999.0
		mp.hp = 100.0
		for s3 in range(5):
			ms._smoke_t = 0.0
			ms._tick_smoke(1.0)
		smoke_hurt[pass_m] = 100.0 - mp.hp
	ok(smoke_hurt[1] < smoke_hurt[0] * 0.3, "a gas mask keeps most of the smoke out (%.1f vs %.1f)" % [smoke_hurt[1], smoke_hurt[0]])
	ms.burning.clear()
	mp.gear.clear()
	mp.hp = 100.0
	ms.generators = [Vector2i(mt.x + 1, mt.y + 1)]
	ms.fume_h = 0.0
	for k2 in range(40): ms._generator_fumes()
	ok(ms.fume_h > 0.8 and mp.hp < 100.0, "a generator running in a closed house poisons you (hp %.0f)" % mp.hp)
	mw.set_wall(mt.x + 2, mt.y, 0, Defs.wall(Defs.WM_PLASTER_CREAM, Defs.WS_WINDOW))
	mw.set_edge_state(mt.x + 2, mt.y, 0, Defs.ES_OPEN)
	var f1: float = ms.fume_h
	for k3 in range(10): ms._generator_fumes()
	ok(ms.fume_h < f1, "an open window clears it")
	mw.set_edge_state(mt.x + 2, mt.y, 0, 0)
	ms.fume_h = 0.0
	mp.equip(Inv.find(mp.inv, "gas_mask"))
	for k4 in range(40): ms._generator_fumes()
	ok(ms.fume_h < 0.8 * 0.5, "a gas mask slows it a great deal (%.2f)" % ms.fume_h)
	ms.generators = []
	mp.corpses_near = 8
	mp.corpse_exp = 0.0
	mp.gear.clear()
	mp._tick_body(1.0)
	var ce0: float = mp.corpse_exp
	mp.corpse_exp = 0.0
	Inv.add_new(mp.inv, "dust_mask", 1)
	mp.equip(Inv.find(mp.inv, "dust_mask"))
	mp._tick_body(1.0)
	ok(mp.corpse_exp < ce0 * 0.5, "a dust mask cuts the stench of the dead (%.1f vs %.1f)" % [mp.corpse_exp, ce0])
	mp.corpses_near = 0
	ok(str(Loot.T["military"]).contains("gas_mask") and str(Loot.T["store_hardware"]).contains("dust_mask"), "masks are in the loot")

	print("== animation, sound and moving house")
	for an in ["s_carry", "s_hold", "s_reload", "s_vault"]:
		ok(ArtChars.ANIMS.has(an), "character animation %s exists" % an)
	var as_ := Sim.new(9191)
	as_.new_game("unemployed", [], "house")
	quiet(as_)
	var anp: Player = as_.player
	anp.carrying = {"o": Defs.O_CRATE, "rot": 0, "items": []}
	anp.update(1.0 / 30.0, Vector2.ZERO, false)
	ok(anp.anim == "s_hold", "standing with furniture in your arms uses the holding pose (%s)" % anp.anim)
	run(as_, 0.3, Vector2(1, 0))
	ok(anp.anim == "s_carry", "walking with it uses the carrying walk (%s)" % anp.anim)
	anp.carrying = {}
	anp.start_action("Climbing", 2.0, func(): pass, false)
	anp.update(1.0 / 30.0, Vector2.ZERO, false)
	ok(anp.anim == "s_vault", "climbing through a window or over a fence has its own animation (%s)" % anp.anim)
	anp.cancel_action()
	anp.start_action("Reloading", 2.0, func(): pass, false)
	anp.update(1.0 / 30.0, Vector2.ZERO, false)
	ok(anp.anim == "s_reload", "so does reloading (%s)" % anp.anim)
	anp.cancel_action()
	Sfx._make_buses()
	ok(AudioServer.get_bus_index("Near") >= 0 and AudioServer.get_bus_index("Muffled") >= 0, "the sound mix has a near bus (room echo) and a muffled bus")
	var atl := Vector2i(floori(anp.pos.x), floori(anp.pos.y))
	clear_area(as_, atl, 6)
	for yy in range(atl.y - 6, atl.y + 7):
		for xx in range(atl.x - 6, atl.x + 7):
			as_.world.chunk(xx >> 4, yy >> 4).bld[((yy & 15) << 4) | (xx & 15)] = 0
	anp.pos = Vector2(atl) + Vector2(0.5, 0.5)
	ok(Sfx.bus_for(as_, anp.pos + Vector2(4, 0)) == "Near", "outdoors, a sound in the open is heard plainly")
	as_.world.chunk(atl.x >> 4, atl.y >> 4).bld[((atl.y & 15) << 4) | (atl.x & 15)] = 777
	ok(Sfx.bus_for(as_, anp.pos + Vector2(4, 0)) == "Muffled", "from inside a building, the street is muffled")
	ok(Sfx.bus_for(as_, anp.pos + Vector2(0, World.UNDER)) == "Muffled", "and so is a floor below")
	# a settlement that cannot feed itself moves in with its neighbours
	var fk := Vector2i(50, 50)
	var fk2 := Vector2i(51, 50)
	as_.factions.sites = {fk: {"f": 0, "fallen": false, "name": "Dry Camp", "pop": 5, "morale": 2.0, "food": 0.0, "met": true, "x": 50 * 384, "y": 50 * 384},
		fk2: {"f": 0, "fallen": false, "name": "Mill Camp", "pop": 4, "morale": 60.0, "food": 80.0, "met": false, "x": 51 * 384, "y": 50 * 384}}
	var mover = as_.npcs.spawn(anp.pos + Vector2(2, 0), false)
	mover.fac = 0
	mover.site = fk
	ok(as_.factions.relocate(fk) == fk2, "a starving, hopeless settlement leaves for the nearest one that will have them")
	ok(as_.factions.sites[fk]["fallen"] and int(as_.factions.sites[fk2]["pop"]) == 9, "the old place is empty; the new one has nine mouths")
	ok(mover.site == fk2 and mover.task == "travel" and mover.task_pos.distance_to(Vector2(51 * 384, 50 * 384)) < 2.0, "its people walk to their new home")
	for i5 in range(30): as_.npcs.update(1.0 / 30.0, 0.0)
	ok(as_.npcs.list.has(mover), "and do not vanish on the way")
	mover.task_pos = mover.pos + Vector2(0.5, 0.0)       # (the new home brought within the loaded area)
	for i6 in range(10): as_.npcs.update(1.0 / 30.0, 0.0)
	ok(as_.npcs.list.has(mover) and mover.task == "", "arriving, they settle")
	as_.factions.sites = {fk: {"f": 0, "fallen": false, "name": "Lone Camp", "pop": 3, "morale": 0.0, "food": 0.0, "met": false, "x": 0, "y": 0}}
	ok(as_.factions.relocate(fk) == Vector2i(-99999, -99999) and not as_.factions.sites[fk]["fallen"], "with nowhere to go, they stay and starve")
	as_.npcs.list.clear()

	print("== prisons, bunkers, laboratories")
	for kind in ["prison", "lab", "bunker"]:
		var plan_k = BuildGen.gen(kind, {"prison": 34, "lab": 26, "bunker": 13}[kind], {"prison": 28, "lab": 22, "bunker": 13}[kind], 0, 4242, 1)
		var cntk: Dictionary = {}
		for cell in plan_k.obj:
			var oid: int = Defs.o_id(cell)
			if oid != 0 and Defs.o_part(cell) == 0: cntk[oid] = int(cntk.get(oid, 0)) + 1
		var inside_n := 0
		for v in plan_k.inside: inside_n += int(v != 0)
		match kind:
			"prison": ok(int(cntk.get(Defs.O_BED, 0)) >= 4 and int(cntk.get(Defs.O_TOILET, 0)) >= 4 and plan_k.btype == "prison", "a prison has cells, each with a cot and a toilet (%d, %d)" % [int(cntk.get(Defs.O_BED, 0)), int(cntk.get(Defs.O_TOILET, 0))])
			"lab": ok(int(cntk.get(Defs.O_MED_CABINET, 0)) >= 3 and int(cntk.get(Defs.O_DESK, 0)) >= 3 and plan_k.btype == "lab", "a laboratory has benches and cabinets")
			"bunker": ok(int(cntk.get(Defs.O_MIL_CRATE, 0)) >= 1 and int(cntk.get(Defs.O_HATCH, 0)) == 1 and int(cntk.get(Defs.O_SANDBAG, 0)) >= 4, "a bunker has military crates, sandbags and a hatch down")
		ok(inside_n > 20, "%s is a real building (%d tiles indoors)" % [kind, inside_n])
	ok(Loot.T.has("lab") and str(Loot.T["lab"]).contains("lab_report") and Loot.OVERRIDE.has("prison"), "each has its own loot")
	var rs := Sim.new(1212)
	rs.new_game("unemployed", [], "house")
	quiet(rs)
	var roles2: Dictionary = {}
	var lc := rs.world.chunk_at(floori(rs.player.pos.x), floori(rs.player.pos.y))
	var saved_bt: Dictionary = lc.btype.duplicate()
	var uid0: int = rs.world.bld(floori(rs.player.pos.x), floori(rs.player.pos.y))
	if uid0 != 0:
		lc.btype[uid0] = "prison"
		for i7 in range(60):
			var rl: String = rs.zombies._role_for(rs.player.pos)
			roles2[rl] = int(roles2.get(rl, 0)) + 1
		ok(int(roles2.get("prisoner", 0)) > 30, "the infected in a prison were mostly prisoners (%s)" % str(roles2))
		lc.btype[uid0] = "lab"
		roles2 = {}
		for i8 in range(60):
			var rl2: String = rs.zombies._role_for(rs.player.pos)
			roles2[rl2] = int(roles2.get(rl2, 0)) + 1
		ok(int(roles2.get("hazmat", 0)) > 20, "in a lab, staff in sealed suits (%s)" % str(roles2))
		lc.btype = saved_bt
	else:
		ok(false, "start position is indoors for the role test")
	var hzm: Zombie = rs.zombies.spawn(rs.player.pos + Vector2(3, 0), 0)
	rs.zombies._apply_role(hzm, "hazmat")
	var cv2: Zombie = rs.zombies.spawn(rs.player.pos + Vector2(4, 0), 0)
	cv2.role = "civilian"
	cv2.armor = 1.0
	hzm.hp = 100.0
	cv2.hp = 100.0
	rs.zombies.damage(hzm, 40.0, rs.player.pos, 0.0, false, false)
	rs.zombies.damage(cv2, 40.0, rs.player.pos, 0.0, false, false)
	ok(hzm.hp > cv2.hp + 10.0, "a sealed suit turns much of a blow (%.0f vs %.0f)" % [hzm.hp, cv2.hp])
	rs.zombies.list.clear()
	var rep2: Dictionary = Items.make("lab_report", 1)
	rs.read_note(rep2)
	ok(String(rep2.get("txt", "")).begins_with("LAB REPORT"), "lab reports can be read")
	rs.weather["temp"] = -15.0
	var cold_out: float = rs.zombies.cold_factor(Vector2(-99999, -99999))
	rs.weather["temp"] = 15.0
	ok(cold_out < 0.8 and rs.zombies.cold_factor(Vector2(-99999, -99999)) == 1.0, "as the reports say, hard frost slows the infected outdoors (x%.2f)" % cold_out)

	print("== the second dozen crops")
	ok(Farming.CROP_OBJ.size() >= 24, "%d crops can be grown" % Farming.CROP_OBJ.size())
	var all_ok := true
	for crn in Farming.CROP_OBJ.keys():
		if not Items.DB.has(crn) or not Items.DB.has("seeds_" + crn) or not Farming.YIELD.has(crn) or not Farming.GROW_HOURS.has(crn) or Defs.obj(int(Farming.CROP_OBJ[crn])).get("crop", "") != crn:
			all_ok = false
			print("    incomplete crop: ", crn)
	ok(all_ok, "each has seeds, produce, a yield, a growing time and a plant")
	var fs2 := Sim.new(2323)
	fs2.new_game("farmer", [], "farm")
	quiet(fs2)
	var fp: Player = fs2.player
	var ft2 := Vector2i(floori(fp.pos.x) + 2, floori(fp.pos.y))
	clear_area(fs2, ft2, 2)
	fs2.world.set_ground(ft2.x, ft2.y, Defs.G_SOIL)
	fs2.world.set_obj(ft2.x, ft2.y, Defs.ocell(int(Farming.CROP_OBJ["blueberries"]), 0, 3))
	fs2.world.set_ent(ft2.x, ft2.y, {"k": "crop", "t": "blueberries", "s": 3, "g": 999.0, "w": 50.0})
	var hv_fn: Callable
	for o in Actions._obj_options(fs2, {"kind": "obj", "x": ft2.x, "y": ft2.y}):
		if String(o["label"]).begins_with("Harvest"): hv_fn = o["fn"]
	ok(hv_fn.is_valid(), "ripe blueberries can be picked")
	hv_fn.call()
	run(fs2, 4.0)
	ok(Inv.count(fp.inv, "blueberries") > 0 and Defs.o_id(fs2.world.obj(ft2.x, ft2.y)) == int(Farming.CROP_OBJ["blueberries"]) and int(fs2.world.ent(ft2.x, ft2.y)["s"]) == 2,
		"a perennial bush bears again instead of being pulled up")
	fs2.world.set_obj(ft2.x, ft2.y, Defs.ocell(int(Farming.CROP_OBJ["radish"]), 0, 3))
	fs2.world.set_ent(ft2.x, ft2.y, {"k": "crop", "t": "radish", "s": 3, "g": 999.0, "w": 50.0})
	for o in Actions._obj_options(fs2, {"kind": "obj", "x": ft2.x, "y": ft2.y}):
		if String(o["label"]).begins_with("Harvest"): o["fn"].call()
	run(fs2, 4.0)
	ok(Inv.count(fp.inv, "radish") > 0 and fs2.world.obj(ft2.x, ft2.y) == 0, "an annual like radish is pulled up when harvested")
	# mushrooms only fruit out of the sun
	var mk3 := ft2 + Vector2i(0, 1)
	fs2.world.set_obj(mk3.x, mk3.y, Defs.ocell(int(Farming.CROP_OBJ["oyster_mushroom"]), 0, 0))
	fs2.world.set_ent(mk3.x, mk3.y, {"k": "crop", "t": "oyster_mushroom", "s": 0, "g": 0.0, "w": 90.0})
	fs2.weather["temp"] = 15.0
	fs2.weather["rain"] = 0.0
	fs2.hour = floorf(fs2.hour / 24.0) * 24.0 + 12.0
	var mc: Chunk = fs2.world.chunk_at(mk3.x, mk3.y)
	fs2._sim_ents(mc, 2.0, false)
	var g_day: float = float(fs2.world.ent(mk3.x, mk3.y)["g"])
	fs2.hour = floorf(fs2.hour / 24.0) * 24.0 + 23.5
	fs2.world.ent(mk3.x, mk3.y)["w"] = 90.0
	fs2._sim_ents(mc, 2.0, false)
	ok(g_day == 0.0 and float(fs2.world.ent(mk3.x, mk3.y)["g"]) > 0.0, "mushrooms do not grow in the noon sun, only in the dark")

	print("== twenty kinds of wildlife")
	ok(AnimalSim.SPECIES.size() >= 20, "%d wild species" % AnimalSim.SPECIES.size())
	var wv := Sim.new(3434)
	wv.new_game("unemployed", [], "cabin")
	quiet(wv)
	var wvp: Player = wv.player
	var wvt := Vector2i(floori(wvp.pos.x), floori(wvp.pos.y))
	clear_area(wv, wvt, 8)
	for yy2 in range(wvt.y - 8, wvt.y + 9):
		for xx2 in range(wvt.x - 8, wvt.x + 9):
			wv.world.chunk(xx2 >> 4, yy2 >> 4).bld[((yy2 & 15) << 4) | (xx2 & 15)] = 0
	wvp.pos = Vector2(wvt) + Vector2(0.5, 0.5)
	wv.animals.list.clear()
	var cat_w = wv.animals.spawn("cat", wvp.pos + Vector2(4, 0))
	var rat2_w = wv.animals.spawn("rat", wvp.pos + Vector2(6, 0))
	var mouse2_w = wv.animals.spawn("mouse", wvp.pos + Vector2(5, 1))
	var wv_home: Vector2 = wvp.pos
	wvp.pos += Vector2(0, 30)              # out of sight: none of them is running from you
	for k9 in range(30 * 60): 
		if not wv.animals.list.has(rat2_w) and not wv.animals.list.has(mouse2_w): break
		cat_w.t = 99.0
		wv.animals.update(1.0 / 30.0)
	ok(not wv.animals.list.has(rat2_w) and not wv.animals.list.has(mouse2_w), "a cat keeps the rats and mice down")
	wvp.pos = wv_home
	wv.animals.damage(cat_w, 100.0, wvp.pos)
	var dropped_cat := false
	for it2 in wv.world.items_at(floori(cat_w.pos.x), floori(cat_w.pos.y)):
		dropped_cat = true
	ok(not wv.animals.list.has(cat_w) and not dropped_cat, "and leaves nothing to butcher")
	wv.animals.list.clear()
	wv.settings["god"] = false
	var goose_w = wv.animals.spawn("goose", wvp.pos + Vector2(2.5, 0))
	wvp.hp = 100.0
	for k10 in range(150): wv.animals.update(1.0 / 30.0)
	ok(wvp.hp < 100.0 and wvp.hp > 80.0, "walk up to a goose and it comes at you, hard but not deadly (hp %.0f)" % wvp.hp)
	wv.animals.list.clear()
	wvp.hp = 100.0
	wv.weather["temp"] = 22.0
	var sw2_w = wv.animals.spawn("swarm", wvp.pos + Vector2(0.5, 0))
	var st0_w: float = wvp.stress
	for k11 in range(90):
		sw2_w.pos = wvp.pos + Vector2(0.4, 0)
		wv.animals.update(1.0 / 30.0)
	ok(wvp.stress > st0_w, "standing in an insect swarm wears on you (stress %.0f -> %.0f)" % [st0_w, wvp.stress])
	wv.burning[Vector2i(floori(sw2_w.pos.x) + 1, floori(sw2_w.pos.y))] = 30.0
	wv.fires.append(Vector2i(floori(sw2_w.pos.x) + 1, floori(sw2_w.pos.y)))
	wv.animals.update(1.0 / 30.0)
	ok(not wv.animals.list.has(sw2_w), "smoke breaks it up")
	wv.burning.clear()
	wv.fires.clear()
	wv.animals.list.clear()
	wv.settings["god"] = true
	var fr2_w = wv.animals.spawn("frog", wvp.pos + Vector2(6, 0))
	wv.hour = floorf(wv.hour / 24.0) * 24.0 + 23.5
	wv.noises.clear()
	for k12 in range(30 * 30):
		fr2_w.state = AnimalSim.IDLE
		wv.animals.update(1.0 / 30.0)
		if not wv.noises.is_empty(): break
	ok(not wv.noises.is_empty(), "frogs sing at night, loud enough to carry")
	wv.animals.list.clear()
	var but_ok_w := true
	for kk_w in ["hare", "mouse", "pigeon", "goose", "chicken", "frog"]:
		var dr_w: String = AnimalSim.SPECIES[kk_w]["drop"]
		var found2_w := false
		for r2 in Recipes.LIST:
			if (r2.get("in", []) as Array).size() > 0 and r2["in"][0][0] == dr_w: found2_w = true
		if not found2_w: but_ok_w = false
	ok(but_ok_w, "each new animal you can hunt can be butchered")

	print("== settings and save files")
	Opts.vibrate = false
	ok(not Opts.buzz(50), "with vibration off, nothing buzzes")
	Opts.vibrate = true
	ok(Opts.buzz(1), "with it on, a hit asks the phone to buzz")
	SaveGame.delete("sys_exp")
	ws.player.weight = 66.6
	ok(SaveGame.save(ws, "sys_exp"), "save a game to export")
	var zipf: String = SaveGame.export_slot("sys_exp", "user://exports/test_export.zip")
	ok(zipf != "" and FileAccess.file_exists(zipf), "the slot exports to a single file")
	ws.player.weight = 11.1
	SaveGame.save(ws, "sys_exp")
	ok(SaveGame.import_slot(zipf, "sys_exp"), "and imports back")
	var li: Sim = SaveGame.load_game("sys_exp")
	ok(li != null and absf(li.player.weight - 66.6) < 0.01, "the imported game is the exported one, not the newer save")
	var bad := FileAccess.open("user://exports/test_bad.zip", FileAccess.WRITE)
	bad.store_string("not a zip")
	bad.close()
	ok(not SaveGame.import_slot("user://exports/test_bad.zip", "sys_exp"), "a broken file is refused")
	li = SaveGame.load_game("sys_exp")
	ok(li != null and absf(li.player.weight - 66.6) < 0.01, "and the save is left as it was")
	ok(SaveGame.exports().has("user://exports/test_export.zip"), "exported files are listed for import")
	DirAccess.remove_absolute("user://exports/test_export.zip")
	DirAccess.remove_absolute("user://exports/test_bad.zip")
	SaveGame.delete("sys_exp")

	print("")
	print("RESULT: %d checks, %d failed" % [checks, fails])
	quit(1 if fails > 0 else 0)
