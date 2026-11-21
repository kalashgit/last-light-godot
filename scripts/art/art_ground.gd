class_name ArtGround
extends RefCounted
## Ground textures, painted texel by texel (64 across a tile) from tileable noise, so a tile meets
## the next without a seam: grass with blades catching the light, dry patches and the odd flower;
## leaf litter on the forest floor; dirt with pebbles; rippled sand; water with glints; asphalt with
## its aggregate, worn patches and hairline cracks; slabbed sidewalks with weeds in the joints;
## gravel stone by stone; concrete with expansion joints; plank floors with grain and staggered ends;
## tiled floors with grout and a sheen; carpet; lino; tilled soil in furrows.
## Natural ground spills a ragged, feathered margin over its neighbours.
## Decals (cracks, stains, tar patches, manholes, litter, leaves, weeds, stones, tufts, flowers) are
## scattered over the ground at draw time, so no stretch of ground repeats.

const RES := 64            # texels across a tile
const LIFT := 1.05         # painted a touch light: the broad tint over the land only darkens (WorldView.macro_tint)
const DECALS := {"crack": 4, "stain": 3, "patch": 2, "manhole": 1, "litter": 4, "leaves": 3, "weeds": 3, "rocks": 2, "tufts": 4, "flowers": 2}

static var _nz: Dictionary = {}

static func queue_jobs(jobs: Array[Callable]) -> void:
	for g in range(Defs.G_COUNT):
		if g == Defs.G_VOID:
			continue
		var gg: int = g
		jobs.append(func(): _gen_ground(gg))
	jobs.append(_gen_decals)

## let go of the noise images once the art is painted (a static holding images until the engine
## shuts down is freed too late, after the resources it points into)
static func release() -> void:
	_nz.clear()

## tileable noise (0..1) over a tile, made once per seed
static func noise(seed_v: int, freq: float, oct: int) -> Image:
	var key := "%d/%.4f/%d" % [seed_v, freq, oct]
	if _nz.has(key):
		return _nz[key]
	var fn := FastNoiseLite.new()
	fn.seed = seed_v
	fn.noise_type = FastNoiseLite.TYPE_SIMPLEX_SMOOTH
	fn.frequency = freq
	fn.fractal_type = FastNoiseLite.FRACTAL_FBM
	fn.fractal_octaves = oct
	var im: Image = fn.get_seamless_image(RES, RES, false, false, 0.15, true)
	_nz[key] = im
	return im

static func _k(c: Color, k: float) -> Color:
	return Color(c.r * k, c.g * k, c.b * k, c.a)

## a stone (or clod) in this texel, if any: x = its shading (lit toward the upper left of the screen,
## darker at its rim), y = a hash to colour it by; x < 0 when there is none
static func stone(u: float, v: float, cells: int, s: int, dens: float, r0: float, r1: float) -> Vector2:
	var cu: float = u * cells
	var cv: float = v * cells
	var bi: int = floori(cu)
	var bj: int = floori(cv)
	var best := Vector2(-1.0, 0.0)
	var bestd := 9.0
	for oj in range(-1, 2):
		for oi in range(-1, 2):
			var ci: int = posmod(bi + oi, cells)
			var cj: int = posmod(bj + oj, cells)
			if Rng.f2(ci, cj, s) > dens:
				continue
			var px: float = bi + oi + 0.2 + Rng.f2(ci, cj, s + 1) * 0.6
			var py: float = bj + oj + 0.2 + Rng.f2(ci, cj, s + 2) * 0.6
			var r: float = r0 + Rng.f2(ci, cj, s + 3) * (r1 - r0)
			var dx: float = (cu - px) / r
			var dy: float = (cv - py) / (r * 0.85)
			var d: float = dx * dx + dy * dy
			if d < 1.0 and d < bestd:
				bestd = d
				best = Vector2(1.08 - dx * 0.28 - dy * 0.12 - d * d * 0.3, Rng.f2(ci, cj, s + 4))
	return best

