class_name Sfx
extends Node
## Procedural sound effects: every sample is synthesised into PCM at boot.

const RATE := 22050
var _streams: Dictionary = {}
var _players: Array[AudioStreamPlayer] = []
var _next := 0
var _ambient_t := 0.0
var _rotor_t := 0.0
var _bus := "Near"
var _pos: Variant = null          # where in the world the sound being played comes from (screen coords), or null
var _players2d: Array = []        # positional voices: pan with where the sound is on screen
var _started2d: Array = []
static var build_now := false     # tests: build everything immediately
var _extra: Dictionary = {}       # streams built off the main thread, waiting to be handed over
var _beds: Dictionary = {}        # loop name -> AudioStreamPlayer (wind, rain, crickets, birds, tension)
var _started: Array = []      # when each voice last started (msec), so the oldest is the one cut off
var _room_wet := 0.0

func _ready() -> void:
	_make_buses()
	for i in range(16):
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
	# the voices and the background loops take a second or two to synthesise: do it off the main
	# thread so the game starts at once, and hand them over when they are ready
	if build_now:
		_build_extra()
		_extra_ready()
	else:
		WorkerThreadPool.add_task(func():
			_build_extra()
			call_deferred("_extra_ready"))
	_make("thunder", 1.6, func(t, n): return n * (0.7 * exp(-t * 2.2) + 0.3 * exp(-absf(t - 0.4) * 6.0)) * (0.6 + 0.4 * sin(t * 13.0)))
	_make("fire", 0.3, func(t, n): return n * 0.35 * (0.3 + 0.7 * absf(sin(t * 61.0))) * exp(-t * 4.0))
	_make("engine", 0.5, func(t, n): return (sin(t * 62.0 * TAU) * 0.4 + sin(t * 124.0 * TAU) * 0.2 + n * 0.12) * (0.7 + 0.3 * sin(t * 28.0 * TAU)) * sin(t / 0.5 * PI))
	_make("call", 0.3, func(t, n): return (sin(t * (330.0 + t * 260.0) * TAU) * 0.4 + sin(t * 660.0 * TAU) * 0.12 + n * 0.05) * sin(t / 0.3 * PI))
	for v in range(3):
		var sh: float = 1.0 + float(v) * 0.07
		_make("step%d" % v, 0.09, func(t, n): return (sin(t * 85.0 * sh * TAU) * 0.3 * exp(-t * 55.0) + n * 0.22 * exp(-t * 45.0)), 2600.0)
		_make("step_wood%d" % v, 0.11, func(t, n): return (sin(t * 120.0 * sh * TAU) * 0.38 + sin(t * 240.0 * sh * TAU) * 0.08 + n * 0.1) * exp(-t * 38.0), 3200.0)
		_make("step_grass%d" % v, 0.13, func(t, n): return (n * 0.2 * exp(-t * 24.0) * (0.6 + 0.4 * sin(t * 160.0 * sh)) + sin(t * 70.0 * TAU) * 0.12 * exp(-t * 50.0)), 1800.0)
		_make("step_gravel%d" % v, 0.12, func(t, n): return (n * 0.3 * exp(-t * 26.0) * (0.5 + 0.5 * absf(sin(t * 700.0 * sh))) + sin(t * 80.0 * TAU) * 0.15 * exp(-t * 50.0)), 5000.0)
		_make("step_water%d" % v, 0.18, func(t, n): return (n * 0.2 + sin(t * (240.0 + 60.0 * v) * TAU) * 0.07) * sin(t / 0.18 * PI), 2200.0)
	_make("dawn", 6.0, func(t, n):
		var env: float = sin(minf(t / 6.0, 1.0) * PI)
		return (sin(t * 110.0 * TAU) * 0.16 + sin(t * 164.8 * TAU) * 0.11 + sin(t * 220.0 * TAU) * 0.07 * (0.5 + 0.5 * sin(t * 0.9))) * env * 0.8)
	_make("night", 8.0, func(t, n):
		var env: float = sin(minf(t / 8.0, 1.0) * PI)
		return (sin(t * 98.0 * TAU) * 0.14 + sin(t * 116.5 * TAU) * 0.1 + sin(t * 146.8 * TAU) * 0.06 * (0.5 + 0.5 * sin(t * 0.6))) * env * 0.7)
	_make("rainsong", 7.0, func(t, n):
		var env2: float = sin(minf(t / 7.0, 1.0) * PI)
		var step: int = int(t * 1.5) % 4
		var f: float = [196.0, 174.6, 164.8, 146.8][step]
		return (sin(t * f * TAU) * 0.12 * exp(-fmod(t, 0.667) * 3.0) + n * 0.02) * env2)
	_make("hearth", 7.0, func(t, n):
		var env3: float = sin(minf(t / 7.0, 1.0) * PI)
		return (sin(t * 130.8 * TAU) * 0.12 + sin(t * 164.8 * TAU) * 0.1 + sin(t * 196.0 * TAU) * 0.08) * env3 * (0.7 + 0.3 * sin(t * 1.3)))
	_make("swing", 0.16, func(t, n): return n * 0.3 * sin(t / 0.16 * PI) * (0.4 + t * 3.0))
	_make("hit", 0.14, func(t, n): return (sin(t * 180.0 * TAU * (1.0 - t * 3.0)) * 0.6 + n * 0.5) * exp(-t * 30.0))
	_make("thump", 0.2, func(t, n): return (sin(t * 70.0 * TAU) * 0.8 + n * 0.25) * exp(-t * 22.0))
	_make("shot", 0.35, func(t, n): return n * 0.95 * exp(-t * 14.0) + sin(t * 90.0 * TAU) * 0.5 * exp(-t * 20.0))
	_make("glass", 0.4, func(t, n): return (sin(t * 3300.0 * TAU) * 0.3 + sin(t * 4700.0 * TAU) * 0.25 + n * 0.5) * exp(-t * 9.0) * (0.6 + 0.4 * sin(t * 90.0)))
	_make("door", 0.22, func(t, n): return (sin(t * (240.0 + sin(t * 40.0) * 60.0) * TAU) * 0.3 + n * 0.12) * sin(t / 0.22 * PI))
	_make("break", 0.3, func(t, n): return (n * 0.7 + sin(t * 110.0 * TAU) * 0.4) * exp(-t * 12.0))
	_make("groan", 0.7, func(t, n): return (sin(t * (95.0 + sin(t * 9.0) * 14.0) * TAU) * 0.45 + sin(t * 190.0 * TAU) * 0.15 + n * 0.08) * sin(t / 0.7 * PI))
	_make("hurt", 0.25, func(t, n): return (sin(t * (300.0 - t * 500.0) * TAU) * 0.5 + n * 0.3) * exp(-t * 12.0))
	_make("pickup", 0.08, func(t, n): return sin(t * 900.0 * TAU) * 0.25 * exp(-t * 40.0))
	_make("eat", 0.18, func(t, n): return n * 0.25 * absf(sin(t * 28.0)) * exp(-t * 8.0))
	_make("build", 0.12, func(t, n): return (sin(t * 520.0 * TAU) * 0.4 + n * 0.4) * exp(-t * 45.0))
	_make("click", 0.04, func(t, n): return n * 0.4 * exp(-t * 120.0))
	_make("alarm", 0.5, func(t, n): return sin(t * (880.0 if fmod(t, 0.25) < 0.125 else 660.0) * TAU) * 0.35)
	_make("levelup", 0.35, func(t, n): return sin(t * (520.0 + floorf(t * 9.0) * 130.0) * TAU) * 0.25 * (1.0 - t / 0.35))
	_make("zdie", 0.4, func(t, n): return (sin(t * (120.0 - t * 150.0) * TAU) * 0.5 + n * 0.3) * exp(-t * 7.0))
	_make("rotor", 1.2, func(t, n): return (n * 0.5 + sin(t * 55.0 * TAU) * 0.4) * (0.35 + 0.65 * pow(absf(sin(t * 11.0 * PI)), 3.0)))
	_make("sneeze", 0.3, func(t, n): return n * 0.6 * exp(-absf(t - 0.12) * 28.0) + sin(t * 420.0 * TAU) * 0.15 * exp(-t * 14.0))
	_make("scream", 0.9, func(t, n): return (sin(t * (760.0 + sin(t * 31.0) * 90.0 - t * 240.0) * TAU) * 0.45 + n * 0.12) * sin(minf(t / 0.9, 1.0) * PI))
	_make("bark", 0.22, func(t, n): return (sin(t * (300.0 - t * 500.0) * TAU) * 0.5 + n * 0.35) * exp(-t * 16.0))

