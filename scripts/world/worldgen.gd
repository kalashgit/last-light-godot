class_name WorldGen
extends RefCounted
## Deterministic, unbounded world generator.
## The world is divided into 384x384-tile regions. Each region has a road node that may host
## a hamlet, town or city; nodes are linked by highways. Everything is derived from the seed,
## so any chunk can be generated at any time in any order.

const REGION := 384
const K_WILD := 0
const K_HAMLET := 1
const K_TOWN := 2
const K_CITY := 3
const F_N := 1
const F_E := 2
const F_S := 4
const F_W := 8

var seed_v: int
var n_forest := FastNoiseLite.new()
var n_water := FastNoiseLite.new()
var n_detail := FastNoiseLite.new()
var n_cluster := FastNoiseLite.new()
var _regions: Dictionary = {}
var _lots: Dictionary = {}
var _lot_order: Array = []

func _init(world_seed: int) -> void:
	seed_v = world_seed
	n_forest.seed = Rng.h(world_seed + 11) & 0x7FFFFFFF
	n_forest.noise_type = FastNoiseLite.TYPE_SIMPLEX_SMOOTH
	n_forest.frequency = 0.011
	n_forest.fractal_octaves = 3
	n_water.seed = Rng.h(world_seed + 23) & 0x7FFFFFFF
	n_water.noise_type = FastNoiseLite.TYPE_SIMPLEX_SMOOTH
	n_water.frequency = 0.006
	n_water.fractal_octaves = 2
	n_detail.seed = Rng.h(world_seed + 37) & 0x7FFFFFFF
	n_detail.noise_type = FastNoiseLite.TYPE_SIMPLEX
	n_detail.frequency = 0.05
	n_detail.fractal_octaves = 2

## population multiplier for a chunk (0.25 .. 2.4), from a Voronoi-style cellular field
func cluster(cx: int, cy: int) -> float:
	if n_cluster.seed != ((seed_v + 91) & 0x7FFFFFFF):
		n_cluster.seed = (seed_v + 91) & 0x7FFFFFFF
		n_cluster.noise_type = FastNoiseLite.TYPE_CELLULAR
		n_cluster.cellular_return_type = FastNoiseLite.RETURN_CELL_VALUE
		n_cluster.frequency = 0.09
	var v: float = n_cluster.get_noise_2d(cx, cy) * 0.5 + 0.5
	return 0.25 + v * v * 2.15

static func fdiv(a: int, b: int) -> int:
	return floori(float(a) / float(b))

# ------------------------------------------------------------------ regions
func region_kind(rx: int, ry: int) -> int:
	if rx == 0 and ry == 0:
		return K_TOWN
	var f: float = Rng.f2(rx, ry, seed_v + 101)
	if f < 0.34: return K_WILD
	if f < 0.60: return K_HAMLET
	if f < 0.88: return K_TOWN
	return K_CITY

func region_node(rx: int, ry: int) -> Vector2i:
	var jx: int = int(REGION * 0.34) + Rng.i2(rx, ry, seed_v + 103, int(REGION * 0.32))
	var jy: int = int(REGION * 0.34) + Rng.i2(rx, ry, seed_v + 107, int(REGION * 0.32))
	return Vector2i(rx * REGION + jx, ry * REGION + jy)

## highway rectangles (5 wide) leaving the node of region (rx,ry) to the east and south
## returns Array of [Rect2i, axis]  axis 0 = runs along x, 1 = along y
func region_highways(rx: int, ry: int) -> Array:
	var n: Vector2i = region_node(rx, ry)
	var e: Vector2i = region_node(rx + 1, ry)
	var s: Vector2i = region_node(rx, ry + 1)
	var bx: int = (rx + 1) * REGION
	var by: int = (ry + 1) * REGION
	var out: Array = []
	# east link: along own row to the region border, along the border, then along the neighbour's row
	out.append([Rect2i(n.x - 2, n.y - 2, bx - n.x + 5, 5), 0])
	out.append([Rect2i(bx - 2, mini(n.y, e.y) - 2, 5, absi(e.y - n.y) + 5), 1])
	out.append([Rect2i(bx - 2, e.y - 2, e.x - bx + 5, 5), 0])
	# south link
	out.append([Rect2i(n.x - 2, n.y - 2, 5, by - n.y + 5), 1])
	out.append([Rect2i(mini(n.x, s.x) - 2, by - 2, absi(s.x - n.x) + 5, 5), 0])
	out.append([Rect2i(s.x - 2, by - 2, 5, s.y - by + 5), 1])
	return out

func region(rx: int, ry: int) -> Dictionary:
	var key := Vector2i(rx, ry)
	if _regions.has(key):
		return _regions[key]
	var R := {"rx": rx, "ry": ry, "kind": region_kind(rx, ry), "node": region_node(rx, ry),
		"rect": Rect2i(), "half": 0, "streets": [], "lots": []}
	var rng: RandomNumberGenerator = Rng.make(Rng.h2(rx, ry, seed_v + 211))
	if R["kind"] != K_WILD:
		_plan_town(R, rng)
	_plan_pois(R, rng)
	if _regions.size() > 24:
		_regions.clear()
	_regions[key] = R
	return R

