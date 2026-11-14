class_name Sim
extends RefCounted
## The whole simulation: world, player, zombies, clock, weather, utilities, noise.
## No scene-tree access — it can run headless and is what the save file describes.

const START_HOUR := 9.0

var world: World
var player: Player
var zombies: ZombieSim
var npcs: NpcSim
var factions: Factions
var animals: AnimalSim
var rng := RandomNumberGenerator.new()
var seed_v := 0
var hour := START_HOUR           # absolute game hours since midnight of day 1
var time_scale := 1.0
var settings := {"zombies": 1.0, "loot": 1.0, "day_min": 60.0, "infection": true, "god": false, "respawn": false, "zspeed": 1.0,
	"xp": 1.0, "util": 1, "season": 0, "flyover": 1, "kit": false, "growth": 1.0, "dark": 1.0, "guide": true, "meta": true, "events": 1.0}
var weather := {"cloud": 0.3, "rain": 0.0, "fog": 0.0, "temp": 21.0, "wind": 0.2}
var power_off_h := 0.0
var water_off_h := 0.0
var noises: Array = []           # [pos, radius, ttl, from_zombie]
var fx: Array = []               # transient events for renderer / audio
var log: Array = []              # [text, color, age]
var ui_events: Array = []        # requests for the UI layer
var safe_pos := Vector2.ZERO
var safe_radius := 16.0
var safe_bld := 0
var sleep_quality := 1.0
var alarms: Array = []           # [pos, seconds left]
var alarms_done: Dictionary = {}
var generators: Array = []       # Vector2i of running generators (loaded chunks)
var banks: Array = []            # Vector2i of charged battery banks (loaded chunks)
var pipes: Dictionary = {}       # building uid -> water units left in its pipes after the mains fail
const GEN_RANGE := 14
const GEN_CAP := 6               # appliances one generator carries before it strains
const BANK_RANGE := 10
const SUB_RANGE := 48             # a repaired substation feeds the streets around it
var substations: Array = []       # Vector2i of substations carrying power (loaded chunks)
const BANK_MAX := 60.0           # load-hours a bank holds
var fires: Array = []            # Vector2i of lit campfires (loaded chunks)
var spikes: Array = []           # Vector2i spike traps near the player
var _spike_t := 0.0
var lamps: Array = []            # Vector2i light-emitting objects near the player
var dead := false
var vehicle: Vehicle = null       # the car being driven, if any
var burning: Dictionary = {}      # Vector2i tile -> seconds of fire left
var brake := false
var _fire_t := 0.0
var lives := 0                   # survivors lost in this world so far
var speed := 1                   # time control: simulation steps per frame (1, 2 or 4)
var flags: Dictionary = {}       # one-off facts (tutorial progress, story triggers)
var guide_i := 0                 # current tutorial objective (-1 = finished / off)
var fly_next_h := 1e12           # absolute hour the next flyover starts
var fly_end_h := 0.0
var fly_active := false
var fly_track := Vector2.ZERO
var _fly_t := 0.0
var _fly_lost := 0.0
var _fly_pack_t := 0.0
var _meta_t := 200.0
var _guide_inv := 0
var view_loaded: Array = []      # chunks loaded since the renderer last looked
var _slow_t := 0.0
var _weather_h := 0.0
var _ent_h := 0.0
var _power_said := false
var _water_said := false
var _last_bld := 0

func _init(world_seed: int) -> void:
	seed_v = world_seed
	rng.seed = Rng.h(world_seed + 5)
	world = World.new(world_seed)
	world.hour = hour
	player = Player.new(self)
	zombies = ZombieSim.new(self)
	npcs = NpcSim.new(self)
	factions = Factions.new(self)
	animals = AnimalSim.new(self)
	world.on_unload = func(c: Chunk):
		zombies.on_chunk_unload(c)
		npcs.on_chunk_unload(c)
		animals.on_chunk_unload(c)
	var r: RandomNumberGenerator = Rng.make(world_seed + 99)
	power_off_h = r.randf_range(5.0, 16.0) * 24.0
	water_off_h = r.randf_range(6.0, 20.0) * 24.0

const GUIDE := [
	["move", "Objective: walk around — drag in the lower-left of the screen"],
	["door", "Objective: open a door — face it and tap USE"],
	["loot", "Objective: search a container and take something (USE, or BAG)"],
	["equip", "Objective: equip a weapon — BAG, tap the item, Equip"],
	["eat", "Objective: eat or drink something from your BAG"],
	["kill", "Objective: put down one of the infected (ATTACK)"],
	["craft", "Objective: make something — MAKE (try ripping a sheet into rags)"],
	["sleep", "Objective: when you are tired, sleep in a bed (USE)"],
]

## turn the sandbox options into concrete world parameters (new games only)
func apply_settings() -> void:
	var r: RandomNumberGenerator = Rng.make(seed_v + 99)
	match int(settings["util"]):
		0:
			power_off_h = r.randf_range(1.0, 5.0) * 24.0
			water_off_h = r.randf_range(1.0, 6.0) * 24.0
		1:
			power_off_h = r.randf_range(5.0, 16.0) * 24.0
			water_off_h = r.randf_range(6.0, 20.0) * 24.0
		2:
			power_off_h = r.randf_range(20.0, 45.0) * 24.0
			water_off_h = r.randf_range(22.0, 50.0) * 24.0
		_:
			power_off_h = 1e12
			water_off_h = 1e12
	match int(settings["flyover"]):
		0: fly_next_h = 1e12
		_: fly_next_h = r.randf_range(4.0, 8.0) * 24.0 + r.randf_range(9.0, 17.0)
	guide_i = 0 if settings.get("guide", true) else -1
	world.growth = float(settings.get("growth", 1.0))

## can a person standing here walk out of the building? doors count as passable unless barricaded,
## windows and walls do not. (tile-level search; used to make sure nobody spawns sealed in)
func can_escape(pos: Vector2) -> bool:
	var start := Vector2i(floori(pos.x), floori(pos.y))
	var seen := {start: true}
	var stack: Array = [start]
	var n := 0
	while not stack.is_empty() and n < 3000:
		var c: Vector2i = stack.pop_back()
		n += 1
		if world.bld(c.x, c.y) == 0:
			return true
		for d in [Vector2i(1, 0), Vector2i(-1, 0), Vector2i(0, 1), Vector2i(0, -1)]:
			var t: Vector2i = c + d
			if seen.has(t) or world.tile_blocked(t.x, t.y):
				continue
			var side: int = 1 if d.x != 0 else 0
			var ex: int = c.x + (1 if d.x > 0 else 0)
			var ey: int = c.y + (1 if d.y > 0 else 0)
			var wid: int = world.wall(ex, ey, side)
			if wid != 0:
				var shape: int = wid & 3
				var planked: bool = (world.edge_state(ex, ey, side) & Defs.ES_PLANK_MASK) != 0
				if shape == Defs.WS_WINDOW or (shape == Defs.WS_SOLID and not Defs.wall_is_fence(wid)) or (shape == Defs.WS_DOOR and planked):
					continue
			seen[t] = true
			stack.append(t)
	return false

## the nearest open outdoor spot (used when somebody is stuck)
func outside_spot(pos: Vector2) -> Vector2:
	world.stream(pos, 2, 999)
	for r in range(1, 30):
		for dy in range(-r, r + 1):
			for dx in range(-r, r + 1):
				if maxi(absi(dx), absi(dy)) != r:
					continue
				var t := Vector2(floorf(pos.x) + dx + 0.5, floorf(pos.y) + dy + 0.5)
				if world.bld(floori(t.x), floori(t.y)) == 0 and not world.blocked(t.x, t.y, Player.R) and not world.blocked(t.x + 0.4, t.y, Player.R) and not world.blocked(t.x, t.y + 0.4, Player.R):
					return t
	return pos

## the player is stuck: put them on open ground outside, without it counting as a way to cheat
func unstick() -> void:
	if vehicle != null:
		return
	player.cancel_action()
	player.pos = outside_spot(player.pos)
	safe_pos = player.pos
	say("You find your way out.", Color(0.8, 0.85, 0.9))

## place the player in a building of the chosen kind near the starting town
func new_game(occupation: String, trait_list: Array = [], start_kind: String = "house") -> void:
	apply_settings()
	var st: Dictionary = world.gen.find_start(start_kind)
	player.pos = st["pos"]
	world.stream(player.pos, 2, 999)
	if not can_escape(player.pos):
		player.pos = outside_spot(player.pos)      # never begin sealed in
	safe_pos = player.pos
	player.look = [rng.randi() % 4, rng.randi() % 10, rng.randi() % 6, rng.randi() % 6]
	player.setup_occupation(occupation, trait_list)
	player.pname = String(settings.get("pname", ""))
	world.loot_mult = float(settings["loot"]) * player.tmod("loot")
	world.stream(player.pos, 2, 999)
	safe_bld = world.bld(floori(player.pos.x), floori(player.pos.y))
	alarms_done[safe_bld] = true
	if settings.get("kit", false):
		for it in [["baseball_bat", 1], ["school_bag", 1], ["water_bottle", 1], ["canned_beans", 2], ["can_opener", 1], ["bandage", 2]]:
			Inv.add_new(player.inv, it[0], it[1], hour)
		player.bag = Inv.find(player.inv, "school_bag")
		if player.weapon.is_empty():
			player.weapon = Inv.find(player.inv, "baseball_bat")
	_guide_inv = player.inv.size()
	_process_world_events()
	say("Day 1. The broadcasts have stopped. Find food, water and a weapon.", Color(0.9, 0.85, 0.7))

# ------------------------------------------------------------------ helpers
func day() -> int:
	return int(hour / 24.0) + 1

func hour_of_day() -> float:
	return fposmod(hour, 24.0)

func clock_text() -> String:
	var h: float = hour_of_day()
	return "Day %d  %02d:%02d" % [day(), int(h), int((h - floorf(h)) * 60.0)]

func underground() -> bool:
	return World.level(player.pos.y) == 1

# ------------------------------------------------------------------ fire
func flammability(x: int, y: int) -> float:
	var g: int = world.ground(x, y)
	if g == Defs.G_VOID or Defs.ground_is_water(g):
		return 0.0
	var f := 0.0
	if g == Defs.G_WOOD or g == Defs.G_WOOD_DARK or g == Defs.G_PLANK or g == Defs.G_CARPET_RED or g == Defs.G_CARPET_BLUE or g == Defs.G_CARPET_BEIGE: f = 0.5
	elif g == Defs.G_GRASS or g == Defs.G_GRASS_DARK or g == Defs.G_FOREST: f = 0.22
	var o: int = Defs.o_id(world.obj(x, y))
	if o != 0:
		if o <= Defs.O_REEDS or o == Defs.O_HAY or o == Defs.O_WEEDS: f = maxf(f, 0.7)
		elif o >= Defs.O_FRIDGE and o != Defs.O_STOVE and o != Defs.O_BATHTUB and o != Defs.O_TOILET: f = maxf(f, 0.6)
	for side in range(2):
		var wid: int = world.wall(x, y, side)
		if wid != 0:
			var tex: int = Defs.wall_tex(wid)
			if tex == Defs.WT_SIDING or tex == Defs.WT_PLANK or tex == Defs.WT_LOG or tex == Defs.WT_PICKET or tex == Defs.WT_HEDGE or tex == Defs.WT_PLASTER:
				f = maxf(f, 0.45)
	return f * (1.0 - float(weather["rain"]) * (0.8 if world.bld(x, y) == 0 else 0.0))

