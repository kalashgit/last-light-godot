class_name Sfx
extends Node
## The game's sound. Everything comes from a library made offline by tools/audio/make_sounds.py
## (assets/audio, listed in manifest.json): effects with several takes each, ambience and machine
## loops, and music. A take is picked at random, never the one heard last, and pitched a little, so
## nothing repeats exactly. A sound comes from where it happens: it pans with its place on screen,
## falls away with distance, and is muffled through walls, floors and shut doors.
## Under everything run loops that fade toward the level the world asks for: wind, rain on the street
## or drumming on the roof, crickets on warm nights, birds by day, a low pulse when the infected are
## close, the engine you are driving, a fire, an alarm, rotor blades overhead.
## Music: a title theme, short cues at dawn, at night, in the rain and at home, and one for death.
## The library loads a few files a frame, so the game starts at once.

const LIB := "res://assets/audio/"
const LOAD_BUDGET_USEC := 4000          # how much of each frame loading may take
const VOICES := 16
const BEDS := ["bed_wind", "bed_rain", "bed_rain_in", "bed_crickets", "bed_birds", "bed_tension",
	"loop_engine", "loop_fire", "loop_alarm", "loop_caralarm", "loop_rotor"]
## how loud each cue plays (dB); calm cues sit under the world, the title and death come forward
const MUSIC_DB := {"title": -3.0, "dawn": -9.0, "night": -10.0, "rain": -10.0, "home": -9.0, "death": -4.0}
const CALM := ["dawn", "night", "rain", "home"]
## which gunshot each gun makes
const GUN_SHOT := {"pistol": "shot_pistol", "revolver": "shot_revolver", "shotgun": "shot_shotgun", "rifle": "shot_rifle"}
static var build_now := false           # tests: load everything at once

var _lib: Dictionary = {}               # effect -> Array of AudioStream (its takes)
var _last: Dictionary = {}              # effect -> the take heard last
var _loops: Dictionary = {}             # loop -> AudioStream
var _music: Dictionary = {}             # cue -> AudioStream
var _queue: Array = []                  # [kind, name, path] still to load
var _players: Array[AudioStreamPlayer] = []
var _started: Array = []                # when each voice last started (msec), so the oldest is the one cut off
var _players2d: Array = []              # positional voices: pan with where the sound is on screen
var _started2d: Array = []
var _bus := "Near"
var _pos: Variant = null                # where in the world the sound being played comes from (screen coords), or null
var _beds: Dictionary = {}              # loop -> AudioStreamPlayer
var _room_wet := 0.0
var _music_p: AudioStreamPlayer         # the cue playing now
var _music_old: AudioStreamPlayer       # the cue fading out
var _music_cue := ""                    # what _music_p is playing
var _music_want := ""                   # a cue asked for before it had loaded
var _shuffle_t := 0.0

func _ready() -> void:
	_make_buses()
	for i in range(VOICES):
		var p := AudioStreamPlayer.new()
		add_child(p)
		_players.append(p)
		_started.append(0)
		var p2 := AudioStreamPlayer2D.new()
		p2.attenuation = 0.0            # distance is already in the volume; this voice only pans
		p2.max_distance = 6000.0
		p2.panning_strength = 1.4
		add_child(p2)
		_players2d.append(p2)
		_started2d.append(0)
	_music_p = AudioStreamPlayer.new()
	_music_old = AudioStreamPlayer.new()
	for mp in [_music_p, _music_old]:
		mp.bus = "Music"
		add_child(mp)
	_queue = manifest_queue()
	if build_now:
		_load_some(-1)
		_start_beds()

## everything in the library, in the order it is wanted: the title music first, then the effects,
## the loops and the rest of the music
static func manifest_queue() -> Array:
	var q: Array = []
	if not FileAccess.file_exists(LIB + "manifest.json"):
		push_warning("Sfx: no sound library at %smanifest.json" % LIB)
		return q
	var m = JSON.parse_string(FileAccess.get_file_as_string(LIB + "manifest.json"))
	if typeof(m) != TYPE_DICTIONARY:
		return q
	var mus: Dictionary = m.get("music", {})
	if mus.has("title"):
		q.append(["music", "title", LIB + String(mus["title"])])
	var snd: Dictionary = m.get("sounds", {})
	for nm in snd.keys():
		for fn in snd[nm]:
			q.append(["sfx", nm, LIB + String(fn)])
	var lp: Dictionary = m.get("loops", {})
	for nm in lp.keys():
		q.append(["loop", nm, LIB + String(lp[nm])])
	for nm in mus.keys():
		if nm != "title":
			q.append(["music", nm, LIB + String(mus[nm])])
	return q

