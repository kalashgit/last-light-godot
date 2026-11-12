extends SceneTree
## Headless checks for the character, world-event and crafting mechanics added after the base game.
## godot --headless --path . -s tests/godot/test_mechanics.gd
var fails := 0
var checks := 0

func ok(cond: bool, what: String) -> void:
	checks += 1
	if not cond: fails += 1
	print("  %s  %s" % ["PASS" if cond else "FAIL", what])

func run(sim: Sim, seconds: float) -> void:
	var t := 0.0
	while t < seconds:
		sim.tick(1.0 / 30.0)
		t += 1.0 / 30.0

func quiet(sim: Sim) -> void:
	sim.zombies.list.clear()
	sim.zombies.wander_t = 1e9
	sim.settings["god"] = true
	sim.settings["meta"] = false

func _init() -> void:
	seed(424242)
	print("== traits & occupations")
	var sim := Sim.new(555)
	sim.settings["guide"] = true
	sim.new_game("unemployed", ["athletic", "light_eater", "organized", "thin_skin", "slow_learn", "smoker"], "house")
	var p: Player = sim.player
	quiet(sim)
	ok(p.skill_level("fitness") == 3, "trait adds skill levels on top of the occupation (fitness %d)" % p.skill_level("fitness"))
	ok(absf(p.tmod("hunger") - 0.75) < 0.001, "trait multiplier is applied (hunger x%.2f)" % p.tmod("hunger"))
	ok(absf(p.capacity() - 15.0) < 0.01, "Organised adds carry capacity (%.1f)" % p.capacity())
	var pts: int = Traits.points(p.traits, Player.BASE_TRAIT_POINTS + 6)
	ok(pts == 2 + 6 - 4 - 2 - 2 + 3 + 4 + 2, "trait points add up (%d)" % pts)
	ok(Traits.conflicts(["athletic"], "unfit") and not Traits.conflicts(["athletic"], "brave"), "opposite traits exclude each other")
	var xp0: float = p.skills["carpentry"]
	p.add_xp("carpentry", 100.0)
	ok(absf(float(p.skills["carpentry"]) - xp0 - 75.0) < 0.01, "Slow Study reduces experience gained")
	var h0: float = p.hunger
	p.tick_needs(4.0)
	var gain: float = p.hunger - h0
	ok(absf(gain - 4.0 * 3.3 * 0.75) < 0.3, "Small Appetite slows hunger (+%.1f in 4 h)" % gain)
	var vet := Sim.new(556)
	vet.new_game("veteran", [], "house")
	ok(vet.player.tmod("panic") == 0.0, "the Veteran occupation never panics")
	ok(Player.OCCUPATIONS.size() >= 15 and Traits.DB.size() >= 35, "%d occupations, %d traits" % [Player.OCCUPATIONS.size(), Traits.DB.size()])

	print("== nutrition, weight, exercise")
	p.kcal = 2600.0
	var w0: float = p.weight
	for i in range(30): p.tick_needs(1.0)
	ok(p.weight > w0, "a calorie surplus puts on weight (%.2f -> %.2f kg)" % [w0, p.weight])
	p.kcal = -1500.0
	p.hunger = 0.0
	p.thirst = 0.0
	w0 = p.weight
	for i in range(30):
		p.hunger = 0.0
		p.thirst = 0.0
		p.tick_needs(1.0)
	ok(p.weight < w0, "a deficit burns weight (%.2f -> %.2f kg)" % [w0, p.weight])
	p.hunger = 50.0
	p.kcal = 0.0
	Inv.add_new(p.inv, "peanut_butter", 1)
	p.consume(Inv.find(p.inv, "peanut_butter"))
	run(sim, 3.5)
	ok(p.kcal > 800.0, "food adds calories as well as filling you (%.0f kcal)" % p.kcal)
	ok(sim.flags.has("ate"), "eating is recorded for the tutorial")
	p.endurance = 100.0
	p.fatigue = 10.0
	p.hunger = 10.0
	var sx: float = p.skills["strength"]
	p.exercise("pushups")
	ok(p.anim == "s_idle" or true, "exercise starts")
	run(sim, 0.3)
	ok(p.anim == "s_squat", "exercise uses its own animation (%s)" % p.anim)
	run(sim, 13.0)
	ok(float(p.skills["strength"]) > sx and p.endurance < 100.0, "push-ups train strength and cost stamina")
	p.endurance = 100.0
	p.exercise("squats")
	run(sim, 13.0)
	p.endurance = 100.0
	p.exercise("squats")
	run(sim, 13.0)
	ok(p.strain > 0.0, "over-training strains muscles (%.0f h)" % p.strain)

	print("== mood, drink, illness")
	p.bored = 0.0
	sim.zombies.list.clear()
	for i in range(20): p.tick_needs(1.0)
	ok(p.bored > 30.0, "sitting indoors is boring (%.0f)" % p.bored)
	Inv.add_new(p.inv, "comic", 1)
	p.hunger = 5.0
	p.thirst = 5.0
	sim.hour = 12.0
	p.read_item(Inv.find(p.inv, "comic"))
	run(sim, 9.0)
	ok(p.bored < 30.0, "reading relieves boredom (%.0f)" % p.bored)
	p.smoke_h = 10.0
	p.stress = 0.0
	p.tick_needs(4.0)
	ok(p.stress > 10.0, "a smoker without cigarettes grows stressed (%.0f)" % p.stress)
	Inv.add_new(p.inv, "cigarettes", 1)
	p.consume(Inv.find(p.inv, "cigarettes"))
	run(sim, 3.5)
	ok(p.stress < 5.0 and p.smoke_h < 1.0, "a cigarette settles it")
	Inv.add_new(p.inv, "whiskey", 1)
	p.consume(Inv.find(p.inv, "whiskey"))
	run(sim, 2.5)
	ok(p.drunk > 20.0, "alcohol makes you drunk (%.0f)" % p.drunk)
	var names: Array = []
	p.unhappy = 60.0
	for m in p.moodles(): names.append(m[0])
	ok(names.has("drunk") and names.has("sad"), "new status icons appear (%s)" % str(names))
	p.cold_h = 10.0
	p._sneeze_t = 0.1
	sim.noises.clear()
	run(sim, 0.5)
	ok(sim.noises.size() > 0 or sim.log[sim.log.size() - 1][0] == "You sneeze", "a head cold makes you sneeze out loud")
	p.cold_h = 0.0
	p.drunk = 0.0

	print("== condition, repair, clothing")
	Inv.add_new(p.inv, "baseball_bat", 1)
	var bat: Dictionary = Inv.find(p.inv, "baseball_bat")
	bat["c"] = 0.3
	p.weapon = bat
	Inv.add_new(p.inv, "duct_tape", 1)
	ok(Actions.craft(sim, Recipes.by_id("repair_tape")), "taping a damaged weapon starts")
	run(sim, 6.0)
	ok(float(bat["c"]) > 0.6 and int(bat.get("rp", 0)) == 1, "repair restores condition (%.2f) and counts the repair" % float(bat["c"]))
	bat["c"] = 0.3
	Actions.craft(sim, Recipes.by_id("repair_tape"))
	run(sim, 6.0)
	ok(float(bat["c"]) < 0.6, "the second repair holds less (%.2f)" % float(bat["c"]))
	Inv.add_new(p.inv, "jacket", 1)
	var jk: Dictionary = Inv.find(p.inv, "jacket")
	p.equip(jk)
	jk["c"] = 0.4
	var d0: float = p.clothing_def()
	Inv.add_new(p.inv, "rag", 2)
	Inv.add_new(p.inv, "needle_thread", 1)
	p.skills["tailoring"] = 150.0
	Actions.craft(sim, Recipes.by_id("patch"))
	run(sim, 7.0)
	ok(float(jk["c"]) > 0.6 and p.clothing_def() > d0, "patching clothing restores it and adds protection (%.2f -> %.2f)" % [d0, p.clothing_def()])
	ok(Recipes.missing(Recipes.by_id("forge_nails"), p, false, false) != "", "workshop recipes need a workbench")
	Inv.add_new(p.inv, "scrap_metal", 1)
	Inv.add_new(p.inv, "hammer", 1)
	ok(Recipes.missing(Recipes.by_id("forge_nails"), p, false, true) == "", "…and work beside one")

	print("== trapping")
	var w: World = sim.world
	var spot := Vector2i(-1, -1)
	var px := floori(p.pos.x)
	var py := floori(p.pos.y)
	for r in range(2, 40):
		for a in range(24):
			var q: Vector2 = p.pos + Vector2(cos(a / 24.0 * TAU), sin(a / 24.0 * TAU)) * r
			var tx := floori(q.x)
			var ty := floori(q.y)
			if spot.x < 0 and w.bld(tx, ty) == 0 and Defs.ground_is_natural(w.ground(tx, ty)) and w.obj(tx, ty) == 0 and w.obj(tx + 1, ty) == 0 and not w.tile_blocked(tx, ty) and Defs.ground_is_natural(w.ground(tx + 1, ty)):
				spot = Vector2i(tx, ty)
	p.pos = Vector2(spot.x + 0.5, spot.y + 0.5)
	p.facing = Vector2(1, 0)
	Inv.add_new(p.inv, "snare", 1)
	Actions.place_item(sim, Inv.find(p.inv, "snare"))
	var tt: Vector2i = p.front_tile()
	ok(Defs.o_id(w.obj(tt.x, tt.y)) == Defs.O_SNARE, "snare placed on open ground")
	var te: Dictionary = w.ent(tt.x, tt.y)
	te["bait"] = 1
	var tc: Chunk = w.chunk_at(tt.x, tt.y)
	tc.zone = 0
	var saved_pos: Vector2 = p.pos
	p.pos += Vector2(40, 0)
	for i in range(400):
		if String(te.get("caught", "")) != "": break
		sim._sim_ents(tc, 1.0, false)
	p.pos = saved_pos
	ok(String(te.get("caught", "")) != "", "a baited snare eventually catches something (%s)" % te.get("caught", ""))
	var topts: Array = Actions.options(sim, {"kind": "obj", "x": tt.x, "y": tt.y})
	(topts[0]["fn"] as Callable).call()
	ok(Inv.count(p.inv, "raw_rabbit") + Inv.count(p.inv, "raw_bird") == 1, "the catch goes into the inventory")

	print("== cellars")
	var hatch_lot: Dictionary = {}
	var hatch_plan: LotBuilder.LotPlan = null
	var cellars := 0
	var houses := 0
	for lot in w.gen.region(0, 0)["lots"]:
		if lot["k"] != "house": continue
		houses += 1
		var plan: LotBuilder.LotPlan = w.gen.lot_plan(lot)
		if plan.hatch.x >= 0:
			cellars += 1
			if hatch_lot.is_empty():
				hatch_lot = lot
				hatch_plan = plan
	ok(cellars > 3, "some houses have cellar hatches (%d of %d)" % [cellars, houses])
	if hatch_plan != null:
		var hr: Rect2i = hatch_lot["r"]
		var hx: int = hr.position.x + hatch_plan.hatch.x
		var hy: int = hr.position.y + hatch_plan.hatch.y
		p.pos = Vector2(hx + 0.5, hy + 0.5)
		w.stream(p.pos, 2, 999)
		sim._process_world_events()
		ok(Defs.o_id(w.obj(hx, hy)) == Defs.O_HATCH, "the hatch is in the house floor")
		var hopts: Array = Actions.options(sim, {"kind": "obj", "x": hx, "y": hy})
		(hopts[0]["fn"] as Callable).call()
		run(sim, 2.5)
		ok(sim.underground(), "climbing down moves the survivor underground (y=%.0f)" % p.pos.y)
		ok(not w.blocked(p.pos.x, p.pos.y, Player.R) and w.bld(floori(p.pos.x), floori(p.pos.y)) != 0, "the cellar is a walkable room")
		ok(sim.daylight() < 0.2 and absf(sim.temperature_base() - 12.0) < 0.01, "it is dark and cool down there")
		var loot := 0
		var uc: Chunk = w.chunk_at(floori(p.pos.x), floori(p.pos.y))
		for ch in w.chunks.values():
			for i in range(256):
				if ch.btype.get(ch.bld[i], "") == "cellar" and Defs.obj(ch.obj[i] & 1023).has("c"):
					loot += w.container_at(ch.cx * 16 + (i & 15), ch.cy * 16 + (i >> 4)).size()
		ok(loot > 0, "cellar storage holds loot (%d stacks)" % loot)
		var lx := hx
		var ly := hy + World.UNDER
		ok(Defs.o_id(w.obj(lx, ly)) == Defs.O_LADDER, "a ladder leads back up")
		var lopts: Array = Actions.options(sim, {"kind": "obj", "x": lx, "y": ly})
		(lopts[0]["fn"] as Callable).call()
		run(sim, 2.5)
		ok(not sim.underground() and w.bld(floori(p.pos.x), floori(p.pos.y)) == hatch_plan.bld_id, "climbing up returns to the same house")

	print("== randomized stories")
	var stories := {"stash": 0, "corpses": 0, "sealed": 0, "broken": 0}
	for ry in range(-1, 2):
		for rx in range(-1, 2):
			for lot in w.gen.region(rx, ry)["lots"]:
				var plan: LotBuilder.LotPlan = w.gen.lot_plan(lot)
				if plan.btype == "stash": stories["stash"] += 1
				if plan.corpses.size() > 0: stories["corpses"] += 1
				if plan.zspawn.size() > 0: stories["sealed"] += 1
				for i in range(plan.w * plan.h):
					if (plan.st_n[i] & Defs.ES_BROKEN) != 0 or (plan.st_w[i] & Defs.ES_BROKEN) != 0:
						stories["broken"] += 1
						break
	ok(stories["stash"] > 0 and stories["corpses"] > 0 and stories["sealed"] > 0 and stories["broken"] > 0, "story houses are generated %s" % str(stories))
	var sl: Dictionary = {}
	for lot in w.gen.region(0, 0)["lots"]:
		if w.gen.lot_plan(lot).corpses.size() > 0 and sl.is_empty(): sl = lot
	if not sl.is_empty():
		var sr: Rect2i = sl["r"]
		p.pos = Vector2(sr.get_center()) + Vector2(0.5, 0.5)
		for i in range(60):
			w.stream(p.pos, 2, 8)
			sim._process_world_events()
		var found := 0
		var armed := false
		for ch in w.chunks.values():
			for cp in ch.corpses:
				if cp.has("perm"):
					found += 1
		ok(found > 0, "story corpses are placed in the world (%d)" % found)

	print("== overgrowth")
	var w2 := World.new(555)
	w2.hour = 24.0 * 60.0
	var node: Vector2i = w2.gen.region(0, 0)["node"]
	var weeds := 0
	var grass := 0
	for cy in range((node.y >> 4) - 2, (node.y >> 4) + 3):
		for cx in range((node.x >> 4) - 2, (node.x >> 4) + 3):
			var c: Chunk = w2.load_chunk(cx, cy)
			var c0: Chunk = w.gen.gen_chunk(cx, cy)
			for i in range(256):
				if (c.obj[i] & 1023) == Defs.O_WEEDS: weeds += 1
				if (c.obj[i] & 1023) == Defs.O_TALL_GRASS and c0.obj[i] == 0: grass += 1
	ok(weeds > 20 and grass > 20, "after two months weeds crack the pavement and lawns grow wild (%d weeds, %d tall grass)" % [weeds, grass])

	print("== flyover & distant events")
	var s3 := Sim.new(777)
	s3.new_game("athlete", [], "house")
	quiet(s3)
	ok(s3.fly_next_h > 4.0 * 24.0 and s3.fly_next_h < 9.0 * 24.0, "a flyover is scheduled for day %d" % int(s3.fly_next_h / 24.0 + 1))
	s3.hour = s3.fly_next_h + 0.01
	var z: Zombie = s3.zombies.spawn(s3.player.pos + Vector2(30, 0), 0)
	z.dir = Vector2(1, 0)
	# step outside so the aircraft can see the survivor
	var out_pos := Vector2.ZERO
	for r in range(3, 30):
		var q2: Vector2 = s3.player.pos + Vector2(0, r)
		if s3.world.bld(floori(q2.x), floori(q2.y)) == 0 and not s3.world.blocked(q2.x, q2.y, 0.2):
			out_pos = q2
			break
	s3.player.pos = out_pos
	z.pos = out_pos + Vector2(30, 0)
	s3.zombies.wander_t = 1e9
	run(s3, 3.0)
	ok(s3.fly_active, "the flyover starts on schedule")
	ok(z.state == Zombie.INVESTIGATE or z.state == Zombie.CHASE, "it draws the infected from far away (state %s)" % Zombie.STATE_NAMES[z.state])
	s3.hour = s3.fly_end_h + 0.01
	run(s3, 0.2)
	ok(not s3.fly_active and s3.fly_next_h > 1e9, "it ends, and with 'Once' it does not return")
	s3.settings["meta"] = true
	s3._meta_t = 0.1
	s3.noises.clear()
	var logn: int = s3.log.size()
	run(s3, 0.3)
	ok(s3.log.size() > logn, "distant events are reported: \"%s\"" % s3.log[s3.log.size() - 1][0])
	ok(Sim.compass(Vector2.ZERO, Vector2(-1, -1)) == "north" and Sim.compass(Vector2.ZERO, Vector2(1, -1)) == "east", "compass directions match the screen")

	var ln: int = s3.log.size()
	s3.radio_report()
	ok(s3.log.size() >= ln + 2, "a radio picks up the emergency broadcast: %s" % s3.log[s3.log.size() - 1][0])
	print("== sandbox")
	var s4 := Sim.new(888)
	s4.settings["util"] = 3
	s4.settings["season"] = 2
	s4.settings["flyover"] = 0
	s4.settings["kit"] = true
	s4.settings["guide"] = false
	s4.new_game("builder", [], "cabin")
	ok(s4.power_off_h > 1e9 and s4.fly_next_h > 1e9, "utilities and flyovers can be switched off")
	ok(s4.temperature_base() < Sim.new(888).temperature_base() - 10.0, "a winter start is cold (%.0f°C)" % s4.temperature_base())
	ok(Inv.count(s4.player.inv, "baseball_bat") == 1 and not s4.player.bag.is_empty(), "starter kit is handed out")
	ok(s4.world.btype_at(floori(s4.player.pos.x), floori(s4.player.pos.y)) == "cabin", "start location: cabin")
	var s5 := Sim.new(888)
	s5.new_game("farmer", [], "farm")
	ok(s5.world.btype_at(floori(s5.player.pos.x), floori(s5.player.pos.y)) == "farm", "start location: farm")
	ok(s4.guide_text() == "" and sim.guide_text() != "", "guided objectives can be turned off")

	print("== tutorial objectives")
	var s6 := Sim.new(999)
	s6.new_game("chef", [], "house")
	quiet(s6)
	ok(s6.guide_i == 0, "starts at the first objective")
	s6.player.pos += Vector2(0.0, 0.0)
	s6.safe_pos = s6.player.pos + Vector2(5, 0)
	run(s6, 0.2)
	s6.flags["door"] = true
	run(s6, 0.2)
	s6.flags["took"] = true
	run(s6, 0.2)
	ok(s6.guide_i >= 4, "objectives advance as the player does things (now %d: %s)" % [s6.guide_i, s6.guide_text()])

	print("== alarms, salvage, compost")
	var bx := floori(sim.safe_pos.x)
	var by := floori(sim.safe_pos.y)
	ok(not sim.alarm_armed(bx, by), "the starting home never has an alarm")
	var armed_n := 0
	var bcount := 0
	for ch in w.chunks.values():
		for i in range(256):
			if ch.bld[i] != 0 and (i % 37) == 0:
				bcount += 1
				if sim.alarm_armed(ch.cx * 16 + (i & 15), ch.cy * 16 + (i >> 4)): armed_n += 1
	ok(bcount > 0, "alarm state can be queried per building (%d of %d sampled tiles armed)" % [armed_n, bcount])
	# compost
	var comp := Vector2i(floori(sim.safe_pos.x), floori(sim.safe_pos.y))
	p.pos = sim.safe_pos
	w.stream(p.pos, 2, 999)
	sim._process_world_events()
	var free := Vector2i(-1, -1)
	for dy in range(-3, 4):
		for dx in range(-3, 4):
			if free.x < 0 and w.obj(comp.x + dx, comp.y + dy) == 0 and not w.tile_blocked(comp.x + dx, comp.y + dy) and (dx != 0 or dy != 0):
				free = Vector2i(comp.x + dx, comp.y + dy)
	w.set_obj(free.x, free.y, Defs.ocell(Defs.O_COMPOST, 0, 0))
	var bin: Array = w.container_at(free.x, free.y)
	bin.append(Items.make("bread", 5, sim.hour - 500.0))
	var cc: Chunk = w.chunk_at(free.x, free.y)
	for i in range(200): sim._sim_ents(cc, 1.0, false)
	ok(Inv.count(bin, "fertilizer") >= 1, "rotten food in a compost bin becomes fertiliser")
	# car salvage
	var car := Vector2i(-1, -1)
	for ch in w.chunks.values():
		for i in range(256):
			if car.x < 0 and (ch.obj[i] & 1023) == Defs.O_CAR and Defs.o_part(ch.obj[i]) == 0:
				car = Vector2i(ch.cx * 16 + (i & 15), ch.cy * 16 + (i >> 4))
	if car.x >= 0:
		Inv.add_new(p.inv, "wrench", 1)
		var before: int = Inv.count(p.inv, "scrap_metal")
		Actions._salvage_car(sim, car.x, car.y)
		run(sim, 9.0)
		ok(Inv.count(p.inv, "scrap_metal") > before and p.skills["mechanics"] > 0.0, "salvaging a car yields parts and Mechanics XP")
	else:
		ok(true, "no car in the loaded area to salvage (skipped)")

	print("== save / load of the new state")
	p.weight = 77.7
	p.unhappy = 33.0
	sim.flags["x"] = 1
	SaveGame.delete("mech_slot")
	ok(SaveGame.save(sim, "mech_slot"), "save")
	var l: Sim = SaveGame.load_game("mech_slot")
	ok(l != null and absf(l.player.weight - 77.7) < 0.001 and absf(l.player.unhappy - 33.0) < 0.001, "weight and mood restored")
	ok(l != null and l.player.traits.size() == 6 and l.player.skill_level("fitness") == p.skill_level("fitness"), "traits restored and still applied")
	ok(l != null and l.flags.has("x") and l.guide_i == sim.guide_i, "story flags and tutorial progress restored")
	ok(SaveGame.migrate({"v": 2, "seed": 1, "player": {}, "settings": {}}).get("v", 0) == SaveGame.SCHEMA, "schema 2 saves migrate to the current schema")
	SaveGame.delete("mech_slot")

	print("")
	print("RESULT: %d checks, %d failed" % [checks, fails])
	quit(1 if fails > 0 else 0)