func _build_extra() -> void:
	_into = _extra
	_make_voices()
	_make_beds_streams()
	_into = null

func _extra_ready() -> void:
	for k in _extra.keys():
		_streams[k] = _extra[k]
	_extra.clear()
	_start_beds()

var _into = null                  # where _make puts what it builds (the worker's own dictionary while it runs)
func _make(name: String, dur: float, f: Callable, lowpass_hz: float = 0.0, fades: bool = true) -> void:
	var n: int = int(dur * RATE)
	var data := PackedByteArray()
	data.resize(n * 2)
	var rng := RandomNumberGenerator.new()
	rng.seed = hash(name)
	var a: float = 1.0 - exp(-TAU * lowpass_hz / RATE) if lowpass_hz > 0.0 else 1.0
	var y := 0.0
	var fade_in: int = int(0.003 * RATE)
	var fade_out: int = mini(int(0.012 * RATE), n / 3)
	for i in range(n):
		var t: float = float(i) / RATE
		var x: float = f.call(t, rng.randf_range(-1.0, 1.0))
		y += (x - y) * a
		var g: float = 1.0
		if fades and i < fade_in: g = float(i) / float(fade_in)
		if fades and i > n - fade_out: g = minf(g, float(n - i) / float(fade_out))
		var v: float = clampf(y * g, -1.0, 1.0)
		data.encode_s16(i * 2, int(v * 32000.0))
	var s := AudioStreamWAV.new()
	s.format = AudioStreamWAV.FORMAT_16_BITS
	s.mix_rate = RATE
	s.stereo = false
	s.data = data
	if _into != null:
		_into[name] = s
	else:
		_streams[name] = s

