class_name ArtWorld
extends RefCounted
## Generates ground tiles, walls, fences, overlays and all world objects.

const T := 0.14     # wall thickness in tiles

static func queue_jobs(jobs: Array[Callable]) -> void:
	Art.ground.resize(Defs.G_COUNT)
	for g in range(Defs.G_COUNT):
		Art.ground[g] = []
		if g == Defs.G_VOID:
			continue
		var gg: int = g
		jobs.append(func(): _gen_ground(gg))
	Art.wall_spr.resize(Defs.WT_COUNT)
	for t in range(Defs.WT_COUNT):
		var tt: int = t
		jobs.append(func(): _gen_wall_tex(tt))
	jobs.append(_gen_overlays)
	jobs.append(_gen_nature)
	jobs.append(_gen_crops)
	var models: Dictionary = Models.all()
	for id in models.keys():
		var oid: int = id
		var boxes: Array = models[id]
		jobs.append(func(): _gen_object(oid, boxes))

# ------------------------------------------------------------------ ground
static func _ground_color(g: int, u: int, v: int, s: int) -> Color:
	var n: float = Rng.f2(u, v, s)
	var n2: float = Rng.f2(u / 3, v / 3, s + 5)
	match g:
		Defs.G_GRASS:
			var c := Color(0.30, 0.42, 0.23)
			var k: float = 0.86 + n * 0.22 + n2 * 0.1
			if n > 0.93: k *= 1.25
			elif n < 0.06: k *= 0.75
			return Color(c.r * k, c.g * k, c.b * k)
		Defs.G_GRASS_DARK:
			var c2 := Color(0.25, 0.36, 0.20)
			var k2: float = 0.84 + n * 0.22 + n2 * 0.12
			if n > 0.94: k2 *= 1.2
			return Color(c2.r * k2, c2.g * k2, c2.b * k2)
		Defs.G_FOREST:
			var c3 := Color(0.24, 0.30, 0.17)
			var k3: float = 0.82 + n * 0.24 + n2 * 0.12
			if n > 0.9:
				return Color(0.42 * k3, 0.33 * k3, 0.18 * k3)
			return Color(c3.r * k3, c3.g * k3, c3.b * k3)
		Defs.G_DIRT:
			var k4: float = 0.86 + n * 0.2 + n2 * 0.1
			if n > 0.96: k4 *= 0.7
			return Color(0.43 * k4, 0.35 * k4, 0.25 * k4)
		Defs.G_SAND:
			var k5: float = 0.9 + n * 0.14
			return Color(0.72 * k5, 0.66 * k5, 0.48 * k5)
		Defs.G_WATER, Defs.G_DEEP_WATER:
			var deep: float = 0.78 if g == Defs.G_DEEP_WATER else 1.0
			var k6: float = (0.9 + n2 * 0.12) * deep
			var wave: int = posmod(u - v + int(Rng.f2(v / 4, 0, s) * 9.0), 13)
			if wave == 0 and posmod(u + v, 7) < 4:
				k6 *= 1.3
			return Color(0.2 * k6, 0.37 * k6, 0.5 * k6)
		Defs.G_ASPHALT, Defs.G_ASPHALT_LX, Defs.G_ASPHALT_LY, Defs.G_PARKING:
			var k7: float = 0.88 + n * 0.2
			if n > 0.975: k7 *= 1.3
			var col := Color(0.235 * k7, 0.24 * k7, 0.25 * k7)
			if g == Defs.G_ASPHALT_LX and v >= 15 and v <= 16 and posmod(u, 32) >= 6 and posmod(u, 32) < 26:
				return Color(0.78 * k7, 0.66 * k7, 0.25 * k7)
			if g == Defs.G_ASPHALT_LY and u >= 15 and u <= 16 and posmod(v, 32) >= 6 and posmod(v, 32) < 26:
				return Color(0.78 * k7, 0.66 * k7, 0.25 * k7)
			if g == Defs.G_PARKING and u <= 1:
				return Color(0.75 * k7, 0.75 * k7, 0.72 * k7)
			return col
		Defs.G_SIDEWALK:
			var k8: float = 0.92 + n * 0.1
			if u == 0 or v == 0: k8 *= 0.8
			return Color(0.56 * k8, 0.56 * k8, 0.53 * k8)
		Defs.G_GRAVEL:
			var k9: float = 0.75 + n * 0.45
			return Color(0.47 * k9, 0.45 * k9, 0.41 * k9)
		Defs.G_CONCRETE:
			var k10: float = 0.93 + n * 0.08
			if u == 0 or v == 0 or u == 16 or v == 16: k10 *= 0.88
			return Color(0.5 * k10, 0.5 * k10, 0.49 * k10)
		Defs.G_WOOD, Defs.G_WOOD_DARK, Defs.G_PLANK:
			var base := Color(0.56, 0.42, 0.27)
			if g == Defs.G_WOOD_DARK: base = Color(0.40, 0.29, 0.19)
			elif g == Defs.G_PLANK: base = Color(0.62, 0.50, 0.32)
			var row: int = v / 8
			var k11: float = 0.9 + Rng.f2(row, u / 16 + row * 3, s) * 0.14 + n * 0.06
			if posmod(v, 8) == 0 or posmod(u + row * 11, 32) == 0: k11 *= 0.72
			return Color(base.r * k11, base.g * k11, base.b * k11)
		Defs.G_TILE, Defs.G_TILE_BLUE:
			var chk: bool = ((u / 8) + (v / 8)) % 2 == 0
			var k12: float = 0.96 + n * 0.04
			if posmod(u, 8) == 0 or posmod(v, 8) == 0: k12 *= 0.84
			if g == Defs.G_TILE:
				var b1: float = 0.76 if chk else 0.66
				return Color(b1 * k12, b1 * k12, b1 * 0.97 * k12)
			var bl := Color(0.52, 0.62, 0.68) if chk else Color(0.62, 0.68, 0.72)
			return Color(bl.r * k12, bl.g * k12, bl.b * k12)
		Defs.G_CARPET_RED, Defs.G_CARPET_BLUE, Defs.G_CARPET_BEIGE:
			var cb := Color(0.5, 0.24, 0.22)
			if g == Defs.G_CARPET_BLUE: cb = Color(0.24, 0.31, 0.42)
			elif g == Defs.G_CARPET_BEIGE: cb = Color(0.58, 0.52, 0.40)
			var k13: float = 0.88 + n * 0.18
			if (u + v) % 2 == 0: k13 *= 0.95
			return Color(cb.r * k13, cb.g * k13, cb.b * k13)
		Defs.G_LINO:
			var k14: float = 0.95 + n * 0.06
			if posmod(u, 16) == 0 or posmod(v, 16) == 0: k14 *= 0.86
			return Color(0.6 * k14, 0.63 * k14, 0.56 * k14)
		Defs.G_SOIL:
			var k15: float = 0.72 + n * 0.2 + sin(float(v) / 32.0 * TAU * 4.0) * 0.14
			return Color(0.34 * k15, 0.26 * k15, 0.18 * k15)
	return Color(1, 0, 1)

