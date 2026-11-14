class_name NpcSim
extends RefCounted
## Other survivors. A small first system: they wait, follow, fight the infected beside you,
## get hungry, talk, and some of them are not friendly. Stored per chunk like the infected.

const STAY := 0
const FOLLOW := 1
const HOSTILE := 2
const NAMES := ["Mara", "Ilya", "Tomas", "Renee", "Odile", "Jonah", "Priya", "Kasper", "Lena", "Amos", "Wren", "Dario"]
const TEMPERS := ["brave", "cautious", "generous", "wary"]
const JOBS := ["medic", "mechanic", "farmer", "hunter", "cook", "guard"]
const EDIBLE := ["canned_beans", "granola_bar", "canned_corn", "cooked_egg", "berries", "cooked_chicken"]
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
	var stock: Array = []          # what they carry: swapped, eaten, added to when they scavenge
	var thirst := 15.0
	var fatigue := 20.0
	var trust := 30.0              # 0 stranger .. 100 would die for you
	var temper := ""               # brave | cautious | generous | wary
	var job := ""                  # medic | mechanic | farmer | hunter | cook | guard
	var home := Vector2.ZERO       # where they sleep and return to
	var wpn := ""                  # a weapon you gave them
	var task := ""                 # "" | sleep | scavenge | home | flee
	var task_pos := Vector2.ZERO
	var task_t := 0.0
	var seen_kills := -1
	var fac := -1                  # faction index, or -1 for a loner
	var site := Vector2i.ZERO      # region key of their settlement
	var recruit := false           # lives at your shelter
	var work := ""                 # farm | guard | scavenge | cook | nurse | fix
	var trader := false            # passing through with goods to swap
	var leave_h := 0.0             # traders: when they move on
	var away_until := 0.0          # scavengers: out on a trip until this hour
	var uh := 0.0                  # hour they were last simulated (for time spent unloaded)
	var _work_t := 0.0
	var help_until := 0.0          # agreed to help you for a while, then goes home
	var forgiven_h := -99.0        # when they last accepted an apology

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
	n.temper = TEMPERS[randi() % TEMPERS.size()]
	n.job = JOBS[randi() % JOBS.size()]
	n.trust = randf_range(22.0, 40.0) + (8.0 if n.temper == "generous" else (-8.0 if n.temper == "wary" else 0.0))
	n.home = pos
	list.append(n)
	return n

static func _ser(n: Npc) -> Array:
	return [n.pos.x, n.pos.y, n.hp, n.state, n.look, n.name, n.hunger, n.met, n.gift, n.stock, n.thirst, n.fatigue, n.trust, n.temper, n.job, n.home, n.wpn, n.fac, n.site, n.recruit, n.work, n.trader, n.leave_h, n.away_until, n.uh, n.help_until, n.forgiven_h]

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
	n.home = n.pos
	if a.size() > 16:
		n.thirst = a[10]
		n.fatigue = a[11]
		n.trust = a[12]
		n.temper = a[13]
		n.job = a[14]
		n.home = a[15]
		n.wpn = a[16]
		if a.size() > 18:
			n.fac = a[17]
			n.site = a[18]
		if a.size() > 24:
			n.recruit = a[19]
			n.work = a[20]
			n.trader = a[21]
			n.leave_h = a[22]
			n.away_until = a[23]
			n.uh = a[24]
		if a.size() > 26:
			n.help_until = a[25]
			n.forgiven_h = a[26]
	else:
		n.temper = TEMPERS[n.id % TEMPERS.size()]
		n.job = JOBS[n.id % JOBS.size()]
	return n

func on_chunk_loaded(c: Chunk) -> void:
	for a in c.npcs:
		var n: Npc = _de(a)
		list.append(n)
		if n.recruit and n.uh > 0.0 and sim.hour - n.uh > 1.0:
			_catch_up_recruit(n, sim.hour - n.uh)
	c.npcs = []
	if not c.spawned:
		for sn in c.story_n:
			var p: Vector2 = sn[0]
			if not sim.world.blocked(p.x, p.y, 0.2):
				spawn(p, sn[1])
		sim.factions.on_chunk_first(c)

func on_chunk_unload(c: Chunk) -> void:
	var keep: Array = []
	for n in list:
		# companions travel with the player; everyone else stays with their chunk
		if (floori(n.pos.x) >> 4) == c.cx and (floori(n.pos.y) >> 4) == c.cy and n.state != FOLLOW:
			n.uh = sim.hour
			if n.trader:
				continue                   # a trader out of sight has moved on for good
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

func ray_hit(p: Vector2, dir: Vector2, rng: float) -> Npc:
	var best: Npc = null
	var bt := 1e9
	for n in list:
		if n.away_until > 0.0:
			continue
		var rel: Vector2 = n.pos - p
		var t: float = rel.dot(dir)
		if t < 0.3 or t > rng or t >= bt:
			continue
		if (rel - dir * t).length() > 0.38:
			continue
		if not sim.world.los(p.x, p.y, n.pos.x, n.pos.y):
			continue
		best = n
		bt = t
	return best

func nearest(p: Vector2, r: float) -> Npc:
	var best: Npc = null
	var bd: float = r
	for n in list:
		if n.away_until > 0.0:
			continue
		var d: float = n.pos.distance_to(p)
		if d < bd:
			bd = d
			best = n
	return best