func ignite(x: int, y: int, strength: float = 1.0) -> void:
	if burning.size() > 160 or not world.is_loaded(x, y):
		return
	var k := Vector2i(x, y)
	if not burning.has(k):
		burning[k] = rng.randf_range(10.0, 22.0) * strength
		world.notify(x, y)

func _tick_fire(dt: float) -> void:
	if burning.is_empty():
		return
	_fire_t -= dt
	var step: bool = _fire_t <= 0.0
	if step:
		_fire_t = 1.0
	for k in burning.keys():
		burning[k] = float(burning[k]) - dt
		var tile: Vector2i = k
		if step:
			if not fires.has(tile):
				fires.append(tile)
			noise(Vector2(tile.x + 0.5, tile.y + 0.5), 7.0)
			emit_fx("fire", Vector2(tile.x + 0.5, tile.y + 0.5))
			for d in [Vector2i(1, 0), Vector2i(-1, 0), Vector2i(0, 1), Vector2i(0, -1)]:
				var n: Vector2i = tile + d
				if not burning.has(n) and randf() < flammability(n.x, n.y) * 0.16:
					ignite(n.x, n.y)
			# whatever stands in the flames burns
			if player.alive and vehicle == null and absf(player.pos.x - tile.x - 0.5) < 0.6 and absf(player.pos.y - tile.y - 0.5) < 0.6:
				player.hurt(6.0, "Burned to death")
				if randf() < 0.35:
					player.add_wound(Rng.pick_weighted(rng, Player.HIT_WEIGHTS_LOW), "burn", "fire")
			for z in zombies.list.duplicate():
				if absf(z.pos.x - tile.x - 0.5) < 0.6 and absf(z.pos.y - tile.y - 0.5) < 0.6:
					zombies.damage(z, 22.0, z.pos, 0.0, false, false)
		if float(burning[k]) <= 0.0:
			burning.erase(k)
			fires.erase(tile)
			# what is left behind
			var cell: int = world.obj(tile.x, tile.y)
			if cell != 0 and flammability(tile.x, tile.y) > 0.0:
				var oid: int = Defs.o_id(cell)
				world.remove_object(tile.x, tile.y)
				if oid >= Defs.O_TREE_OAK and oid <= Defs.O_TREE_BIRCH:
					world.set_obj(tile.x, tile.y, Defs.O_TREE_DEAD)
			for side in range(2):
				var wid: int = world.wall(tile.x, tile.y, side)
				if wid != 0:
					var tex: int = Defs.wall_tex(wid)
					if tex == Defs.WT_SIDING or tex == Defs.WT_PLANK or tex == Defs.WT_LOG or tex == Defs.WT_PICKET or tex == Defs.WT_HEDGE:
						world.set_wall(tile.x, tile.y, side, 0)
			var g: int = world.ground(tile.x, tile.y)
			if Defs.ground_is_natural(g) or g == Defs.G_WOOD or g == Defs.G_WOOD_DARK or g == Defs.G_PLANK or g == Defs.G_CARPET_RED or g == Defs.G_CARPET_BLUE or g == Defs.G_CARPET_BEIGE:
				world.set_ground(tile.x, tile.y, Defs.G_DIRT)

## 0 = deep night, 1 = full day
func daylight() -> float:
	if underground():
		return 0.1
	var h: float = hour_of_day()
	var v := 0.0
	if h >= 7.0 and h <= 18.5: v = 1.0
	elif h > 5.0 and h < 7.0: v = (h - 5.0) / 2.0
	elif h > 18.5 and h < 21.0: v = 1.0 - (h - 18.5) / 2.5
	return v * (1.0 - float(weather["cloud"]) * 0.25)

func has_power(x: int, y: int) -> bool:
	if world.ent(x, y).get("off", false):
		return false                   # switched off at the appliance
	if hour < power_off_h:
		return true
	for g in generators:
		if absi(g.x - x) <= GEN_RANGE and absi(g.y - y) <= GEN_RANGE:
			return true
	for bk in banks:
		if absi(bk.x - x) <= BANK_RANGE and absi(bk.y - y) <= BANK_RANGE:
			return true
	for ss in substations:
		if absi(ss.x - x) <= SUB_RANGE and absi(ss.y - y) <= SUB_RANGE:
			return true
	return false

## put a dead substation back on line: days of grid power for the streets around it, and a hum they can hear
func repair_substation(x: int, y: int) -> bool:
	var e: Dictionary = world.ent(x, y)
	if hour < power_off_h or hour < float(e.get("until", 0.0)):
		return false
	e["k"] = "substation"
	e["until"] = hour + rng.randf_range(5.0, 9.0) * 24.0
	e["said"] = 0
	world.set_ent(x, y, e)
	substations.append(Vector2i(x, y))
	world.chunk_at(x, y).touched = true
	noise(Vector2(x + 0.5, y + 0.5), 20.0)
	return true

const APPLIANCES := [Defs.O_FRIDGE, Defs.O_FREEZER, Defs.O_STOVE, Defs.O_LAMP, Defs.O_TV, Defs.O_WASHER, Defs.O_GAS_PUMP, Defs.O_VENDING]

## appliances switched on within a square around (x, y)
func loads_near(x: int, y: int, r: int) -> int:
	var n := 0
	for cy in range((y - r) >> 4, ((y + r) >> 4) + 1):
		for cx in range((x - r) >> 4, ((x + r) >> 4) + 1):
			var c: Chunk = world.chunk(cx, cy)
			if c == null:
				continue
			for i in range(256):
				var o: int = c.obj[i]
				if o == 0 or Defs.o_part(o) != 0 or not APPLIANCES.has(o & 1023):
					continue
				var ax: int = cx * 16 + (i & 15)
				var ay: int = cy * 16 + (i >> 4)
				if absi(ax - x) <= r and absi(ay - y) <= r and not c.ents.get(i, {}).get("off", false):
					n += 1
	return n

func has_water() -> bool:
	return hour < water_off_h

## after the mains fail a house's pipes still hold what was in them, once
func pipe_water(b: int) -> int:
	if has_water():
		return 999
	if b == 0:
		return 0
	if not pipes.has(b):
		pipes[b] = 12 + Rng.h2(b, 7, seed_v) % 14
	return int(pipes[b])

func draw_pipe(b: int, units: int) -> int:
	if has_water():
		return units
	var have: int = pipe_water(b)
	var took: int = mini(have, units)
	pipes[b] = have - took
	return took

func near_fire(p: Vector2) -> bool:
	for f in fires:
		if absf(f.x + 0.5 - p.x) < 2.6 and absf(f.y + 0.5 - p.y) < 2.6:
			return true
	return false

func near_workbench(p: Vector2) -> bool:
	var px: int = floori(p.x)
	var py: int = floori(p.y)
	for dy in range(-2, 3):
		for dx in range(-2, 3):
			if Defs.o_id(world.obj(px + dx, py + dy)) == Defs.O_WORKBENCH:
				return true
	return false

## other workstations within two steps: "kiln", "forge"
func stations(p: Vector2) -> Array:
	var out: Array = []
	var px: int = floori(p.x)
	var py: int = floori(p.y)
	for dy in range(-2, 3):
		for dx in range(-2, 3):
			var id: int = Defs.o_id(world.obj(px + dx, py + dy))
			if id == Defs.O_KILN and not out.has("kiln"): out.append("kiln")
			elif id == Defs.O_FORGE and not out.has("forge"): out.append("forge")
	return out

## does the building at this tile have an armed alarm the player has not dealt with yet
func alarm_armed(x: int, y: int) -> bool:
	var b: int = world.bld(x, y)
	if b == 0 or alarms_done.has(b) or not has_power(x, y):
		return false
	var bt: String = world.btype_at(x, y)
	if bt == "cellar" or bt == "camp" or bt == "stash":
		return false
	var chance: int = 6 if (bt == "house" or bt == "cabin" or bt == "farm") else 18
	return (Rng.h(b + seed_v) % 100) < chance

static func compass(from: Vector2, to: Vector2) -> String:
	var d: Vector2 = to - from
	var ang: float = atan2(d.x - d.y, -(d.x + d.y))      # screen-space: 0 = up
	var names: Array = ["north", "north-east", "east", "south-east", "south", "south-west", "west", "north-west"]
	return names[posmod(int(round(ang / (PI / 4.0))), 8)]

func near_heat(p: Vector2) -> bool:
	if near_fire(p):
		return true
	var px: int = floori(p.x)
	var py: int = floori(p.y)
	for dy in range(-2, 3):
		for dx in range(-2, 3):
			if Defs.o_id(world.obj(px + dx, py + dy)) == Defs.O_STOVE and has_power(px, py):
				return true
	return false

func say(text: String, color: Color = Color(0.9, 0.9, 0.85)) -> void:
	if log.size() > 0 and log[log.size() - 1][0] == text and float(log[log.size() - 1][2]) < 1.5:
		return
	log.append([text, color, 0.0])
	if log.size() > 40:
		log.pop_front()

func emit_fx(kind: String, pos: Vector2, extra: Dictionary = {}) -> void:
	if fx.size() < 64:
		extra["k"] = kind
		extra["p"] = pos
		fx.append(extra)

func noise(pos: Vector2, radius: float, from_zombie: bool = false) -> void:
	if radius <= 0.5:
		return
	# heavy rain drowns out sounds made outdoors
	if world.bld(floori(pos.x), floori(pos.y)) == 0 and World.level(pos.y) == 0:
		radius *= 1.0 - float(weather.get("rain", 0.0)) * 0.25
	noises.append([pos, radius, 0.7, from_zombie])

func wake(reason: String = "") -> void:
	if player.sleeping:
		player.sleeping = false
		time_scale = 1.0
		if reason != "":
			say(reason, Color(1.0, 0.8, 0.6))
		ui_events.append({"type": "wake"})

func on_player_death() -> void:
	dead = true
	time_scale = 1.0
	speed = 1
	ui_events.append({"type": "death"})

