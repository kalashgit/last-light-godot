class_name World
extends RefCounted
## Chunk store, streaming, spatial queries and all tile mutations.
## Rendering and AI read from here; nothing in this class touches the scene tree.

var gen: WorldGen
var seed_v: int
var chunks: Dictionary = {}          # Vector2i -> Chunk
var store: Dictionary = {}           # Vector2i -> saved chunk Dictionary (unloaded but touched)
var explored: Dictionary = {}        # Vector2i -> PackedByteArray minimap
var ev_loaded: Array = []            # chunks loaded since last poll
var ev_unloaded: Array = []          # chunk keys unloaded since last poll
var ev_tiles: Array = []             # Vector2i tiles whose visuals changed
var ev_ground: Array = []            # Vector2i chunk keys whose ground layer changed
var store_loader: Callable           # optional: func(key) -> Dictionary  (disk region lookup)
var on_unload: Callable              # optional: func(chunk) called before a chunk is stored
var hour := 0.0
var loot_mult := 1.0
var growth := 1.0                    # overgrowth speed (sandbox)

## cellars live in a mirror band of the map far to the "south": same x, y + UNDER
const UNDER := 131072

static func is_under(y: float) -> bool:
	return y >= UNDER * 0.5

## 0 = ground level, 1 = cellar band, 2 = upper-floor band
static func level(y: float) -> int:
	if y < UNDER * 0.5:
		return 0
	return 1 if y < UNDER * 1.5 else 2

var _lc: Chunk = null
var _lkey := Vector2i(999999, 999999)

func _init(world_seed: int) -> void:
	seed_v = world_seed
	gen = WorldGen.new(world_seed)

# ------------------------------------------------------------------ access
func chunk(cx: int, cy: int) -> Chunk:
	if _lkey.x == cx and _lkey.y == cy:
		return _lc
	var k := Vector2i(cx, cy)
	var c: Chunk = chunks.get(k)
	if c != null:
		_lc = c
		_lkey = k
	return c

func chunk_at(x: int, y: int) -> Chunk:
	return chunk(x >> 4, y >> 4)

func is_loaded(x: int, y: int) -> bool:
	return chunk(x >> 4, y >> 4) != null

func ground(x: int, y: int) -> int:
	var c: Chunk = chunk(x >> 4, y >> 4)
	if c == null:
		return 0
	return c.ground[((y & 15) << 4) | (x & 15)]

func obj(x: int, y: int) -> int:
	var c: Chunk = chunk(x >> 4, y >> 4)
	if c == null:
		return 0
	return c.obj[((y & 15) << 4) | (x & 15)]

func bld(x: int, y: int) -> int:
	var c: Chunk = chunk(x >> 4, y >> 4)
	if c == null:
		return 0
	return c.bld[((y & 15) << 4) | (x & 15)]

## side 0 = north edge of tile, 1 = west edge of tile
func wall(x: int, y: int, side: int) -> int:
	var c: Chunk = chunk(x >> 4, y >> 4)
	if c == null:
		return 0
	var i: int = ((y & 15) << 4) | (x & 15)
	return c.wall_n[i] if side == 0 else c.wall_w[i]

func edge_state(x: int, y: int, side: int) -> int:
	var c: Chunk = chunk(x >> 4, y >> 4)
	if c == null:
		return 0
	var i: int = ((y & 15) << 4) | (x & 15)
	return c.st_n[i] if side == 0 else c.st_w[i]

static func idx(x: int, y: int) -> int:
	return ((y & 15) << 4) | (x & 15)

func btype_at(x: int, y: int) -> String:
	var c: Chunk = chunk_at(x, y)
	if c == null:
		return ""
	return c.btype.get(c.bld[idx(x, y)], "")

