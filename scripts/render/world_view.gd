class_name WorldView
extends Node2D
## Renders the simulation. Static world geometry is cached per chunk in "strips"
## (one per tile diagonal) so depth sorting against moving characters is a plain z-index.
##   z = (diagonal - anchor) * 3 + layer      layer 0 walls/objects, 1 characters, 2 roofs

const CAR_COLORS := [Color("9a3a32"), Color("3a5a86"), Color("d8d8d2"), Color("3a3d40"), Color("6a7a5a"), Color("c2a85a"), Color("7a8a94"), Color("5a3a4a")]
const ROOF_COLORS := [Color("5a5552"), Color("6a4a3c"), Color("4a5560"), Color("7a4038"), Color("4c5a48"), Color("6a6460")]
const VIEW_RADIUS := 24.0

var sim: Sim
var cam: Camera2D
var fx: FxView
var zoom := 1.5
var cut_bld := 0
var cut_tile := Vector2i.ZERO
var d0 := 0
var shake := 0.0
var _chunks: Dictionary = {}      # Vector2i -> {"base", "nat", "rows": Array, "roofs": Array, "c": Chunk}
var _ents: Node2D
var _zviews: Dictionary = {}
var _pool: Array = []
var _pview: EntityView
var _ghost: EntityView
var _stamp := 0
var _wall_tints: Array = []
var _cam_pos := Vector2.ZERO
var _roof_uv := PackedVector2Array()
var _nviews: Dictionary = {}      # npc id -> EntityView
var _aviews: Dictionary = {}      # animal id -> AnimalView
var _vparts: Array = []           # CarPart nodes for the driven car

class AnimalView extends Node2D:
	var a: AnimalSim.Animal
	var stamp := 0
	func _process(_dt: float) -> void:
		if visible: queue_redraw()
	func _draw() -> void:
		if a == null: return
		var sp: Dictionary = AnimalSim.SPECIES[a.kind]
		var col := Color(String(sp["col"]))
		if a.flash > 0.0: col = col.lerp(Color(1.5, 1.2, 1.1), 0.6)
		var L: float = sp["len"]
		var sd: Vector2 = Iso.to_screen(a.dir.x, a.dir.y).normalized()
		var fx: float = 1.0 if sd.x >= 0.0 else -1.0
		var hop: float = absf(sin(a.anim_t * (14.0 if a.state != 0 else 7.0))) * (3.0 if a.moving else 0.0) * (L / 14.0)
		var up: float = L * 0.55 + hop
		draw_set_transform(Vector2.ZERO, 0.0, Vector2(1.0, 0.45))
		draw_circle(Vector2(0, 2), L * 0.5, Color(0, 0, 0, 0.28))
		draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)
		var dark := col.darkened(0.35)
		if a.kind == "pheasant":
			draw_colored_polygon(PackedVector2Array([Vector2(-L * 0.9 * fx, -up * 0.5), Vector2(-L * 0.2 * fx, -up * 0.9), Vector2(-L * 0.2 * fx, -up * 0.4)]), dark)
			draw_circle(Vector2(0, -up * 0.6), L * 0.34, col)
			draw_circle(Vector2(L * 0.38 * fx, -up * 1.05), L * 0.17, Color(0.2, 0.4, 0.3))
			return
		# legs
		for lx in [-0.3, 0.3]:
			var sw: float = sin(a.anim_t * 14.0 + lx * 9.0) * (2.0 if a.moving else 0.0)
			draw_line(Vector2(lx * L * fx, -up * 0.5), Vector2(lx * L * fx + sw, 0), dark, maxf(1.5, L * 0.1))
		# body, head
		var body := PackedVector2Array([Vector2(-L * 0.5 * fx, -up * 0.5), Vector2(-L * 0.42 * fx, -up), Vector2(L * 0.4 * fx, -up * 1.02), Vector2(L * 0.5 * fx, -up * 0.55), Vector2(L * 0.3 * fx, -up * 0.42), Vector2(-L * 0.3 * fx, -up * 0.4)])
		draw_colored_polygon(body, col)
		var hx: float = L * 0.62 * fx
		var hy: float = -up * (1.25 if a.kind == "deer" else (1.05 if a.kind != "boar" else 0.85))
		draw_circle(Vector2(hx, hy), L * (0.2 if a.kind != "boar" else 0.26), col.lightened(0.08))
		match a.kind:
			"rabbit":
				draw_line(Vector2(hx, hy), Vector2(hx - 1.0 * fx, hy - L * 0.5), col, 2.0)
				draw_circle(Vector2(-L * 0.5 * fx, -up * 0.8), 1.8, Color(0.95, 0.95, 0.9))
			"deer":
				draw_line(Vector2(hx, hy), Vector2(L * 0.42 * fx, -up), col, L * 0.16)
				draw_line(Vector2(hx, hy - 2), Vector2(hx + 3 * fx, hy - 8), dark, 1.5)
				draw_line(Vector2(hx, hy - 2), Vector2(hx - 2 * fx, hy - 8), dark, 1.5)
			"boar":
				draw_line(Vector2(hx + 3 * fx, hy + 2), Vector2(hx + 6 * fx, hy), Color(0.9, 0.9, 0.82), 1.5)
			"fox":
				draw_colored_polygon(PackedVector2Array([Vector2(-L * 0.5 * fx, -up * 0.8), Vector2(-L * 1.05 * fx, -up * 0.95), Vector2(-L * 0.55 * fx, -up * 0.5)]), col)
				draw_circle(Vector2(-L * 1.0 * fx, -up * 0.92), 1.8, Color(0.95, 0.95, 0.9))