## permadeath, persistent world: a new survivor wakes somewhere in the same world.
## The previous one stays where they fell — as a corpse, or walking if the fever had them.
func new_survivor(occupation: String, trait_list: Array = [], start_kind: String = "house", look: Array = []) -> void:
	var old: Player = player
	var c: Chunk = world.chunk_at(floori(old.pos.x), floori(old.pos.y))
	var gear_left: Array = old.inv.duplicate(true)
	if c != null:
		if old.infection >= 0.0 or String(old.death_cause).contains("infected"):
			var z: Zombie = zombies.spawn(old.pos, 0)
			z.look = old.look.duplicate()
			z.loot = gear_left
			z.hp = 130.0
		else:
			c.corpses.append({"x": old.pos.x, "y": old.pos.y, "d": old.dir8, "l": old.look.duplicate(), "h": hour, "perm": 1, "loot": gear_left})
			c.touched = true
			world.notify(floori(old.pos.x), floori(old.pos.y))
	lives += 1
	world.explored = {}        # what the dead knew of the map dies with them
	objectives = []
	player = Player.new(self)
	dead = false
	var st: Dictionary = world.gen.find_start(start_kind, lives)
	player.pos = st["pos"]
	world.stream(player.pos, 2, 999)
	if not can_escape(player.pos):
		player.pos = outside_spot(player.pos)
	player.look = look if look.size() == 4 else [rng.randi() % 4, rng.randi() % 10, rng.randi() % 6, rng.randi() % 6]
	player.setup_occupation(occupation, trait_list)
	world.loot_mult = float(settings["loot"]) * player.tmod("loot")
	world.stream(player.pos, 2, 999)
	safe_pos = player.pos
	safe_radius = 0.0
	guide_i = -1
	_guide_inv = player.inv.size()
	_process_world_events()
	# nothing that was near the old body should be standing over the new one
	for zz in zombies.list.duplicate():
		if zz.pos.distance_to(player.pos) < 8.0 and zz.loot.is_empty():
			zombies.list.erase(zz)
	say("Day %d. Someone else is still alive." % day(), Color(0.9, 0.85, 0.7))

# ------------------------------------------------------------------ notes, documents, markers
const NOTE_LORE := ["\"They said the east road was open. It was not.\"", "\"If the taps still run when you read this, fill everything you own.\"",
	"\"We boarded the windows the first night. By the fourth we wished we had left a way out.\"", "\"Do not trust the quiet houses. Quiet means the door held.\"",
	"\"M. — gone to find your mother. Wait three days, then go north without me.\""]

func add_marker(x: int, y: int, label: String, seen: bool = false) -> void:
	for m in player.markers:
		if int(m[0]) == x and int(m[1]) == y:
			return
	if Vector2(x, y).distance_to(player.pos) < 10.0:
		seen = true
	player.markers.append([x, y, label, seen])

## rumoured places become known once you have been there
func _update_markers() -> void:
	for m in player.markers:
		if (m.size() < 4 or not m[3]) and Vector2(float(m[0]), float(m[1])).distance_to(player.pos) < 10.0:
			if m.size() < 4: m.append(true)
			else: m[3] = true

func journal_add(text: String) -> void:
	player.journal.append([hour, text])
	if player.journal.size() > 80:
		player.journal.pop_front()

## what kind of place is this, in words (for notes and markers)
func place_name(pos: Vector2) -> String:
	if vehicle != null: return "a car"
	var bt: String = world.btype_at(floori(pos.x), floori(pos.y))
	if bt != "": return "a " + bt.replace("_", " ")
	for dy in range(-3, 4):
		for dx in range(-3, 4):
			var id: int = Defs.o_id(world.obj(floori(pos.x) + dx, floori(pos.y) + dy))
			if Vehicle.is_vehicle(id): return "a " + String(Vehicle.TYPES[id]["n"])
			if id == Defs.O_WELL: return "a well"
			if id == Defs.O_GENERATOR: return "a generator"
	return "open ground"

## put what you know on paper: the note is a physical thing anyone can find later
func write_note() -> bool:
	var pencil: Dictionary = Inv.find(player.inv, "pencil")
	var paper: Dictionary = Inv.find(player.inv, "notebook")
	if pencil.is_empty() or paper.is_empty():
		say("You need a pencil and a notebook", Color(0.9, 0.8, 0.6))
		return false
	Inv.use_charge(player.inv, paper)
	var note: Dictionary = Items.make("note", 1, hour)
	note["mx"] = floori(player.pos.x)
	note["my"] = floori(player.pos.y)
	note["txt"] = "Day %d. I was at %s here. Worth coming back to." % [day(), place_name(player.pos)]
	note["lab"] = "%s (note, day %d)" % [place_name(player.pos).capitalize(), day()]
	player.inv.append(note)
	say("You write it down and mark the place.", Color(0.8, 0.9, 0.75))
	return true

## a note found in the world gets its contents the first time anyone reads it
func _fill_found_note(note: Dictionary) -> void:
	var px: int = floori(player.pos.x)
	var py: int = floori(player.pos.y)
	var hv: int = Rng.h2(px, py, seed_v + 977 + int(hour))
	note["txt"] = NOTE_LORE[hv % NOTE_LORE.size()]
	if (hv >> 6) % 100 < 70:
		var best: Array = []
		var rx0: int = WorldGen.fdiv(px, WorldGen.REGION)
		var ry0: int = WorldGen.fdiv(py, WorldGen.REGION)
		var cands: Array = []
		for lot in world.gen.region(rx0, ry0)["lots"]:
			var r: Rect2i = lot["r"]
			var c: Vector2i = r.get_center()
			var d: float = Vector2(c - Vector2i(px, py)).length()
			if d < 30.0 or d > 260.0:
				continue
			var k: String = lot["k"]
			if k != "house" and k != "park" and k != "woods":
				cands.append([c, "the " + k.replace("_", " ")])
			elif k == "house" and cands.size() < 40 and (Rng.h2(c.x, c.y, 5) % 5) == 0:
				var plan: LotBuilder.LotPlan = world.gen.lot_plan(lot)
				if plan.btype == "stash": cands.append([c, "a boarded-up house with supplies"])
				elif plan.hatch.x >= 0: cands.append([c, "a house with a cellar"])
		if not cands.is_empty():
			best = cands[(hv >> 14) % cands.size()]
			var c2: Vector2i = best[0]
			note["mx"] = c2.x
			note["my"] = c2.y
			note["lab"] = String(best[1]).capitalize() + " (from a note)"
			note["txt"] = String(note["txt"]) + " Below it, a sketch: %s, %s of here." % [best[1], Sim.compass(player.pos, Vector2(c2))]

const DIARY := ["Day 3. The neighbours stopped answering. Their dog has not stopped barking.", "Day 6. We moved the food down to the cellar. M. says the sound carries less there.",
	"Day 9. Someone took the car. I hope they made it.", "Day 12. Last entry, I think. If you read this, the key is under the blue pot."]

func _fill_document(doc: Dictionary) -> void:
	var px: int = floori(player.pos.x)
	var py: int = floori(player.pos.y)
	var hv: int = Rng.h2(px, py, seed_v + 1301 + int(hour))
	match String(doc["id"]):
		"diary":
			doc["txt"] = "Someone's diary. " + DIARY[hv % DIARY.size()] + " " + DIARY[(hv >> 5) % DIARY.size()]
			if (hv >> 9) % 100 < 50:
				_fill_found_note(doc)                  # some diaries name a place, and it may be out of date
				if doc.has("mx"):
					doc["txt"] = "Someone's diary. %s They wrote of %s, %s of here." % [DIARY[hv % DIARY.size()], String(doc.get("lab", "a place")).replace(" (from a note)", "").to_lower(), compass(player.pos, Vector2(float(doc["mx"]), float(doc["my"])))]
					doc["lab"] = String(doc.get("lab", "A place")).replace("(from a note)", "(from a diary)")
				else:
					doc["txt"] = "Someone's diary. " + DIARY[hv % DIARY.size()] + " " + DIARY[(hv >> 5) % DIARY.size()]
		"bulletin":
			# printed in the first days: the place it promises may since have been emptied, or overrun
			var a: float = float(hv % 360) * PI / 180.0
			var site := Vector2i(px + int(cos(a) * float(60 + (hv >> 8) % 90)), py + int(sin(a) * float(60 + (hv >> 8) % 90)))
			var kind: String = ["supply drop", "evacuation point", "aid station"][(hv >> 3) % 3]
			doc["txt"] = "EMERGENCY BULLETIN — residents should report to the %s %s of here. Bring identification and water." % [kind, compass(player.pos, Vector2(site))]
			doc["mx"] = site.x
			doc["my"] = site.y
			doc["lab"] = kind.capitalize() + " (bulletin)"
			if not pending_sites.has(site):
				pending_sites[site] = "supply" if (hv >> 12) % 100 < 45 else "overrun"
		"local_map":
			# marks the streets around a town centre as known
			var cx: int = px >> 4
			var cy: int = py >> 4
			var known := 0
			for dy in range(-6, 7):
				for dx in range(-6, 7):
					var k := Vector2i(cx + dx, cy + dy)
					if not world.explored.has(k):
						var ch: Chunk = world.gen.gen_chunk(k.x, k.y) if absi(dx) > 2 or absi(dy) > 2 or world.chunk(k.x, k.y) == null else world.chunk(k.x, k.y)
						world.explored[k] = ch.map_px if ch.map_px.size() == Iso.CS2 else WorldGen._minimap(ch)
						known += 1
			doc["txt"] = "A road map of the surrounding streets, folded soft. (%d blocks added to your map.)" % known

## a compass: where home and the places you have marked are, from here
func take_bearing() -> void:
	var lines: Array = []
	if not home.is_empty():
		lines.append("home %s, %d paces" % [compass(player.pos, home_pos()), int(home_pos().distance_to(player.pos))])
	for ob in objectives:
		if ob["state"] == "open":
			var at := Vector2(float(ob["x"]), float(ob["y"]))
			lines.append("%s %s, %d paces" % [String(ob["kind"]).replace("distress", "the distress call"), compass(player.pos, at), int(at.distance_to(player.pos))])
	var near: Array = []
	for mk in player.markers:
		near.append([Vector2(float(mk[0]), float(mk[1])).distance_to(player.pos), mk])
	near.sort_custom(func(a, b): return a[0] < b[0])
	for i in range(mini(3, near.size())):
		var mk2: Array = near[i][1]
		lines.append("%s %s, %d paces" % [mk2[2], compass(player.pos, Vector2(float(mk2[0]), float(mk2[1]))), int(near[i][0])])
	if lines.is_empty():
		say("The needle points north. You have nowhere marked to go.", Color(0.85, 0.85, 0.75))
	else:
		say("Bearing: " + "; ".join(lines) + ".", Color(0.85, 0.85, 0.75))
	player.add_xp("tracking", 2.0)

## a road atlas: the whole district, roughly, without walking it
func read_atlas(it: Dictionary) -> int:
	var cx: int = floori(player.pos.x) >> 4
	var cy: int = floori(player.pos.y) >> 4
	var known := 0
	for dy in range(-12, 13):
		for dx in range(-12, 13):
			var k := Vector2i(cx + dx, cy + dy)
			if not world.explored.has(k) and (dx * dx + dy * dy) <= 144:
				var ch: Chunk = world.chunk(k.x, k.y)
				if ch == null: ch = world.gen.gen_chunk(k.x, k.y)
				world.explored[k] = ch.map_px if ch.map_px.size() == Iso.CS2 else WorldGen._minimap(ch)
				known += 1
	it["read"] = 1
	say("You trace the roads with a finger. (%d blocks added to your map.)" % known, Color(0.86, 0.84, 0.72))
	journal_add("Studied a road atlas of the district.")
	return known