# ------------------------------------------------------------------ passability
func edge_blocks(x: int, y: int, side: int) -> bool:
	var c: Chunk = chunk(x >> 4, y >> 4)
	if c == null:
		return true
	var i: int = ((y & 15) << 4) | (x & 15)
	var w: int = c.wall_n[i] if side == 0 else c.wall_w[i]
	if w == 0:
		return false
	var shape: int = w & 3
	if shape == Defs.WS_ARCH:
		return false
	if shape == Defs.WS_DOOR:
		var st: int = c.st_n[i] if side == 0 else c.st_w[i]
		if (st & Defs.ES_PLANK_MASK) != 0:
			return true
		return (st & (Defs.ES_OPEN | Defs.ES_BROKEN)) == 0
	return true

func edge_opaque(x: int, y: int, side: int) -> bool:
	var c: Chunk = chunk(x >> 4, y >> 4)
	if c == null:
		return true
	var i: int = ((y & 15) << 4) | (x & 15)
	var w: int = c.wall_n[i] if side == 0 else c.wall_w[i]
	if w == 0:
		return false
	var tex: int = Defs.WALL_MATS[w >> 2][0]
	if tex >= Defs.WT_PICKET:
		return false
	var shape: int = w & 3
	if shape == Defs.WS_ARCH:
		return false
	var st: int = c.st_n[i] if side == 0 else c.st_w[i]
	if shape == Defs.WS_DOOR:
		return (st & (Defs.ES_OPEN | Defs.ES_BROKEN)) == 0
	if shape == Defs.WS_WINDOW:
		return ((st & Defs.ES_PLANK_MASK) >> Defs.ES_PLANK_SHIFT) >= 3 or (st & Defs.ES_CURTAIN) != 0
	return true

func tile_blocked(x: int, y: int) -> bool:
	var c: Chunk = chunk(x >> 4, y >> 4)
	if c == null:
		return true
	var i: int = ((y & 15) << 4) | (x & 15)
	var g: int = c.ground[i]
	if g == Defs.G_VOID or g == Defs.G_DEEP_WATER:
		return true
	var o: int = c.obj[i]
	if o == 0:
		return false
	return Defs.obj_solid(o) > 0.0

## can an entity walk from tile a to 4-adjacent tile b (ignores entity radius)
func can_step(ax: int, ay: int, bx: int, by: int) -> bool:
	if tile_blocked(bx, by):
		return false
	if ax != bx:
		return not edge_blocks(maxi(ax, bx), ay, 1)
	return not edge_blocks(ax, maxi(ay, by), 0)

## square collision test for a body of half-size r at (px,py)
func blocked(px: float, py: float, r: float) -> bool:
	var x0: int = floori(px - r)
	var x1: int = floori(px + r)
	var y0: int = floori(py - r)
	var y1: int = floori(py + r)
	for ty in range(y0, y1 + 1):
		for tx in range(x0, x1 + 1):
			var c: Chunk = chunk(tx >> 4, ty >> 4)
			if c == null:
				return true
			var i: int = ((ty & 15) << 4) | (tx & 15)
			var g: int = c.ground[i]
			if g == Defs.G_VOID or g == Defs.G_DEEP_WATER:
				return true
			var o: int = c.obj[i]
			if o != 0:
				var s: float = Defs.obj_solid(o)
				if s >= 0.5:
					return true
				if s > 0.0 and absf(px - (tx + 0.5)) < r + s and absf(py - (ty + 0.5)) < r + s:
					return true
	if x0 != x1:
		for ty in range(y0, y1 + 1):
			if edge_blocks(x1, ty, 1):
				return true
	if y0 != y1:
		for tx in range(x0, x1 + 1):
			if edge_blocks(tx, y1, 0):
				return true
	return false

## slide-move a body; returns the new position
func move(pos: Vector2, delta: Vector2, r: float) -> Vector2:
	var steps: int = maxi(1, ceili(delta.length() / 0.12))
	var d: Vector2 = delta / float(steps)
	var p: Vector2 = pos
	for i in range(steps):
		if d.x != 0.0 and not blocked(p.x + d.x, p.y, r):
			p.x += d.x
		if d.y != 0.0 and not blocked(p.x, p.y + d.y, r):
			p.y += d.y
	return p

