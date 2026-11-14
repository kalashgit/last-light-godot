class_name Vehicle
extends RefCounted
## A car while it is being driven. Parked cars are ordinary multi-tile world objects;
## getting in lifts the object out of the chunk into one of these, getting out puts it back.
## Headings follow object rotation: 0 = +y, 1 = +x, 2 = -y, 3 = -x.

const DIRS := [Vector2(0, 1), Vector2(1, 0), Vector2(0, -1), Vector2(-1, 0)]
const TANK := 12.0
## per type: road / off-road top speed (tiles/s), tank, fuel per tile, protection from attacks,
## engine noise radius, crash severity, whether it has an engine, whether it can tow
const TYPES := {
	Defs.O_CAR: {"n": "car", "road": 9.5, "off": 4.6, "tank": 12.0, "use": 0.004, "prot": 0.85, "noise": 10.0, "crash": 1.0, "motor": true, "tow": true},
	Defs.O_VAN: {"n": "van", "road": 8.0, "off": 4.0, "tank": 16.0, "use": 0.006, "prot": 0.9, "noise": 12.0, "crash": 0.85, "motor": true, "tow": true},
	Defs.O_PICKUP: {"n": "pickup", "road": 8.8, "off": 6.4, "tank": 14.0, "use": 0.005, "prot": 0.8, "noise": 12.0, "crash": 0.9, "motor": true, "tow": true},
	Defs.O_TRUCK: {"n": "box truck", "road": 7.2, "off": 3.4, "tank": 24.0, "use": 0.009, "prot": 0.9, "noise": 15.0, "crash": 0.7, "motor": true, "tow": true},
	Defs.O_BUS: {"n": "bus", "road": 6.4, "off": 2.8, "tank": 30.0, "use": 0.011, "prot": 0.95, "noise": 16.0, "crash": 0.6, "motor": true, "tow": false},
	Defs.O_AMBULANCE: {"n": "ambulance", "road": 8.6, "off": 4.0, "tank": 18.0, "use": 0.007, "prot": 0.9, "noise": 12.0, "crash": 0.85, "motor": true, "tow": true},
	Defs.O_POLICE_CAR: {"n": "police car", "road": 10.5, "off": 5.0, "tank": 14.0, "use": 0.005, "prot": 0.85, "noise": 10.0, "crash": 1.0, "motor": true, "tow": true},
	Defs.O_HATCHBACK: {"n": "hatchback", "road": 10.0, "off": 4.2, "tank": 10.0, "use": 0.0035, "prot": 0.8, "noise": 9.0, "crash": 1.1, "motor": true, "tow": false},
	Defs.O_WAGON: {"n": "station wagon", "road": 9.2, "off": 4.4, "tank": 14.0, "use": 0.0045, "prot": 0.85, "noise": 10.0, "crash": 1.0, "motor": true, "tow": true},
	Defs.O_SUV: {"n": "SUV", "road": 9.5, "off": 6.0, "tank": 18.0, "use": 0.006, "prot": 0.9, "noise": 11.0, "crash": 0.85, "motor": true, "tow": true},
	Defs.O_OFFROADER: {"n": "off-roader", "road": 9.0, "off": 7.6, "tank": 16.0, "use": 0.006, "prot": 0.7, "noise": 12.0, "crash": 0.9, "motor": true, "tow": true},
	Defs.O_UTILITY: {"n": "utility truck", "road": 8.0, "off": 5.0, "tank": 20.0, "use": 0.007, "prot": 0.9, "noise": 13.0, "crash": 0.8, "motor": true, "tow": true},
	Defs.O_DELIVERY: {"n": "delivery van", "road": 8.2, "off": 3.8, "tank": 16.0, "use": 0.0065, "prot": 0.9, "noise": 12.0, "crash": 0.85, "motor": true, "tow": true},
	Defs.O_TANKER: {"n": "fuel tanker", "road": 6.8, "off": 2.8, "tank": 30.0, "use": 0.011, "prot": 0.9, "noise": 15.0, "crash": 0.65, "motor": true, "tow": false},
	Defs.O_TOW_TRUCK: {"n": "tow truck", "road": 8.4, "off": 4.6, "tank": 20.0, "use": 0.008, "prot": 0.9, "noise": 13.0, "crash": 0.8, "motor": true, "tow": true},
	Defs.O_TRACTOR: {"n": "tractor", "road": 4.6, "off": 4.6, "tank": 10.0, "use": 0.005, "prot": 0.3, "noise": 16.0, "crash": 0.6, "motor": true, "tow": true},
	Defs.O_MOTORBIKE: {"n": "motorcycle", "road": 12.5, "off": 5.6, "tank": 5.0, "use": 0.002, "prot": 0.0, "noise": 13.0, "crash": 2.2, "motor": true, "tow": false},
	Defs.O_BICYCLE: {"n": "bicycle", "road": 5.6, "off": 3.4, "tank": 0.0, "use": 0.0, "prot": 0.0, "noise": 0.0, "crash": 1.6, "motor": false, "tow": false},
}
const TOWABLE := [Defs.O_CAR, Defs.O_VAN, Defs.O_PICKUP, Defs.O_CAR_WRECK, Defs.O_AMBULANCE, Defs.O_POLICE_CAR, Defs.O_HATCHBACK, Defs.O_WAGON, Defs.O_SUV, Defs.O_OFFROADER, Defs.O_DELIVERY]
## only a tow truck can haul these
const HEAVY_TOW := [Defs.O_TRUCK, Defs.O_BUS, Defs.O_UTILITY, Defs.O_TANKER, Defs.O_TRACTOR]

