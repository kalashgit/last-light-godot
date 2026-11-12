class_name Vehicle
extends RefCounted
## A car while it is being driven. Parked cars are ordinary multi-tile world objects;
## getting in lifts the object out of the chunk into one of these, getting out puts it back.
## Headings follow object rotation: 0 = +y, 1 = +x, 2 = -y, 3 = -x.

const DIRS := [Vector2(0, 1), Vector2(1, 0), Vector2(0, -1), Vector2(-1, 0)]
const TANK := 12.0

var sim: Sim
var pos := Vector2.ZERO          # centre of the 2x4 footprint
var heading := 0
var speed := 0.0                 # tiles per second along the heading (negative = reversing)
var ent: Dictionary = {}         # fuel, eng, bat, key, hot, sv ...
var trunk: Array = []
var tint_key := Vector2i.ZERO    # original anchor: keeps the paint colour
var lights := true
var _turn_cd := 0.0
var _noise_t := 0.0

static func car_ent(sim: Sim, ax: int, ay: int) -> Dictionary:
	var w: World = sim.world
	var e: Dictionary = w.ent(ax, ay)
	if e.is_empty():
		e = {"k": "car", "fuel": Rng.h2(ax, ay, sim.seed_v + 55) % 7}
		w.set_ent(ax, ay, e)
	if not e.has("eng"):
		var hv: int = Rng.h2(ax, ay, sim.seed_v + 57)
		e["eng"] = 0.35 + float(hv % 60) / 100.0
		e["bat"] = 0 if (hv >> 8) % 100 < 22 else 1
		e["key"] = 1 if (hv >> 16) % 100 < 30 else 0
		e["hot"] = 0
		e["tire"] = 0.5 + float((hv >> 4) % 50) / 100.0
	return e

func size() -> Vector2:
	return Vector2(2, 4) if heading % 2 == 0 else Vector2(4, 2)

func anchor_f() -> Vector2:
	return pos - size() * 0.5

func _blocked_at(p: Vector2) -> int:
	# 0 free, 1 soft (fence: smash through), 2 solid
	var w: World = sim.world
	var a: Vector2 = p - size() * 0.5
	var x0: int = floori(a.x + 0.12)
	var y0: int = floori(a.y + 0.12)
	var x1: int = floori(a.x + size().x - 0.12)
	var y1: int = floori(a.y + size().y - 0.12)
	var res := 0
	for y in range(y0, y1 + 1):
		for x in range(x0, x1 + 1):
			if w.tile_blocked(x, y) or Defs.ground_is_water(w.ground(x, y)):
				return 2
			for side in range(2):
				if (side == 1 and x == x0) or (side == 0 and y == y0):
					continue
				var wid: int = w.wall(x, y, side)
				if wid == 0 or not w.edge_blocks(x, y, side):
					continue
				if Defs.wall_is_fence(wid):
					res = 1
				else:
					return 2
	return res

func _smash_fences(p: Vector2) -> void:
	var w: World = sim.world
	var a: Vector2 = p - size() * 0.5
	for y in range(floori(a.y), floori(a.y + size().y) + 1):
		for x in range(floori(a.x), floori(a.x + size().x) + 1):
			for side in range(2):
				var wid: int = w.wall(x, y, side)
				if wid != 0 and Defs.wall_is_fence(wid):
					w.set_wall(x, y, side, 0)

