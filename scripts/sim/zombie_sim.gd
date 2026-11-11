class_name ZombieSim
extends RefCounted
## Zombie population: spawning per chunk, perception (sight + hearing), pathfinding,
## door / window breaching, attacks and the off-screen population store.

const R := 0.2
const DENSITY := [0.16, 0.7, 2.3, 4.6]      # per chunk by zone
const MAX_ACTIVE := 320

var sim: Sim
var list: Array[Zombie] = []
var _next_id := 1
var _grid: Dictionary = {}
var _frame := 0
var _path_budget := 0
var wander_t := 20.0

func _init(s: Sim) -> void:
	sim = s

# ------------------------------------------------------------------ population
func growth() -> float:
	var day: float = sim.hour / 24.0
	return 1.0 + clampf(day / 28.0, 0.0, 1.0) * 0.8

func spawn(pos: Vector2, kind: int = -1) -> Zombie:
	var z := Zombie.new()
	z.id = _next_id
	_next_id += 1
	z.pos = pos
	var r: float = randf()
	if kind < 0:
		kind = 0
		if r < 0.07: kind = 1
		elif r < 0.12: kind = 2
		elif r < 0.18: kind = 3
	_apply_kind(z, kind)
	z.look = [randi() % 4, randi() % 10, randi() % 6, randi() % 6]
	var a: float = randf() * TAU
	z.dir = Vector2(cos(a), sin(a))
	z.d8 = Iso.dir8(z.dir)
	z.think_t = randf() * 0.5
	list.append(z)
	return z

func _apply_kind(z: Zombie, kind: int) -> void:
	z.kind = kind
	z.hp = randf_range(70.0, 130.0)
	z.speed = randf_range(0.95, 1.35)
	match kind:
		1: z.speed = randf_range(1.9, 2.3)
		2:
			z.speed = randf_range(0.5, 0.7)
			z.hp *= 0.7
		3:
			z.hp *= 2.0
			z.speed = randf_range(0.85, 1.05)
	z.speed *= float(sim.settings.get("zspeed", 1.0))

func on_chunk_loaded(c: Chunk) -> void:
	for a in c.zombies:
		if list.size() >= MAX_ACTIVE:
			break
		var z: Zombie = Zombie.from_save(a)
		z.id = _next_id
		_next_id += 1
		var ang: float = randf() * TAU
		z.dir = Vector2(cos(ang), sin(ang))
		z.d8 = Iso.dir8(z.dir)
		z.think_t = randf() * 0.5
		list.append(z)
	c.zombies = []
	var mult: float = float(sim.settings.get("zombies", 1.0))
	if not c.spawned:
		c.spawned = true
		c.touched = true
		var dens: float = DENSITY[c.zone] * mult * growth()
		var n: int = int(dens) + (1 if randf() < dens - floorf(dens) else 0)
		_spawn_in_chunk(c, mini(n, 16))
	elif sim.settings.get("respawn", true) and sim.hour - c.last_hour > 36.0:
		# slow repopulation of areas the player left long ago
		var target: float = DENSITY[c.zone] * mult * growth() * 0.5
		var have: int = count_in_chunk(c.cx, c.cy)
		var add: int = int(minf(target - have, (sim.hour - c.last_hour) / 36.0))
		if add > 0:
			_spawn_in_chunk(c, add)

func _spawn_in_chunk(c: Chunk, n: int) -> void:
	var w: World = sim.world
	var tries: int = n * 8
	var made := 0
	while made < n and tries > 0:
		tries -= 1
		var lx: int = randi() % 16
		var ly: int = randi() % 16
		var x: int = c.cx * 16 + lx
		var y: int = c.cy * 16 + ly
		var i: int = ly * 16 + lx
		var g: int = c.ground[i]
		if g == Defs.G_VOID or Defs.ground_is_water(g) or c.obj[i] != 0:
			continue
		var p := Vector2(x + 0.5, y + 0.5)
		if p.distance_to(sim.safe_pos) < sim.safe_radius:
			continue
		if c.bld[i] != 0 and (c.bld[i] == sim.safe_bld or randf() < 0.55):
			continue
		if p.distance_to(sim.player.pos) < 14.0:
			continue
		spawn(p)
		made += 1

