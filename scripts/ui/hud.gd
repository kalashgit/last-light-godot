class_name Hud
extends Control
## In-game HUD and all gameplay input. Everything here is multi-touch aware:
## each finger is tracked by index so moving, attacking and interacting never block each other.
## Keyboard: WASD/arrows move, Shift run, C sneak, Space attack, E interact (hold = options),
## R reload, F light, I inventory, H health, B craft, M map, Esc menu, +/- zoom.

const STICK_R := 74.0
const MOODLE_COLORS := [Color(0.82, 0.74, 0.34), Color(0.88, 0.56, 0.26), Color(0.86, 0.34, 0.24), Color(0.62, 0.14, 0.14)]

var main: Node
var sim: Sim
var view: WorldView
var move := Vector2.ZERO
var run_on := false
var placing: Dictionary = {}
var debug := false
var safe := Rect2(0, 0, 720, 1152)

var _stick_touch := -1
var _stick_origin := Vector2.ZERO
var _stick_vec := Vector2.ZERO
var _attack_touch := -1
var _interact_touch := -1
var _interact_t := 0.0
var _interact_fired := false
var _free: Dictionary = {}        # touch index -> [start pos, current pos, start time]
var _pinch_d := 0.0
var _btn: Dictionary = {}         # id -> [center, radius]
var _key_attack := false
var _key_interact_t := -1.0
var _target := ""
var _target_t := 0.0
var _fps_t := 0.0
var _frame_ms := 0.0
var _hot: Array = []              # quick-slot weapons shown in the hotbar

func _ready() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE

func reset_input() -> void:
	_stick_touch = -1
	_stick_vec = Vector2.ZERO
	_attack_touch = -1
	_interact_touch = -1
	_free.clear()
	move = Vector2.ZERO
	_key_attack = false
	_key_interact_t = -1.0

# ------------------------------------------------------------------ layout
func _layout() -> void:
	var r: float = safe.end.x
	var b: float = safe.end.y
	var t: float = safe.position.y
	_btn.clear()
	_btn["attack"] = [Vector2(r - 86, b - 100), 62.0]
	_btn["interact"] = [Vector2(r - 214, b - 78), 50.0]
	var p: Player = sim.player
	_hot.clear()
	if sim.vehicle == null:
		_btn["run"] = [Vector2(r - 66, b - 230), 40.0]
		_btn["sneak"] = [Vector2(r - 168, b - 198), 40.0]
		if not Inv.find(p.inv, "flashlight").is_empty() or not Inv.find(p.inv, "candle").is_empty():
			_btn["light"] = [Vector2(r - 262, b - 176), 32.0]
		if p.weapon_def().has("gun"):
			_btn["reload"] = [Vector2(r - 300, b - 64), 32.0]
		if not p.weapon_def().is_empty():
			_btn["shove"] = [Vector2(r - 52, b - 318), 34.0]
		_btn["call"] = [Vector2(r - 136, b - 290), 30.0]
		# hotbar: the first four weapons carried, one tap to draw
		for it in p.inv:
			var idf: Dictionary = Items.def(it["id"])
			if idf.has("wpn") or idf.has("gun"):
				_hot.append(it)
				if _hot.size() >= 4:
					break
		for hi in range(_hot.size()):
			_btn["hot%d" % hi] = [Vector2(r - 104 - hi * 60, t + 112), 27.0]
	_btn["speed"] = [Vector2(r - 34, t + 238), 26.0]
	var names: Array = ["menu", "map", "craft", "char", "inv"]
	for i in range(names.size()):
		_btn[names[i]] = [Vector2(r - 40 - i * 68, t + 40), 31.0]
	_btn["zoom_in"] = [Vector2(r - 34, t + 118), 26.0]
	_btn["zoom_out"] = [Vector2(r - 34, t + 178), 26.0]
	if not placing.is_empty():
		var py: float = b - (250.0 if safe.size.y > safe.size.x else 96.0)
		_btn["place_ok"] = [Vector2(safe.get_center().x - 70, py), 50.0]
		_btn["place_no"] = [Vector2(safe.get_center().x + 70, py), 50.0]
	if not p.carrying.is_empty():
		_btn["turn"] = [Vector2(r - 262, b - 176), 34.0]
	if sim.vehicle != null:
		_btn["horn"] = [Vector2(r - 168, b - 198), 36.0]
	_scale_buttons()