## line of sight between two world points (walls / closed doors block)
func los(ax: float, ay: float, bx: float, by: float) -> bool:
	var cx: int = floori(ax)
	var cy: int = floori(ay)
	var ex: int = floori(bx)
	var ey: int = floori(by)
	var dx: float = bx - ax
	var dy: float = by - ay
	var sx: int = 1 if dx > 0.0 else -1
	var sy: int = 1 if dy > 0.0 else -1
	var tdx: float = absf(1.0 / dx) if absf(dx) > 0.00001 else 1e20
	var tdy: float = absf(1.0 / dy) if absf(dy) > 0.00001 else 1e20
	var tmx: float = ((cx + (1 if dx > 0.0 else 0)) - ax) / dx if absf(dx) > 0.00001 else 1e20
	var tmy: float = ((cy + (1 if dy > 0.0 else 0)) - ay) / dy if absf(dy) > 0.00001 else 1e20
	var guard := 0
	while (cx != ex or cy != ey) and guard < 160:
		guard += 1
		if tmx < tmy:
			var nx: int = cx + sx
			if edge_opaque(maxi(cx, nx), cy, 1):
				return false
			cx = nx
			tmx += tdx
		else:
			var ny: int = cy + sy
			if edge_opaque(cx, maxi(cy, ny), 0):
				return false
			cy = ny
			tmy += tdy
	return true

## how much of a sound gets from a to b: 1.0 in the open, less through each wall, shut door or window,
## and much less between floors. Open doors, broken windows, arches and fences let it through.
func sound_pass(a: Vector2, b: Vector2) -> float:
	var la: int = World.level(a.y)
	var lb: int = World.level(b.y)
	var k := 1.0
	if la != lb:
		k = 0.4
		b = Vector2(b.x, b.y - float(UNDER) * lb + float(UNDER) * la)
	var cx: int = floori(a.x)
	var cy: int = floori(a.y)
	var ex: int = floori(b.x)
	var ey: int = floori(b.y)
	var dx: float = b.x - a.x
	var dy: float = b.y - a.y
	var sx: int = 1 if dx > 0.0 else -1
	var sy: int = 1 if dy > 0.0 else -1
	var tdx: float = absf(1.0 / dx) if absf(dx) > 0.00001 else 1e20
	var tdy: float = absf(1.0 / dy) if absf(dy) > 0.00001 else 1e20
	var tmx: float = ((cx + (1 if dx > 0.0 else 0)) - a.x) / dx if absf(dx) > 0.00001 else 1e20
	var tmy: float = ((cy + (1 if dy > 0.0 else 0)) - a.y) / dy if absf(dy) > 0.00001 else 1e20
	var guard := 0
	while (cx != ex or cy != ey) and guard < 70 and k > 0.2:
		guard += 1
		var wx: int
		var wy: int
		var side: int
		if tmx < tmy:
			var nx: int = cx + sx
			wx = maxi(cx, nx); wy = cy; side = 1
			cx = nx
			tmx += tdx
		else:
			var ny: int = cy + sy
			wx = cx; wy = maxi(cy, ny); side = 0
			cy = ny
			tmy += tdy
		var wid: int = wall(wx, wy, side)
		if wid == 0 or Defs.wall_is_fence(wid):
			continue
		var shape: int = wid & 3
		var st: int = edge_state(wx, wy, side)
		if shape == Defs.WS_ARCH or (st & (Defs.ES_OPEN | Defs.ES_BROKEN)) != 0:
			continue
		if shape == Defs.WS_DOOR: k *= 0.72
		elif shape == Defs.WS_WINDOW: k *= 0.8 if (st & Defs.ES_PLANK_MASK) == 0 else 0.65
		else:
			var tex: int = Defs.wall_tex(wid)
			k *= 0.5 if (tex == Defs.WT_BRICK or tex == Defs.WT_CONCRETE) else 0.62
	return maxf(k, 0.2)

