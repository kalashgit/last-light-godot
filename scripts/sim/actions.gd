class_name Actions
extends RefCounted
## Context interactions between the player and the world: doors, windows, containers,
## furniture, trees, water, farming, building and crafting.

# ------------------------------------------------------------------ target discovery
## returns interaction targets near the player, best first.
const HEAVY := [Defs.O_FRIDGE, Defs.O_STOVE, Defs.O_FREEZER, Defs.O_VENDING, Defs.O_GUN_LOCKER, Defs.O_WASHER, Defs.O_WORKBENCH, Defs.O_METAL_SHELF, Defs.O_MED_CABINET]
const LIGHT_MOVABLE := [Defs.O_LAMP, Defs.O_PLANT, Defs.O_STOOL, Defs.O_HAY, Defs.O_RAIN_BARREL, Defs.O_STOVE, Defs.O_SPIKES]

static func targets(sim: Sim) -> Array:
	var p: Player = sim.player
	var w: World = sim.world
	var px: int = floori(p.pos.x)
	var py: int = floori(p.pos.y)
	var f: Vector2 = p.facing
	var out: Array = []
	# edges of the player's tile
	var edges: Array = [
		[px, py, 0, Vector2(0, -1), p.pos.y - py], [px, py + 1, 0, Vector2(0, 1), py + 1 - p.pos.y],
		[px, py, 1, Vector2(-1, 0), p.pos.x - px], [px + 1, py, 1, Vector2(1, 0), px + 1 - p.pos.x]]
	for e in edges:
		var wid: int = w.wall(e[0], e[1], e[2])
		if wid == 0:
			continue
		var shape: int = wid & 3
		var st: int = w.edge_state(e[0], e[1], e[2])
		var fence: bool = Defs.wall_is_fence(wid)
		if shape == Defs.WS_SOLID and not fence and (st & Defs.ES_PLANK_MASK) == 0 and Defs.wall_mat(wid) != Defs.WM_BUILT_PLANK:
			continue
		if shape == Defs.WS_ARCH:
			continue
		var dist: float = e[4]
		if dist > 0.8:
			continue
		var dv: Vector2 = e[3]
		out.append({"kind": "edge", "x": e[0], "y": e[1], "side": e[2], "dir": dv, "score": f.dot(dv) * 1.2 + (0.9 - dist)})
	# objects / ground items / water around
	for dy in range(-1, 2):
		for dx in range(-1, 2):
			var x: int = px + dx
			var y: int = py + dy
			var c := Vector2(x + 0.5, y + 0.5)
			var to: Vector2 = c - p.pos
			var d: float = to.length()
			var dirv: Vector2 = to / d if d > 0.01 else f
			if (dx != 0 or dy != 0) and not w.los(p.pos.x, p.pos.y, c.x, c.y):
				continue
			var base: float = f.dot(dirv) * 0.8 + (1.6 - d) * 0.5
			var cell: int = w.obj(x, y)
			if cell != 0:
				var od: Dictionary = Defs.obj(Defs.o_id(cell))
				if od.has("c") or od.has("use") or od.has("scrap"):
					out.append({"kind": "obj", "x": x, "y": y, "score": base + (0.25 if od.has("c") or od.has("use") else -0.4)})
			if not w.items_at(x, y).is_empty():
				out.append({"kind": "ground", "x": x, "y": y, "score": base + 0.1 - (0.3 if dx != 0 or dy != 0 else 0.0)})
			var g: int = w.ground(x, y)
			if Defs.ground_is_water(g) and (dx == 0 or dy == 0):
				out.append({"kind": "water", "x": x, "y": y, "score": base - 0.2})
			elif g == Defs.G_SOIL and cell == 0 and (dx == 0 or dy == 0):
				out.append({"kind": "soil", "x": x, "y": y, "score": base - 0.3})
			elif g == Defs.G_SAND and dx == 0 and dy == 0 and Inv.has_tag(p.inv, "dig"):
				out.append({"kind": "sand", "x": x, "y": y, "score": base - 0.6})
	# corpses
	for cy in range((py - 2) >> 4, ((py + 2) >> 4) + 1):
		for cx in range((px - 2) >> 4, ((px + 2) >> 4) + 1):
			var ch: Chunk = w.chunk(cx, cy)
			if ch == null:
				continue
			for cp in ch.corpses:
				var cpos := Vector2(cp["x"], cp["y"])
				var d2: float = cpos.distance_to(p.pos)
				if d2 < 1.3:
					out.append({"kind": "corpse", "corpse": cp, "x": floori(cpos.x), "y": floori(cpos.y), "score": 0.6 - d2 * 0.3 + f.dot((cpos - p.pos).normalized()) * 0.3})
	# a fire within reach
	var best_fire := Vector2i(-99999, 0)
	var bfd := 1.8
	for bk in sim.burning.keys():
		var fdd: float = Vector2(bk.x + 0.5, bk.y + 0.5).distance_to(p.pos)
		if fdd < bfd:
			bfd = fdd
			best_fire = bk
	if best_fire.x != -99999:
		out.append({"kind": "fire_tile", "x": best_fire.x, "y": best_fire.y, "score": 2.0})
	var nn = sim.npcs.nearest(p.pos, 1.7)
	if nn != null and nn.state != NpcSim.HOSTILE:
		out.append({"kind": "npc", "npc": nn, "x": floori(nn.pos.x), "y": floori(nn.pos.y), "score": 0.75 + f.dot((nn.pos - p.pos).normalized()) * 0.5})
	out.sort_custom(func(a, b): return float(a["score"]) > float(b["score"]))
	return out

static func target_name(sim: Sim, t: Dictionary) -> String:
	var w: World = sim.world
	match t["kind"]:
		"edge":
			var wid: int = w.wall(t["x"], t["y"], t["side"])
			var shape: int = wid & 3
			if Defs.wall_is_fence(wid):
				return "Gate" if shape == Defs.WS_DOOR else String(Defs.WALL_MATS[wid >> 2][3]).capitalize()
			return ["Wall", "Window", "Door", "Doorway"][shape]
		"obj":
			return Defs.obj(Defs.o_id(w.obj(t["x"], t["y"]))).get("n", "Object")
		"ground": return "Items on the ground"
		"water": return "Water"
		"soil": return "Tilled soil"
		"sand": return "Sand"
		"corpse": return "Corpse"
		"npc": return String(t["npc"].name)
		"fire_tile": return "Fire"
	return ""

# ------------------------------------------------------------------ options
static func _opt(label: String, fn: Callable) -> Dictionary:
	return {"label": label, "fn": fn}

static func options(sim: Sim, t: Dictionary) -> Array:
	match t["kind"]:
		"edge": return _edge_options(sim, t)
		"obj": return _obj_options(sim, t)
		"ground": return [_opt("Pick up items", func(): sim.ui_events.append({"type": "loot"}))]
		"corpse": return _corpse_options(sim, t)
		"water": return _water_options(sim, t)
		"soil": return _soil_options(sim, t)
		"sand": return [_opt("Dig sand", func(): _dig(sim, "sand"))]
		"npc": return sim.npcs.options(t["npc"])
		"fire_tile": return _fire_fight_options(sim, t["x"], t["y"])
	return []

## press of the INTERACT button. full_menu = long press.
static func interact(sim: Sim, full_menu: bool = false) -> void:
	var p: Player = sim.player
	if not p.alive:
		return
	if p.sleeping:
		sim.wake("You get up.")
		return
	if p.hidden:
		leave_hiding(sim)
		return
	if sim.vehicle != null:
		if full_menu:
			sim.ui_events.append({"type": "menu", "title": "The %s" % String(sim.vehicle.spec()["n"]), "options": vehicle_menu(sim)})
		else:
			exit_vehicle(sim)
		return
	if not p.dragging.is_empty():
		_drop_corpse(sim)
		return
	if not p.carrying.is_empty():
		place_carried(sim)
		return
	var ts: Array = targets(sim)
	if ts.is_empty():
		sim.say("Nothing to interact with here", Color(0.7, 0.7, 0.7))
		return
	var t: Dictionary = ts[0]
	# holding USE with several things in reach: first choose which one
	if full_menu:
		var distinct: Array = []
		var names_seen: Dictionary = {}
		for tt in ts:
			var nm: String = target_name(sim, tt)
			var key: String = "%s@%d,%d" % [nm, int(tt.get("x", 0)), int(tt.get("y", 0))]
			if names_seen.has(key) or options(sim, tt).is_empty():
				continue
			names_seen[key] = true
			distinct.append(tt)
			if distinct.size() >= 6:
				break
		if distinct.size() > 1:
			var pick: Array = []
			for tt2 in distinct:
				var target: Dictionary = tt2
				var lbl: String = target_name(sim, target)
				if target["kind"] == "edge" or target["kind"] == "obj":
					lbl += " (%s)" % Sim.compass(p.pos, Vector2(float(target["x"]) + 0.5, float(target["y"]) + 0.5)) if Vector2(float(target["x"]) + 0.5, float(target["y"]) + 0.5).distance_to(p.pos) > 0.6 else ""
				pick.append(_opt(lbl, func(): sim.ui_events.append({"type": "menu", "title": target_name(sim, target), "options": options(sim, target)})))
			sim.ui_events.append({"type": "menu", "title": "What do you want to use?", "options": pick})
			return
	var opts: Array = options(sim, t)
	if opts.is_empty():
		return
	if opts.size() == 1 or (not full_menu and t["kind"] == "edge" and opts[0].get("quick", false)):
		(opts[0]["fn"] as Callable).call()
	else:
		sim.ui_events.append({"type": "menu", "title": target_name(sim, t), "options": opts})

# ------------------------------------------------------------------ edges
static func _other_side(sim: Sim, x: int, y: int, side: int) -> Vector2i:
	var px: int = floori(sim.player.pos.x)
	var py: int = floori(sim.player.pos.y)
	if side == 1:
		return Vector2i(x - 1 if px >= x else x, py)
	return Vector2i(px, y - 1 if py >= y else y)