class CarPart extends Node2D:
	var h := -1
	var tint := Color.WHITE
	func _draw() -> void:
		if h >= 0:
			Art.world.draw(self, h, Vector2.ZERO, tint)

func _ready() -> void:
	for m in Defs.WALL_MATS:
		_wall_tints.append(Color(String(m[1])))
	cam = Camera2D.new()
	add_child(cam)
	cam.make_current()
	_ents = Node2D.new()
	add_child(_ents)
	fx = FxView.new()
	fx.z_index = 4000
	fx.z_as_relative = false
	add_child(fx)
	_pview = EntityView.new()
	_pview.is_player = true
	_pview.z_as_relative = false
	_ents.add_child(_pview)
	_ghost = EntityView.new()
	_ghost.is_player = true
	_ghost.ghost = true
	_ghost.z_as_relative = false
	_ghost.z_index = 3990
	_ghost.modulate = Color(1, 1, 1, 0.3)
	_ents.add_child(_ghost)
	var r: Rect2 = Art.world.rects[Art.misc["roof"]]
	var ts: Vector2 = Vector2(Art.world.width, Art.world.height)
	for p in [Vector2(32, 0.5), Vector2(63.5, 16), Vector2(32, 31.5), Vector2(0.5, 16)]:
		_roof_uv.append((r.position + p) / ts)

func attach(s: Sim) -> void:
	clear()
	sim = s
	var p: Vector2 = sim.player.pos
	d0 = floori(p.x) + floori(p.y)
	_cam_pos = Iso.to_screen(p.x, p.y)
	for c in sim.world.chunks.values():
		_add_chunk(c)
	sim.view_loaded.clear()
	sim.world.ev_unloaded.clear()
	sim.world.ev_tiles.clear()
	sim.world.ev_ground.clear()

func clear() -> void:
	for k in _chunks.keys():
		_free_chunk(k)
	_chunks.clear()
	for id in _zviews.keys():
		(_zviews[id] as Node).queue_free()
	_zviews.clear()
	for id in _nviews.keys():
		(_nviews[id] as Node).queue_free()
	_nviews.clear()
	for id in _aviews.keys():
		(_aviews[id] as Node).queue_free()
	_aviews.clear()
	for cp in _vparts:
		(cp as Node).queue_free()
	_vparts.clear()
	if fx != null:
		fx.flames = []
	cut_bld = 0

# ------------------------------------------------------------------ chunk nodes
func _z(d: int, layer: int) -> int:
	return clampi((d - d0) * 3 + layer, -3900, 3900)

func _make_strip(c: Chunk, kind: int, dl: int) -> Strip:
	var s := Strip.new()
	s.view = self
	s.c = c
	s.kind = kind
	s.dl = dl
	s.z_as_relative = false
	s.position = Iso.to_screen(c.cx * 16, c.cy * 16)
	var d: int = c.cx * 16 + c.cy * 16 + dl
	match kind:
		Strip.K_GROUND: s.z_index = -4096
		Strip.K_NATURAL: s.z_index = -4095
		Strip.K_ROW: s.z_index = _z(d, 0)
		Strip.K_ROOF: s.z_index = _z(d, 2)
	add_child(s)
	return s