func _scale_buttons() -> void:
	if absf(Opts.btn - 1.0) > 0.01:
		for id in _btn.keys():
			_btn[id][1] = float(_btn[id][1]) * Opts.btn

func _hit(pos: Vector2) -> String:
	var best := ""
	var bd := 1e9
	for id in _btn.keys():
		var c: Vector2 = _btn[id][0]
		var d: float = pos.distance_to(c)
		if d <= float(_btn[id][1]) * 1.18 and d < bd:
			bd = d
			best = id
	return best

# ------------------------------------------------------------------ input
func _input(ev: InputEvent) -> void:
	if sim == null or main.state != "play" or main.panels.is_open():
		return
	if ev is InputEventScreenTouch:
		if ev.pressed:
			_touch_down(ev.index, ev.position)
		else:
			_touch_up(ev.index, ev.position)
	elif ev is InputEventScreenDrag:
		_touch_move(ev.index, ev.position)
	elif ev is InputEventKey and not ev.echo:
		_key(ev)

func _touch_down(i: int, pos: Vector2) -> void:
	var p: Player = sim.player
	if p.sleeping:
		sim.wake("You get up.")
		return
	var id: String = _hit(pos)
	match id:
		"attack":
			_attack_touch = i
		"interact":
			_interact_touch = i
			_interact_t = 0.0
			_interact_fired = false
		"run":
			run_on = not run_on
			if run_on: p.sneaking = false
		"sneak":
			p.sneaking = not p.sneaking
			if p.sneaking: run_on = false
		"light": toggle_light()
		"reload": p.reload()
		"horn":
			sim.noise(p.pos, 45.0)
			sim.emit_fx("alarm", p.pos)
			sim.say("The horn carries a long way.", Color(1.0, 0.85, 0.6))
		"turn":
			p.carrying["rot"] = (int(p.carrying.get("rot", 0)) + 1) % 4
		"shove": p.try_shove()
		"call": p.call_out(not p.sneaking)
		"speed": cycle_speed()
		"hot0", "hot1", "hot2", "hot3":
			var hi: int = int(id.substr(3))
			if hi < _hot.size():
				p.equip(_hot[hi])
				sim.emit_fx("equip", p.pos)
		"zoom_in": view.zoom = clampf(view.zoom * 1.2, 0.8, 3.0)
		"zoom_out": view.zoom = clampf(view.zoom / 1.2, 0.8, 3.0)
		"inv", "char", "craft", "map":
			main.open_panel(id)
		"menu":
			main.open_panel("pause")
		"place_ok":
			var r: Dictionary = placing
			if Actions.craft(sim, r):
				placing = {}
		"place_no":
			placing = {}
		_:
			var size: Vector2 = get_viewport_rect().size
			if _stick_touch < 0 and pos.x < size.x * 0.5 and pos.y > size.y * 0.4:
				_stick_touch = i
				_stick_origin = pos
				_stick_vec = Vector2.ZERO
			else:
				_free[i] = [pos, pos, Time.get_ticks_msec()]
				if _free.size() == 2:
					var ks: Array = _free.keys()
					_pinch_d = (_free[ks[0]][1] as Vector2).distance_to(_free[ks[1]][1])

func _touch_move(i: int, pos: Vector2) -> void:
	if i == _stick_touch:
		var d: Vector2 = pos - _stick_origin
		var sr: float = STICK_R * Opts.stick
		if d.length() > sr * 1.35:
			_stick_origin = pos - d.normalized() * sr * 1.35
			d = pos - _stick_origin
		_stick_vec = d.limit_length(sr) / sr
	elif _free.has(i):
		_free[i][1] = pos
		if _free.size() == 2:
			var ks: Array = _free.keys()
			var nd: float = (_free[ks[0]][1] as Vector2).distance_to(_free[ks[1]][1])
			if _pinch_d > 10.0 and nd > 10.0:
				view.zoom = clampf(view.zoom * nd / _pinch_d, 0.8, 3.0)
			_pinch_d = nd

func _touch_up(i: int, pos: Vector2) -> void:
	if i == _stick_touch:
		_stick_touch = -1
		_stick_vec = Vector2.ZERO
	if i == _attack_touch:
		_attack_touch = -1
	if i == _interact_touch:
		_interact_touch = -1
		if not _interact_fired:
			Actions.interact(sim, false)
	if _free.has(i):
		var f: Array = _free[i]
		var was_single: bool = _free.size() == 1
		_free.erase(i)
		if was_single and (f[0] as Vector2).distance_to(pos) < 16.0 and Time.get_ticks_msec() - int(f[2]) < 350:
			_world_tap(pos)