static func _edge_options(sim: Sim, t: Dictionary) -> Array:
	var w: World = sim.world
	var p: Player = sim.player
	var x: int = t["x"]
	var y: int = t["y"]
	var side: int = t["side"]
	var wid: int = w.wall(x, y, side)
	var st: int = w.edge_state(x, y, side)
	var shape: int = wid & 3
	var fence: bool = Defs.wall_is_fence(wid)
	var planks: int = (st & Defs.ES_PLANK_MASK) >> Defs.ES_PLANK_SHIFT
	var out: Array = []
	var other: Vector2i = _other_side(sim, x, y, side)
	var inside: bool = w.bld(floori(p.pos.x), floori(p.pos.y)) != 0
	if shape == Defs.WS_DOOR:
		var open: bool = (st & Defs.ES_OPEN) != 0
		var broken: bool = (st & Defs.ES_BROKEN) != 0
		if not broken and planks == 0:
			if open:
				var o: Dictionary = _opt("Close", func(): _toggle_door(sim, x, y, side))
				o["quick"] = true
				out.append(o)
			elif (st & Defs.ES_LOCKED) != 0 and not inside:
				var o2: Dictionary = _opt("Locked — try the door", func():
					sim.say("Locked. Break a window, pry it open, or bash it down.", Color(1.0, 0.85, 0.6))
					sim.emit_fx("locked", p.pos))
				o2["quick"] = true
				out.append(o2)
				if Inv.has_tag(p.inv, "crowbar"):
					out.append(_opt("Pry open with crowbar", func():
						p.start_action("Prying door", 4.5, func():
							w.set_edge_state(x, y, side, (st & ~Defs.ES_LOCKED) | Defs.ES_OPEN)
							sim.noise(p.pos, 12.0)
							sim.emit_fx("door", p.pos))))
			else:
				var o3: Dictionary = _opt("Open", func():
					if sim.door_jammed(x, y, side):
						sim.say("It won't budge — swollen in the frame. Force it?", Color(1.0, 0.85, 0.6))
						sim.emit_fx("locked", p.pos)
						return
					_toggle_door(sim, x, y, side))
				o3["quick"] = true
				out.append(o3)
				if not fence and inside:
					if (st & Defs.ES_LOCKED) != 0:
						out.append(_opt("Unlock", func(): w.set_edge_state(x, y, side, st & ~Defs.ES_LOCKED)))
					else:
						out.append(_opt("Lock", func(): w.set_edge_state(x, y, side, st | Defs.ES_LOCKED)))
	elif shape == Defs.WS_WINDOW:
		var wopen: bool = (st & Defs.ES_OPEN) != 0
		var wbroken: bool = (st & Defs.ES_BROKEN) != 0
		if planks == 0:
			if wopen or wbroken:
				out.append(_opt("Climb through", func(): _climb(sim, x, y, side, 1.6, wbroken)))
			if not wbroken:
				out.append(_opt("Close window" if wopen else "Open window", func():
					w.set_edge_state(x, y, side, st ^ Defs.ES_OPEN)
					sim.emit_fx("door", p.pos)
					sim.noise(p.pos, 3.0)))
				if not wopen:
					out.append(_opt("Smash window", func():
						w.damage_edge(x, y, side, 999.0)
						sim.emit_fx("glass", p.pos)
						sim.noise(p.pos, 16.0)
						if p.weapon.is_empty() and randf() < 0.4:
							p.add_wound(9 + randi() % 2, "glass" if randf() < 0.3 else "scratch", "broken glass")))
			if wbroken and Inv.count(p.inv, "glass_pane") > 0:
				out.append(_opt("Fit a new pane of glass", func():
					p.start_action("Glazing", 6.0, func():
						if Inv.take(p.inv, "glass_pane", 1):
							w.set_edge_state(x, y, side, w.edge_state(x, y, side) & ~Defs.ES_BROKEN)
							p.add_xp("glassmaking", 20.0)
							p.add_xp("carpentry", 6.0))))
			if (st & Defs.ES_CURTAIN) == 0 and Inv.count(p.inv, "sheet") > 0:
				out.append(_opt("Hang sheet as curtain", func():
					if Inv.take(p.inv, "sheet", 1):
						w.set_edge_state(x, y, side, st | Defs.ES_CURTAIN)))
			elif (st & Defs.ES_CURTAIN) != 0:
				out.append(_opt("Take down curtain", func():
					w.set_edge_state(x, y, side, st & ~Defs.ES_CURTAIN)
					Inv.add(p.inv, Items.make("sheet", 1))))
	elif fence and shape == Defs.WS_SOLID:
		var tex: int = Defs.WALL_MATS[wid >> 2][0]
		if tex == Defs.WT_CHAIN:
			out.append(_opt("Climb fence", func(): _climb(sim, x, y, side, 3.0, false)))
		elif tex == Defs.WT_HEDGE:
			out.append(_opt("Push through hedge", func(): _climb(sim, x, y, side, 2.2, false)))
		else:
			var oh: Dictionary = _opt("Hop over", func(): _climb(sim, x, y, side, 0.8, false))
			oh["quick"] = true
			out.append(oh)
	if shape == Defs.WS_DOOR and (st & (Defs.ES_OPEN | Defs.ES_BROKEN)) == 0 and not fence:
		out.append(_opt("Peek through the gap", func(): _peek(sim, x, y, side)))
		if sim.door_jammed(x, y, side):
			out.append(_opt("Force the stuck door", func():
				p.start_action("Shouldering the door", 3.0 if not Inv.has_tag(p.inv, "crowbar") else 1.5, func():
					sim.noise(p.pos, 9.0)
					p.endurance = maxf(0.0, p.endurance - 12.0)
					if Inv.has_tag(p.inv, "crowbar") or randf() < 0.35 + p.skill_level("strength") * 0.06:
						sim.unjammed["%d,%d,%d" % [x, y, side]] = true
						_toggle_door(sim, x, y, side)
						sim.say("It gives with a crack.", Color(0.8, 0.85, 0.9))
					else:
						sim.say("Not yet. Again?", Color(0.9, 0.8, 0.6)))))
	# alarms: an electrician can find and cut them from outside
	if not fence and (shape == Defs.WS_DOOR or shape == Defs.WS_WINDOW) and not inside and Inv.has_tag(p.inv, "screwdriver"):
		var tb: Vector2i = other
		if w.bld(tb.x, tb.y) != 0 and not sim.alarms_done.has(w.bld(tb.x, tb.y)):
			out.append(_opt("Check for an alarm", func():
				p.start_action("Inspecting the frame", 4.0, func():
					var b: int = w.bld(tb.x, tb.y)
					var lvl: int = p.skill_level("electrical")
					if not sim.alarm_armed(tb.x, tb.y):
						sim.alarms_done[b] = true
						sim.say("No alarm on this building", Color(0.75, 0.9, 0.7))
						p.add_xp("electrical", 4.0)
					elif randf() < 0.35 + lvl * 0.13:
						sim.alarms_done[b] = true
						sim.say("You find the sensor wire and cut it. Alarm disarmed.", Color(0.75, 0.9, 0.7))
						p.add_xp("electrical", 30.0)
					elif randf() < 0.3:
						sim.alarms_done[b] = true
						sim.alarms.append([p.pos, 28.0])
						sim.say("You trip the alarm!", Color(1.0, 0.5, 0.4))
						sim.emit_fx("alarm", p.pos)
					else:
						sim.say("There is an alarm, but you cannot get at the wiring. Try again.", Color(1.0, 0.85, 0.6))
						p.add_xp("electrical", 8.0))))
	# barricading (doors, windows)
	if not fence and (shape == Defs.WS_DOOR or shape == Defs.WS_WINDOW):
		if planks < 4 and Inv.count(p.inv, "plank") >= 1 and Inv.count(p.inv, "nails") >= 2 and Inv.has_tag(p.inv, "hammer"):
			out.append(_opt("Barricade (1 plank, 2 nails)", func():
				p.start_action("Barricading", 3.0 - p.skill_level("carpentry") * 0.15, func():
					if Inv.count(p.inv, "plank") < 1 or Inv.count(p.inv, "nails") < 2:
						return
					Inv.take(p.inv, "plank", 1)
					Inv.take(p.inv, "nails", 2)
					var cur: int = w.edge_state(x, y, side)
					var n: int = ((cur & Defs.ES_PLANK_MASK) >> Defs.ES_PLANK_SHIFT) + 1
					w.set_edge_state(x, y, side, (cur & ~Defs.ES_PLANK_MASK & ~Defs.ES_OPEN) | (n << Defs.ES_PLANK_SHIFT))
					sim.noise(p.pos, 13.0)
					sim.emit_fx("build", p.pos)
					p.add_xp("carpentry", 10.0))))
		if planks == 0 and Inv.count(p.inv, "scrap_metal") >= 3 and Inv.count(p.inv, "nails") >= 4 and Inv.has_tag(p.inv, "hammer"):
			out.append(_opt("Barricade with sheet metal (3 scrap, 4 nails)", func():
				p.start_action("Fixing sheet metal", 6.0, func():
					if Inv.count(p.inv, "scrap_metal") < 3 or Inv.count(p.inv, "nails") < 4:
						return
					Inv.take(p.inv, "scrap_metal", 3)
					Inv.take(p.inv, "nails", 4)
					var cur2: int = w.edge_state(x, y, side)
					w.set_edge_state(x, y, side, (cur2 & ~Defs.ES_PLANK_MASK & ~Defs.ES_OPEN) | (4 << Defs.ES_PLANK_SHIFT))
					sim.noise(p.pos, 15.0)
					sim.emit_fx("build", p.pos)
					p.add_xp("metalworking", 18.0))))
		if planks > 0 and (Inv.has_tag(p.inv, "hammer") or Inv.has_tag(p.inv, "crowbar")):
			out.append(_opt("Remove a plank", func():
				p.start_action("Removing plank", 2.5, func():
					var cur: int = w.edge_state(x, y, side)
					var n: int = (cur & Defs.ES_PLANK_MASK) >> Defs.ES_PLANK_SHIFT
					if n <= 0:
						return
					w.set_edge_state(x, y, side, (cur & ~Defs.ES_PLANK_MASK) | ((n - 1) << Defs.ES_PLANK_SHIFT))
					Inv.add(p.inv, Items.make("plank", 1))
					sim.noise(p.pos, 8.0))))
	# player-built structures can be dismantled
	if Defs.wall_mat(wid) == Defs.WM_BUILT_PLANK or (Defs.wall_mat(wid) == Defs.WM_PICKET and Inv.has_tag(p.inv, "hammer")):
		if Inv.has_tag(p.inv, "hammer"):
			out.append(_opt("Dismantle", func():
				p.start_action("Dismantling", 4.0, func():
					w.set_wall(x, y, side, 0)
					Inv.add(p.inv, Items.make("plank", 1 + (1 if p.skill_level("carpentry") >= 2 else 0)))
					sim.noise(p.pos, 10.0)
					p.add_xp("carpentry", 5.0))))
	return out

static func _toggle_door(sim: Sim, x: int, y: int, side: int) -> void:
	var w: World = sim.world
	var st: int = w.edge_state(x, y, side)
	if (st & Defs.ES_OPEN) != 0:
		# don't close on top of something standing in the doorway? (edges are thin: always fine)
		w.set_edge_state(x, y, side, st & ~Defs.ES_OPEN)
	else:
		w.set_edge_state(x, y, side, (st | Defs.ES_OPEN) & ~Defs.ES_LOCKED)
	sim.emit_fx("door", sim.player.pos)
	sim.flags["door"] = true
	sim.noise(sim.player.pos, 2.0 if sim.player.sneaking else 4.0)

static func _climb(sim: Sim, x: int, y: int, side: int, dur: float, glass: bool) -> void:
	var p: Player = sim.player
	var w: World = sim.world
	var o: Vector2i = _other_side(sim, x, y, side)
	if w.tile_blocked(o.x, o.y):
		sim.say("Something blocks the other side", Color(0.9, 0.8, 0.6))
		return
	if p.over_weight() > 6.0:
		sim.say("You are carrying too much to climb", Color(0.9, 0.8, 0.6))
		return
	p.start_action("Climbing", dur * (1.3 if p.fatigue > 70.0 else 1.0), func():
		if w.tile_blocked(o.x, o.y):
			return
		p.pos = Vector2(o.x + 0.5, o.y + 0.5)
		p.endurance = maxf(0.0, p.endurance - dur * 5.0)
		sim.noise(p.pos, 5.0)
		sim.emit_fx("step", p.pos)
		if glass and randf() < 0.22:
			p.add_wound([7, 8, 9, 10, 11, 12, 13, 14][randi() % 8], "glass" if randf() < 0.4 else "scratch", "broken glass")
		elif dur > 2.0 and randf() < 0.03 + p.over_weight() * 0.02:
			p.add_wound(13 + randi() % 2, "fracture", "bad landing")
		p.add_xp("fitness", 2.0))