func damage(n: Npc, dmg: float, by_player: bool) -> void:
	if not list.has(n):
		return          # already dead: two attackers in one frame must not kill them twice
	n.hp -= dmg
	n.flash = 0.2
	sim.emit_fx("hit", n.pos)
	if by_player and n.state != HOSTILE:
		n.state = HOSTILE
		sim.say("%s turns on you." % n.name, Color(1.0, 0.6, 0.5))
	if by_player and n.fac >= 0 and Factions.kind(n.fac) != Factions.RAIDER:
		sim.factions.hear_of(n, -25.0, n.hp > 0.0)        # a survivor who lives tells them; a dead one cannot
	if n.hp <= 0.0:
		list.erase(n)
		if n.fac >= 0:
			if by_player and Factions.kind(n.fac) == Factions.RAIDER:
				# everyone else is glad of it
				for fi in range(Factions.LIST.size()):
					if Factions.kind(fi) != Factions.RAIDER: sim.factions.add_rep(fi, 3.0)
				sim.factions.member_died(n, false)
			else:
				sim.factions.member_died(n, by_player)
		var c: Chunk = sim.world.chunk_at(floori(n.pos.x), floori(n.pos.y))
		var carried: Array = []
		for sid in n.stock:
			carried.append(Items.make(sid, 1, sim.hour))
		if n.wpn != "":
			carried.append(Items.make(n.wpn, 1, sim.hour))
		if not by_player and dmg <= 0.0 and c != null and sim.settings.get("infection", true):
			# bitten to death: they get up again, still carrying what they had
			var zr: Zombie = sim.zombies.spawn(n.pos, 0)
			zr.look = n.look.duplicate()
			zr.loot = carried
			zr.state = Zombie.DOWN
			zr.t = 6.0
			sim.say("%s is dead. It will not stay that way." % n.name, Color(1.0, 0.6, 0.5))
			return
		if c != null:
			c.corpses.append({"x": n.pos.x, "y": n.pos.y, "d": n.d8, "l": n.look, "h": sim.hour, "perm": 1, "loot": carried})
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
		if not list.has(n):
			continue
		if n.away_until > 0.0:
			if sim.hour < n.away_until:
				continue                   # out scavenging
			_return_from_trip(n)
		n.anim_t += dt
		n.atk_cd = maxf(0.0, n.atk_cd - dt)
		n.swing = maxf(0.0, n.swing - dt)
		n.flash = maxf(0.0, n.flash - dt)
		n.hunger = minf(100.0, n.hunger + dh * 3.0)
		n.thirst = minf(100.0, n.thirst + dh * 4.0)
		n.fatigue = minf(100.0, n.fatigue + dh * (4.2 if n.task != "sleep" else -12.0))
		if n.fatigue < 0.0: n.fatigue = 0.0
		_needs(n, dh)
		if n.hp <= 0.0:
			damage(n, 0.01, false)        # starved or died of thirst: an ordinary body
			continue
		n.anim = "s_attack" if n.swing > 0.0 else "s_idle"
		# they notice what you do near them
		if n.seen_kills < 0: n.seen_kills = p.kills
		if p.kills > n.seen_kills and n.state != HOSTILE and n.pos.distance_squared_to(p.pos) < 100.0:
			n.trust = minf(100.0, n.trust + 2.0 * (p.kills - n.seen_kills))
		n.seen_kills = p.kills
		if n.help_until > 0.0 and sim.hour > n.help_until:
			n.help_until = 0.0
			if n.state == FOLLOW:
				n.state = STAY
				n.task = "home"
				sim.say("%s: \"That's what I promised. I'm heading back.\"" % n.name, Color(0.85, 0.85, 0.7))
		if n.state == FOLLOW and n.help_until <= 0.0:
			n.trust = minf(100.0, n.trust + dh * 0.6)
			n.home = n.pos
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
		if n.fac >= 0 and n.state != HOSTILE and sim.factions.rep_of(n.fac) < -15.0:
			n.state = HOSTILE                 # the whole group knows what you did
		if n.state == HOSTILE:
			var dp: float = n.pos.distance_to(p.pos)
			var victim: Npc = null
			var vd: float = minf(dp, 7.0)
			for o in list:
				if o.state != HOSTILE and o.fac != n.fac and o.pos.distance_to(n.pos) < vd and sim.world.los(n.pos.x, n.pos.y, o.pos.x, o.pos.y):
					vd = o.pos.distance_to(n.pos)
					victim = o
			if victim != null:
				if vd > 0.95:
					_go(n, victim.pos, 2.6, dt)
				elif n.atk_cd <= 0.0:
					n.atk_cd = 1.2
					n.swing = 0.4
					n.anim_t = 0.0
					damage(victim, randf_range(8.0, 14.0), false)
				continue
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
			elif n.task == "travel":
				routine(n, dt)              # a hostile patrol that has not seen you keeps marching
			continue
		# theft: taking from the house they live in, in front of them
		if n.state == STAY and n.met:
			for ev in sim.ui_events:
				if ev["type"] == "loot" and n.pos.distance_to(n.home) < 12.0 and p.pos.distance_to(n.home) < 8.0 and sim.world.bld(floori(p.pos.x), floori(p.pos.y)) != 0 \
						and sim.world.bld(floori(p.pos.x), floori(p.pos.y)) == sim.world.bld(floori(n.home.x), floori(n.home.y)) and sim.world.los(n.pos.x, n.pos.y, p.pos.x, p.pos.y):
					n.trust = maxf(0.0, n.trust - 6.0)
					sim.factions.add_rep(n.fac, -6.0)
					sim.say("%s: \"Those are %s.\"" % [n.name, "ours" if n.fac >= 0 else "mine"], Color(1.0, 0.8, 0.6))
		# fear: the cautious and the badly hurt run instead of standing their ground
		var threats := 0
		var away := Vector2.ZERO
		for z2 in sim.zombies.list:
			var dz: float = z2.pos.distance_to(n.pos)
			if dz < 4.5 and z2.state != Zombie.DOWN:
				threats += 1
				away += (n.pos - z2.pos).normalized()
		var limit: int = 4 if n.temper == "brave" else (1 if n.temper == "cautious" else 2)
		if threats > 0 and (threats > limit or n.hp < 35.0) and n.wpn == "" or (threats > limit + 2):
			n.task = "flee"
			n.task_t = 2.5
			n.task_pos = (p.pos if n.state == FOLLOW and p.pos.distance_to(n.pos) > 3.0 else n.pos + away.normalized() * 6.0)
		if n.task == "flee":
			n.task_t -= dt
			_go(n, n.task_pos, 4.3, dt)
			if n.task_t <= 0.0: n.task = ""
			continue
		# someone is trying to kill them: hit back
		var foe: Npc = null
		for o2 in list:
			if o2.state == HOSTILE and o2.pos.distance_to(n.pos) < 1.3: foe = o2
		if foe != null and n.atk_cd <= 0.0:
			n.atk_cd = 1.0
			n.swing = 0.4
			n.anim_t = 0.0
			damage(foe, randf_range(10.0, 18.0) * (1.4 if n.wpn != "" or n.job == "guard" else 1.0), false)
			continue
		# friends fight what is next to them
		if target != null and td < 1.3 and n.atk_cd <= 0.0:
			n.atk_cd = 1.0
			n.swing = 0.4
			n.anim_t = 0.0
			n.dir = (target.pos - n.pos).normalized()
			n.d8 = Iso.dir8(n.dir)
			var wdmg: float = 1.0
			if n.wpn != "":
				var wdr: Array = Items.def(n.wpn)["wpn"]["dmg"]
				wdmg = (float(wdr[0]) + float(wdr[1])) / 48.0 + 0.5
			if n.job == "guard" or n.job == "hunter": wdmg *= 1.25
			sim.zombies.damage(target, randf_range(18.0, 30.0) * wdmg, n.pos, 0.3, randf() < 0.2, false)
			if not sim.zombies.list.has(target):
				sim.player.kills -= 1       # their kill, not yours
		elif n.state == STAY:
			routine(n, dt)
		elif n.state == FOLLOW:
			var dpl: float = n.pos.distance_to(p.pos)
			if dpl > 2.2:
				_go(n, p.pos, 4.4 if dpl > 6.0 else 2.6, dt)
			if n.trust < 8.0:
				n.state = STAY
				sim.say("%s: \"I'm done following you.\"" % n.name, Color(1.0, 0.8, 0.6))
			if n.hunger >= 100.0:
				n.state = STAY
				sim.say("%s: \"I can't keep going on nothing. I'm staying here.\"" % n.name, Color(0.85, 0.85, 0.7))