func _world_tap(pos: Vector2) -> void:
	var p: Player = sim.player
	if not p.alive:
		return
	var wp: Vector2 = view.screen_to_world(pos)
	var d: Vector2 = wp - p.pos
	if d.length() > 0.25 and p.swing_t <= 0.0:
		p.facing = d.normalized()
		p.dir8 = Iso.dir8(p.facing)
	if d.length() < 1.7:
		Actions.interact(sim, false)

func cycle_speed() -> void:
	if sim.threatened():
		sim.speed = 1
		sim.say("Not while something is hunting you", Color(0.9, 0.8, 0.6))
		return
	sim.speed = 2 if sim.speed == 1 else (4 if sim.speed == 2 else 1)

func toggle_light() -> void:
	var p: Player = sim.player
	if p.light_on:
		p.light_on = false
		return
	var fl: Dictionary = Inv.find(p.inv, "flashlight")
	if not fl.is_empty() and int(fl.get("u", 0)) <= 0:
		var bat: Dictionary = Inv.find(p.inv, "battery")
		if not bat.is_empty():
			Inv.split(p.inv, bat, 1)
			fl["u"] = 100
			sim.say("You swap in a fresh battery", Color(0.9, 0.9, 0.7))
	if (not fl.is_empty() and int(fl.get("u", 0)) > 0) or not Inv.find(p.inv, "candle").is_empty():
		p.light_on = true
	else:
		sim.say("Your light is dead. You need a battery.", Color(0.9, 0.8, 0.6))

func _key(ev: InputEventKey) -> void:
	var p: Player = sim.player
	if ev.pressed:
		if p.sleeping:
			sim.wake("You get up.")
			return
		match ev.keycode:
			KEY_SPACE: _key_attack = true
			KEY_E: _key_interact_t = 0.0
			KEY_Q: Actions.interact(sim, true)
			KEY_C:
				p.sneaking = not p.sneaking
				if p.sneaking: run_on = false
			KEY_R: p.reload()
			KEY_F: toggle_light()
			KEY_V: p.try_shove()
			KEY_G: p.call_out(not p.sneaking)
			KEY_T: cycle_speed()
			KEY_1, KEY_2, KEY_3, KEY_4:
				var ki: int = ev.keycode - KEY_1
				if ki < _hot.size(): p.equip(_hot[ki])
			KEY_I, KEY_TAB: main.open_panel("inv")
			KEY_H: main.open_panel("char")
			KEY_B: main.open_panel("craft")
			KEY_M: main.open_panel("map")
			KEY_ESCAPE:
				if not placing.is_empty(): placing = {}
				else: main.open_panel("pause")
			KEY_EQUAL, KEY_KP_ADD: view.zoom = clampf(view.zoom * 1.2, 0.8, 3.0)
			KEY_MINUS, KEY_KP_SUBTRACT: view.zoom = clampf(view.zoom / 1.2, 0.8, 3.0)
			KEY_ENTER:
				if not placing.is_empty():
					if Actions.craft(sim, placing): placing = {}
			KEY_F3: debug = not debug
	else:
		match ev.keycode:
			KEY_SPACE: _key_attack = false
			KEY_E:
				if _key_interact_t >= 0.0 and _key_interact_t < 0.45:
					Actions.interact(sim, false)
				_key_interact_t = -1.0