func _add_chunk(c: Chunk) -> void:
	var k := Vector2i(c.cx, c.cy)
	if _chunks.has(k):
		_free_chunk(k)
	var rows: Array = []
	var roofs: Array = []
	rows.resize(31)
	roofs.resize(31)
	var has_row := PackedByteArray()
	var has_roof := PackedByteArray()
	has_row.resize(31)
	has_roof.resize(31)
	for i in range(Iso.CS2):
		var dl: int = (i & 15) + (i >> 4)
		if c.obj[i] != 0 or c.wall_n[i] != 0 or c.wall_w[i] != 0:
			has_row[dl] = 1
		if c.bld[i] != 0:
			has_roof[dl] = 1
			# corner posts live on the tile diagonally in front of a building corner
			has_row[dl] = 1
			if dl + 1 < 31: has_row[dl + 1] = 1
			if dl + 2 < 31: has_row[dl + 2] = 1
	for i in c.items.keys():
		has_row[(int(i) & 15) + (int(i) >> 4)] = 1
	for cp in c.corpses:
		has_row[clampi((floori(cp["x"]) & 15) + (floori(cp["y"]) & 15), 0, 30)] = 1
	for dl in range(31):
		if has_row[dl] == 1:
			rows[dl] = _make_strip(c, Strip.K_ROW, dl)
		if has_roof[dl] == 1:
			roofs[dl] = _make_strip(c, Strip.K_ROOF, dl)
	_chunks[k] = {"c": c, "base": _make_strip(c, Strip.K_GROUND, 0), "nat": _make_strip(c, Strip.K_NATURAL, 0), "rows": rows, "roofs": roofs}

func _free_chunk(k: Vector2i) -> void:
	var cv: Dictionary = _chunks.get(k, {})
	if cv.is_empty():
		return
	(cv["base"] as Node).queue_free()
	(cv["nat"] as Node).queue_free()
	for s in cv["rows"]:
		if s != null: (s as Node).queue_free()
	for s in cv["roofs"]:
		if s != null: (s as Node).queue_free()
	_chunks.erase(k)

func _dirty_tile(x: int, y: int) -> void:
	var k := Vector2i(x >> 4, y >> 4)
	var cv: Dictionary = _chunks.get(k, {})
	if cv.is_empty():
		return
	var dl: int = (x & 15) + (y & 15)
	var rows: Array = cv["rows"]
	if rows[dl] == null:
		rows[dl] = _make_strip(cv["c"], Strip.K_ROW, dl)
	else:
		(rows[dl] as Strip).queue_redraw()
	var roofs: Array = cv["roofs"]
	if roofs[dl] == null and (cv["c"] as Chunk).bld[((y & 15) << 4) | (x & 15)] != 0:
		roofs[dl] = _make_strip(cv["c"], Strip.K_ROOF, dl)       # a roof was built where there was none
	if roofs[dl] != null:
		(roofs[dl] as Strip).queue_redraw()

func _redraw_building(b: int) -> void:
	if b == 0:
		return
	for cv in _chunks.values():
		var c: Chunk = cv["c"]
		if not c.btype.has(b):
			continue
		for s in cv["rows"]:
			if s != null and (s as Strip).blds.has(b):
				(s as Strip).queue_redraw()
		for s in cv["roofs"]:
			if s != null:
				(s as Strip).queue_redraw()