func update(dt: float, move_screen: Vector2, braking: bool) -> void:
	var w: World = sim.world
	_turn_cd = maxf(0.0, _turn_cd - dt)
	var eng: float = ent.get("eng", 0.5)
	var has_fuel: bool = float(ent.get("fuel", 0.0)) > 0.0 and eng > 0.05
	var on_road: bool = Defs.ground_is_road(w.ground(floori(pos.x), floori(pos.y)))
	var vmax: float = (9.5 if on_road else 4.6) * (0.55 + eng * 0.45) * (0.7 + float(ent.get("tire", 1.0)) * 0.3)
	var want := 0.0
	if move_screen.length() > 0.25 and has_fuel and not braking:
		var wd: Vector2 = Iso.screen_dir_to_world(move_screen)
		var target: int = 0
		if absf(wd.x) > absf(wd.y):
			target = 1 if wd.x > 0.0 else 3
		else:
			target = 0 if wd.y > 0.0 else 2
		if target == heading:
			want = vmax
		elif target == (heading + 2) % 4:
			want = -vmax * 0.35
		elif _turn_cd <= 0.0 and absf(speed) > 0.4:
			# quarter turn, pivoting about the centre if the new footprint is clear
			var old: int = heading
			heading = target
			if _blocked_at(pos) == 2:
				heading = old
			else:
				speed = absf(speed) * 0.6
				_turn_cd = 0.4
				want = vmax
		else:
			want = vmax * 0.5
	var acc: float = 5.0 if absf(want) > absf(speed) else 7.0
	if braking: acc = 14.0
	speed = move_toward(speed, want, acc * dt)
	if absf(speed) > 0.01:
		var np: Vector2 = pos + DIRS[heading] * speed * dt
		var b: int = _blocked_at(np)
		if b == 2:
			if absf(speed) > 2.5:
				ent["eng"] = maxf(0.0, eng - absf(speed) * 0.012)
				sim.emit_fx("break", pos)
				sim.noise(pos, 22.0)
				sim.player.hurt(maxf(0.0, absf(speed) - 5.0) * 2.0, "Died in a crash")
				if absf(speed) > 6.0:
					sim.say("You hit hard. The engine does not like that.", Color(1.0, 0.7, 0.5))
			speed = -speed * 0.2
		else:
			if b == 1:
				_smash_fences(np)
				speed *= 0.75
				ent["eng"] = maxf(0.0, eng - 0.01)
				sim.emit_fx("break", pos)
			pos = np
		ent["fuel"] = maxf(0.0, float(ent.get("fuel", 0.0)) - absf(speed) * dt * 0.004)
		if float(ent["fuel"]) <= 0.0:
			sim.say("The engine dies. Out of fuel.", Color(1.0, 0.8, 0.5))
	# anything walking in front of a moving car
	if absf(speed) > 2.0:
		var half: Vector2 = size() * 0.5 + Vector2(0.25, 0.25)
		for z in sim.zombies.list.duplicate():
			var d: Vector2 = z.pos - pos
			if absf(d.x) < half.x and absf(d.y) < half.y:
				sim.zombies.damage(z, absf(speed) * 20.0, pos - DIRS[heading] * signf(speed), 1.2, true, false)
				ent["eng"] = maxf(0.0, float(ent["eng"]) - 0.004 * absf(speed))
				speed *= 0.9
	_noise_t -= dt
	if _noise_t <= 0.0 and has_fuel:
		_noise_t = 0.5
		sim.noise(pos, 10.0 + absf(speed) * 1.7)
		if absf(speed) > 0.5:
			sim.emit_fx("engine", pos)

# ------------------------------------------------------------------ enter / exit
static func enter(sim: Sim, ax: int, ay: int) -> Vehicle:
	var w: World = sim.world
	var cell: int = w.obj(ax, ay)
	var id: int = Defs.o_id(cell)
	var rot: int = Defs.o_rot(cell)
	var v := Vehicle.new()
	v.sim = sim
	v.heading = rot
	v.ent = car_ent(sim, ax, ay)
	v.tint_key = Vector2i(ax, ay)
	var c: Chunk = w.chunk_at(ax, ay)
	var ai: int = World.idx(ax, ay)
	if c.containers.has(ai):
		v.trunk = c.containers[ai]
		c.containers.erase(ai)
	c.ents.erase(ai)
	var fs: Vector2i = Defs.obj_size(id, rot)
	for j in range(fs.y):
		for i in range(fs.x):
			w.set_obj(ax + i, ay + j, 0)
	v.pos = Vector2(ax, ay) + Vector2(fs) * 0.5
	return v

## park: put the car back into the world as an object. returns false if there is no room here.
func park() -> bool:
	var w: World = sim.world
	var s: Vector2 = size()
	var a: Vector2 = anchor_f()
	var ax: int = roundi(a.x)
	var ay: int = roundi(a.y)
	for j in range(int(s.y)):
		for i in range(int(s.x)):
			if w.obj(ax + i, ay + j) != 0 or w.tile_blocked(ax + i, ay + j):
				return false
	for j in range(int(s.y)):
		for i in range(int(s.x)):
			w.set_obj(ax + i, ay + j, Defs.ocell(Defs.O_CAR, heading, j * int(s.x) + i))
	w.set_ent(ax, ay, ent)
	var c: Chunk = w.chunk_at(ax, ay)
	c.containers[World.idx(ax, ay)] = trunk
	c.touched = true
	pos = Vector2(ax, ay) + s * 0.5
	return true

func save() -> Dictionary:
	return {"pos": pos, "h": heading, "ent": ent, "trunk": trunk, "tk": tint_key}

static func from_save(sim: Sim, d: Dictionary) -> Vehicle:
	var v := Vehicle.new()
	v.sim = sim
	v.pos = d["pos"]
	v.heading = d["h"]
	v.ent = d["ent"]
	v.trunk = d.get("trunk", [])
	v.tint_key = d.get("tk", Vector2i.ZERO)
	return v