func count_in_chunk(cx: int, cy: int) -> int:
	var n := 0
	for z in list:
		if (floori(z.pos.x) >> 4) == cx and (floori(z.pos.y) >> 4) == cy:
			n += 1
	return n

## called by World just before a chunk is unloaded
func on_chunk_unload(c: Chunk) -> void:
	var keep: Array[Zombie] = []
	for z in list:
		if (floori(z.pos.x) >> 4) == c.cx and (floori(z.pos.y) >> 4) == c.cy:
			c.zombies.append(z.save())
			c.touched = true
		else:
			keep.append(z)
	list = keep
	c.last_hour = sim.hour

## zombies of a loaded chunk, serialised (for saving without unloading)
func serialized_in_chunk(cx: int, cy: int) -> Array:
	var out: Array = []
	for z in list:
		if (floori(z.pos.x) >> 4) == cx and (floori(z.pos.y) >> 4) == cy:
			out.append(z.save())
	return out

## a roaming pack arriving from outside the player's view
func spawn_wanderers() -> void:
	var p: Vector2 = sim.player.pos
	var w: World = sim.world
	var day: float = sim.hour / 24.0
	var n: int = int(randf_range(2.0, 4.0 + minf(day, 20.0) * 0.4) * float(sim.settings.get("zombies", 1.0)))
	for attempt in range(12):
		var a: float = randf() * TAU
		var c: Vector2 = p + Vector2(cos(a), sin(a)) * randf_range(30.0, 40.0)
		if w.tile_blocked(floori(c.x), floori(c.y)) or w.bld(floori(c.x), floori(c.y)) != 0:
			continue
		var dest: Vector2 = p + Vector2(randf_range(-14, 14), randf_range(-14, 14))
		for i in range(n):
			var q: Vector2 = c + Vector2(randf_range(-2.5, 2.5), randf_range(-2.5, 2.5))
			if w.tile_blocked(floori(q.x), floori(q.y)) or list.size() >= MAX_ACTIVE:
				continue
			var z: Zombie = spawn(q)
			z.state = Zombie.INVESTIGATE
			z.goal = dest + Vector2(randf_range(-3, 3), randf_range(-3, 3))
			z.has_goal = true
			z.give_up = 60.0
		return

# ------------------------------------------------------------------ queries
func count_threats(p: Vector2, r: float) -> int:
	var n := 0
	var r2: float = r * r
	for z in list:
		if z.seen and z.state != Zombie.DOWN and z.pos.distance_squared_to(p) < r2:
			n += 1
	return n

func in_radius(p: Vector2, r: float) -> Array:
	var out: Array = []
	var r2: float = r * r
	for z in list:
		if z.pos.distance_squared_to(p) < r2:
			out.append(z)
	return out

## zombies within range and facing cone (dot >= min_dot), nearest first
func in_cone(p: Vector2, facing: Vector2, rng: float, min_dot: float) -> Array:
	var out: Array = []
	for z in list:
		var d: Vector2 = z.pos - p
		var dist: float = d.length()
		if dist > rng + R:
			continue
		if dist > 0.35 and d.dot(facing) / dist < min_dot:
			continue
		out.append(z)
	out.sort_custom(func(a, b): return a.pos.distance_squared_to(p) < b.pos.distance_squared_to(p))
	return out

func nearest_in_cone(p: Vector2, facing: Vector2, rng: float, min_dot: float, need_los: bool = false) -> Zombie:
	var best: Zombie = null
	var bd := 1e9
	for z in list:
		var d: Vector2 = z.pos - p
		var dist: float = d.length()
		if dist > rng or dist >= bd:
			continue
		if dist > 0.35 and d.dot(facing) / dist < min_dot:
			continue
		if need_los and not sim.world.los(p.x, p.y, z.pos.x, z.pos.y):
			continue
		best = z
		bd = dist
	return best

func ray_hit(p: Vector2, dir: Vector2, rng: float) -> Zombie:
	var best: Zombie = null
	var bt := 1e9
	for z in list:
		var rel: Vector2 = z.pos - p
		var t: float = rel.dot(dir)
		if t < 0.0 or t > rng or t >= bt:
			continue
		if (rel - dir * t).length() > 0.42:
			continue
		if not sim.world.los(p.x, p.y, z.pos.x, z.pos.y):
			continue
		best = z
		bt = t
	return best