func _plan_town(R: Dictionary, rng: RandomNumberGenerator) -> void:
	var node: Vector2i = R["node"]
	var kind: int = R["kind"]
	var half := 40
	match kind:
		K_HAMLET: half = rng.randi_range(36, 50)
		K_TOWN: half = rng.randi_range(78, 100)
		K_CITY: half = rng.randi_range(110, 122)
	var rx0: int = int(R["rx"]) * REGION + 10
	var ry0: int = int(R["ry"]) * REGION + 10
	var x0: int = maxi(node.x - half, rx0)
	var y0: int = maxi(node.y - half, ry0)
	var x1: int = mini(node.x + half, rx0 + REGION - 20)
	var y1: int = mini(node.y + half, ry0 + REGION - 20)
	var rect := Rect2i(x0, y0, x1 - x0, y1 - y0)
	R["rect"] = rect
	R["half"] = half
	var streets: Array = R["streets"]
	streets.append([Rect2i(node.x - 2, y0, 5, y1 - y0), 1])
	streets.append([Rect2i(x0, node.y - 2, x1 - x0, 5), 0])
	var blocks: Array = []
	var quads: Array = [
		[Rect2i(x0, y0, node.x - 3 - x0, node.y - 3 - y0), F_E | F_S],
		[Rect2i(node.x + 4, y0, x1 - node.x - 4, node.y - 3 - y0), F_W | F_S],
		[Rect2i(x0, node.y + 4, node.x - 3 - x0, y1 - node.y - 4), F_E | F_N],
		[Rect2i(node.x + 4, node.y + 4, x1 - node.x - 4, y1 - node.y - 4), F_W | F_N],
	]
	for q in quads:
		_split(q[0], q[1], rng, blocks, streets)
	# zoning
	var must: Array = ["grocery", "pharmacy", "hardware", "diner", "police", "gas", "clinic", "clothing", "gunstore", "bar", "bookstore", "office", "school", "firestation", "warehouse"]
	if kind == K_HAMLET:
		must = ["grocery", "gas", "diner", "hardware"]
	var must_i := 0
	var lots: Array = R["lots"]
	# process blocks nearest the centre first so essential shops land downtown
	blocks.sort_custom(func(a, b):
		var ca: Vector2 = Vector2((a[0] as Rect2i).get_center()) - Vector2(node)
		var cb: Vector2 = Vector2((b[0] as Rect2i).get_center()) - Vector2(node)
		return ca.length_squared() < cb.length_squared())
	for bi in range(blocks.size()):
		var br: Rect2i = blocks[bi][0]
		var flags: int = blocks[bi][1]
		if br.size.x < 12 or br.size.y < 12:
			lots.append({"r": br, "f": 2, "k": "woods"})
			continue
		var c: Vector2i = br.get_center()
		var dist: float = maxf(absf(c.x - node.x), absf(c.y - node.y)) / float(half)
		var commercial: bool = dist < (0.42 if kind == K_CITY else 0.34) or (kind == K_HAMLET and bi < 2)
		var roll: float = rng.randf()
		if not commercial and roll < 0.07:
			lots.append({"r": br, "f": _any_facing(flags), "k": "park"})
			continue
		var industrial: bool = (not commercial) and kind == K_CITY and dist > 0.75 and roll > 0.8
		_block_lots(br, flags, rng, commercial, industrial, must, must_i, lots)
		for l in lots:
			if l.has("_m"):
				must_i += 1
				l.erase("_m")
	for i in range(lots.size()):
		var l2: Dictionary = lots[i]
		var r: Rect2i = l2["r"]
		l2["id"] = (Rng.h2(r.position.x, r.position.y, seed_v + 311) & 0x3FFFFFFF) | 1

static func _any_facing(flags: int) -> int:
	if flags & F_S: return 2
	if flags & F_N: return 0
	if flags & F_E: return 1
	return 3

func _split(r: Rect2i, flags: int, rng: RandomNumberGenerator, blocks: Array, streets: Array) -> void:
	if r.size.x < 10 or r.size.y < 10:
		return
	var mx: int = rng.randi_range(38, 46)
	var min_b := 17
	var can_x: bool = r.size.x >= min_b * 2 + 5
	var can_y: bool = r.size.y >= min_b * 2 + 5
	if r.size.x > mx and can_x and (r.size.x >= r.size.y or not (r.size.y > mx and can_y)):
		var cut: int = rng.randi_range(min_b, r.size.x - min_b - 5)
		streets.append([Rect2i(r.position.x + cut + 1, r.position.y, 3, r.size.y), 1])
		_split(Rect2i(r.position.x, r.position.y, cut, r.size.y), flags | F_E, rng, blocks, streets)
		_split(Rect2i(r.position.x + cut + 5, r.position.y, r.size.x - cut - 5, r.size.y), flags | F_W, rng, blocks, streets)
	elif r.size.y > mx and can_y:
		var cut2: int = rng.randi_range(min_b, r.size.y - min_b - 5)
		streets.append([Rect2i(r.position.x, r.position.y + cut2 + 1, r.size.x, 3), 0])
		_split(Rect2i(r.position.x, r.position.y, r.size.x, cut2), flags | F_S, rng, blocks, streets)
		_split(Rect2i(r.position.x, r.position.y + cut2 + 5, r.size.x, r.size.y - cut2 - 5), flags | F_N, rng, blocks, streets)
	else:
		blocks.append([r, flags])