# ------------------------------------------------------------------ objects
static func _obj_options(sim: Sim, t: Dictionary) -> Array:
	var w: World = sim.world
	var p: Player = sim.player
	var x: int = t["x"]
	var y: int = t["y"]
	var cell: int = w.obj(x, y)
	var id: int = Defs.o_id(cell)
	var d: Dictionary = Defs.obj(id)
	var a: Vector2i = w.anchor_of(x, y)
	var use: String = d.get("use", "")
	var out: Array = []
	if d.has("c"):
		out.append(_opt("Search %s" % String(d["n"]).to_lower(), func(): sim.ui_events.append({"type": "loot", "focus": a})))
	if id == Defs.O_WARDROBE or id == Defs.O_LOCKER:
		out.append(_opt("Hide inside", func(): hide_in(sim, a.x, a.y)))
	match use:
		"bed":
			out.append(_opt("Sleep", func(): sim.start_sleep(1.0 if id != Defs.O_SOFA and id != Defs.O_BEDROLL else 0.8)))
			if sim.home.is_empty() or Vector2(float(sim.home["x"]), float(sim.home["y"])).distance_to(Vector2(x, y)) > 3.0:
				out.append(_opt("Make this place your shelter", func():
					sim.set_home(Vector2(x + 0.5, y + 0.5))
					sim.say("This is home now. Survivors you take in will live and store food here.", Color(0.75, 0.9, 0.7))))
			out.append(_opt("Sit and rest", func(): _rest(sim)))
			if id == Defs.O_BEDROLL:
				out.append(_opt("Roll up bedroll", func():
					w.remove_object(x, y)
					Inv.add(p.inv, Items.make("bedroll_item", 1))))
		"rest":
			out.append(_opt("Sit and rest", func(): _rest(sim)))
			out.append(_opt("Sleep (uncomfortable)", func(): sim.start_sleep(0.6)))
		"sink":
			var pb: int = w.bld(a.x, a.y)
			if sim.has_water() and float(sim.weather["temp"]) < -8.0 and not sim.near_heat(Vector2(a.x + 0.5, a.y + 0.5)):
				out.append(_opt("The pipes have frozen", func(): sim.say("Nothing. Warm the house — a fire or a stove nearby — and they will thaw.", Color(0.75, 0.85, 1.0))))
			elif sim.has_water():
				out.append(_opt("Drink", func(): _drink_source(sim, false, 999)))
				out.append(_opt("Fill water containers", func(): _fill(sim, false, 999)))
				out.append(_opt("Wash yourself", func(): _wash(sim, func(n: int) -> int: return n)))
				out.append(_opt("Wash your clothes", func(): _laundry(sim, func(n: int) -> int: return n)))
			elif sim.pipe_water(pb) > 0:
				out.append(_opt("Drink what is left in the pipes (%d)" % sim.pipe_water(pb), func():
					if sim.draw_pipe(pb, 1) > 0: _drink_source(sim, false, 1)))
				out.append(_opt("Drain the pipes into your bottles", func():
					var used: int = _fill(sim, false, sim.pipe_water(pb))
					sim.draw_pipe(pb, used)))
				out.append(_opt("Wash yourself (uses 3)", func(): _wash(sim, func(n: int) -> int: return sim.draw_pipe(pb, n))))
			else:
				# a rain collector beside the fixture can be piped into it
				var barrel := Vector2i(-99999, 0)
				for by in range(a.y - 2, a.y + 3):
					for bx in range(a.x - 2, a.x + 3):
						if Defs.o_id(w.obj(bx, by)) == Defs.O_RAIN_BARREL: barrel = Vector2i(bx, by)
				var pe: Dictionary = w.ent(a.x, a.y)
				if pe.get("k", "") == "plumb" and barrel.x > -99999:
					var be: Dictionary = w.ent(barrel.x, barrel.y)
					out.append(_opt("Drink (piped, filtered rainwater: %d)" % int(be.get("w", 0.0)), func():
						if float(be.get("w", 0.0)) < 1.0:
							sim.say("The collector is empty.", Color(0.8, 0.8, 0.9))
							return
						be["w"] = float(be["w"]) - 1.0
						_drink_source(sim, false, 1)))
					out.append(_opt("Fill water containers", func():
						var took: int = _fill(sim, false, int(be.get("w", 0.0)))
						be["w"] = maxf(0.0, float(be.get("w", 0.0)) - took)))
				elif barrel.x > -99999 and Inv.has_tag(p.inv, "wrench"):
					out.append(_opt("Plumb in the rain collector", func():
						p.start_action("Plumbing", 9.0, func():
							w.set_ent(a.x, a.y, {"k": "plumb"})
							p.add_xp("metalworking", 20.0)
							sim.noise(p.pos, 8.0)
							sim.say("Rainwater now runs to this tap, filtered.", Color(0.75, 0.9, 0.7)))))
				else:
					out.append(_opt("Dry — the water is off", func(): sim.say("Not a drop. A rain collector within two tiles and a wrench would fix that.", Color(0.8, 0.8, 0.9))))
		"stove":
			out.append(_opt("Cook", func(): sim.ui_events.append({"type": "craft", "cat": "Cooking"})))
		"workbench":
			out.append(_opt("Craft", func(): sim.ui_events.append({"type": "craft", "cat": "Carpentry"})))
		"tree":
			if Inv.has_tag(p.inv, "axe"):
				out.append(_opt("Chop down", func(): _chop(sim, x, y)))
			out.append(_opt("Gather branches", func(): _forage(sim, x, y, true)))
		"forage":
			out.append(_opt("Forage", func(): _forage(sim, x, y, false)))
			out.append(_opt("Look for animal tracks", func(): _track(sim)))
		"berries":
			if Defs.o_part(cell) == 0:
				out.append(_opt("Pick berries", func():
					p.start_action("Picking berries", 3.0, func():
						Inv.add(p.inv, Items.make("berries", 2 + randi() % 3 + p.skill_level("foraging") / 3, sim.hour))
						w.set_obj(x, y, Defs.ocell(Defs.O_BERRY_BUSH, 0, 1))
						w.set_ent(x, y, {"k": "berry", "h": sim.hour})
						p.add_xp("foraging", 8.0))))
			out.append(_opt("Forage", func(): _forage(sim, x, y, false)))
		"car":
			out.append_array(_car_options(sim, a.x, a.y))
			if id != Defs.O_BICYCLE:
				out.append(_opt("Siphon fuel", func(): _siphon(sim, a.x, a.y)))
				out.append(_opt("Salvage parts", func(): _salvage_car(sim, a.x, a.y)))
		"gas_pump":
			out.append(_opt("Fill gas can", func():
				if not sim.has_power(x, y):
					sim.say("The pump is dead without power", Color(0.9, 0.8, 0.6))
					return
				_fill_gas(sim, 8)))
		"campfire":
			out.append_array(_fire_options(sim, a.x, a.y))
		"rain_barrel":
			var e: Dictionary = w.ent(x, y)
			var units: int = int(e.get("w", 0.0))
			if e.get("ice", false):
				out.append(_opt("Frozen solid (%d units of ice)" % units, func(): sim.say("It will not thaw until it warms up — or you carry it inside.", Color(0.75, 0.85, 1.0))))
			else:
				out.append(_opt("Drink rainwater (%d left)" % units, func(): _drink_barrel(sim, x, y)))
				out.append(_opt("Fill water containers", func(): _fill_barrel(sim, x, y)))
				out.append(_opt("Wash yourself (uses 3)", func(): _wash(sim, func(n: int) -> int:
					var took: int = mini(n, int(float(e.get("w", 0.0))))
					e["w"] = float(e.get("w", 0.0)) - took
					return took)))
		"generator":
			out.append_array(_gen_options(sim, x, y))
		"crop":
			out.append_array(_crop_options(sim, x, y))
		"trap":
			out.append_array(_trap_options(sim, x, y))
		"kiln":
			out.append(_opt("Use the kiln", func(): sim.ui_events.append({"type": "craft", "cat": "Kiln"})))
		"forge":
			out.append(_opt("Work the forge", func(): sim.ui_events.append({"type": "craft", "cat": "Smithing"})))
		"well":
			out.append(_opt("Draw water and drink", func(): _drink_source(sim, false, 999)))
			out.append(_opt("Fill water containers", func(): _fill(sim, false, 999)))
			out.append(_opt("Wash yourself", func(): _wash(sim, func(n: int) -> int: return n)))
			out.append(_opt("Wash your clothes", func(): _laundry(sim, func(n: int) -> int: return n)))
		"battery_bank":
			var be: Dictionary = w.ent(x, y)
			if be.is_empty():
				be = {"k": "bank", "w": 0.0}
				w.set_ent(x, y, be)
			out.append(_opt("Check the charge", func():
				var lo: int = sim.loads_near(x, y, Sim.BANK_RANGE)
				sim.say("Charge %d%%. %d appliances switched on nearby: about %d hours left." % [int(float(be.get("w", 0.0)) / Sim.BANK_MAX * 100.0), lo, int(float(be.get("w", 0.0)) / maxf(0.5, 0.5 * float(maxi(1, lo))))], Color(0.85, 0.88, 0.8))))
			out.append(_opt("Switch on" if be.get("off", false) else "Switch off", func(): be["off"] = not be.get("off", false)))
		"solar":
			out.append(_opt("Check the panel", func():
				var sun: float = clampf(sim.daylight() * (1.0 - float(sim.weather.get("cloud", 0.0)) * 0.7), 0.0, 1.0)
				var bank := false
				for bdy in range(-6, 7):
					for bdx in range(-6, 7):
						if w.ent(x + bdx, y + bdy).get("k", "") == "bank": bank = true
				sim.say("Output %d%%. %s" % [int(sun * 100.0), "Charging a battery bank." if bank else "No battery bank within six tiles to charge."], Color(0.85, 0.88, 0.8))))
		"sign":
			var se: Dictionary = w.ent(x, y)
			if se.has("txt"):
				out.append(_opt("Read the sign", func():
					sim.say("The sign reads: \"%s\"" % String(se["txt"]), Color(0.86, 0.84, 0.72))
					sim.add_marker(x, y, String(se.get("lab", "A sign")))))
			if not Inv.find(p.inv, "pencil").is_empty() or Inv.has_tag(p.inv, "knife"):
				out.append(_opt("Write on it" if not se.has("txt") else "Write something new", func():
					var txt: String = "Day %d. Someone lived here. %s" % [sim.day(), "Shelter and water inside." if w.bld(floori(p.pos.x), floori(p.pos.y)) != 0 or sim.near_roof(p.pos) else "Keep moving."]
					w.set_ent(x, y, {"k": "sign", "txt": txt, "lab": "Sign left on day %d" % sim.day()})
					sim.say("You write: \"%s\"" % txt, Color(0.8, 0.9, 0.75))))
		"fallen":
			if Inv.has_tag(p.inv, "axe") or Inv.has_tag(p.inv, "saw"):
				out.append(_opt("Cut it up", func():
					p.start_action("Cutting up the tree", 14.0 - p.skill_level("axe") * 0.8, func():
						w.remove_object(a.x, a.y)
						Inv.add_new(p.inv, "log", 2, sim.hour)
						Inv.add_new(p.inv, "branch", 3, sim.hour)
						p.endurance = maxf(0.0, p.endurance - 25.0)
						p.add_xp("axe", 15.0)
						sim.noise(p.pos, 14.0)
						sim.say("The way is clear. Two logs and some branches.", Color(0.75, 0.9, 0.7)))))
			else:
				out.append(_opt("Too big to move without an axe or saw", func(): sim.say("You need an axe or a saw.", Color(0.9, 0.8, 0.6))))
			out.append(_opt("Climb over", func():
				var to: Vector2 = p.pos + p.facing.normalized() * 2.2
				if sim.world.blocked(to.x, to.y, Player.R):
					sim.say("No footing on the other side.", Color(0.9, 0.8, 0.6))
					return
				p.start_action("Climbing over", 2.0, func():
					p.pos = to
					sim.noise(p.pos, 4.0))))
		"spikes":
			out.append(_opt("About the spikes", func(): sim.say("Anything that walks across is torn up. They wear out.", Color(0.85, 0.85, 0.75))))
		"stairs":
			var attic_l: bool = id == Defs.O_ATTIC_LADDER
			if World.level(p.pos.y) == 0:
				out.append(_opt("Climb into the attic" if attic_l else "Go upstairs", func(): _use_stairs(sim, World.UNDER * 2, "Dust and boxes under the rafters." if attic_l else "You climb to the upper floor.")))
			else:
				out.append(_opt("Climb down" if attic_l else "Go downstairs", func(): _use_stairs(sim, -World.UNDER * 2, "You come back down.")))
		"coop":
			out.append_array(_coop_options(sim, x, y))
		"hatch":
			out.append(_opt("Climb down to the cellar", func(): _use_stairs(sim, World.UNDER)))
		"ladder":
			out.append(_opt("Climb up", func(): _use_stairs(sim, -World.UNDER)))
		"compost":
			out.append(_opt("About composting", func(): sim.say("Rotten food left in the bin slowly turns into fertiliser.", Color(0.8, 0.9, 0.75))))
		"fridge":
			pass
	if id == Defs.O_CAR_WRECK:
		out.append(_opt("Salvage parts", func(): _salvage_car(sim, a.x, a.y)))
	if Sim.APPLIANCES.has(id):
		var ae: Dictionary = w.ent(a.x, a.y)
		var is_off: bool = ae.get("off", false)
		out.append(_opt("Switch on" if is_off else "Switch off", func():
			var e2: Dictionary = w.ent(a.x, a.y)
			if e2.is_empty():
				e2 = {"k": "app"}
				w.set_ent(a.x, a.y, e2)
			e2["off"] = not e2.get("off", false)
			sim.emit_fx("click", p.pos)
			sim.say("%s %s." % [String(d["n"]), "off" if e2["off"] else "on"], Color(0.8, 0.85, 0.9))))
	if movable(sim, a.x, a.y) and p.carrying.is_empty():
		out.append(_opt("Pick up and carry", func(): _pick_up(sim, a.x, a.y)))
		if Defs.obj_size(id, 0) == Vector2i(1, 1) and int(d.get("sym", 0)) == 0:
			out.append(_opt("Turn it", func():
				w.set_obj(a.x, a.y, Defs.ocell(id, (Defs.o_rot(cell) + 1) % 4, 0))
				sim.emit_fx("build", p.pos)))
	if id == Defs.O_TV:
		out.append(_opt("Watch the broadcast", func(): _watch_tv(sim, x, y)))
	if d.has("scrap") and Inv.has_tag(p.inv, "hammer"):
		out.append(_opt("Dismantle", func(): _dismantle(sim, x, y)))
	out.append(_opt("Look closer", func(): sim.say(look_closer(sim, a.x, a.y), Color(0.85, 0.88, 0.8))))
	if id == Defs.O_WOOD_CRATE or id == Defs.O_RAIN_BARREL or id == Defs.O_CAMPFIRE:
		out.append(_opt("Remove", func():
			p.start_action("Removing", 2.5, func(): w.remove_object(x, y))))
	return out

static func _dismantle(sim: Sim, x: int, y: int) -> void:
	var p: Player = sim.player
	var w: World = sim.world
	p.start_action("Dismantling", 5.0 - p.skill_level("carpentry") * 0.25, func():
		var cell: int = w.obj(x, y)
		if cell == 0:
			return
		var d: Dictionary = Defs.obj(Defs.o_id(cell))
		var lvl: int = p.skill_level("carpentry")
		for sc in d.get("scrap", []):
			var n: int = int(ceil(float(sc[1]) * clampf(0.5 + lvl * 0.1, 0.5, 1.0)))
			if n > 0:
				w.drop_item(floori(p.pos.x), floori(p.pos.y), Items.make(sc[0], n, sim.hour))
		if Defs.o_id(cell) == Defs.O_TV or Defs.o_id(cell) == Defs.O_WASHER:
			p.add_xp("electrical", 14.0)
		w.remove_object(x, y)
		sim.noise(p.pos, 11.0)
		sim.emit_fx("build", p.pos)
		p.add_xp("carpentry", 12.0))

## for the first days a public-access channel still loops practical lessons
static func _watch_tv(sim: Sim, x: int, y: int) -> void:
	var p: Player = sim.player
	if not sim.has_power(x, y):
		sim.say("The screen stays dark. No power.", Color(0.8, 0.8, 0.8))
		return
	if sim.day() > 9:
		sim.say("Only static. The last channel went off the air.", Color(0.8, 0.8, 0.8))
		return
	if int(sim.flags.get("tv_day", 0)) == sim.day():
		sim.say("Today's programme has already looped. Try tomorrow.", Color(0.8, 0.8, 0.8))
		return
	var lessons: Array = ["cooking", "carpentry", "farming", "fishing", "trapping", "foraging", "first_aid", "tailoring", "electrical"]
	var skill: String = lessons[(sim.day() - 1) % lessons.size()]
	p.start_action("Watching a lesson on %s" % skill.replace("_", " "), 10.0, func():
		sim.flags["tv_day"] = sim.day()
		p.add_xp(skill, 45.0)
		p.bored = maxf(0.0, p.bored - 30.0)
		sim.noise(p.pos, 6.0)
		sim.say("You pick up a few things about %s" % skill.replace("_", " "), Color(0.6, 0.9, 0.6)))

# ------------------------------------------------------------------ the dead
static func _remove_corpse(sim: Sim, cp: Dictionary) -> void:
	var c: Chunk = sim.world.chunk_at(floori(cp["x"]), floori(cp["y"]))
	if c != null:
		c.corpses.erase(cp)
		c.touched = true
		sim.world.notify(floori(cp["x"]), floori(cp["y"]))

static func _drop_corpse(sim: Sim) -> void:
	var p: Player = sim.player
	var cp: Dictionary = p.dragging
	p.dragging = {}
	cp["x"] = p.pos.x + p.facing.x * 0.4
	cp["y"] = p.pos.y + p.facing.y * 0.4
	var c: Chunk = sim.world.chunk_at(floori(cp["x"]), floori(cp["y"]))
	if c == null:
		c = sim.world.chunk_at(floori(p.pos.x), floori(p.pos.y))
		cp["x"] = p.pos.x
		cp["y"] = p.pos.y
	c.corpses.append(cp)
	c.touched = true
	sim.world.notify(floori(cp["x"]), floori(cp["y"]))
	sim.say("You let the body down", Color(0.8, 0.8, 0.8))

static func _corpse_options(sim: Sim, t: Dictionary) -> Array:
	var p: Player = sim.player
	var w: World = sim.world
	var cp: Dictionary = t["corpse"]
	var out: Array = [_opt("Search corpse", func(): sim.ui_events.append({"type": "loot", "focus": cp}))]
	out.append(_opt("Drag the body", func():
		_remove_corpse(sim, cp)
		p.dragging = cp
		sim.say("You take it by the ankles. USE to let go.", Color(0.8, 0.8, 0.8))))
	if Inv.has_tag(p.inv, "dig"):
		out.append(_opt("Bury", func():
			p.start_action("Digging a grave", 9.0, func():
				_remove_corpse(sim, cp)
				var gx: int = floori(cp["x"])
				var gy: int = floori(cp["y"])
				if w.obj(gx, gy) == 0 and Defs.ground_is_natural(w.ground(gx, gy)):
					w.set_obj(gx, gy, Defs.ocell(Defs.O_GRAVE, 0, 0))
				p.endurance = maxf(0.0, p.endurance - 30.0)
				p.unhappy = minf(100.0, p.unhappy + 4.0)
				p.add_xp("strength", 6.0))))
	if Inv.has_tag(p.inv, "fire"):
		out.append(_opt("Burn the bodies here", func():
			p.start_action("Lighting the pyre", 4.0, func():
				var lighter: Dictionary = Inv.find_tag(p.inv, "fire")
				if lighter.is_empty():
					return
				Inv.use_charge(p.inv, lighter)
				var n := 0
				var cc: Vector2 = Vector2(cp["x"], cp["y"])
				for ch in w.chunks.values():
					for other in (ch as Chunk).corpses.duplicate():
						if Vector2(other["x"], other["y"]).distance_to(cc) < 1.8:
							_remove_corpse(sim, other)
							n += 1
				sim.ignite(floori(cc.x), floori(cc.y), 1.5)
				sim.noise(p.pos, 8.0)
				sim.say("%d bodies burn. Keep clear of the flames." % n, Color(1.0, 0.8, 0.5)))))
	return out

static func _track(sim: Sim) -> void:
	var p: Player = sim.player
	p.start_action("Reading the ground", 4.0 - p.skill_level("tracking") * 0.25, func():
		var found: String = sim.animals.track(p.pos, p.skill_level("tracking"))
		p.add_xp("tracking", 8.0 if found != "" else 3.0)
		sim.say(found if found != "" else "Nothing has passed this way lately.", Color(0.8, 0.88, 0.75)))