## the harder conversations: asking a favour, making a demand at weapon-point, making amends
func social_options(n: Npc, tr: float) -> Array:
	var p: Player = sim.player
	var out: Array = []
	if n.state == STAY and not n.recruit and not n.trader and tr >= 40.0 and n.help_until <= 0.0:
		out.append({"label": "\"Help me for a few hours?\"", "fn": func(): ask_help(n)})
	if not p.weapon.is_empty() and not n.recruit:
		out.append({"label": "Threaten them: \"Hand it over.\"", "fn": func(): threaten(n)})
	if tr < 30.0 and sim.hour - n.forgiven_h > 24.0:
		out.append({"label": "\"I'm sorry. Take this.\" (give food)", "fn": func(): apologize(n)})
	return out

func ask_help(n: Npc) -> bool:
	var tr: float = n.trust + (sim.factions.rep_of(n.fac) * 0.4 if n.fac >= 0 else 0.0)
	var keen: bool = n.temper == "brave" or n.temper == "generous" or tr >= 60.0
	if n.hunger > 80.0 or n.hp < 40.0 or (not keen and randf() < 0.5):
		sim.say("%s: \"Not today. I can barely look after myself.\"" % n.name, Color(0.85, 0.85, 0.7))
		return false
	n.state = FOLLOW
	n.help_until = sim.hour + 6.0
	n.met = true
	sim.say("%s: \"Six hours. Then I'm going home.\"" % n.name, Color(0.7, 0.9, 0.7))
	return true

## a demand with a weapon in your hand: they may give in, run, or fight. none of them forget it
func threaten(n: Npc) -> String:
	var p: Player = sim.player
	var gun: bool = Items.def(p.weapon["id"]).has("gun")
	var give: float = 0.35 + (0.3 if gun else 0.0) + (0.2 if n.temper == "cautious" else 0.0) - (0.35 if n.temper == "brave" else 0.0) \
		- (0.25 if n.wpn != "" else 0.0) + (0.15 if n.hp < 50.0 else 0.0)
	n.trust = maxf(0.0, n.trust - 40.0)
	n.met = true
	if n.fac >= 0:
		sim.factions.hear_of(n, -20.0, true)
	var r: float = randf()
	if r < give and not n.stock.is_empty():
		var took: Array = []
		for k in range(mini(2, n.stock.size())):
			var sid: String = n.stock.pop_back()
			Inv.add_new(p.inv, sid, 1, sim.hour)
			took.append(Items.def(sid)["n"])
		sim.say("%s raises their hands and gives you %s. They will remember your face." % [n.name, " and ".join(took)], Color(1.0, 0.75, 0.55))
		return "gave"
	if n.temper == "brave" or n.wpn != "" or r > 0.85:
		n.state = HOSTILE
		sim.say("%s: \"Over my dead body.\"" % n.name, Color(1.0, 0.55, 0.45))
		return "fight"
	n.task = "flee"
	n.task_t = 6.0
	n.task_pos = n.pos + (n.pos - p.pos).normalized() * 12.0
	sim.say("%s bolts." % n.name, Color(1.0, 0.75, 0.55))
	return "fled"