# ------------------------------------------------------------------ damage
func damage(z: Zombie, dmg: float, from: Vector2, kb: float, knockdown: bool, crit: bool) -> void:
	z.hp -= dmg
	z.flash = 0.18
	z.alert = 10.0
	sim.emit_fx("hit", z.pos, {"crit": crit})
	if randf() < (0.8 if crit else 0.4):
		sim.world.add_blood(z.pos.x + randf_range(-0.3, 0.3), z.pos.y + randf_range(-0.3, 0.3))
	if z.hp <= 0.0:
		kill(z)
		return
	var away: Vector2 = (z.pos - from).normalized()
	if kb > 0.0:
		z.pos = sim.world.move(z.pos, away * kb, R)
	if z.state != Zombie.DOWN:
		if knockdown:
			z.state = Zombie.DOWN
			z.t = randf_range(1.6, 2.8)
			z.anim = "z_fall"
			z.anim_t = 0.0
		else:
			z.state = Zombie.STAGGER
			z.t = 0.38
			z.anim = "z_hit"
			z.anim_t = 0.0
	z.goal = sim.player.pos
	z.has_goal = true

func kill(z: Zombie) -> void:
	list.erase(z)
	var w: World = sim.world
	var c: Chunk = w.chunk_at(floori(z.pos.x), floori(z.pos.y))
	if c != null:
		c.corpses.append({"x": z.pos.x, "y": z.pos.y, "d": z.d8, "l": z.look, "h": sim.hour})
		c.touched = true
		w.notify(floori(z.pos.x), floori(z.pos.y))
	w.add_blood(z.pos.x, z.pos.y)
	sim.player.kills += 1
	sim.emit_fx("zdie", z.pos)

# ------------------------------------------------------------------ update
func sight_range() -> float:
	var p: Player = sim.player
	var light: float = sim.daylight()
	var r: float = lerpf(6.0, 14.0, light)
	if p.sneaking:
		r *= 0.6 - p.skill_level("sneaking") * 0.03
		var cell: int = sim.world.obj(floori(p.pos.x), floori(p.pos.y))
		if cell != 0 and Defs.obj(Defs.o_id(cell)).has("slow"):
			r *= 0.7
	if p.running: r *= 1.15
	if p.light_on and light < 0.4: r *= 1.35
	r *= 1.0 - float(sim.weather["fog"]) * 0.4
	r *= 1.0 - float(sim.weather["rain"]) * 0.15
	return maxf(r, 2.0)

func update(dt: float) -> void:
	_frame += 1
	_path_budget = 3
	var p: Player = sim.player
	var sr: float = sight_range()
	# spatial hash for separation (near zombies only)
	_grid.clear()
	for z in list:
		if z.pos.distance_squared_to(p.pos) < 400.0:
			var key: int = (floori(z.pos.x) & 0xFFFF) | ((floori(z.pos.y) & 0xFFFF) << 16)
			if _grid.has(key):
				(_grid[key] as Array).append(z)
			else:
				_grid[key] = [z]
	var i: int = list.size() - 1
	while i >= 0:
		if i < list.size():
			var z: Zombie = list[i]
			var d2: float = z.pos.distance_squared_to(p.pos)
			if d2 > 900.0:
				if (z.id + _frame) % 4 == 0:
					_update_z(z, dt * 4.0, sr, false)
			else:
				_update_z(z, dt, sr, d2 < 400.0)
				if (z.id + _frame) % 5 == 0:
					_update_seen(z, d2)
		i -= 1
	wander_t -= dt
	if wander_t <= 0.0:
		wander_t = randf_range(35.0, 70.0)
		var day: float = sim.hour / 24.0
		if randf() < 0.22 + minf(day, 20.0) * 0.015:
			spawn_wanderers()

