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
			touch(5, Vector2(size.x * 0.5, size.y * 0.3), true)      # pinch
			touch(6, Vector2(size.x * 0.5 + 100, size.y * 0.3), true)
			p0 = Vector2(main.view.zoom, 0)
		172: drag(6, Vector2(size.x * 0.5 + 220, size.y * 0.3), Vector2(120, 0))
		175:
			ok(main.view.zoom > p0.x * 1.3, "two-finger pinch zooms the camera (%.2f -> %.2f)" % [p0.x, main.view.zoom])
			touch(5, Vector2.ZERO, false)
			touch(6, Vector2.ZERO, false)
		180:
			print("")
			print("RESULT: %d checks, %d failed" % [checks, fails])
			SaveGame.delete(main.SLOT)
			quit(1 if fails > 0 else 0)
	return false