## a bulletin's promise comes true or does not, the first time anyone gets there
func _resolve_sites(c: Chunk) -> void:
	if pending_sites.is_empty():
		return
	for k in pending_sites.keys():
		if (k.x >> 4) != c.cx or (k.y >> 4) != c.cy:
			continue
		var what: String = pending_sites[k]
		pending_sites.erase(k)
		if what == "supply":
			var placed := 0
			for d in [Vector2i(0, 0), Vector2i(2, 0), Vector2i(0, 2), Vector2i(2, 2), Vector2i(-2, 0)]:
				var t: Vector2i = k + d
				if world.obj(t.x, t.y) == 0 and not world.tile_blocked(t.x, t.y) and placed < 3:
					world.set_obj(t.x, t.y, Defs.ocell(Defs.O_CRATE, 0, 0))
					var arr: Array = Loot.roll("stash", "", rng, hour, 1.0)
					world.chunk_at(t.x, t.y).containers[World.idx(t.x, t.y)] = arr
					placed += 1
		else:
			var made := 0
			for n in range(60):
				if made >= 10:
					break
				var zp := Vector2(k.x + rng.randf_range(-5.0, 5.0), k.y + rng.randf_range(-5.0, 5.0))
				if not world.blocked(zp.x, zp.y, 0.3):
					zombies.spawn(zp)
					made += 1

func read_note(note: Dictionary) -> void:
	if not note.has("txt") and note["id"] != "note" and note["id"] != "survivor_note":
		_fill_document(note)
	if not note.has("txt"):
		_fill_found_note(note)
	say(String(note["txt"]), Color(0.86, 0.84, 0.72))
	journal_add(String(note["txt"]))
	if note.has("mx"):
		add_marker(int(note["mx"]), int(note["my"]), String(note.get("lab", "Marked on a note")))
		say("Marked on your map.", Color(0.75, 0.9, 0.7))
	player.bored = maxf(0.0, player.bored - 10.0)
	flags["read_note"] = true

# ------------------------------------------------------------------ fish stocks
var unjammed: Dictionary = {}     # doors forced or found free: "x,y,side" -> true
var pending_sites: Dictionary = {}  # Vector2i -> "supply" | "overrun": what a bulletin promised, decided when it was printed
var objectives: Array = []        # {"text", "x", "y", "state", "due", "kind"}
var home: Dictionary = {}         # your shelter: {"x", "y", "b"}
var _trader_h := 60.0
var _event_h := 30.0               # game hours until the world throws something at you
const EVENTS := ["distress", "fleeing", "patrol", "horde", "wildfire", "crash"]
var snow_cover := 0.0            # 0 bare .. 1 deep: settles while it snows, melts above freezing
var flooded: Dictionary = {}       # Vector2i tile -> ground it had before the water came up
var _wet_h := 0.0                  # hours of heavy rain in a row
var lightning := 0.0               # seconds of flash left (renderer)
var fish: Dictionary = {}          # chunk key -> [stock 0..1, hour last updated]

## how many fish are left in this stretch of water (1 = untouched), recovering about 3% a day
func fish_stock(x: int, y: int) -> float:
	var k := Vector2i(x >> 4, y >> 4)
	if not fish.has(k):
		return 1.0
	var e: Array = fish[k]
	return minf(1.0, float(e[0]) + (hour - float(e[1])) / 24.0 * 0.03)

func take_fish(x: int, y: int) -> void:
	var k := Vector2i(x >> 4, y >> 4)
	fish[k] = [maxf(0.05, fish_stock(x, y) - 0.12), hour]

## make the building (or spot) you are in your shelter: recruits live and store food here
func set_home(pos: Vector2) -> void:
	home = {"x": floori(pos.x), "y": floori(pos.y), "b": world.bld(floori(pos.x), floori(pos.y))}
	add_marker(floori(pos.x), floori(pos.y), "Your shelter")

func home_pos() -> Vector2:
	return Vector2(float(home["x"]) + 0.5, float(home["y"]) + 0.5) if not home.is_empty() else Vector2.ZERO

## every storage container in your shelter: [x, y, Array]
func home_stores() -> Array:
	var out: Array = []
	if home.is_empty():
		return out
	var hx: int = home["x"]
	var hy: int = home["y"]
	var hb: int = home["b"]
	for y in range(hy - 12, hy + 13):
		for x in range(hx - 12, hx + 13):
			if not world.is_loaded(x, y):
				continue
			var cell: int = world.obj(x, y)
			if cell == 0 or Defs.o_part(cell) != 0:
				continue
			var d: Dictionary = Defs.obj(Defs.o_id(cell))
			if not d.has("c") or Vehicle.is_vehicle(Defs.o_id(cell)) or d.get("use", "") == "bed" or Defs.o_id(cell) == Defs.O_TRASH_CAN or Defs.o_id(cell) == Defs.O_MAILBOX:
				continue                          # proper storage only: not under the bed, not the bin
			if hb != 0 and world.bld(x, y) != hb:
				continue
			out.append([x, y, world.container_at(x, y)])
	return out

## a few interior doors are swollen in their frames: stuck until forced
func door_jammed(x: int, y: int, side: int) -> bool:
	var key: String = "%d,%d,%d" % [x, y, side]
	if unjammed.has(key) or world.bld(x, y) == 0:
		return false
	return Rng.h2(x * 2 + side, y, seed_v + 4401) % 100 < 6

func near_roof(pos: Vector2) -> bool:
	for d in [Vector2i(1, 0), Vector2i(-1, 0), Vector2i(0, 1), Vector2i(0, -1)]:
		if world.bld(floori(pos.x) + d.x, floori(pos.y) + d.y) != 0:
			return true
	return false

## smoke fills a room with a fire in it: you cough, it hurts, and it gets in your eyes
var _smoke_t := 0.0
func _tick_smoke(dt: float) -> void:
	if burning.is_empty() or not player.alive or vehicle != null:
		return
	_smoke_t -= dt
	if _smoke_t > 0.0:
		return
	_smoke_t = 1.0
	var b: int = world.bld(floori(player.pos.x), floori(player.pos.y))
	var thick := 0
	for k in burning.keys():
		var d: float = Vector2(k.x + 0.5, k.y + 0.5).distance_to(player.pos)
		if (b != 0 and world.bld(k.x, k.y) == b and d < 9.0) or d < 2.5:
			thick += 1
	if thick > 0 and b != 0 and _room_vented(b):
		thick = int(ceil(float(thick) * 0.4))          # an open window or door lets the worst of it out
	if thick > 0:
		if not settings.get("god", false):
			player.hurt(minf(4.0, 0.6 * float(thick)), "Choked on smoke")
		player.endurance = maxf(0.0, player.endurance - 3.0)
		noise(player.pos, 5.0)                 # coughing
		if rng.randf() < 0.3:
			say("Smoke fills your lungs. Get out!", Color(1.0, 0.7, 0.5))

## is there an open (or broken) door or window in this building near you?
func _room_vented(b: int) -> bool:
	var px: int = floori(player.pos.x)
	var py: int = floori(player.pos.y)
	for y in range(py - 6, py + 7):
		for x in range(px - 6, px + 7):
			for side in range(2):
				var wid: int = world.wall(x, y, side)
				if wid == 0 or (wid & 3) == Defs.WS_SOLID:
					continue
				if world.bld(x, y) != b and world.bld(x - (1 if side == 1 else 0), y - (1 if side == 0 else 0)) != b:
					continue
				if (world.edge_state(x, y, side) & (Defs.ES_OPEN | Defs.ES_BROKEN)) != 0 or (wid & 3) == Defs.WS_ARCH:
					return true
	return false

# ------------------------------------------------------------------ the event director
## every so often the world does something near you that you did not cause
func _director(dh: float) -> void:
	if not settings.get("meta", true) or float(settings.get("events", 1.0)) <= 0.0 or underground() or not player.alive:
		return
	_event_h -= dh * float(settings.get("events", 1.0))
	if _event_h > 0.0:
		return
	_event_h = rng.randf_range(10.0, 26.0)
	var order: Array = EVENTS.duplicate()
	for i in range(order.size()):
		var j: int = rng.randi() % order.size()
		var tmp = order[i]
		order[i] = order[j]
		order[j] = tmp
	for k in order:
		if world_event(String(k)):
			return

## an open outdoor tile at a distance from here, in a loaded chunk if asked
func _open_spot(center: Vector2, rmin: float, rmax: float, loaded: bool) -> Vector2:
	for attempt in range(40):
		var a: float = rng.randf() * TAU
		var q: Vector2 = center + Vector2(cos(a), sin(a)) * rng.randf_range(rmin, rmax)
		var qx: int = floori(q.x)
		var qy: int = floori(q.y)
		if loaded and not world.is_loaded(qx, qy):
			continue
		if World.level(q.y) != World.level(center.y):
			continue
		if loaded and (world.tile_blocked(qx, qy) or world.bld(qx, qy) != 0 or Defs.ground_is_water(world.ground(qx, qy))):
			continue
		return Vector2(qx + 0.5, qy + 0.5)
	return Vector2.INF