## the colour of ground g at (u, v) in tiles (periodic every tile)
static func texel(g: int, u: float, v: float, s: int, n1: Image, n2: Image, n3: Image) -> Color:
	var ix: int = posmod(floori(u * RES), RES)
	var iy: int = posmod(floori(v * RES), RES)
	var lo: float = n1.get_pixel(ix, iy).r       # broad mottling
	var hi: float = n2.get_pixel(ix, iy).r       # fine detail
	var md: float = n3.get_pixel(ix, iy).r       # patches (dry, damp, stained, old)
	var h: float = Rng.f2(ix, iy, s)             # each texel its own
	var fu: float = fposmod(u, 1.0)
	var fv: float = fposmod(v, 1.0)
	match g:
		Defs.G_GRASS, Defs.G_GRASS_DARK:
			var dark: bool = g == Defs.G_GRASS_DARK
			var c: Color = Color(0.25, 0.38, 0.19).lerp(Color(0.37, 0.48, 0.23), lo)
			if dark:
				c = Color(0.2, 0.31, 0.16).lerp(Color(0.29, 0.39, 0.2), lo)
			c = c.lerp(Color(0.5, 0.48, 0.29), smoothstep(0.6, 0.82, md) * (0.3 if dark else 0.55))
			c = c.lerp(Color(0.21, 0.33, 0.17), smoothstep(0.55, 0.85, hi) * 0.35)
			# blades: short strokes upright on the screen, the tips catching the light
			var bl: float = Rng.f2(ix - iy, (ix + iy) / 10, s + 1)
			if bl > 0.86:
				c = Color(c.r * 1.22 + 0.02, c.g * 1.18 + 0.02, c.b * 1.05)
			elif bl < 0.13:
				c = _k(c, 0.76)
			c = _k(c, 0.92 + h * 0.16)
			if not dark and Rng.f2(ix / 2, iy / 2, s + 7) > 0.9975:
				return [Color(0.92, 0.9, 0.82), Color(0.95, 0.82, 0.25), Color(0.7, 0.55, 0.85)][Rng.i2(ix / 2, iy / 2, s + 8, 3)]
			if h < 0.01:
				return Color(0.36, 0.29, 0.2)
			return c
		Defs.G_FOREST:
			var cf: Color = Color(0.21, 0.24, 0.13).lerp(Color(0.33, 0.3, 0.18), lo)
			# leaf litter: a leaf in most small cells, each turned its own way
			var cu: float = u * 14.0
			var cv: float = v * 14.0
			var ci: int = posmod(floori(cu), 14)
			var cj: int = posmod(floori(cv), 14)
			if Rng.f2(ci, cj, s + 3) > 0.3:
				var lx: float = fposmod(cu, 1.0) - (0.3 + Rng.f2(ci, cj, s + 4) * 0.4)
				var ly: float = fposmod(cv, 1.0) - (0.3 + Rng.f2(ci, cj, s + 5) * 0.4)
				var ang: float = Rng.f2(ci, cj, s + 6) * PI
				var ru: float = lx * cos(ang) + ly * sin(ang)
				var rv: float = -lx * sin(ang) + ly * cos(ang)
				if ru * ru / 0.17 + rv * rv / 0.05 < 1.0:
					var lc: Color = [Color(0.55, 0.36, 0.16), Color(0.45, 0.3, 0.14), Color(0.64, 0.5, 0.2), Color(0.36, 0.26, 0.13), Color(0.5, 0.42, 0.18)][Rng.i2(ci, cj, s + 9, 5)]
					return _k(lc, 0.92 + rv * 0.5 + h * 0.12)
			if hi > 0.68:
				cf = cf.lerp(Color(0.25, 0.36, 0.16), (hi - 0.68) * 2.2)
			return _k(cf, 0.88 + h * 0.2)
		Defs.G_DIRT:
			var cd: Color = Color(0.36, 0.28, 0.19).lerp(Color(0.5, 0.41, 0.29), lo)
			cd = cd.lerp(Color(0.29, 0.22, 0.15), smoothstep(0.62, 0.85, md) * 0.6)
			var st: Vector2 = stone(u, v, 9, s + 20, 0.32, 0.18, 0.32)
			if st.x >= 0.0:
				return _k(Color(0.52, 0.47, 0.4).lerp(Color(0.62, 0.56, 0.47), st.y), st.x)
			return _k(cd, 0.9 + h * 0.18 + (hi - 0.5) * 0.12)
		Defs.G_SAND:
			var cs: Color = Color(0.69, 0.63, 0.46).lerp(Color(0.78, 0.72, 0.55), lo)
			var rip: float = sin((fu * 2.0 + fv * 5.0 + lo * 1.5) * TAU)
			return _k(cs, 1.0 + rip * 0.045 + (h - 0.5) * 0.09)
		Defs.G_WATER, Defs.G_DEEP_WATER:
			var cw: Color = Color(0.16, 0.31, 0.39).lerp(Color(0.22, 0.4, 0.47), lo)
			if g == Defs.G_DEEP_WATER:
				cw = _k(cw, 0.72)
			# glints along the screen's horizontal, broken up by the swell
			var wv: float = fposmod((fu + fv) * 6.0 + hi * 1.6, 1.0)
			if lo > 0.42 and wv < 0.06:
				return cw.lerp(Color(0.62, 0.76, 0.82), 0.5 * (lo - 0.3))
			if lo > 0.42 and wv < 0.13:
				return _k(cw, 0.9)
			return _k(cw, 0.97 + h * 0.05)
		Defs.G_ASPHALT, Defs.G_ASPHALT_LX, Defs.G_ASPHALT_LY, Defs.G_PARKING:
			var ca: Color = Color(0.2, 0.205, 0.215).lerp(Color(0.275, 0.28, 0.29), lo)
			ca = ca.lerp(Color(0.31, 0.31, 0.3), smoothstep(0.66, 0.9, md) * 0.5)          # sun-bleached, worn
			if h > 0.93:
				ca = _k(ca, 1.38)
			elif h < 0.07:
				ca = _k(ca, 0.7)
			else:
				ca = _k(ca, 0.95 + h * 0.1)
			if absf(hi - 0.5) < 0.011 and md > 0.52:
				ca = _k(ca, 0.55)                                                    # a hairline crack
			var line := Color(0.0, 0.0, 0.0, 0.0)
			if g == Defs.G_ASPHALT_LX and fv >= 15.0 / 32.0 and fv < 17.0 / 32.0 and fu >= 6.0 / 32.0 and fu < 26.0 / 32.0:
				line = Color(0.8, 0.67, 0.24)
			elif g == Defs.G_ASPHALT_LY and fu >= 15.0 / 32.0 and fu < 17.0 / 32.0 and fv >= 6.0 / 32.0 and fv < 26.0 / 32.0:
				line = Color(0.8, 0.67, 0.24)
			elif g == Defs.G_PARKING and fu < 2.2 / 32.0:
				line = Color(0.8, 0.8, 0.76)
			if line.a > 0.0:
				# paint wears off where the traffic ran
				var wear: float = clampf((0.55 - hi) * 2.5 + h * 0.4, 0.0, 0.75)
				return line.lerp(ca, wear * 0.7)
			return ca
		Defs.G_SIDEWALK:
			var cw2: Color = Color(0.53, 0.53, 0.5).lerp(Color(0.61, 0.61, 0.58), lo)
			cw2 = cw2.lerp(Color(0.44, 0.44, 0.42), smoothstep(0.68, 0.9, md) * 0.5)
			var jv: float = fposmod(fv * 2.0, 1.0)
			if fu < 0.03 or jv < 0.06:
				if Rng.f2(ix / 3, iy / 3, s + 9) > 0.82:
					return Color(0.3, 0.42, 0.2).lerp(Color(0.4, 0.5, 0.25), h)       # weeds in the joint
				return _k(cw2, 0.68 + h * 0.1)
			if absf(hi - 0.5) < 0.008 and md > 0.6:
				return _k(cw2, 0.6)
			return _k(cw2, 0.95 + h * 0.08)
		Defs.G_GRAVEL:
			var sg: Vector2 = stone(u, v, 16, s + 30, 0.97, 0.38, 0.62)
			if sg.x >= 0.0:
				var gc: Color = Color(0.5, 0.48, 0.44).lerp(Color(0.64, 0.6, 0.54), sg.y)
				if sg.y > 0.85:
					gc = Color(0.55, 0.47, 0.38)
				return _k(gc, sg.x * (0.95 + h * 0.08))
			return _k(Color(0.3, 0.29, 0.27), 0.85 + h * 0.3)
		Defs.G_CONCRETE:
			var cc: Color = Color(0.49, 0.49, 0.48).lerp(Color(0.56, 0.56, 0.54), lo)
			cc = cc.lerp(Color(0.42, 0.42, 0.4), smoothstep(0.7, 0.92, md) * 0.45)
			if fu < 0.015 or fv < 0.015:
				return _k(cc, 0.78)
			if absf(hi - 0.5) < 0.006 and md > 0.66:
				return _k(cc, 0.65)
			return _k(cc, 0.96 + h * 0.06)
		Defs.G_WOOD, Defs.G_WOOD_DARK, Defs.G_PLANK:
			var bw := Color(0.56, 0.42, 0.27)
			if g == Defs.G_WOOD_DARK:
				bw = Color(0.4, 0.29, 0.19)
			elif g == Defs.G_PLANK:
				bw = Color(0.55, 0.48, 0.36)
			var rows: int = 4 if g == Defs.G_PLANK else 6
			var rr: float = v * rows
			var r: int = posmod(floori(rr), rows)
			var off: float = Rng.f2(r, 3, s + 11)
			var pu: float = fposmod(u + off, 1.0)
			# (one board end per row per tile, so the texture repeats every tile: shades go by row)
			var kw: float = 0.86 + Rng.f2(r, 0, s + 12) * 0.22
			var fr: float = fposmod(rr, 1.0)
			# grain: fine lines along the board, gently wavering
			kw *= 1.0 + sin((fr * 7.0 + sin(fu * TAU * 2.0 + r) * 0.5 + lo * 2.0) * TAU) * 0.045
			# a knot or two
			var kx: float = Rng.f2(r, 1, s + 13)
			if kx < 0.35 and absf(pu - (0.2 + kx * 1.8)) < 0.025 and absf(fr - 0.5) < 0.22:
				kw *= 0.72
			if fr < 0.09:
				kw *= 0.6                                    # the gap between boards
			elif pu < 0.012:
				kw *= 0.58                                   # a board's end
			elif g == Defs.G_PLANK and pu < 0.06 and absf(fr - 0.3) < 0.07:
				return Color(0.25, 0.24, 0.22)               # nail heads
			return _k(bw, kw * (0.97 + h * 0.06))
		Defs.G_TILE, Defs.G_TILE_BLUE:
			var tu: float = fu * 4.0
			var tv: float = fv * 4.0
			var ti: int = floori(tu)
			var tj: int = floori(tv)
			var gu: float = fposmod(tu, 1.0)
			var gv: float = fposmod(tv, 1.0)
			if gu < 0.07 or gv < 0.07:
				return _k(Color(0.46, 0.45, 0.42), 0.9 + h * 0.15)
			var chk: bool = (ti + tj) % 2 == 0
			var ct: Color = (Color(0.8, 0.79, 0.74) if chk else Color(0.64, 0.64, 0.62)) if g == Defs.G_TILE else (Color(0.48, 0.6, 0.68) if chk else Color(0.82, 0.84, 0.84))
			var kt: float = 0.95 + Rng.f2(ti, tj, s + 20) * 0.07
			kt *= 1.0 + (0.5 - gu) * 0.07 + (0.5 - gv) * 0.03           # a sheen toward the light
			if Rng.f2(ti * 7 + floori(gu * 5.0), tj * 7 + floori(gv * 5.0), s + 21) > 0.995:
				kt *= 0.8                                                   # a chip
			return _k(ct, kt * (0.985 + h * 0.03))
		Defs.G_CARPET_RED, Defs.G_CARPET_BLUE, Defs.G_CARPET_BEIGE:
			var cb := Color(0.48, 0.22, 0.2)
			if g == Defs.G_CARPET_BLUE:
				cb = Color(0.23, 0.3, 0.41)
			elif g == Defs.G_CARPET_BEIGE:
				cb = Color(0.58, 0.52, 0.4)
			var fib: float = Rng.f2(ix, iy / 2, s + 14)
			return _k(cb, 0.84 + lo * 0.14 + (fib - 0.5) * 0.16 + (h - 0.5) * 0.06 - smoothstep(0.7, 0.95, md) * 0.08)
		Defs.G_LINO:
			var cl: Color = Color(0.61, 0.63, 0.57).lerp(Color(0.67, 0.68, 0.62), lo)
			if h > 0.955:
				return _k(cl, 0.78)
			if h < 0.03:
				return _k(cl, 1.1)
			if fposmod(fu * 2.0, 1.0) < 0.02 or fposmod(fv * 2.0, 1.0) < 0.02:
				return _k(cl, 0.9)
			return _k(cl, 0.98 + (hi - 0.5) * 0.08 + smoothstep(0.75, 0.95, md) * 0.06)
		Defs.G_SOIL:
			var cso: Color = Color(0.29, 0.21, 0.14).lerp(Color(0.38, 0.28, 0.19), lo)
			var fw: float = fposmod(fv * 5.0, 1.0)
			var ks: float = 0.78 + 0.3 * (0.5 + 0.5 * sin(fw * TAU)) + cos(fw * TAU) * 0.08
			var cl2: Vector2 = stone(u, v, 18, s + 40, 0.45, 0.25, 0.45)
			if cl2.x >= 0.0:
				ks *= 0.85 + (cl2.x - 0.8) * 0.6
			return _k(cso, ks * (0.92 + h * 0.14))
	return Color(1, 0, 1)

