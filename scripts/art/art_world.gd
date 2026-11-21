class_name ArtWorld
extends RefCounted
## Generates ground tiles, walls, fences, overlays and all world objects.

const T := 0.14     # wall thickness in tiles

static func queue_jobs(jobs: Array[Callable]) -> void:
	Art.ground.resize(Defs.G_COUNT)
	for g in range(Defs.G_COUNT):
		Art.ground[g] = []
	ArtGround.queue_jobs(jobs)
	Art.wall_spr.resize(Defs.WT_COUNT)
	for t in range(Defs.WT_COUNT):
		var tt: int = t
		jobs.append(func(): _gen_wall_tex(tt))
	jobs.append(_gen_overlays)
	jobs.append(_gen_nature)
	jobs.append(_gen_crops)
	var models: Dictionary = Models.all()
	var rendered: Dictionary = ArtModels.rendered_vehicles()
	for id in models.keys():
		if rendered.has(id):
			continue                       # drawn from its 3D render instead (ArtModels)
		var oid: int = id
		var boxes: Array = models[id]
		jobs.append(func(): _gen_object(oid, boxes))

# ------------------------------------------------------------------ walls
static func _tex_mat(t: int) -> int:
	match t:
		Defs.WT_SIDING: return Painter.M_SIDING
		Defs.WT_BRICK: return Painter.M_BRICK
		Defs.WT_PLASTER: return Painter.M_PLASTER
		Defs.WT_CONCRETE: return Painter.M_CONCRETE
		Defs.WT_METAL: return Painter.M_CORRUGATED
		Defs.WT_LOG: return Painter.M_LOG
		Defs.WT_PLANK: return Painter.M_PLANK_V
		Defs.WT_TILE: return Painter.M_TILE
		Defs.WT_PICKET: return Painter.M_PICKET
		Defs.WT_CHAIN: return Painter.M_MESH
		Defs.WT_STONE: return Painter.M_STONE
		Defs.WT_HEDGE: return Painter.M_HEDGE
	return Painter.M_FLAT

static func _transpose(boxes: Array) -> Array:
	var out: Array = []
	for b in boxes:
		out.append([b[1], b[0], b[2], b[4], b[3], b[5], b[6], b[7]])
	return out

static func _add_edge_sprite(boxes: Array, orient: int, maxz: int = 76) -> int:
	var bb: Array = boxes if orient == 0 else _transpose(boxes)
	var p: Painter = Painter.render_tile_part(Painter.sort_boxes(bb), 0, 0, maxz, 8)
	return Art.world.add(p.img, 8 + 32, 8 + maxz)

static func _gen_wall_tex(t: int) -> void:
	var m: int = _tex_mat(t)
	var w := Color.WHITE
	var H: float = Iso.WALL_H
	var sets: Array = []
	if t <= Defs.WT_TILE:
		var trim := Color(0.86, 0.86, 0.84)
		sets = [
			[[0, 0, 0, 1, T, H, w, m]],
			[[0, 0, 0, 1, T, 26, w, m], [0, 0, 54, 1, T, H, w, m], [0, 0, 26, 0.2, T, 54, w, m], [0.8, 0, 26, 1, T, 54, w, m],
				[0.18, 0, 25, 0.82, T + 0.03, 27, trim, Painter.M_FLAT], [0.18, T, 26, 0.2, T + 0.02, 55, trim, Painter.M_FLAT], [0.8, T, 26, 0.82, T + 0.02, 55, trim, Painter.M_FLAT],
				[0.18, T, 54, 0.82, T + 0.02, 56, trim, Painter.M_FLAT]],
			[[0, 0, 0, 0.1, T, H, w, m], [0.9, 0, 0, 1, T, H, w, m], [0.1, 0, 62, 0.9, T, H, w, m]],
			[[0, 0, 0, 1, T, 9, Color(0.8, 0.8, 0.8), Painter.M_FLAT]],
			[[0, 0, 0, 0.1, T, 9, Color(0.8, 0.8, 0.8), Painter.M_FLAT], [0.9, 0, 0, 1, T, 9, Color(0.8, 0.8, 0.8), Painter.M_FLAT]],
			[[0, 0, 0, T, T, H, w, m]],
			[[0, 0, 0, T, T, 9, Color(0.8, 0.8, 0.8), Painter.M_FLAT]],
		]
	elif t == Defs.WT_PICKET:
		var solid := [[0, 0, 0, 1, 0.05, 22, w, m], [0, 0, 0, 0.07, 0.07, 25, w, Painter.M_FLAT]]
		var posts := [[0, 0, 0, 0.07, 0.07, 25, w, Painter.M_FLAT], [0.93, 0, 0, 1, 0.07, 25, w, Painter.M_FLAT]]
		sets = [solid, solid, posts, solid, posts, [[0, 0, 0, 0.07, 0.07, 25, w, Painter.M_FLAT]], [[0, 0, 0, 0.07, 0.07, 25, w, Painter.M_FLAT]]]
	elif t == Defs.WT_CHAIN:
		var solid2 := [[0, 0, 0, 1, 0.03, 46, w, m], [0, 0, 0, 0.06, 0.06, 48, Color(0.7, 0.7, 0.7), Painter.M_FLAT], [0, 0, 45, 1, 0.04, 47, Color(0.7, 0.7, 0.7), Painter.M_FLAT]]
		var posts2 := [[0, 0, 0, 0.06, 0.06, 48, Color(0.7, 0.7, 0.7), Painter.M_FLAT], [0.94, 0, 0, 1, 0.06, 48, Color(0.7, 0.7, 0.7), Painter.M_FLAT]]
		sets = [solid2, solid2, posts2, solid2, posts2, [[0, 0, 0, 0.06, 0.06, 48, Color(0.7, 0.7, 0.7), Painter.M_FLAT]], [[0, 0, 0, 0.06, 0.06, 48, Color(0.7, 0.7, 0.7), Painter.M_FLAT]]]
	elif t == Defs.WT_STONE:
		var solid3 := [[0, 0, 0, 1, 0.22, 15, w, m]]
		sets = [solid3, solid3, [[0, 0, 0, 0.12, 0.22, 15, w, m], [0.88, 0, 0, 1, 0.22, 15, w, m]], solid3, solid3, [[0, 0, 0, 0.22, 0.22, 15, w, m]], [[0, 0, 0, 0.22, 0.22, 15, w, m]]]
	else:
		var solid4 := [[0, 0, 0, 1, 0.3, 30, w, m]]
		sets = [solid4, solid4, [[0, 0, 0, 0.1, 0.3, 30, w, m], [0.9, 0, 0, 1, 0.3, 30, w, m]], [[0, 0, 0, 1, 0.3, 10, w, m]], solid4, [[0, 0, 0, 0.3, 0.3, 30, w, m]], [[0, 0, 0, 0.3, 0.3, 10, w, m]]]
	var per_orient: Array = []
	for orient in range(2):
		var arr: Array = []
		for s in sets:
			arr.append(_add_edge_sprite(s, orient))
		per_orient.append(arr)
	Art.wall_spr[t] = per_orient

