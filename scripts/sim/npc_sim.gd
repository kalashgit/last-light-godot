class_name NpcSim
extends RefCounted
## Other survivors. A small first system: they wait, follow, fight the infected beside you,
## get hungry, talk, and some of them are not friendly. Stored per chunk like the infected.

const STAY := 0
const FOLLOW := 1
const HOSTILE := 2
const NAMES := ["Mara", "Ilya", "Tomas", "Renee", "Odile", "Jonah", "Priya", "Kasper", "Lena", "Amos", "Wren", "Dario"]
const LINES := ["I counted eleven days since I heard a voice that wasn't mine.", "The pharmacy downtown still had shelves when I ran past. Too many of them, though.",
	"Don't light anything after dark. They see it from the next street.", "My brother went for the farm road. If you see a blue pack, that's his.",
	"When the engines come over, get under a roof. I learned that one the hard way.", "Cellars. Half the houses here have one. Look for the hatch."]

class Npc:
	var id := 0
	var pos := Vector2.ZERO
	var dir := Vector2(0.7, 0.7)
	var d8 := 0
	var hp := 100.0
	var state := 0
	var look := [0, 0, 0, 0]
	var name := ""
	var hunger := 20.0
	var met := false
	var gift := false
	var anim := "s_idle"
	var anim_t := 0.0
	var atk_cd := 0.0
	var swing := 0.0
	var path := PackedVector2Array()
	var path_i := 0
	var repath := 0.0
	var flash := 0.0
	var stock: Array = []          # item ids they are willing to swap

var sim: Sim
var list: Array = []
var _next := 1

func _init(s: Sim) -> void:
	sim = s

func spawn(pos: Vector2, hostile: bool) -> Npc:
	var n := Npc.new()
	n.id = _next
	_next += 1
	n.pos = pos
	n.state = HOSTILE if hostile else STAY
	n.look = [randi() % 4, randi() % 10, randi() % 6, randi() % 6]
	n.name = NAMES[randi() % NAMES.size()]
	var goods: Array = ["bandage", "ammo_9mm", "painkillers", "battery", "matches", "duct_tape", "nails", "canned_beans", "water_bottle", "disinfectant", "kitchen_knife", "lighter"]
	for k in range(3):
		n.stock.append(goods[randi() % goods.size()])
	list.append(n)
	return n

static func _ser(n: Npc) -> Array:
	return [n.pos.x, n.pos.y, n.hp, n.state, n.look, n.name, n.hunger, n.met, n.gift, n.stock]

func _de(a: Array) -> Npc:
	var n := Npc.new()
	n.id = _next
	_next += 1
	n.pos = Vector2(a[0], a[1])
	n.hp = a[2]
	n.state = a[3]
	n.look = a[4]
	n.name = a[5]
	n.hunger = a[6]
	n.met = a[7]
	n.gift = a[8]
	n.stock = a[9] if a.size() > 9 else []
	return n

func on_chunk_loaded(c: Chunk) -> void:
	for a in c.npcs:
		list.append(_de(a))
	c.npcs = []
	if not c.spawned:
		for sn in c.story_n:
			var p: Vector2 = sn[0]
			if not sim.world.blocked(p.x, p.y, 0.2):
				spawn(p, sn[1])

func on_chunk_unload(c: Chunk) -> void:
	var keep: Array = []
	for n in list:
		# companions travel with the player; everyone else stays with their chunk
		if (floori(n.pos.x) >> 4) == c.cx and (floori(n.pos.y) >> 4) == c.cy and n.state != FOLLOW:
			c.npcs.append(_ser(n))
			c.touched = true
		else:
			keep.append(n)
	list = keep

func serialized_in_chunk(cx: int, cy: int) -> Array:
	var out: Array = []
	for n in list:
		if (floori(n.pos.x) >> 4) == cx and (floori(n.pos.y) >> 4) == cy:
			out.append(_ser(n))
	return out

func nearest(p: Vector2, r: float) -> Npc:
	var best: Npc = null
	var bd: float = r
	for n in list:
		var d: float = n.pos.distance_to(p)
		if d < bd:
			bd = d
			best = n
	return best

func damage(n: Npc, dmg: float, by_player: bool) -> void:
	n.hp -= dmg
	n.flash = 0.2
	sim.emit_fx("hit", n.pos)
	if by_player and n.state != HOSTILE:
		n.state = HOSTILE
		sim.say("%s turns on you." % n.name, Color(1.0, 0.6, 0.5))
	if n.hp <= 0.0:
		list.erase(n)
		var c: Chunk = sim.world.chunk_at(floori(n.pos.x), floori(n.pos.y))
		if c != null:
			c.corpses.append({"x": n.pos.x, "y": n.pos.y, "d": n.d8, "l": n.look, "h": sim.hour, "perm": 1, "lt": "corpse_survivor"})
			c.touched = true
			sim.world.notify(floori(n.pos.x), floori(n.pos.y))
		sim.say("%s is dead." % n.name, Color(0.9, 0.8, 0.7))

