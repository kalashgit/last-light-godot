class_name LotBuilder
extends RefCounted
## Builds one lot (building + yard) in a canonical orientation (street on the +v side)
## and then rotates it to face the real street. Output is a LotPlan stamped into chunks.

const E_NONE := 0
const E_WALL := 1
const E_DOOR := 2
const E_WINDOW := 3
const E_ARCH := 4
const E_PICKET := 5
const E_PICKET_GATE := 6
const E_CHAIN := 7
const E_CHAIN_GATE := 8
const E_HEDGE := 9
const E_STONE := 10

class LotPlan:
	var w: int
	var h: int
	var ground := PackedByteArray()
	var wall_n := PackedByteArray()
	var wall_w := PackedByteArray()
	var st_n := PackedByteArray()
	var st_w := PackedByteArray()
	var obj := PackedInt32Array()
	var inside := PackedByteArray()
	var roof := PackedByteArray()
	var bld_id := 0
	var btype := ""
	var spawn := Vector2i(-1, -1)     # a free indoor cell (lot coords)
	var hatch := Vector2i(-1, -1)     # cellar hatch cell (lot coords) or -1
	var cellar := Rect2i()            # cellar room footprint (lot coords)
	var corpses: Array = []           # [Vector2i cell, loot table]
	var zspawn: Array = []            # Vector2i cells of scripted zombies
	var blood: Array = []             # Vector2i cells with blood
	var stairs := Vector2i(-1, -1)    # staircase to the upper floor (lot coords) or -1
	var npcs: Array = []              # [Vector2i cell, hostile]

var cw: int
var ch: int
var rng: RandomNumberGenerator
var room := PackedInt32Array()
var floor_g := PackedByteArray()
var en := PackedByteArray()
var ew := PackedByteArray()
var lock_n := PackedByteArray()
var lock_w := PackedByteArray()
var occ := PackedByteArray()
var rooms: Array = []
var placements: Array = []
var ext_mat: int = Defs.WM_SIDING_WHITE
var flat_roof := false
var btype := "house"
var hatch_c := Vector2i(-1, -1)
var corpse_c: Array = []
var zspawn_c: Array = []
var blood_c: Array = []
var stairs_c := Vector2i(-1, -1)
var npc_c: Array = []
const F_LOCK := 1
const F_PLANK := 2
const F_BROKEN := 4

func _init(width: int, height: int, r: RandomNumberGenerator) -> void:
	cw = width
	ch = height
	rng = r
	room.resize(cw * ch)
	room.fill(-1)
	floor_g.resize(cw * ch)
	occ.resize(cw * ch)
	en.resize((cw + 1) * (ch + 1))
	ew.resize((cw + 1) * (ch + 1))
	lock_n.resize((cw + 1) * (ch + 1))
	lock_w.resize((cw + 1) * (ch + 1))

func inb(u: int, v: int) -> bool:
	return u >= 0 and v >= 0 and u < cw and v < ch

func room_at(u: int, v: int) -> int:
	if u < 0 or v < 0 or u >= cw or v >= ch:
		return -1
	return room[v * cw + u]

func add_room(r: Rect2i, type: String, floor_id: int, wall_mat: int) -> int:
	var idx: int = rooms.size()
	rooms.append({"r": r, "type": type, "floor": floor_id, "wall": wall_mat})
	for v in range(r.position.y, r.end.y):
		for u in range(r.position.x, r.end.x):
			room[v * cw + u] = idx
			floor_g[v * cw + u] = floor_id
	return idx

func set_floor(r: Rect2i, g: int) -> void:
	for v in range(maxi(r.position.y, 0), mini(r.end.y, ch)):
		for u in range(maxi(r.position.x, 0), mini(r.end.x, cw)):
			if room[v * cw + u] < 0:
				floor_g[v * cw + u] = g

## edge between two 4-adjacent cells
func set_edge(a: Vector2i, b: Vector2i, kind: int, locked: bool = false) -> void:
	if a.y != b.y:
		var i: int = maxi(a.y, b.y) * (cw + 1) + a.x
		en[i] = kind
		lock_n[i] = F_LOCK if locked else 0
	else:
		var i2: int = a.y * (cw + 1) + maxi(a.x, b.x)
		ew[i2] = kind
		lock_w[i2] = F_LOCK if locked else 0