# ------------------------------------------------------------------ per-frame sync
func sync(dt: float) -> void:
	if sim == null:
		return
	var w: World = sim.world
	var p: Player = sim.player
	_stamp += 1
	for c in sim.view_loaded:
		_add_chunk(c)
	sim.view_loaded.clear()
	for k in w.ev_unloaded:
		_free_chunk(k)
	w.ev_unloaded.clear()
	if w.ev_tiles.size() > 0:
		for t in w.ev_tiles:
			_dirty_tile(t.x, t.y)
			_dirty_tile(t.x + 1, t.y)
			_dirty_tile(t.x, t.y + 1)
		w.ev_tiles.clear()
	if w.ev_ground.size() > 0:
		for k in w.ev_ground:
			var cv: Dictionary = _chunks.get(k, {})
			if not cv.is_empty():
				(cv["base"] as Strip).queue_redraw()
				(cv["nat"] as Strip).queue_redraw()
		w.ev_ground.clear()
	# z anchor
	var ptx: int = floori(p.pos.x)
	var pty: int = floori(p.pos.y)
	if absi(ptx + pty - d0) > 900:
		d0 = ptx + pty
		for cv in _chunks.values():
			var c: Chunk = cv["c"]
			for dl in range(31):
				var d: int = c.cx * 16 + c.cy * 16 + dl
				if cv["rows"][dl] != null: (cv["rows"][dl] as Strip).z_index = _z(d, 0)
				if cv["roofs"][dl] != null: (cv["roofs"][dl] as Strip).z_index = _z(d, 2)
	# cutaway
	var nb: int = w.bld(ptx, pty)
	var nt := Vector2i(ptx, pty)
	if nb != cut_bld or (nb != 0 and nt != cut_tile):
		var old: int = cut_bld
		cut_bld = nb
		cut_tile = nt
		_redraw_building(old)
		if nb != old or nb != 0:
			_redraw_building(nb)
	# player
	var ps: Vector2 = Iso.to_screen(p.pos.x, p.pos.y)
	_pview.position = ps
	_pview.z_index = _z(ptx + pty, 1)
	_pview.look = p.look
	var wl := 0
	var wd: Dictionary = p.weapon_def()
	if wd.has("wpn"): wl = int(wd["wpn"].get("spr", 1))
	elif wd.has("gun"): wl = int(wd["gun"].get("spr", 4))
	var prog := -1.0
	if p.swing_t > 0.0 and p.swing_dur > 0.0:
		prog = 1.0 - p.swing_t / p.swing_dur
	var sy: float = 0.86 if (p.sneaking and p.alive and not p.sleeping) else 1.0
	_pview.scale = Vector2(1.0, sy)
	_pview.set_frame(p.anim, p.anim_t, p.dir8, prog, wl, p.hit_flash)
	_ghost.position = ps
	_ghost.scale = _pview.scale
	_ghost.look = p.look
	_ghost.set_frame(p.anim, p.anim_t, p.dir8, prog, wl, 0.0)
	_pview.visible = sim.vehicle == null and not p.hidden
	_ghost.visible = sim.vehicle == null and not p.hidden
	_sync_vehicle()
	_sync_npcs()
	_sync_animals()
	fx.flames = sim.burning.keys()
	# zombies
	var vr2: float = VIEW_RADIUS * VIEW_RADIUS
	for z in sim.zombies.list:
		if z.pos.distance_squared_to(p.pos) > vr2:
			continue
		var target: float = 1.0 if z.seen else 0.0
		z.alpha = move_toward(z.alpha, target, dt * 5.0)
		if z.alpha <= 0.01:
			continue
		var v: EntityView = _zviews.get(z.id)
		if v == null:
			v = _pool.pop_back() if _pool.size() > 0 else null
			if v == null:
				v = EntityView.new()
				v.z_as_relative = false
				_ents.add_child(v)
			v.zombie = z
			v.look = z.look
			v._key = -1
			v.visible = true
			_zviews[z.id] = v
		v.stamp = _stamp
		v.position = Iso.to_screen(z.pos.x, z.pos.y)
		v.z_index = _z(floori(z.pos.x) + floori(z.pos.y), 1)
		v.modulate.a = z.alpha
		var anim: String = z.anim
		var zp := -1.0
		if z.state == Zombie.DOWN:
			if z.anim_t > 0.35:
				anim = "z_lie"
		elif z.state == Zombie.STAGGER and z.anim == "z_fall":
			zp = clampf(1.0 - z.anim_t / 0.7, 0.0, 0.99)
		elif z.state == Zombie.ATTACK or (z.state == Zombie.THUMP and z.anim == "z_attack"):
			zp = clampf(z.anim_t / 0.45, 0.0, 0.99)
		var sc: float = 1.12 if z.kind == 3 else 1.0
		v.scale = Vector2(sc, sc * (0.78 if z.feeding else 1.0))
		v.set_frame(anim, z.anim_t + z.id * 0.37, z.d8, zp, 0, z.flash)
	for id in _zviews.keys():
		var v2: EntityView = _zviews[id]
		if v2.stamp != _stamp:
			v2.visible = false
			v2.zombie = null
			_pool.append(v2)
			_zviews.erase(id)
	# camera
	var want: Vector2 = ps + Vector2(0, -18)
	_cam_pos = _cam_pos.lerp(want, clampf(dt * 9.0, 0.0, 1.0))
	if _cam_pos.distance_to(want) > 600.0:
		_cam_pos = want
	shake = maxf(0.0, shake - dt * 3.0)
	var off := Vector2.ZERO
	if shake > 0.0:
		off = Vector2(randf_range(-1, 1), randf_range(-1, 1)) * shake * 5.0
	cam.position = (_cam_pos + off).round()
	cam.zoom = Vector2(zoom, zoom)
	_consume_fx()