static func is_vehicle(id: int) -> bool:
	return TYPES.has(id)

static func tank_of(id: int) -> float:
	return float(TYPES.get(id, TYPES[Defs.O_CAR])["tank"])

var sim: Sim
var oid := Defs.O_CAR
var tow: Dictionary = {}         # a vehicle on the hitch: {"o", "ent", "trunk", "tk"}
var passengers: Array = []       # companions riding along (serialised survivors)
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
	var tid: int = Defs.o_id(w.obj(ax, ay))
	if tid == Defs.O_BICYCLE and not e.has("eng"):
		e.merge({"eng": 1.0, "bat": 1, "key": 1, "hot": 0, "tire": 0.6 + float(Rng.h2(ax, ay, 3) % 40) / 100.0, "win": 1.0, "lit": 0, "fuel": 0.0})
	if not e.has("eng"):
		var hv: int = Rng.h2(ax, ay, sim.seed_v + 57)
		e["eng"] = 0.35 + float(hv % 60) / 100.0
		e["bat"] = 0 if (hv >> 8) % 100 < 22 else 1
		e["key"] = 1 if (hv >> 16) % 100 < 30 else 0
		e["hot"] = 0
		e["tire"] = 0.5 + float((hv >> 4) % 50) / 100.0
	if not e.has("win"):
		e["win"] = 1.0
		e["lit"] = 1
	e["fuel"] = minf(float(e.get("fuel", 0.0)), tank_of(tid)) if TYPES.has(tid) else e.get("fuel", 0.0)
	return e

func spec() -> Dictionary:
	return TYPES.get(oid, TYPES[Defs.O_CAR])

func motor() -> bool:
	return bool(spec()["motor"])

func size() -> Vector2:
	return Vector2(Defs.obj_size(oid, heading))

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
	var sp: Dictionary = spec()
	var p: Player = sim.player
	var has_fuel: bool = (float(ent.get("fuel", 0.0)) > 0.0 and eng > 0.05) if motor() else p.endurance > 3.0
	var g_here: int = w.ground(floori(pos.x), floori(pos.y))
	var on_road: bool = Defs.ground_is_road(g_here) or g_here == Defs.G_CONCRETE or g_here == Defs.G_PLANK or g_here == Defs.G_SIDEWALK
	var tire: float = float(ent.get("tire", 1.0))
	var vmax: float = (float(sp["road"]) if on_road else float(sp["off"])) * (0.55 + eng * 0.45) * (0.7 + tire * 0.3)
	if tire < 0.15: vmax *= 0.35            # running on a flat
	if not tow.is_empty(): vmax *= 0.6
	if not on_road and sim.muddy(floori(pos.x), floori(pos.y)):
		vmax *= 0.6 if oid != Defs.O_PICKUP else 0.85      # a pickup copes with mud
	if sim.icy(floori(pos.x), floori(pos.y)):
		vmax *= 0.65
		_turn_cd = maxf(_turn_cd, 0.25)        # she slides before she turns
	if not motor():
		vmax *= 0.7 + p.endurance / 330.0
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
				crash(absf(speed))
			speed = -speed * 0.2
		else:
			if b == 1:
				_smash_fences(np)
				speed *= 0.75
				ent["eng"] = maxf(0.0, eng - 0.01)
				sim.emit_fx("break", pos)
			pos = np
		if motor():
			ent["fuel"] = maxf(0.0, float(ent.get("fuel", 0.0)) - absf(speed) * dt * float(sp["use"]) * (1.6 if not tow.is_empty() else 1.0))
			if float(ent["fuel"]) <= 0.0:
				sim.say("The engine dies. Out of fuel.", Color(1.0, 0.8, 0.5))
		else:
			p.endurance = maxf(0.0, p.endurance - absf(speed) * dt * 0.55 * (1.0 - p.skill_level("fitness") * 0.05))
			p.add_xp("fitness", absf(speed) * dt * 0.02)
	# anything walking in front of a moving car
	if absf(speed) > 2.0:
		var half: Vector2 = size() * 0.5 + Vector2(0.25, 0.25)
		for z in sim.zombies.list.duplicate():
			var d: Vector2 = z.pos - pos
			if absf(d.x) < half.x and absf(d.y) < half.y:
				sim.zombies.damage(z, absf(speed) * (20.0 if size().x + size().y > 3.0 else 9.0), pos - DIRS[heading] * signf(speed), 1.2, true, false)
				ent["eng"] = maxf(0.0, float(ent["eng"]) - 0.004 * absf(speed))
				speed *= 0.9
				if size().x + size().y <= 3.0 and absf(speed) > 2.0:
					# on two wheels a body in the road puts you on the ground
					speed = 0.0
					sim.say("You go over the handlebars.", Color(1.0, 0.6, 0.45))
					if not sim.settings.get("god", false):
						p.hurt(8.0, "Thrown from a bike")
						p.add_wound(Rng.pick_weighted(sim.rng, Player.HIT_WEIGHTS), "laceration", "the road")
					break
		for a in sim.animals.list.duplicate():
			var da: Vector2 = a.pos - pos
			if absf(da.x) < half.x and absf(da.y) < half.y:
				sim.animals.damage(a, absf(speed) * 15.0, pos)
	_noise_t -= dt
	if _noise_t <= 0.0 and has_fuel and motor():
		_noise_t = 0.5
		sim.noise(pos, (float(sp["noise"]) + absf(speed) * 1.7) * (1.8 if int(ent.get("muf", 1)) == 0 else 1.0))
		if absf(speed) > 0.5:
			sim.emit_fx("engine", pos)
	elif not motor() and absf(speed) > 0.5:
		_noise_t = maxf(_noise_t, 0.0)
		if _noise_t <= 0.0:
			_noise_t = 0.5
			sim.noise(pos, 2.5)

