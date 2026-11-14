extends SceneTree
## Multi-touch control test against the real main scene (synthetic InputEventScreenTouch/Drag).
## godot --headless --path . -s tests/godot/test_touch.gd
var main: Node
var frame := 0
var t0 := -1
var fails := 0
var checks := 0
var p0 := Vector2.ZERO
var door := Vector3i(-1, -1, -1)
var sc: ScrollContainer = null

func _find_scroll(n: Node) -> ScrollContainer:
	for ch in n.get_children():
		if ch is ScrollContainer:
			return ch
		var r: ScrollContainer = _find_scroll(ch)
		if r != null:
			return r
	return null

func ok(cond: bool, what: String) -> void:
	checks += 1
	if not cond: fails += 1
	print("  %s  %s" % ["PASS" if cond else "FAIL", what])

func touch(i: int, pos: Vector2, pressed: bool) -> void:
	var e := InputEventScreenTouch.new()
	e.index = i
	e.position = root.get_final_transform() * pos      # viewport -> window coordinates
	e.pressed = pressed
	Input.parse_input_event(e)

func drag(i: int, pos: Vector2, rel: Vector2) -> void:
	var e := InputEventScreenDrag.new()
	e.index = i
	e.position = root.get_final_transform() * pos
	e.relative = root.get_final_transform().basis_xform(rel)
	Input.parse_input_event(e)

func _initialize() -> void:
	main = load("res://main.tscn").instantiate()
	root.add_child(main)