static func _pair(key: String, boxes: Array) -> void:
	Art.ov[key] = [_add_edge_sprite(boxes, 0), _add_edge_sprite(boxes, 1)]

static func _gen_overlays() -> void:
	var glass := Color(0.62, 0.78, 0.88, 0.42)
	var frame := Color(0.9, 0.9, 0.88)
	var G: int = Painter.M_GLASS
	var F: int = Painter.M_FLAT
	_pair("glass", [[0.2, T * 0.4, 27, 0.8, T * 0.6, 54, glass, G], [0.49, T * 0.6, 27, 0.51, T * 0.62, 54, frame, F], [0.2, T * 0.6, 40, 0.8, T * 0.62, 41, frame, F]])
	_pair("glass_open", [[0.2, T * 0.4, 41, 0.8, T * 0.6, 54, glass, G], [0.49, T * 0.6, 41, 0.51, T * 0.62, 54, frame, F], [0.2, T * 0.6, 40, 0.8, T * 0.62, 42, frame, F]])
	_pair("glass_broken", [[0.2, T * 0.4, 27, 0.3, T * 0.6, 34, glass, G], [0.7, T * 0.4, 46, 0.8, T * 0.6, 54, glass, G], [0.62, T * 0.4, 27, 0.8, T * 0.6, 31, glass, G], [0.2, T * 0.4, 49, 0.36, T * 0.6, 54, glass, G]])
	_pair("curtain", [[0.2, T * 0.2, 27, 0.8, T * 0.3, 54, Color(0.55, 0.5, 0.42), Painter.M_FABRIC]])
	var wood := Color(0.55, 0.42, 0.27)
	for k in range(1, 5):
		var planks: Array = []
		var dplanks: Array = []
		for i in range(k):
			planks.append([0.06, T, 28 + i * 7 - (i % 2), 0.94, T + 0.04, 33 + i * 7 + (i % 2), wood, Painter.M_PLANK_H])
			dplanks.append([0.04, T, 10 + i * 13 - (i % 2), 0.96, T + 0.04, 16 + i * 13 + (i % 2), wood, Painter.M_PLANK_H])
		_pair("planks%d" % k, planks)
		_pair("dplanks%d" % k, dplanks)
	var door := Color(0.47, 0.33, 0.22)
	_pair("door", [[0.1, T * 0.3, 0, 0.9, T * 0.7, 62, door, Painter.M_PLANK_V], [0.76, T * 0.7, 28, 0.81, T * 0.7 + 0.03, 32, Color(0.8, 0.72, 0.4), F]])
	_pair("door_open", [[0.1, T, 0, 0.16, T + 0.8, 62, door, Painter.M_PLANK_V]])
	_pair("door_cut", [[0.1, T * 0.3, 0, 0.9, T * 0.7, 9, door, F]])
	_pair("door_open_cut", [[0.1, T, 0, 0.16, T + 0.8, 9, door, F]])
	_pair("door_broken", [[0.1, T * 0.3, 0, 0.3, T * 0.7, 20, door, Painter.M_PLANK_V], [0.78, T * 0.3, 0, 0.9, T * 0.7, 34, door, Painter.M_PLANK_V]])
	var gate := Color(0.75, 0.72, 0.66)
	_pair("gate", [[0.07, 0, 0, 0.93, 0.05, 21, gate, Painter.M_PICKET], [0.07, 0.05, 9, 0.93, 0.06, 11, gate, F]])
	_pair("gate_open", [[0.07, 0.05, 0, 0.11, 0.9, 21, gate, Painter.M_PICKET]])
	_pair("gate_chain", [[0.06, 0, 0, 0.94, 0.03, 44, Color(0.6, 0.64, 0.66), Painter.M_MESH], [0.06, 0, 43, 0.94, 0.04, 45, Color(0.5, 0.5, 0.5), F], [0.06, 0, 0, 0.94, 0.04, 2, Color(0.5, 0.5, 0.5), F]])
	_pair("gate_chain_open", [[0.06, 0.04, 0, 0.09, 0.9, 44, Color(0.6, 0.64, 0.66), Painter.M_MESH]])
	_gen_roofs()
	# white pixel block for solid colour polygons
	var wp := Image.create(8, 8, false, Image.FORMAT_RGBA8)
	wp.fill(Color.WHITE)
	Art.misc["white"] = Art.world.add(wp, 0, 0, "", false)
	# blood splats
	var splats: Array = []
	for i in range(4):
		var bp := Painter.new(40, 22)
		for k in range(7 + i * 2):
			var cx: float = 20.0 + (Rng.f2(k, i, 91) - 0.5) * 22.0
			var cy: float = 11.0 + (Rng.f2(k, i, 92) - 0.5) * 10.0
			var r: float = 2.0 + Rng.f2(k, i, 93) * 5.0
			bp.ellipse(cx, cy, r, r * 0.5, Color(0.36 + Rng.f2(k, i, 94) * 0.1, 0.05, 0.04, 0.8))
		splats.append(Art.world.add(bp.img, 20, 11 - 16))
	Art.misc["blood"] = splats
	# selection diamond + ground shadow
	var sp := Painter.new(64, 32)
	for yy in range(32):
		for xx in range(64):
			var d: float = absf(xx + 0.5 - 32.0) / 32.0 + absf(yy + 0.5 - 16.0) / 16.0
			if d <= 1.0 and d > 0.86:
				sp.img.set_pixel(xx, yy, Color(1, 1, 1, 0.9))
			elif d <= 0.86:
				sp.img.set_pixel(xx, yy, Color(1, 1, 1, 0.16))
	Art.misc["select"] = Art.world.add(sp.img, 32, 0, "", false)
	var sh := Painter.new(32, 16)
	for yy in range(16):
		for xx in range(32):
			var dx: float = (xx + 0.5 - 16.0) / 16.0
			var dy: float = (yy + 0.5 - 8.0) / 8.0
			var d2: float = dx * dx + dy * dy
			if d2 < 1.0:
				sh.img.set_pixel(xx, yy, Color(0, 0, 0, 0.38 * (1.0 - d2)))
	Art.misc["shadow"] = Art.world.add(sh.img, 16, 8, "", false)