## food offered with an apology: a little trust back, and a little standing with their people
func apologize(n: Npc) -> bool:
	var p: Player = sim.player
	var food: Dictionary = {}
	for it in p.inv:
		if Items.def(it["id"]).get("cat", "") == "food" and not Items.def(it["id"]).has("raw"):
			food = it
			break
	if food.is_empty():
		sim.say("You have nothing to offer them.", Color(0.9, 0.8, 0.6))
		return false
	var one: Dictionary = Inv.split(p.inv, food, 1)
	n.stock.append(one["id"])
	n.forgiven_h = sim.hour
	n.trust = minf(100.0, n.trust + (18.0 if n.temper == "generous" else (8.0 if n.temper == "wary" else 12.0)))
	if n.fac >= 0:
		sim.factions.add_rep(n.fac, 4.0)
	sim.say("%s takes the %s. \"...All right.\"" % [n.name, String(Items.def(one["id"])["n"]).to_lower()], Color(0.8, 0.9, 0.75))
	return true

## eat and drink from what they carry; go without and it starts to cost them
func _needs(n: Npc, dh: float) -> void:
	if n.recruit and n.hunger > 55.0 and _eat_from_stores(n):
		n.hunger = maxf(0.0, n.hunger - 45.0)
	if n.recruit and n.thirst > 55.0 and _drink_from_stores(n):
		n.thirst = maxf(0.0, n.thirst - 60.0)
	if n.recruit:
		# a fed, rested person settles in; a hungry one starts to doubt you
		n.trust = clampf(n.trust + dh * (0.4 if n.hunger < 60.0 else -1.2), 0.0, 100.0)
		if n.trust < 15.0 or n.hunger >= 100.0 and n.hp < 50.0:
			n.recruit = false
			n.work = ""
			n.home = n.pos + Vector2(randf_range(-30, 30), randf_range(-30, 30))
			sim.say("%s has left your shelter. There was nothing to eat, or nothing to stay for." % n.name, Color(1.0, 0.75, 0.55))
	var st: Dictionary = sim.factions.site_of(n)
	if n.hunger > 55.0 and not st.is_empty() and float(st["food"]) > 0.3 and n.state != FOLLOW:
		st["food"] = float(st["food"]) - 0.3
		n.hunger = maxf(0.0, n.hunger - 45.0)
	if n.hunger > 55.0:
		for sid in n.stock:
			if EDIBLE.has(sid):
				n.stock.erase(sid)
				n.hunger = maxf(0.0, n.hunger - 45.0)
				break
	if n.thirst > 55.0 and n.stock.has("water_bottle"):
		n.stock.erase("water_bottle")
		n.stock.append("empty_bottle")
		n.thirst = maxf(0.0, n.thirst - 60.0)
	elif n.thirst > 70.0 and sim.has_water() and sim.world.bld(floori(n.pos.x), floori(n.pos.y)) != 0:
		n.thirst = 10.0            # the taps still run
	if n.hunger >= 100.0: n.hp -= dh * 1.5
	if n.thirst >= 100.0: n.hp -= dh * 4.0
	if n.hunger < 60.0 and n.thirst < 60.0 and n.task == "sleep":
		n.hp = minf(100.0, n.hp + dh * 3.0)

# ------------------------------------------------------------------ your shelter
const WORKS := {"farm": "tend the crops", "guard": "keep watch", "scavenge": "go out scavenging", "cook": "cook what we bring in", "nurse": "look after the wounded", "fix": "keep the vehicles running"}
const TRIP_FINDS := ["canned_beans", "canned_soup", "water_bottle", "bandage", "nails", "plank", "ammo_9mm", "battery", "painkillers", "seeds_potato", "duct_tape", "scrap_metal"]

func _take_from_stores(pred: Callable) -> Dictionary:
	for st in sim.home_stores():
		var arr: Array = st[2]
		for it in arr:
			if pred.call(it):
				var one: Dictionary = Inv.split(arr, it, 1)
				sim.world.chunk_at(int(st[0]), int(st[1])).touched = true
				return one
	return {}

func _put_in_stores(it: Dictionary) -> bool:
	var stores: Array = sim.home_stores()
	if stores.is_empty():
		return false
	var arr: Array = stores[0][2]
	Inv.add(arr, it)
	sim.world.chunk_at(int(stores[0][0]), int(stores[0][1])).touched = true
	return true

func _eat_from_stores(n: Npc) -> bool:
	var got: Dictionary = _take_from_stores(func(it):
		var d: Dictionary = Items.def(it["id"])
		return d.has("hunger") and not d.has("raw") and float(d["hunger"]) > 0.0 and Items.fresh_state(it, sim.hour) < 2)     # tins: they get them open with a knife
	return not got.is_empty()

func _drink_from_stores(n: Npc) -> bool:
	if sim.has_water():
		return true
	var got: Dictionary = _take_from_stores(func(it): return it["id"] == "water_bottle" and int(it.get("u", 1)) > 0)
	if not got.is_empty():
		_put_in_stores(Items.make("empty_bottle", 1))
		return true
	return false