func _block_lots(br: Rect2i, flags: int, rng: RandomNumberGenerator, commercial: bool, industrial: bool, must: Array, must_i: int, lots: Array) -> void:
	# rows[]: [rect, facing]
	var rows: Array = []
	var has_n: bool = (flags & F_N) != 0
	var has_s: bool = (flags & F_S) != 0
	var has_e: bool = (flags & F_E) != 0
	var has_w: bool = (flags & F_W) != 0
	var along_x: bool = has_n or has_s
	if along_x and (has_e or has_w) and br.size.y > br.size.x and not (has_n and has_s):
		along_x = false
	if along_x:
		if has_n and has_s and br.size.y >= 28:
			var d: int = br.size.y / 2
			rows.append([Rect2i(br.position.x, br.position.y, br.size.x, d), 0])
			rows.append([Rect2i(br.position.x, br.position.y + d, br.size.x, br.size.y - d), 2])
		elif has_s:
			var d2: int = mini(br.size.y, 22)
			rows.append([Rect2i(br.position.x, br.end.y - d2, br.size.x, d2), 2])
			if br.size.y - d2 >= 6:
				lots.append({"r": Rect2i(br.position.x, br.position.y, br.size.x, br.size.y - d2), "f": 2, "k": "woods"})
		else:
			var d3: int = mini(br.size.y, 22)
			rows.append([Rect2i(br.position.x, br.position.y, br.size.x, d3), 0])
			if br.size.y - d3 >= 6:
				lots.append({"r": Rect2i(br.position.x, br.position.y + d3, br.size.x, br.size.y - d3), "f": 0, "k": "woods"})
	else:
		if has_e and has_w and br.size.x >= 28:
			var d4: int = br.size.x / 2
			rows.append([Rect2i(br.position.x, br.position.y, d4, br.size.y), 3])
			rows.append([Rect2i(br.position.x + d4, br.position.y, br.size.x - d4, br.size.y), 1])
		elif has_e:
			var d5: int = mini(br.size.x, 22)
			rows.append([Rect2i(br.end.x - d5, br.position.y, d5, br.size.y), 1])
			if br.size.x - d5 >= 6:
				lots.append({"r": Rect2i(br.position.x, br.position.y, br.size.x - d5, br.size.y), "f": 1, "k": "woods"})
		else:
			var d6: int = mini(br.size.x, 22)
			rows.append([Rect2i(br.position.x, br.position.y, d6, br.size.y), 3])
			if br.size.x - d6 >= 6:
				lots.append({"r": Rect2i(br.position.x + d6, br.position.y, br.size.x - d6, br.size.y), "f": 3, "k": "woods"})
	var used := 0
	for row in rows:
		var rr: Rect2i = row[0]
		var facing: int = row[1]
		var length: int = rr.size.x if (facing == 0 or facing == 2) else rr.size.y
		var pos := 0
		while pos < length:
			var target: int = rng.randi_range(13, 17)
			if commercial:
				target = rng.randi_range(15, 22)
			if industrial:
				target = rng.randi_range(20, 28)
			var lw: int = target
			if length - pos - lw < 12:
				lw = length - pos
			var lr: Rect2i
			if facing == 0 or facing == 2:
				lr = Rect2i(rr.position.x + pos, rr.position.y, lw, rr.size.y)
			else:
				lr = Rect2i(rr.position.x, rr.position.y + pos, rr.size.x, lw)
			pos += lw
			var k := "house"
			var from_must := false
			if lw < 9:
				k = "woods"
			elif industrial:
				k = "warehouse" if rng.randf() < 0.7 else "parking"
			elif commercial:
				if must_i + used < must.size():
					k = must[must_i + used]
					used += 1
					from_must = true
				else:
					var f: float = rng.randf()
					if f < 0.12: k = "parking"
					elif f < 0.3: k = "house"
					else: k = BuildGen.SHOP_KINDS[rng.randi() % BuildGen.SHOP_KINDS.size()]
			var lot := {"r": lr, "f": facing, "k": k}
			if from_must:
				lot["_m"] = 1
			lots.append(lot)

