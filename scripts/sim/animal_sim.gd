class_name AnimalSim
extends RefCounted
## Wildlife. Animals belong to the chunk they live in, like everything else: hunt an area out
## and it stays empty until something wanders back in.

const IDLE := 0
const FLEE := 1
const CHARGE := 2
##            name        hp   speed sight  carcass            zones  aggressive  body colour
const SPECIES := {
	"rabbit": {"n": "Rabbit", "hp": 10.0, "sp": 5.4, "see": 6.0, "drop": "carcass_rabbit", "col": "8a7458", "len": 9.0},
	"deer": {"n": "Deer", "hp": 42.0, "sp": 6.6, "see": 11.0, "drop": "carcass_deer", "col": "a07a50", "len": 22.0},
	"pheasant": {"n": "Pheasant", "hp": 5.0, "sp": 5.0, "see": 7.0, "drop": "carcass_bird", "col": "7a5a3a", "len": 8.0, "loud": 1},
	"boar": {"n": "Wild boar", "hp": 60.0, "sp": 4.4, "see": 7.0, "drop": "carcass_boar", "col": "4a3c34", "len": 18.0, "mean": 1},
	"fox": {"n": "Fox", "hp": 18.0, "sp": 5.8, "see": 9.0, "drop": "carcass_fox", "col": "b8642c", "len": 13.0},
}
const KINDS := ["rabbit", "rabbit", "deer", "pheasant", "pheasant", "boar", "fox", "deer"]

class Animal:
	var id := 0
	var kind := "rabbit"
	var pos := Vector2.ZERO
	var dir := Vector2(1, 0)
	var hp := 10.0
	var state := 0
	var t := 0.0
	var goal := Vector2.ZERO
	var atk := 0.0
	var anim_t := 0.0
	var flash := 0.0
	var moving := false

var sim: Sim
var list: Array = []
var _next := 1

func _init(s: Sim) -> void:
	sim = s

func spawn(kind: String, pos: Vector2) -> Animal:
	var a := Animal.new()
	a.id = _next
	_next += 1
	a.kind = kind
	a.pos = pos
	a.goal = pos
	a.hp = SPECIES[kind]["hp"]
	a.t = randf_range(0.5, 4.0)
	list.append(a)
	return a

func _free_spot(c: Chunk, salt: int) -> Vector2:
	for k in range(12):
		var i: int = Rng.h2(c.cx * 31 + k, c.cy * 17 + salt, sim.seed_v + 333) % 256
		if Defs.ground_is_natural(c.ground[i]) and c.obj[i] == 0 and c.bld[i] == 0:
			return Vector2(c.cx * 16 + (i & 15) + 0.5, c.cy * 16 + (i >> 4) + 0.5)
	return Vector2(-1, -1)

func on_chunk_loaded(c: Chunk, first: bool) -> void:
	for a in c.animals:
		var an: Animal = spawn(a[0], Vector2(a[1], a[2]))
		an.hp = a[3]
	c.animals = []
	if World.level(c.cy * 16.0) != 0 or c.zone > 1:
		return
	var hv: int = Rng.h2(c.cx, c.cy, sim.seed_v + 808)
	var quota: int = [0, 0, 1, 1, 2, 3][hv % 6] if c.zone == 0 else [0, 0, 0, 1, 1, 2][hv % 6]
	if first:
		for k in range(quota):
			var p: Vector2 = _free_spot(c, k)
			if p.x >= 0.0:
				spawn(KINDS[(hv >> (4 + k * 3)) % KINDS.size()], p)
		c.an_h = sim.hour
	elif quota > 0 and sim.hour - c.an_h > 96.0:
		# something wanders back in, slowly, and never past what the land carried
		var here := 0
		for a2 in list:
			if (floori(a2.pos.x) >> 4) == c.cx and (floori(a2.pos.y) >> 4) == c.cy: here += 1
		c.an_h = sim.hour
		if here < quota:
			var p2: Vector2 = _free_spot(c, int(sim.hour))
			if p2.x >= 0.0:
				spawn(KINDS[(hv >> 4) % KINDS.size()], p2)

func on_chunk_unload(c: Chunk) -> void:
	var keep: Array = []
	for a in list:
		if (floori(a.pos.x) >> 4) == c.cx and (floori(a.pos.y) >> 4) == c.cy:
			c.animals.append([a.kind, a.pos.x, a.pos.y, a.hp])
			c.touched = true
		else:
			keep.append(a)
	list = keep

func serialized_in_chunk(cx: int, cy: int) -> Array:
	var out: Array = []
	for a in list:
		if (floori(a.pos.x) >> 4) == cx and (floori(a.pos.y) >> 4) == cy:
			out.append([a.kind, a.pos.x, a.pos.y, a.hp])
	return out

func nearest(p: Vector2, r: float) -> Animal:
	var best: Animal = null
	var bd: float = r
	for a in list:
		var d: float = a.pos.distance_to(p)
		if d < bd:
			bd = d
			best = a
	return best

func ray_hit(p: Vector2, dir: Vector2, rng: float) -> Animal:
	var best: Animal = null
	var bt := 1e9
	for a in list:
		var rel: Vector2 = a.pos - p
		var t: float = rel.dot(dir)
		if t < 0.0 or t > rng or t >= bt:
			continue
		if (rel - dir * t).length() > 0.45:
			continue
		if not sim.world.los(p.x, p.y, a.pos.x, a.pos.y):
			continue
		best = a
		bt = t
	return best