## the radius at which a sound made at `from` with nominal radius r is still heard at `to`
func heard(from: Vector2, r: float, to: Vector2) -> bool:
	var lf: int = World.level(from.y)
	var lt: int = World.level(to.y)
	var t2: Vector2 = to if lf == lt else Vector2(to.x, to.y - float(UNDER) * lt + float(UNDER) * lf)
	var d: float = from.distance_to(t2)
	if d >= r:
		return false
	return d < r * sound_pass(from, to)

## straight walkable line (no walls, solid tiles)
func walk_clear(ax: float, ay: float, bx: float, by: float) -> bool:
	var cx: int = floori(ax)
	var cy: int = floori(ay)
	var ex: int = floori(bx)
	var ey: int = floori(by)
	var dx: float = bx - ax
	var dy: float = by - ay
	var sx: int = 1 if dx > 0.0 else -1
	var sy: int = 1 if dy > 0.0 else -1
	var tdx: float = absf(1.0 / dx) if absf(dx) > 0.00001 else 1e20
	var tdy: float = absf(1.0 / dy) if absf(dy) > 0.00001 else 1e20
	var tmx: float = ((cx + (1 if dx > 0.0 else 0)) - ax) / dx if absf(dx) > 0.00001 else 1e20
	var tmy: float = ((cy + (1 if dy > 0.0 else 0)) - ay) / dy if absf(dy) > 0.00001 else 1e20
	var guard := 0
	while (cx != ex or cy != ey) and guard < 80:
		guard += 1
		if tmx < tmy:
			var nx: int = cx + sx
			if edge_blocks(maxi(cx, nx), cy, 1) or tile_blocked(nx, cy):
				return false
			cx = nx
			tmx += tdx
		else:
			var ny: int = cy + sy
			if edge_blocks(cx, maxi(cy, ny), 0) or tile_blocked(cx, ny):
				return false
			cy = ny
			tmy += tdy
	return true

# ------------------------------------------------------------------ mutation
func _touch(c: Chunk, tiles_changed: bool) -> void:
	c.touched = true
	if tiles_changed:
		c.modified = true

func notify(x: int, y: int) -> void:
	ev_tiles.append(Vector2i(x, y))

func set_ground(x: int, y: int, g: int) -> void:
	var c: Chunk = chunk_at(x, y)
	if c == null:
		return
	c.ground[idx(x, y)] = g
	_touch(c, true)
	ev_ground.append(Vector2i(c.cx, c.cy))

## every roof the player builds shares one building id: stand under any of it and it is cut away
const PLAYER_BLD := 0x30000001

func set_roof(x: int, y: int, uid: int) -> void:
	var c: Chunk = chunk_at(x, y)
	if c == null:
		return
	c.bld[idx(x, y)] = uid
	c.roof[idx(x, y)] = 0
	_touch(c, true)
	notify(x, y)

func set_obj(x: int, y: int, cell: int) -> void:
	var c: Chunk = chunk_at(x, y)
	if c == null:
		return
	c.obj[idx(x, y)] = cell
	_touch(c, true)
	notify(x, y)

func set_wall(x: int, y: int, side: int, w: int, st: int = 0) -> void:
	var c: Chunk = chunk_at(x, y)
	if c == null:
		return
	var i: int = idx(x, y)
	if side == 0:
		c.wall_n[i] = w
		c.st_n[i] = st
	else:
		c.wall_w[i] = w
		c.st_w[i] = st
	c.edge_hp.erase(i * 2 + side)
	_touch(c, true)
	notify(x, y)

func set_edge_state(x: int, y: int, side: int, st: int) -> void:
	var c: Chunk = chunk_at(x, y)
	if c == null:
		return
	var i: int = idx(x, y)
	if side == 0:
		c.st_n[i] = st
	else:
		c.st_w[i] = st
	_touch(c, true)
	notify(x, y)