static func _gen_ground(g: int) -> void:
	Art.ground[g] = []
	var natural: bool = Defs.GROUND_PRIORITY[g] > 0
	var variants: int = 2
	match g:
		Defs.G_GRASS, Defs.G_GRASS_DARK, Defs.G_FOREST: variants = 4
		Defs.G_DIRT, Defs.G_ASPHALT, Defs.G_WOOD, Defs.G_WOOD_DARK: variants = 3
		Defs.G_ASPHALT_LX, Defs.G_ASPHALT_LY, Defs.G_LINO, Defs.G_TILE, Defs.G_TILE_BLUE, Defs.G_CARPET_RED, Defs.G_CARPET_BLUE, Defs.G_CARPET_BEIGE: variants = 1
	for vi in range(variants):
		var s: int = g * 31 + vi * 7
		# the broad and fine noise are the same for every variant of a ground (so variants meet
		# without a seam); only the patches and the texel-level detail differ
		var n1: Image = noise(g * 101, 0.035, 3)
		var n2: Image = noise(g * 101 + 1, 0.11, 2)
		var n3: Image = noise(g * 101 + 2 + vi * 13, 0.03, 2)
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
					var out: float = maxf(maxf(-wx, wx - 1.0), maxf(-wy, wy - 1.0))
					if out > 0.2:
						continue
					var al := 1.0
					if out > 0.0:
						# a ragged, feathered margin over the neighbours
						var m: float = 0.03 + n3.get_pixel(posmod(floori(wx * RES), RES), posmod(floori(wy * RES), RES)).r * 0.1 + Rng.f2(xx / 2, yy / 2, s + 3) * 0.06
						al = clampf((m - out) / 0.035, 0.0, 1.0)
						if al <= 0.0:
							continue
					var col: Color = _k(texel(g, wx, wy, s, n1, n2, n3), LIFT)
					col.a = al
					p.img.set_pixel(xx, yy, col)
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
						p2.img.set_pixel(xx, yy, _k(texel(g, clampf(wx2, 0.0, 0.999), clampf(wy2, 0.0, 0.999), s, n1, n2, n3), LIFT))
			Art.ground[g].append(Art.world.add(p2.img, 34, 2))