## run one event now; false if it could not happen here
func world_event(kind: String) -> bool:
	var p: Vector2 = player.pos
	match kind:
		"distress":
			for o in objectives:
				if o["kind"] == "distress" and o["state"] == "open": return false
			var spot: Vector2 = _open_spot(p, 55.0, 95.0, false)
			if spot == Vector2.INF: return false
			var ob: Dictionary = {"kind": "distress", "x": floori(spot.x), "y": floori(spot.y), "state": "open", "due": hour + 30.0, "spawned": false, "npc": -1,
				"text": "Answer the distress call %s of here" % compass(p, spot)}
			objectives.append(ob)
			add_marker(ob["x"], ob["y"], "Distress call")
			if not Inv.find_tag(player.inv, "radio").is_empty() or Inv.count(player.inv, "radio") > 0:
				say("The radio crackles: \"…anyone… we're pinned down, %s of the… please…\"" % compass(p, spot), Color(1.0, 0.85, 0.5))
			else:
				say("A red flare climbs into the sky to the %s. Someone wants to be found." % compass(p, spot), Color(1.0, 0.6, 0.45))
			journal_add("A call for help, %s of where I stood. Marked on the map." % compass(p, spot))
			return true
		"fleeing":
			var s: Vector2 = _open_spot(p, 16.0, 22.0, true)
			if s == Vector2.INF: return false
			var n = npcs.spawn(s, false)
			n.task = "flee"
			n.task_t = 14.0
			n.task_pos = p
			n.trust = 45.0
			var back: Vector2 = (s - p).normalized()
			for i in range(rng.randi_range(3, 5)):
				var zq: Vector2 = s + back * rng.randf_range(4.0, 7.0) + Vector2(rng.randf_range(-2, 2), rng.randf_range(-2, 2))
				if world.is_loaded(floori(zq.x), floori(zq.y)) and not world.tile_blocked(floori(zq.x), floori(zq.y)):
					var z: Zombie = zombies.spawn(zq)
					z.state = Zombie.INVESTIGATE
					z.goal = p
					z.has_goal = true
					z.give_up = 40.0
			noise(s, 26.0)
			say("Running footsteps and a voice: \"Help! They're right behind me!\" — to the %s." % compass(p, s), Color(1.0, 0.75, 0.5))
			return true
		"patrol":
			var cands: Array = []
			for key in factions.sites.keys():
				var st: Dictionary = factions.sites[key]
				if not st["fallen"] and Vector2(key).distance_to(Vector2(p) / float(WorldGen.REGION)) < 3.0:
					cands.append([int(st["f"]), key])
			if cands.is_empty(): return false
			var pick: Array = cands[rng.randi() % cands.size()]
			var f: int = int(pick[0])
			var from: Vector2 = _open_spot(p, 20.0, 26.0, true)
			if from == Vector2.INF: return false
			var to: Vector2 = p + (p - from).normalized() * 24.0
			var hostile: bool = Factions.kind(f) == Factions.RAIDER or factions.rep_of(f) < -50.0
			for i in range(rng.randi_range(2, 3)):
				var m = npcs.spawn(from + Vector2(rng.randf_range(-1, 1), rng.randf_range(-1, 1)), false)
				m.fac = f
				m.site = pick[1]
				m.task = "travel"
				m.task_pos = to + Vector2(rng.randf_range(-1.5, 1.5), rng.randf_range(-1.5, 1.5))
				m.task_t = 240.0
				m.wpn = "baseball_bat" if rng.randf() < 0.5 else ""
				m.home = m.task_pos
				if hostile: m.state = NpcSim.HOSTILE
			say("Voices and boots, %s of you: a %s patrol." % [compass(p, from), Factions.fname(f)], Color(0.9, 0.85, 0.65))
			return true
		"horde":
			var c: Vector2 = _open_spot(p, 30.0, 38.0, true)
			if c == Vector2.INF: return false
			var dest: Vector2 = p + (p - c).normalized() * 40.0
			var n2: int = int(rng.randi_range(12, 22) * float(settings.get("zombies", 1.0)))
			var made := 0
			for i in range(n2 * 2):
				if made >= n2 or zombies.list.size() >= ZombieSim.MAX_ACTIVE: break
				var q: Vector2 = c + Vector2(rng.randf_range(-4, 4), rng.randf_range(-4, 4))
				if not world.is_loaded(floori(q.x), floori(q.y)) or world.tile_blocked(floori(q.x), floori(q.y)): continue
				var z2: Zombie = zombies.spawn(q)
				z2.state = Zombie.INVESTIGATE
				z2.goal = dest + Vector2(rng.randf_range(-5, 5), rng.randf_range(-5, 5))
				z2.has_goal = true
				z2.give_up = 400.0
				made += 1
			if made < 6: return false
			say("A long, low moan rolls in from the %s. Many of them, moving together." % compass(p, c), Color(1.0, 0.55, 0.45))
			return true
		"wildfire":
			if float(weather["rain"]) > 0.1 or float(weather["temp"]) < 12.0 or snow_cover > 0.2: return false
			for attempt in range(30):
				var fs: Vector2 = _open_spot(p, 24.0, 40.0, true)
				if fs == Vector2.INF: return false
				if flammability(floori(fs.x), floori(fs.y)) > 0.25 or Defs.o_id(world.obj(floori(fs.x), floori(fs.y))) != 0:
					ignite(floori(fs.x), floori(fs.y), 3.0)
					if burning.has(Vector2i(floori(fs.x), floori(fs.y))):
						say("Smoke rises to the %s. Something out there has caught fire." % compass(p, fs), Color(1.0, 0.65, 0.4))
						return true
			return false
		"crash":
			var cs: Vector2 = _open_spot(p, 20.0, 34.0, true)
			if cs == Vector2.INF: return false
			var cx: int = floori(cs.x)
			var cy: int = floori(cs.y)
			var cc: Chunk = world.chunk_at(cx, cy)
			var gear: Array = []
			for gid in ["water_bottle", "bandage", "canned_beans", "car_keys" if Items.DB.has("car_keys") else "battery"]:
				if rng.randf() < 0.7: gear.append(Items.make(gid, 1, hour))
			cc.corpses.append({"x": cs.x, "y": cs.y, "d": rng.randi() % 8, "l": [rng.randi() % 4, rng.randi() % 10, rng.randi() % 6, rng.randi() % 6], "h": hour, "perm": 1, "loot": gear})
			cc.touched = true
			world.notify(cx, cy)
			if flammability(cx + 1, cy) > 0.1: ignite(cx + 1, cy, 2.0)
			noise(cs, 50.0)
			emit_fx("meta_crash", cs)
			add_marker(cx, cy, "Crash")
			say("Tyres scream, then a crash of metal to the %s. Every one of them heard that." % compass(p, cs), Color(1.0, 0.7, 0.45))
			return true
	return false

## the things you were asked to do, and whether you did them
func _check_objectives() -> void:
	for ob in objectives:
		if ob["state"] != "open": continue
		var at := Vector2(float(ob["x"]) + 0.5, float(ob["y"]) + 0.5)
		match String(ob["kind"]):
			"distress":
				if not ob["spawned"]:
					if hour > float(ob["due"]):
						ob["state"] = "failed"
						say("The calls for help have stopped.", Color(0.8, 0.75, 0.7))
						journal_add("No more calls from the %s. Too late." % compass(player.pos, at))
					elif at.distance_to(player.pos) < 40.0 and world.is_loaded(ob["x"], ob["y"]):
						var spot: Vector2 = _open_spot(at, 0.0, 4.0, true)
						if spot == Vector2.INF: spot = outside_spot(at)
						var n = npcs.spawn(spot, false)
						n.trust = 40.0
						n.temper = "brave"
						ob["npc"] = n.id
						ob["spawned"] = true
						for i in range(rng.randi_range(4, 7)):
							var zq: Vector2 = _open_spot(spot, 3.0, 6.0, true)
							if zq == Vector2.INF: continue
							var z: Zombie = zombies.spawn(zq)
							z.state = Zombie.INVESTIGATE
							z.goal = spot
							z.has_goal = true
							z.give_up = 120.0
						noise(spot, 18.0)
					continue
				var nn = null
				for n2 in npcs.list:
					if n2.id == int(ob["npc"]): nn = n2
				if nn == null:
					if at.distance_to(player.pos) < 30.0:
						ob["state"] = "failed"
						say("You were too late for whoever called.", Color(0.85, 0.7, 0.65))
					continue
				if nn.pos.distance_to(player.pos) < 6.0 and zombies.in_radius(nn.pos, 9.0).is_empty():
					ob["state"] = "done"
					nn.trust = minf(100.0, nn.trust + 35.0)
					nn.met = true
					var gift: String = ["ammo_9mm", "painkillers", "canned_beans", "bandage", "battery"][rng.randi() % 5]
					Inv.add_new(player.inv, gift, 2, hour)
					say("%s: \"You came. I didn't think anyone would.\" They press %s into your hands." % [nn.name, Items.def(gift)["n"]], Color(0.7, 0.95, 0.7))
					journal_add("Answered a call for help. %s owes me." % nn.name)

## spike traps tear up whatever walks over them, and wear out doing it
func _tick_spikes(dt: float) -> void:
	if spikes.is_empty():
		return
	_spike_t -= dt
	if _spike_t > 0.0:
		return
	_spike_t = 0.4
	for sp in spikes.duplicate():
		if Defs.o_id(world.obj(sp.x, sp.y)) != Defs.O_SPIKES:
			spikes.erase(sp)
			continue
		var used := false
		for z in zombies.list.duplicate():
			if floori(z.pos.x) == sp.x and floori(z.pos.y) == sp.y and z.state != Zombie.DOWN:
				zombies.damage(z, 16.0, z.pos, 0.0, randf() < 0.25, false)
				used = true
		if player.alive and vehicle == null and floori(player.pos.x) == sp.x and floori(player.pos.y) == sp.y and not player.sneaking and not settings.get("god", false):
			player.hurt(3.0, "Bled out on your own spikes")
			if randf() < 0.3:
				player.add_wound(15 + randi() % 2, "laceration", "a spike trap")
				say("You step on your own spikes. Sneak across them.", Color(1.0, 0.7, 0.5))
		if used:
			var c: Chunk = world.chunk_at(sp.x, sp.y)
			var i: int = World.idx(sp.x, sp.y)
			var hp: float = float(c.obj_hp.get(i, 60.0)) - 4.0
			c.obj_hp[i] = hp
			c.touched = true
			if hp <= 0.0:
				world.remove_object(sp.x, sp.y)
				spikes.erase(sp)
				emit_fx("break", Vector2(sp.x + 0.5, sp.y + 0.5))

## is anything hunting the survivor right now? (fast-forward drops back to normal speed)
func threatened() -> bool:
	if not burning.is_empty() and player.alive:
		for k in burning.keys():
			if Vector2(k.x + 0.5, k.y + 0.5).distance_squared_to(player.pos) < 25.0:
				return true
	for z in zombies.list:
		if (z.state == Zombie.CHASE or z.state == Zombie.ATTACK or z.state == Zombie.THUMP) and z.pos.distance_squared_to(player.pos) < 196.0:
			return true
	for n in npcs.list:
		if n.state == NpcSim.HOSTILE and n.pos.distance_squared_to(player.pos) < 144.0:
			return true
	return false

# ------------------------------------------------------------------ main tick
func tick(dt: float, move_screen: Vector2 = Vector2.ZERO, want_run: bool = false) -> void:
	var dh: float = dt * time_scale * 24.0 / (float(settings["day_min"]) * 60.0)
	hour += dh
	world.hour = hour
	for l in log:
		l[2] = float(l[2]) + dt
	var i: int = noises.size() - 1
	while i >= 0:
		noises[i][2] = float(noises[i][2]) - dt
		if float(noises[i][2]) <= 0.0:
			noises.remove_at(i)
		i -= 1
	if vehicle != null and player.alive:
		vehicle.update(dt, move_screen, brake)
		player.pos = vehicle.pos
		player.facing = Vehicle.DIRS[vehicle.heading]
		player.dir8 = Iso.dir8(player.facing)
		player.update(dt, Vector2.ZERO, false)
	else:
		player.update(dt, move_screen, want_run)
	player.tick_needs(dh)
	_tick_fire(dt)
	_tick_spikes(dt)
	lightning = maxf(0.0, lightning - dt)
	_tick_smoke(dt)
	zombies.update(dt)
	npcs.update(dt, dh)
	animals.update(dt)
	if world.stream(player.pos, 3, 1) == 0:
		world.gen.prewarm_step(player.pos + player.facing * 30.0)
	_process_world_events()
	_weather_h += dh
	if _weather_h >= 0.25:
		_update_weather(_weather_h)
		_weather_h = 0.0
	_ent_h += dh
	_slow_t -= dt
	if _slow_t <= 0.0:
		_slow_t = 1.0
		_slow_tick(_ent_h)
		_ent_h = 0.0
	if player.sleeping:
		_sleep_check()
	_tick_events(dt)
	# alarms keep screaming
	var ai: int = alarms.size() - 1
	while ai >= 0:
		alarms[ai][1] = float(alarms[ai][1]) - dt
		noise(alarms[ai][0], 42.0)
		if float(alarms[ai][1]) <= 0.0:
			alarms.remove_at(ai)
		ai -= 1