## anchor tile of the (possibly multi-tile) object occupying x,y
func anchor_of(x: int, y: int) -> Vector2i:
	var cell: int = obj(x, y)
	if cell == 0:
		return Vector2i(x, y)
	var off: Vector2i = Defs.part_offset(Defs.o_id(cell), Defs.o_rot(cell), Defs.o_part(cell))
	return Vector2i(x - off.x, y - off.y)

func remove_object(x: int, y: int) -> void:
	var cell: int = obj(x, y)
	if cell == 0:
		return
	var id: int = Defs.o_id(cell)
	var rot: int = Defs.o_rot(cell)
	var a: Vector2i = anchor_of(x, y)
	var fs: Vector2i = Defs.obj_size(id, rot)
	for j in range(fs.y):
		for i in range(fs.x):
			if Defs.o_id(obj(a.x + i, a.y + j)) == id:
				set_obj(a.x + i, a.y + j, 0)
	var c: Chunk = chunk_at(a.x, a.y)
	if c != null:
		var ai: int = idx(a.x, a.y)
		# spill container contents on the ground
		if c.containers.has(ai):
			for it in c.containers[ai]:
				drop_item(a.x, a.y, it)
			c.containers.erase(ai)
		c.ents.erase(ai)
		c.obj_hp.erase(ai)

## damage a barrier on an edge. returns true when something broke.
func damage_edge(x: int, y: int, side: int, dmg: float) -> bool:
	var c: Chunk = chunk_at(x, y)
	if c == null:
		return false
	var i: int = idx(x, y)
	var w: int = c.wall_n[i] if side == 0 else c.wall_w[i]
	if w == 0:
		return false
	var st: int = c.st_n[i] if side == 0 else c.st_w[i]
	var key: int = i * 2 + side
	var planks: int = (st & Defs.ES_PLANK_MASK) >> Defs.ES_PLANK_SHIFT
	var shape: int = w & 3
	var max_hp: float = float(Defs.WALL_MATS[w >> 2][2])
	if planks > 0:
		max_hp = Defs.PLANK_HP
	elif shape == Defs.WS_DOOR:
		max_hp = Defs.DOOR_HP if Defs.WALL_MATS[w >> 2][0] < Defs.WT_PICKET else 50.0
	elif shape == Defs.WS_WINDOW:
		if (st & (Defs.ES_BROKEN | Defs.ES_OPEN)) != 0:
			return false
		max_hp = Defs.WINDOW_HP
	var hp: float = c.edge_hp.get(key, max_hp)
	hp -= dmg
	_touch(c, false)
	if hp > 0.0:
		c.edge_hp[key] = hp
		return false
	c.edge_hp.erase(key)
	if planks > 0:
		st = (st & ~Defs.ES_PLANK_MASK) | ((planks - 1) << Defs.ES_PLANK_SHIFT)
		set_edge_state(x, y, side, st)
	elif shape == Defs.WS_DOOR or shape == Defs.WS_WINDOW:
		set_edge_state(x, y, side, (st | Defs.ES_BROKEN) & ~Defs.ES_LOCKED)
	else:
		set_wall(x, y, side, 0)
	return true

# ------------------------------------------------------------------ items & containers
func items_at(x: int, y: int) -> Array:
	var c: Chunk = chunk_at(x, y)
	if c == null:
		return []
	return c.items.get(idx(x, y), [])

func drop_item(x: int, y: int, it: Dictionary) -> void:
	var c: Chunk = chunk_at(x, y)
	if c == null:
		return
	var i: int = idx(x, y)
	if not c.items.has(i):
		c.items[i] = []
	Inv.add(c.items[i], it)
	c.touched = true
	notify(x, y)

func ground_items_changed(x: int, y: int) -> void:
	var c: Chunk = chunk_at(x, y)
	if c == null:
		return
	var i: int = idx(x, y)
	if c.items.has(i) and (c.items[i] as Array).is_empty():
		c.items.erase(i)
	c.touched = true
	notify(x, y)