## wash off dirt and blood: cleaner wounds stay clean longer. `draw` takes n units and returns what it got
static func _wash(sim: Sim, draw: Callable) -> void:
	var p: Player = sim.player
	if p.grime < 8.0:
		sim.say("You are clean enough.", Color(0.8, 0.85, 0.9))
		return
	p.start_action("Washing", 5.0, func():
		var got: int = draw.call(3)
		if got <= 0:
			sim.say("Not enough water left to wash.", Color(0.8, 0.8, 0.9))
			return
		p.grime = maxf(0.0, p.grime - 35.0 * float(got))
		for wd in p.wounds:
			if wd["band"]: wd["dirty"] = maxf(0.0, float(wd["dirty"]) - 8.0)
		p.unhappy = maxf(0.0, p.unhappy - 6.0)
		p.temp -= 6.0 if sim.weather.get("temp", 15.0) < 10.0 else 0.0
		sim.say("Clean, or close enough.", Color(0.75, 0.9, 1.0)))

## what a careful look at a world object tells you
static func look_closer(sim: Sim, x: int, y: int) -> String:
	var w: World = sim.world
	var cell: int = w.obj(x, y)
	var id: int = Defs.o_id(cell)
	var d: Dictionary = Defs.obj(id)
	var bits: Array = [String(d.get("n", "Something"))]
	var c: Chunk = w.chunk_at(x, y)
	var hp_max: float = float(d.get("hp", 100))
	var hp: float = float(c.obj_hp.get(World.idx(x, y), hp_max)) if c != null else hp_max
	if hp < hp_max * 0.95:
		bits.append("damaged (%d%%)" % int(hp / hp_max * 100.0))
	if d.has("c") and not Vehicle.is_vehicle(id):
		if c != null and c.containers.has(World.idx(x, y)):
			var n: int = (c.containers[World.idx(x, y)] as Array).size()
			bits.append("empty" if n == 0 else "%d things inside" % n)
		else:
			bits.append("not searched yet")
	if Sim.APPLIANCES.has(id):
		bits.append("switched off" if w.ent(x, y).get("off", false) else ("running" if sim.has_power(x, y) else "no power"))
	var e: Dictionary = w.ent(x, y)
	match String(e.get("k", "")):
		"fire": bits.append("burning, about %d hours of fuel" % int(float(e.get("fuel", 0.0))) if e.get("lit", false) else "cold ashes")
		"barrel": bits.append("%d units of rainwater%s" % [int(float(e.get("w", 0.0))), ", frozen" if e.get("ice", false) else ""])
		"gen": bits.append("%s, %.0f h of fuel, condition %d%%" % ["running" if e.get("on", false) else "off", float(e.get("fuel", 0.0)), int(float(e.get("c", 1.0)) * 100.0)])
		"bank": bits.append("charge %d%%" % int(float(e.get("w", 0.0)) / Sim.BANK_MAX * 100.0))
		"crop": bits.append("%s, %s" % [String(e["t"]), Farming.STAGE_NAMES[int(e["s"])]])
		"coop": bits.append("%d hens" % int(e.get("hens", 0)))
	if Vehicle.is_vehicle(id):
		return condition_text(Vehicle.car_ent(sim, x, y), id)
	return ", ".join(bits) + "."

## scrub the clothes you are wearing; you put them back on damp
static func _laundry(sim: Sim, draw: Callable) -> void:
	var p: Player = sim.player
	if p.cloth_dirt < 10.0:
		sim.say("Your clothes are clean enough.", Color(0.8, 0.85, 0.9))
		return
	p.start_action("Washing clothes", 10.0, func():
		var got: int = draw.call(4)
		if got <= 0:
			sim.say("Not enough water.", Color(0.8, 0.8, 0.9))
			return
		p.cloth_dirt = maxf(0.0, p.cloth_dirt - 25.0 * float(got))
		p.wet = minf(100.0, p.wet + 45.0)
		sim.say("Clean clothes. Damp ones, for now.", Color(0.75, 0.9, 1.0)))

## put a fire out: an extinguisher clears an area, water douses a tile, a sheet smothers a small one
static func _fire_fight_options(sim: Sim, x: int, y: int) -> Array:
	var p: Player = sim.player
	var out: Array = []
	var ext: Dictionary = Inv.find(p.inv, "fire_extinguisher")
	if not ext.is_empty() and int(ext.get("u", 0)) > 0:
		var q: Dictionary = _opt("Spray the extinguisher", func():
			Inv.use_charge(p.inv, ext)
			for dy in range(-1, 2):
				for dx in range(-1, 2):
					sim.burning.erase(Vector2i(x + dx, y + dy))
					sim.fires.erase(Vector2i(x + dx, y + dy))
			sim.noise(p.pos, 8.0)
			sim.emit_fx("glass", Vector2(x + 0.5, y + 0.5))
			sim.say("A white cloud, and the flames are gone.", Color(0.85, 0.9, 1.0)))
		q["quick"] = true
		out.append(q)
	if p.water_units() >= 2:
		out.append(_opt("Douse it with water (2)", func():
			p.consume_water(2)
			sim.burning.erase(Vector2i(x, y))
			sim.fires.erase(Vector2i(x, y))
			sim.emit_fx("thump", Vector2(x + 0.5, y + 0.5))
			sim.say("It hisses out.", Color(0.85, 0.9, 1.0))))
	if Inv.count(p.inv, "sheet") > 0 and float(sim.burning.get(Vector2i(x, y), 99.0)) < 30.0:
		out.append(_opt("Smother it with a sheet", func():
			Inv.take(p.inv, "sheet", 1)
			sim.burning.erase(Vector2i(x, y))
			sim.fires.erase(Vector2i(x, y))
			sim.say("Beaten out. The sheet is ruined.", Color(0.85, 0.9, 1.0))))
	if out.is_empty():
		out.append(_opt("Nothing to put it out with", func(): sim.say("Water, a sheet or an extinguisher. Or get away from it.", Color(1.0, 0.75, 0.5))))
	return out

## sit down for a while: stamina and sore arms recover much faster than standing. any attack interrupts it.
static func _rest(sim: Sim) -> void:
	var p: Player = sim.player
	if sim.threatened():
		sim.say("Not with them this close", Color(1.0, 0.7, 0.6))
		return
	p.start_action("Resting", 8.0, func():
		p.endurance = minf(100.0, p.endurance + 55.0)
		p.arm_strain = maxf(0.0, p.arm_strain - 30.0)
		p.panic = maxf(0.0, p.panic - 15.0)
		sim.hour += 0.25
		sim.say("You get your breath back.", Color(0.8, 0.9, 0.75)))

# ------------------------------------------------------------------ vehicles
static func _car_options(sim: Sim, ax: int, ay: int) -> Array:
	var p: Player = sim.player
	var e: Dictionary = Vehicle.car_ent(sim, ax, ay)
	var out: Array = []
	var tid: int = Defs.o_id(sim.world.obj(ax, ay))
	var tank: float = Vehicle.tank_of(tid)
	if tid == Defs.O_BICYCLE:
		out.append(_opt("Ride the bicycle", func():
			p.cancel_action()
			sim.vehicle = Vehicle.enter(sim, ax, ay)
			sim.brake = false
			sim.say("Quiet, and it runs on you. Watch your stamina.", Color(0.75, 0.9, 0.7))))
		if float(e.get("tire", 1.0)) < 0.9 and Inv.count(p.inv, "duct_tape") > 0:
			out.append(_opt("Patch the tyres (duct tape)", func(): _patch_tyre(sim, e)))
		return out
	var can_start: bool = int(e.get("key", 0)) == 1 or int(e.get("hot", 0)) == 1
	if can_start:
		out.append(_opt("Ride" if tid == Defs.O_MOTORBIKE else "Drive", func():
			if int(e.get("bat", 0)) == 0:
				sim.say("You turn the key. Nothing — the battery is dead or missing.", Color(0.9, 0.8, 0.6))
				return
			if float(e.get("eng", 0.0)) <= 0.05:
				sim.say("The engine is wrecked. It needs repair before it will turn over.", Color(0.9, 0.8, 0.6))
				return
			p.cancel_action()
			sim.vehicle = Vehicle.enter(sim, ax, ay)
			sim.brake = false
			_board_companions(sim)
			sim.noise(p.pos, 14.0)
			sim.emit_fx("engine", p.pos)
			if float(e.get("fuel", 0.0)) <= 0.0:
				sim.say("You get in. The tank is empty.", Color(0.9, 0.8, 0.6))
			else:
				sim.say("The engine catches. Steer with the stick; USE to get out.", Color(0.75, 0.9, 0.7))))
	else:
		var keys: Array = []
		for kit in p.inv:
			if kit["id"] == "car_keys" and not (kit.get("no", []) as Array).has("%d,%d" % [ax, ay]) and (not kit.has("car") or kit["car"] == "%d,%d" % [ax, ay]):
				keys.append(kit)
		if not keys.is_empty():
			out.append(_opt("Try the car keys you found", func(): try_keys(sim, e, ax, ay)))
		out.append(_opt("Hotwire (no key)", func(): _hotwire(sim, e)))
	if int(e.get("bat", 0)) == 0 and Inv.count(p.inv, "car_battery") > 0:
		out.append(_opt("Install car battery", func():
			p.start_action("Fitting battery", 5.0, func():
				var b: Dictionary = Inv.find(p.inv, "car_battery")
				if b.is_empty(): return
				Inv.split(p.inv, b, 1)
				e["bat"] = 1
				p.add_xp("mechanics", 10.0)
				sim.say("Battery connected.", Color(0.75, 0.9, 0.7)))))
	var can: Dictionary = Inv.find_tag(p.inv, "fuel_can")
	if not can.is_empty() and int(can.get("u", 0)) > 0 and float(e.get("fuel", 0.0)) < tank - 0.5:
		out.append(_opt("Refuel from gas can", func():
			p.start_action("Refuelling", 4.0, func():
				var n: float = minf(float(int(can.get("u", 0))), tank - float(e.get("fuel", 0.0)))
				can["u"] = int(can.get("u", 0)) - int(ceil(n))
				e["fuel"] = float(e.get("fuel", 0.0)) + n
				sim.say("Tank: %d / %d" % [int(float(e["fuel"])), int(tank)], Color(0.75, 0.9, 0.7)))))
	if float(e.get("tire", 1.0)) < 0.9 and Inv.count(p.inv, "duct_tape") > 0:
		out.append(_opt("Patch the tyres (duct tape)", func(): _patch_tyre(sim, e)))
	if float(e.get("tire", 1.0)) < 0.99 and Inv.count(p.inv, "tyre_kit") > 0:
		out.append(_opt("Repair the tyres properly (tyre kit)", func():
			p.start_action("Plugging and inflating", 6.0, func():
				if not Inv.take(p.inv, "tyre_kit", 1): return
				e["tire"] = 1.0
				p.add_xp("mechanics", 14.0)
				sim.say("Good as new.", Color(0.75, 0.9, 0.7)))))
	if float(e.get("win", 1.0)) < 0.99 and Inv.count(p.inv, "glass_pane") > 0:
		out.append(_opt("Fit a new window (glass pane)", func():
			p.start_action("Fitting glass", 7.0, func():
				if not Inv.take(p.inv, "glass_pane", 1): return
				e["win"] = minf(1.0, float(e.get("win", 1.0)) + 0.34)
				p.add_xp("mechanics", 12.0)
				sim.say("Windows: %d%%" % int(float(e["win"]) * 100.0), Color(0.75, 0.9, 0.7)))))
	if int(e.get("muf", 1)) == 0 and Inv.count(p.inv, "scrap_metal") > 0 and Inv.has_tag(p.inv, "wrench"):
		out.append(_opt("Patch the muffler (scrap metal)", func():
			p.start_action("Patching the muffler", 6.0, func():
				if not Inv.take(p.inv, "scrap_metal", 1): return
				e["muf"] = 1
				p.add_xp("mechanics", 14.0)
				sim.say("Quieter.", Color(0.75, 0.9, 0.7)))))
	if int(e.get("lit", 1)) == 0 and Inv.count(p.inv, "wire") > 0:
		out.append(_opt("Rewire the headlights (wire)", func():
			if p.skill_level("electrical") < 1:
				sim.say("You need Electrical 1 to trace the fault.", Color(0.9, 0.8, 0.6))
				return
			p.start_action("Rewiring", 6.0, func():
				if not Inv.take(p.inv, "wire", 1): return
				e["lit"] = 1
				p.add_xp("electrical", 16.0)
				sim.say("The headlights work again.", Color(0.75, 0.9, 0.7)))))
	if float(e.get("eng", 1.0)) < 0.95 and Inv.has_tag(p.inv, "wrench") and Inv.count(p.inv, "scrap_metal") > 0:
		out.append(_opt("Repair engine (1 scrap metal)", func():
			p.start_action("Repairing engine", 9.0 - p.skill_level("mechanics") * 0.5, func():
				var sm: Dictionary = Inv.find(p.inv, "scrap_metal")
				if sm.is_empty(): return
				Inv.split(p.inv, sm, 1)
				e["eng"] = minf(1.0, float(e.get("eng", 0.0)) + 0.14 + 0.03 * p.skill_level("mechanics"))
				p.add_xp("mechanics", 22.0)
				sim.noise(p.pos, 8.0)
				sim.emit_fx("build", p.pos)
				sim.say("Engine condition: %d%%" % int(float(e["eng"]) * 100.0), Color(0.75, 0.9, 0.7)))))
	out.append(_opt("Look it over", func(): sim.say(condition_text(e, tid), Color(0.85, 0.88, 0.8))))
	return out

static func condition_text(e: Dictionary, tid: int) -> String:
	var t: String = "Fuel %d/%d · engine %d%% · tyres %d%%" % [int(float(e.get("fuel", 0.0))), int(Vehicle.tank_of(tid)), int(float(e.get("eng", 0.0)) * 100.0), int(float(e.get("tire", 1.0)) * 100.0)]
	if tid != Defs.O_MOTORBIKE:
		t += " · windows %d%%" % int(float(e.get("win", 1.0)) * 100.0)
	if tid != Defs.O_BICYCLE:
		t += " · muffler %s" % ("ok" if int(e.get("muf", 1)) == 1 else "holed")
	t += " · lights %s · battery %s · %s" % ["ok" if int(e.get("lit", 1)) == 1 else "broken", "ok" if int(e.get("bat", 0)) == 1 else "dead",
		"key in the ignition" if int(e.get("key", 0)) == 1 else ("hotwired" if int(e.get("hot", 0)) == 1 else "no key")]
	return t

static func _patch_tyre(sim: Sim, e: Dictionary) -> void:
	var p: Player = sim.player
	p.start_action("Patching tyres", 5.0, func():
		var tape: Dictionary = Inv.find(p.inv, "duct_tape")
		if tape.is_empty(): return
		Inv.use_charge(p.inv, tape)
		e["tire"] = minf(0.85, float(e.get("tire", 0.0)) + 0.3 + p.skill_level("mechanics") * 0.03)
		p.add_xp("mechanics", 8.0)
		sim.say("Tyres: %d%%. A patch is never as good as new." % int(float(e["tire"]) * 100.0), Color(0.75, 0.9, 0.7)))