# ------------------------------------------------------------------ world events
func _tick_events(dt: float) -> void:
	# ---- the flyover: a low aircraft circles and every infected for a mile follows the noise
	if not fly_active and hour >= fly_next_h:
		fly_active = true
		fly_end_h = hour + rng.randf_range(1.2, 2.2)
		fly_track = player.pos
		_fly_lost = 0.0
		say("Rotor blades. An aircraft is sweeping low over the area.", Color(1.0, 0.75, 0.5))
		ui_events.append({"type": "flyover"})
	if fly_active:
		_fly_t -= dt
		_fly_pack_t -= dt
		if _fly_t <= 0.0:
			_fly_t = 1.2
			var hidden: bool = underground() or world.bld(floori(player.pos.x), floori(player.pos.y)) != 0
			if not hidden:
				fly_track = player.pos
				_fly_lost = 0.0
			else:
				_fly_lost += 1.2
				if _fly_lost > 25.0:
					fly_track += Vector2(rng.randf_range(-5.0, 5.0), rng.randf_range(-5.0, 5.0))
			if not underground():
				noise(fly_track, 55.0)
				emit_fx("rotor", fly_track)
		if _fly_pack_t <= 0.0 and not underground():
			_fly_pack_t = rng.randf_range(22.0, 34.0)
			zombies.spawn_wanderers()
		if hour >= fly_end_h:
			fly_active = false
			say("The aircraft drones away. The dead it stirred up remain.", Color(1.0, 0.75, 0.5))
			if int(settings["flyover"]) >= 2:
				fly_next_h = hour + rng.randf_range(5.0, 9.0) * 24.0
			else:
				fly_next_h = 1e12
	# ---- distant events: the world beyond the screen is not quiet
	if settings.get("meta", true) and not underground():
		_meta_t -= dt
		if _meta_t <= 0.0:
			_meta_t = rng.randf_range(150.0, 330.0)
			var a: float = rng.randf() * TAU
			var mp: Vector2 = player.pos + Vector2(cos(a), sin(a)) * rng.randf_range(22.0, 40.0)
			var kinds: Array = [["gunshot", 45.0, "A gunshot cracks to the %s."], ["scream", 34.0, "A scream carries from the %s, then stops."],
				["dog", 24.0, "A dog is barking to the %s."], ["caralarm", 40.0, "A car alarm starts wailing to the %s."], ["crash", 22.0, "Glass shatters somewhere to the %s."]]
			var k: Array = kinds[rng.randi() % kinds.size()]
			noise(mp, k[1])
			if k[0] == "caralarm":
				alarms.append([mp, 14.0])
			emit_fx("meta_" + String(k[0]), mp)
			if not player.sleeping:
				say(String(k[2]) % compass(player.pos, mp), Color(0.8, 0.8, 0.7))
	# ---- tutorial objectives
	if guide_i >= 0 and guide_i < GUIDE.size():
		var done := false
		match GUIDE[guide_i][0]:
			"move": done = player.pos.distance_to(safe_pos) > 2.5
			"door": done = flags.has("door")
			"loot": done = player.inv.size() > _guide_inv or flags.has("took")
			"equip": done = not player.weapon.is_empty()
			"eat": done = flags.has("ate")
			"kill": done = player.kills > 0
			"craft": done = flags.has("crafted")
			"sleep": done = flags.has("slept")
		if done:
			guide_i += 1
			emit_fx("levelup", player.pos)
			if guide_i >= GUIDE.size():
				guide_i = -1
				say("You know the basics now. Stay quiet, stay fed, stay alive.", Color(0.6, 0.9, 0.6))

## what a battery radio picks up: the automated emergency loop
func radio_report() -> void:
	if underground():
		say("Nothing but static down here.", Color(0.8, 0.8, 0.7))
		return
	var col := Color(0.75, 0.85, 0.95)
	var wx: String = "clear skies"
	if float(weather["rain"]) > 0.3: wx = "heavy rain"
	elif float(weather["cloud"]) > 0.65: wx = "overcast, rain likely"
	elif float(weather["fog"]) > 0.2: wx = "fog"
	say("\"…automated emergency broadcast. Conditions: %s, %d degrees.\"" % [wx, int(round(float(weather["temp"])))], col)
	if hour < power_off_h:
		var days: float = (power_off_h - hour) / 24.0
		if days < 3.0:
			say("\"Grid operators report critical staffing. Expect power loss within days.\"", col)
		else:
			say("\"Utilities remain in service. Conserve water and fuel.\"", col)
	else:
		say("\"…this station is running on reserve power…\"", col)
	# tomorrow, read off the same seasonal curve the weather follows
	var tomorrow: float = temperature_base_at(hour + 24.0)
	var fc: String = "a hard frost, snow possible" if tomorrow < 0.0 else ("a cold day" if tomorrow < 8.0 else ("a warm day" if tomorrow > 22.0 else "mild"))
	if float(weather.get("wind", 0.0)) > 0.55 and float(weather["cloud"]) > 0.6: fc += ", with storms building"
	say("\"Tomorrow: %s, around %d degrees.\"" % [fc, int(round(tomorrow))], col)
	if not factions.sites.is_empty() and rng.randf() < 0.5:
		var ks: Array = factions.sites.keys()
		var st: Dictionary = factions.sites[ks[rng.randi() % ks.size()]]
		if not st["fallen"] and Factions.kind(int(st["f"])) != Factions.RAIDER:
			say("\"…this is %s. If you can hear us, we have walls and we have work.\"" % Factions.fname(int(st["f"])), Color(0.8, 0.9, 0.75))
			add_marker(int(st["x"]), int(st["y"]), String(st["name"]) + " (radio)")
	if fly_active:
		say("\"Air units are sweeping your sector now. Stay indoors.\"", Color(1.0, 0.75, 0.5))
	elif fly_next_h - hour < 30.0 and fly_next_h - hour > 0.0:
		say("\"Aerial survey flights are scheduled for this area within the day.\"", Color(1.0, 0.75, 0.5))
	noise(player.pos, 5.0)

func guide_text() -> String:
	if guide_i < 0 or guide_i >= GUIDE.size():
		return ""
	return GUIDE[guide_i][1]

func _process_world_events() -> void:
	if world.ev_loaded.size() > 0:
		for c in world.ev_loaded:
			_catch_up(c)
			animals.on_chunk_loaded(c, not c.spawned)
			_resolve_sites(c)
			npcs.on_chunk_loaded(c)
			zombies.on_chunk_loaded(c)
			view_loaded.append(c)
		world.ev_loaded.clear()
	# without a renderer attached (headless tests) nobody drains these queues
	if view_loaded.size() > 400: view_loaded.clear()
	if world.ev_unloaded.size() > 400: world.ev_unloaded.clear()
	if world.ev_tiles.size() > 2000: world.ev_tiles.clear()
	if world.ev_ground.size() > 2000: world.ev_ground.clear()

func _sleep_check() -> void:
	var p: Player = player
	if p.fatigue <= 1.0:
		wake("You wake up rested.")
		return
	if p.hunger > 92.0 or p.thirst > 92.0:
		wake("Hunger and thirst wake you.")
		return
	for z in zombies.list:
		if z.state >= Zombie.INVESTIGATE and z.pos.distance_squared_to(p.pos) < 64.0:
			wake("Something is close. You jolt awake!")
			return
	if p.hp < 25.0:
		wake("Pain wakes you.")
	elif fly_active and not underground():
		wake("The thunder of rotor blades wakes you.")

# ------------------------------------------------------------------ weather
func temperature_base_at(h: float) -> float:
	var saved: float = hour
	hour = h
	var t: float = temperature_base()
	hour = saved
	return t

func temperature_base() -> float:
	if underground():
		return 12.0
	var doy: float = fposmod(190.0 + float(settings.get("season", 0)) * 91.0 + hour / 24.0, 365.0)
	var seasonal: float = 11.0 + 12.0 * cos((doy - 200.0) / 365.0 * TAU)
	var daily: float = 5.0 * cos((hour_of_day() - 15.0) / 24.0 * TAU)
	return seasonal + daily

func _update_weather(dh: float) -> void:
	var c: float = weather["cloud"]
	c = clampf(c + rng.randf_range(-0.22, 0.22) * dh * 2.0 + (0.5 - c) * 0.02, 0.0, 1.0)
	weather["cloud"] = c
	var rain: float = weather["rain"]
	if c > 0.68:
		rain = clampf(rain + rng.randf_range(-0.3, 0.5) * dh * 2.0, 0.0, 1.0)
	else:
		rain = maxf(0.0, rain - dh * 1.5)
	weather["rain"] = rain
	var h: float = hour_of_day()
	var fog: float = weather["fog"]
	if h > 4.0 and h < 8.0 and c > 0.4:
		fog = clampf(fog + rng.randf_range(-0.1, 0.3) * dh * 2.0, 0.0, 0.8)
	else:
		fog = maxf(0.0, fog - dh * 0.6)
	weather["fog"] = fog
	var wind: float = weather.get("wind", 0.2)
	wind = clampf(wind + rng.randf_range(-0.25, 0.25) * dh * 2.0 + (0.25 + rain * 0.35 - wind) * 0.05, 0.0, 1.0)
	weather["wind"] = wind
	weather["temp"] = temperature_base() - rain * 3.0 - c * 2.0
	# rain below freezing is snow; heavy rain with a gale is a storm
	weather["snow"] = rain if float(weather["temp"]) <= 0.5 else 0.0
	weather["storm"] = rain > 0.75 and wind > 0.6 and float(weather["temp"]) > 3.0
	_weather_hazards(dh)
	if hour >= power_off_h and not _power_said:
		_power_said = true
		say("The lights flicker and die. The power grid is down.", Color(1.0, 0.8, 0.5))
		ui_events.append({"type": "power"})
	if hour >= water_off_h and not _water_said:
		_water_said = true
		say("The taps sputter. The water has stopped.", Color(1.0, 0.8, 0.5))

## what the weather does to the world: settles snow, ices, floods, knocks trees down, strikes
var _dawn_day := -1
func _weather_hazards(dh: float) -> void:
	# a few quiet notes as the sun comes up, once a day, when nothing is close
	var hod_m: float = hour_of_day()
	if hod_m > 5.6 and hod_m < 6.4 and day() != _dawn_day and player.alive and not threatened():
		_dawn_day = day()
		emit_fx("music_dawn", player.pos)
	var t: float = weather["temp"]
	var rain: float = weather["rain"]
	if float(weather.get("snow", 0.0)) > 0.1:
		snow_cover = minf(1.0, snow_cover + dh * float(weather["snow"]) * 0.12)
	elif t > 2.0:
		snow_cover = maxf(0.0, snow_cover - dh * (t - 2.0) * 0.02)
	# floods: a long downpour pushes the water over its banks
	_wet_h = _wet_h + dh if rain > 0.75 else maxf(0.0, _wet_h - dh * 0.5)
	if _wet_h > 6.0 and flooded.size() < 60:
		_flood_step()
	elif _wet_h <= 0.0 and not flooded.is_empty() and rng.randf() < dh * 0.5:
		_recede_step()
	if bool(weather.get("storm", false)) and rng.randf() < dh * 1.4:
		_storm_event()

