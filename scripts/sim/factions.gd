class_name Factions
extends RefCounted
## Groups of survivors, the places they hold, what they think of you, and the work they offer.
## A settlement is a real place with real people in it, plus a small ledger (food, morale, headcount)
## that keeps running while you are away.

const OPEN := 0        # will talk and trade
const WARY := 1        # keeps strangers at arm's length
const RAIDER := 2      # takes what it wants
const LIST := [["The Millbrook Commune", OPEN], ["Saint Anne's Shelter", OPEN], ["The Wardens", WARY], ["Harrow Road Crew", RAIDER],
	["The Orchard Families", OPEN], ["Lockhouse", WARY], ["The Ashmen", RAIDER], ["The Ferrymen", OPEN]]
const SITE_KINDS := ["farm", "cabin", "warehouse", "school", "firestation", "police", "clinic", "diner"]
const WANTS := [["canned_beans", 3, "food"], ["bandage", 2, "med"], ["plank", 6, "build"], ["nails", 20, "build"], ["disinfectant", 1, "med"], ["seeds_potato", 2, "food"], ["water_bottle", 2, "food"]]
const REWARDS := ["ammo_9mm", "first_aid_kit", "canned_beans", "battery", "duct_tape", "painkillers"]

var sim: Sim
var rep: Dictionary = {}          # faction index -> -100 .. 100
var sites: Dictionary = {}        # Vector2i region -> settlement record
var tasks: Array = []             # {"site", "f", "want", "n", "due", "state": open|done|expired|failed, "kind"}
var _raid_h := 0.0

func _init(s: Sim) -> void:
	sim = s

static func fname(f: int) -> String:
	return LIST[f][0]

static func kind(f: int) -> int:
	return LIST[f][1]

func rep_of(f: int) -> float:
	return float(rep.get(f, 0.0))

func add_rep(f: int, d: float) -> void:
	if f < 0:
		return
	rep[f] = clampf(rep_of(f) + d, -100.0, 100.0)

static func rep_word(r: float) -> String:
	if r <= -40.0: return "hunted"
	if r < -15.0: return "unwelcome"
	if r < 15.0: return "a stranger"
	if r < 40.0: return "known"
	if r < 70.0: return "welcome"
	return "one of them"

## where a region's settlement would be, if it has one (deterministic from the seed)
func site_for(rx: int, ry: int) -> Dictionary:
	var hv: int = Rng.h2(rx, ry, sim.seed_v + 4711)
	if (rx != 0 or ry != 0) and hv % 100 >= 65:
		return {}
	var cands: Array = []
	for lot in sim.world.gen.region(rx, ry)["lots"]:
		if SITE_KINDS.has(String(lot["k"])):
			cands.append(lot)
	if cands.is_empty():
		return {}
	var lot2: Dictionary = cands[(hv >> 8) % cands.size()]
	var r: Rect2i = lot2["r"]
	var f: int = (hv >> 16) % LIST.size()
	if rx == 0 and ry == 0 and kind(f) == RAIDER:
		f = (f + 1) % LIST.size()         # nobody starts next door to raiders
	return {"c": r.get_center(), "f": f, "k": lot2["k"]}

func found(key: Vector2i, center: Vector2i, f: int, pop: int) -> Dictionary:
	var s := {"f": f, "name": "%s at the %s" % [fname(f), "old place"], "x": center.x, "y": center.y, "food": float(pop) * 6.0, "morale": 60.0, "pop": pop,
		"born": sim.hour, "fallen": false, "met": false, "med": 2, "built": 0}
	sites[key] = s
	return s