## the horn, or a police car's siren: heard a long way off
func horn() -> void:
	sim.noise(pos, 70.0 if oid == Defs.O_POLICE_CAR else 45.0)
	sim.emit_fx("alarm", pos)
	sim.say("The siren wails across the town." if oid == Defs.O_POLICE_CAR else "The horn carries a long way.", Color(1.0, 0.85, 0.6))

## a hard stop: hurt the driver and whatever parts take it
func crash(v: float) -> void:
	var sp: Dictionary = spec()
	var eng: float = ent.get("eng", 0.5)
	ent["eng"] = maxf(0.0, eng - v * 0.012 * (1.0 if motor() else 0.0))
	sim.emit_fx("break", pos)
	sim.noise(pos, 22.0 if motor() else 8.0)
	var harm: float = maxf(0.0, v - 5.0) * 2.0 * float(sp["crash"])
	if not motor(): harm = maxf(harm, (v - 2.5) * 3.0)
	if harm > 0.0:
		sim.player.hurt(harm, "Died in a crash")
		if harm > 12.0 and randf() < 0.35:
			sim.player.add_wound(Rng.pick_weighted(sim.rng, Player.HIT_WEIGHTS), "fracture" if harm > 22.0 else "laceration", "the crash")
	var parts: Array = []
	if randf() < 0.4 + v * 0.03:
		ent["tire"] = maxf(0.0, float(ent.get("tire", 1.0)) - 0.12 - v * 0.015)
		parts.append("tyres")
	if motor() and randf() < 0.25 + v * 0.03:
		ent["win"] = maxf(0.0, float(ent.get("win", 1.0)) - 0.34)
		parts.append("glass")
	if motor() and int(ent.get("lit", 1)) == 1 and randf() < 0.2 + v * 0.03:
		ent["lit"] = 0
		parts.append("headlights")
	if motor() and int(ent.get("muf", 1)) == 1 and randf() < 0.15 + v * 0.02:
		ent["muf"] = 0
		parts.append("the muffler — she is loud now")
	if v > 6.0 or parts.size() > 0:
		sim.say("You hit hard.%s" % ((" Damaged: " + ", ".join(parts) + ".") if parts.size() > 0 else ""), Color(1.0, 0.7, 0.5))