# ------------------------------------------------------------------ roofs
## roof tile textures (flat diamonds, tinted and skewed at draw time): asphalt shingles in rows
## across the slope, one texture for faces that slope along x and one for faces that slope along y
## (so the rows always run along the eaves), and a gravel-and-membrane flat roof. Then a few things
## that stand on flat roofs.
static func _gen_roofs() -> void:
	var n1: Image = ArtGround.noise(9101, 0.05, 3)
	var n2: Image = ArtGround.noise(9102, 0.16, 2)
	for kind in ["roof_flat", "roof_x", "roof_y"]:
		var p := Painter.new(64, 32)
		for yy in range(32):
			for xx in range(64):
				var a: float = (xx + 0.5 - 32.0) / 32.0
				var b: float = (yy + 0.5) / 16.0
				var wx: float = (a + b) * 0.5
				var wy: float = (b - a) * 0.5
				if wx < 0.0 or wx >= 1.0 or wy < 0.0 or wy >= 1.0:
					continue
				var ix: int = floori(wx * 64.0)
				var iy: int = floori(wy * 64.0)
				var lo: float = n1.get_pixel(ix, iy).r
				var hi: float = n2.get_pixel(ix, iy).r
				var h: float = Rng.f2(ix, iy, 9103)
				var k := 1.0
				if kind == "roof_flat":
					# rolled roofing in strips, gravel over it, stains where water stood
					k = 0.86 + (h - 0.5) * 0.16 + (lo - 0.5) * 0.1
					if h > 0.97: k += 0.12
					elif h < 0.025: k -= 0.16
					if fposmod(wy * 2.0, 1.0) < 0.03: k -= 0.07
					if lo > 0.72: k -= (lo - 0.72) * 0.5
				else:
					var across: float = wx if kind == "roof_x" else wy      # down the slope
					var along: float = wy if kind == "roof_x" else wx       # along the eaves
					var ra: float = across * 8.0
					var ri: int = floori(ra)
					var fa: float = ra - ri
					var tb: float = along * 4.0 + (0.5 if ri % 2 == 1 else 0.0)
					var ti: int = floori(tb)
					k = 0.9 + Rng.f2(ri, posmod(ti, 4), 9104) * 0.14         # each tab a shade of its own
					k *= 0.92 + lo * 0.12                                    # weathering
					if fa < 0.13:
						k *= 0.62                                            # the shadow under the row above
					elif fa < 0.24:
						k *= 1.08                                            # the tab's lit lower edge
					if fposmod(tb, 1.0) < 0.035:
						k *= 0.7                                             # the slot between tabs
					k *= 0.95 + h * 0.1                                      # granules
					if hi > 0.82:
						k *= 0.9                                             # a streak
				k = clampf(k, 0.0, 1.0)
				var col := Color(k, k, k)
				if kind != "roof_flat" and lo < 0.12:
					col = Color(k * 0.85, k * 0.95, k * 0.7)                # a little moss
				p.img.set_pixel(xx, yy, col)
		Art.misc[kind] = Art.world.add(p.img, 32, 0, "", false)
	var metal := Color(0.66, 0.68, 0.68)
	var dark := Color(0.3, 0.31, 0.32)
	var M: int = Painter.M_FLAT
	Art.misc["roof_ac"] = _add_edge_sprite([[0.18, 0.22, 0, 0.82, 0.78, 20, metal, Painter.M_CORRUGATED], [0.28, 0.32, 20, 0.72, 0.68, 21, dark, M],
		[0.12, 0.5, 0, 0.18, 0.56, 6, dark, M]], 0, 30)
	Art.misc["roof_vent"] = _add_edge_sprite([[0.44, 0.44, 0, 0.56, 0.56, 13, Color(0.5, 0.5, 0.5), M], [0.4, 0.4, 13, 0.6, 0.6, 15, Color(0.4, 0.4, 0.4), M]], 0, 20)
	Art.misc["roof_hatch"] = _add_edge_sprite([[0.3, 0.3, 0, 0.7, 0.7, 5, Color(0.55, 0.55, 0.52), M], [0.33, 0.33, 5, 0.67, 0.67, 6, Color(0.62, 0.62, 0.6), M]], 0, 12)
	Art.misc["roof_skylight"] = _add_edge_sprite([[0.22, 0.2, 0, 0.78, 0.8, 4, Color(0.6, 0.6, 0.58), M], [0.26, 0.24, 4, 0.74, 0.76, 6, Color(0.55, 0.7, 0.8, 0.85), Painter.M_GLASS]], 0, 12)