## called by Main every frame while playing. returns [move vector, run flag]
func poll(dt: float) -> void:
	var p: Player = sim.player
	var kv := Vector2.ZERO
	if Input.is_key_pressed(KEY_A) or Input.is_key_pressed(KEY_LEFT): kv.x -= 1.0
	if Input.is_key_pressed(KEY_D) or Input.is_key_pressed(KEY_RIGHT): kv.x += 1.0
	if Input.is_key_pressed(KEY_W) or Input.is_key_pressed(KEY_UP): kv.y -= 1.0
	if Input.is_key_pressed(KEY_S) or Input.is_key_pressed(KEY_DOWN): kv.y += 1.0
	if _stick_touch >= 0:
		move = _stick_vec if _stick_vec.length() > Opts.dead else Vector2.ZERO
	else:
		move = kv.normalized()
	sim.brake = sim.vehicle != null and (_attack_touch >= 0 or _key_attack)
	if sim.vehicle == null and (_attack_touch >= 0 or _key_attack):
		p.try_attack()
	if _interact_touch >= 0 and not _interact_fired:
		_interact_t += dt
		if _interact_t >= 0.45:
			_interact_fired = true
			Actions.interact(sim, true)
	if _key_interact_t >= 0.0:
		_key_interact_t += dt
		if _key_interact_t >= 0.45:
			_key_interact_t = -1.0
			Actions.interact(sim, true)
	# what would INTERACT do right now? (label + highlight), refreshed a few times a second
	_target_t -= dt
	if _target_t <= 0.0:
		_target_t = 0.2
		_target = ""
		if p.alive and not p.busy():
			var ts: Array = Actions.targets(sim)
			if sim.vehicle != null:
				_target = "Get out"
			elif not p.carrying.is_empty():
				_target = "Set down the %s" % String(Defs.obj(int(p.carrying["o"]))["n"]).to_lower()
			elif ts.size() > 0:
				var opts: Array = Actions.options(sim, ts[0])
				if opts.size() > 0:
					_target = String(opts[0]["label"]) if (opts.size() == 1 or opts[0].get("quick", false)) else Actions.target_name(sim, ts[0])
	# build placement preview
	var fxv: FxView = view.fx
	if not placing.is_empty():
		var bt: Dictionary = Actions.build_target(sim, placing)
		fxv.hl_on = bt.has("x")
		if fxv.hl_on:
			fxv.hl_tile = Vector2i(int(bt["x"]), int(bt["y"]))
			fxv.hl_edge = int(bt.get("side", -1))
			fxv.hl_ok = bt["ok"]
	elif not p.carrying.is_empty():
		var ct: Dictionary = Actions.build_target(sim, Actions.carry_recipe(p))
		fxv.hl_on = ct.has("x")
		if fxv.hl_on:
			fxv.hl_tile = Vector2i(int(ct["x"]), int(ct["y"]))
			fxv.hl_edge = -1
			fxv.hl_ok = ct["ok"]
	else:
		fxv.hl_on = false
	# flashlight battery
	if p.light_on:
		var fl: Dictionary = Inv.find(p.inv, "flashlight")
		if not fl.is_empty() and int(fl.get("u", 0)) > 0:
			if randf() < dt * 0.12:
				fl["u"] = int(fl["u"]) - 1
		elif Inv.find(p.inv, "candle").is_empty():
			p.light_on = false
	_fps_t += dt
	queue_redraw()

func want_run() -> bool:
	return run_on or Input.is_key_pressed(KEY_SHIFT)

# ------------------------------------------------------------------ drawing
func _txt(text: String, pos: Vector2, size: int = 18, col: Color = UiKit.TEXT, align: int = HORIZONTAL_ALIGNMENT_LEFT, width: float = -1) -> void:
	var font: Font = ThemeDB.fallback_font
	size = int(round(size * Opts.text))
	draw_string_outline(font, pos, text, align, width, size, 4, Color(0, 0, 0, 0.75 * col.a))
	draw_string(font, pos, text, align, width, size, col)

func _round_btn(id: String, label: String, col: Color, on: bool = false, size: int = 16) -> void:
	if not _btn.has(id):
		return
	var c: Vector2 = _btn[id][0]
	var r: float = _btn[id][1]
	draw_circle(c, r, Color(0.05, 0.07, 0.07, 0.55))
	draw_circle(c, r - 3.0, Color(col.r, col.g, col.b, 0.5 if not on else 0.92))
	draw_arc(c, r, 0, TAU, 40, Color(0.9, 0.88, 0.78, 0.75 if on else 0.4), 2.0, true)
	var font: Font = ThemeDB.fallback_font
	draw_string(font, c + Vector2(-r, size * 0.36), label, HORIZONTAL_ALIGNMENT_CENTER, r * 2.0, size, Color(0.96, 0.94, 0.86))

func _bar(pos: Vector2, w: float, h: float, v: float, col: Color) -> void:
	draw_rect(Rect2(pos, Vector2(w, h)), Color(0, 0, 0, 0.55))
	draw_rect(Rect2(pos + Vector2(1, 1), Vector2((w - 2) * clampf(v, 0.0, 1.0), h - 2)), col)

