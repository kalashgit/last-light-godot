class_name Pathfinder
extends RefCounted
## Bounded A* over the tile grid (walls live on tile edges).
## Works inside a WIN x WIN window around the start so it can use flat arrays.

const WIN := 48
const HALF := 24

static var _g := PackedFloat32Array()
static var _f := PackedFloat32Array()
static var _parent := PackedInt32Array()
static var _state := PackedByteArray()      # 0 new, 1 open, 2 closed
static var _heap := PackedInt32Array()
static var _heap_n := 0
static var iterations := 0

static func _heap_push(n: int) -> void:
	if _heap_n >= _heap.size():
		_heap.resize(_heap.size() + 256)
	var i: int = _heap_n
	_heap[i] = n
	_heap_n += 1
	while i > 0:
		var p: int = (i - 1) >> 1
		if _f[_heap[p]] <= _f[_heap[i]]:
			break
		var t: int = _heap[p]
		_heap[p] = _heap[i]
		_heap[i] = t
		i = p

static func _heap_pop() -> int:
	var top: int = _heap[0]
	_heap_n -= 1
	_heap[0] = _heap[_heap_n]
	var i := 0
	while true:
		var l: int = i * 2 + 1
		var r: int = l + 1
		var m: int = i
		if l < _heap_n and _f[_heap[l]] < _f[_heap[m]]:
			m = l
		if r < _heap_n and _f[_heap[r]] < _f[_heap[m]]:
			m = r
		if m == i:
			break
		var t: int = _heap[m]
		_heap[m] = _heap[i]
		_heap[i] = t
		i = m
	return top

## cost of crossing from tile a to 4-neighbour b; < 0 means impossible.
## breach > 0 lets the path go through doors / windows / fences at that extra cost.
static func _step_cost(w: World, ax: int, ay: int, bx: int, by: int, breach: float) -> float:
	if w.tile_blocked(bx, by):
		return -1.0
	var ex: int = maxi(ax, bx) if ax != bx else ax
	var ey: int = ay if ax != bx else maxi(ay, by)
	var side: int = 1 if ax != bx else 0
	if not w.edge_blocks(ex, ey, side):
		return 1.0
	if breach <= 0.0:
		return -1.0
	var wid: int = w.wall(ex, ey, side)
	var shape: int = wid & 3
	if shape == Defs.WS_DOOR or shape == Defs.WS_WINDOW:
		return 1.0 + breach
	var tex: int = Defs.WALL_MATS[wid >> 2][0]
	if tex == Defs.WT_PICKET or tex == Defs.WT_STONE or tex == Defs.WT_HEDGE:
		return 1.0 + breach * 0.6
	if tex == Defs.WT_PLANK or tex == Defs.WT_CHAIN:
		return 1.0 + breach * 2.5
	return -1.0

## returns tile-centre waypoints from start (exclusive) to goal (inclusive); empty if none.
static func find(w: World, sx: int, sy: int, gx: int, gy: int, max_iter: int = 700, breach: float = 0.0) -> PackedVector2Array:
	var out := PackedVector2Array()
	if _g.size() == 0:
		_g.resize(WIN * WIN)
		_f.resize(WIN * WIN)
		_parent.resize(WIN * WIN)
		_state.resize(WIN * WIN)
		_heap.resize(512)
	var ox: int = sx - HALF
	var oy: int = sy - HALF
	# clamp goal into the window
	var tgx: int = clampi(gx, ox + 1, ox + WIN - 2)
	var tgy: int = clampi(gy, oy + 1, oy + WIN - 2)
	_state.fill(0)
	_heap_n = 0
	var start: int = HALF * WIN + HALF
	var goal: int = (tgy - oy) * WIN + (tgx - ox)
	if start == goal:
		return out
	_g[start] = 0.0
	_f[start] = 0.0
	_parent[start] = -1
	_state[start] = 1
	_heap_push(start)
	var best: int = start
	var best_h := 1e9
	var iters := 0
	var found := false
	while _heap_n > 0 and iters < max_iter:
		iters += 1
		var cur: int = _heap_pop()
		if _state[cur] == 2:
			continue
		_state[cur] = 2
		if cur == goal:
			found = true
			best = cur
			break
		var cx: int = cur % WIN
		var cy: int = cur / WIN
		var wx: int = cx + ox
		var wy: int = cy + oy
		var hcur: float = absf(float(tgx - wx)) + absf(float(tgy - wy))
		if hcur < best_h:
			best_h = hcur
			best = cur
		var c_e := -1.0
		var c_w := -1.0
		var c_s := -1.0
		var c_n := -1.0
		if cx < WIN - 1: c_e = _step_cost(w, wx, wy, wx + 1, wy, breach)
		if cx > 0: c_w = _step_cost(w, wx, wy, wx - 1, wy, breach)
		if cy < WIN - 1: c_s = _step_cost(w, wx, wy, wx, wy + 1, breach)
		if cy > 0: c_n = _step_cost(w, wx, wy, wx, wy - 1, breach)
		for k in range(8):
			var dx := 0
			var dy := 0
			var cost := -1.0
			match k:
				0:
					dx = 1; cost = c_e
				1:
					dx = -1; cost = c_w
				2:
					dy = 1; cost = c_s
				3:
					dy = -1; cost = c_n
				4:
					dx = 1; dy = 1
					if c_e == 1.0 and c_s == 1.0 and _step_cost(w, wx + 1, wy, wx + 1, wy + 1, 0.0) == 1.0 and _step_cost(w, wx, wy + 1, wx + 1, wy + 1, 0.0) == 1.0: cost = 1.414
				5:
					dx = -1; dy = 1
					if c_w == 1.0 and c_s == 1.0 and _step_cost(w, wx - 1, wy, wx - 1, wy + 1, 0.0) == 1.0 and _step_cost(w, wx, wy + 1, wx - 1, wy + 1, 0.0) == 1.0: cost = 1.414
				6:
					dx = 1; dy = -1
					if c_e == 1.0 and c_n == 1.0 and _step_cost(w, wx + 1, wy, wx + 1, wy - 1, 0.0) == 1.0 and _step_cost(w, wx, wy - 1, wx + 1, wy - 1, 0.0) == 1.0: cost = 1.414
				7:
					dx = -1; dy = -1
					if c_w == 1.0 and c_n == 1.0 and _step_cost(w, wx - 1, wy, wx - 1, wy - 1, 0.0) == 1.0 and _step_cost(w, wx, wy - 1, wx - 1, wy - 1, 0.0) == 1.0: cost = 1.414
			if cost < 0.0:
				continue
			var nx: int = cx + dx
			var ny: int = cy + dy
			if nx < 0 or ny < 0 or nx >= WIN or ny >= WIN:
				continue
			var ni: int = ny * WIN + nx
			if _state[ni] == 2:
				continue
			var ng: float = _g[cur] + cost
			if _state[ni] == 0 or ng < _g[ni]:
				_g[ni] = ng
				var hx: float = absf(float(tgx - (nx + ox)))
				var hy: float = absf(float(tgy - (ny + oy)))
				_f[ni] = ng + maxf(hx, hy) + minf(hx, hy) * 0.414
				_parent[ni] = cur
				_state[ni] = 1
				_heap_push(ni)
	iterations = iters
	if not found and best == start:
		return out
	var node: int = best
	var rev: Array = []
	while node != start and node >= 0:
		rev.append(node)
		node = _parent[node]
	for i in range(rev.size() - 1, -1, -1):
		var n: int = rev[i]
		out.append(Vector2((n % WIN) + ox + 0.5, (n / WIN) + oy + 0.5))
	return out