## load from the queue until the deadline (usec; -1: all of it)
func _load_some(deadline: int) -> void:
	while not _queue.is_empty():
		var it: Array = _queue.pop_front()
		var s: Resource = load(String(it[2]))
		if s is AudioStream:
			match String(it[0]):
				"sfx":
					if not _lib.has(it[1]):
						_lib[it[1]] = []
					(_lib[it[1]] as Array).append(s)
				"loop":
					set_loop(s, true)
					_loops[it[1]] = s
				"music":
					set_loop(s, it[1] == "title")
					_music[it[1]] = s
		else:
			push_warning("Sfx: could not load %s" % it[2])
		if deadline >= 0 and Time.get_ticks_usec() >= deadline:
			return

static func set_loop(s: AudioStream, on: bool) -> void:
	if s is AudioStreamOggVorbis:
		(s as AudioStreamOggVorbis).loop = on
	elif s is AudioStreamWAV:
		var w := s as AudioStreamWAV
		w.loop_mode = AudioStreamWAV.LOOP_FORWARD if on else AudioStreamWAV.LOOP_DISABLED
		w.loop_begin = 0
		w.loop_end = int(w.get_length() * w.mix_rate) if on else 0

func ready_all() -> bool:
	return _queue.is_empty()

func _process(dt: float) -> void:
	if not _queue.is_empty():
		_load_some(Time.get_ticks_usec() + LOAD_BUDGET_USEC)
	if _beds.is_empty() and not _loops.is_empty() and (_queue.is_empty() or _loops.size() >= BEDS.size()):
		_start_beds()
	if _music_want != "" and _music.has(_music_want):
		var w: String = _music_want
		_music_want = ""
		music(w)
	_fade_music(dt)

## "Near": your own space (a little room echo indoors); "Muffled": through walls, a floor or a shut
## door; "Music": the score, with its own volume
static func _make_buses() -> void:
	if AudioServer.get_bus_index("Near") >= 0:
		return
	for nm in ["Near", "Muffled", "Music"]:
		AudioServer.add_bus()
		var bi: int = AudioServer.bus_count - 1
		AudioServer.set_bus_name(bi, nm)
		AudioServer.set_bus_send(bi, "Master")
		if nm == "Near":
			var rv := AudioEffectReverb.new()
			rv.room_size = 0.32
			rv.damping = 0.6
			rv.wet = 0.0
			rv.dry = 1.0
			AudioServer.add_bus_effect(bi, rv)
		elif nm == "Muffled":
			var lp := AudioEffectLowPassFilter.new()
			lp.cutoff_hz = 900.0
			AudioServer.add_bus_effect(bi, lp)
			AudioServer.set_bus_volume_db(bi, -5.0)
	Opts.apply()

## which bus a sound from src belongs on for a listener at the player
static func bus_for(sim: Sim, src: Vector2) -> String:
	var lp: Vector2 = sim.player.pos
	if src.distance_to(lp) < 1.5:
		return "Near"
	var bl: int = sim.world.bld(floori(lp.x), floori(lp.y))
	var bs: int = sim.world.bld(floori(src.x), floori(src.y))
	if World.level(src.y) != World.level(lp.y) or bl != bs:
		return "Muffled"
	return "Near"

## a take of `name`, never the one heard last when there is a choice (null if there is none)
func pick(name: String) -> AudioStream:
	var takes: Array = _lib.get(name, [])
	if takes.is_empty():
		return null
	var i: int = randi() % takes.size()
	if takes.size() > 1 and i == int(_last.get(name, -1)):
		i = (i + 1 + randi() % (takes.size() - 1)) % takes.size()
	_last[name] = i
	return takes[i]

## play a take of `name`, `volume_db` from its level in the library, at speed `pitch`
func play(name: String, volume_db: float = 0.0, pitch: float = 1.0) -> void:
	var s: AudioStream = pick(name)
	if s == null:
		return
	# a free voice if there is one; otherwise cut off the oldest sound, never the newest
	var pool: Array = _players if _pos == null else _players2d
	var st: Array = _started if _pos == null else _started2d
	var vi: int = -1
	var oldest: int = 0
	for i in range(pool.size()):
		if not pool[i].playing:
			vi = i
			break
		if int(st[i]) < int(st[oldest]):
			oldest = i
	if vi < 0:
		vi = oldest
	var p = pool[vi]
	st[vi] = Time.get_ticks_msec()
	if _pos != null:
		(p as AudioStreamPlayer2D).global_position = _pos
	p.bus = _bus
	p.stream = s
	p.volume_db = volume_db
	p.pitch_scale = pitch
	p.play()