func _flood_step() -> void:
	var px: int = floori(player.pos.x)
	var py: int = floori(player.pos.y)
	for tries in range(40):
		var x: int = px + rng.randi_range(-40, 40)
		var y: int = py + rng.randi_range(-40, 40)
		if not world.is_loaded(x, y) or World.level(y) != 0 or flooded.has(Vector2i(x, y)):
			continue
		var g: int = world.ground(x, y)
		if Defs.ground_is_water(g) or g == Defs.G_VOID or world.bld(x, y) != 0 or world.obj(x, y) != 0:
			continue
		var wet := false
		for d in [Vector2i(1, 0), Vector2i(-1, 0), Vector2i(0, 1), Vector2i(0, -1)]:
			if Defs.ground_is_water(world.ground(x + d.x, y + d.y)) and not flooded.has(Vector2i(x + d.x, y + d.y)) or flooded.has(Vector2i(x + d.x, y + d.y)):
				wet = true
		if wet:
			flooded[Vector2i(x, y)] = g
			world.set_ground(x, y, Defs.G_WATER)
			if flooded.size() == 1:
				say("The river is over its banks.", Color(0.7, 0.85, 1.0))
			return

func _recede_step() -> void:
	var k: Vector2i = flooded.keys()[rng.randi() % flooded.size()]
	if world.is_loaded(k.x, k.y):
		world.set_ground(k.x, k.y, int(flooded[k]))
	flooded.erase(k)

func _storm_event() -> void:
	lightning = 0.25
	emit_fx("thunder", player.pos)
	var px: int = floori(player.pos.x)
	var py: int = floori(player.pos.y)
	for tries in range(30):
		var x: int = px + rng.randi_range(-30, 30)
		var y: int = py + rng.randi_range(-30, 30)
		var id: int = Defs.o_id(world.obj(x, y))
		if id < Defs.O_TREE_OAK or id > Defs.O_TREE_BIRCH or not world.is_loaded(x, y):
			continue
		if rng.randf() < 0.25:
			ignite(x, y, 1.0)             # struck
			return
		# blown down: it lies across the tile beside it, roads included
		var tree_cell: int = world.obj(x, y)
		world.set_obj(x, y, 0)
		for ax in [x, x - 1]:
			if world.obj(ax, y) == 0 and world.obj(ax + 1, y) == 0 and world.bld(ax, y) == 0 and world.bld(ax + 1, y) == 0 \
					and not world.tile_blocked(ax, y) and not world.tile_blocked(ax + 1, y):
				world.set_obj(ax, y, Defs.ocell(Defs.O_FALLEN_TREE, 0, 0))
				world.set_obj(ax + 1, y, Defs.ocell(Defs.O_FALLEN_TREE, 0, 1))
				noise(Vector2(x + 0.5, y + 0.5), 18.0)
				say("Somewhere close, a tree comes down.", Color(0.8, 0.85, 0.9)) if Vector2(x, y).distance_to(player.pos) < 25.0 else null
				return
		world.set_obj(x, y, tree_cell)
		return

## after a long rain, bare earth turns to mud
func muddy(x: int, y: int) -> bool:
	if world.bld(x, y) != 0 or float(weather["temp"]) <= 0.0:
		return false
	var g: int = world.ground(x, y)
	return (_wet_h > 2.0 or float(weather["rain"]) > 0.6) and (g == Defs.G_DIRT or g == Defs.G_SOIL or g == Defs.G_GRASS or g == Defs.G_GRASS_DARK or g == Defs.G_FOREST)

## underfoot: ice and packed snow outdoors when it is cold
func icy(x: int, y: int) -> bool:
	if world.bld(x, y) != 0 or float(weather["temp"]) > 0.0:
		return false
	var g: int = world.ground(x, y)
	return snow_cover > 0.3 or ((g == Defs.G_ASPHALT or g == Defs.G_SIDEWALK or g == Defs.G_ASPHALT_LX or g == Defs.G_ASPHALT_LY or g == Defs.G_CONCRETE) and _wet_h > 0.0)

# ------------------------------------------------------------------ slow world tick (1 Hz)
func _slow_tick(dh: float) -> void:
	factions.tick(dh)
	_update_markers()
	_director(dh)
	_check_objectives()
	_trader_h -= dh
	if _trader_h <= 0.0:
		_trader_h = rng.randf_range(50.0, 90.0)
		npcs.send_trader()
	generators.clear()
	banks.clear()
	substations.clear()
	fires.clear()
	for bk in burning.keys():
		fires.append(bk)
	lamps.clear()
	spikes.clear()
	var px: int = floori(player.pos.x)
	var py: int = floori(player.pos.y)
	for k in world.chunks.keys():
		var c: Chunk = world.chunks[k]
		c.last_hour = hour
		if not c.ents.is_empty():
			_sim_ents(c, dh, false)
		if not c.corpses.is_empty():
			var ci: int = c.corpses.size() - 1
			while ci >= 0:
				if hour - float(c.corpses[ci]["h"]) > 96.0 and not c.corpses[ci].has("perm"):
					var cp: Dictionary = c.corpses[ci]
					c.corpses.remove_at(ci)
					world.notify(floori(cp["x"]), floori(cp["y"]))
				ci -= 1
		if absi(c.cx - (px >> 4)) <= 1 and absi(c.cy - (py >> 4)) <= 1:
			for i in range(Iso.CS2):
				var o: int = c.obj[i] & 1023
				if o == Defs.O_STREET_LAMP or o == Defs.O_LAMP:
					lamps.append(Vector2i(c.cx * 16 + (i & 15), c.cy * 16 + (i >> 4)))
				elif o == Defs.O_SPIKES:
					spikes.append(Vector2i(c.cx * 16 + (i & 15), c.cy * 16 + (i >> 4)))
	var near := 0
	for cy2 in range((py - 4) >> 4, ((py + 4) >> 4) + 1):
		for cx2 in range((px - 4) >> 4, ((px + 4) >> 4) + 1):
			var cc: Chunk = world.chunk(cx2, cy2)
			if cc != null:
				for cp2 in cc.corpses:
					if absf(float(cp2["x"]) - player.pos.x) < 4.0 and absf(float(cp2["y"]) - player.pos.y) < 4.0 and hour - float(cp2["h"]) > 6.0:
						near += 1
	player.corpses_near = near
	# building entry: alarms
	var b: int = world.bld(px, py)
	if b != 0 and b != _last_bld and not alarms_done.has(b):
		var armed: bool = alarm_armed(px, py)
		alarms_done[b] = true
		if armed:
			alarms.append([player.pos, 28.0])
			say("An alarm starts blaring!", Color(1.0, 0.5, 0.4))
			emit_fx("alarm", player.pos)
	_last_bld = b
	# running generators hum; battery banks hum not at all, but run down
	for g in generators:
		noise(Vector2(g.x + 0.5, g.y + 0.5), 11.0)
	if hour >= power_off_h:
		for bk in banks:
			var covered := false
			for g2 in generators:
				if absi(g2.x - bk.x) <= 4 and absi(g2.y - bk.y) <= 4: covered = true
			if not covered:
				var be: Dictionary = world.ent(bk.x, bk.y)
				be["w"] = maxf(0.0, float(be.get("w", 0.0)) - dh * 0.5 * float(maxi(1, loads_near(bk.x, bk.y, BANK_RANGE))))