func recruit_to_home(n: Npc) -> void:
	n.recruit = true
	n.state = STAY
	n.home = sim.home_pos() + Vector2(randf_range(-2.0, 2.0), randf_range(-2.0, 2.0))
	n.task = "home"
	n.work = {"farmer": "farm", "guard": "guard", "hunter": "scavenge", "cook": "cook", "medic": "nurse", "mechanic": "fix"}.get(n.job, "guard")

## the hours you were away from the shelter, done in one go
func _catch_up_recruit(n: Npc, hours: float) -> void:
	var days: float = hours / 24.0
	var meals: int = int(ceil(days * 2.0))
	var fed := 0
	for k in range(meals):
		if _eat_from_stores(n): fed += 1
	n.hunger = clampf(n.hunger + hours * 3.0 - float(fed) * 45.0, 0.0, 100.0)
	n.thirst = 20.0 if sim.has_water() or _drink_from_stores(n) else minf(100.0, n.thirst + hours * 2.0)
	match n.work:
		"farm":
			_tend_crops(n, true)
		"scavenge":
			for t in range(int(days)):
				if not _trip_outcome(n):
					return
		"fix":
			_fix_vehicles(n, hours)

func _tend_crops(n: Npc, all: bool) -> bool:
	var w: World = sim.world
	var hx: int = int(sim.home["x"])
	var hy: int = int(sim.home["y"])
	var did := false
	for y in range(hy - 10, hy + 11):
		for x in range(hx - 10, hx + 11):
			var e: Dictionary = w.ent(x, y)
			if e.get("k", "") != "crop":
				continue
			if int(e["s"]) == 3:
				var yr: Array = Farming.YIELD[e["t"]]
				_put_in_stores(Items.make(e["t"], randi_range(int(yr[0]), int(yr[1])), sim.hour))
				w.set_ent(x, y, {"k": "crop", "t": e["t"], "s": 0, "g": 0.0, "w": 60.0})
				w.set_obj(x, y, Defs.ocell(int(Farming.CROP_OBJ[e["t"]]), 0, 0))     # and sow it again
				did = true
			elif int(e["s"]) < 3 and float(e["w"]) < 50.0:
				e["w"] = 65.0
				did = true
			if did and not all:
				return true
	return did

func _fix_vehicles(n: Npc, hours: float) -> bool:
	var w: World = sim.world
	var hx: int = int(sim.home["x"])
	var hy: int = int(sim.home["y"])
	for y in range(hy - 12, hy + 13):
		for x in range(hx - 12, hx + 13):
			var cell: int = w.obj(x, y)
			if cell == 0 or Defs.o_part(cell) != 0 or not Vehicle.is_vehicle(Defs.o_id(cell)):
				continue
			var e: Dictionary = Vehicle.car_ent(sim, x, y)
			if float(e.get("eng", 1.0)) < 0.95 or float(e.get("tire", 1.0)) < 0.85:
				var scrap: Dictionary = _take_from_stores(func(it): return it["id"] == "scrap_metal")
				if scrap.is_empty():
					return false
				e["eng"] = minf(1.0, float(e.get("eng", 0.5)) + 0.15 * minf(hours, 4.0))
				e["tire"] = minf(0.85, float(e.get("tire", 0.5)) + 0.1 * minf(hours, 4.0))
				return true
	return false

## one scavenging trip: they may come back with something, or not come back
func _trip_outcome(n: Npc) -> bool:
	var risk: float = 0.03 if n.wpn != "" else 0.08
	if n.temper == "cautious": risk *= 0.7
	if randf() < risk:
		list.erase(n)
		sim.say("%s went out scavenging and did not come back." % n.name, Color(1.0, 0.6, 0.5))
		return false
	var found: Array = []
	for k in range(randi_range(1, 3)):
		var id: String = TRIP_FINDS[randi() % TRIP_FINDS.size()]
		var it: Dictionary = Items.make(id, 6 if id == "ammo_9mm" else (8 if id == "nails" else 1), sim.hour)
		if _put_in_stores(it):
			found.append(Items.def(id)["n"])
	if not found.is_empty() and n.pos.distance_to(sim.player.pos) < 40.0:
		sim.say("%s is back: %s, in the stores." % [n.name, ", ".join(found)], Color(0.75, 0.9, 0.7))
	return true

func _return_from_trip(n: Npc) -> void:
	n.away_until = 0.0
	n.pos = n.home
	_trip_outcome(n)