# ------------------------------------------------------------------ choosing the sound for an event
## which footstep: the ground under the foot decides (and snow lying out in the open covers it)
func _step_for(sim: Sim, p: Vector2) -> String:
	var g: int = sim.world.ground(floori(p.x), floori(p.y))
	if g == Defs.G_WATER or g == Defs.G_DEEP_WATER:
		return "step_water"
	if sim.snow_cover > 0.25 and World.level(p.y) == 0 and sim.world.bld(floori(p.x), floori(p.y)) == 0:
		return "step_snow"
	match g:
		Defs.G_WOOD, Defs.G_WOOD_DARK, Defs.G_PLANK: return "step_wood"
		Defs.G_GRASS, Defs.G_GRASS_DARK, Defs.G_FOREST: return "step_grass"
		Defs.G_DIRT, Defs.G_SOIL, Defs.G_SAND: return "step_dirt"
		Defs.G_GRAVEL: return "step_gravel"
		Defs.G_TILE, Defs.G_TILE_BLUE, Defs.G_LINO: return "step_tile"
		Defs.G_CARPET_RED, Defs.G_CARPET_BLUE, Defs.G_CARPET_BEIGE: return "step_carpet"
	return "step_concrete"

## the air the weapon moves: a blade whips, a bat whooshes, an axe or a sledge heaves
static func swing_for(e: Dictionary) -> String:
	match String(e.get("wt", "blunt")):
		"shove": return "swing_shove"
		"blade", "spear": return "swing_blade"
		"axe": return "swing_heavy"
	return "swing_heavy" if float(e.get("kg", 1.0)) >= 2.0 else "swing_blunt"

## what landing sounds like: a crack, a wet cut, a bullet going in, a skull giving way
static func hit_for(e: Dictionary) -> String:
	if bool(e.get("crit", false)) and String(e.get("w", "blunt")) != "shove":
		return "hit_crit"
	match String(e.get("w", "blunt")):
		"blade": return "hit_blade"
		"bullet": return "hit_bullet"
	return "hit_blunt"

static func shot_for(e: Dictionary) -> String:
	var gun: String = String(e.get("gun", ""))
	if GUN_SHOT.has(gun):
		return GUN_SHOT[gun]
	var g: Dictionary = Items.def(gun).get("gun", {}) if gun != "" else {}
	match String(g.get("ammo", "")):
		"shells": return "shot_shotgun"
		"rifle_rounds": return "shot_rifle"
	return "shot_pistol"