## container contents for the object at x,y (rolled lazily, deterministic per tile)
func container_at(x: int, y: int) -> Array:
	var a: Vector2i = anchor_of(x, y)
	var c: Chunk = chunk_at(a.x, a.y)
	if c == null:
		return []
	var i: int = idx(a.x, a.y)
	if c.containers.has(i):
		return c.containers[i]
	var cell: int = c.obj[i]
	var d: Dictionary = Defs.obj(Defs.o_id(cell))
	var arr: Array = []
	var table: String = d.get("c", "")
	if table != "":
		var rng: RandomNumberGenerator = Rng.make(Rng.h2(a.x, a.y, seed_v + 977))
		arr = Loot.roll(table, c.btype.get(c.bld[i], ""), rng, hour, loot_mult)
	c.containers[i] = arr
	c.touched = true
	return arr

func has_container(x: int, y: int) -> bool:
	var cell: int = obj(x, y)
	if cell == 0:
		return false
	return Defs.obj(Defs.o_id(cell)).has("c")

func ent(x: int, y: int) -> Dictionary:
	var c: Chunk = chunk_at(x, y)
	if c == null:
		return {}
	return c.ents.get(idx(x, y), {})

func set_ent(x: int, y: int, e: Dictionary) -> void:
	var c: Chunk = chunk_at(x, y)
	if c == null:
		return
	if e.is_empty():
		c.ents.erase(idx(x, y))
	else:
		c.ents[idx(x, y)] = e
	c.touched = true

func add_blood(x: float, y: float) -> void:
	var c: Chunk = chunk_at(floori(x), floori(y))
	if c == null:
		return
	if c.blood.size() > 40:
		c.blood.pop_front()
	c.blood.append([x, y, randi() % 4])
	c.touched = true
	ev_ground.append(Vector2i(c.cx, c.cy))

# ------------------------------------------------------------------ streaming
func load_chunk(cx: int, cy: int) -> Chunk:
	var k := Vector2i(cx, cy)
	if chunks.has(k):
		return chunks[k]
	var c: Chunk = gen.gen_chunk(cx, cy)
	var data: Dictionary = {}
	if store.has(k):
		data = store[k]
		store.erase(k)
	elif store_loader.is_valid():
		data = store_loader.call(k)
	if not data.is_empty():
		c.load_data(data)
		if c.modified:
			c.map_px = WorldGen._minimap(c)
	if not c.modified and growth > 0.0:
		# nature takes the town back: only chunks the player never altered regrow
		gen.overgrow(c, hour / 24.0 * growth)
	chunks[k] = c
	explored[k] = c.map_px
	ev_loaded.append(c)
	return c

func unload_chunk(k: Vector2i) -> void:
	var c: Chunk = chunks.get(k)
	if c == null:
		return
	if on_unload.is_valid():
		on_unload.call(c)
	if c.touched or c.modified or c.spawned:
		store[k] = c.save_data()
	chunks.erase(k)
	if _lkey == k:
		_lc = null
		_lkey = Vector2i(999999, 999999)
	ev_unloaded.append(k)

## keep chunks within `radius` (in chunks) of the centre loaded. returns number still missing.
func stream(center: Vector2, radius: int, budget: int) -> int:
	var ccx: int = floori(center.x) >> 4
	var ccy: int = floori(center.y) >> 4
	var missing: Array = []
	for dy in range(-radius, radius + 1):
		for dx in range(-radius, radius + 1):
			var k := Vector2i(ccx + dx, ccy + dy)
			if not chunks.has(k):
				missing.append(k)
	if missing.size() > 0:
		missing.sort_custom(func(a, b): return (a - Vector2i(ccx, ccy)).length_squared() < (b - Vector2i(ccx, ccy)).length_squared())
		for i in range(mini(budget, missing.size())):
			load_chunk(missing[i].x, missing[i].y)
	var drop: Array = []
	for k in chunks.keys():
		if absi(k.x - ccx) > radius + 1 or absi(k.y - ccy) > radius + 1:
			drop.append(k)
	for k in drop:
		unload_chunk(k)
	return maxi(missing.size() - budget, 0)