func _sync_vehicle() -> void:
	var v: Vehicle = sim.vehicle
	for cp0 in _vparts:
		(cp0 as CarPart).visible = false
	if v == null:
		return
	while _vparts.size() < 16:
		var n := CarPart.new()
		n.z_as_relative = false
		_ents.add_child(n)
		_vparts.append(n)
	var k := 0
	k = _car_parts(v.oid, v.heading, v.anchor_f(), v.tint_key, k, 0)
	if not v.tow.is_empty():
		var ta: Vector2i = v.tow_anchor(0, 0)
		_car_parts(int(v.tow["o"]), v.heading, v.anchor_f() + Vector2(ta), v.tow.get("tk", Vector2i.ZERO), k, k)

func _car_parts(oid: int, heading: int, a: Vector2, tk: Vector2i, k: int, part0: int) -> int:
	var s: Vector2 = Vector2(Defs.obj_size(oid, heading))
	var tint: Color = CAR_COLORS[Rng.h2(tk.x, tk.y, 71) % CAR_COLORS.size()] if oid != Defs.O_CAR_WRECK else Color.WHITE
	for j in range(int(s.y)):
		for i in range(int(s.x)):
			var cp: CarPart = _vparts[k]
			var h: int = Art.obj_spr.get(Defs.ocell(oid, heading, k - part0), -1)
			if cp.h != h or cp.tint != tint:
				cp.h = h
				cp.tint = tint
				cp.queue_redraw()
			cp.visible = true
			cp.position = Iso.to_screen(a.x + i, a.y + j)
			cp.z_index = _z(floori(a.x + i + 0.5) + floori(a.y + j + 0.5), 1)
			k += 1
	return k

func _sync_animals() -> void:
	var p: Player = sim.player
	var vr2: float = VIEW_RADIUS * VIEW_RADIUS
	for a in sim.animals.list:
		if a.pos.distance_squared_to(p.pos) > vr2:
			continue
		var v: AnimalView = _aviews.get(a.id)
		if v == null:
			v = AnimalView.new()
			v.z_as_relative = false
			v.a = a
			_ents.add_child(v)
			_aviews[a.id] = v
		v.stamp = _stamp
		v.position = Iso.to_screen(a.pos.x, a.pos.y)
		v.z_index = _z(floori(a.pos.x) + floori(a.pos.y), 1)
	for id in _aviews.keys():
		var v2: AnimalView = _aviews[id]
		if v2.stamp != _stamp:
			v2.queue_free()
			_aviews.erase(id)

func _sync_npcs() -> void:
	var p: Player = sim.player
	var vr2: float = VIEW_RADIUS * VIEW_RADIUS
	for n in sim.npcs.list:
		if n.pos.distance_squared_to(p.pos) > vr2 or n.away_until > 0.0:
			continue
		var v: EntityView = _nviews.get(n.id)
		if v == null:
			v = EntityView.new()
			v.z_as_relative = false
			v.look = n.look
			_ents.add_child(v)
			_nviews[n.id] = v
		v.stamp = _stamp
		v.position = Iso.to_screen(n.pos.x, n.pos.y)
		v.z_index = _z(floori(n.pos.x) + floori(n.pos.y), 1)
		var np := -1.0
		if n.swing > 0.0:
			np = clampf(1.0 - n.swing / 0.4, 0.0, 0.99)
		v.modulate = Color(1.0, 0.8, 0.8) if n.state == NpcSim.HOSTILE else Color.WHITE
		v.set_frame(n.anim, n.anim_t + n.id * 0.41, n.d8, np, 2 if n.state == NpcSim.HOSTILE else 1, n.flash)
	for id in _nviews.keys():
		var v2: EntityView = _nviews[id]
		if v2.stamp != _stamp:
			v2.queue_free()
			_nviews.erase(id)