func consume(sim: Sim, _view: WorldView) -> void:
	var pp: Vector2 = sim.player.pos
	var steps := 0
	var groans := 0
	var snarls := 0
	# indoors your own sounds come back off the walls
	var inside: bool = sim.world.bld(floori(pp.x), floori(pp.y)) != 0 or sim.underground()
	_room_wet = move_toward(_room_wet, 0.16 if inside else 0.0, 0.02)
	var nb: int = AudioServer.get_bus_index("Near")
	if nb >= 0:
		(AudioServer.get_bus_effect(nb, 0) as AudioEffectReverb).wet = _room_wet
	for e in sim.fx:
		var k: String = e["k"]
		var ev_p: Vector2 = e["p"]
		var d: float = ev_p.distance_to(pp)
		if k.begins_with("music_"):
			music(k.substr(6))
			continue
		_bus = bus_for(sim, ev_p)
		_pos = Iso.to_screen(ev_p.x, ev_p.y)
		if k.begins_with("meta_"):
			# distant events are heard from far beyond the screen
			var mv: float = -6.0 - d * 0.25
			match k:
				"meta_gunshot": play("shot_far", mv - 2.0, randf_range(0.9, 1.05))
				"meta_scream": play("scream", mv - 3.0, randf_range(0.94, 1.06))
				"meta_dog": play("bark", mv, randf_range(0.9, 1.1))
				"meta_crash": play("crash_far", mv)
				# (a car alarm is carried by its loop)
			continue
		if d > 26.0:
			continue
		var vol: float = -d * 0.9
		var pv: float = randf_range(0.96, 1.04)
		match k:
			"step":
				steps += 1
				if steps <= 1:
					var soft: bool = d < 0.6 and sim.player.sneaking
					play(_step_for(sim, ev_p), vol - (17.0 if soft else 11.0) + randf_range(-1.5, 1.0), randf_range(0.93, 1.07))
			"swing": play(swing_for(e), vol - 9.0, pv)
			"hit": play(hit_for(e), vol - (7.0 if String(e.get("w", "")) == "shove" else 3.0), randf_range(0.92, 1.08))
			"zdie": play("zdie", vol - 3.0, randf_range(0.9, 1.08))
			"groan":
				groans += 1
				if groans <= 2: play("groan", vol - 7.0, randf_range(0.88, 1.1))
			"snarl":
				snarls += 1
				if snarls <= 1: play("snarl", vol - 4.0, randf_range(0.9, 1.1))
			"shot": play(shot_for(e), 0.0, randf_range(0.97, 1.03))
			"thump": play("thump", vol - 2.0, randf_range(0.9, 1.08))
			"glass": play("glass", vol - 2.0, pv)
			"door":
				if bool(e.get("car", false)): play("car_door", vol - 4.0, pv)
				elif e.has("open"): play("door_open" if bool(e["open"]) else "door_close", vol - 5.0, pv)
				else: play("door_open" if randf() < 0.5 else "door_close", vol - 5.0, pv)
			"locked": play("locked", vol - 5.0, pv)
			"break": play("break", vol - 2.0, pv)
			"hurt": play("hurt", -3.0, randf_range(0.95, 1.05))
			"death":
				play("death", -1.0)
				music("death")
			"pickup": play("pickup", -9.0, pv)
			"equip": play("equip", -9.0, pv)
			"reload": play("reload", -6.0, pv)
			"eat": play("eat", -6.0, pv)
			"build": play("build", vol - 5.0, pv)
			"click": play("click", -8.0)
			"levelup": play("levelup", -8.0)
			"sneeze": play("sneeze", -4.0)
			"call": play("call", vol - 4.0)
			"thunder": play("thunder", -3.0, randf_range(0.85, 1.05))
			"horn": play("siren" if bool(e.get("siren", false)) else "horn", vol - 3.0)
			"ignition": play("ignition", vol - 6.0)
			# "engine", "fire", "alarm", "rotor": their loops carry them
	_bus = "Near"
	_pos = null
	_update_beds(sim)
	_shuffles(sim)

# ------------------------------------------------------------------ the world's background
func _start_beds() -> void:
	for b in BEDS:
		if not _loops.has(b) or _beds.has(b):
			continue
		var p := AudioStreamPlayer.new()
		p.stream = _loops[b]
		p.volume_db = -80.0
		p.bus = "Near"
		add_child(p)
		if p.is_inside_tree():
			p.play()
		_beds[b] = p

## the level each loop should sit at, from what the world is doing right now
static func bed_targets(sim: Sim) -> Dictionary:
	var pp: Vector2 = sim.player.pos
	var under: bool = sim.underground()
	var inside: bool = sim.world.bld(floori(pp.x), floori(pp.y)) != 0 or under
	var wind: float = float(sim.weather.get("wind", 0.2))
	var rain: float = float(sim.weather.get("rain", 0.0))
	var light: float = sim.daylight()
	var warm: bool = float(sim.weather.get("temp", 15.0)) > 9.0
	var threat: int = sim.zombies.count_threats(pp, 12.0)
	var t := {}
	t["bed_wind"] = (-34.0 + wind * 22.0) - (12.0 if inside else 0.0)
	# out in it you hear the street hiss; under a roof, the drumming overhead and drips off the eaves
	t["bed_rain"] = -80.0 if rain < 0.05 or inside else -26.0 + rain * 18.0
	t["bed_rain_in"] = -80.0 if rain < 0.05 or not inside or under else -28.0 + rain * 16.0
	t["bed_crickets"] = -24.0 if (light < 0.3 and warm and not inside and rain < 0.3) else -80.0
	t["bed_birds"] = -26.0 if (light > 0.6 and rain < 0.2 and warm and not inside) else -80.0
	t["bed_tension"] = -80.0 if threat == 0 else clampf(-22.0 + float(threat) * 3.0, -22.0, -9.0)
	# machines and fires
	var v: Vehicle = sim.vehicle
	var running: bool = v != null and v.motor() and float(v.ent.get("fuel", 0.0)) > 0.0 and float(v.ent.get("eng", 1.0)) > 0.05
	t["loop_engine"] = -9.0 if running else -80.0
	var fd := 99.0
	for b in sim.burning.keys():
		fd = minf(fd, Vector2(b.x + 0.5, b.y + 0.5).distance_to(pp))
	t["loop_fire"] = -80.0 if fd > 14.0 else -9.0 - fd * 1.6
	var ad := 99.0
	var cd := 99.0
	for a in sim.alarms:
		var dd: float = (a[0] as Vector2).distance_to(pp)
		if a.size() > 2 and String(a[2]) == "car":
			cd = minf(cd, dd)
		else:
			ad = minf(ad, dd)
	t["loop_alarm"] = -80.0 if ad > 60.0 else -5.0 - ad * 0.5
	t["loop_caralarm"] = -80.0 if cd > 60.0 else -7.0 - cd * 0.5
	t["loop_rotor"] = -80.0 if not sim.fly_active or under else -5.0 - minf(sim.fly_track.distance_to(pp), 40.0) * 0.35
	return t