## first time the chunk holding a site is entered: the people are put there
func on_chunk_first(c: Chunk) -> void:
	if World.level(c.cy * 16.0) != 0:
		return
	var rx: int = WorldGen.fdiv(c.cx * 16, WorldGen.REGION)
	var ry: int = WorldGen.fdiv(c.cy * 16, WorldGen.REGION)
	var key := Vector2i(rx, ry)
	if sites.has(key):
		return
	var st: Dictionary = site_for(rx, ry)
	if st.is_empty():
		return
	var ctr: Vector2i = st["c"]
	if (ctr.x >> 4) != c.cx or (ctr.y >> 4) != c.cy:
		return
	var spots: Array = []
	for i in range(256):
		var x: int = c.cx * 16 + (i & 15)
		var y: int = c.cy * 16 + (i >> 4)
		if c.ground[i] != Defs.G_VOID and c.obj[i] == 0 and not Defs.ground_is_water(c.ground[i]) and Vector2(x - ctr.x, y - ctr.y).length() < 7.0:
			spots.append(Vector2(x + 0.5, y + 0.5))
	if spots.size() < 3:
		return
	var f: int = st["f"]
	var pop: int = 3 + Rng.h2(ctr.x, ctr.y, 9) % 3
	var s: Dictionary = found(key, ctr, f, pop)
	s["name"] = "%s, at the %s" % [fname(f), String(st["k"]).replace("_", " ")]
	for k in range(pop):
		var sp: Vector2 = spots[(Rng.h2(ctr.x + k, ctr.y, 31) % spots.size())]
		var n = sim.npcs.spawn(sp, kind(f) == RAIDER)
		enlist(n, f, key)
		if k == 0: n.job = "guard"

func enlist(n, f: int, key: Vector2i) -> void:
	n.fac = f
	n.site = key
	if kind(f) == WARY: n.trust -= 8.0
	if kind(f) == RAIDER:
		n.state = NpcSim.HOSTILE
		n.wpn = "kitchen_knife"

func site_of(n) -> Dictionary:
	if n.fac < 0 or not sites.has(n.site):
		return {}
	return sites[n.site]

func member_died(n, by_player: bool) -> void:
	var s: Dictionary = site_of(n)
	if by_player:
		add_rep(n.fac, -40.0)
	if s.is_empty():
		return
	s["pop"] = maxi(0, int(s["pop"]) - 1)
	s["morale"] = maxf(0.0, float(s["morale"]) - 12.0)
	_check_fallen(n.site)

func _check_fallen(key: Vector2i) -> void:
	var s: Dictionary = sites[key]
	if int(s["pop"]) <= 0 and not s["fallen"]:
		s["fallen"] = true
		for t in tasks:
			if t["site"] == key and t["state"] == "open":
				t["state"] = "failed"
		if s["met"]:
			sim.say("Word reaches you: %s is gone." % s["name"], Color(1.0, 0.75, 0.55))

## the ledger: runs for every known settlement whether you are there or not
func tick(dh: float) -> void:
	for key in sites.keys():
		var s: Dictionary = sites[key]
		if s["fallen"]:
			continue
		var pop: float = float(int(s["pop"]))
		var made: float = (0.75 if kind(int(s["f"])) == OPEN else 0.5) + 0.05 * float(int(s.get("built", 0)))
		s["food"] = clampf(float(s["food"]) + pop * (made - 1.0) * dh / 24.0, 0.0, 400.0)
		if float(s["food"]) <= 0.0:
			s["morale"] = maxf(0.0, float(s["morale"]) - dh * 1.2)
		elif float(s["food"]) > pop * 3.0:
			s["morale"] = minf(100.0, float(s["morale"]) + dh * 0.15)
		if float(s["morale"]) <= 0.0 and sim.rng.randf() < dh / 36.0:
			# someone walks out, or does not wake up
			s["pop"] = int(s["pop"]) - 1
			s["morale"] = 15.0
			_remove_one_member(key)
			_check_fallen(key)
	for t in tasks:
		if t["state"] == "open" and sim.hour > float(t["due"]):
			t["state"] = "expired"
			add_rep(int(t["f"]), -5.0)
			sim.say("You are too late: %s stopped waiting for the %s." % [fname(int(t["f"])), Items.def(t["want"])["n"]], Color(1.0, 0.8, 0.6))
	# raiders do what raiders do, to whoever is nearest
	_raid_h -= dh
	if _raid_h <= 0.0:
		_raid_h = sim.rng.randf_range(40.0, 90.0)
		_raid()