static func _gen_ground(g: int) -> void:
	var natural: bool = Defs.GROUND_PRIORITY[g] > 0
	var variants: int = 4 if (g == Defs.G_GRASS or g == Defs.G_GRASS_DARK or g == Defs.G_FOREST) else (2 if natural or g == Defs.G_WATER or g == Defs.G_ASPHALT else 1)
	for vi in range(variants):
		var s: int = g * 31 + vi * 7
		if natural:
			var p := Painter.new(76, 44)
			var ox := 38.0
			var oy := 6.0
			for yy in range(44):
				for xx in range(76):
					var a: float = (xx + 0.5 - ox) / 32.0
					var b: float = (yy + 0.5 - oy) / 16.0
					var wx: float = (a + b) * 0.5
					var wy: float = (b - a) * 0.5
					var m: float = 0.02 + Rng.f2(xx / 2, yy / 2, s + 3) * 0.13
					if wx >= -m and wx < 1.0 + m and wy >= -m and wy < 1.0 + m:
						p.img.set_pixel(xx, yy, _ground_color(g, int(floor(wx * 32.0)) + 64, int(floor(wy * 32.0)) + 64, s))
			Art.ground[g].append(Art.world.add(p.img, ox, oy))
		else:
			# slightly inflated diamond: neighbours overlap by ~1px so no seams show at fractional zoom
			var p2 := Painter.new(68, 36)
			for yy in range(36):
				for xx in range(68):
					var a2: float = (xx + 0.5 - 34.0) / 32.0
					var b2: float = (yy + 0.5 - 2.0) / 16.0
					var wx2: float = (a2 + b2) * 0.5
					var wy2: float = (b2 - a2) * 0.5
					if wx2 >= -0.036 and wx2 < 1.036 and wy2 >= -0.036 and wy2 < 1.036:
						p2.img.set_pixel(xx, yy, _ground_color(g, int(floor(clampf(wx2, 0.0, 0.999) * 32.0)), int(floor(clampf(wy2, 0.0, 0.999) * 32.0)), s))
			Art.ground[g].append(Art.world.add(p2.img, 34, 2))

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
	# roof tile texture (flat diamond, tinted + skewed at draw time)
	var p := Painter.new(64, 32)
	for yy in range(32):
		for xx in range(64):
			var a: float = (xx + 0.5 - 32.0) / 32.0
			var b: float = (yy + 0.5) / 16.0
			var wx: float = (a + b) * 0.5
			var wy: float = (b - a) * 0.5
			if wx >= 0.0 and wx < 1.0 and wy >= 0.0 and wy < 1.0:
				p.img.set_pixel(xx, yy, Painter.shade(Painter.M_SHINGLE, Color.WHITE, int(wx * 32.0), int(wy * 32.0), 1.0))
	Art.misc["roof"] = Art.world.add(p.img, 32, 0, "", false)
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
	var hnd: int = Art.world.add(p.img, ax, ay)
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

static func _gen_crops() -> void:
	var ids := [Defs.O_CROP_POTATO, Defs.O_CROP_CABBAGE, Defs.O_CROP_CARROT, Defs.O_CROP_TOMATO]
	for ci in range(4):
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
					3:
						p.line(sx, sy, sx, sy - size * 2.0, Color(0.36, 0.3, 0.2))
						p.ball(sx, sy - size * 1.2, size * 0.8, size, green, 220 + si, 0.3)
						if stage == 3:
							p.put(int(sx) - 2, int(sy - size), Color(0.85, 0.15, 0.12))
							p.put(int(sx) + 2, int(sy - size * 1.5), Color(0.85, 0.15, 0.12))
							p.put(int(sx) + 1, int(sy - size * 0.7), Color(0.85, 0.15, 0.12))
			var hnd: int = Art.world.add(p.img, ax, ay)
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
				var hnd: int = Art.world.add(p.img, 2 + 32, 2 + maxz)
				var part: int = j * fs.x + i
				if rots == 1:
					for rr in range(4):
						Art.obj_spr[Defs.ocell(id, rr, part)] = hnd
				else:
					Art.obj_spr[Defs.ocell(id, r, part)] = hnd