func _consume_fx() -> void:
	for e in sim.fx:
		var sp: Vector2 = Iso.to_screen((e["p"] as Vector2).x, (e["p"] as Vector2).y) + Vector2(0, -24)
		match e["k"]:
			"hit":
				fx.burst(sp, 10 if e.get("crit", false) else 5, Color(0.55, 0.08, 0.06), 70.0, 0.45, 2.0)
			"zdie":
				fx.burst(sp, 14, Color(0.5, 0.07, 0.05), 80.0, 0.6, 2.0)
			"hurt":
				fx.burst(sp, 8, Color(0.8, 0.1, 0.08), 70.0, 0.5, 2.0)
				shake = 1.0
			"glass":
				fx.burst(sp, 14, Color(0.75, 0.88, 0.95, 0.9), 90.0, 0.6, 1.5)
			"break":
				fx.burst(sp, 10, Color(0.55, 0.42, 0.28), 80.0, 0.6, 2.5)
			"thump":
				fx.burst(sp, 3, Color(0.6, 0.55, 0.45, 0.8), 40.0, 0.3, 1.5)
			"build":
				fx.burst(sp, 5, Color(0.7, 0.6, 0.4, 0.8), 40.0, 0.4, 1.5)
			"shot":
				var dir: Vector2 = e.get("dir", Vector2.RIGHT)
				var p2: Vector2 = (e["p"] as Vector2) + dir * 9.0
				fx.flash_line(sp + Vector2(0, -4), Iso.to_screen(p2.x, p2.y) + Vector2(0, -28))
				shake = maxf(shake, 0.4)
			"levelup":
				fx.note(sp + Vector2(0, -30), "SKILL UP", Color(0.6, 1.0, 0.6))
			"fire":
				fx.burst(sp + Vector2(0, 14), 3, Color(1.0, 0.62, 0.2, 0.9), 26.0, 0.7, 2.5, 70.0)
				fx.burst(sp, 2, Color(0.2, 0.2, 0.2, 0.55), 18.0, 1.2, 4.0, 110.0)
			"engine":
				fx.burst(sp + Vector2(0, 18), 2, Color(0.35, 0.35, 0.35, 0.5), 16.0, 0.6, 3.0, 30.0)
			"call":
				fx.note(sp + Vector2(0, -30), "!", Color(1.0, 0.9, 0.6))
	# note: sim.fx is cleared by Main after audio has also consumed it

func screen_to_world(screen_pos: Vector2) -> Vector2:
	var wp: Vector2 = get_canvas_transform().affine_inverse() * screen_pos
	return Iso.to_world(wp)

func world_to_screen(wx: float, wy: float, h: float = 0.0) -> Vector2:
	return get_canvas_transform() * (Iso.to_screen(wx, wy) + Vector2(0, -h))

# ------------------------------------------------------------------ strip drawing
func draw_strip(s: Strip) -> void:
	match s.kind:
		Strip.K_GROUND: _draw_ground(s, false)
		Strip.K_NATURAL: _draw_ground(s, true)
		Strip.K_ROW: _draw_row(s)
		Strip.K_ROOF: _draw_roof(s)

func _draw_ground(s: Strip, natural: bool) -> void:
	var c: Chunk = s.c
	var A: Atlas = Art.world
	var bx: int = c.cx * 16
	var by: int = c.cy * 16
	if not natural:
		for i in range(Iso.CS2):
			var g: int = c.ground[i]
			if g == 0 or Defs.GROUND_PRIORITY[g] > 0:
				continue
			var lx: int = i & 15
			var ly: int = i >> 4
			var vars: Array = Art.ground[g]
			A.draw(s, vars[Rng.h2(bx + lx, by + ly, 3) % vars.size()], Vector2((lx - ly) * 32.0, (lx + ly) * 16.0))
		return
	for pr in range(1, 7):
		for i in range(Iso.CS2):
			var g2: int = c.ground[i]
			if Defs.GROUND_PRIORITY[g2] != pr:
				continue
			var lx2: int = i & 15
			var ly2: int = i >> 4
			var vars2: Array = Art.ground[g2]
			A.draw(s, vars2[Rng.h2(bx + lx2, by + ly2, 3) % vars2.size()], Vector2((lx2 - ly2) * 32.0, (lx2 + ly2) * 16.0))
	var splats: Array = Art.misc["blood"]
	for b in c.blood:
		var rel: Vector2 = Iso.to_screen(float(b[0]) - bx, float(b[1]) - by)
		A.draw(s, splats[int(b[2]) % splats.size()], rel + Vector2(0, -16))