# ------------------------------------------------------------------ decals
## a decal sprite: painted onto a tile-sized canvas (anchor at the tile's top corner), alpha where empty
const DY := 8      # room above the tile for things that stand up (weeds, tufts)

static func _decal_canvas() -> Painter:
	return Painter.new(64, 32 + DY)

static func _wpx(_p: Painter, wx: float, wy: float) -> Vector2:
	return Vector2(32.0 + (wx - wy) * 32.0, (wx + wy) * 16.0 + DY)

static func _blend(p: Painter, x: int, y: int, c: Color) -> void:
	if x < 0 or y < 0 or x >= p.img.get_width() or y >= p.img.get_height():
		return
	var o: Color = p.img.get_pixel(x, y)
	if o.a <= 0.0:
		p.img.set_pixel(x, y, c)
		return
	var a: float = c.a + o.a * (1.0 - c.a)
	p.img.set_pixel(x, y, Color((c.r * c.a + o.r * o.a * (1.0 - c.a)) / a, (c.g * c.a + o.g * o.a * (1.0 - c.a)) / a, (c.b * c.a + o.b * o.a * (1.0 - c.a)) / a, a))

static func _gen_decals() -> void:
	Art.decals.clear()
	for nm in DECALS.keys():
		var arr: Array = []
		for k in range(int(DECALS[nm])):
			var p: Painter = _decal_canvas()
			_paint_decal(p, nm, k)
			arr.append(Art.world.add(p.img, 32, DY))
		Art.decals[nm] = arr