func _plan_pois(R: Dictionary, rng: RandomNumberGenerator) -> void:
	var rx: int = R["rx"]
	var ry: int = R["ry"]
	var node: Vector2i = R["node"]
	var town: Rect2i = R["rect"]
	var lots: Array = R["lots"]
	var bounds := Rect2i(rx * REGION + 4, ry * REGION + 4, REGION - 8, REGION - 8)
	var n: int = rng.randi_range(3, 6)
	var placed: Array = []
	for i in range(n * 3):
		if placed.size() >= n:
			break
		var kinds: Array = ["farm", "farm", "cabin", "camp", "gas", "house", "house", "warehouse", "cabin", "diner", "checkpoint", "quarantine"]
		var k: String = kinds[rng.randi() % kinds.size()]
		var w := 16
		var h := 20
		match k:
			"farm":
				w = rng.randi_range(40, 48)
				h = rng.randi_range(40, 46)
			"cabin":
				w = 14
				h = 13
			"camp":
				w = 11
				h = 11
			"gas":
				w = 22
				h = 18
			"warehouse":
				w = 24
				h = 22
			"diner":
				w = 18
				h = 18
			"checkpoint":
				w = 18
				h = 14
			"quarantine":
				w = 28
				h = 26
		var along_x: bool = rng.randf() < 0.5
		var side: int = 1 if rng.randf() < 0.5 else -1
		var lr: Rect2i
		var facing := 0
		if along_x:
			# east highway: runs along y = node.y, x from node.x to region edge
			var x: int = rng.randi_range(node.x + 30, bounds.end.x - w - 2) if bounds.end.x - w - 2 > node.x + 30 else -999999
			if x == -999999:
				continue
			if side > 0:
				lr = Rect2i(x, node.y + 4, w, h)
				facing = 0
			else:
				lr = Rect2i(x, node.y - 3 - h, w, h)
				facing = 2
		else:
			var y: int = rng.randi_range(node.y + 30, bounds.end.y - h - 2) if bounds.end.y - h - 2 > node.y + 30 else -999999
			if y == -999999:
				continue
			# for E/W facing lots the footprint is rotated: swap w/h
			if side > 0:
				lr = Rect2i(node.x + 4, y, h, w)
				facing = 3
			else:
				lr = Rect2i(node.x - 3 - h, y, h, w)
				facing = 1
		if not bounds.encloses(lr):
			continue
		if town.size.x > 0 and town.grow(6).intersects(lr):
			continue
		var clash := false
		for p in placed:
			if (p as Rect2i).grow(4).intersects(lr):
				clash = true
		if clash:
			continue
		placed.append(lr)
		lots.append({"r": lr, "f": facing, "k": k, "poi": 1,
			"id": (Rng.h2(lr.position.x, lr.position.y, seed_v + 313) & 0x3FFFFFFF) | 1})

func lot_plan(lot: Dictionary) -> LotBuilder.LotPlan:
	var id: int = lot["id"]
	if _lots.has(id):
		return _lots[id]
	var r: Rect2i = lot["r"]
	var plan: LotBuilder.LotPlan = BuildGen.gen(lot["k"], r.size.x, r.size.y, lot["f"], Rng.h2(id, 7, seed_v), id)
	_lots[id] = plan
	_lot_order.append(id)
	if _lot_order.size() > 160:
		_lots.erase(_lot_order.pop_front())
	return plan