func _draw_row(s: Strip) -> void:
	var c: Chunk = s.c
	var w: World = sim.world
	var A: Atlas = Art.world
	s.blds.clear()
	var bx: int = c.cx * 16
	var by: int = c.cy * 16
	for lx in range(maxi(0, s.dl - 15), mini(15, s.dl) + 1):
		var ly: int = s.dl - lx
		var i: int = ly * 16 + lx
		var x: int = bx + lx
		var y: int = by + ly
		var pos := Vector2((lx - ly) * 32.0, (lx + ly) * 16.0)
		var wn: int = c.wall_n[i]
		var ww: int = c.wall_w[i]
		var b0: int = c.bld[i]
		if wn != 0:
			_draw_wall(s, pos, wn, c.st_n[i], 0, x, y, b0, c.bld[i - 16] if ly > 0 else w.bld(x, y - 1))
		if ww != 0:
			_draw_wall(s, pos, ww, c.st_w[i], 1, x, y, b0, c.bld[i - 1] if lx > 0 else w.bld(x - 1, y))
		if wn == 0 and ww == 0:
			# outer corner post where a wall ends north-west of this tile
			var an: int = c.wall_n[i - 1] if lx > 0 else w.wall(x - 1, y, 0)
			var aw: int = c.wall_w[i - 16] if ly > 0 else w.wall(x, y - 1, 1)
			if an != 0 and aw != 0 and Defs.WALL_MATS[an >> 2][0] <= Defs.WT_TILE and Defs.WALL_MATS[aw >> 2][0] <= Defs.WT_TILE:
				var bb: int = w.bld(x - 1, y - 1)
				var cutp: bool = cut_bld != 0 and bb == cut_bld and (y > cut_tile.y or x > cut_tile.x)
				if bb != 0 and not s.blds.has(bb): s.blds.append(bb)
				A.draw(s, Art.wall_spr[Defs.WALL_MATS[an >> 2][0]][0][Art.WV_CUT_POST if cutp else Art.WV_POST], pos, _wall_tints[an >> 2])
		if c.items.has(i):
			var arr: Array = c.items[i]
			var n: int = mini(arr.size(), 3)
			for k in range(n):
				var ih: int = Art.item_icon.get(arr[k]["id"], -1)
				if ih >= 0:
					var r: Rect2 = Art.icons.rects[ih]
					var ip: Vector2 = pos + Vector2(-8 + k * 7 - (n - 1) * 3.5, 9 + (k % 2) * 4)
					s.draw_texture_rect_region(Art.icons.texture, Rect2(ip, Vector2(16, 16)), r)
		var o: int = c.obj[i]
		if o != 0:
			var h: int = Art.obj_spr.get(o, -1)
			if h >= 0:
				var od: Dictionary = Defs.OBJ[o & 1023]
				var tint := Color.WHITE
				if od.has("tint"):
					if Vehicle.is_vehicle(o & 1023):
						var a: Vector2i = Vector2i(x, y) - Defs.part_offset(o & 1023, (o >> 10) & 3, (o >> 12) & 15)
						tint = CAR_COLORS[Rng.h2(a.x, a.y, 71) % CAR_COLORS.size()]
					else:
						var k2: float = 0.82 + Rng.f2(x, y, 73) * 0.18
						tint = Color(k2, k2 * (0.94 + Rng.f2(x, y, 74) * 0.06), k2 * 0.92)
				A.draw(s, h, pos, tint)
	for cp in c.corpses:
		var cx: int = floori(cp["x"])
		var cy: int = floori(cp["y"])
		if (cx & 15) + (cy & 15) != s.dl or (cx >> 4) != c.cx or (cy >> 4) != c.cy:
			continue
		var rel: Vector2 = Iso.to_screen(float(cp["x"]) - bx, float(cp["y"]) - by)
		var fr: Array = EntityView.pick("z_lie", 0.0, int(cp["d"]))
		var frame: PackedInt32Array = fr[0]
		var look: Array = cp["l"]
		var cols: Array = [EntityView.ZSKIN[int(look[0]) % 4], EntityView.SHIRT[int(look[1]) % 10].lerp(Color(0.4, 0.38, 0.33), 0.5),
			EntityView.PANTS[int(look[2]) % 6].lerp(Color(0.3, 0.3, 0.27), 0.4), EntityView.HAIR[int(look[3]) % 6], Color.WHITE]
		for li in range(5):
			if fr[1]:
				Art.chars.draw_flipped(s, frame[li], rel, cols[li])
			else:
				Art.chars.draw(s, frame[li], rel, cols[li])