# ------------------------------------------------------------------ nature
static func _shadow(p: Painter, cx: float, cy: float, rx: float, ry: float, a: float = 0.22) -> void:
	for yy in range(int(cy - ry), int(cy + ry) + 1):
		for xx in range(int(cx - rx), int(cx + rx) + 1):
			var dx: float = (xx + 0.5 - cx) / rx
			var dy: float = (yy + 0.5 - cy) / ry
			if dx * dx + dy * dy <= 1.0:
				p.put(xx, yy, Color(0, 0, 0, a))

static func _trunk(p: Painter, cx: float, base_y: float, hgt: float, wd: float, c: Color, birch: bool = false) -> void:
	for i in range(int(hgt)):
		var yy: int = int(base_y) - i
		var ww: float = wd * (1.0 - 0.35 * float(i) / hgt) + (1.5 if i < 3 else 0.0)
		for xx in range(int(cx - ww * 0.5), int(cx + ww * 0.5) + 1):
			var t: float = (xx - (cx - ww * 0.5)) / maxf(ww, 1.0)
			var k: float = 1.05 - t * 0.5 + (Rng.f2(xx, yy / 3, 5) - 0.5) * 0.16
			var col := Color(c.r * k, c.g * k, c.b * k)
			if birch and Rng.f2(xx / 2, yy / 2, 9) > 0.86:
				col = Color(0.15, 0.14, 0.13)
			p.put(xx, yy, col)

static func _reg(id: int, p: Painter, ax: float, ay: float, part: int = 0) -> void:
	var hnd: int = Art.world.add(Painter.stylize(p.img, true, false, 0.02, id), ax, ay)
	for r in range(4):
		Art.obj_spr[Defs.ocell(id, r, part)] = hnd