func get_edge(a: Vector2i, b: Vector2i) -> int:
	if a.y != b.y:
		return en[maxi(a.y, b.y) * (cw + 1) + a.x]
	return ew[a.y * (cw + 1) + maxi(a.x, b.x)]

## create walls wherever room ids differ
func build_walls() -> void:
	for v in range(ch):
		for u in range(cw):
			var r: int = room[v * cw + u]
			if u + 1 < cw:
				var r2: int = room[v * cw + u + 1]
				if r != r2 and ew[v * (cw + 1) + u + 1] == E_NONE:
					ew[v * (cw + 1) + u + 1] = E_WALL
			if v + 1 < ch:
				var r3: int = room[(v + 1) * cw + u]
				if r != r3 and en[(v + 1) * (cw + 1) + u] == E_NONE:
					en[(v + 1) * (cw + 1) + u] = E_WALL
			if r >= 0:
				if u == 0: ew[v * (cw + 1)] = E_WALL
				if v == 0: en[u] = E_WALL

func _reserve(c: Vector2i) -> void:
	if inb(c.x, c.y) and occ[c.y * cw + c.x] == 0:
		occ[c.y * cw + c.x] = 2

## shared edges between two rooms: Array of [cell_a, cell_b]
func shared_edges(ra: int, rb: int) -> Array:
	var out: Array = []
	var R: Rect2i = rooms[ra]["r"]
	for v in range(R.position.y, R.end.y):
		for u in range(R.position.x, R.end.x):
			for d in [Vector2i(1, 0), Vector2i(-1, 0), Vector2i(0, 1), Vector2i(0, -1)]:
				if room_at(u + d.x, v + d.y) == rb:
					out.append([Vector2i(u, v), Vector2i(u + d.x, v + d.y)])
	return out

func door_between(ra: int, rb: int, kind: int = E_DOOR) -> bool:
	var se: Array = shared_edges(ra, rb)
	if se.is_empty():
		return false
	# prefer edges away from corners: pick from the middle third
	var pick: Array = se[clampi(se.size() / 2 + rng.randi_range(-1, 1), 0, se.size() - 1)]
	set_edge(pick[0], pick[1], kind)
	_reserve(pick[0])
	_reserve(pick[1])
	return true

## connect all rooms with doors (spanning tree from room `start`, plus a few loops)
func connect_rooms(start: int = 0, arch_types: Array = []) -> void:
	var seen: Array = [start]
	var queue: Array = [start]
	while queue.size() > 0:
		var a: int = queue.pop_front()
		var order: Array = range(rooms.size())
		for b in order:
			if seen.has(b):
				continue
			var kind: int = E_DOOR
			if arch_types.has(rooms[b]["type"]) and arch_types.has(rooms[a]["type"]):
				kind = E_ARCH
			if door_between(a, b, kind):
				seen.append(b)
				queue.append(b)

## exterior door on a side of a room. side: 0 N, 1 W, 2 S, 3 E. returns outside cell or (-1,-1)
func exterior_door(ri: int, side: int, locked: bool = false, kind: int = E_DOOR) -> Vector2i:
	var R: Rect2i = rooms[ri]["r"]
	var cands: Array = []
	match side:
		0:
			for u in range(R.position.x, R.end.x):
				if room_at(u, R.position.y - 1) < 0: cands.append([Vector2i(u, R.position.y), Vector2i(u, R.position.y - 1)])
		2:
			for u in range(R.position.x, R.end.x):
				if room_at(u, R.end.y) < 0: cands.append([Vector2i(u, R.end.y - 1), Vector2i(u, R.end.y)])
		1:
			for v in range(R.position.y, R.end.y):
				if room_at(R.position.x - 1, v) < 0: cands.append([Vector2i(R.position.x, v), Vector2i(R.position.x - 1, v)])
		3:
			for v in range(R.position.y, R.end.y):
				if room_at(R.end.x, v) < 0: cands.append([Vector2i(R.end.x - 1, v), Vector2i(R.end.x, v)])
	if cands.is_empty():
		return Vector2i(-1, -1)
	var lo: int = 1 if cands.size() > 2 else 0
	var pick: Array = cands[rng.randi_range(lo, cands.size() - 1 - lo)]
	set_edge(pick[0], pick[1], kind, locked)
	_reserve(pick[0])
	var outc: Vector2i = pick[1]
	if inb(outc.x, outc.y):
		occ[outc.y * cw + outc.x] = 2
	return outc