func _draw_wall(s: Strip, pos: Vector2, wid: int, st: int, orient: int, x: int, y: int, b1: int, b2: int) -> void:
	var A: Atlas = Art.world
	var mat: int = wid >> 2
	var shape: int = wid & 3
	var tex: int = Defs.WALL_MATS[mat][0]
	var tint: Color = _wall_tints[mat]
	if b1 != 0 and not s.blds.has(b1): s.blds.append(b1)
	if b2 != 0 and not s.blds.has(b2): s.blds.append(b2)
	var spr: Array = Art.wall_spr[tex][orient]
	if tex >= Defs.WT_PICKET:
		if shape == Defs.WS_DOOR:
			A.draw(s, spr[Art.WV_DOOR], pos, tint)
			var open: bool = (st & (Defs.ES_OPEN | Defs.ES_BROKEN)) != 0
			var key: String = ("gate_chain" if tex == Defs.WT_CHAIN else "gate") + ("_open" if open else "")
			if not ((st & Defs.ES_BROKEN) != 0):
				A.draw(s, Art.ov[key][orient], pos, tint)
		else:
			A.draw(s, spr[Art.WV_SOLID], pos, tint)
		return
	var cut := false
	if cut_bld != 0 and (b1 == cut_bld or b2 == cut_bld):
		cut = (y > cut_tile.y) if orient == 0 else (x > cut_tile.x)
	var v: int = Art.WV_SOLID
	if shape == Defs.WS_WINDOW: v = Art.WV_WINDOW
	elif shape == Defs.WS_DOOR or shape == Defs.WS_ARCH: v = Art.WV_DOOR
	if cut:
		v = Art.WV_CUT_DOOR if (shape == Defs.WS_DOOR or shape == Defs.WS_ARCH) else Art.WV_CUT
	A.draw(s, spr[v], pos, tint)
	var planks: int = (st & Defs.ES_PLANK_MASK) >> Defs.ES_PLANK_SHIFT
	if shape == Defs.WS_DOOR:
		if (st & Defs.ES_BROKEN) != 0:
			if not cut: A.draw(s, Art.ov["door_broken"][orient], pos)
		elif (st & Defs.ES_OPEN) != 0:
			A.draw(s, Art.ov["door_open_cut" if cut else "door_open"][orient], pos)
		else:
			A.draw(s, Art.ov["door_cut" if cut else "door"][orient], pos)
		if planks > 0 and not cut:
			A.draw(s, Art.ov["dplanks%d" % planks][orient], pos)
	elif shape == Defs.WS_WINDOW and not cut:
		if (st & Defs.ES_CURTAIN) != 0:
			A.draw(s, Art.ov["curtain"][orient], pos)
		if (st & Defs.ES_BROKEN) != 0:
			A.draw(s, Art.ov["glass_broken"][orient], pos)
		elif (st & Defs.ES_OPEN) != 0:
			A.draw(s, Art.ov["glass_open"][orient], pos)
		else:
			A.draw(s, Art.ov["glass"][orient], pos)
		if planks > 0:
			A.draw(s, Art.ov["planks%d" % planks][orient], pos)

func _draw_roof(s: Strip) -> void:
	# all roof tiles of a strip go out as ONE triangle array (one draw call per strip)
	var c: Chunk = s.c
	var H: float = Iso.WALL_H
	var pts := PackedVector2Array()
	var cols := PackedColorArray()
	var uvs := PackedVector2Array()
	var idx := PackedInt32Array()
	for lx in range(maxi(0, s.dl - 15), mini(15, s.dl) + 1):
		var ly: int = s.dl - lx
		var i: int = ly * 16 + lx
		var b: int = c.bld[i]
		if b == 0 or b == cut_bld:
			continue
		var pos := Vector2((lx - ly) * 32.0, (lx + ly) * 16.0)
		var r: int = c.roof[i]
		var h0: float = H + (r & 3) * 11.0
		var h1: float = H + ((r >> 2) & 3) * 11.0
		var h2: float = H + ((r >> 4) & 3) * 11.0
		var h3: float = H + ((r >> 6) & 3) * 11.0
		var k: float = clampf(0.92 + (h3 - h1) * 0.018 + (h0 - h2) * 0.012, 0.62, 1.2)
		var base: Color = ROOF_COLORS[(b >> 3) % ROOF_COLORS.size()]
		var col := Color(base.r * k, base.g * k, base.b * k)
		var n: int = pts.size()
		# 0.5 px overlap hides hairlines between neighbouring roof tiles
		pts.append(pos + Vector2(0, -h0 - 0.5))
		pts.append(pos + Vector2(32.5, 16 - h1))
		pts.append(pos + Vector2(0, 32.5 - h2))
		pts.append(pos + Vector2(-32.5, 16 - h3))
		for q in range(4):
			cols.append(col)
			uvs.append(_roof_uv[q])
		idx.append_array(PackedInt32Array([n, n + 1, n + 2, n, n + 2, n + 3]))
	if pts.size() > 0:
		RenderingServer.canvas_item_add_triangle_array(s.get_canvas_item(), idx, pts, cols, uvs, PackedInt32Array(), PackedFloat32Array(), Art.world.texture.get_rid())