# ------------------------------------------------------------------ chunks
func gen_chunk(cx: int, cy: int) -> Chunk:
	if World.is_under(cy * 16.0):
		return _gen_under(cx, cy)
	var c := Chunk.new(cx, cy)
	var CS: int = Iso.CS
	var x0: int = cx * CS
	var y0: int = cy * CS
	var crect := Rect2i(x0, y0, CS, CS)
	var rx: int = fdiv(x0, REGION)
	var ry: int = fdiv(y0, REGION)
	var R: Dictionary = region(rx, ry)
	var town: Rect2i = R["rect"]
	var in_town: bool = town.size.x > 0 and town.intersects(crect)
	var D := Defs
	# ---- terrain
	for ly in range(CS):
		for lx in range(CS):
			var x: int = x0 + lx
			var y: int = y0 + ly
			var i: int = ly * CS + lx
			if in_town and town.has_point(Vector2i(x, y)):
				c.ground[i] = D.G_GRASS
				continue
			var wv: float = n_water.get_noise_2d(x, y)
			if wv > 0.5:
				if wv > 0.62:
					c.ground[i] = D.G_DEEP_WATER
				elif wv > 0.54:
					c.ground[i] = D.G_WATER
				else:
					c.ground[i] = D.G_SAND
					if Rng.f2(x, y, seed_v + 5) < 0.08:
						c.obj[i] = D.O_REEDS
				continue
			var fv: float = n_forest.get_noise_2d(x, y)
			var dv: float = n_detail.get_noise_2d(x, y)
			var r: float = Rng.f2(x, y, seed_v + 1)
			if fv > 0.22:
				c.ground[i] = D.G_FOREST
				var p: float = minf(0.1 + (fv - 0.22) * 0.5, 0.3)
				if r < p:
					var t: float = Rng.f2(x, y, seed_v + 2)
					c.obj[i] = D.O_TREE_PINE if t < 0.45 else (D.O_TREE_OAK if t < 0.8 else (D.O_TREE_BIRCH if t < 0.95 else D.O_TREE_DEAD))
				elif r < p + 0.05:
					c.obj[i] = D.O_BUSH if Rng.f2(x, y, seed_v + 3) < 0.8 else D.O_BERRY_BUSH
				elif r < p + 0.06:
					c.obj[i] = D.O_STUMP if Rng.f2(x, y, seed_v + 3) < 0.5 else D.O_ROCK
			elif fv > 0.05:
				c.ground[i] = D.G_GRASS_DARK
				if r < 0.045:
					c.obj[i] = D.O_TREE_OAK if Rng.f2(x, y, seed_v + 2) < 0.6 else D.O_TREE_BIRCH
				elif r < 0.09:
					c.obj[i] = D.O_BUSH if Rng.f2(x, y, seed_v + 3) < 0.85 else D.O_BERRY_BUSH
				elif r < 0.16 and dv > 0.1:
					c.obj[i] = D.O_TALL_GRASS
			else:
				c.ground[i] = D.G_GRASS
				if dv < -0.62:
					c.ground[i] = D.G_DIRT
					if r < 0.02: c.obj[i] = D.O_ROCK
				elif r < 0.008:
					c.obj[i] = D.O_TREE_OAK
				elif r < 0.02:
					c.obj[i] = D.O_BUSH
				elif r < 0.03:
					c.obj[i] = D.O_FLOWERS
				elif dv > 0.25 and r < 0.3:
					c.obj[i] = D.O_TALL_GRASS
				elif r < 0.034:
					c.obj[i] = D.O_ROCK
	# ---- highways
	var has_road := false
	for ny in range(ry - 1, ry + 2):
		for nx in range(rx - 1, rx + 2):
			for hw in region_highways(nx, ny):
				var hr: Rect2i = hw[0]
				if not hr.grow(1).intersects(crect):
					continue
				has_road = true
				var axis: int = hw[1]
				var gr: Rect2i = hr.grow(1).intersection(crect)
				for y in range(gr.position.y, gr.end.y):
					for x in range(gr.position.x, gr.end.x):
						var i2: int = (y - y0) * CS + (x - x0)
						c.obj[i2] = 0
						if hr.has_point(Vector2i(x, y)):
							var centre: bool = (y == hr.position.y + 2) if axis == 0 else (x == hr.position.x + 2)
							var g: int = c.ground[i2]
							if centre and g != D.G_ASPHALT_LX and g != D.G_ASPHALT_LY and g != D.G_ASPHALT:
								c.ground[i2] = D.G_ASPHALT_LX if axis == 0 else D.G_ASPHALT_LY
							elif not centre:
								c.ground[i2] = D.G_ASPHALT
							elif g == D.G_ASPHALT_LX or g == D.G_ASPHALT_LY:
								c.ground[i2] = D.G_ASPHALT
						elif not D.ground_is_road(c.ground[i2]):
							c.ground[i2] = D.G_GRAVEL
	# ---- roadside stories: pile-ups and people who did not make it out of town
	if has_road and not in_town and Rng.f2(cx, cy, seed_v + 901) < 0.05:
		_road_story(c, x0, y0)
	# ---- town streets
	if in_town:
		var streets: Array = R["streets"]
		for st in streets:
			var sr: Rect2i = st[0]
			var grown: Rect2i = sr.grow_individual(1, 0, 1, 0) if st[1] == 1 else sr.grow_individual(0, 1, 0, 1)
			var gi: Rect2i = grown.intersection(crect)
			for y in range(gi.position.y, gi.end.y):
				for x in range(gi.position.x, gi.end.x):
					var i3: int = (y - y0) * CS + (x - x0)
					if not D.ground_is_road(c.ground[i3]):
						c.ground[i3] = D.G_SIDEWALK
						c.obj[i3] = 0
						if Rng.f2(x, y, seed_v + 9) < 0.012:
							c.obj[i3] = D.O_STREET_LAMP if Rng.f2(x, y, seed_v + 10) < 0.6 else (D.O_HYDRANT if Rng.f2(x, y, seed_v + 10) < 0.8 else D.O_TRASH_CAN)
		for st in streets:
			var sr2: Rect2i = st[0]
			var axis2: int = st[1]
			var si: Rect2i = sr2.intersection(crect)
			var mid: int = (sr2.position.y + sr2.size.y / 2) if axis2 == 0 else (sr2.position.x + sr2.size.x / 2)
			for y in range(si.position.y, si.end.y):
				for x in range(si.position.x, si.end.x):
					var i4: int = (y - y0) * CS + (x - x0)
					var was_road: bool = D.ground_is_road(c.ground[i4])
					c.obj[i4] = 0
					var centre2: bool = (y == mid) if axis2 == 0 else (x == mid)
					if centre2 and not was_road:
						c.ground[i4] = D.G_ASPHALT_LX if axis2 == 0 else D.G_ASPHALT_LY
					else:
						c.ground[i4] = D.G_ASPHALT
					# abandoned traffic
					if not centre2 and Rng.f2(x, y, seed_v + 12) < 0.0015:
						c.obj[i4] = D.O_BARREL
	# ---- lots
	var lots: Array = R["lots"]
	var has_lot := false
	for lot in lots:
		var lr: Rect2i = lot["r"]
		if not lr.intersects(crect):
			continue
		has_lot = true
		var plan: LotBuilder.LotPlan = lot_plan(lot)
		var li: Rect2i = lr.intersection(crect)
		var poi: bool = lot.has("poi")
		c.btype[plan.bld_id] = plan.btype
		for y in range(li.position.y, li.end.y):
			for x in range(li.position.x, li.end.x):
				var ci: int = (y - y0) * CS + (x - x0)
				var pi: int = (y - lr.position.y) * plan.w + (x - lr.position.x)
				var pg: int = plan.ground[pi]
				if poi:
					if D.ground_is_road(c.ground[ci]) or c.ground[ci] == D.G_GRAVEL:
						continue
					if D.ground_is_water(c.ground[ci]) or c.ground[ci] == D.G_SAND:
						c.ground[ci] = D.G_GRASS
					if plan.btype != "cabin" and plan.btype != "camp":
						c.obj[ci] = 0
					elif pg != 0 or plan.inside[pi] != 0:
						c.obj[ci] = 0
				if pg != 0:
					c.ground[ci] = pg
				if plan.wall_n[pi] != 0:
					c.wall_n[ci] = plan.wall_n[pi]
					c.st_n[ci] = plan.st_n[pi]
				if plan.wall_w[pi] != 0:
					c.wall_w[ci] = plan.wall_w[pi]
					c.st_w[ci] = plan.st_w[pi]
				if plan.obj[pi] != 0:
					c.obj[ci] = plan.obj[pi]
				if plan.inside[pi] != 0:
					c.bld[ci] = plan.bld_id
					c.roof[ci] = plan.roof[pi]
		for cp in plan.corpses:
			var cw: Vector2i = lr.position + (cp[0] as Vector2i)
			if crect.has_point(cw):
				c.corpses.append(_story_corpse(cw, cp[1]))
		for bc in plan.blood:
			var bw: Vector2i = lr.position + (bc as Vector2i)
			if crect.has_point(bw):
				c.blood.append([bw.x + 0.5, bw.y + 0.5, Rng.h2(bw.x, bw.y, 5) % 4])
		for nc in plan.npcs:
			var nw: Vector2i = lr.position + (nc[0] as Vector2i)
			if crect.has_point(nw):
				c.story_n.append([Vector2(nw.x + 0.5, nw.y + 0.5), nc[1]])
		for zc in plan.zspawn:
			var zw: Vector2i = lr.position + (zc as Vector2i)
			if crect.has_point(zw):
				c.story_z.append(Vector2(zw.x + 0.5, zw.y + 0.5))
	# ---- zone + minimap
	if in_town:
		var node: Vector2i = R["node"]
		var d: float = maxf(absf(x0 + 8 - node.x), absf(y0 + 8 - node.y)) / float(maxi(int(R["half"]), 1))
		c.zone = 3 if d < 0.4 else 2
		if int(R["kind"]) == K_HAMLET:
			c.zone = 2
	elif has_lot or has_road:
		c.zone = 1
	c.map_px = _minimap(c)
	return c