## "Near": your own space (a little room echo indoors); "Muffled": through walls, a floor or a shut door
static func _make_buses() -> void:
	if AudioServer.get_bus_index("Near") >= 0:
		return
	for nm in ["Near", "Muffled"]:
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
		else:
			var lp := AudioEffectLowPassFilter.new()
			lp.cutoff_hz = 900.0
			AudioServer.add_bus_effect(bi, lp)
			AudioServer.set_bus_volume_db(bi, -5.0)

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

func play(name: String, volume_db: float = 0.0, pitch: float = 1.0) -> void:
	if not _streams.has(name):
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
	p.stream = _streams[name]
	p.volume_db = volume_db
	p.pitch_scale = pitch
	p.play()

# ------------------------------------------------------------------ voices of the infected
## a groan is a voice: a buzzing throat (a low wobbling pitch with its harmonics) shaped by an open
## vowel (two formant peaks), with a breathy rasp over it and a swell-and-fade envelope
func _make_voices() -> void:
	for v in range(4):
		var f0: float = [72.0, 88.0, 64.0, 104.0][v]
		var f1: float = [520.0, 640.0, 450.0, 700.0][v]
		var f2: float = [950.0, 1150.0, 860.0, 1250.0][v]
		var dur: float = [1.1, 0.8, 1.3, 0.7][v]
		_make("groan%d" % v, dur, func(t, n):
			var pitch: float = f0 * (1.0 + 0.06 * sin(t * 5.3 + v) + 0.03 * sin(t * 17.0)) * (1.0 - 0.18 * t / dur)
			var s := 0.0
			for h in range(1, 14):
				var fh: float = pitch * h
				var g: float = exp(-pow((fh - f1) / 180.0, 2.0)) + 0.6 * exp(-pow((fh - f2) / 240.0, 2.0)) + 0.25 / h
				s += sin(t * fh * TAU + h * 0.7) * g
			var env: float = sin(minf(t / dur, 1.0) * PI) * (0.75 + 0.25 * sin(t * 9.0))
			return (s * 0.09 + n * 0.08) * env, 3200.0)

# ------------------------------------------------------------------ the world's background
## seamless loops under everything: wind, rain, crickets at night, birds by day, and a low tension
## drone that rises when the infected are close. Each fades toward a level the world sets.
func _make_loop(name: String, dur: float, f: Callable, lowpass_hz: float) -> void:
	_make(name, dur, f, lowpass_hz, false)
	var s: AudioStreamWAV = _into[name] if _into != null else _streams[name]
	# no fades at the ends: the shape repeats exactly, so the join is seamless
	s.loop_mode = AudioStreamWAV.LOOP_FORWARD
	s.loop_begin = 0
	s.loop_end = int(dur * RATE)