func _update_beds(sim: Sim) -> void:
	if _beds.is_empty():
		return
	var tg: Dictionary = bed_targets(sim)
	var dt: float = get_process_delta_time()
	for b in _beds.keys():
		var pl: AudioStreamPlayer = _beds[b]
		var want: float = float(tg.get(b, -80.0))
		pl.volume_db = move_toward(pl.volume_db, want, dt * (30.0 if want > pl.volume_db else 18.0))
	# the engine climbs in pitch as you pick up speed
	if _beds.has("loop_engine") and sim.vehicle != null:
		var ep: AudioStreamPlayer = _beds["loop_engine"]
		ep.pitch_scale = lerpf(ep.pitch_scale, 0.85 + minf(absf(sim.vehicle.speed), 8.0) * 0.1, minf(1.0, dt * 4.0))
	# a calm cue gives way when the infected come
	if _music_cue in CALM and float(tg["bed_tension"]) > -60.0:
		music("")

## the infected close by drag their feet: now and then the nearest one on the move is heard
func _shuffles(sim: Sim) -> void:
	_shuffle_t -= get_process_delta_time()
	if _shuffle_t > 0.0:
		return
	_shuffle_t = randf_range(0.55, 0.95)
	var pp: Vector2 = sim.player.pos
	var best: Zombie = null
	var bd := 9.0
	for z in sim.zombies.list:
		if z.anim != "z_walk" and z.anim != "z_crawl":
			continue
		var dz: float = z.pos.distance_to(pp)
		if dz < bd:
			bd = dz
			best = z
	if best == null:
		return
	_bus = bus_for(sim, best.pos)
	_pos = Iso.to_screen(best.pos.x, best.pos.y)
	play("shuffle", -13.0 - bd * 1.2, randf_range(0.85, 1.1))
	_bus = "Near"
	_pos = null

# ------------------------------------------------------------------ music
## start a cue ("" fades the music out); the cue already playing carries on. The old cue fades out
## while the new one fades in.
func music(cue: String) -> void:
	if cue == _music_cue and (cue == "" or _music_p.playing):
		return
	if cue != "" and not _music.has(cue):
		_music_want = cue                  # not loaded yet: it starts when it is
		return
	_music_want = ""
	if _music_p.playing:
		var tmp: AudioStreamPlayer = _music_old
		_music_old = _music_p
		_music_p = tmp
	_music_p.stop()
	_music_cue = cue
	if cue == "":
		return
	_music_p.stream = _music[cue]
	_music_p.volume_db = float(MUSIC_DB.get(cue, -8.0)) - (0.0 if cue == "death" else 24.0)
	if _music_p.is_inside_tree():
		_music_p.play()

func _fade_music(dt: float) -> void:
	if _music_old.playing:
		_music_old.volume_db = move_toward(_music_old.volume_db, -60.0, dt * 18.0)
		if _music_old.volume_db <= -59.0:
			_music_old.stop()
	if _music_p.playing:
		_music_p.volume_db = move_toward(_music_p.volume_db, float(MUSIC_DB.get(_music_cue, -8.0)), dt * 16.0)

func music_cue() -> String:
	return _music_cue if _music_p.playing else ""