## what a recruit does at your shelter during the day
func _work(n: Npc, dt: float) -> bool:
	var p: Player = sim.player
	if sim.home.is_empty():
		return false
	n._work_t -= dt
	match n.work:
		"guard":
			var hp_: Vector2 = sim.home_pos()
			for z in sim.zombies.list:
				if z.pos.distance_to(hp_) < 9.0 and z.state != Zombie.DOWN:
					if n._work_t <= 0.0:
						n._work_t = 30.0
						sim.say("%s: \"Coming in from the %s!\"" % [n.name, Sim.compass(hp_, z.pos)], Color(1.0, 0.8, 0.6))
					_go(n, z.pos, 2.8, dt)
					return true
			if n.pos.distance_to(hp_) > 1.5:
				_go(n, hp_, 2.4, dt)
				return true
		"farm":
			if n._work_t <= 0.0:
				n._work_t = 20.0
				_tend_crops(n, false)
		"scavenge":
			var hod: float = sim.hour_of_day()
			if hod > 8.0 and hod < 12.0 and n.away_until <= 0.0 and sim.hour - n.leave_h > 20.0 and n.hunger < 70.0:
				n.leave_h = sim.hour
				n.away_until = sim.hour + 6.0
				sim.say("%s heads out to scavenge. Back by evening." % n.name, Color(0.8, 0.85, 0.9))
				return true
		"cook":
			if n._work_t <= 0.0:
				n._work_t = 40.0
				if sim.near_heat(n.pos) or sim.near_heat(sim.home_pos()):
					var raw: Dictionary = _take_from_stores(func(it): return Items.def(it["id"]).has("cook"))
					if not raw.is_empty():
						var done: String = Items.def(raw["id"])["cook"]
						_put_in_stores(Items.make(done, int(raw.get("n", 1)), sim.hour))
		"nurse":
			if n._work_t <= 0.0 and p.pos.distance_to(n.pos) < 4.0:
				n._work_t = 10.0
				for wd in p.wounds:
					if not wd["band"] and float(wd.get("bleed_h", 0.0)) > 0.0:
						var bnd: Dictionary = _take_from_stores(func(it): return it["id"] == "bandage" or it["id"] == "rag")
						if bnd.is_empty() and not Inv.find(p.inv, "bandage").is_empty():
							Inv.split(p.inv, Inv.find(p.inv, "bandage"), 1)
							bnd = {"id": "bandage"}
						if not bnd.is_empty():
							wd["band"] = true
							wd["dirty"] = 0.0
							sim.say("%s dresses your %s." % [n.name, String(Player.PARTS[int(wd["part"])]).to_lower()], Color(0.75, 0.9, 0.7))
						break
		"fix":
			if n._work_t <= 0.0:
				n._work_t = 60.0
				_fix_vehicles(n, 0.5)
	return false

# ------------------------------------------------------------------ traders on the road
const TRADE_GOODS := ["ammo_9mm", "shells", "first_aid_kit", "antibiotics", "car_battery", "gas_can", "seeds_corn", "seeds_wheat", "binoculars",
	"leather_jacket", "boots", "fishing_rod", "salt", "glass_pane", "wire", "suture_kit", "hatchet", "backpack", "canned_beans", "water_bottle"]

func send_trader() -> void:
	var p: Player = sim.player
	if World.level(p.pos.y) != 0:
		return
	for tries in range(30):
		var a: float = randf() * TAU
		var spot: Vector2 = p.pos + Vector2(cos(a), sin(a)) * randf_range(20.0, 28.0)
		if not sim.world.is_loaded(floori(spot.x), floori(spot.y)) or sim.world.bld(floori(spot.x), floori(spot.y)) != 0 or sim.world.blocked(spot.x, spot.y, 0.3):
			continue
		var n: Npc = spawn(Vector2(floorf(spot.x) + 0.5, floorf(spot.y) + 0.5), false)
		n.trader = true
		n.met = true
		n.temper = "generous"
		n.trust = 45.0
		n.stock = []
		for k in range(8):
			n.stock.append(TRADE_GOODS[randi() % TRADE_GOODS.size()])
		n.wpn = "kitchen_knife"
		n.leave_h = sim.hour + 8.0
		n.home = p.pos.lerp(spot, 0.6)
		# often a member of a settlement, travelling between places
		var open_sites: Array = []
		for k3 in sim.factions.sites.keys():
			var st5: Dictionary = sim.factions.sites[k3]
			if not st5["fallen"] and Factions.kind(int(st5["f"])) != Factions.RAIDER: open_sites.append(k3)
		if not open_sites.is_empty() and randf() < 0.6:
			var sk: Vector2i = open_sites[randi() % open_sites.size()]
			n.fac = int(sim.factions.sites[sk]["f"])
			n.site = sk
		n.task = "home"
		sim.say("Someone is coming along the road, pulling a loaded cart.", Color(0.85, 0.85, 0.7))
		return