func _make_beds_streams() -> void:
	_make_loop("bed_wind", 6.0, func(t, n): return n * 0.5 * (0.6 + 0.4 * sin(t / 6.0 * TAU)) * (0.8 + 0.2 * sin(t / 2.0 * TAU)), 500.0)
	_make_loop("bed_rain", 4.0, func(t, n): return n * 0.45 * (0.85 + 0.15 * sin(t / 1.0 * TAU)), 3800.0)
	_make_loop("bed_crickets", 4.0, func(t, n):
		var chirp: float = 1.0 if fmod(t * 3.0, 1.0) < 0.12 and fmod(t, 2.0) < 1.4 else 0.0
		return sin(t * 4300.0 * TAU) * 0.18 * chirp * (0.6 + 0.4 * sin(t * 90.0 * TAU)) + sin(t * 3900.0 * TAU) * 0.06 * (1.0 if fmod(t * 2.3 + 0.4, 1.0) < 0.1 else 0.0), 0.0)
	_make_loop("bed_birds", 8.0, func(t, n):
		var b := 0.0
		for c in [[0.6, 2600.0], [2.3, 3300.0], [4.1, 2900.0], [6.2, 3600.0]]:
			var dt2: float = t - float(c[0])
			if dt2 > 0.0 and dt2 < 0.35:
				b += sin(t * (float(c[1]) + 900.0 * sin(dt2 * 40.0)) * TAU) * 0.2 * sin(dt2 / 0.35 * PI)
		return b, 0.0)
	_make_loop("bed_tension", 6.0, func(t, n):
		var pulse: float = 0.6 + 0.4 * pow(absf(sin(t / 1.5 * PI)), 4.0)
		return (sin(t * 55.0 * TAU) * 0.22 + sin(t * 58.0 * TAU) * 0.16 + sin(t * 110.0 * TAU) * 0.05 + n * 0.03) * pulse, 900.0)

func _start_beds() -> void:
	for b in ["bed_wind", "bed_rain", "bed_crickets", "bed_birds", "bed_tension"]:
		var p := AudioStreamPlayer.new()
		p.stream = _streams[b]
		p.volume_db = -80.0
		p.bus = "Near"
		add_child(p)
		if p.is_inside_tree(): p.play()
		_beds[b] = p

## the level each bed should sit at, from what the world is doing right now
static func bed_targets(sim: Sim) -> Dictionary:
	var pp: Vector2 = sim.player.pos
	var inside: bool = sim.world.bld(floori(pp.x), floori(pp.y)) != 0 or sim.underground()
	var wind: float = float(sim.weather.get("wind", 0.2))
	var rain: float = float(sim.weather.get("rain", 0.0))
	var light: float = sim.daylight()
	var warm: bool = float(sim.weather.get("temp", 15.0)) > 9.0
	var threat: int = sim.zombies.count_threats(pp, 12.0)
	var t := {}
	t["bed_wind"] = (-34.0 + wind * 22.0) - (12.0 if inside else 0.0)
	t["bed_rain"] = (-60.0 if rain < 0.05 else -26.0 + rain * 18.0) - (10.0 if inside else 0.0)
	t["bed_crickets"] = -24.0 if (light < 0.3 and warm and not inside and rain < 0.3) else -80.0
	t["bed_birds"] = -26.0 if (light > 0.6 and rain < 0.2 and warm and not inside) else -80.0
	t["bed_tension"] = -80.0 if threat == 0 else clampf(-22.0 + float(threat) * 3.0, -22.0, -9.0)
	return t

func _update_beds(sim: Sim) -> void:
	if _beds.is_empty():
		return
	var tg: Dictionary = bed_targets(sim)
	var dt: float = get_process_delta_time()
	for b in _beds.keys():
		var pl: AudioStreamPlayer = _beds[b]
		pl.volume_db = move_toward(pl.volume_db, float(tg[b]), dt * (30.0 if float(tg[b]) > pl.volume_db else 18.0))