func _update_z(z: Zombie, dt: float, sr: float, near: bool) -> void:
	var p: Player = sim.player
	var w: World = sim.world
	z.anim_t += dt
	z.flash = maxf(0.0, z.flash - dt)
	z.atk_cd = maxf(0.0, z.atk_cd - dt)
	if not w.is_loaded(floori(z.pos.x), floori(z.pos.y)):
		return
	match z.state:
		Zombie.DOWN:
			z.t -= dt
			if z.t <= 0.0:
				z.state = Zombie.STAGGER
				z.t = 0.7
				z.anim = "z_fall"
				z.anim_t = 0.0
			return
		Zombie.STAGGER:
			z.t -= dt
			if z.t <= 0.0:
				z.state = Zombie.CHASE if z.alert > 0.0 else Zombie.IDLE
			return
		Zombie.CLIMB:
			z.t -= dt
			if z.t <= 0.0:
				if not w.blocked(z.climb_to.x, z.climb_to.y, R):
					z.pos = z.climb_to
				z.state = Zombie.DOWN if randf() < 0.4 else Zombie.STAGGER
				z.t = 0.9
				z.anim = "z_fall" if z.state == Zombie.DOWN else "z_hit"
				z.anim_t = 0.0
			return
		Zombie.ATTACK:
			z.t -= dt
			if z.t <= 0.0:
				var d: float = z.pos.distance_to(p.pos)
				if d < 1.0 and p.alive and w.los(z.pos.x, z.pos.y, p.pos.x, p.pos.y):
					p.take_zombie_hit(z)
				z.atk_cd = 1.15
				z.state = Zombie.CHASE
			return
		Zombie.THUMP:
			z.t -= dt
			z.alert -= dt
			if z.t <= 0.0:
				z.t = 0.95
				var e: Vector3i = z.thump
				if not w.edge_blocks(e.x, e.y, e.z) or (z.alert <= -6.0 and z.give_up <= 0.0):
					z.state = Zombie.CHASE if z.alert > 0.0 else Zombie.INVESTIGATE
					z.give_up = 8.0
				else:
					var broke: bool = w.damage_edge(e.x, e.y, e.z, randf_range(6.0, 11.0) * (2.0 if z.kind == 3 else 1.0))
					sim.emit_fx("thump", z.pos)
					sim.noise(z.pos, 9.0, true)
					z.anim = "z_attack"
					z.anim_t = 0.0
					if broke:
						sim.emit_fx("break", z.pos)
						if not w.edge_blocks(e.x, e.y, e.z):
							z.state = Zombie.CHASE if z.alert > 0.0 else Zombie.INVESTIGATE
							z.give_up = 10.0
						else:
							_try_climb(z, e)
			z.give_up = maxf(0.0, z.give_up - dt)
			# keep perceiving while thumping
			z.think_t -= dt
			if z.think_t <= 0.0:
				z.think_t = 0.5
				if _sees_player(z, sr):
					z.alert = 9.0
			return
	z.think_t -= dt
	if z.think_t <= 0.0:
		z.think_t = randf_range(0.3, 0.5)
		_think(z, sr)
	if z.state == Zombie.CHASE and z.atk_cd <= 0.0 and p.alive:
		var dp: float = z.pos.distance_to(p.pos)
		if dp < 0.85:
			z.state = Zombie.ATTACK
			z.t = 0.42
			z.anim = "z_attack"
			z.anim_t = 0.0
			z.dir = (p.pos - z.pos).normalized()
			z.d8 = Iso.dir8(z.dir)
			return
	if z.has_goal:
		_move(z, dt, near)
		z.anim = "z_crawl" if z.kind == 2 else "z_walk"
	else:
		z.anim = "z_crawl" if z.kind == 2 else "z_idle"
	if z.state == Zombie.CHASE:
		z.moan_t -= dt
		if z.moan_t <= 0.0:
			z.moan_t = randf_range(2.5, 5.0)
			sim.noise(z.pos, 7.0, true)
			if near:
				sim.emit_fx("groan", z.pos)

func _sees_player(z: Zombie, sr: float) -> bool:
	var p: Player = sim.player
	if not p.alive:
		return false
	var to: Vector2 = p.pos - z.pos
	var d: float = to.length()
	if d > sr:
		return false
	if d > 2.2 and z.dir.dot(to) / d < -0.25:
		return false
	return sim.world.los(z.pos.x, z.pos.y, p.pos.x, p.pos.y)

