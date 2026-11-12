class_name Sim
extends RefCounted
## The whole simulation: world, player, zombies, clock, weather, utilities, noise.
## No scene-tree access — it can run headless and is what the save file describes.

const START_HOUR := 9.0

var world: World
var player: Player
var zombies: ZombieSim
var rng := RandomNumberGenerator.new()
var seed_v := 0
var hour := START_HOUR           # absolute game hours since midnight of day 1
var time_scale := 1.0
var settings := {"zombies": 1.0, "loot": 1.0, "day_min": 48.0, "infection": true, "god": false, "respawn": true, "zspeed": 1.0,
	"xp": 1.0, "util": 1, "season": 0, "flyover": 1, "kit": false, "growth": 1.0, "dark": 1.0, "guide": true, "meta": true}
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
var fires: Array = []            # Vector2i of lit campfires (loaded chunks)
var lamps: Array = []            # Vector2i light-emitting objects near the player
var dead := false
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
	world.on_unload = zombies.on_chunk_unload
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

## place the player in a building of the chosen kind near the starting town
func new_game(occupation: String, trait_list: Array = [], start_kind: String = "house") -> void:
	apply_settings()
	var st: Dictionary = world.gen.find_start(start_kind)
	player.pos = st["pos"]
	safe_pos = player.pos
	player.look = [rng.randi() % 4, rng.randi() % 10, rng.randi() % 6, rng.randi() % 6]
	player.setup_occupation(occupation, trait_list)
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
	return World.is_under(player.pos.y)

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
	if hour < power_off_h:
		return true
	for g in generators:
		if absi(g.x - x) <= 14 and absi(g.y - y) <= 14:
			return true
	return false

func has_water() -> bool:
	return hour < water_off_h

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
	ui_events.append({"type": "death"})

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
	player.update(dt, move_screen, want_run)
	player.tick_needs(dh)
	zombies.update(dt)
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
	weather["temp"] = temperature_base() - rain * 3.0 - c * 2.0
	if hour >= power_off_h and not _power_said:
		_power_said = true
		say("The lights flicker and die. The power grid is down.", Color(1.0, 0.8, 0.5))
		ui_events.append({"type": "power"})
	if hour >= water_off_h and not _water_said:
		_water_said = true
		say("The taps sputter. The water has stopped.", Color(1.0, 0.8, 0.5))

# ------------------------------------------------------------------ slow world tick (1 Hz)
func _slow_tick(dh: float) -> void:
	generators.clear()
	fires.clear()
	lamps.clear()
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
	# running generators hum
	for g in generators:
		noise(Vector2(g.x + 0.5, g.y + 0.5), 11.0)

func _sim_ents(c: Chunk, dh: float, catch_up: bool) -> void:
	var rain: float = weather["rain"]
	for i in c.ents.keys():
		var e: Dictionary = c.ents[i]
		var x: int = c.cx * 16 + (int(i) & 15)
		var y: int = c.cy * 16 + (int(i) >> 4)
		match e.get("k", ""):
			"crop":
				var outdoors: bool = c.bld[i] == 0
				if outdoors and rain > 0.05:
					e["w"] = minf(100.0, float(e["w"]) + rain * 40.0 * dh)
				var stage: int = e["s"]
				if stage < 3:
					if float(e["w"]) > 5.0:
						e["g"] = float(e["g"]) + dh * (1.4 if e.get("f", 0) == 1 else 1.0)
						e["dry"] = 0.0
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
				if rain > 0.05:
					e["w"] = minf(40.0, float(e["w"]) + rain * 6.0 * dh)
			"gen":
				if e.get("on", false):
					e["fuel"] = float(e["fuel"]) - dh
					e["c"] = float(e.get("c", 1.0)) - dh * 0.004
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
			"trap":
				if String(e.get("caught", "")) == "":
					# snares work best far from people and with bait
					var chance: float = (0.03 + 0.012 * player.skill_level("trapping")) * dh
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
	time_scale = 60.0
	ui_events.append({"type": "sleep"})

# ------------------------------------------------------------------ persistence
func save_meta() -> Dictionary:
	return {"v": SaveGame.SCHEMA, "seed": seed_v, "hour": hour, "settings": settings, "weather": weather,
		"player": player.save(), "safe_pos": safe_pos, "safe_bld": safe_bld, "alarms_done": alarms_done,
		"power_off": power_off_h, "water_off": water_off_h, "explored": world.explored, "dead": dead,
		"psaid": _power_said, "wsaid": _water_said, "rng": rng.state, "flags": flags, "guide": guide_i,
		"fly_next": fly_next_h, "fly_end": fly_end_h, "fly_on": fly_active}

func load_meta(d: Dictionary) -> void:
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
	world.growth = float(settings.get("growth", 1.0))
	player.load(d["player"])
	world.loot_mult = float(settings["loot"]) * player.tmod("loot")
	_guide_inv = player.inv.size()