## long-press USE while inside
static func vehicle_menu(sim: Sim) -> Array:
	var v: Vehicle = sim.vehicle
	var out: Array = []
	out.append(_opt("Get out", func(): exit_vehicle(sim)))
	out.append(_opt("Look it over", func(): sim.say(condition_text(v.ent, v.oid), Color(0.85, 0.88, 0.8))))
	if v.motor() and v.size().x + v.size().y > 3.0 and absf(v.speed) < 0.5:
		out.append(_opt("Sleep in the seat", func():
			if sim.player.fatigue < 20.0:
				sim.say("You are not tired enough to sleep", Color(0.8, 0.8, 0.9))
				return
			sim.start_sleep(0.55)))
	if v.tow.is_empty() and bool(v.spec()["tow"]):
		var b: Vector2i = v.behind()
		if b.x != -1 or b.y != -1:
			out.append(_opt("Hitch the %s behind you" % String(Defs.obj(Defs.o_id(sim.world.obj(b.x, b.y)))["n"]).to_lower(), func():
				if absf(v.speed) > 0.5:
					sim.say("Stop first", Color(0.9, 0.8, 0.6))
					return
				if v.hitch(b.x, b.y):
					sim.noise(v.pos, 8.0)
					sim.say("Chained on. Slow and thirsty, but it moves.", Color(0.75, 0.9, 0.7))))
	elif not v.tow.is_empty():
		out.append(_opt("Unhitch the %s" % String(Defs.obj(int(v.tow["o"]))["n"]).to_lower(), func():
			if not v.unhitch():
				sim.say("Stop somewhere with room behind you", Color(0.9, 0.8, 0.6))
			else:
				sim.say("Unhitched.", Color(0.8, 0.85, 0.9))))
	return out

## seats: following companions climb in with you
static func _board_companions(sim: Sim) -> void:
	var v: Vehicle = sim.vehicle
	var seats: int = {Defs.O_BUS: 12, Defs.O_VAN: 3, Defs.O_TRUCK: 2, Defs.O_AMBULANCE: 3, Defs.O_PICKUP: 2, Defs.O_CAR: 3, Defs.O_POLICE_CAR: 3}.get(v.oid, 0)
	for n in sim.npcs.list.duplicate():
		if seats <= 0:
			break
		if n.state == NpcSim.FOLLOW and n.pos.distance_to(sim.player.pos) < 6.0:
			v.passengers.append(NpcSim._ser(n))
			sim.npcs.list.erase(n)
			seats -= 1
	if not v.passengers.is_empty():
		sim.say("%d %s in with you." % [v.passengers.size(), "climbs" if v.passengers.size() == 1 else "climb"], Color(0.8, 0.85, 0.9))

static func _unload_companions(sim: Sim, v: Vehicle) -> void:
	var k := 0
	for a in v.passengers:
		var n = sim.npcs._de(a)
		var side: Vector2 = Vector2(Vehicle.DIRS[v.heading].y, -Vehicle.DIRS[v.heading].x)
		var spot: Vector2 = v.pos - side * (1.6 + float(k % 2) * 0.8) + Vehicle.DIRS[v.heading] * float(k / 2)
		if sim.world.blocked(spot.x, spot.y, 0.25):
			spot = sim.player.pos
		n.pos = spot
		n.state = NpcSim.FOLLOW
		sim.npcs.list.append(n)
		k += 1
	v.passengers.clear()

## keys you picked up somewhere: one of them may fit this car; a key that fits is remembered as this car's
static func try_keys(sim: Sim, e: Dictionary, ax: int, ay: int) -> bool:
	var p: Player = sim.player
	var here: String = "%d,%d" % [ax, ay]
	for kit in p.inv:
		if kit["id"] != "car_keys": continue
		if kit.get("car", "") == here or (not kit.has("car") and not (kit.get("no", []) as Array).has(here) and sim.rng.randf() < 0.3):
			kit["car"] = here
			e["key"] = 1
			sim.say("The key slides in and turns. This one is yours now.", Color(0.75, 0.9, 0.7))
			return true
		if not kit.has("car"):
			var no: Array = kit.get("no", [])
			no.append(here)
			kit["no"] = no
	sim.say("None of your keys fit this one.", Color(0.9, 0.8, 0.6))
	return false

static func _hotwire(sim: Sim, e: Dictionary) -> void:
	var p: Player = sim.player
	var skilled: bool = p.occupation == "burglar" or (p.skill_level("mechanics") >= 2 and p.skill_level("electrical") >= 1)
	var pliers: bool = Inv.has_tag(p.inv, "pliers")
	if not skilled and not Inv.has_tag(p.inv, "screwdriver") and not pliers:
		sim.say("Without Mechanics 2 and Electrical 1 you would need at least a screwdriver to try.", Color(0.9, 0.8, 0.6))
		return
	p.start_action("Hotwiring", 6.0 if skilled else 12.0, func():
		var chance: float = (0.7 + 0.05 * p.skill_level("electrical") if skilled else 0.18) + (0.12 if pliers else 0.0)
		sim.noise(p.pos, 7.0)
		p.add_xp("electrical", 12.0)
		if randf() < chance:
			e["hot"] = 1
			sim.say("The dash lights flicker on. It will start now.", Color(0.75, 0.9, 0.7))
		else:
			sim.say("Sparks, and nothing. Try again.", Color(0.9, 0.8, 0.6)))

static func exit_vehicle(sim: Sim) -> bool:
	var v: Vehicle = sim.vehicle
	var p: Player = sim.player
	if v == null:
		return false
	if absf(v.speed) > 1.2:
		sim.say("Stop the car first (BRAKE)", Color(0.9, 0.8, 0.6))
		return false
	if not v.park():
		sim.say("No room to park here — roll forward a little", Color(0.9, 0.8, 0.6))
		return false
	sim.vehicle = null
	sim.brake = false
	_unload_companions(sim, v)
	# step out on whichever side is free
	var side: Vector2 = Vector2(Vehicle.DIRS[v.heading].y, -Vehicle.DIRS[v.heading].x)
	var half: float = v.size().x * 0.5 + 0.6 if v.heading % 2 == 0 else v.size().y * 0.5 + 0.6
	for sgn in [1.0, -1.0]:
		for along in [0.0, 1.0, -1.0, 1.6, -1.6]:
			var t: Vector2 = v.pos + side * half * sgn + Vehicle.DIRS[v.heading] * along
			t = Vector2(floorf(t.x) + 0.5, floorf(t.y) + 0.5)
			if not sim.world.blocked(t.x, t.y, Player.R):
				p.pos = t
				sim.emit_fx("door", p.pos)
				sim.say("You get out.", Color(0.8, 0.85, 0.9))
				return true
	# boxed in on both sides: climb out over the bonnet
	var f: Vector2 = v.pos + Vehicle.DIRS[v.heading] * 2.6
	p.pos = Vector2(floorf(f.x) + 0.5, floorf(f.y) + 0.5)
	return true

# ------------------------------------------------------------------ animals
static func _coop_options(sim: Sim, x: int, y: int) -> Array:
	var p: Player = sim.player
	var w: World = sim.world
	var e: Dictionary = w.ent(x, y)
	if e.is_empty():
		var hv: int = Rng.h2(x, y, sim.seed_v + 61)
		e = {"k": "coop", "hens": 2 + hv % 3, "eggs": float((hv >> 4) % 4), "fed": 30.0, "starve": 0.0}
		w.set_ent(x, y, e)
	var out: Array = []
	var hens: int = int(e.get("hens", 0))
	var eggs: int = int(float(e.get("eggs", 0.0)))
	out.append(_opt("Collect eggs (%d)" % eggs, func():
		if eggs <= 0:
			sim.say("No eggs yet. %d hens, %s." % [hens, "fed" if float(e.get("fed", 0.0)) > 0.0 else "hungry"], Color(0.85, 0.85, 0.75))
			return
		p.start_action("Collecting eggs", 2.5, func():
			Inv.add_new(p.inv, "egg", eggs, sim.hour)
			e["eggs"] = float(e.get("eggs", 0.0)) - float(eggs)
			p.add_xp("animal_care", 6.0 * eggs)
			sim.say("%d eggs." % eggs, Color(0.75, 0.9, 0.7)))))
	var feed: Dictionary = {}
	for it in p.inv:
		if String(Items.def(it["id"]).get("cat", "")) == "seed" or String(it["id"]) == "canned_corn" or String(it["id"]) == "cabbage":
			feed = it
			break
	if hens > 0 and not feed.is_empty():
		out.append(_opt("Feed the hens (%s)" % Items.def(feed["id"])["n"], func():
			Inv.split(p.inv, feed, 1)
			e["fed"] = minf(240.0, float(e.get("fed", 0.0)) + 60.0 + 6.0 * p.skill_level("animal_care"))
			e["starve"] = 0.0
			p.add_xp("animal_care", 10.0)
			sim.say("The hens crowd the feed. Good for about %d days." % int(float(e["fed"]) / 24.0), Color(0.75, 0.9, 0.7))))
	if hens > 0:
		out.append(_opt("Take a hen for the pot", func():
			if not Inv.has_tag(p.inv, "knife"):
				sim.say("You need a knife", Color(0.9, 0.8, 0.6))
				return
			p.start_action("Butchering", 6.0 - p.skill_level("butchering") * 0.3, func():
				e["hens"] = int(e.get("hens", 0)) - 1
				Inv.add_new(p.inv, "raw_chicken", 1 + (1 if p.skill_level("butchering") >= 3 else 0), sim.hour)
				p.add_xp("butchering", 25.0)
				sim.noise(p.pos, 6.0)
				sim.say("One less hen.", Color(0.85, 0.85, 0.75)))))
	out.append(_opt("Look in", func():
		sim.say("%d hens, %d eggs, feed for %d hours." % [hens, eggs, int(maxf(0.0, float(e.get("fed", 0.0))))], Color(0.85, 0.88, 0.8))))
	return out

static func hide_in(sim: Sim, x: int, y: int) -> void:
	var p: Player = sim.player
	if not p.carrying.is_empty() or not p.dragging.is_empty():
		sim.say("Not with your arms full", Color(0.9, 0.8, 0.6))
		return
	p.start_action("Squeezing in", 1.2, func():
		p.hidden = true
		p.hide_at = Vector2i(x, y)
		sim.emit_fx("door", p.pos)
		# anything already chasing saw where you went
		for z in sim.zombies.list:
			if z.state == Zombie.CHASE and z.pos.distance_to(p.pos) < 5.0:
				z.goal = p.pos
				z.has_goal = true
		sim.say("You pull the door to. Keep still. USE to come out.", Color(0.8, 0.85, 0.9)), false)

static func leave_hiding(sim: Sim) -> void:
	var p: Player = sim.player
	if not p.hidden:
		return
	p.hidden = false
	sim.emit_fx("door", p.pos)
	sim.noise(p.pos, 3.0)

## crack a closed door: see what is on the other side without opening it
static func _peek(sim: Sim, x: int, y: int, side: int) -> void:
	var p: Player = sim.player
	p.start_action("Peeking", 1.5, func():
		var other: Vector2i = _other_side(sim, x, y, side)
		var c := Vector2(other.x + 0.5, other.y + 0.5)
		var seen := 0
		for z in sim.zombies.list:
			if z.pos.distance_to(c) < 6.0 and sim.world.los(c.x, c.y, z.pos.x, z.pos.y):
				z.peeked = 4.0
				seen += 1
		sim.noise(p.pos, 1.0)
		sim.say(("Through the gap: %d of them." % seen) if seen > 0 else "Through the gap: nothing moving.", Color(0.85, 0.85, 0.75)))

## look a long way: who and what is out there
static func use_binoculars(sim: Sim) -> void:
	var p: Player = sim.player
	p.start_action("Looking through binoculars", 2.0, func():
		var zs := 0
		var dirs: Dictionary = {}
		for z in sim.zombies.list:
			var d: float = z.pos.distance_to(p.pos)
			if d < 40.0 and d > 3.0 and p.facing.dot((z.pos - p.pos).normalized()) > 0.5 and sim.world.los(p.pos.x, p.pos.y, z.pos.x, z.pos.y):
				zs += 1
				z.peeked = 6.0
				var cd: String = Sim.compass(p.pos, z.pos)
				dirs[cd] = int(dirs.get(cd, 0)) + 1
		var people := 0
		for n in sim.npcs.list:
			if n.pos.distance_to(p.pos) < 40.0 and p.facing.dot((n.pos - p.pos).normalized()) > 0.5: people += 1
		var game := 0
		for an in sim.animals.list:
			if an.pos.distance_to(p.pos) < 40.0 and p.facing.dot((an.pos - p.pos).normalized()) > 0.5: game += 1
		var parts: Array = []
		for k in dirs.keys(): parts.append("%d %s" % [dirs[k], k])
		sim.say("Through the lenses: %s%s%s." % [("infected " + ", ".join(parts)) if zs > 0 else "no infected", (", %d people" % people) if people > 0 else "", (", %d animals" % game) if game > 0 else ""], Color(0.8, 0.9, 1.0))
		sim.ui_events.append({"type": "zoom", "z": 0.9, "t": 6.0}))

static func _use_stairs(sim: Sim, dy: int, msg: String = "") -> void:
	var p: Player = sim.player
	var src: Vector2 = p.pos
	# whatever is on your heels follows you up or down
	var followers: Array = []
	for z in sim.zombies.list:
		if (z.state == Zombie.CHASE or z.state == Zombie.INVESTIGATE) and z.pos.distance_to(src) < 10.0 and not z.trapped:
			followers.append(z)
			z.goal = src
			z.has_goal = true
			z.state = Zombie.INVESTIGATE
			z.give_up = 25.0
			z.path = PackedVector2Array()
	p.start_action("Climbing", 1.6, func():
		var dest := Vector2(p.pos.x, p.pos.y + dy)
		# lift the followers out before the floor you leave is unloaded
		var climbing: Array = []
		for zf in followers:
			if sim.zombies.list.has(zf):
				climbing.append([zf, zf.pos.distance_to(src) / maxf(0.4, zf.speed) + 0.8])
				sim.zombies.list.erase(zf)
		sim.world.stream(dest, 2, 999)
		var t := Vector2(floorf(dest.x) + 0.5, floorf(dest.y) + 0.5)
		if sim.world.blocked(t.x, t.y, Player.R):
			# find a free neighbouring tile next to the ladder / hatch
			for d in [Vector2(0, 1), Vector2(1, 0), Vector2(-1, 0), Vector2(0, -1), Vector2(1, 1), Vector2(-1, 1)]:
				if not sim.world.blocked(t.x + d.x, t.y + d.y, Player.R):
					t += d
					break
		p.pos = t
		# they come up after you, a little behind: how far back they were, at their pace
		for cl in climbing:
			var z2: Zombie = cl[0]
			var lag: float = cl[1]
			sim.zombies.list.append(z2)
			var spot: Vector2 = t
			for d2 in [Vector2(0, 1), Vector2(1, 0), Vector2(-1, 0), Vector2(0, -1), Vector2(1, 1), Vector2(-1, -1), Vector2(1, -1), Vector2(-1, 1)]:
				if not sim.world.blocked(t.x + d2.x, t.y + d2.y, 0.3):
					spot = t + d2
					break
			z2.pos = spot
			z2.state = Zombie.STAGGER          # still on the stairs: they arrive after `lag` seconds
			z2.t = lag
			z2.anim = "z_walk"
			z2.goal = t
			z2.has_goal = true
			z2.path = PackedVector2Array()
		sim._process_world_events()
		sim.emit_fx("step", p.pos)
		for n in sim.npcs.list:
			if n.state == NpcSim.FOLLOW and n.pos.distance_to(Vector2(t.x, t.y - dy)) < 6.0:
				n.pos = t
				n.path = PackedVector2Array()
		sim.say(msg if msg != "" else ("You climb down into the dark." if dy > 0 else "You climb back up."), Color(0.8, 0.85, 0.9)))