## what a survivor who is not following anyone does with the day
func routine(n: Npc, dt: float) -> void:
	var w: World = sim.world
	if n.trader:
		if sim.hour > n.leave_h:
			var away: Vector2 = n.pos + (n.pos - sim.player.pos).normalized() * 3.0
			_go(n, away, 2.4, dt)
			if n.pos.distance_to(sim.player.pos) > 34.0:
				list.erase(n)
			return
		if n.pos.distance_to(n.home) > 1.2:
			_go(n, n.home, 2.0, dt)
		return
	if n.recruit:
		var hod0: float = sim.hour_of_day()
		var night0: bool = hod0 >= 22.0 or hod0 < 6.0
		if not night0 and n.fatigue < 85.0 and n.task != "sleep":
			if not _work(n, dt) and n.pos.distance_to(n.home) > 1.5:
				_go(n, n.home, 2.2, dt)       # recruits do not help themselves to your stores
			return
	var hod: float = sim.hour_of_day()
	var night: bool = hod >= 22.0 or hod < 6.0
	match n.task:
		"travel":
			# a patrol or a traveller passing through: walk on, and leave the map once out of sight
			n.task_t -= dt
			_go(n, n.task_pos, 2.3, dt)
			if n.task_t > 1e5 and n.pos.distance_to(n.task_pos) < 1.5:
				n.task = ""                  # moved house: this is home now
			elif (n.pos.distance_to(n.task_pos) < 1.5 or n.task_t <= 0.0) and n.pos.distance_to(sim.player.pos) > 18.0:
				list.erase(n)
			elif n.pos.distance_to(n.task_pos) < 1.5:
				n.task_pos = n.pos + (n.pos - sim.player.pos).normalized() * 10.0
			return
		"sleep":
			n.anim = "s_idle"
			if (not night and n.fatigue < 30.0) or n.fatigue <= 0.0:
				n.task = ""
		"scavenge":
			n.task_t -= dt
			if n.pos.distance_to(n.task_pos) > 1.3 and n.task_t > 0.0:
				_go(n, n.task_pos, 2.4, dt)
			else:
				var tx: int = floori(n.task_pos.x)
				var ty: int = floori(n.task_pos.y)
				if n.task_t > 0.0 and w.has_container(tx, ty) and n.stock.size() < 8:
					var arr: Array = w.container_at(tx, ty)
					for it in arr:
						var cat: String = Items.def(it["id"]).get("cat", "")
						if cat == "food" or cat == "drink" or cat == "med" or cat == "ammo":
							var one: Dictionary = Inv.split(arr, it, 1)      # physically taken: the shelf has one less
							n.stock.append(one["id"])
							w.chunk_at(tx, ty).touched = true
							break
				n.task = "home"
		"home":
			if n.pos.distance_to(n.home) > 1.2:
				_go(n, n.home, 2.4, dt)
			else:
				n.task = ""
		_:
			n.task_t -= dt
			if night or n.fatigue > 85.0:
				if n.pos.distance_to(n.home) > 1.5:
					_go(n, n.home, 2.4, dt)
				else:
					n.task = "sleep"
			elif n.task_t <= 0.0:
				n.task_t = randf_range(20.0, 45.0)
				if n.hunger > 35.0 or n.thirst > 35.0 or n.stock.size() < 4:
					# look for something worth taking within a short walk
					var hx: int = floori(n.pos.x)
					var hy: int = floori(n.pos.y)
					var best := Vector2.ZERO
					var bd := 99.0
					for yy in range(hy - 9, hy + 10):
						for xx in range(hx - 9, hx + 10):
							var cell: int = w.obj(xx, yy)
							if cell == 0 or Defs.o_part(cell) != 0 or not Defs.obj(Defs.o_id(cell)).has("c"):
								continue
							var dd: float = Vector2(xx + 0.5, yy + 0.5).distance_to(n.pos)
							if dd < bd and dd > 1.0 and (Rng.h2(xx, yy, n.id + int(sim.hour)) % 3) == 0:
								bd = dd
								best = Vector2(xx + 0.5, yy + 0.5)
					if bd < 99.0:
						n.task = "scavenge"
						n.task_pos = best
						n.task_t = 25.0

static func trust_word(t: float) -> String:
	if t < 15.0: return "does not trust you"
	if t < 35.0: return "is wary of you"
	if t < 60.0: return "trusts you a little"
	if t < 85.0: return "trusts you"
	return "would follow you anywhere"