func _process(_dt: float) -> bool:
	frame += 1
	if main.state == "title" and t0 < 0:
		main.new_game(777, "builder", {})
		main.sim.zombies.list.clear()
		main.sim.zombies.wander_t = 99999.0
		main.sim.settings["god"] = true
		t0 = frame
		return false
	if main.state != "play":
		if frame > 2000:
			print("boot timeout")
			quit(1)
		return false
	var f: int = frame - t0
	var sim: Sim = main.sim
	var p: Player = sim.player
	var hud: Hud = main.hud
	var size: Vector2 = root.get_visible_rect().size
	match f:
		5:
			print("== touch controls (viewport %s)" % size)
			# stand in the open so movement is unobstructed
			for r in range(4, 40):
				var q: Vector2 = sim.safe_pos + Vector2(r, 0)
				if sim.world.bld(floori(q.x), floori(q.y)) == 0 and not sim.world.blocked(q.x, q.y, 0.3) and sim.world.walk_clear(q.x, q.y, q.x + 3.0, q.y + 3.0):
					p.pos = q
					break
			sim.zombies.list.clear()
			p0 = p.pos
			touch(0, Vector2(130, size.y - 160), true)
		8: drag(0, Vector2(210, size.y - 160), Vector2(80, 0))
		30:
			ok(hud.move.x > 0.9 and absf(hud.move.y) < 0.2, "joystick drag produces full right input (%.2f, %.2f)" % [hud.move.x, hud.move.y])
			ok(p.pos.distance_to(p0) > 0.8, "player walks while the stick is held (%.2f tiles)" % p.pos.distance_to(p0))
			ok(p.pos.x > p0.x and p.pos.y < p0.y, "screen-right maps to world (+x, -y)")
			# second finger: attack while still moving
			var a: Vector2 = hud._btn["attack"][0]
			touch(1, a, true)
		34:
			ok(p.swing_t > 0.0, "second finger attacks while the first keeps moving")
			ok(hud.move.x > 0.9, "movement input unaffected by the attack touch")
		40: touch(1, hud._btn["attack"][0], false)
		44:
			var before: Vector2 = p.pos
			p0 = before
		60:
			ok(p.pos.distance_to(p0) > 0.3, "still moving after attack finger lifts")
			drag(0, Vector2(130, size.y - 240), Vector2(-80, -80))
		75:
			ok(hud.move.y < -0.5, "dragging up changes direction (%.2f, %.2f)" % [hud.move.x, hud.move.y])
			touch(0, Vector2(130, size.y - 240), false)
		80:
			ok(hud.move == Vector2.ZERO, "releasing the stick clears input")
			p0 = p.pos
		95:
			ok(p.pos.distance_to(p0) < 0.02, "player stops when the stick is released")
			# toggles
			touch(2, hud._btn["sneak"][0], true)
			touch(2, hud._btn["sneak"][0], false)
		98:
			ok(p.sneaking, "SNEAK button toggles sneaking")
			touch(2, hud._btn["run"][0], true)
			touch(2, hud._btn["run"][0], false)
		101:
			ok(hud.run_on and not p.sneaking, "RUN toggles on and cancels sneak")
			touch(2, hud._btn["run"][0], true)
			touch(2, hud._btn["run"][0], false)
			# USE on a door
			var w: World = sim.world
			var px := floori(sim.safe_pos.x)
			var py := floori(sim.safe_pos.y)
			for y in range(py - 12, py + 12):
				for x in range(px - 12, px + 12):
					for s in range(2):
						var wid := w.wall(x, y, s)
						if wid != 0 and (wid & 3) == Defs.WS_DOOR and not Defs.wall_is_fence(wid) and door.x < 0:
							door = Vector3i(x, y, s)
			w.set_edge_state(door.x, door.y, door.z, 0)
			p.pos = Vector2(door.x + 0.5, door.y + 0.5)
			p.facing = Vector2(0, -1) if door.z == 0 else Vector2(-1, 0)
		104:
			touch(3, hud._btn["interact"][0], true)
		106:
			touch(3, hud._btn["interact"][0], false)
		110:
			ok((sim.world.edge_state(door.x, door.y, door.z) & Defs.ES_OPEN) != 0, "tapping USE opens the door in front")
			Inv.add_new(p.inv, "plank", 2)               # makes "Barricade" available -> more than one option
			touch(3, hud._btn["interact"][0], true)      # long press -> options menu
		150:
			ok(main.panels.current == "menu", "holding USE opens the options menu (%s)" % main.panels.current)
			touch(3, hud._btn["interact"][0], false)
			main.panels.close()
		155:
			touch(4, hud._btn["inv"][0], true)
			touch(4, hud._btn["inv"][0], false)
		158:
			ok(main.panels.current == "inv", "BAG button opens the inventory")
			var h0: float = sim.hour
			p0 = Vector2(h0, 0)
		170:
			ok(absf(sim.hour - p0.x) < 0.000001, "simulation is paused while a panel is open")
			main.panels.close()
			main.panels.open("journal")
			ok(main.panels.current == "journal" and main.panels.body.get_child_count() > 0, "the journal opens and lists what you know")
			main.panels.open("import")
			ok(main.panels.current == "import" and main.panels.body.get_child_count() > 2, "the save import screen opens")
			main.panels.open("settings")
			var vib := false
			for cb in main.panels.body.get_children():
				if cb is Button and String(cb.text).begins_with("Vibration"): vib = true
			ok(vib, "settings offer a vibration switch")
			main.panels.close()
			sim.player.carrying = {"o": Defs.O_CRATE, "rot": 0, "items": []}
			main.view._sync_carry(sim.player)
			ok(main.view.carry_handle() >= 0, "furniture you carry is drawn in your arms")
			sim.player.carrying = {}
			main.view._sync_carry(sim.player)
			ok(main.view.carry_handle() < 0, "and gone once set down")
			ok(Art.char_frames.has("s_carry") and (Art.char_frames["s_carry"] as Array).size() == 5 and Art.char_frames.has("s_vault") and Art.char_frames.has("s_reload"), "carry, climb and reload frames are painted in all five directions")
			touch(5, Vector2(size.x * 0.5, size.y * 0.3), true)      # pinch
			touch(6, Vector2(size.x * 0.5 + 100, size.y * 0.3), true)
			p0 = Vector2(main.view.zoom, 0)
		172: drag(6, Vector2(size.x * 0.5 + 220, size.y * 0.3), Vector2(120, 0))
		175:
			ok(main.view.zoom > p0.x * 1.3, "two-finger pinch zooms the camera (%.2f -> %.2f)" % [p0.x, main.view.zoom])
			touch(5, Vector2.ZERO, false)
			touch(6, Vector2.ZERO, false)
		180:
			# list scrolling: a finger that lands on a row must scroll the list, not press the row
			main.panels.open("craft", {"cat": "Carpentry"})
		186:
			sc = _find_scroll(main.panels.body)
			ok(sc != null, "crafting panel has a scroll list")
			if sc != null:
				# make sure the list is longer than the panel on any screen size
				for k in range(24):
					sc.get_child(0).add_child(UiKit.button("filler row %d" % k, func(): main.panels.close()))
		187:
			if sc != null:
				print("    touchscreen=", DisplayServer.is_touchscreen_available(), " list height=", sc.get_child(0).size.y, " view=", sc.size.y)
				var c: Vector2 = sc.get_global_rect().get_center()
				touch(7, c + Vector2(0, 120), true)
		188:
			if sc != null:
				var c2: Vector2 = sc.get_global_rect().get_center()
				drag(7, c2 + Vector2(0, 60), Vector2(0, -60))
		190:
			if sc != null:
				var c3: Vector2 = sc.get_global_rect().get_center()
				drag(7, c3 + Vector2(0, -80), Vector2(0, -140))
		192:
			if sc != null:
				var c4: Vector2 = sc.get_global_rect().get_center()
				touch(7, c4 + Vector2(0, -80), false)
		196:
			if sc != null:
				ok(sc.scroll_vertical > 20, "dragging on a list row scrolls the list (%d px)" % sc.scroll_vertical)
				ok(main.panels.current == "craft" and p.action.is_empty(), "the drag did not trigger the row underneath")
			main.panels.close()
		200:
			touch(1, main.hud._btn["speed"][0], true)
			touch(1, main.hud._btn["speed"][0], false)
		203:
			ok(sim.speed == 2, "the time button fast-forwards (x%d)" % sim.speed)
			var h0: float = sim.hour
			main._play(1.0 / 30.0)
			ok(sim.hour - h0 > 0.0, "and the clock runs")
			var zt: Zombie = sim.zombies.spawn(p.pos + Vector2(2, 0), 0)
			zt.state = Zombie.CHASE
			sim.settings["god"] = true
		205:
			ok(sim.speed == 1, "fast-forward drops out when something is chasing you")
			sim.zombies.list.clear()
			sim.noises.clear()
			touch(1, main.hud._btn["call"][0], true)
			touch(1, main.hud._btn["call"][0], false)
		207:
			ok(sim.noises.size() > 0, "CALL makes a noise the infected can hear")
			ok(main.hud._btn.has("shove"), "a SHOVE button appears while a weapon is drawn")
			p.attack_cd = 0.0
			p.swing_t = 0.0
			if main.hud._btn.has("shove"):
				touch(1, main.hud._btn["shove"][0], true)
				touch(1, main.hud._btn["shove"][0], false)
		209:
			ok(p.force_shove and p.swing_t > 0.0, "SHOVE starts a shove, not a weapon swing")
			Inv.add_new(p.inv, "pistol", 1)
		214:
			var hi := -1
			for k in range(main.hud._hot.size()):
				if main.hud._hot[k]["id"] == "pistol": hi = k
			ok(hi >= 0, "weapons carried show up in the hotbar (%d slots)" % main.hud._hot.size())
			if hi >= 0:
				touch(1, main.hud._btn["hot%d" % hi][0], true)
				touch(1, main.hud._btn["hot%d" % hi][0], false)
		216:
			ok(not p.weapon.is_empty() and p.weapon["id"] == "pistol", "tapping a hotbar slot draws that weapon")
			for id in ["inv", "char", "craft", "map", "pause"]:
				main.open_panel(id)
				var opened: bool = main.panels.is_open() and main.panels.current == id
				main.panels.close()
				ok(opened and not main.panels.is_open(), "the %s panel opens and closes" % id)
			var v := Vehicle.new()
			v.sim = sim
			v.pos = p.pos
			v.ent = {"k": "car", "fuel": 5.0, "eng": 0.8, "bat": 1, "key": 1, "hot": 0, "tire": 1.0}
			sim.vehicle = v
		219:
			ok(not main.hud._btn.has("run") and not main.hud._btn.has("shove"), "on-foot buttons are hidden while driving")
			touch(1, main.hud._btn["attack"][0], true)
		222:
			ok(sim.brake, "holding the big button brakes")
			touch(1, main.hud._btn["attack"][0], false)
			sim.log.clear()
			touch(2, main.hud._btn["interact"][0], true)
			touch(2, main.hud._btn["interact"][0], false)
		225:
			ok(not sim.brake, "releasing it lets go of the brake")
			ok(sim.vehicle == null or sim.log.size() > 0, "EXIT gets out, or says why it cannot")
			sim.vehicle = null
		228:
			print("")
			print("RESULT: %d checks, %d failed" % [checks, fails])
			SaveGame.delete(main.SLOT)
			quit(1 if fails > 0 else 0)
	return false