func _think(z: Zombie, sr: float) -> void:
	var p: Player = sim.player
	if _sees_player(z, sr):
		z.alert = 9.0
		z.goal = p.pos
		z.has_goal = true
		if z.state != Zombie.CHASE:
			z.state = Zombie.CHASE
			z.repath_t = 0.0
			z.path = PackedVector2Array()
			z.moan_t = randf_range(0.2, 1.5)
		return
	z.alert -= 0.4
	if z.state == Zombie.CHASE:
		if z.alert <= 0.0:
			z.state = Zombie.INVESTIGATE
			z.give_up = 10.0
		return
	# hearing
	var best_score := 0.0
	var best_pos := Vector2.ZERO
	for n in sim.noises:
		var np: Vector2 = n[0]
		var nr: float = n[1]
		if n[3] and z.state >= Zombie.INVESTIGATE:
			continue
		var d: float = np.distance_to(z.pos)
		if d < nr and nr - d > best_score:
			best_score = nr - d
			best_pos = np
	if best_score > 0.0:
		z.goal = best_pos + Vector2(randf_range(-1.2, 1.2), randf_range(-1.2, 1.2))
		z.has_goal = true
		if z.state != Zombie.INVESTIGATE:
			z.path = PackedVector2Array()
			z.repath_t = 0.0
		z.state = Zombie.INVESTIGATE
		z.give_up = 14.0
		return
	if z.state == Zombie.INVESTIGATE:
		z.give_up -= 0.4
		if z.give_up <= 0.0 or z.pos.distance_to(z.goal) < 0.9:
			z.state = Zombie.IDLE
			z.has_goal = false
			z.path = PackedVector2Array()
	elif z.state == Zombie.WANDER:
		z.give_up -= 0.4
		if z.give_up <= 0.0 or z.pos.distance_to(z.goal) < 0.7:
			z.state = Zombie.IDLE
			z.has_goal = false
	elif randf() < 0.035:
		var g: Vector2 = z.pos + Vector2(randf_range(-4, 4), randf_range(-4, 4))
		if sim.world.walk_clear(z.pos.x, z.pos.y, g.x, g.y):
			z.goal = g
			z.has_goal = true
			z.state = Zombie.WANDER
			z.give_up = 8.0

func _move(z: Zombie, dt: float, near: bool) -> void:
	var w: World = sim.world
	var sp: float = z.speed * (0.45 if z.state == Zombie.WANDER else (0.8 if z.state == Zombie.INVESTIGATE else 1.0))
	var target: Vector2 = z.goal
	while z.path_i < z.path.size() and z.pos.distance_to(z.path[z.path_i]) < 0.4:
		z.path_i += 1
	z.repath_t -= dt
	if z.path_i < z.path.size():
		target = z.path[z.path_i]
		# drop the path when the goal has moved far from where it led
		if z.repath_t <= 0.0 and z.path[z.path.size() - 1].distance_to(z.goal) > 2.5:
			z.path = PackedVector2Array()
	elif z.state != Zombie.WANDER and not w.walk_clear(z.pos.x, z.pos.y, z.goal.x, z.goal.y):
		if z.repath_t <= 0.0 and _path_budget > 0:
			_path_budget -= 1
			z.repath_t = randf_range(1.2, 2.2)
			z.path = Pathfinder.find(w, floori(z.pos.x), floori(z.pos.y), floori(z.goal.x), floori(z.goal.y), 600, 14.0)
			z.path_i = 0
			if z.path.size() > 0:
				target = z.path[0]
	var to: Vector2 = target - z.pos
	var dist: float = to.length()
	if dist < 0.05:
		return
	var dv: Vector2 = to / dist
	z.dir = z.dir.lerp(dv, minf(1.0, dt * 8.0)).normalized()
	z.d8 = Iso.dir8(z.dir)
	var step: float = minf(sp * dt, dist)
	var np: Vector2 = w.move(z.pos, dv * step, R)
	var moved: float = np.distance_to(z.pos)
	z.pos = np
	if moved < step * 0.3:
		z.stuck_t += dt
		if z.stuck_t > 0.3:
			z.stuck_t = 0.0
			_blocked(z, dv)
	else:
		z.stuck_t = 0.0
	if near:
		_separate(z)