## windows on exterior walls. every `step` cells
func windows(step: int = 3, phase: int = 1) -> void:
	for v in range(ch):
		for u in range(cw):
			var r: int = room[v * cw + u]
			if r < 0:
				continue
			for d in [Vector2i(1, 0), Vector2i(-1, 0), Vector2i(0, 1), Vector2i(0, -1)]:
				if room_at(u + d.x, v + d.y) >= 0:
					continue
				var a := Vector2i(u, v)
				var b := Vector2i(u + d.x, v + d.y)
				if get_edge(a, b) != E_WALL:
					continue
				var along: int = u if d.x == 0 else v
				if posmod(along + phase, step) == 0:
					set_edge(a, b, E_WINDOW)

func _free(u: int, v: int, ri: int) -> bool:
	return inb(u, v) and room[v * cw + u] == ri and occ[v * cw + u] == 0

func _connected(ri: int) -> bool:
	var R: Rect2i = rooms[ri]["r"]
	var start := Vector2i(-1, -1)
	var total := 0
	for v in range(R.position.y, R.end.y):
		for u in range(R.position.x, R.end.x):
			if room[v * cw + u] == ri and occ[v * cw + u] != 1:
				total += 1
				if start.x < 0 or occ[v * cw + u] == 2:
					start = Vector2i(u, v)
	if total == 0:
		return false
	var seen: Dictionary = {start: true}
	var stack: Array = [start]
	var count := 0
	while stack.size() > 0:
		var c: Vector2i = stack.pop_back()
		count += 1
		for d in [Vector2i(1, 0), Vector2i(-1, 0), Vector2i(0, 1), Vector2i(0, -1)]:
			var n: Vector2i = c + d
			if seen.has(n) or not inb(n.x, n.y):
				continue
			if room[n.y * cw + n.x] != ri or occ[n.y * cw + n.x] == 1:
				continue
			seen[n] = true
			stack.append(n)
	return count == total

func _mark(au: int, av: int, w2: int, h2: int, val: int) -> void:
	for j in range(h2):
		for i in range(w2):
			occ[(av + j) * cw + au + i] = val

## raw placement (no checks). canonical rot.
func put(id: int, u: int, v: int, rot: int = 0) -> void:
	placements.append([id, u, v, rot])
	var fs: Vector2i = Defs.obj_size(id, rot)
	for j in range(fs.y):
		for i in range(fs.x):
			if inb(u + i, v + j):
				occ[(v + j) * cw + u + i] = 1

## place against a wall of the room with its back to the wall
func place_wall(ri: int, id: int, tries: int = 30) -> bool:
	var R: Rect2i = rooms[ri]["r"]
	var d: Dictionary = Defs.obj(id)
	var sz: Array = d["sz"]
	var tall: bool = int(d["h"]) > 40
	var solid: bool = float(d["solid"]) > 0.0
	for t in range(tries):
		var side: int = rng.randi() % 4
		var along: int = sz[0]
		var depth: int = sz[1]
		var au := 0
		var av := 0
		var w2 := 0
		var h2 := 0
		match side:
			0:
				au = R.position.x + rng.randi() % R.size.x
				av = R.position.y
				w2 = along
				h2 = depth
			1:
				au = R.position.x
				av = R.position.y + rng.randi() % R.size.y
				w2 = depth
				h2 = along
			2:
				au = R.position.x + rng.randi() % R.size.x
				av = R.end.y - depth
				w2 = along
				h2 = depth
			_:
				au = R.end.x - depth
				av = R.position.y + rng.randi() % R.size.y
				w2 = depth
				h2 = along
		var ok := true
		for j in range(h2):
			for i in range(w2):
				if not _free(au + i, av + j, ri):
					ok = false
		if not ok:
			continue
		# wall behind must be solid wall (windows allowed for low furniture)
		for k in range(along):
			var e := 0
			match side:
				0: e = en[av * (cw + 1) + au + k]
				1: e = ew[(av + k) * (cw + 1) + au]
				2: e = en[(av + h2) * (cw + 1) + au + k]
				_: e = ew[(av + k) * (cw + 1) + au + w2]
			if e != E_WALL and not (e == E_WINDOW and not tall):
				ok = false
		if not ok:
			continue
		_mark(au, av, w2, h2, 1)
		if solid and not _connected(ri):
			_mark(au, av, w2, h2, 0)
			continue
		placements.append([id, au, av, side])
		return true
	return false