static func _salvage_car(sim: Sim, ax: int, ay: int) -> void:
	var p: Player = sim.player
	var w: World = sim.world
	if not Inv.has_tag(p.inv, "wrench") and not Inv.has_tag(p.inv, "screwdriver"):
		sim.say("You need a wrench or a screwdriver", Color(0.9, 0.8, 0.6))
		return
	var e: Dictionary = w.ent(ax, ay)
	if e.is_empty():
		e = {"k": "car", "fuel": Rng.h2(ax, ay, sim.seed_v + 55) % 7}
		w.set_ent(ax, ay, e)
	if int(e.get("sv", 0)) >= 3:
		sim.say("Nothing useful left on this one", Color(0.8, 0.8, 0.8))
		return
	p.start_action("Salvaging parts", 7.0 - p.skill_level("mechanics") * 0.4, func():
		var lvl: int = p.skill_level("mechanics")
		var n: int = int(e.get("sv", 0))
		e["sv"] = n + 1
		var got: Array = [["scrap_metal", 1 + (1 if randf() < 0.3 + lvl * 0.1 else 0)]]
		if randf() < 0.4 + lvl * 0.08: got.append(["wire", 1])
		if n == 0 and randf() < 0.35 + lvl * 0.1: got.append(["car_battery", 1])
		var names: Array = []
		for g in got:
			Inv.add_new(p.inv, g[0], int(g[1]), sim.hour)
			names.append("%d %s" % [int(g[1]), Items.def(g[0])["n"]])
		sim.say("Salvaged: " + ", ".join(names), Color(0.75, 0.9, 0.7))
		sim.noise(p.pos, 9.0)
		sim.emit_fx("build", p.pos)
		p.add_xp("mechanics", 16.0))

static func _trap_options(sim: Sim, x: int, y: int) -> Array:
	var p: Player = sim.player
	var w: World = sim.world
	var e: Dictionary = w.ent(x, y)
	if e.is_empty():
		e = {"k": "trap", "h": sim.hour, "bait": 0, "caught": ""}
		w.set_ent(x, y, e)
	var out: Array = []
	if String(e.get("caught", "")) != "":
		out.append(_opt("Collect the catch", func():
			var id: String = e["caught"]
			Inv.add_new(p.inv, id, 1, sim.hour)
			e["caught"] = ""
			p.add_xp("trapping", 28.0)
			sim.say("The snare held: %s" % Items.def(id)["n"], Color(0.75, 0.9, 0.7))
			sim.emit_fx("pickup", p.pos)))
	else:
		out.append(_opt("Check snare (empty%s)" % (", baited" if e.get("bait", 0) == 1 else ""), func():
			sim.say("Nothing yet. Snares do best far from town, baited, and left alone.", Color(0.8, 0.85, 0.8))))
		if e.get("bait", 0) == 0:
			for bid in ["carrot", "berries", "cabbage", "apple"]:
				if Inv.count(p.inv, bid) > 0:
					var bait: String = bid
					out.append(_opt("Bait with %s" % String(Items.def(bait)["n"]).to_lower(), func():
						if Inv.take(p.inv, bait, 1):
							e["bait"] = 1))
					break
	out.append(_opt("Pick up snare", func():
		w.set_ent(x, y, {})
		w.set_obj(x, y, 0)
		Inv.add_new(p.inv, "snare", 1)))
	return out

static func _chop(sim: Sim, x: int, y: int) -> void:
	var p: Player = sim.player
	var w: World = sim.world
	if p.endurance < 8.0:
		sim.say("Too exhausted to chop", Color(0.9, 0.8, 0.6))
		return
	p.start_action("Chopping", 1.6, func():
		var cell: int = w.obj(x, y)
		var id: int = Defs.o_id(cell)
		if cell == 0 or Defs.obj(id).get("use", "") != "tree":
			return
		var c: Chunk = w.chunk_at(x, y)
		var i: int = World.idx(x, y)
		var hp: float = c.obj_hp.get(i, float(Defs.obj(id)["hp"]))
		hp -= 32.0 + p.skill_level("axe") * 5.0
		p.endurance -= 7.0
		sim.noise(p.pos, 13.0)
		sim.emit_fx("thump", p.pos)
		p.add_xp("axe", 4.0)
		p.add_xp("strength", 1.5)
		var axe: Dictionary = Inv.find_tag(p.inv, "axe")
		if hp <= 0.0:
			c.obj_hp.erase(i)
			w.set_obj(x, y, Defs.O_STUMP)
			var logs: int = 1 if id == Defs.O_TREE_DEAD else (2 + randi() % 2)
			w.drop_item(x, y, Items.make("log", logs))
			w.drop_item(x, y, Items.make("branch", 1 + randi() % 3))
			sim.say("Timber!", Color(0.8, 0.9, 0.7))
			sim.emit_fx("break", p.pos)
		else:
			c.obj_hp[i] = hp
			c.touched = true
			_chop(sim, x, y))

static func _forage(sim: Sim, x: int, y: int, branches: bool) -> void:
	var p: Player = sim.player
	var w: World = sim.world
	var e: Dictionary = w.ent(x, y)
	if e.get("k", "") == "forage":
		sim.say("Nothing left to find here for now", Color(0.8, 0.8, 0.8))
		return
	p.start_action("Gathering" if branches else "Foraging", 3.5, func():
		var lvl: int = p.skill_level("foraging")
		w.set_ent(x, y, {"k": "forage", "h": sim.hour})
		p.add_xp("foraging", 6.0)
		var r: float = randf() - lvl * 0.04
		var found: String = ""
		var n := 1
		if branches:
			found = "branch"
			n = 1 + randi() % 2
		elif r < 0.18: found = "berries"
		elif r < 0.3: found = "mushroom"
		elif r < 0.45: found = "branch"
		elif r < 0.56: found = "stone"
		elif r < 0.6: found = ["seeds_potato", "seeds_cabbage", "seeds_carrot", "seeds_tomato"][randi() % 4]
		if found == "":
			sim.say("You find nothing useful", Color(0.8, 0.8, 0.8))
			return
		Inv.add(p.inv, Items.make(found, n, sim.hour))
		sim.say("Found: %s" % Items.def(found)["n"], Color(0.75, 0.9, 0.7))
		sim.emit_fx("pickup", p.pos))

static func _siphon(sim: Sim, ax: int, ay: int) -> void:
	var p: Player = sim.player
	var w: World = sim.world
	var can: Dictionary = Inv.find_tag(p.inv, "fuel_can")
	if can.is_empty():
		sim.say("You need a gas can", Color(0.9, 0.8, 0.6))
		return
	var e: Dictionary = w.ent(ax, ay)
	if e.is_empty():
		e = {"k": "car", "fuel": Rng.h2(ax, ay, sim.seed_v + 55) % 7}
		w.set_ent(ax, ay, e)
	if int(e["fuel"]) <= 0:
		sim.say("The tank is dry", Color(0.9, 0.8, 0.6))
		return
	p.start_action("Siphoning fuel", 5.0, func():
		var room: int = int(Items.def(can["id"])["maxuses"]) - int(can.get("u", 0))
		var n: int = mini(room, int(e["fuel"]))
		can["u"] = int(can.get("u", 0)) + n
		e["fuel"] = int(e["fuel"]) - n
		sim.say("Siphoned %d units of fuel" % n, Color(0.8, 0.9, 0.7)))

static func _fill_gas(sim: Sim, n: int) -> void:
	var p: Player = sim.player
	var can: Dictionary = Inv.find_tag(p.inv, "fuel_can")
	if can.is_empty():
		sim.say("You need a gas can", Color(0.9, 0.8, 0.6))
		return
	p.start_action("Pumping fuel", 4.0, func():
		can["u"] = int(Items.def(can["id"])["maxuses"])
		sim.say("Gas can filled", Color(0.8, 0.9, 0.7)))

# ------------------------------------------------------------------ water
static func _drink_source(sim: Sim, tainted: bool, units: int) -> void:
	var p: Player = sim.player
	if p.thirst < 3.0:
		sim.say("You are not thirsty", Color(0.8, 0.8, 0.9))
		return
	p.start_action("Drinking", 2.2, func():
		p.thirst = maxf(0.0, p.thirst - 60.0)
		if tainted and randf() < 0.5:
			p.sick = minf(100.0, p.sick + 26.0)
			sim.say("The water tastes foul. Your stomach churns.", Color(0.8, 1.0, 0.6))
		sim.emit_fx("eat", p.pos))

## fill empty bottles / top up containers. returns units used
static func _fill(sim: Sim, tainted: bool, units: int) -> int:
	var p: Player = sim.player
	var used := 0
	var n: int = Inv.count(p.inv, "empty_bottle")
	n = mini(n, units / 5)
	if n > 0:
		Inv.take(p.inv, "empty_bottle", n)
		for i in range(n):
			var it: Dictionary = Items.make("water_bottle", 1)
			if tainted: it["d"] = 1
			p.inv.append(it)
		used += n * 5
	for it in p.inv:
		var d: Dictionary = Items.def(it["id"])
		if d.has("water") and it.has("u"):
			var mx: int = int(d.get("maxuses", d.get("uses", 0)))
			var need: int = mx - int(it["u"])
			if need > 0 and used + need <= units:
				it["u"] = mx
				used += need
				if tainted: it["d"] = 1
				elif it["id"] == "water_bottle" and int(it["u"]) == mx and need == mx: it.erase("d")
	if used == 0:
		sim.say("Nothing to fill", Color(0.8, 0.8, 0.9))
	else:
		sim.say("Filled your water containers", Color(0.7, 0.85, 1.0))
		sim.emit_fx("pickup", p.pos)
	return used

static func _dig(sim: Sim, what: String) -> void:
	var p: Player = sim.player
	p.start_action("Digging", 5.0, func():
		Inv.add_new(p.inv, what, 1 + randi() % 2, sim.hour)
		p.endurance = maxf(0.0, p.endurance - 12.0)
		p.add_xp("pottery" if what == "clay" else "glassmaking", 4.0)
		sim.say("Dug up some %s" % what, Color(0.75, 0.9, 0.7))
		sim.emit_fx("pickup", p.pos))

static func _water_options(sim: Sim, t: Dictionary) -> Array:
	var p: Player = sim.player
	var out: Array = [
		_opt("Drink (untreated)", func(): _drink_source(sim, true, 999)),
		_opt("Fill water containers (untreated)", func(): _fill(sim, true, 999))]
	if Inv.has_tag(p.inv, "dig"):
		out.append(_opt("Dig clay from the bank", func(): _dig(sim, "clay")))
	# a gap in a bridge or a channel: span it with planks if there is something to rest them on
	var wx3: int = t["x"]
	var wy3: int = t["y"]
	var shore := false
	for d3 in [Vector2i(1, 0), Vector2i(-1, 0), Vector2i(0, 1), Vector2i(0, -1)]:
		var g3: int = sim.world.ground(wx3 + d3.x, wy3 + d3.y)
		if g3 == Defs.G_CONCRETE or g3 == Defs.G_PLANK or Defs.ground_is_road(g3): shore = true
	if shore and Inv.count(p.inv, "plank") >= 3 and Inv.count(p.inv, "nails") >= 6 and Inv.has_tag(p.inv, "hammer"):
		out.append(_opt("Lay a plank span across (3 planks, 6 nails)", func():
			p.start_action("Laying a span", 9.0 - p.skill_level("carpentry") * 0.4, func():
				if not Inv.take(p.inv, "plank", 3) or not Inv.take(p.inv, "nails", 6): return
				sim.world.set_ground(wx3, wy3, Defs.G_PLANK)
				sim.noise(p.pos, 13.0)
				sim.emit_fx("build", p.pos)
				p.add_xp("carpentry", 25.0)
				sim.say("A rough span. It will take a car, carefully.", Color(0.75, 0.9, 0.7)))))
	if not p.weapon.is_empty() and Items.def(p.weapon["id"]).get("wpn", {}).get("type", "") == "spear":
		out.append(_opt("Spear fish", func():
			p.start_action("Spear fishing", 6.0, func():
				p.add_xp("fishing", 8.0)
				p.add_xp("spear", 4.0)
				if randf() < (0.18 + p.skill_level("fishing") * 0.05 + p.skill_level("spear") * 0.03) * sim.fish_stock(t["x"], t["y"]):
					sim.take_fish(t["x"], t["y"])
					Inv.add(p.inv, Items.make("raw_fish", 1, sim.hour))
					sim.say("You spear a fish", Color(0.7, 0.9, 1.0))
				else:
					sim.say("The fish are faster than you", Color(0.8, 0.8, 0.8)))))
	if Inv.has_tag(p.inv, "fishing"):
		out.append(_opt("Fish", func():
			p.start_action("Fishing", 8.0, func():
				var stock: float = sim.fish_stock(t["x"], t["y"])
				var hod: float = sim.hour_of_day()
				var dawn_dusk: bool = (hod >= 4.0 and hod < 7.0) or (hod >= 18.0 and hod < 21.0)
				var ch: float = (0.35 + p.skill_level("fishing") * 0.06) * stock * (1.35 if dawn_dusk else 1.0) * (0.6 if float(sim.weather["temp"]) < 2.0 else 1.0)
				p.add_xp("fishing", 10.0)
				if randf() < ch:
					sim.take_fish(t["x"], t["y"])
					Inv.add(p.inv, Items.make("raw_fish", 1, sim.hour))
					sim.say("You caught a fish", Color(0.7, 0.9, 1.0))
					sim.emit_fx("pickup", p.pos)
				else:
					sim.say("Nothing bites", Color(0.8, 0.8, 0.8)))))
	return out