# ------------------------------------------------------------------ enter / exit
static func enter(sim: Sim, ax: int, ay: int) -> Vehicle:
	var w: World = sim.world
	var cell: int = w.obj(ax, ay)
	var id: int = Defs.o_id(cell)
	var rot: int = Defs.o_rot(cell)
	var v := Vehicle.new()
	v.sim = sim
	v.oid = id
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
	if not tow.is_empty() and not _tow_room(ax, ay):
		return false
	for j in range(int(s.y)):
		for i in range(int(s.x)):
			w.set_obj(ax + i, ay + j, Defs.ocell(oid, heading, j * int(s.x) + i))
	if not tow.is_empty():
		_drop_tow(ax, ay)
	w.set_ent(ax, ay, ent)
	var c: Chunk = w.chunk_at(ax, ay)
	c.containers[World.idx(ax, ay)] = trunk
	c.touched = true
	pos = Vector2(ax, ay) + s * 0.5
	return true

# ------------------------------------------------------------------ towing
## where a towed 2x4 sits: directly behind, same heading
func tow_anchor(ax: int, ay: int) -> Vector2i:
	var d: Vector2 = DIRS[heading]
	return Vector2i(ax - int(d.x) * 4, ay - int(d.y) * 4) if d.x + d.y > 0.0 else Vector2i(ax - int(d.x) * int(size().x), ay - int(d.y) * int(size().y))

func _tow_room(ax: int, ay: int) -> bool:
	var t: Vector2i = tow_anchor(ax, ay)
	var fs: Vector2i = Defs.obj_size(int(tow["o"]), heading)
	for j in range(fs.y):
		for i in range(fs.x):
			if sim.world.obj(t.x + i, t.y + j) != 0 or sim.world.tile_blocked(t.x + i, t.y + j):
				return false
	return true

func _drop_tow(ax: int, ay: int) -> void:
	var w: World = sim.world
	var t: Vector2i = tow_anchor(ax, ay)
	var tid: int = tow["o"]
	var fs: Vector2i = Defs.obj_size(tid, heading)
	for j in range(fs.y):
		for i in range(fs.x):
			w.set_obj(t.x + i, t.y + j, Defs.ocell(tid, heading, j * fs.x + i))
	if not (tow.get("ent", {}) as Dictionary).is_empty():
		w.set_ent(t.x, t.y, tow["ent"])
	var c: Chunk = w.chunk_at(t.x, t.y)
	c.containers[World.idx(t.x, t.y)] = tow.get("trunk", [])
	c.touched = true
	tow = {}

## a vehicle standing right behind this one (its anchor), or (-1,-1)
func behind() -> Vector2i:
	var w: World = sim.world
	var back: Vector2 = pos - DIRS[heading] * (size().y if heading % 2 == 0 else size().x) * 0.5 - DIRS[heading] * 1.2
	for k in range(3):
		var q: Vector2 = back - DIRS[heading] * float(k)
		var cell: int = w.obj(floori(q.x), floori(q.y))
		if cell != 0 and can_tow(Defs.o_id(cell)):
			return w.anchor_of(floori(q.x), floori(q.y))
	return Vector2i(-1, -1)

func can_tow(tid: int) -> bool:
	return TOWABLE.has(tid) or (oid == Defs.O_TOW_TRUCK and HEAVY_TOW.has(tid))

func hitch(ax: int, ay: int) -> bool:
	if not spec()["tow"] or not tow.is_empty():
		return false
	var w: World = sim.world
	var cell: int = w.obj(ax, ay)
	var tid: int = Defs.o_id(cell)
	if not can_tow(tid):
		return false
	var c: Chunk = w.chunk_at(ax, ay)
	var ai: int = World.idx(ax, ay)
	tow = {"o": tid, "ent": c.ents.get(ai, {}), "trunk": w.container_at(ax, ay), "tk": Vector2i(ax, ay)}
	c.containers.erase(ai)
	c.ents.erase(ai)
	var fs: Vector2i = Defs.obj_size(tid, Defs.o_rot(cell))
	for j in range(fs.y):
		for i in range(fs.x):
			w.set_obj(ax + i, ay + j, 0)
	return true

func unhitch() -> bool:
	if tow.is_empty() or absf(speed) > 0.5:
		return false
	var a: Vector2 = anchor_f()
	var ax: int = roundi(a.x)
	var ay: int = roundi(a.y)
	if not _tow_room(ax, ay):
		return false
	_drop_tow(ax, ay)
	return true

func save() -> Dictionary:
	return {"pos": pos, "h": heading, "ent": ent, "trunk": trunk, "tk": tint_key, "o": oid, "tow": tow, "pax": passengers}

static func from_save(sim: Sim, d: Dictionary) -> Vehicle:
	var v := Vehicle.new()
	v.sim = sim
	v.pos = d["pos"]
	v.heading = d["h"]
	v.ent = d["ent"]
	v.trunk = d.get("trunk", [])
	v.tint_key = d.get("tk", Vector2i.ZERO)
	v.oid = d.get("o", Defs.O_CAR)
	v.tow = d.get("tow", {})
	v.passengers = d.get("pax", [])
	return v