func _go(n: Npc, target: Vector2, speed: float, dt: float) -> void:
	var w: World = sim.world
	var goal: Vector2 = target
	n.repath -= dt
	while n.path_i < n.path.size() and n.pos.distance_to(n.path[n.path_i]) < 0.4:
		n.path_i += 1
	if n.path_i < n.path.size():
		goal = n.path[n.path_i]
	elif not w.walk_clear(n.pos.x, n.pos.y, target.x, target.y) and n.repath <= 0.0:
		n.repath = 1.0
		n.path = Pathfinder.find(w, floori(n.pos.x), floori(n.pos.y), floori(target.x), floori(target.y), 500, 0.0)
		n.path_i = 0
		# survivors use doors like people do
		if n.path.is_empty():
			for side in range(2):
				for d in [Vector2i(0, 0), Vector2i(1, 0), Vector2i(0, 1)]:
					var ex: int = floori(n.pos.x) + d.x
					var ey: int = floori(n.pos.y) + d.y
					var wid: int = w.wall(ex, ey, side)
					if wid != 0 and (wid & 3) == Defs.WS_DOOR and (w.edge_state(ex, ey, side) & (Defs.ES_OPEN | Defs.ES_PLANK_MASK)) == 0:
						w.set_edge_state(ex, ey, side, (w.edge_state(ex, ey, side) | Defs.ES_OPEN) & ~Defs.ES_LOCKED)
	var to: Vector2 = goal - n.pos
	if to.length() > 0.05:
		n.dir = to.normalized()
		n.d8 = Iso.dir8(n.dir)
		n.pos = w.move(n.pos, n.dir * minf(speed * dt, to.length()), 0.2)
		n.anim = "s_walk"

func update(dt: float, dh: float) -> void:
	var p: Player = sim.player
	for n in list.duplicate():
		n.anim_t += dt
		n.atk_cd = maxf(0.0, n.atk_cd - dt)
		n.swing = maxf(0.0, n.swing - dt)
		n.flash = maxf(0.0, n.flash - dt)
		n.hunger = minf(100.0, n.hunger + dh * 3.0)
		n.anim = "s_attack" if n.swing > 0.0 else "s_idle"
		if not sim.world.is_loaded(floori(n.pos.x), floori(n.pos.y)):
			if n.state == FOLLOW and World.level(n.pos.y) == World.level(p.pos.y):
				n.pos = p.pos
			continue
		# the infected do not care who they bite
		var close := 0
		var target: Zombie = null
		var td := 99.0
		for z in sim.zombies.list:
			var d: float = z.pos.distance_to(n.pos)
			if d < 0.9 and z.state != Zombie.DOWN:
				close += 1
			if d < td:
				td = d
				target = z
		if close > 0:
			n.hp -= dt * 7.0 * close
			if n.hp <= 0.0:
				damage(n, 0.0, false)
				continue
		if n.state == HOSTILE:
			var dp: float = n.pos.distance_to(p.pos)
			if p.alive and dp < 11.0 and sim.world.los(n.pos.x, n.pos.y, p.pos.x, p.pos.y):
				if dp > 0.95:
					_go(n, p.pos, 2.6, dt)
				elif n.atk_cd <= 0.0:
					n.atk_cd = 1.2
					n.swing = 0.4
					n.anim_t = 0.0
					n.dir = (p.pos - n.pos).normalized()
					n.d8 = Iso.dir8(n.dir)
					if not sim.settings.get("god", false) and sim.vehicle == null:
						p.hurt(randf_range(6.0, 12.0), "Killed by another survivor")
						if randf() < 0.5:
							p.add_wound(Rng.pick_weighted(sim.rng, Player.HIT_WEIGHTS), "laceration" if randf() < 0.4 else "scratch", "a blade")
						p.cancel_action()
						sim.emit_fx("hurt", p.pos)
			continue
		# friends fight what is next to them
		if target != null and td < 1.3 and n.atk_cd <= 0.0:
			n.atk_cd = 1.0
			n.swing = 0.4
			n.anim_t = 0.0
			n.dir = (target.pos - n.pos).normalized()
			n.d8 = Iso.dir8(n.dir)
			sim.zombies.damage(target, randf_range(18.0, 30.0), n.pos, 0.3, randf() < 0.2, false)
			if not sim.zombies.list.has(target):
				sim.player.kills -= 1       # their kill, not yours
		elif n.state == FOLLOW:
			var dpl: float = n.pos.distance_to(p.pos)
			if dpl > 2.2:
				_go(n, p.pos, 4.4 if dpl > 6.0 else 2.6, dt)
			if n.hunger >= 100.0:
				n.state = STAY
				sim.say("%s: \"I can't keep going on nothing. I'm staying here.\"" % n.name, Color(0.85, 0.85, 0.7))