static func _drink_barrel(sim: Sim, x: int, y: int) -> void:
	var e: Dictionary = sim.world.ent(x, y)
	if float(e.get("w", 0.0)) < 1.0:
		sim.say("The collector is empty", Color(0.8, 0.8, 0.9))
		return
	e["w"] = float(e["w"]) - 1.0
	_drink_source(sim, randf() < 0.3, 1)

static func _fill_barrel(sim: Sim, x: int, y: int) -> void:
	var e: Dictionary = sim.world.ent(x, y)
	var have: int = int(e.get("w", 0.0))
	if have < 1:
		sim.say("The collector is empty", Color(0.8, 0.8, 0.9))
		return
	var used: int = _fill(sim, true, have)
	e["w"] = float(e["w"]) - used

# ------------------------------------------------------------------ fire / generator
static func _fire_options(sim: Sim, x: int, y: int) -> Array:
	var w: World = sim.world
	var p: Player = sim.player
	var e: Dictionary = w.ent(x, y)
	if e.is_empty():
		e = {"k": "fire", "fuel": 0.0, "lit": false}
		w.set_ent(x, y, e)
	var out: Array = []
	var fuel_item: Dictionary = {}
	for it in p.inv:
		if Items.def(it["id"]).has("fuel") and not p.is_equipped(it):
			fuel_item = it
			break
	if not fuel_item.is_empty():
		out.append(_opt("Add fuel: %s" % Items.def(fuel_item["id"])["n"], func():
			var one: Dictionary = Inv.split(p.inv, fuel_item, 1)
			e["fuel"] = float(e["fuel"]) + float(Items.def(one["id"])["fuel"])
			sim.say("Fuel for about %.1f hours" % float(e["fuel"]), Color(1.0, 0.85, 0.6))))
	if not e["lit"]:
		out.append(_opt("Light fire", func():
			var lighter: Dictionary = Inv.find_tag(p.inv, "fire")
			if lighter.is_empty():
				sim.say("You need a lighter or matches", Color(0.9, 0.8, 0.6))
				return
			if float(e["fuel"]) <= 0.0:
				sim.say("Add fuel first", Color(0.9, 0.8, 0.6))
				return
			if float(sim.weather["rain"]) > 0.5 and w.bld(x, y) == 0:
				sim.say("It is raining too hard", Color(0.9, 0.8, 0.6))
				return
			p.start_action("Lighting fire", 2.5, func():
				Inv.use_charge(p.inv, lighter)
				e["lit"] = true
				w.set_obj(x, y, Defs.ocell(Defs.O_CAMPFIRE, 0, 1))
				sim.fires.append(Vector2i(x, y)))))
	else:
		out.append(_opt("Cook", func(): sim.ui_events.append({"type": "craft", "cat": "Cooking"})))
		out.append(_opt("Put out", func():
			e["lit"] = false
			w.set_obj(x, y, Defs.ocell(Defs.O_CAMPFIRE, 0, 0))
			sim.fires.erase(Vector2i(x, y))))
	return out

static func _gen_options(sim: Sim, x: int, y: int) -> Array:
	var w: World = sim.world
	var p: Player = sim.player
	var e: Dictionary = w.ent(x, y)
	if e.is_empty():
		e = {"k": "gen", "fuel": 0.0, "on": false}
		w.set_ent(x, y, e)
	var out: Array = []
	out.append(_opt(("Turn off (load %d of %d)" % [int(e.get("load", sim.loads_near(x, y, Sim.GEN_RANGE))), Sim.GEN_CAP]) if e["on"] else "Turn on (%.0f h fuel, %d appliances in reach)" % [float(e["fuel"]), sim.loads_near(x, y, Sim.GEN_RANGE)], func():
		if not e["on"] and float(e["fuel"]) <= 0.0:
			sim.say("The generator needs fuel", Color(0.9, 0.8, 0.6))
			return
		e["on"] = not e["on"]
		if e["on"]:
			sim.generators.append(Vector2i(x, y))
			sim.say("The generator rattles to life", Color(0.8, 0.9, 0.7))
		else:
			sim.generators.erase(Vector2i(x, y))))
	out.append(_opt("Refuel", func():
		var can: Dictionary = Inv.find_tag(p.inv, "fuel_can")
		if can.is_empty() or int(can.get("u", 0)) <= 0:
			sim.say("You need a gas can with fuel", Color(0.9, 0.8, 0.6))
			return
		p.start_action("Refuelling", 3.0, func():
			e["fuel"] = float(e["fuel"]) + float(int(can["u"])) * 6.0
			can["u"] = 0)))
	if p.skill_level("electrical") >= 1 and Inv.count(p.inv, "scrap_metal") > 0 and float(e.get("c", 1.0)) < 0.95:
		out.append(_opt("Repair (%d%%)" % int(float(e.get("c", 1.0)) * 100.0), func():
			p.start_action("Repairing generator", 6.0, func():
				if Inv.take(p.inv, "scrap_metal", 1):
					e["c"] = minf(1.0, float(e.get("c", 1.0)) + 0.2 + p.skill_level("electrical") * 0.05)
					p.add_xp("electrical", 20.0))))
	out.append(_opt("Pick up", func():
		if e["on"]:
			sim.say("Turn it off first", Color(0.9, 0.8, 0.6))
			return
		p.start_action("Lifting generator", 3.0, func():
			w.remove_object(x, y)
			Inv.add(p.inv, Items.make("generator_item", 1)))))
	return out

# ------------------------------------------------------------------ farming
static func _crop_ent(sim: Sim, x: int, y: int) -> Dictionary:
	var w: World = sim.world
	var e: Dictionary = w.ent(x, y)
	if e.is_empty():
		var cell: int = w.obj(x, y)
		var crop: String = Defs.obj(Defs.o_id(cell)).get("crop", "potato")
		var stage: int = Defs.o_part(cell)
		e = {"k": "crop", "t": crop, "s": stage, "g": float(Farming.GROW_HOURS[crop]) * float(mini(stage, 3)) / 3.0, "w": 40.0}
		w.set_ent(x, y, e)
	return e

static func _crop_options(sim: Sim, x: int, y: int) -> Array:
	var w: World = sim.world
	var p: Player = sim.player
	var e: Dictionary = _crop_ent(sim, x, y)
	var out: Array = []
	var stage: int = e["s"]
	if stage == 3:
		out.append(_opt("Harvest %s" % e["t"], func():
			p.start_action("Harvesting", 3.0, func():
				var yr: Array = Farming.YIELD[e["t"]]
				var n: int = randi_range(yr[0], yr[1]) + p.skill_level("farming") / 2
				Inv.add(p.inv, Items.make(e["t"], n, sim.hour))
				if randf() < 0.5 + p.skill_level("farming") * 0.05:
					Inv.add(p.inv, Items.make("seeds_" + String(e["t"]), 1 + randi() % 2))
				w.set_ent(x, y, {})
				w.set_obj(x, y, 0)
				p.add_xp("farming", 25.0)
				sim.say("Harvested %d %s" % [n, e["t"]], Color(0.75, 0.9, 0.7))
				sim.emit_fx("pickup", p.pos))))
	var can: Dictionary = Inv.find_tag(p.inv, "watering")
	if stage < 3 and not can.is_empty():
		out.append(_opt("Water plant", func():
			if int(can.get("u", 0)) <= 0:
				sim.say("The watering can is empty", Color(0.9, 0.8, 0.6))
				return
			p.start_action("Watering", 1.5, func():
				can["u"] = int(can["u"]) - 1
				e["w"] = minf(100.0, float(e["w"]) + 45.0)
				p.add_xp("farming", 3.0))))
	if e.get("ill", 0) == 1:
		var cure: Dictionary = Inv.find_tag(p.inv, "plant_cure")
		if not cure.is_empty():
			out.append(_opt("Treat mildew", func():
				Inv.use_charge(p.inv, cure)
				e["ill"] = 0
				e["ill_h"] = 0.0
				p.add_xp("farming", 10.0)
				sim.say("Sprayed. The leaves should recover.", Color(0.75, 0.9, 0.7))))
	if stage < 3 and e.get("f", 0) == 0 and Inv.count(p.inv, "fertilizer") > 0:
		out.append(_opt("Fertilise", func():
			var f: Dictionary = Inv.find(p.inv, "fertilizer")
			if not f.is_empty():
				Inv.use_charge(p.inv, f)
				e["f"] = 1))
	out.append(_opt("Inspect", func():
		var info: String = "%s: %s%s" % [String(e["t"]).capitalize(), Farming.STAGE_NAMES[stage], " — MILDEW, needs spraying" if e.get("ill", 0) == 1 else ""]
		if p.skill_level("farming") >= 1 and stage < 3:
			info += ", water %d%%" % int(e["w"])
			var left: float = float(Farming.GROW_HOURS[e["t"]]) - float(e["g"])
			info += ", ~%d h to harvest" % int(left)
		elif stage < 3:
			info += ", soil is %s" % ("dry" if float(e["w"]) < 15.0 else "moist")
		sim.say(info, Color(0.8, 0.9, 0.75))))
	out.append(_opt("Dig up", func():
		w.set_ent(x, y, {})
		w.set_obj(x, y, 0)))
	return out

static func _soil_options(sim: Sim, t: Dictionary) -> Array:
	var p: Player = sim.player
	var w: World = sim.world
	var x: int = t["x"]
	var y: int = t["y"]
	var out: Array = []
	for it in p.inv:
		var d: Dictionary = Items.def(it["id"])
		if d.has("seed"):
			var crop: String = d["seed"]
			var seed_item: Dictionary = it
			out.append(_opt("Plant %s" % crop, func():
				p.start_action("Planting", 2.5, func():
					if w.obj(x, y) != 0 or not p.inv.has(seed_item):
						return
					Inv.use_charge(p.inv, seed_item)
					w.set_obj(x, y, Defs.ocell(int(Farming.CROP_OBJ[crop]), 0, 0))
					w.set_ent(x, y, {"k": "crop", "t": crop, "s": 0, "g": 0.0, "w": 25.0})
					p.add_xp("farming", 8.0))))
	if out.is_empty():
		out.append(_opt("Tilled soil — you need seeds", func(): sim.say("You have no seeds to plant", Color(0.8, 0.8, 0.8))))
	return out

# ------------------------------------------------------------------ containers near the player
## returns Array of {"label", "items": Array, "cap": float, "kind", "x","y"}
static func nearby_containers(sim: Sim) -> Array:
	var p: Player = sim.player
	var w: World = sim.world
	var px: int = floori(p.pos.x)
	var py: int = floori(p.pos.y)
	var out: Array = []
	var seen: Dictionary = {}
	for dy in range(-1, 2):
		for dx in range(-1, 2):
			var x: int = px + dx
			var y: int = py + dy
			if (dx != 0 or dy != 0) and not w.los(p.pos.x, p.pos.y, x + 0.5, y + 0.5):
				continue
			var cell: int = w.obj(x, y)
			if cell != 0:
				var d: Dictionary = Defs.obj(Defs.o_id(cell))
				if d.has("c"):
					var a: Vector2i = w.anchor_of(x, y)
					if not seen.has(a):
						seen[a] = true
						out.append({"label": d["n"], "items": w.container_at(x, y), "cap": float(d.get("cap", 20)), "kind": "obj", "x": a.x, "y": a.y,
							"cold": (Defs.o_id(cell) == Defs.O_FRIDGE or Defs.o_id(cell) == Defs.O_FREEZER) and sim.has_power(x, y)})
			if dx != 0 or dy != 0:
				var gi: Array = w.items_at(x, y)
				if not gi.is_empty():
					out.append({"label": "Ground nearby", "items": gi, "cap": 9999.0, "kind": "ground", "x": x, "y": y})
	for cy in range((py - 2) >> 4, ((py + 2) >> 4) + 1):
		for cx in range((px - 2) >> 4, ((px + 2) >> 4) + 1):
			var ch: Chunk = w.chunk(cx, cy)
			if ch == null:
				continue
			for cp in ch.corpses:
				if Vector2(cp["x"], cp["y"]).distance_to(p.pos) < 1.4:
					if not cp.has("loot"):
						var rng: RandomNumberGenerator = Rng.make(Rng.h2(int(float(cp["x"]) * 16.0), int(float(cp["y"]) * 16.0), sim.seed_v + int(float(cp["h"]) * 10.0)))
						cp["loot"] = Loot.roll(cp.get("lt", "corpse"), "", rng, sim.hour, float(sim.settings["loot"]))
						ch.touched = true
					out.append({"label": "Corpse", "items": cp["loot"], "cap": 20.0, "kind": "corpse", "x": floori(cp["x"]), "y": floori(cp["y"]), "ref": cp})
	# the tile under the player is always available as "Ground"
	var c0: Chunk = w.chunk_at(px, py)
	if c0 != null:
		var gi2: int = World.idx(px, py)
		if not c0.items.has(gi2):
			c0.items[gi2] = []
		out.push_front({"label": "Ground", "items": c0.items[gi2], "cap": 9999.0, "kind": "ground", "x": px, "y": py})
	return out