func _remove_one_member(key: Vector2i) -> void:
	for n in sim.npcs.list:
		if n.fac >= 0 and n.site == key and n.state != NpcSim.FOLLOW:
			sim.npcs.list.erase(n)
			return

func _raid() -> void:
	var raiders: Array = []
	var victims: Array = []
	for key in sites.keys():
		var s: Dictionary = sites[key]
		if s["fallen"]: continue
		if kind(int(s["f"])) == RAIDER: raiders.append(key)
		else: victims.append(key)
	# your shelter is a target too, if a raider camp is near enough
	if not raiders.is_empty() and not sim.home.is_empty():
		var hk := Vector2i(WorldGen.fdiv(int(sim.home["x"]), WorldGen.REGION), WorldGen.fdiv(int(sim.home["y"]), WorldGen.REGION))
		for rk0 in raiders:
			if Vector2(rk0 - hk).length() < 2.9 and sim.rng.randf() < 0.5:
				raid_shelter(rk0)
				return
	if raiders.is_empty() or victims.is_empty():
		return
	var rk: Vector2i = raiders[sim.rng.randi() % raiders.size()]
	var best: Vector2i = victims[0]
	for v in victims:
		if Vector2(v - rk).length() < Vector2(best - rk).length(): best = v
	if Vector2(best - rk).length() > 2.9:
		return
	var s2: Dictionary = sites[best]
	s2["food"] = float(s2["food"]) * 0.65
	s2["morale"] = maxf(0.0, float(s2["morale"]) - 15.0)
	sites[rk]["food"] = float(sites[rk]["food"]) + float(s2["food"]) * 0.3
	if s2["met"]:
		sim.say("Smoke over %s. %s came in the night and took what they wanted." % [s2["name"], fname(int(sites[rk]["f"]))], Color(1.0, 0.75, 0.55))

## raiders come for your shelter: guards may drive them off; otherwise they take from the stores
func raid_shelter(rk: Vector2i) -> String:
	var guards: Array = []
	for n in sim.npcs.list:
		if n.recruit and n.work == "guard" and n.away_until <= 0.0:
			guards.append(n)
	var held: bool = sim.rng.randf() < 0.25 * float(guards.size()) + (0.25 if sim.player.pos.distance_to(sim.home_pos()) < 15.0 else 0.0)
	var name: String = fname(int(sites[rk]["f"]))
	if held:
		for g in guards:
			if sim.rng.randf() < 0.3:
				g.hp = maxf(5.0, g.hp - sim.rng.randf_range(15.0, 40.0))
		sim.say("%s tried your shelter in the night. Your people drove them off." % name, Color(0.75, 0.9, 0.7))
		return "held"
	var taken := 0
	for st in sim.home_stores():
		var arr: Array = st[2]
		for it in arr.duplicate():
			var c0: String = Items.def(it["id"]).get("cat", "")
			if (c0 == "food" or c0 == "drink" or c0 == "med" or c0 == "ammo") and sim.rng.randf() < 0.5:
				arr.erase(it)
				taken += int(it.get("n", 1))
		sim.world.chunk_at(int(st[0]), int(st[1])).touched = true
	sites[rk]["food"] = float(sites[rk]["food"]) + float(taken) * 0.5
	sim.say("%s raided your shelter while it was unguarded. %d things gone from the stores." % [name, taken], Color(1.0, 0.6, 0.45))
	return "robbed"

# ------------------------------------------------------------------ what a member offers
func open_task(key: Vector2i) -> Dictionary:
	for t in tasks:
		if t["site"] == key and t["state"] == "open":
			return t
	return {}