static func _paint_decal(p: Painter, nm: String, k: int) -> void:
	var s: int = 7000 + k * 37 + nm.length() * 101
	match nm:
		"crack":
			# a meandering crack with a branch or two
			for br in range(1 + k % 2 + 1):
				var x: float = 0.15 + Rng.f2(k, br, s) * 0.35
				var y: float = 0.2 + Rng.f2(k, br, s + 1) * 0.5
				var ang: float = Rng.f2(k, br, s + 2) * TAU
				var n: int = 14 + int(Rng.f2(k, br, s + 3) * 18.0)
				for i in range(n):
					ang += (Rng.f2(i, br + k * 5, s + 4) - 0.5) * 1.1
					x += cos(ang) * 0.025
					y += sin(ang) * 0.025
					if x < 0.02 or x > 0.98 or y < 0.02 or y > 0.98:
						break
					var q: Vector2 = _wpx(p, x, y)
					_blend(p, int(q.x), int(q.y), Color(0.06, 0.06, 0.06, 0.42 - 0.012 * absf(float(i) - n * 0.5)))
		"stain":
			var cx: float = 0.35 + Rng.f2(k, 0, s) * 0.3
			var cy: float = 0.35 + Rng.f2(k, 1, s) * 0.3
			var rad: float = 0.16 + Rng.f2(k, 2, s) * 0.14
			var n3: Image = noise(s, 0.09, 2)
			for yy in range(32):
				for xx in range(64):
					var a: float = (xx + 0.5 - 32.0) / 32.0
					var b: float = (yy + 0.5) / 16.0
					var wx: float = (a + b) * 0.5
					var wy: float = (b - a) * 0.5
					var d: float = Vector2(wx - cx, wy - cy).length() / rad + (n3.get_pixel(posmod(int(wx * 64.0), 64), posmod(int(wy * 64.0), 64)).r - 0.5) * 0.9
					if d < 1.0:
						var oil: bool = k == 2
						_blend(p, xx, yy + DY, Color(0.05, 0.05, 0.06, (0.34 if oil else 0.22) * clampf((1.0 - d) * 3.0, 0.0, 1.0)))
		"patch":
			# a square of newer, darker asphalt
			var u0: float = 0.15 + Rng.f2(k, 0, s) * 0.2
			var v0: float = 0.15 + Rng.f2(k, 1, s) * 0.2
			var u1: float = u0 + 0.3 + Rng.f2(k, 2, s) * 0.25
			var v1: float = v0 + 0.25 + Rng.f2(k, 3, s) * 0.25
			for yy in range(32):
				for xx in range(64):
					var a2: float = (xx + 0.5 - 32.0) / 32.0
					var b2: float = (yy + 0.5) / 16.0
					var wx2: float = (a2 + b2) * 0.5
					var wy2: float = (b2 - a2) * 0.5
					if wx2 >= u0 and wx2 <= u1 and wy2 >= v0 and wy2 <= v1:
						var edge: bool = wx2 - u0 < 0.02 or u1 - wx2 < 0.02 or wy2 - v0 < 0.02 or v1 - wy2 < 0.02
						var hh: float = Rng.f2(xx, yy, s + 5)
						_blend(p, xx, yy + DY, Color(0.17 + hh * 0.03, 0.175 + hh * 0.03, 0.18 + hh * 0.03, 0.55 if not edge else 0.3))
		"manhole":
			for yy in range(32):
				for xx in range(64):
					var dx: float = (xx + 0.5 - 32.0) / 15.0
					var dy: float = (yy + 0.5 - 16.0) / 7.5
					var d2: float = dx * dx + dy * dy
					if d2 < 1.0:
						var ring: bool = d2 > 0.78
						var grid: bool = (posmod(xx + yy * 2, 6) == 0 or posmod(xx - yy * 2, 6) == 0) and d2 < 0.7
						var cm := Color(0.24, 0.23, 0.22)
						if ring: cm = Color(0.34, 0.33, 0.31)
						elif grid: cm = Color(0.17, 0.16, 0.16)
						_blend(p, xx, yy + DY, Color(cm.r, cm.g, cm.b, 1.0))
					elif d2 < 1.15:
						_blend(p, xx, yy + DY, Color(0.1, 0.1, 0.1, 0.4))
		"litter":
			for i in range(2 + k % 3):
				var x2: float = 0.2 + Rng.f2(k, i, s) * 0.6
				var y2: float = 0.2 + Rng.f2(k, i, s + 1) * 0.6
				var q2: Vector2 = _wpx(p, x2, y2)
				match (k + i) % 4:
					0:      # a sheet of paper, curled
						for yy in range(4):
							for xx in range(6):
								_blend(p, int(q2.x) + xx - yy, int(q2.y) + yy, Color(0.86, 0.85, 0.8, 0.95) if yy > 0 else Color(0.95, 0.95, 0.92, 0.95))
					1:      # a crushed can
						for xx in range(4):
							_blend(p, int(q2.x) + xx, int(q2.y), Color(0.7, 0.2, 0.18, 1.0))
							_blend(p, int(q2.x) + xx, int(q2.y) + 1, Color(0.55, 0.56, 0.58, 1.0))
					2:      # a bottle
						for xx in range(5):
							_blend(p, int(q2.x) + xx, int(q2.y), Color(0.2, 0.42, 0.22, 0.9) if xx < 4 else Color(0.6, 0.7, 0.6, 0.9))
						_blend(p, int(q2.x) + 1, int(q2.y) - 1, Color(0.6, 0.8, 0.6, 0.6))
					3:      # a wrapper
						for xx in range(3):
							_blend(p, int(q2.x) + xx, int(q2.y), Color(0.85, 0.72, 0.2, 0.95))
							_blend(p, int(q2.x) + xx, int(q2.y) + 1, Color(0.3, 0.35, 0.7, 0.95))
		"leaves":
			for i in range(10 + k * 4):
				var x3: float = 0.08 + Rng.f2(k, i, s) * 0.84
				var y3: float = 0.08 + Rng.f2(k, i, s + 1) * 0.84
				var q3: Vector2 = _wpx(p, x3, y3)
				var lc: Color = [Color(0.6, 0.38, 0.15), Color(0.7, 0.55, 0.2), Color(0.45, 0.28, 0.13), Color(0.55, 0.22, 0.12)][Rng.i2(k, i, s + 2, 4)]
				_blend(p, int(q3.x), int(q3.y), lc)
				_blend(p, int(q3.x) + 1, int(q3.y), _k(lc, 0.85))
				if Rng.f2(k, i, s + 3) > 0.5:
					_blend(p, int(q3.x) - 1, int(q3.y), _k(lc, 1.1))
		"weeds", "tufts":
			var weeds: bool = nm == "weeds"
			for t in range(2 + k % 3):
				var x4: float = 0.2 + Rng.f2(k, t, s) * 0.6
				var y4: float = 0.2 + Rng.f2(k, t, s + 1) * 0.6
				var q4: Vector2 = _wpx(p, x4, y4)
				var base := Color(0.3, 0.42, 0.2) if weeds else Color(0.3, 0.43, 0.21)
				for bl in range(7 + k * 2):
					var bx: float = q4.x + (Rng.f2(t, bl, s + 2) - 0.5) * 7.0
					var tall: int = 3 + int(Rng.f2(t, bl, s + 3) * (5.0 if weeds else 4.0))
					var lean: float = (Rng.f2(t, bl, s + 4) - 0.5) * 0.6
					for hgt in range(tall):
						var cg: Color = base.lerp(Color(0.5, 0.6, 0.3), float(hgt) / tall)
						_blend(p, int(bx + lean * hgt), int(q4.y) - hgt, cg)
				# a little shadow at the root
				for xx in range(-3, 4):
					_blend(p, int(q4.x) + xx, int(q4.y) + 1, Color(0.0, 0.0, 0.0, 0.18))
		"rocks":
			for i in range(2 + k * 2):
				var x5: float = 0.25 + Rng.f2(k, i, s) * 0.5
				var y5: float = 0.25 + Rng.f2(k, i, s + 1) * 0.5
				var q5: Vector2 = _wpx(p, x5, y5)
				var rr: float = 1.5 + Rng.f2(k, i, s + 2) * 2.5
				var rc: Color = Color(0.5, 0.48, 0.44).lerp(Color(0.62, 0.58, 0.52), Rng.f2(k, i, s + 3))
				for yy in range(-int(rr) - 1, int(rr) + 2):
					for xx in range(-int(rr * 1.4) - 1, int(rr * 1.4) + 2):
						var dd: float = pow(xx / (rr * 1.4), 2.0) + pow(yy / rr, 2.0)
						if dd < 1.0:
							_blend(p, int(q5.x) + xx, int(q5.y) + yy, _k(rc, 1.15 - xx * 0.05 - yy * 0.08 - dd * 0.2))
				for xx in range(-int(rr * 1.4), int(rr * 1.4) + 2):
					_blend(p, int(q5.x) + xx + 1, int(q5.y) + int(rr) + 1, Color(0.0, 0.0, 0.0, 0.2))
		"flowers":
			var fc: Color = [Color(0.95, 0.9, 0.3), Color(0.92, 0.92, 0.88), Color(0.75, 0.55, 0.9)][k % 3]
			for i in range(6 + k * 3):
				var x6: float = 0.25 + Rng.f2(k, i, s) * 0.5
				var y6: float = 0.25 + Rng.f2(k, i, s + 1) * 0.5
				var q6: Vector2 = _wpx(p, x6, y6)
				_blend(p, int(q6.x), int(q6.y) + 1, Color(0.25, 0.4, 0.18))
				_blend(p, int(q6.x), int(q6.y), fc)
				_blend(p, int(q6.x) + 1, int(q6.y), _k(fc, 0.85))