# ------------------------------------------------------------------ talking
func options(n: Npc) -> Array:
	var p: Player = sim.player
	var out: Array = []
	if n.state == HOSTILE:
		return out
	out.append({"label": "Talk to %s" % n.name, "fn": func():
		if not n.met:
			n.met = true
			sim.say("%s: \"You're alive. I'd stopped expecting that.\"" % n.name, Color(0.85, 0.85, 0.7))
		else:
			sim.say("%s: \"%s\"" % [n.name, LINES[randi() % LINES.size()]], Color(0.85, 0.85, 0.7))
		p.bored = maxf(0.0, p.bored - 20.0)
		p.unhappy = maxf(0.0, p.unhappy - 8.0)})
	if n.state == STAY:
		out.append({"label": "\"Come with me.\"", "fn": func():
			if n.hunger > 85.0:
				sim.say("%s: \"Not until I've eaten something.\"" % n.name, Color(0.85, 0.85, 0.7))
			else:
				n.state = FOLLOW
				sim.say("%s falls in behind you." % n.name, Color(0.75, 0.9, 0.7))})
	else:
		out.append({"label": "\"Wait here.\"", "fn": func():
			n.state = STAY
			sim.say("%s: \"I'll hold this spot.\"" % n.name, Color(0.85, 0.85, 0.7))})
	# barter: one of theirs for one of yours. They want things that keep a person alive.
	var offer: Dictionary = {}
	for it0 in p.inv:
		var c0: String = Items.def(it0["id"]).get("cat", "")
		if (c0 == "food" or c0 == "drink" or c0 == "med" or c0 == "ammo") and not is_same(it0, p.weapon) and Items.fresh_state(it0, sim.hour) < 2 and not n.stock.has(it0["id"]):
			offer = it0
			break
	if n.met and not offer.is_empty():
		for si in range(n.stock.size()):
			var want_id: String = n.stock[si]
			var give_it: Dictionary = offer
			out.append({"label": "Trade your %s for their %s" % [Items.def(give_it["id"])["n"], Items.def(want_id)["n"]], "fn": func():
				if not p.inv.has(give_it) or not n.stock.has(want_id):
					return
				var given: Dictionary = Inv.split(p.inv, give_it, 1)
				n.stock.erase(want_id)
				n.stock.append(given["id"])
				Inv.add_new(p.inv, want_id, 6 if want_id == "ammo_9mm" else 1, sim.hour)
				sim.say("%s: \"Fair.\"" % n.name, Color(0.85, 0.85, 0.7))})
	elif n.met and n.stock.size() > 0:
		out.append({"label": "Ask what they would trade", "fn": func():
			var names: Array = []
			for sid in n.stock: names.append(Items.def(sid)["n"])
			sim.say("%s has %s — and wants food, drink, medicine or ammunition for it." % [n.name, ", ".join(names)], Color(0.85, 0.85, 0.7))})
	for it in p.inv:
		var d: Dictionary = Items.def(it["id"])
		if d.has("hunger") and not d.has("raw") and p.can_eat(it) == "" and Items.fresh_state(it, sim.hour) < 2:
			var food: Dictionary = it
			out.append({"label": "Give %s (%s is %s)" % [d["n"], n.name, "starving" if n.hunger > 80.0 else ("hungry" if n.hunger > 45.0 else "fed")], "fn": func():
				Inv.split(p.inv, food, 1)
				n.hunger = maxf(0.0, n.hunger - float(d["hunger"]) * 2.0)
				n.hp = minf(100.0, n.hp + 15.0)
				if not n.gift:
					n.gift = true
					var gifts: Array = ["bandage", "ammo_9mm", "painkillers", "battery", "matches", "duct_tape"]
					var g: String = gifts[randi() % gifts.size()]
					Inv.add_new(p.inv, g, 6 if g == "ammo_9mm" else 1, sim.hour)
					sim.say("%s presses something into your hand: %s." % [n.name, Items.def(g)["n"]], Color(0.75, 0.9, 0.7))
				else:
					sim.say("%s: \"Thank you.\"" % n.name, Color(0.85, 0.85, 0.7))})
			break
	return out