# ------------------------------------------------------------------ crafting & building
## where a build recipe would be placed: {"ok", "x", "y", "side", "why"}
static func build_target(sim: Sim, r: Dictionary) -> Dictionary:
	var p: Player = sim.player
	var w: World = sim.world
	var b: Dictionary = r["build"]
	if b.has("wall"):
		var e: Vector3i = p.front_edge()
		if w.wall(e.x, e.y, e.z) != 0:
			return {"ok": false, "why": "There is already something on that edge", "x": e.x, "y": e.y, "side": e.z}
		if not w.is_loaded(e.x, e.y):
			return {"ok": false, "why": "Out of reach"}
		return {"ok": true, "x": e.x, "y": e.y, "side": e.z}
	var ft: Vector2i = p.front_tile()
	if b.has("ground"):
		var g: int = w.ground(ft.x, ft.y)
		if b.get("natural", 0) == 1 and not Defs.ground_is_natural(g):
			return {"ok": false, "why": "You can only dig in soil or grass", "x": ft.x, "y": ft.y, "side": -1}
		if w.obj(ft.x, ft.y) != 0 or Defs.ground_is_water(g) or g == Defs.G_VOID:
			return {"ok": false, "why": "The tile in front is not clear", "x": ft.x, "y": ft.y, "side": -1}
		if g == int(b["ground"]):
			return {"ok": false, "why": "Already done here", "x": ft.x, "y": ft.y, "side": -1}
		return {"ok": true, "x": ft.x, "y": ft.y, "side": -1}
	if b.has("roof"):
		if w.bld(ft.x, ft.y) != 0:
			return {"ok": false, "why": "There is already a roof over that tile", "x": ft.x, "y": ft.y, "side": -1}
		if w.ground(ft.x, ft.y) == Defs.G_VOID or Defs.ground_is_water(w.ground(ft.x, ft.y)):
			return {"ok": false, "why": "Nothing to build over", "x": ft.x, "y": ft.y, "side": -1}
		var held: bool = w.wall(ft.x, ft.y, 0) != 0 or w.wall(ft.x, ft.y, 1) != 0 or w.wall(ft.x, ft.y + 1, 0) != 0 or w.wall(ft.x + 1, ft.y, 1) != 0
		for dd in [Vector2i(1, 0), Vector2i(-1, 0), Vector2i(0, 1), Vector2i(0, -1)]:
			if w.bld(ft.x + dd.x, ft.y + dd.y) != 0: held = true
		if not held:
			return {"ok": false, "why": "A roof needs a wall or another roof beside it to rest on", "x": ft.x, "y": ft.y, "side": -1}
		return {"ok": true, "x": ft.x, "y": ft.y, "side": -1}
	var id: int = b["obj"]
	var fs: Vector2i = Defs.obj_size(id, int(b.get("rot", 0)))
	for j in range(fs.y):
		for i in range(fs.x):
			var cellr := Rect2(Vector2(ft.x + i, ft.y + j), Vector2.ONE)
			for z in sim.zombies.list:
				if cellr.has_point(z.pos): return {"ok": false, "why": "Something is standing there", "x": ft.x, "y": ft.y, "side": -1}
			for n in sim.npcs.list:
				if not p.carrying.is_empty() and n.state == NpcSim.FOLLOW: continue     # the one holding the other end steps aside
				if cellr.has_point(n.pos): return {"ok": false, "why": "%s is standing there" % n.name, "x": ft.x, "y": ft.y, "side": -1}
			if Defs.o_id(w.obj(ft.x + i, ft.y + j)) == Defs.O_STAIRS:
				return {"ok": false, "why": "Not across the stairs", "x": ft.x, "y": ft.y, "side": -1}
			if w.tile_blocked(ft.x + i, ft.y + j) or w.obj(ft.x + i, ft.y + j) != 0 or Defs.ground_is_water(w.ground(ft.x + i, ft.y + j)):
				return {"ok": false, "why": "Not enough clear space in front of you", "x": ft.x, "y": ft.y, "side": -1}
	return {"ok": true, "x": ft.x, "y": ft.y, "side": -1}

static func craft(sim: Sim, r: Dictionary) -> bool:
	var p: Player = sim.player
	var w: World = sim.world
	var why: String = Recipes.missing(r, p, sim.near_heat(p.pos), sim.near_workbench(p.pos), sim.stations(p.pos))
	if why != "":
		sim.say("Can't make that: " + why, Color(1.0, 0.8, 0.5))
		return false
	if r.has("build"):
		var bt: Dictionary = build_target(sim, r)
		if not bt["ok"]:
			sim.say(bt["why"], Color(1.0, 0.8, 0.5))
			return false
	var skill: String = ""
	if r.has("xp"):
		skill = r["xp"][0]
	var dur: float = float(r["time"]) * (1.0 - (p.skill_level(skill) * 0.04 if skill != "" else 0.0))
	var hammering: bool = (r["tools"] as Array).has("hammer")
	p.start_action(r["n"], dur, func():
		if Recipes.missing(r, p, sim.near_heat(p.pos), sim.near_workbench(p.pos), sim.stations(p.pos)) != "":
			return
		sim.flags["crafted"] = true
		p.bored = maxf(0.0, p.bored - 4.0)
		var target: Dictionary = {}
		if r.has("build"):
			target = build_target(sim, r)
			if not target["ok"]:
				sim.say(target["why"], Color(1.0, 0.8, 0.5))
				return
		for inp in r["in"]:
			if inp[0] == "water":
				p.consume_water(int(inp[1]))
			else:
				for k in range(int(inp[1])):
					var it: Dictionary = Inv.find(p.inv, inp[0])
					if it.is_empty():
						break
					p.unequip(it) if int(it.get("n", 1)) <= 1 else null
					if it.has("u") and (inp[0] == "disinfectant" or inp[0] == "duct_tape" or inp[0] == "glue" or inp[0] == "salt"):
						Inv.use_charge(p.inv, it)
					else:
						Inv.split(p.inv, it, 1)
		var sp: String = r.get("special", "")
		if sp == "patch" and not Recipes.patch_target(p).is_empty():
			var tl: int = p.skill_level("tailoring")
			var garment: Dictionary = Recipes.patch_target(p)
			garment["c"] = minf(1.0, float(garment.get("c", 1.0)) + 0.25 + tl * 0.04)
			if int(garment.get("pt", 0)) < 3 and tl >= 1:
				garment["pt"] = int(garment.get("pt", 0)) + 1
			sim.say("Patched. It will take a few more bites.", Color(0.75, 0.9, 0.7))
		elif (sp == "repair_tape" or sp == "repair_glue" or sp == "sharpen") and not p.weapon.is_empty():
			var ml: int = p.skill_level("maintenance")
			var times: int = int(p.weapon.get("rp", 0))
			if sp == "sharpen":
				p.weapon["sh"] = minf(1.0, float(p.weapon.get("sh", 1.0)) + 0.5 + ml * 0.06)
				sim.say("The edge is keen again (%d%%)." % int(float(p.weapon["sh"]) * 100.0), Color(0.75, 0.9, 0.7))
			else:
				var base: float = 0.35 if sp == "repair_tape" else 0.5
				p.weapon["c"] = minf(1.0, float(p.weapon.get("c", 1.0)) + base * (1.0 + ml * 0.06) / (1.0 + times * 0.5))
				p.weapon["rp"] = times + 1
				sim.say("Condition now %d%%. Each repair holds a little less." % int(float(p.weapon["c"]) * 100.0), Color(0.75, 0.9, 0.7))
		if sp == "purify_bleach":
			var bl: Dictionary = Inv.find_tag(p.inv, "bleach")
			if not bl.is_empty():
				Inv.use_charge(p.inv, bl)
			for it in p.inv:
				if it.has("d") and Items.def(it["id"]).has("water"):
					it.erase("d")
			sim.say("A few drops, a few minutes. The water is safe.", Color(0.7, 0.85, 1.0))
		if r.get("special", "") == "purify":
			for it in p.inv:
				if it.has("d") and Items.def(it["id"]).has("water"):
					it.erase("d")
			sim.say("The water is safe to drink now", Color(0.7, 0.85, 1.0))
		var cooking: bool = r["cat"] == "Cooking" and r.get("near", "") == "heat" and not r.has("special")
		var cl: int = p.skill_level("cooking")
		if cooking and randf() < maxf(0.0, 0.16 - cl * 0.03):
			# an unwatched pan
			Inv.add_new(p.inv, "burnt_food", 1, sim.hour)
			sim.say("You burn it.", Color(1.0, 0.7, 0.5))
			if randf() < 0.25:
				p.add_wound(9 + randi() % 2, "burn", "hot pan")
		else:
			for o in r.get("out", []):
				var qty: int = int(o[1])
				if r.has("butcher") and Items.def(o[0]).has("raw"):
					# a practised hand wastes less
					qty = maxi(1, int(round(float(qty) * (0.6 + 0.1 * minf(6.0, float(p.skill_level("butchering")))))))
				Inv.add_new(p.inv, o[0], qty, sim.hour)
				if cooking and cl > 0:
					var made: Dictionary = Inv.find(p.inv, o[0])
					if not made.is_empty():
						made["q"] = 1.0 + cl * 0.04
		if r.has("build"):
			var b: Dictionary = r["build"]
			if b.has("wall"):
				w.set_wall(target["x"], target["y"], target["side"], Defs.wall(int(b["wall"]), int(b.get("shape", 0))), int(b.get("state", 0)))
			elif b.has("roof"):
				w.set_roof(target["x"], target["y"], World.PLAYER_BLD)
				sim.alarms_done[World.PLAYER_BLD] = true
			elif b.has("ground"):
				w.set_ground(target["x"], target["y"], int(b["ground"]))
				var oc: int = w.obj(target["x"], target["y"])
				if oc != 0:
					w.set_obj(target["x"], target["y"], 0)
			else:
				var id: int = b["obj"]
				var fs: Vector2i = Defs.obj_size(id, 0)
				for j in range(fs.y):
					for i in range(fs.x):
						w.set_obj(int(target["x"]) + i, int(target["y"]) + j, Defs.ocell(id, 0, j * fs.x + i))
				if id == Defs.O_RAIN_BARREL:
					w.set_ent(target["x"], target["y"], {"k": "barrel", "w": 0.0})
				elif id == Defs.O_CAMPFIRE:
					w.set_ent(target["x"], target["y"], {"k": "fire", "fuel": 1.0, "lit": false})
				elif id == Defs.O_BATTERY_BANK:
					w.set_ent(target["x"], target["y"], {"k": "bank", "w": 0.0})
				elif id == Defs.O_SOLAR:
					w.set_ent(target["x"], target["y"], {"k": "solar"})
		if r.has("xp"):
			p.add_xp(r["xp"][0], float(r["xp"][1]))
		if hammering:
			sim.noise(p.pos, 13.0)
		sim.emit_fx("build" if r.has("build") or hammering else "pickup", p.pos))
	return true

# ------------------------------------------------------------------ carrying furniture
static func movable(sim: Sim, ax: int, ay: int) -> bool:
	var cell: int = sim.world.obj(ax, ay)
	if cell == 0:
		return false
	var id: int = Defs.o_id(cell)
	var d: Dictionary = Defs.obj(id)
	if Vehicle.is_vehicle(id) or id == Defs.O_CAR_WRECK or id == Defs.O_DUMPSTER or id == Defs.O_COOP or id == Defs.O_SIGN:
		return false
	var e: Dictionary = sim.world.ent(ax, ay)
	if e.get("lit", false) or e.get("on", false):
		return false
	return d.has("scrap") or (d.has("c") and int(d.get("hp", 100)) < 900) or LIGHT_MOVABLE.has(id)

static func _pick_up(sim: Sim, ax: int, ay: int) -> void:
	var p: Player = sim.player
	var w: World = sim.world
	var id: int = Defs.o_id(w.obj(ax, ay))
	if HEAVY.has(id) and p.skill_level("strength") < 6:
		var helper := false
		for n in sim.npcs.list:
			if n.state == NpcSim.FOLLOW and n.pos.distance_to(p.pos) < 4.0: helper = true
		if not helper:
			sim.say("Too heavy to lift alone. Strength 6, or someone to take the other end.", Color(0.9, 0.8, 0.6))
			return
	p.start_action("Lifting", 2.0 if not HEAVY.has(id) else 4.0, func():
		var cell: int = w.obj(ax, ay)
		if cell == 0 or Defs.o_id(cell) != id or not p.carrying.is_empty():
			return
		var d: Dictionary = Defs.obj(id)
		var contents: Array = []
		if d.has("c"):
			contents = w.container_at(ax, ay)       # rolls its loot now if nobody has looked yet
		var c: Chunk = w.chunk_at(ax, ay)
		var ai: int = World.idx(ax, ay)
		var ent: Dictionary = c.ents.get(ai, {})
		c.containers.erase(ai)
		c.ents.erase(ai)
		w.remove_object(ax, ay)
		p.carrying = {"o": id, "rot": Defs.o_rot(cell), "items": contents, "ent": ent}
		p.endurance = maxf(0.0, p.endurance - (8.0 if not HEAVY.has(id) else 20.0))
		sim.noise(p.pos, 6.0)
		sim.emit_fx("build", p.pos)
		sim.say("You lift the %s%s. USE to set it down." % [String(d["n"]).to_lower(), " and everything in it" if contents.size() > 0 else ""], Color(0.8, 0.85, 0.9)))

static func carry_recipe(p: Player) -> Dictionary:
	return {"n": Defs.obj(int(p.carrying["o"]))["n"], "carry": 1, "build": {"obj": int(p.carrying["o"]), "rot": int(p.carrying.get("rot", 0))}}

static func place_carried(sim: Sim) -> bool:
	var p: Player = sim.player
	var w: World = sim.world
	if p.carrying.is_empty():
		return false
	var bt: Dictionary = build_target(sim, carry_recipe(p))
	if not bt["ok"]:
		sim.say(bt["why"], Color(1.0, 0.8, 0.5))
		return false
	var id: int = p.carrying["o"]
	var rot: int = p.carrying.get("rot", 0)
	var fs: Vector2i = Defs.obj_size(id, rot)
	var tx: int = bt["x"]
	var ty: int = bt["y"]
	for j in range(fs.y):
		for i in range(fs.x):
			w.set_obj(tx + i, ty + j, Defs.ocell(id, rot, j * fs.x + i))
	var c: Chunk = w.chunk_at(tx, ty)
	if Defs.obj(id).has("c"):
		c.containers[World.idx(tx, ty)] = p.carrying.get("items", [])
	if not (p.carrying.get("ent", {}) as Dictionary).is_empty():
		w.set_ent(tx, ty, p.carrying["ent"])
	c.touched = true
	p.carrying = {}
	sim.noise(p.pos, 6.0)
	sim.emit_fx("build", p.pos)
	return true

## place a carried placeable item (generator, bedroll) in front of the player
static func place_item(sim: Sim, it: Dictionary) -> void:
	var p: Player = sim.player
	var w: World = sim.world
	var d: Dictionary = Items.def(it["id"])
	var id: int = d["place"]
	var ft: Vector2i = p.front_tile()
	if w.tile_blocked(ft.x, ft.y) or w.obj(ft.x, ft.y) != 0:
		sim.say("No room in front of you", Color(1.0, 0.8, 0.5))
		return
	if id == Defs.O_SNARE and (not Defs.ground_is_natural(w.ground(ft.x, ft.y)) or w.bld(ft.x, ft.y) != 0):
		sim.say("Snares need open ground", Color(1.0, 0.8, 0.5))
		return
	Inv.split(p.inv, it, 1)
	w.set_obj(ft.x, ft.y, Defs.ocell(id, 0, 0))
	if id == Defs.O_GENERATOR:
		w.set_ent(ft.x, ft.y, {"k": "gen", "fuel": 0.0, "on": false, "c": 1.0})
	elif id == Defs.O_SNARE:
		w.set_ent(ft.x, ft.y, {"k": "trap", "h": sim.hour, "bait": 0, "caught": ""})
		p.add_xp("trapping", 6.0)
	sim.emit_fx("build", p.pos)