static func _minimap(c: Chunk) -> PackedByteArray:
	var m := PackedByteArray()
	m.resize(Iso.CS2)
	for i in range(Iso.CS2):
		var v: int = c.ground[i]
		if c.bld[i] != 0:
			v = 100
		else:
			var o: int = c.obj[i] & 1023
			if o >= Defs.O_TREE_OAK and o <= Defs.O_TREE_DEAD:
				v = 101
		m[i] = v
	return m

func _story_corpse(cell: Vector2i, table: String) -> Dictionary:
	var hv: int = Rng.h2(cell.x, cell.y, seed_v + 31)
	return {"x": cell.x + 0.3 + (hv % 40) / 100.0, "y": cell.y + 0.3 + ((hv >> 8) % 40) / 100.0, "d": (hv >> 4) % 8,
		"l": [hv % 4, (hv >> 3) % 10, (hv >> 7) % 6, (hv >> 11) % 6], "h": 0.0, "perm": 1, "lt": table}

func _stamp_obj(c: Chunk, lx: int, ly: int, id: int, rot: int) -> bool:
	var fs: Vector2i = Defs.obj_size(id, rot)
	if lx < 0 or ly < 0 or lx + fs.x > 16 or ly + fs.y > 16:
		return false
	for j in range(fs.y):
		for i in range(fs.x):
			var k: int = (ly + j) * 16 + lx + i
			if c.obj[k] != 0 or not Defs.ground_is_road(c.ground[k]):
				return false
	for j in range(fs.y):
		for i in range(fs.x):
			c.obj[(ly + j) * 16 + lx + i] = Defs.ocell(id, rot, j * fs.x + i)
	return true

func _road_story(c: Chunk, x0: int, y0: int) -> void:
	var rng: RandomNumberGenerator = Rng.make(Rng.h2(c.cx, c.cy, seed_v + 903))
	for ly in range(3, 11):
		for lx in range(3, 11):
			var g: int = c.ground[ly * 16 + lx]
			if g != Defs.G_ASPHALT_LX and g != Defs.G_ASPHALT_LY:
				continue
			var along_x: bool = g == Defs.G_ASPHALT_LX
			var placed := 0
			if along_x:
				if _stamp_obj(c, lx - 1, ly - 2, Defs.O_CAR_WRECK, 1): placed += 1
				if _stamp_obj(c, lx + 1, ly + 1, Defs.O_CAR if rng.randf() < 0.6 else Defs.O_CAR_WRECK, 3): placed += 1
			else:
				if _stamp_obj(c, lx - 2, ly - 1, Defs.O_CAR_WRECK, 0): placed += 1
				if _stamp_obj(c, lx + 1, ly + 1, Defs.O_CAR if rng.randf() < 0.6 else Defs.O_CAR_WRECK, 2): placed += 1
			if placed == 0:
				continue
			for k in range(rng.randi_range(1, 3)):
				var cl := Vector2i(lx + rng.randi_range(-3, 3), ly + rng.randi_range(-3, 3))
				if cl.x < 0 or cl.y < 0 or cl.x > 15 or cl.y > 15 or c.obj[cl.y * 16 + cl.x] != 0:
					continue
				c.corpses.append(_story_corpse(Vector2i(x0 + cl.x, y0 + cl.y), "corpse_survivor" if k == 0 else "corpse"))
				c.blood.append([x0 + cl.x + 0.5, y0 + cl.y + 0.5, k % 4])
			return