## which decal (set name) lies on a tile of ground g, if any: chosen by a hash of the tile
static func decal_for(g: int, hsh: int, indoors: bool) -> String:
	var r: float = float(hsh % 1000) / 1000.0
	if indoors:
		return "stain" if r < 0.03 else ""
	match g:
		Defs.G_ASPHALT, Defs.G_ASPHALT_LX, Defs.G_ASPHALT_LY:
			if r < 0.06: return "crack"
			if r < 0.1: return "stain"
			if r < 0.12: return "patch"
			if r < 0.126: return "manhole"
			if r < 0.15: return "litter"
		Defs.G_PARKING:
			if r < 0.12: return "stain"
			if r < 0.18: return "crack"
			if r < 0.22: return "litter"
		Defs.G_SIDEWALK:
			if r < 0.08: return "crack"
			if r < 0.15: return "weeds"
			if r < 0.19: return "litter"
			if r < 0.23: return "leaves"
		Defs.G_CONCRETE:
			if r < 0.08: return "crack"
			if r < 0.14: return "stain"
		Defs.G_GRASS:
			if r < 0.2: return "tufts"
			if r < 0.24: return "rocks"
			if r < 0.29: return "flowers"
			if r < 0.32: return "leaves"
		Defs.G_GRASS_DARK:
			if r < 0.24: return "tufts"
			if r < 0.28: return "rocks"
		Defs.G_FOREST:
			if r < 0.25: return "leaves"
			if r < 0.36: return "tufts"
			if r < 0.4: return "rocks"
		Defs.G_DIRT:
			if r < 0.18: return "rocks"
			if r < 0.27: return "tufts"
		Defs.G_GRAVEL:
			if r < 0.1: return "weeds"
		Defs.G_SAND:
			if r < 0.07: return "rocks"
	return ""