func _blocked(z: Zombie, dv: Vector2) -> void:
	var w: World = sim.world
	var tx: int = floori(z.pos.x)
	var ty: int = floori(z.pos.y)
	var cands: Array = []
	if absf(dv.x) > 0.25:
		cands.append(Vector3i(tx + 1, ty, 1) if dv.x > 0.0 else Vector3i(tx, ty, 1))
	if absf(dv.y) > 0.25:
		cands.append(Vector3i(tx, ty + 1, 0) if dv.y > 0.0 else Vector3i(tx, ty, 0))
	if absf(dv.y) > absf(dv.x):
		cands.reverse()
	for e in cands:
		var ev: Vector3i = e
		if not w.edge_blocks(ev.x, ev.y, ev.z):
			continue
		var wid: int = w.wall(ev.x, ev.y, ev.z)
		var shape: int = wid & 3
		var tex: int = Defs.WALL_MATS[wid >> 2][0]
		var st: int = w.edge_state(ev.x, ev.y, ev.z)
		var planks: bool = (st & Defs.ES_PLANK_MASK) != 0
		if z.state == Zombie.WANDER:
			break
		if not planks and ((shape == Defs.WS_WINDOW and (st & (Defs.ES_BROKEN | Defs.ES_OPEN)) != 0) or (shape == Defs.WS_SOLID and (tex == Defs.WT_PICKET or tex == Defs.WT_STONE))):
			_try_climb(z, ev)
			return
		if shape == Defs.WS_DOOR or shape == Defs.WS_WINDOW or tex == Defs.WT_PLANK or tex >= Defs.WT_PICKET:
			z.state = Zombie.THUMP
			z.thump = ev
			z.t = 0.5
			z.give_up = 20.0
			return
	# blocked by furniture / terrain: forget the path and try again shortly
	z.path = PackedVector2Array()
	z.repath_t = 0.0
	if z.state == Zombie.WANDER:
		z.state = Zombie.IDLE
		z.has_goal = false

func _try_climb(z: Zombie, e: Vector3i) -> void:
	var tx: int = floori(z.pos.x)
	var ty: int = floori(z.pos.y)
	var dest: Vector2
	if e.z == 1:
		dest = Vector2((e.x - 1 if tx >= e.x else e.x) + 0.5, ty + 0.5)
	else:
		dest = Vector2(tx + 0.5, (e.y - 1 if ty >= e.y else e.y) + 0.5)
	if sim.world.tile_blocked(floori(dest.x), floori(dest.y)):
		z.path = PackedVector2Array()
		return
	z.state = Zombie.CLIMB
	z.t = 1.5
	z.climb_to = dest
	z.anim = "z_attack"
	z.anim_t = 0.0

func _separate(z: Zombie) -> void:
	var w: World = sim.world
	var tx: int = floori(z.pos.x)
	var ty: int = floori(z.pos.y)
	for oy in range(-1, 2):
		for ox in range(-1, 2):
			var key: int = ((tx + ox) & 0xFFFF) | (((ty + oy) & 0xFFFF) << 16)
			if not _grid.has(key):
				continue
			for o in _grid[key]:
				var oz: Zombie = o
				if oz == z or oz.state == Zombie.DOWN:
					continue
				var d: Vector2 = z.pos - oz.pos
				var l: float = d.length()
				if l < 0.42 and l > 0.001:
					z.pos = w.move(z.pos, d / l * (0.42 - l) * 0.5, R)
	# keep out of the player's body
	var p: Player = sim.player
	var dp: Vector2 = z.pos - p.pos
	var lp: float = dp.length()
	if lp < 0.44 and lp > 0.001 and p.alive:
		z.pos = w.move(z.pos, dp / lp * (0.44 - lp) * 0.7, R)
		p.pos = w.move(p.pos, -dp / lp * (0.44 - lp) * 0.3, Player.R)

## is this zombie inside the player's field of view (used for rendering fade and panic)
func _update_seen(z: Zombie, d2: float) -> void:
	var p: Player = sim.player
	if d2 > 380.0:
		z.seen = false
		return
	var to: Vector2 = z.pos - p.pos
	var d: float = sqrt(d2)
	if d > 3.0 and p.facing.dot(to) / d < -0.35:
		z.seen = false
		return
	var view: float = lerpf(5.5, 19.0, sim.daylight())
	if p.light_on: view = maxf(view, 10.0)
	if d > view and d > 2.5:
		z.seen = false
		return
	z.seen = sim.world.los(p.pos.x, p.pos.y, z.pos.x, z.pos.y)
