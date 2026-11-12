class_name Sfx
extends Node
## Procedural sound effects: every sample is synthesised into PCM at boot.

const RATE := 22050
var _streams: Dictionary = {}
var _players: Array[AudioStreamPlayer] = []
var _next := 0
var _ambient_t := 0.0
var _rotor_t := 0.0

func _ready() -> void:
	for i in range(10):
		var p := AudioStreamPlayer.new()
		add_child(p)
		_players.append(p)
	_make("step", 0.06, func(t, n): return n * 0.25 * exp(-t * 60.0))
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

func _make(name: String, dur: float, f: Callable) -> void:
	var n: int = int(dur * RATE)
	var data := PackedByteArray()
	data.resize(n * 2)
	var rng := RandomNumberGenerator.new()
	rng.seed = hash(name)
	for i in range(n):
		var t: float = float(i) / RATE
		var v: float = clampf(f.call(t, rng.randf_range(-1.0, 1.0)), -1.0, 1.0)
		data.encode_s16(i * 2, int(v * 32000.0))
	var s := AudioStreamWAV.new()
	s.format = AudioStreamWAV.FORMAT_16_BITS
	s.mix_rate = RATE
	s.stereo = false
	s.data = data
	_streams[name] = s

func play(name: String, volume_db: float = 0.0, pitch: float = 1.0) -> void:
	if not _streams.has(name):
		return
	var p: AudioStreamPlayer = _players[_next]
	_next = (_next + 1) % _players.size()
	p.stream = _streams[name]
	p.volume_db = volume_db
	p.pitch_scale = pitch
	p.play()

func consume(sim: Sim, view: WorldView) -> void:
	var pp: Vector2 = sim.player.pos
	var steps := 0
	for e in sim.fx:
		var k: String = e["k"]
		var d: float = (e["p"] as Vector2).distance_to(pp)
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
				if steps <= 1: play("step", vol - 8.0, randf_range(0.85, 1.15))
			"swing": play("swing", vol - 4.0, randf_range(0.9, 1.1))
			"hit": play("hit", vol, randf_range(0.85, 1.15))
			"zdie": play("zdie", vol, randf_range(0.85, 1.1))
			"thump": play("thump", vol + 2.0, randf_range(0.85, 1.1))
			"shot": play("shot", 3.0)
			"glass": play("glass", vol + 2.0)
			"door", "locked": play("door", vol - 3.0, randf_range(0.9, 1.1))
			"break": play("break", vol)
			"groan": play("groan", vol - 4.0, randf_range(0.75, 1.15))
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
	if sim.alarms.size() > 0:
		_ambient_t -= get_process_delta_time()
		if _ambient_t <= 0.0:
			_ambient_t = 0.5
			var ad: float = (sim.alarms[0][0] as Vector2).distance_to(pp)
			play("alarm", -ad * 0.5)