static func _gen_nature() -> void:
	# anchor = tile top corner; tile centre ground point = anchor + (0,16)
	# oak
	var p := Painter.new(104, 136)
	var ax := 52.0
	var ay := 100.0
	_shadow(p, ax, ay + 18, 30, 12)
	_trunk(p, ax, ay + 18, 46, 9, Color(0.36, 0.27, 0.19))
	var blobs := [[-16, -50, 22, 18], [16, -48, 22, 18], [0, -66, 26, 20], [-20, -34, 18, 14], [20, -32, 18, 14], [0, -44, 24, 18], [-6, -78, 18, 13]]
	for i in range(blobs.size()):
		var bl: Array = blobs[i]
		p.ball(ax + bl[0], ay + 16 + bl[1], bl[2], bl[3], Color(0.27, 0.42, 0.21), 40 + i, 0.2)
	_reg(Defs.O_TREE_OAK, p, ax, ay)
	# pine
	p = Painter.new(80, 140)
	ax = 40.0
	ay = 104.0
	_shadow(p, ax, ay + 18, 22, 9)
	_trunk(p, ax, ay + 18, 30, 7, Color(0.33, 0.24, 0.17))
	for tier in range(5):
		var ty: float = ay - 2 - tier * 19
		var half: float = 26.0 - tier * 4.5
		for row in range(30):
			var yy: int = int(ty) - row
			var hw: float = half * (1.0 - float(row) / 30.0)
			for xx in range(int(ax - hw), int(ax + hw) + 1):
				var n: float = Rng.f2(xx, yy, 70 + tier)
				if absf(xx - ax) > hw - 2.0 and n < 0.5:
					continue
				var k: float = 0.72 + n * 0.3 - float(xx - ax) / half * 0.16 + float(row) / 30.0 * 0.2
				p.put(xx, yy, Color(0.16 * k, 0.33 * k, 0.2 * k))
	_reg(Defs.O_TREE_PINE, p, ax, ay)
	# birch
	p = Painter.new(84, 124)
	ax = 42.0
	ay = 88.0
	_shadow(p, ax, ay + 18, 22, 9)
	_trunk(p, ax, ay + 18, 52, 6, Color(0.86, 0.85, 0.8), true)
	var bb := [[-10, -52, 17, 14], [11, -50, 17, 14], [0, -66, 19, 15], [-3, -42, 18, 12]]
	for i in range(bb.size()):
		var b2: Array = bb[i]
		p.ball(ax + b2[0], ay + 16 + b2[1], b2[2], b2[3], Color(0.45, 0.55, 0.25), 60 + i, 0.24)
	_reg(Defs.O_TREE_BIRCH, p, ax, ay)
	# dead tree
	p = Painter.new(72, 104)
	ax = 36.0
	ay = 68.0
	_shadow(p, ax, ay + 18, 14, 6)
	_trunk(p, ax, ay + 18, 48, 7, Color(0.33, 0.29, 0.25))
	var br := Color(0.3, 0.26, 0.22)
	p.line(ax, ay - 14, ax - 16, ay - 34, br, 2)
	p.line(ax, ay - 20, ax + 15, ay - 40, br, 2)
	p.line(ax - 10, ay - 26, ax - 22, ay - 30, br)
	p.line(ax + 9, ay - 32, ax + 22, ay - 34, br)
	p.line(ax, ay - 28, ax + 2, ay - 52, br, 2)
	p.line(ax + 1, ay - 44, ax - 9, ay - 58, br)
	_reg(Defs.O_TREE_DEAD, p, ax, ay)
	# bush & berry bush
	for bi in range(2):
		p = Painter.new(64, 48)
		ax = 32.0
		ay = 14.0
		_shadow(p, ax, ay + 20, 22, 9)
		p.ball(ax - 9, ay + 12, 13, 10, Color(0.25, 0.4, 0.2), 80, 0.22)
		p.ball(ax + 9, ay + 13, 13, 10, Color(0.25, 0.4, 0.2), 81, 0.22)
		p.ball(ax, ay + 8, 14, 11, Color(0.28, 0.44, 0.22), 82, 0.22)
		if bi == 1:
			for k in range(16):
				var bx: int = int(ax - 16 + Rng.f2(k, 1, 83) * 32.0)
				var by: int = int(ay + 1 + Rng.f2(k, 2, 83) * 18.0)
				if p.img.get_pixel(bx, by).a > 0.5:
					p.put(bx, by, Color(0.72, 0.12, 0.2))
					p.put(bx + 1, by, Color(0.55, 0.08, 0.15))
		_reg(Defs.O_BERRY_BUSH if bi == 1 else Defs.O_BUSH, p, ax, ay)
		if bi == 1:
			# picked variant (part 1): plain bush
			var p2 := Painter.new(64, 48)
			_shadow(p2, ax, ay + 20, 22, 9)
			p2.ball(ax - 9, ay + 12, 13, 10, Color(0.25, 0.4, 0.2), 80, 0.22)
			p2.ball(ax + 9, ay + 13, 13, 10, Color(0.25, 0.4, 0.2), 81, 0.22)
			p2.ball(ax, ay + 8, 14, 11, Color(0.28, 0.44, 0.22), 82, 0.22)
			_reg(Defs.O_BERRY_BUSH, p2, ax, ay, 1)
	# rock
	p = Painter.new(64, 44)
	ax = 32.0
	ay = 10.0
	_shadow(p, ax, ay + 20, 20, 8)
	p.ball(ax - 4, ay + 12, 15, 11, Color(0.5, 0.5, 0.48), 90, 0.1)
	p.ball(ax + 8, ay + 16, 10, 7, Color(0.44, 0.44, 0.43), 91, 0.1)
	_reg(Defs.O_ROCK, p, ax, ay)
	# stump
	p = Painter.new(64, 40)
	ax = 32.0
	ay = 8.0
	_shadow(p, ax, ay + 18, 12, 5)
	_trunk(p, ax, ay + 20, 10, 12, Color(0.36, 0.27, 0.19))
	p.ellipse(ax, ay + 10, 6.5, 3.2, Color(0.68, 0.56, 0.38))
	p.ellipse(ax, ay + 10, 3.0, 1.5, Color(0.56, 0.44, 0.3))
	_reg(Defs.O_STUMP, p, ax, ay)
	# tall grass / reeds
	for gi in range(2):
		p = Painter.new(64, 48)
		ax = 32.0
		ay = 14.0
		for k in range(70):
			var gx: float = (Rng.f2(k, 1, 95 + gi) - 0.5)
			var gy: float = (Rng.f2(k, 2, 95 + gi) - 0.5)
			var sx: float = ax + (gx - gy) * 30.0
			var sy: float = ay + 16 + (gx + gy) * 15.0
			var hh: float = 8.0 + Rng.f2(k, 3, 95) * (8.0 if gi == 0 else 16.0)
			var kk: float = 0.7 + Rng.f2(k, 4, 95) * 0.5
			var col := Color(0.36 * kk, 0.5 * kk, 0.24 * kk) if gi == 0 else Color(0.42 * kk, 0.48 * kk, 0.26 * kk)
			p.line(sx, sy, sx + (Rng.f2(k, 5, 95) - 0.5) * 4.0, sy - hh, col)
			if gi == 1 and k % 3 == 0:
				p.put(int(sx), int(sy - hh), Color(0.4, 0.28, 0.16))
				p.put(int(sx), int(sy - hh) + 1, Color(0.4, 0.28, 0.16))
		_reg(Defs.O_TALL_GRASS if gi == 0 else Defs.O_REEDS, p, ax, ay)
	# flowers
	p = Painter.new(64, 40)
	ax = 32.0
	ay = 6.0
	var fcols := [Color(0.9, 0.85, 0.3), Color(0.85, 0.4, 0.5), Color(0.9, 0.9, 0.92), Color(0.6, 0.45, 0.8)]
	for k in range(22):
		var fx: float = (Rng.f2(k, 1, 99) - 0.5)
		var fy: float = (Rng.f2(k, 2, 99) - 0.5)
		var sx2: float = ax + (fx - fy) * 28.0
		var sy2: float = ay + 16 + (fx + fy) * 14.0
		p.line(sx2, sy2, sx2, sy2 - 4, Color(0.3, 0.48, 0.24))
		p.put(int(sx2), int(sy2) - 5, fcols[k % 4])
		p.put(int(sx2) + 1, int(sy2) - 5, fcols[k % 4].darkened(0.15))
	_reg(Defs.O_FLOWERS, p, ax, ay)
	# weeds pushing through pavement
	p = Painter.new(64, 40)
	ax = 32.0
	ay = 6.0
	for k in range(16):
		var wx: float = (Rng.f2(k, 1, 141) - 0.5)
		var wy: float = (Rng.f2(k, 2, 141) - 0.5)
		var sx3: float = ax + (wx - wy) * 26.0
		var sy3: float = ay + 16 + (wx + wy) * 13.0
		var kk2: float = 0.7 + Rng.f2(k, 3, 141) * 0.4
		p.line(sx3, sy3, sx3 + (Rng.f2(k, 4, 141) - 0.5) * 5.0, sy3 - 3.0 - Rng.f2(k, 5, 141) * 5.0, Color(0.34 * kk2, 0.46 * kk2, 0.22 * kk2))
	_reg(Defs.O_WEEDS, p, ax, ay)
	# snare trap
	p = Painter.new(64, 40)
	ax = 32.0
	ay = 6.0
	for k in range(20):
		var ang2: float = k / 20.0 * TAU
		p.put(int(ax + cos(ang2) * 9.0), int(ay + 17 + sin(ang2) * 4.5), Color(0.62, 0.52, 0.34))
	p.line(ax + 9, ay + 17, ax + 15, ay + 6, Color(0.42, 0.32, 0.2), 2)
	p.line(ax + 15, ay + 6, ax + 9, ay + 15, Color(0.62, 0.52, 0.34))
	_reg(Defs.O_SNARE, p, ax, ay)
	# bedroll
	p = Painter.new(72, 44)
	p.box([0.2, 0.05, 0, 0.8, 0.95, 3, Color(0.3, 0.4, 0.3), Painter.M_FABRIC], 36, 6)
	p.box([0.25, 0.08, 3, 0.75, 0.3, 5, Color(0.75, 0.72, 0.62), Painter.M_FABRIC], 36, 6)
	_reg(Defs.O_BEDROLL, p, 36, 6)
	# campfire: part 0 unlit, part 1 lit
	for lit in range(2):
		p = Painter.new(64, 56)
		ax = 32.0
		ay = 22.0
		for k in range(9):
			var ang: float = k / 9.0 * TAU
			p.ball(ax + cos(ang) * 13.0, ay + 16 + sin(ang) * 6.5, 4, 3, Color(0.5, 0.5, 0.48), 120 + k, 0.1)
		p.line(ax - 8, ay + 18, ax + 8, ay + 13, Color(0.3, 0.22, 0.15), 3)
		p.line(ax - 7, ay + 13, ax + 8, ay + 19, Color(0.26, 0.19, 0.13), 3)
		if lit == 1:
			for k in range(46):
				var fx2: float = (Rng.f2(k, 1, 130) - 0.5) * 14.0
				var fh: float = 6.0 + Rng.f2(k, 2, 130) * 16.0 * (1.0 - absf(fx2) / 8.0)
				var c := Color(1.0, 0.55 + Rng.f2(k, 3, 130) * 0.35, 0.12)
				p.line(ax + fx2, ay + 16, ax + fx2 * 0.4, ay + 16 - fh, c)
			p.ball(ax, ay + 12, 4, 5, Color(1.0, 0.95, 0.6), 131, 0.05)
		_reg(Defs.O_CAMPFIRE, p, ax, ay, lit)