## place anywhere free in the room (optionally away from walls)
func place_free(ri: int, id: int, inset: int = 1, rot: int = -1, tries: int = 20) -> Vector2i:
	var R: Rect2i = rooms[ri]["r"]
	if R.size.x <= inset * 2 or R.size.y <= inset * 2:
		return Vector2i(-1, -1)
	var solid: bool = float(Defs.obj(id)["solid"]) > 0.0
	for t in range(tries):
		var u: int = R.position.x + inset + rng.randi() % (R.size.x - inset * 2)
		var v: int = R.position.y + inset + rng.randi() % (R.size.y - inset * 2)
		var r2: int = rot if rot >= 0 else rng.randi() % 4
		var fs: Vector2i = Defs.obj_size(id, r2)
		var ok := true
		for j in range(fs.y):
			for i in range(fs.x):
				if not _free(u + i, v + j, ri):
					ok = false
		if not ok:
			continue
		_mark(u, v, fs.x, fs.y, 1)
		if solid and not _connected(ri):
			_mark(u, v, fs.x, fs.y, 0)
			continue
		placements.append([id, u, v, r2])
		return Vector2i(u, v)
	return Vector2i(-1, -1)

## place at an exact cell if free and connectivity is preserved
func place_at(ri: int, id: int, u: int, v: int, rot: int) -> bool:
	var fs: Vector2i = Defs.obj_size(id, rot)
	for j in range(fs.y):
		for i in range(fs.x):
			if not _free(u + i, v + j, ri):
				return false
	var solid: bool = float(Defs.obj(id)["solid"]) > 0.0
	_mark(u, v, fs.x, fs.y, 1)
	if solid and not _connected(ri):
		_mark(u, v, fs.x, fs.y, 0)
		return false
	placements.append([id, u, v, rot])
	return true

## yard placement (outside rooms)
func put_yard(id: int, u: int, v: int, rot: int = 0) -> bool:
	var fs: Vector2i = Defs.obj_size(id, rot)
	for j in range(fs.y):
		for i in range(fs.x):
			if not inb(u + i, v + j) or room[(v + j) * cw + u + i] >= 0 or occ[(v + j) * cw + u + i] != 0:
				return false
	put(id, u, v, rot)
	return true

## fence rectangle along the inside of a rect's border; gates given as cells on the border
func fence_rect(r: Rect2i, kind: int, gate_kind: int, gates: Array) -> void:
	for u in range(r.position.x, r.end.x):
		_fence_edge(Vector2i(u, r.position.y - 1), Vector2i(u, r.position.y), kind, gate_kind, gates)
		_fence_edge(Vector2i(u, r.end.y - 1), Vector2i(u, r.end.y), kind, gate_kind, gates)
	for v in range(r.position.y, r.end.y):
		_fence_edge(Vector2i(r.position.x - 1, v), Vector2i(r.position.x, v), kind, gate_kind, gates)
		_fence_edge(Vector2i(r.end.x - 1, v), Vector2i(r.end.x, v), kind, gate_kind, gates)

func _fence_edge(a: Vector2i, b: Vector2i, kind: int, gate_kind: int, gates: Array) -> void:
	if not inb(a.x, a.y) or not inb(b.x, b.y):
		return
	if room[a.y * cw + a.x] >= 0 or room[b.y * cw + b.x] >= 0:
		return
	if get_edge(a, b) != E_NONE:
		return
	var k: int = kind
	if gates.has(a) or gates.has(b):
		k = gate_kind
	set_edge(a, b, k)

## flag exterior windows/doors (or the doors of one room) of rooms >= base_room
func flag_openings(base_room: int, flag: int, only_room: int = -1, doors_only: bool = false) -> void:
	for v in range(ch + 1):
		for u in range(cw + 1):
			for which in range(2):
				var kind: int = en[v * (cw + 1) + u] if which == 0 else ew[v * (cw + 1) + u]
				if kind != E_DOOR and kind != E_WINDOW:
					continue
				if doors_only and kind != E_DOOR:
					continue
				var ra: int = room_at(u, v - 1) if which == 0 else room_at(u - 1, v)
				var rb: int = room_at(u, v)
				if only_room >= 0:
					if ra != only_room and rb != only_room:
						continue
				else:
					if (ra >= 0) == (rb >= 0):
						continue
					if maxi(ra, rb) < base_room:
						continue
				if which == 0:
					lock_n[v * (cw + 1) + u] = flag
				else:
					lock_w[v * (cw + 1) + u] = flag