func damage(a: Animal, dmg: float, from: Vector2) -> void:
	if not list.has(a):
		return
	a.hp -= dmg
	a.flash = 0.2
	sim.emit_fx("hit", a.pos)
	if a.hp <= 0.0:
		list.erase(a)
		sim.world.drop_item(floori(a.pos.x), floori(a.pos.y), Items.make(SPECIES[a.kind]["drop"], 1, sim.hour))
		sim.player.add_xp("tracking", 12.0)
		sim.say("The %s goes down. Butcher it before it spoils." % String(SPECIES[a.kind]["n"]).to_lower(), Color(0.8, 0.9, 0.75))
		return
	if SPECIES[a.kind].has("mean") and a.hp > 22.0:
		a.state = CHARGE
		a.t = 6.0
	else:
		_scare(a, from)

func _scare(a: Animal, from: Vector2) -> void:
	if a.state != FLEE and SPECIES[a.kind].has("loud"):
		sim.noise(a.pos, 7.0)             # a bird breaking cover gives you away
		sim.emit_fx("step", a.pos)
	a.state = FLEE
	a.t = randf_range(3.0, 5.0)
	var away: Vector2 = (a.pos - from)
	a.dir = (away.normalized() if away.length() > 0.05 else Vector2(1, 0)).rotated(randf_range(-0.5, 0.5))

func update(dt: float) -> void:
	var p: Player = sim.player
	var w: World = sim.world
	for a in list.duplicate():
		a.anim_t += dt
		a.flash = maxf(0.0, a.flash - dt)
		a.atk = maxf(0.0, a.atk - dt)
		a.moving = false
		if not w.is_loaded(floori(a.pos.x), floori(a.pos.y)):
			continue
		var sp: Dictionary = SPECIES[a.kind]
		var dp: float = a.pos.distance_to(p.pos)
		# what can it see or hear?
		var see: float = float(sp["see"]) * (0.45 if p.sneaking else 1.0) * (0.6 if sim.daylight() < 0.3 else 1.0)
		var noticed: bool = p.alive and sim.vehicle == null and dp < see and w.los(a.pos.x, a.pos.y, p.pos.x, p.pos.y)
		if sim.vehicle != null and dp < 12.0: noticed = true
		var scare_from: Vector2 = p.pos
		if not noticed and a.state == IDLE:
			for n in sim.noises:
				if not n[3] and w.heard(n[0], float(n[1]) * 0.8, a.pos):
					noticed = true
					scare_from = n[0]
					break
		if not noticed and a.state == IDLE:
			for z in sim.zombies.list:
				if z.pos.distance_squared_to(a.pos) < 12.0:
					noticed = true
					scare_from = z.pos
					break
		match a.state:
			IDLE:
				if noticed:
					if sp.has("mean") and dp < 3.6 and scare_from == p.pos:
						a.state = CHARGE
						a.t = 5.0
					else:
						_scare(a, scare_from)
				else:
					a.t -= dt
					if a.t <= 0.0:
						a.t = randf_range(2.0, 7.0)
						a.goal = a.pos + Vector2(randf_range(-3, 3), randf_range(-3, 3))
					var to: Vector2 = a.goal - a.pos
					if to.length() > 0.3:
						a.dir = to.normalized()
						var np: Vector2 = w.move(a.pos, a.dir * 1.1 * dt, 0.2)
						a.moving = np.distance_to(a.pos) > 0.001
						if not a.moving: a.goal = a.pos
						a.pos = np
			FLEE:
				a.t -= dt
				var np2: Vector2 = w.move(a.pos, a.dir * float(sp["sp"]) * dt, 0.2)
				if np2.distance_to(a.pos) < float(sp["sp"]) * dt * 0.4:
					a.dir = a.dir.rotated(1.3 if randf() < 0.5 else -1.3)       # ran into something: turn
				a.pos = np2
				a.moving = true
				if a.t <= 0.0 and not noticed:
					a.state = IDLE
					a.goal = a.pos
			CHARGE:
				a.t -= dt
				if not p.alive or a.t <= 0.0 or dp > 9.0 or sim.vehicle != null:
					a.state = IDLE
					a.goal = a.pos
				elif dp > 0.85:
					a.dir = (p.pos - a.pos).normalized()
					a.pos = w.move(a.pos, a.dir * float(sp["sp"]) * dt, 0.2)
					a.moving = true
				elif a.atk <= 0.0:
					a.atk = 1.4
					if not sim.settings.get("god", false):
						p.hurt(randf_range(6.0, 12.0), "Gored by a wild boar")
						if randf() < 0.5:
							p.add_wound(11 + randi() % 4, "laceration", "a boar's tusk")
						p.cancel_action()
						sim.emit_fx("hurt", p.pos)
						sim.say("The boar hits you low and hard.", Color(1.0, 0.6, 0.45))

## read the ground: which way did the nearest animal go?
func track(from: Vector2, skill: int) -> String:
	var a: Animal = nearest(from, 22.0 + skill * 5.0)
	if a == null:
		return ""
	return "%s sign, heading %s — about %d paces." % [SPECIES[a.kind]["n"], Sim.compass(from, a.pos), int(a.pos.distance_to(from) / 5.0 + 1.0) * 5]