## cellar layout for a lot: Array of [Vector2i cell (lot coords), object cell]
func _cellar_objects(plan: LotBuilder.LotPlan) -> Array:
	var rng: RandomNumberGenerator = Rng.make(Rng.h2(plan.bld_id, 17, seed_v))
	var out: Array = []
	var r: Rect2i = plan.cellar
	var kinds: Array = [Defs.O_METAL_SHELF, Defs.O_CRATE, Defs.O_BARREL, Defs.O_BOXES, Defs.O_CRATE, Defs.O_METAL_SHELF]
	for x in range(r.position.x, r.end.x):
		var cell := Vector2i(x, r.position.y)
		if cell != plan.hatch and rng.randf() < 0.7:
			out.append([cell, Defs.ocell(kinds[rng.randi() % kinds.size()], 0, 0)])
	for y in range(r.position.y + 1, r.end.y):
		var cell2 := Vector2i(r.position.x, y)
		if cell2 != plan.hatch and rng.randf() < 0.5:
			out.append([cell2, Defs.ocell(kinds[rng.randi() % kinds.size()], 1, 0)])
	return out

## the underground band: nothing but the cellars of the buildings above
func _gen_under(cx: int, cy: int) -> Chunk:
	var c := Chunk.new(cx, cy)
	var x0: int = cx * 16
	var y0: int = cy * 16
	var lvl: int = World.level(y0)
	var sy0: int = y0 - World.UNDER * lvl
	var srect := Rect2i(x0, sy0, 16, 16)
	if lvl == 2:
		return _gen_upper(c, x0, sy0, srect)
	var R: Dictionary = region(fdiv(x0, REGION), fdiv(sy0, REGION))
	var wall: int = Defs.wall(Defs.WM_CONCRETE, Defs.WS_SOLID)
	for lot in R["lots"]:
		var lr: Rect2i = lot["r"]
		if not lr.grow(1).intersects(srect):
			continue
		var plan: LotBuilder.LotPlan = lot_plan(lot)
		if plan.hatch.x < 0:
			continue
		var cr := Rect2i(lr.position + plan.cellar.position, plan.cellar.size)
		var uid: int = plan.bld_id + 0x40000000
		c.btype[uid] = "cellar"
		for ly in range(16):
			for lx in range(16):
				var x: int = x0 + lx
				var y: int = sy0 + ly
				var i: int = ly * 16 + lx
				var inside: bool = cr.has_point(Vector2i(x, y))
				if inside:
					c.ground[i] = Defs.G_CONCRETE
					c.bld[i] = uid
				if x >= cr.position.x and x < cr.end.x and (y == cr.position.y or y == cr.end.y):
					c.wall_n[i] = wall
				if y >= cr.position.y and y < cr.end.y and (x == cr.position.x or x == cr.end.x):
					c.wall_w[i] = wall
		for o in _cellar_objects(plan):
			var w: Vector2i = lr.position + (o[0] as Vector2i)
			if srect.has_point(w):
				c.obj[(w.y - sy0) * 16 + (w.x - x0)] = o[1]
		var hw: Vector2i = lr.position + plan.hatch
		if srect.has_point(hw):
			c.obj[(hw.y - sy0) * 16 + (hw.x - x0)] = Defs.ocell(Defs.O_LADDER, 0, 0)
		if Rng.f2(plan.bld_id, 3, seed_v + 77) < 0.2:
			var zc := Vector2i(cr.end.x - 1, cr.end.y - 1)
			if srect.has_point(zc) and zc != hw:
				c.story_z.append(Vector2(zc.x + 0.5, zc.y + World.UNDER + 0.5))
	c.map_px.resize(Iso.CS2)
	return c

## the upper-floor band: one open storey over the footprint of every house with a staircase
func _gen_upper(c: Chunk, x0: int, sy0: int, srect: Rect2i) -> Chunk:
	var R: Dictionary = region(fdiv(x0, REGION), fdiv(sy0, REGION))
	var w_in: int = Defs.wall(Defs.WM_PLASTER_CREAM, Defs.WS_SOLID)
	var w_out: int = Defs.wall(Defs.WM_SIDING_WHITE, Defs.WS_SOLID)
	var kinds: Array = [Defs.O_WARDROBE, Defs.O_DRESSER, Defs.O_NIGHTSTAND, Defs.O_BOOKSHELF, Defs.O_CRATE, Defs.O_ARMCHAIR, Defs.O_DESK]
	for lot in R["lots"]:
		var lr: Rect2i = lot["r"]
		if not lr.grow(1).intersects(srect):
			continue
		var plan: LotBuilder.LotPlan = lot_plan(lot)
		if plan.stairs.x < 0:
			continue
		var uid: int = plan.bld_id + 0x20000000
		c.btype[uid] = "attic" if plan.attic else "house"
		for ly in range(16):
			for lx in range(16):
				var px: int = x0 + lx - lr.position.x
				var py: int = sy0 + ly - lr.position.y
				var here: bool = px >= 0 and py >= 0 and px < plan.w and py < plan.h and plan.inside[py * plan.w + px] != 0
				var north: bool = px >= 0 and py - 1 >= 0 and px < plan.w and py - 1 < plan.h and plan.inside[(py - 1) * plan.w + px] != 0
				var west: bool = px - 1 >= 0 and py >= 0 and px - 1 < plan.w and py < plan.h and plan.inside[py * plan.w + px - 1] != 0
				var i: int = ly * 16 + lx
				if here:
					c.ground[i] = Defs.G_PLANK if plan.attic else Defs.G_WOOD_DARK
					c.bld[i] = uid
					c.roof[i] = plan.roof[py * plan.w + px]
				if here != north:
					c.wall_n[i] = w_in if here else w_out
				if here != west:
					c.wall_w[i] = w_in if here else w_out
				if here and plan.attic and Vector2i(px, py) != plan.stairs:
					if Rng.f2(x0 + lx, sy0 + ly, plan.bld_id + 6) < 0.16:
						c.obj[i] = Defs.ocell(Defs.O_BOXES, 0, 0)          # boxed-up lives
				elif here and not north and Vector2i(px, py) != plan.stairs:
					var f: float = Rng.f2(x0 + lx, sy0 + ly, plan.bld_id + 5)
					if f < 0.5:
						c.obj[i] = Defs.ocell(kinds[int(f * 100.0) % kinds.size()], 0, 0)
				elif here and Rng.f2(x0 + lx, sy0 + ly, plan.bld_id + 9) < 0.05 and Vector2i(px, py) != plan.stairs:
					c.obj[i] = Defs.ocell(Defs.O_BEDROLL, 0, 0)
		var sw: Vector2i = lr.position + plan.stairs
		if srect.has_point(sw):
			c.obj[(sw.y - sy0) * 16 + (sw.x - x0)] = Defs.ocell(Defs.O_ATTIC_LADDER if plan.attic else Defs.O_STAIRS, 2, 0)
			if Rng.f2(plan.bld_id, 4, seed_v + 79) < 0.3:
				c.story_z.append(Vector2(sw.x + 2.5, sw.y + World.UNDER * 2 + 1.5))
	c.map_px.resize(Iso.CS2)
	return c