## random walkable cell of a room (not furniture)
func free_cell(ri: int) -> Vector2i:
	var R: Rect2i = rooms[ri]["r"]
	for t in range(30):
		var u: int = R.position.x + rng.randi() % R.size.x
		var v: int = R.position.y + rng.randi() % R.size.y
		if room[v * cw + u] == ri and occ[v * cw + u] != 1:
			return Vector2i(u, v)
	return Vector2i(-1, -1)

# ------------------------------------------------------------------ finalize
func _map(u: int, v: int, facing: int) -> Vector2i:
	match facing:
		2: return Vector2i(u, v)
		3: return Vector2i(ch - 1 - v, u)
		0: return Vector2i(cw - 1 - u, ch - 1 - v)
	return Vector2i(v, cw - 1 - u)

static func _edge_wall(kind: int, mat: int) -> int:
	match kind:
		E_WALL: return Defs.wall(mat, Defs.WS_SOLID)
		E_DOOR: return Defs.wall(mat, Defs.WS_DOOR)
		E_WINDOW: return Defs.wall(mat, Defs.WS_WINDOW)
		E_ARCH: return Defs.wall(mat, Defs.WS_ARCH)
		E_PICKET: return Defs.wall(Defs.WM_PICKET, Defs.WS_SOLID)
		E_PICKET_GATE: return Defs.wall(Defs.WM_PICKET, Defs.WS_DOOR)
		E_CHAIN: return Defs.wall(Defs.WM_CHAIN, Defs.WS_SOLID)
		E_CHAIN_GATE: return Defs.wall(Defs.WM_CHAIN, Defs.WS_DOOR)
		E_HEDGE: return Defs.wall(Defs.WM_HEDGE, Defs.WS_SOLID)
		E_STONE: return Defs.wall(Defs.WM_STONE, Defs.WS_SOLID)
	return 0