func _draw() -> void:
	if sim == null or main.state != "play":
		return
	_layout()
	var p: Player = sim.player
	var size: Vector2 = get_viewport_rect().size
	var portrait: bool = size.y > size.x
	var x0: float = safe.position.x + 12
	var y0: float = safe.position.y + 10
	# low health vignette
	if p.hp < 40.0 and p.alive:
		var a: float = (40.0 - p.hp) / 40.0 * 0.35
		draw_rect(Rect2(0, 0, size.x, 26), Color(0.6, 0.0, 0.0, a))
		draw_rect(Rect2(0, size.y - 26, size.x, 26), Color(0.6, 0.0, 0.0, a))
		draw_rect(Rect2(0, 0, 18, size.y), Color(0.6, 0.0, 0.0, a))
		draw_rect(Rect2(size.x - 18, 0, 18, size.y), Color(0.6, 0.0, 0.0, a))
	# status block
	_txt(sim.clock_text(), Vector2(x0, y0 + 20), 20, UiKit.ACCENT)
	var wtxt: String = "%d°C" % int(round(float(sim.weather["temp"])))
	if float(sim.weather["rain"]) > 0.1: wtxt += "  rain"
	elif float(sim.weather["fog"]) > 0.2: wtxt += "  fog"
	_txt(wtxt, Vector2(x0 + 172, y0 + 20), 15, UiKit.DIM)
	_bar(Vector2(x0, y0 + 30), 210, 14, p.hp / 100.0, Color(0.74, 0.22, 0.2) if p.hp < 50.0 else Color(0.62, 0.7, 0.36))
	_bar(Vector2(x0, y0 + 48), 210, 7, p.endurance / 100.0, Color(0.82, 0.76, 0.45))
	var wd: Dictionary = p.weapon_def()
	var wname: String = "Bare hands"
	if not wd.is_empty():
		wname = wd["n"]
		if wd.has("gun"):
			wname += "  %d/%d (+%d)" % [int(p.weapon.get("u", 0)), int(wd["gun"]["mag"]), Inv.count(p.inv, wd["gun"]["ammo"])]
		elif p.weapon.has("c"):
			wname += "  %d%%" % int(float(p.weapon["c"]) * 100.0)
	_txt(wname, Vector2(x0, y0 + 76), 15, UiKit.TEXT)
	# how far the survivor can currently be heard: quiet / walking / loud
	var nx: float = x0 + 226.0
	var loud: float = clampf(p.noise_r / 9.0, 0.0, 1.0)
	for k in range(3):
		var on: bool = loud > [0.05, 0.4, 0.8][k]
		draw_arc(Vector2(nx, y0 + 44), 6.0 + k * 5.0, -0.9, 0.9, 10, Color(0.95, 0.8, 0.4, 0.95) if on else Color(1, 1, 1, 0.16), 2.0)
	draw_circle(Vector2(nx, y0 + 44), 2.5, Color(0.95, 0.8, 0.4, 0.9) if p.sneaking else Color(1, 1, 1, 0.5))
	# moodles
	var my: float = y0 + 92
	var tex: Texture2D = Art.icons.texture
	for m in p.moodles():
		var lvl: int = clampi(int(m[1]), 1, 4)
		var col: Color = MOODLE_COLORS[lvl - 1]
		draw_rect(Rect2(x0, my, 42, 42), Color(0.05, 0.06, 0.06, 0.7))
		draw_rect(Rect2(x0 + 2, my + 2, 38, 38), Color(col.r, col.g, col.b, 0.85))
		var h: int = Art.misc.get("m_" + String(m[0]), -1)
		if h >= 0:
			draw_texture_rect_region(tex, Rect2(x0 + 5, my + 5, 32, 32), Art.icons.rects[h], Color(0.1, 0.08, 0.07))
		my += 46
	# top buttons
	_round_btn("inv", "BAG", Color(0.3, 0.36, 0.3), false, 14)
	_round_btn("char", "BODY", Color(0.42, 0.26, 0.24), false, 13)
	_round_btn("craft", "MAKE", Color(0.36, 0.32, 0.22), false, 13)
	_round_btn("map", "MAP", Color(0.24, 0.32, 0.38), false, 14)
	_round_btn("menu", "II", Color(0.25, 0.25, 0.25), false, 16)
	_round_btn("zoom_in", "+", Color(0.2, 0.22, 0.22), false, 20)
	_round_btn("zoom_out", "–", Color(0.2, 0.22, 0.22), false, 20)
	_round_btn("speed", "%dx" % sim.speed, Color(0.3, 0.3, 0.2), sim.speed > 1, 15)
	for hi in range(_hot.size()):
		var hid: String = "hot%d" % hi
		var hit: Dictionary = _hot[hi]
		_round_btn(hid, "", Color(0.22, 0.24, 0.24), is_same(p.weapon, hit), 12)
		var hh: int = Art.item_icon.get(hit["id"], -1)
		if hh >= 0:
			var hc: Vector2 = _btn[hid][0]
			draw_texture_rect_region(tex, Rect2(hc - Vector2(18, 18), Vector2(36, 36)), Art.icons.rects[hh])
	# action buttons
	var atk: String = "ATTACK"
	if wd.has("gun"): atk = "FIRE"
	elif wd.is_empty(): atk = "SHOVE"
	var veh: Vehicle = sim.vehicle
	if veh != null:
		_round_btn("attack", "BRAKE", Color(0.62, 0.26, 0.22), _attack_touch >= 0, 17)
		_round_btn("interact", "EXIT", Color(0.7, 0.6, 0.36), _interact_touch >= 0, 17)
		var vx: float = size.x * 0.5 - 130.0
		var vy: float = safe.end.y - (300.0 if portrait else 70.0)
		draw_rect(Rect2(vx - 10, vy - 26, 280, 62), Color(0.04, 0.05, 0.05, 0.6))
		_txt("%d km/h%s" % [int(absf(veh.speed) * 9.0), "  R" if veh.speed < -0.1 else ""], Vector2(vx, vy), 20, UiKit.ACCENT)
		_txt("engine %d%%" % int(float(veh.ent.get("eng", 0.0)) * 100.0), Vector2(vx + 140, vy), 15, UiKit.DIM)
		_txt("fuel", Vector2(vx, vy + 24), 14, UiKit.DIM)
		var fu: float = float(veh.ent.get("fuel", 0.0)) / Vehicle.TANK
		_bar(Vector2(vx + 40, vy + 12), 210, 12, fu, Color(0.8, 0.3, 0.25) if fu < 0.15 else Color(0.82, 0.76, 0.45))
	else:
		_round_btn("attack", atk, Color(0.62, 0.26, 0.22), _attack_touch >= 0, 17)
		_round_btn("interact", "USE", Color(0.7, 0.6, 0.36), _interact_touch >= 0, 17)
	_round_btn("turn", "TURN", Color(0.4, 0.4, 0.3), false, 12)
	_round_btn("horn", "HORN", Color(0.36, 0.34, 0.44), false, 12)
	_round_btn("shove", "SHOVE", Color(0.5, 0.36, 0.26), false, 11)
	_round_btn("call", "CALL", Color(0.36, 0.34, 0.44), false, 11)
	_round_btn("run", "RUN", Color(0.3, 0.42, 0.5), run_on, 14)
	_round_btn("sneak", "SNEAK", Color(0.32, 0.4, 0.3), p.sneaking, 12)
	_round_btn("light", "LIGHT", Color(0.7, 0.66, 0.36), p.light_on, 11)
	_round_btn("reload", "LOAD", Color(0.4, 0.4, 0.42), false, 11)
	if _target != "" and _btn.has("interact"):
		var ic: Vector2 = _btn["interact"][0]
		_txt(_target, Vector2(ic.x - 150, ic.y - 62), 15, UiKit.ACCENT, HORIZONTAL_ALIGNMENT_CENTER, 300)
	# joystick
	if _stick_touch >= 0:
		draw_circle(_stick_origin, STICK_R, Color(0.1, 0.16, 0.15, 0.4))
		draw_arc(_stick_origin, STICK_R, 0, TAU, 48, Color(0.85, 0.85, 0.75, 0.5), 2.0, true)
		draw_circle(_stick_origin + _stick_vec * STICK_R, 30, Color(0.82, 0.74, 0.52, 0.8))
	else:
		var hint := Vector2(safe.position.x + 120, safe.end.y - 130)
		draw_arc(hint, STICK_R, 0, TAU, 48, Color(0.85, 0.85, 0.75, 0.16), 2.0, true)
		draw_circle(hint, 26, Color(0.82, 0.74, 0.52, 0.14))
	# timed action
	if not p.action.is_empty():
		var w: float = 300.0
		var bx: float = size.x * 0.5 - w * 0.5
		var by: float = safe.end.y - (330.0 if portrait else 40.0)
		_bar(Vector2(bx, by), w, 18, float(p.action["t"]) / float(p.action["dur"]), UiKit.ACCENT)
		_txt(String(p.action["label"]), Vector2(bx, by - 8), 16, UiKit.TEXT, HORIZONTAL_ALIGNMENT_CENTER, w)
	if not placing.is_empty():
		_round_btn("place_ok", "BUILD", Color(0.3, 0.5, 0.3), false, 15)
		_round_btn("place_no", "CANCEL", Color(0.5, 0.3, 0.28), false, 13)
		_txt("Placing: %s — face the spot, then BUILD" % placing["n"], Vector2(0, safe.end.y - (318.0 if portrait else 164.0)), 16, UiKit.ACCENT, HORIZONTAL_ALIGNMENT_CENTER, size.x)
	var gt: String = sim.guide_text()
	if gt != "" and not p.sleeping:
		_txt(gt, Vector2(20, safe.position.y + (118.0 if not portrait else 178.0)), 16, Color(0.7, 0.9, 1.0), HORIZONTAL_ALIGNMENT_CENTER, size.x - 40)
	if sim.fly_active and not sim.underground():
		_txt("AIRCRAFT OVERHEAD — get indoors and stay quiet", Vector2(20, safe.position.y + (96.0 if not portrait else 200.0)), 15, Color(1.0, 0.7, 0.45), HORIZONTAL_ALIGNMENT_CENTER, size.x - 40)
	# message log (above the controls in portrait, under the top bar in landscape)
	var ly: float = safe.end.y - 360.0 if portrait else safe.position.y + 146.0
	var shown := 0
	for i in range(sim.log.size() - 1, -1, -1):
		var l: Array = sim.log[i]
		var age: float = l[2]
		if age > 7.0 or shown >= 4:
			break
		var c: Color = l[1]
		c.a = clampf((7.0 - age) / 1.5, 0.0, 1.0)
		_txt(String(l[0]), Vector2(20, ly), 16, c, HORIZONTAL_ALIGNMENT_CENTER, size.x - 40)
		ly += -24.0 if portrait else 22.0
		shown += 1
	# sleeping
	if p.sleeping:
		draw_rect(Rect2(Vector2.ZERO, size), Color(0, 0, 0, 0.72))
		_txt("Sleeping…  %s" % sim.clock_text(), Vector2(0, size.y * 0.45), 26, UiKit.ACCENT, HORIZONTAL_ALIGNMENT_CENTER, size.x)
		_txt("Fatigue %d%%   —   tap to wake" % int(p.fatigue), Vector2(0, size.y * 0.45 + 36), 18, UiKit.DIM, HORIZONTAL_ALIGNMENT_CENTER, size.x)
	if debug:
		var st: Dictionary = {}
		for z in sim.zombies.list:
			var n: String = Zombie.STATE_NAMES[z.state]
			st[n] = st.get(n, 0) + 1
		var lines: Array = [
			"FPS %d   frame %.1f ms   sim %.2f ms" % [Engine.get_frames_per_second(), main.frame_ms, main.sim_ms],
			"zombies %d  %s" % [sim.zombies.list.size(), str(st)],
			"chunks %d  stored %d  path iters %d" % [sim.world.chunks.size(), sim.world.store.size(), Pathfinder.iterations],
			"pos %.1f, %.1f  bld %d  noise %.0f  zone %d" % [p.pos.x, p.pos.y, p.bld, p.noise_r, sim.world.chunk_at(floori(p.pos.x), floori(p.pos.y)).zone if sim.world.chunk_at(floori(p.pos.x), floori(p.pos.y)) != null else -1],
			"power off day %d   water off day %d" % [int(sim.power_off_h / 24.0) + 1, int(sim.water_off_h / 24.0) + 1],
		]
		var dy: float = size.y * 0.34
		for ln in lines:
			_txt(ln, Vector2(x0 + 60, dy), 13, Color(0.7, 1.0, 0.7))
			dy += 18.0