## the second dozen crops: [leaf, fruit, shape]
const NEW_CROPS := [["4a8a3a", "8ac85a", "vine"], ["5a8a4a", "e8e0d0", "spike"], ["3a6a2a", "d8a030", "gourd"], ["3a7a3a", "3a6a2a", "vine"], ["5a9a3a", "c83a4a", "root"], ["5a7a3a", "7a1a3a", "root"], ["2a6a2a", "2a6a2a", "rosette"], ["4a7a2a", "e8c020", "tall"], ["5a8a4a", "8ab06a", "rosette"], ["8a7a5a", "d8c8a8", "cap"], ["3a6a2a", "b83a30", "tree"], ["3a5a3a", "3a4ab0", "bush"]]

static func _paint_crop(p: Painter, spec: Array, sx: float, sy: float, size: float, stage: int, green: Color, si: int) -> void:
	var leaf: Color = Color(String(spec[0])) if stage < 4 else green
	var fruit := Color(String(spec[1]))
	match String(spec[2]):
		"vine":
			p.ball(sx, sy - size * 0.6, size * 0.9, size * 0.7, leaf, 300 + si, 0.35)
			if stage == 3:
				p.ball(sx + 1, sy - size * 0.4, 1.3, 2.2, fruit, 305 + si, 0.1)
		"spike":
			for k in range(2):
				p.line(sx + k, sy, sx + k * 2 - 1, sy - size * 1.8, leaf)
			if stage == 3:
				p.ball(sx, sy - 1, 2.0, 1.6, fruit, 310 + si, 0.1)
		"gourd":
			p.ball(sx, sy - size * 0.3, size * 1.1, size * 0.45, leaf, 315 + si, 0.3)
			if stage >= 2 and stage < 4:
				p.ball(sx + 1, sy - size * 0.35, size * (0.45 if stage == 2 else 0.7), size * 0.5, fruit if stage == 3 else Color(0.6, 0.7, 0.3), 318 + si, 0.1)
		"root":
			for k2 in range(3):
				p.line(sx + k2 - 1, sy, sx + (k2 - 1) * 2, sy - size * 1.2, leaf)
			if stage == 3:
				p.ball(sx, sy - 0.5, 2.0, 1.8, fruit, 320 + si, 0.1)
		"rosette":
			p.ball(sx, sy - size * 0.4, size, size * 0.55, leaf, 325 + si, 0.25)
		"cap":
			p.line(sx, sy, sx, sy - size * 0.6, Color(0.85, 0.82, 0.72))
			p.ball(sx, sy - size * 0.7, size * 0.8, size * 0.35, fruit if stage >= 2 else Color(0.7, 0.66, 0.56), 330 + si, 0.1)
		"tall":
			p.line(sx, sy, sx, sy - size * 4.0, leaf.darkened(0.15))
			p.ball(sx - 1, sy - size * 2.0, size * 0.5, size * 0.3, leaf, 335 + si, 0.2)
			if stage >= 2:
				p.ball(sx, sy - size * 4.2, size * (0.5 if stage == 2 else 0.85), size * 0.6, fruit if stage == 3 else leaf, 338 + si, 0.1)
		"tree":
			p.line(sx, sy, sx, sy - size * 3.2, Color(0.4, 0.3, 0.2))
			p.ball(sx, sy - size * 3.6, size * 1.3, size * 1.1, leaf, 340 + si, 0.3)
			if stage == 3:
				p.put(int(sx) - 2, int(sy - size * 3.4), fruit)
				p.put(int(sx) + 2, int(sy - size * 3.9), fruit)
				p.put(int(sx), int(sy - size * 3.2), fruit)
		"bush":
			p.ball(sx, sy - size * 0.7, size * 1.0, size * 0.8, leaf, 345 + si, 0.35)
			if stage == 3:
				p.put(int(sx) - 2, int(sy - size * 0.6), fruit)
				p.put(int(sx) + 2, int(sy - size * 0.9), fruit)