# ------------------------------------------------------------------ talking
func options(n: Npc) -> Array:
	var p: Player = sim.player
	var out: Array = []
	if n.state == HOSTILE:
		return out
	var tr: float = n.trust + (sim.factions.rep_of(n.fac) * 0.4 if n.fac >= 0 else 0.0)
	out.append({"label": "Talk to %s" % n.name, "fn": func():
		if not n.met:
			n.met = true
			sim.say("%s: \"You're alive. I'd stopped expecting that.\"" % n.name, Color(0.85, 0.85, 0.7))
		else:
			sim.say("%s: \"%s\"" % [n.name, LINES[randi() % LINES.size()]], Color(0.85, 0.85, 0.7))
		sim.say("%s was a %s, is %s by nature, and %s." % [n.name, n.job, n.temper, trust_word(tr)], Color(0.75, 0.82, 0.9))
		n.trust = minf(100.0, n.trust + 1.0)
		p.bored = maxf(0.0, p.bored - 20.0)
		p.unhappy = maxf(0.0, p.unhappy - 8.0)})
	if n.task == "sleep":
		out.append({"label": "(asleep — talking wakes them)", "fn": func():
			n.task = ""
			n.fatigue = maxf(n.fatigue, 40.0)
			n.trust = maxf(0.0, n.trust - 2.0)})
	if n.state == STAY:
		out.append({"label": "\"Come with me.\"", "fn": func():
			if tr < 35.0:
				sim.say("%s: \"I don't know you well enough for that.\"" % n.name, Color(0.85, 0.85, 0.7))
			elif n.hunger > 85.0:
				sim.say("%s: \"Not until I've eaten something.\"" % n.name, Color(0.85, 0.85, 0.7))
			else:
				n.state = FOLLOW
				sim.say("%s falls in behind you." % n.name, Color(0.75, 0.9, 0.7))})
	else:
		out.append({"label": "\"Wait here.\"", "fn": func():
			n.state = STAY
			n.home = n.pos
			n.task = ""
			sim.say("%s: \"I'll hold this spot.\"" % n.name, Color(0.85, 0.85, 0.7))})
	# what trust buys
	if tr >= 50.0 and n.job == "medic":
		var worst: Dictionary = {}
		for wd in p.wounds:
			if not wd.get("band", false) and float(wd.get("bleed_h", 0.0)) > 0.0: worst = wd
		if not worst.is_empty():
			out.append({"label": "\"Can you look at this wound?\"", "fn": func():
				worst["band"] = true
				worst["dirty"] = 0.0
				worst["heal"] = float(worst.get("heal", 0.0)) * 0.8
				sim.say("%s cleans and dresses it properly." % n.name, Color(0.75, 0.9, 0.7))})
	var teach_skill: String = {"medic": "first_aid", "mechanic": "mechanics", "farmer": "farming", "hunter": "aiming", "cook": "cooking", "guard": "short_blunt"}.get(n.job, "")
	if tr >= 50.0 and teach_skill != "" and not sim.flags.has("taught_%s_%s" % [n.name, teach_skill]):
		out.append({"label": "\"Teach me what you know about %s.\"" % teach_skill.replace("_", " "), "fn": func():
			p.start_action("Learning from %s" % n.name, 20.0, func():
				sim.flags["taught_%s_%s" % [n.name, teach_skill]] = true
				p.add_xp(teach_skill, 160.0)
				p.known[n.job] = true          # and a few things you can only learn by watching
				n.trust = minf(100.0, n.trust + 4.0)
				p.bored = maxf(0.0, p.bored - 30.0)
				sim.say("%s shows you how it is done. (%s)" % [n.name, teach_skill.replace("_", " ").capitalize()], Color(0.6, 0.9, 0.6)))})
	if tr >= 55.0 and not sim.flags.has("npc_tip_%d" % n.id):
		out.append({"label": "\"What do you know about this area?\"", "fn": func():
			var tip: Dictionary = {"id": "survivor_note", "n": 1}
			sim._fill_found_note(tip)
			sim.flags["npc_tip_%d" % n.id] = true
			if tip.has("mx"):
				sim.add_marker(int(tip["mx"]), int(tip["my"]), String(tip.get("lab", "A place")).replace("from a note", "%s told you" % n.name))
				sim.say("%s marks a place on your map." % n.name, Color(0.75, 0.9, 0.7))
			else:
				sim.say("%s: \"Nothing near here worth the walk.\"" % n.name, Color(0.85, 0.85, 0.7))})
	if n.wpn == "":
		for itw in p.inv:
			var dw: Dictionary = Items.def(itw["id"])
			if dw.has("wpn") and dw["cat"] == "weapon" and not is_same(itw, p.weapon):
				var gw: Dictionary = itw
				out.append({"label": "Give them your spare %s" % dw["n"], "fn": func():
					if not p.inv.has(gw): return
					Inv.split(p.inv, gw, 1)
					n.wpn = gw["id"]
					n.trust = minf(100.0, n.trust + 10.0)
					sim.say("%s takes the %s. They will stand and fight now." % [n.name, String(dw["n"]).to_lower()], Color(0.75, 0.9, 0.7))})
				break
	if n.fac >= 0:
		out.append_array(sim.factions.options(n, tr))
	if n.trader:
		out.append({"label": "\"What have you got?\"", "fn": func():
			var names: Array = []
			for sid in n.stock: names.append(Items.def(sid)["n"])
			sim.say("%s's cart: %s. Moving on in %d hours." % [n.name, ", ".join(names), maxi(0, int(n.leave_h - sim.hour))], Color(0.85, 0.85, 0.7))})
	# your shelter
	if not sim.home.is_empty() and not n.recruit and n.fac < 0 and not n.trader and n.state == FOLLOW:
		out.append({"label": "\"Come and live at my shelter.\"", "fn": func():
			if tr < 60.0:
				sim.say("%s: \"Not yet. I don't know you well enough.\"" % n.name, Color(0.85, 0.85, 0.7))
				return
			recruit_to_home(n)
			sim.say("%s: \"All right. I'll %s.\"" % [n.name, WORKS[n.work]], Color(0.75, 0.9, 0.7))})
	if n.recruit:
		for wk in WORKS.keys():
			if wk != n.work:
				var job_k: String = wk
				out.append({"label": "Ask them to %s" % WORKS[wk], "fn": func():
					n.work = job_k
					sim.say("%s: \"I'll %s.\"" % [n.name, WORKS[job_k]], Color(0.85, 0.85, 0.7))})
		out.append({"label": "\"How are things?\"", "fn": func():
			var food := 0
			for st2 in sim.home_stores():
				for it2 in st2[2]:
					if Items.def(it2["id"]).has("hunger") and not Items.def(it2["id"]).has("raw"): food += int(it2.get("n", 1))
			sim.say("%s %s. %s, and %s. %d meals in the stores." % [n.name, "is " + WORKS[n.work].replace("keep", "keeping").replace("tend", "tending").replace("go out", "going out").replace("cook", "cooking").replace("look after", "looking after"), "Fed" if n.hunger < 50.0 else "Hungry", trust_word(n.trust), food], Color(0.85, 0.85, 0.7))})
	# barter: one of theirs for one of yours. They want things that keep a person alive.
	var offer: Dictionary = {}
	for it0 in p.inv:
		var c0: String = Items.def(it0["id"]).get("cat", "")
		if (c0 == "food" or c0 == "drink" or c0 == "med" or c0 == "ammo" or (n.trader and (c0 == "tool" or c0 == "material" or c0 == "weapon"))) and not is_same(it0, p.weapon) and Items.fresh_state(it0, sim.hour) < 2 and not n.stock.has(it0["id"]):
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
				n.trust = minf(100.0, n.trust + 5.0)
				sim.factions.add_rep(n.fac, 2.0)
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
				n.trust = minf(100.0, n.trust + (15.0 if n.hunger > 40.0 or n.temper != "wary" else 8.0))
				if not n.gift:
					n.gift = true
					var gifts: Array = ["bandage", "ammo_9mm", "painkillers", "battery", "matches", "duct_tape"]
					var g: String = gifts[randi() % gifts.size()]
					Inv.add_new(p.inv, g, 6 if g == "ammo_9mm" else 1, sim.hour)
					sim.say("%s presses something into your hand: %s." % [n.name, Items.def(g)["n"]], Color(0.75, 0.9, 0.7))
				else:
					sim.say("%s: \"Thank you.\"" % n.name, Color(0.85, 0.85, 0.7))})
			break
	out.append_array(social_options(n, tr))
	return out