## which footstep: the ground under the foot decides
func _step_for(sim: Sim, p: Vector2) -> String:
	match sim.world.ground(floori(p.x), floori(p.y)):
		Defs.G_WOOD, Defs.G_WOOD_DARK, Defs.G_PLANK: return "step_wood"
		Defs.G_GRASS, Defs.G_GRASS_DARK, Defs.G_FOREST, Defs.G_SOIL, Defs.G_DIRT, Defs.G_SAND: return "step_grass"
		Defs.G_GRAVEL: return "step_gravel"
		Defs.G_WATER: return "step_water"
	return "step"

func consume(sim: Sim, view: WorldView) -> void:
	var pp: Vector2 = sim.player.pos
	var steps := 0
	# indoors your own sounds come back off the walls
	var inside: bool = sim.world.bld(floori(pp.x), floori(pp.y)) != 0 or sim.underground()
	_room_wet = move_toward(_room_wet, 0.16 if inside else 0.0, 0.02)
	var nb: int = AudioServer.get_bus_index("Near")
	if nb >= 0:
		(AudioServer.get_bus_effect(nb, 0) as AudioEffectReverb).wet = _room_wet
	for e in sim.fx:
		var k: String = e["k"]
		var d: float = (e["p"] as Vector2).distance_to(pp)
		_bus = bus_for(sim, e["p"])
		var ev_p: Vector2 = e["p"]
		_pos = null if k.begins_with("music_") else Iso.to_screen(ev_p.x, ev_p.y)
		if k.begins_with("meta_"):
			# distant events are heard from far beyond the screen
			var mv: float = -8.0 - d * 0.25
			match k:
				"meta_gunshot": play("shot", mv - 4.0, 0.8)
				"meta_scream": play("scream", mv)
				"meta_dog":
					play("bark", mv)
				"meta_caralarm": play("alarm", mv - 4.0)
				"meta_crash": play("glass", mv)
			continue
		if d > 26.0 and k != "rotor":
			continue
		var vol: float = -d * 0.9
		match k:
			"step":
				steps += 1
				if steps <= 1: play(_step_for(sim, e["p"]) + str(randi() % 3), vol - 8.0 + randf_range(-1.5, 1.0), randf_range(0.92, 1.08))
			"music_dawn": play("dawn", -10.0)
			"music_night": play("night", -11.0)
			"music_rain": play("rainsong", -12.0)
			"music_home": play("hearth", -11.0)
			"swing": play("swing", vol - 4.0, randf_range(0.9, 1.1))
			"hit": play("hit", vol, randf_range(0.85, 1.15))
			"zdie": play("zdie", vol, randf_range(0.85, 1.1))
			"fire":
				if randf() < 0.5: play("fire", vol - 4.0, randf_range(0.8, 1.2))
			"engine": play("engine", vol - 5.0, 0.8 + (absf(sim.vehicle.speed) * 0.08 if sim.vehicle != null else 0.0))
			"call": play("call", vol)
			"thunder": play("thunder", -2.0, randf_range(0.7, 1.0))
			"thump": play("thump", vol + 2.0, randf_range(0.85, 1.1))
			"shot": play("shot", 3.0)
			"glass": play("glass", vol + 2.0)
			"door", "locked": play("door", vol - 3.0, randf_range(0.9, 1.1))
			"break": play("break", vol)
			"groan": play("groan%d" % (randi() % 4), vol - 3.0, randf_range(0.85, 1.12))
			"hurt", "death": play("hurt", 0.0)
			"pickup", "equip", "reload": play("pickup", -6.0)
			"eat": play("eat", -4.0)
			"build": play("build", vol)
			"click": play("click", -4.0)
			"alarm": play("alarm", 0.0)
			"levelup": play("levelup", -4.0)
			"sneeze": play("sneeze", -2.0)
			"rotor":
				_rotor_t -= 1.0
				if _rotor_t <= 0.0:
					_rotor_t = 1.0
					play("rotor", -3.0 - minf(d, 30.0) * 0.3)
	_bus = "Near"
	_pos = null
	_update_beds(sim)
	if sim.alarms.size() > 0:
		_ambient_t -= get_process_delta_time()
		if _ambient_t <= 0.0:
			_ambient_t = 0.5
			var ad: float = (sim.alarms[0][0] as Vector2).distance_to(pp)
			play("alarm", -ad * 0.5)