static func _gen_crops() -> void:
	var ids := [Defs.O_CROP_POTATO, Defs.O_CROP_CABBAGE, Defs.O_CROP_CARROT, Defs.O_CROP_TOMATO,
		Defs.O_CROP_CORN, Defs.O_CROP_WHEAT, Defs.O_CROP_LETTUCE, Defs.O_CROP_PUMPKIN, Defs.O_CROP_PEPPER, Defs.O_CROP_ONION, Defs.O_CROP_STRAWBERRY, Defs.O_CROP_BEANS,
		Defs.O_CROP_PEA, Defs.O_CROP_GARLIC, Defs.O_CROP_SQUASH, Defs.O_CROP_CUCUMBER, Defs.O_CROP_RADISH, Defs.O_CROP_BEET, Defs.O_CROP_SPINACH, Defs.O_CROP_SUNFLOWER, Defs.O_CROP_HERBS, Defs.O_CROP_OYSTER_MUSHROOM, Defs.O_CROP_APPLE, Defs.O_CROP_BLUEBERRIES]
	for ci in range(ids.size()):
		for stage in range(5):
			var p := Painter.new(64, 56)
			var ax := 32.0
			var ay := 22.0
			var green := Color(0.3, 0.5, 0.24)
			if stage == 4:
				green = Color(0.45, 0.38, 0.2)
			var spots := [Vector2(-0.22, -0.22), Vector2(0.22, -0.22), Vector2(-0.22, 0.22), Vector2(0.22, 0.22)]
			for si in range(4):
				var sp: Vector2 = spots[si]
				var sx: float = ax + (sp.x - sp.y) * 32.0
				var sy: float = ay + 16 + (sp.x + sp.y) * 16.0
				var size: float = [1.5, 3.5, 5.5, 7.0, 5.0][stage]
				if stage == 0:
					p.line(sx, sy, sx, sy - 3, green)
					p.put(int(sx) + 1, int(sy) - 3, green)
					continue
				match ci:
					0:
						p.ball(sx, sy - size * 0.7, size, size * 0.8, green, 200 + si, 0.3)
						if stage == 3:
							p.put(int(sx), int(sy - size), Color(0.95, 0.95, 0.9))
							p.put(int(sx) + 2, int(sy - size) + 2, Color(0.95, 0.95, 0.9))
					1:
						var cg := Color(0.5, 0.66, 0.4) if stage < 4 else green
						p.ball(sx, sy - size * 0.5, size, size * 0.7, cg, 210 + si, 0.12)
						if stage >= 2 and stage < 4:
							p.ball(sx, sy - size * 0.6, size * 0.5, size * 0.4, Color(0.68, 0.8, 0.55), 215 + si, 0.1)
					2:
						for k in range(int(size) + 2):
							p.line(sx, sy, sx + (k - size * 0.5) * 1.2, sy - size * 1.3, green)
						if stage == 3:
							p.put(int(sx), int(sy), Color(0.9, 0.5, 0.15))
							p.put(int(sx), int(sy) - 1, Color(0.9, 0.5, 0.15))
					4:  # corn: tall stalks, yellow ears when ripe
						p.line(sx, sy, sx, sy - size * 3.4, Color(0.42, 0.6, 0.3))
						p.line(sx, sy - size * 1.6, sx - size * 0.8, sy - size * 2.2, green)
						p.line(sx, sy - size * 2.4, sx + size * 0.8, sy - size * 3.0, green)
						if stage == 3:
							p.ball(sx + 1, sy - size * 2.0, 1.5, 2.5, Color(0.92, 0.8, 0.3), 230 + si, 0.1)
					5:  # wheat: thin golden blades
						var wc: Color = green if stage < 3 else Color(0.85, 0.72, 0.38)
						for k2 in range(4):
							p.line(sx + k2 - 1.5, sy, sx + k2 - 2.0, sy - size * 2.4, wc)
					6:  # lettuce: pale rosette
						p.ball(sx, sy - size * 0.4, size, size * 0.55, Color(0.58, 0.8, 0.42) if stage < 4 else green, 240 + si, 0.15)
					7:  # pumpkin: vine, orange gourd when ripe
						p.ball(sx, sy - size * 0.3, size * 1.1, size * 0.4, green, 250 + si, 0.3)
						if stage >= 2 and stage < 4:
							p.ball(sx + 1, sy - size * 0.4, size * (0.4 if stage == 2 else 0.75), size * 0.55, Color(0.9, 0.5, 0.15) if stage == 3 else Color(0.6, 0.7, 0.3), 255 + si, 0.1)
					8:  # pepper
						p.ball(sx, sy - size * 0.9, size * 0.8, size * 0.8, green, 260 + si, 0.3)
						if stage == 3:
							p.ball(sx + 1, sy - size * 0.6, 1.6, 2.2, Color(0.85, 0.2, 0.15), 265 + si, 0.1)
					9:  # onion: upright hollow leaves
						for k3 in range(3):
							p.line(sx + k3 - 1, sy, sx + (k3 - 1) * 2, sy - size * 1.6, Color(0.42, 0.62, 0.38) if stage < 4 else green)
						if stage == 3:
							p.ball(sx, sy - 1, 2.2, 1.6, Color(0.88, 0.8, 0.6), 270 + si, 0.1)
					10:  # strawberry: low leaves, red berries
						p.ball(sx, sy - size * 0.35, size * 0.9, size * 0.45, green, 280 + si, 0.3)
						if stage == 3:
							p.put(int(sx) - 2, int(sy) - 1, Color(0.85, 0.15, 0.2))
							p.put(int(sx) + 2, int(sy) - 2, Color(0.85, 0.15, 0.2))
					11:  # beans: climbing on a stake
						p.line(sx, sy, sx, sy - size * 2.6, Color(0.55, 0.42, 0.25))
						p.ball(sx, sy - size * 1.4, size * 0.6, size * 1.1, green, 290 + si, 0.35)
						if stage == 3:
							p.line(sx + 2, sy - size * 1.2, sx + 2, sy - size * 0.7, Color(0.36, 0.62, 0.25))
					3:
						p.line(sx, sy, sx, sy - size * 2.0, Color(0.36, 0.3, 0.2))
						p.ball(sx, sy - size * 1.2, size * 0.8, size, green, 220 + si, 0.3)
						if stage == 3:
							p.put(int(sx) - 2, int(sy - size), Color(0.85, 0.15, 0.12))
							p.put(int(sx) + 2, int(sy - size * 1.5), Color(0.85, 0.15, 0.12))
							p.put(int(sx) + 1, int(sy - size * 0.7), Color(0.85, 0.15, 0.12))
					_:
						_paint_crop(p, NEW_CROPS[ci - 12], sx, sy, size, stage, green, si)
			var hnd: int = Art.world.add(Painter.stylize(p.img, true, false, 0.02, ids[ci] * 7 + stage), ax, ay)
			for r in range(4):
				Art.obj_spr[Defs.ocell(ids[ci], r, stage)] = hnd

# ------------------------------------------------------------------ box objects
static func _gen_object(id: int, boxes: Array) -> void:
	var d: Dictionary = Defs.obj(id)
	var sz: Array = d.get("sz", [1, 1])
	var maxz: int = 8
	for b in boxes:
		maxz = maxi(maxz, int(ceil(b[5])) + 2)
	var rots: int = 1 if d.get("sym", 0) == 1 else 4
	for r in range(rots):
		var rb: Array = Painter.rotate_boxes(boxes, sz[0], sz[1], r)
		var sorted: Array = Painter.sort_boxes(rb)
		var fs: Vector2i = Defs.obj_size(id, r)
		for j in range(fs.y):
			for i in range(fs.x):
				var p: Painter = Painter.render_tile_part(sorted, i, j, maxz, 2)
				var hnd: int = Art.world.add(Painter.stylize(p.img, fs == Vector2i(1, 1), true, 0.025, id, fs == Vector2i(1, 1)), 2 + 32, 2 + maxz)
				var part: int = j * fs.x + i
				if rots == 1:
					for rr in range(4):
						Art.obj_spr[Defs.ocell(id, rr, part)] = hnd
				else:
					Art.obj_spr[Defs.ocell(id, r, part)] = hnd