func options(n, tr: float) -> Array:
	var out: Array = []
	var s: Dictionary = site_of(n)
	if s.is_empty() or s["fallen"]:
		return out
	var p: Player = sim.player
	var f: int = n.fac
	var key: Vector2i = n.site
	var col := Color(0.85, 0.85, 0.7)
	if not s["met"]:
		s["met"] = true
		sim.add_marker(int(s["x"]), int(s["y"]), String(s["name"]))
		sim.say("This is %s. Marked on your map." % s["name"], Color(0.75, 0.9, 0.7))
	out.append({"label": "Ask about %s" % fname(f), "fn": func():
		var days: float = float(s["food"]) / maxf(1.0, float(int(s["pop"])))
		sim.say("%d people. Food for about %d days. Spirits are %s. To them you are %s." % [int(s["pop"]), int(days),
			"high" if float(s["morale"]) > 65.0 else ("holding" if float(s["morale"]) > 30.0 else "breaking"), rep_word(rep_of(f))], col)})
	# giving to the stores
	for it in p.inv:
		var d: Dictionary = Items.def(it["id"])
		if d.has("hunger") and not d.has("raw") and Items.fresh_state(it, sim.hour) < 2 and not is_same(it, p.weapon):
			var food: Dictionary = it
			out.append({"label": "Give %s to their stores" % d["n"], "fn": func():
				if not p.inv.has(food): return
				Inv.split(p.inv, food, 1)
				s["food"] = float(s["food"]) + float(d["hunger"]) / 30.0
				s["morale"] = minf(100.0, float(s["morale"]) + 1.5)
				add_rep(f, 4.0)
				sim.say("%s: \"That will be remembered.\"" % n.name, col)})
			break
	# work
	var t: Dictionary = open_task(key)
	if t.is_empty():
		out.append({"label": "\"Is there anything you need?\"", "fn": func():
			if rep_of(f) < -15.0:
				sim.say("%s: \"Not from you.\"" % n.name, col)
				return
			var w: Array = WANTS[sim.rng.randi() % WANTS.size()]
			var nt := {"site": key, "f": f, "want": w[0], "n": int(w[1]), "kind": w[2], "due": sim.hour + 72.0, "state": "open"}
			tasks.append(nt)
			sim.say("%s: \"%d %s, inside three days. We would not forget it.\"" % [n.name, int(w[1]), Items.def(w[0])["n"]], col)})
	else:
		var have: int = Inv.count(p.inv, t["want"])
		var left: int = int(float(t["due"]) - sim.hour)
		if have >= int(t["n"]):
			out.append({"label": "Hand over %d %s" % [int(t["n"]), Items.def(t["want"])["n"]], "fn": func():
				if Inv.count(p.inv, t["want"]) < int(t["n"]) or t["state"] != "open": return
				Inv.take(p.inv, t["want"], int(t["n"]))
				t["state"] = "done"
				add_rep(f, 15.0)
				n.trust = minf(100.0, n.trust + 10.0)
				match String(t["kind"]):
					"food": s["food"] = float(s["food"]) + float(int(t["n"])) * 0.8
					"med": s["med"] = int(s["med"]) + int(t["n"])
					"build": s["built"] = int(s.get("built", 0)) + 1
				s["morale"] = minf(100.0, float(s["morale"]) + 8.0)
				var rw: String = REWARDS[sim.rng.randi() % REWARDS.size()]
				Inv.add_new(p.inv, rw, 12 if rw == "ammo_9mm" else 1, sim.hour)
				sim.say("%s: \"You came back.\" They give you %s." % [n.name, Items.def(rw)["n"]], Color(0.75, 0.9, 0.7))})
		else:
			out.append({"label": "(they are waiting for %d %s — %d h left, you have %d)" % [int(t["n"]), Items.def(t["want"])["n"], maxi(0, left), have], "fn": func(): pass})
	# shelter
	out.append({"label": "\"Could I sleep here tonight?\"", "fn": func():
		if rep_of(f) + tr * 0.3 < 18.0:
			sim.say("%s: \"We don't know you. Not yet.\"" % n.name, col)
		else:
			sim.say("%s: \"There's a corner. Someone will be on watch.\"" % n.name, col)
			sim.start_sleep(1.0)})
	return out

func save() -> Dictionary:
	return {"rep": rep, "sites": sites, "tasks": tasks, "raid": _raid_h}

func load(d: Dictionary) -> void:
	rep = d.get("rep", {})
	sites = d.get("sites", {})
	tasks = d.get("tasks", [])
	_raid_h = d.get("raid", 50.0)