func _sim_ents(c: Chunk, dh: float, catch_up: bool) -> void:
	var rain: float = weather["rain"]
	for i in c.ents.keys():
		var e: Dictionary = c.ents[i]
		var x: int = c.cx * 16 + (int(i) & 15)
		var y: int = c.cy * 16 + (int(i) >> 4)
		match e.get("k", ""):
			"substation":
				if hour < float(e.get("until", 0.0)):
					if not catch_up:
						substations.append(Vector2i(x, y))
						noise(Vector2(x + 0.5, y + 0.5), 9.0)       # transformers hum
				elif int(e.get("said", 1)) == 0:
					e["said"] = 1
					if not catch_up: say("Somewhere a transformer bangs, and the streetlights die again.", Color(1.0, 0.8, 0.5))
			"crop":
				var outdoors: bool = c.bld[i] == 0
				if outdoors and rain > 0.05:
					e["w"] = minf(100.0, float(e["w"]) + rain * 40.0 * dh)
				var stage: int = e["s"]
				if stage < 3:
					var crop_t: String = e["t"]
					var warm_enough: bool = float(weather["temp"]) > float(Farming.MIN_T.get(crop_t, 4.0)) or not outdoors
					if outdoors and float(weather["temp"]) < 0.0 and Farming.FROST_KILLS.has(crop_t) and randf() < dh * 0.25:
						e["dry"] = 99.0                    # frost blackens tender plants
					var wet_lim: float = 75.0 if Farming.WET_SENSITIVE.has(crop_t) else 85.0
					if e.get("ill", 0) == 0 and float(e["w"]) > wet_lim and randf() < dh * 0.012:
						e["ill"] = 1          # standing water breeds mildew
						e["ill_h"] = 0.0
					if e.get("ill", 0) == 1:
						e["ill_h"] = float(e.get("ill_h", 0.0)) + dh
						if float(e["ill_h"]) > 60.0:
							e["dry"] = 99.0
					elif float(e["w"]) > 5.0 and warm_enough:
						e["g"] = float(e["g"]) + dh * (1.4 if e.get("f", 0) == 1 else 1.0)
						e["dry"] = 0.0
					elif float(e["w"]) > 5.0:
						pass                  # too cold to grow, but not dying
					else:
						e["dry"] = float(e.get("dry", 0.0)) + dh
					e["w"] = maxf(0.0, float(e["w"]) - dh * 1.6)
					var total: float = Farming.GROW_HOURS[e["t"]]
					var ns: int = clampi(int(float(e["g"]) / total * 3.0), 0, 3)
					if float(e.get("dry", 0.0)) > 40.0:
						ns = 4
					if ns != stage:
						e["s"] = ns
						c.obj[i] = Defs.ocell(Defs.o_id(c.obj[i]), 0, ns)
						c.modified = true
						world.notify(x, y)
			"fire":
				if e.get("lit", false):
					e["fuel"] = float(e["fuel"]) - dh
					if float(e["fuel"]) <= 0.0 or (rain > 0.5 and c.bld[i] == 0 and randf() < dh * 2.0) or catch_up:
						e["lit"] = false
						e["fuel"] = maxf(float(e["fuel"]), 0.0)
						c.obj[i] = Defs.ocell(Defs.O_CAMPFIRE, 0, 0)
						c.modified = true
						world.notify(x, y)
					else:
						fires.append(Vector2i(x, y))
			"barrel":
				var frz: bool = float(weather["temp"]) < -2.0 and c.bld[i] == 0
				if frz != bool(e.get("ice", false)):
					e["ice"] = frz
				if rain > 0.05 and not frz:
					e["w"] = minf(40.0, float(e["w"]) + rain * 6.0 * dh)
			"bank":
				e["w"] = clampf(float(e.get("w", 0.0)), 0.0, BANK_MAX)
				if float(e["w"]) > 0.5 and not e.get("off", false) and not catch_up:
					banks.append(Vector2i(x, y))
			"solar":
				# daylight and clear sky charge any battery bank within reach
				var sun: float = clampf(daylight() * (1.0 - float(weather.get("cloud", 0.0)) * 0.7), 0.0, 1.0)
				if sun > 0.05:
					for bdy in range(-6, 7):
						for bdx in range(-6, 7):
							var be: Dictionary = world.ent(x + bdx, y + bdy)
							if be.get("k", "") == "bank":
								be["w"] = minf(BANK_MAX, float(be.get("w", 0.0)) + sun * dh * 1.5)
			"gen":
				if e.get("on", false):
					var load: int = loads_near(x, y, GEN_RANGE)
					e["load"] = load
					e["fuel"] = float(e["fuel"]) - dh * (0.6 + 0.1 * float(mini(load, 10)))
					e["c"] = float(e.get("c", 1.0)) - dh * (0.004 + (0.03 * float(load - GEN_CAP) if load > GEN_CAP else 0.0))
					# rain on an uncovered generator
					if rain > 0.3 and c.bld[i] == 0 and randf() < dh * rain * 0.6:
						e["c"] = float(e["c"]) - 0.25
						if not catch_up: say("Rain gets into the generator. It sparks and coughs.", Color(1.0, 0.75, 0.5))
					if load > GEN_CAP + 3 and randf() < dh * 0.15:
						ignite(x, y, 1.2)                      # an overloaded generator catches fire
						if not catch_up: say("The overloaded generator bursts into flames!", Color(1.0, 0.55, 0.4))
					if load > GEN_CAP + 3 and randf() < dh * 2.0:
						e["on"] = false
						if not catch_up: say("The generator trips — too many things on at once (%d of %d)." % [load, GEN_CAP], Color(1.0, 0.75, 0.5))
					# a running generator tops up nearby battery banks
					for gdy in range(-4, 5):
						for gdx in range(-4, 5):
							var ge: Dictionary = world.ent(x + gdx, y + gdy)
							if ge.get("k", "") == "bank":
								ge["w"] = minf(BANK_MAX, float(ge.get("w", 0.0)) + dh * 4.0)
					if float(e["c"]) <= 0.0:
						e["on"] = false
						e["c"] = 0.0
						if not catch_up: say("A generator sputters and dies. It needs repair.", Color(1.0, 0.8, 0.5))
					elif float(e["fuel"]) <= 0.0:
						e["on"] = false
						e["fuel"] = 0.0
					elif not catch_up:
						generators.append(Vector2i(x, y))
			"berry":
				if hour - float(e["h"]) > 72.0:
					c.ents.erase(i)
					c.obj[i] = Defs.ocell(Defs.O_BERRY_BUSH, 0, 0)
					world.notify(x, y)
			"forage":
				if hour - float(e["h"]) > 30.0:
					c.ents.erase(i)
			"coop":
				if int(e.get("hens", 0)) > 0:
					if float(e.get("fed", 0.0)) > 0.0:
						e["fed"] = float(e["fed"]) - dh
						e["eggs"] = minf(12.0, float(e.get("eggs", 0.0)) + float(int(e["hens"])) * dh / 22.0)
						e["starve"] = 0.0
					else:
						e["starve"] = float(e.get("starve", 0.0)) + dh
						if float(e["starve"]) > 72.0:
							e["starve"] = 0.0
							e["hens"] = int(e["hens"]) - 1
			"trap":
				if String(e.get("caught", "")) == "":
					# snares work best far from people and with bait
					var chance: float = (0.03 + 0.012 * player.skill_level("trapping") + 0.006 * player.skill_level("tracking")) * dh
					if e.get("bait", 0) == 1: chance *= 2.2
					if c.zone >= 2: chance *= 0.25
					if not catch_up and Vector2(x + 0.5, y + 0.5).distance_to(player.pos) < 10.0: chance *= 0.15
					if randf() < chance:
						e["caught"] = "raw_rabbit" if randf() < 0.65 else "raw_bird"
						e["ch"] = hour
						e["bait"] = 0
						c.touched = true
	# refrigeration: powered fridges slow spoilage by pushing the birth time forward
	if not c.containers.is_empty():
		for ci in c.containers.keys():
			var oid: int = c.obj[ci] & 1023
			if oid == Defs.O_COMPOST:
				# rotten food breaks down into fertiliser
				var bin: Array = c.containers[ci]
				var rotten: Array = []
				for it in bin:
					if Items.fresh_state(it, hour) == 2:
						rotten.append(it)
				var units := 0
				for it in rotten:
					units += int(it.get("n", 1))
				if units >= 4 and randf() < dh * 0.25:
					var need := 4
					for it in rotten:
						var take: int = mini(need, int(it.get("n", 1)))
						it["n"] = int(it["n"]) - take
						need -= take
						if int(it["n"]) <= 0:
							bin.erase(it)
						if need <= 0:
							break
					bin.append(Items.make("fertilizer", 1, hour))
					c.touched = true
				continue
			if oid != Defs.O_FRIDGE and oid != Defs.O_FREEZER:
				continue
			var x2: int = c.cx * 16 + (int(ci) & 15)
			var y2: int = c.cy * 16 + (int(ci) >> 4)
			if not has_power(x2, y2):
				continue
			for it in c.containers[ci]:
				if it.has("t"):
					it["t"] = float(it["t"]) + dh * 0.8

## bring a freshly loaded chunk up to date with the time it was away
func _catch_up(c: Chunk) -> void:
	if c.last_hour <= 0.0 or not c.touched:
		c.last_hour = hour
		return
	var elapsed: float = hour - c.last_hour
	if elapsed > 0.05:
		# fridge preservation only counts while the grid was still up
		var powered: float = clampf(minf(hour, power_off_h) - c.last_hour, 0.0, elapsed)
		if not c.ents.is_empty():
			_sim_ents_away(c, elapsed)
		if powered > 0.0:
			for ci in c.containers.keys():
				var oid: int = c.obj[ci] & 1023
				if oid == Defs.O_FRIDGE or oid == Defs.O_FREEZER:
					for it in c.containers[ci]:
						if it.has("t"):
							it["t"] = float(it["t"]) + powered * 0.8
		var ci2: int = c.corpses.size() - 1
		while ci2 >= 0:
			if hour - float(c.corpses[ci2]["h"]) > 96.0 and not c.corpses[ci2].has("perm"):
				c.corpses.remove_at(ci2)
			ci2 -= 1

func _sim_ents_away(c: Chunk, elapsed: float) -> void:
	# coarse steps so crops keep growing while the player is elsewhere
	var steps: int = clampi(int(elapsed / 2.0), 1, 60)
	var saved_rain: float = weather["rain"]
	weather["rain"] = 0.12      # average drizzle over long absences
	for s in range(steps):
		_sim_ents(c, elapsed / float(steps), true)
	weather["rain"] = saved_rain

# ------------------------------------------------------------------ sleeping
func start_sleep(quality: float) -> void:
	var p: Player = player
	if p.fatigue < 20.0:
		say("You are not tired enough to sleep", Color(0.8, 0.8, 0.9))
		return
	if p.pain > 65.0:
		say("The pain keeps you awake", Color(1.0, 0.7, 0.6))
		return
	if p.panic > 40.0:
		say("You are too panicked to sleep", Color(1.0, 0.7, 0.6))
		return
	for z in zombies.list:
		if z.state >= Zombie.INVESTIGATE and z.pos.distance_squared_to(p.pos) < 100.0:
			say("You can't sleep with the infected so close", Color(1.0, 0.7, 0.6))
			return
	p.cancel_action()
	p.sleeping = true
	flags["slept"] = true
	sleep_quality = quality
	time_scale = 20.0          # the world keeps acting while you sleep, twenty times faster
	ui_events.append({"type": "sleep"})

# ------------------------------------------------------------------ persistence
func save_meta() -> Dictionary:
	return {"v": SaveGame.SCHEMA, "seed": seed_v, "hour": hour, "settings": settings, "weather": weather,
		"player": player.save(), "safe_pos": safe_pos, "safe_bld": safe_bld, "alarms_done": alarms_done,
		"power_off": power_off_h, "water_off": water_off_h, "explored": world.explored, "dead": dead,
		"psaid": _power_said, "wsaid": _water_said, "rng": rng.state, "flags": flags, "guide": guide_i,
		"fly_next": fly_next_h, "fly_end": fly_end_h, "fly_on": fly_active, "lives": lives,
		"vehicle": vehicle.save() if vehicle != null else {}, "burning": burning, "factions": factions.save(), "pipes": pipes, "fish": fish, "snowc": snow_cover, "home": home, "psites": pending_sites, "objectives": objectives, "event_h": _event_h, "unjammed": unjammed, "trader_h": _trader_h, "flooded": flooded, "weth": _wet_h}

func load_meta(d: Dictionary) -> void:
	factions.load(d.get("factions", {}))
	pipes = d.get("pipes", {})
	fish = d.get("fish", {})
	snow_cover = d.get("snowc", 0.0)
	home = d.get("home", {})
	objectives = d.get("objectives", [])
	_event_h = d.get("event_h", 30.0)
	pending_sites = d.get("psites", {})
	unjammed = d.get("unjammed", {})
	_trader_h = d.get("trader_h", 60.0)
	flooded = d.get("flooded", {})
	_wet_h = d.get("weth", 0.0)
	hour = d["hour"]
	world.hour = hour
	var st: Dictionary = d.get("settings", {})
	for k in st.keys():
		settings[k] = st[k]
	var wt: Dictionary = d.get("weather", {})
	for k in wt.keys():
		weather[k] = wt[k]
	safe_pos = d.get("safe_pos", Vector2.ZERO)
	safe_bld = d.get("safe_bld", 0)
	safe_radius = 0.0
	alarms_done = d.get("alarms_done", {})
	power_off_h = d.get("power_off", power_off_h)
	water_off_h = d.get("water_off", water_off_h)
	world.explored = d.get("explored", {})
	dead = d.get("dead", false)
	_power_said = d.get("psaid", false)
	_water_said = d.get("wsaid", false)
	if d.has("rng"):
		rng.state = d["rng"]
	flags = d.get("flags", {})
	guide_i = d.get("guide", -1)
	fly_next_h = d.get("fly_next", 1e12)
	fly_end_h = d.get("fly_end", 0.0)
	fly_active = d.get("fly_on", false)
	lives = d.get("lives", 0)
	burning = d.get("burning", {})
	var vd: Dictionary = d.get("vehicle", {})
	if not vd.is_empty():
		vehicle = Vehicle.from_save(self, vd)
	world.growth = float(settings.get("growth", 1.0))
	player.load(d["player"])
	world.loot_mult = float(settings["loot"]) * player.tmod("loot")
	_guide_inv = player.inv.size()