## vegetation creeps over lawns, pavements and roads as the weeks pass
func overgrow(c: Chunk, days: float) -> void:
	if World.is_under(c.cy * 16.0):
		return
	var g: float = clampf((days - 2.0) / 40.0, 0.0, 1.0)
	if g <= 0.0:
		return
	var x0: int = c.cx * 16
	var y0: int = c.cy * 16
	for i in range(Iso.CS2):
		if c.obj[i] != 0 or c.bld[i] != 0:
			continue
		var gr: int = c.ground[i]
		var f: float = Rng.f2(x0 + (i & 15), y0 + (i >> 4), seed_v + 771)
		if gr == Defs.G_GRASS and c.zone >= 2:
			if f < g * 0.30: c.obj[i] = Defs.O_TALL_GRASS
			elif f < g * 0.33: c.obj[i] = Defs.O_BUSH
			elif f < g * 0.36: c.obj[i] = Defs.O_FLOWERS
		elif gr == Defs.G_SIDEWALK or gr == Defs.G_CONCRETE:
			if c.bld[i] == 0 and f < g * 0.12: c.obj[i] = Defs.O_WEEDS
		elif Defs.ground_is_road(gr):
			if f < g * 0.035: c.obj[i] = Defs.O_WEEDS

## find the player's starting building. kind: house | downtown | farm | cabin
func find_start(kind: String = "house", salt: int = 0) -> Dictionary:
	var R: Dictionary = region(0, 0)
	var node: Vector2i = R["node"]
	var best: Dictionary = {}
	var best_score := -1e9
	var want: String = "house" if kind == "downtown" else kind
	for ry in range(-1, 2):
		for rx in range(-1, 2):
			if (rx != 0 or ry != 0) and (kind == "house" or kind == "downtown"):
				continue
			for lot in region(rx, ry)["lots"]:
				if lot["k"] != want:
					continue
				if (kind == "house" or kind == "downtown") and lot.has("poi"):
					continue
				var r: Rect2i = lot["r"]
				var d: float = Vector2(r.get_center() - node).length()
				var score: float = -d
				if kind == "house":
					score = -absf(d - float(R["half"]) * 0.8)
				score += Rng.f2(r.position.x, r.position.y, seed_v + 401 + salt * 13) * (6.0 if salt == 0 else 60.0)
				if score > best_score:
					var plan: LotBuilder.LotPlan = lot_plan(lot)
					if plan.spawn.x < 0 or not plan.zspawn.is_empty() or plan.btype == "stash" or not plan.corpses.is_empty():
						continue
					best_score = score
					best = lot
	if best.is_empty():
		if kind != "house":
			return find_start("house", salt)
		return {"pos": Vector2(node) + Vector2(6.5, 6.5), "lot": {}}
	var plan2: LotBuilder.LotPlan = lot_plan(best)
	var br: Rect2i = best["r"]
	return {"pos": Vector2(br.position.x + plan2.spawn.x + 0.5, br.position.y + plan2.spawn.y + 0.5), "lot": best}

## generate (at most) one not-yet-cached lot plan near a position.
## called once per frame so entering a new street never stalls on building generation.
func prewarm_step(pos: Vector2, radius: float = 70.0) -> bool:
	var rx: int = fdiv(floori(pos.x), REGION)
	var ry: int = fdiv(floori(pos.y), REGION)
	var R: Dictionary = region(rx, ry)
	var pr := Rect2i(floori(pos.x - radius), floori(pos.y - radius), int(radius * 2.0), int(radius * 2.0))
	for lot in R["lots"]:
		if _lots.has(lot["id"]):
			continue
		if (lot["r"] as Rect2i).intersects(pr):
			lot_plan(lot)
			return true
	return false