## facing: side of the lot where the street is. 0 N, 1 E, 2 S, 3 W
func finalize(facing: int, bld_id: int) -> LotPlan:
	var p := LotPlan.new()
	var swap: bool = facing == 1 or facing == 3
	p.w = ch if swap else cw
	p.h = cw if swap else ch
	p.bld_id = bld_id
	p.btype = btype
	var n: int = p.w * p.h
	p.ground.resize(n)
	p.wall_n.resize(n)
	p.wall_w.resize(n)
	p.st_n.resize(n)
	p.st_w.resize(n)
	p.obj.resize(n)
	p.inside.resize(n)
	p.roof.resize(n)
	var froom := PackedInt32Array()
	froom.resize(n)
	froom.fill(-1)
	for v in range(ch):
		for u in range(cw):
			var m: Vector2i = _map(u, v, facing)
			var fi: int = m.y * p.w + m.x
			p.ground[fi] = floor_g[v * cw + u]
			var r: int = room[v * cw + u]
			froom[fi] = r
			if r >= 0:
				p.inside[fi] = 1
				if occ[v * cw + u] != 1 and p.spawn.x < 0:
					p.spawn = m
	# edges
	for v in range(ch + 1):
		for u in range(cw + 1):
			for which in range(2):
				var kind: int = en[v * (cw + 1) + u] if which == 0 else ew[v * (cw + 1) + u]
				if kind == E_NONE:
					continue
				var a: Vector2i
				var b: Vector2i
				if which == 0:
					a = _map(u, v - 1, facing)
					b = _map(u, v, facing)
				else:
					a = _map(u - 1, v, facing)
					b = _map(u, v, facing)
				var is_n: bool = a.y != b.y
				var c := Vector2i(a.x, maxi(a.y, b.y)) if is_n else Vector2i(maxi(a.x, b.x), a.y)
				if c.x < 0 or c.y < 0 or c.x >= p.w or c.y >= p.h:
					continue
				var fi2: int = c.y * p.w + c.x
				var mat: int = ext_mat
				var vis_room: int = froom[fi2]
				if vis_room >= 0:
					mat = rooms[vis_room]["wall"]
				var wid: int = _edge_wall(kind, mat)
				var fl: int = lock_n[v * (cw + 1) + u] if which == 0 else lock_w[v * (cw + 1) + u]
				var st: int = Defs.ES_LOCKED if (fl & F_LOCK) != 0 else 0
				if (fl & F_PLANK) != 0:
					st = (st & ~Defs.ES_LOCKED) | (2 << Defs.ES_PLANK_SHIFT)
				if (fl & F_BROKEN) != 0:
					st = Defs.ES_BROKEN
				if is_n:
					p.wall_n[fi2] = wid
					p.st_n[fi2] = st
				else:
					p.wall_w[fi2] = wid
					p.st_w[fi2] = st
	# story data
	if hatch_c.x >= 0:
		p.hatch = _map(hatch_c.x, hatch_c.y, facing)
		var cr := Rect2i(p.hatch.x - 2, p.hatch.y - 1, 5, 4)
		cr.position.x = clampi(cr.position.x, 1, maxi(p.w - 6, 1))
		cr.position.y = clampi(cr.position.y, 1, maxi(p.h - 5, 1))
		p.cellar = cr
		if not cr.has_point(p.hatch):
			p.hatch = Vector2i(-1, -1)
	for cc0 in corpse_c:
		p.corpses.append([_map(cc0[0].x, cc0[0].y, facing), cc0[1]])
	for zc in zspawn_c:
		p.zspawn.append(_map(zc.x, zc.y, facing))
	for bc in blood_c:
		p.blood.append(_map(bc.x, bc.y, facing))
	if stairs_c.x >= 0:
		p.stairs = _map(stairs_c.x, stairs_c.y, facing)
	for nc in npc_c:
		p.npcs.append([_map(nc[0].x, nc[0].y, facing), nc[1]])
	# objects
	var krot: int = [2, 1, 0, 3][facing]
	for pl in placements:
		var raw_id: int = pl[0]
		var id: int = raw_id & 0xFFFF
		var mature: bool = (raw_id & 0x10000) != 0
		var rot: int = pl[3]
		var fs: Vector2i = Defs.obj_size(id, rot)
		var frot: int = (rot + krot) % 4
		if Defs.obj(id).get("sym", 0) == 1 and fs == Vector2i(1, 1):
			frot = 0
		var cells: Array = []
		var minx := 99999
		var miny := 99999
		for j in range(fs.y):
			for i in range(fs.x):
				var m2: Vector2i = _map(int(pl[1]) + i, int(pl[2]) + j, facing)
				cells.append(m2)
				minx = mini(minx, m2.x)
				miny = mini(miny, m2.y)
		var ffs: Vector2i = Defs.obj_size(id, frot)
		for c2 in cells:
			var cc: Vector2i = c2
			if cc.x < 0 or cc.y < 0 or cc.x >= p.w or cc.y >= p.h:
				continue
			var part: int = (cc.y - miny) * ffs.x + (cc.x - minx)
			if mature:
				part = 3
			p.obj[cc.y * p.w + cc.x] = Defs.ocell(id, frot, part)
	# roof corner heights
	if not flat_roof:
		var cwid: int = p.w + 1
		var lvl := PackedByteArray()
		lvl.resize(cwid * (p.h + 1))
		for y in range(p.h + 1):
			for x in range(p.w + 1):
				var all_in := true
				for d in [Vector2i(-1, -1), Vector2i(0, -1), Vector2i(-1, 0), Vector2i(0, 0)]:
					var qx: int = x + d.x
					var qy: int = y + d.y
					if qx < 0 or qy < 0 or qx >= p.w or qy >= p.h or p.inside[qy * p.w + qx] == 0:
						all_in = false
				lvl[y * cwid + x] = 1 if all_in else 0
		for pass_i in range(2):
			var nl: PackedByteArray = lvl.duplicate()
			for y in range(1, p.h):
				for x in range(1, p.w):
					var cur: int = lvl[y * cwid + x]
					if cur != pass_i + 1:
						continue
					var mn := 99
					for d2 in [Vector2i(-1, 0), Vector2i(1, 0), Vector2i(0, -1), Vector2i(0, 1), Vector2i(-1, -1), Vector2i(1, 1), Vector2i(-1, 1), Vector2i(1, -1)]:
						mn = mini(mn, lvl[(y + d2.y) * cwid + x + d2.x])
					if mn >= pass_i + 1:
						nl[y * cwid + x] = pass_i + 2
			lvl = nl
		for y in range(p.h):
			for x in range(p.w):
				if p.inside[y * p.w + x] == 0:
					continue
				p.roof[y * p.w + x] = lvl[y * cwid + x] | (lvl[y * cwid + x + 1] << 2) | (lvl[(y + 1) * cwid + x + 1] << 4) | (lvl[(y + 1) * cwid + x] << 6)
	return p
