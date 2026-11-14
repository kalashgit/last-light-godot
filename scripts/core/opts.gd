class_name Opts
extends RefCounted
## Device settings (not part of a save): touch target size, text size, stick feel, volume.

const PATH := "user://settings.cfg"
static var btn := 1.0          # touch target scale 0.85 .. 1.2
static var text := 1.0         # HUD text scale 0.9 .. 1.3
static var dead := 0.14        # joystick dead zone 0.06 .. 0.3
static var stick := 1.0        # joystick travel scale (smaller = more sensitive)
static var volume := 1.0       # master volume 0 .. 1
static var vibrate := true     # short buzz when you are hurt or grabbed (phones only)

static func load_all() -> void:
	var c := ConfigFile.new()
	if c.load(PATH) == OK:
		btn = clampf(float(c.get_value("ui", "btn", 1.0)), 0.85, 1.2)
		text = clampf(float(c.get_value("ui", "text", 1.0)), 0.9, 1.3)
		dead = clampf(float(c.get_value("ui", "dead", 0.14)), 0.06, 0.3)
		stick = clampf(float(c.get_value("ui", "stick", 1.0)), 0.7, 1.3)
		volume = clampf(float(c.get_value("audio", "volume", 1.0)), 0.0, 1.0)
		vibrate = bool(c.get_value("ui", "vibrate", true))
	apply()

static func save_all() -> void:
	var c := ConfigFile.new()
	c.set_value("ui", "btn", btn)
	c.set_value("ui", "text", text)
	c.set_value("ui", "dead", dead)
	c.set_value("ui", "stick", stick)
	c.set_value("audio", "volume", volume)
	c.set_value("ui", "vibrate", vibrate)
	c.save(PATH)
	apply()

static func apply() -> void:
	AudioServer.set_bus_mute(0, volume <= 0.01)
	AudioServer.set_bus_volume_db(0, linear_to_db(maxf(volume, 0.01)))

## a short buzz on a phone; nothing on a desktop. returns whether it asked for one
static func buzz(ms: int) -> bool:
	if not vibrate:
		return false
	Input.vibrate_handheld(ms)
	return true

static func cycle(cur: float, steps: Array) -> float:
	for i in range(steps.size()):
		if absf(float(steps[i]) - cur) < 0.005:
			return float(steps[(i + 1) % steps.size()])
	return float(steps[0])
