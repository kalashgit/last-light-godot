class_name EntityView
extends Node2D
## Draws one character (player or infected) from the layered procedural frames.

const SKIN := [Color("e3bb9c"), Color("cf9f7c"), Color("a06e4c"), Color("f2d2ba")]
const ZSKIN := [Color("9fb092"), Color("93a58a"), Color("7d8f76"), Color("aab89c")]
const SHIRT := [Color("5a7896"), Color("8c4a42"), Color("4f6b4a"), Color("c9c2a8"), Color("3d3f45"), Color("b58a3c"), Color("6a5a80"), Color("9c9c98"), Color("3c6a6e"), Color("a86a4a")]
const PANTS := [Color("3a4458"), Color("4a4238"), Color("2c2e33"), Color("5c6a78"), Color("6a5c44"), Color("38483c")]
const HAIR := [Color("3a2a1c"), Color("1e1a18"), Color("7a5a34"), Color("b0a090"), Color("8a3a24"), Color("c8b070")]

var is_player := false
var ghost := false
var zombie: Zombie = null
var stamp := 0
var frame := PackedInt32Array()
var flip := false
var look: Array = [0, 0, 0, 0]
var weapon_layer := 0
var flash := 0.0
var _key := -1

static func pick(anim: String, t: float, d8: int, progress: float = -1.0) -> Array:
	var dm: Vector2i = ArtChars.dir_map(d8)
	var dirs: Array = Art.char_frames.get(anim, [])
	if dirs.is_empty():
		dirs = Art.char_frames["s_idle"]
	var frames: Array = dirs[dm.x]
	var n: int = frames.size()
	var idx := 0
	if progress >= 0.0:
		idx = clampi(int(progress * n), 0, n - 1)
	else:
		match anim:
			"s_walk": idx = int(t * 11.0) % n
			"z_walk": idx = int(t * 7.0) % n
			"z_idle": idx = int(t * 1.2) % n
			"z_crawl": idx = int(t * 3.0) % n
			"s_work": idx = int(t * 4.0) % n
			"s_squat": idx = int(t * 1.5) % n
			"s_carry": idx = int(t * 8.0) % n
			"s_reload": idx = int(t * 3.0) % n
			"s_vault": idx = int(t * 2.4) % n
			_: idx = clampi(int(t * 9.0), 0, n - 1)
	return [frames[idx], dm.y == 1, idx]

func set_frame(anim: String, t: float, d8: int, progress: float, wl: int, fl: float) -> void:
	var r: Array = pick(anim, t, d8, progress)
	var key: int = hash(anim) * 31 + int(r[2]) * 97 + d8 * 7 + wl + (1000 if fl > 0.0 else 0)
	if key != _key:
		_key = key
		frame = r[0]
		flip = r[1]
		weapon_layer = wl
		flash = fl
		queue_redraw()

func _draw() -> void:
	if frame.is_empty():
		return
	var A: Atlas = Art.chars
	if not ghost:
		Art.world.draw(self, Art.misc["shadow"], Vector2(0, 1))
	var skin: Color = (ZSKIN if zombie != null else SKIN)[int(look[0]) % 4]
	var cols: Array = [skin, SHIRT[int(look[1]) % SHIRT.size()], PANTS[int(look[2]) % PANTS.size()], HAIR[int(look[3]) % HAIR.size()], Color.WHITE]
	if zombie != null:
		match zombie.role:
			"police":
				cols[1] = Color("2c3a5a")
				cols[2] = Color("232a3a")
			"medic":
				cols[1] = Color("8ab8a8")
				cols[2] = Color("8ab8a8")
			"construction":
				cols[1] = Color("d8a020")
				cols[3] = Color("e8c020")
			"military":
				cols[1] = Color("4a5a38")
				cols[2] = Color("4a5034")
			"burned":
				cols[0] = Color("4a3a32")
				cols[1] = Color("2a2420")
				cols[3] = Color("1a1614")
			"soaked":
				cols[0] = (cols[0] as Color).lerp(Color("8aa0a8"), 0.5)
			"decayed":
				cols[0] = (cols[0] as Color).lerp(Color("7a7058"), 0.5)
		cols[1] = (cols[1] as Color).lerp(Color(0.45, 0.45, 0.38), 0.45)
		cols[2] = (cols[2] as Color).lerp(Color(0.35, 0.34, 0.3), 0.4)
	for i in range(5):
		var c: Color = cols[i]
		if flash > 0.0:
			c = c.lerp(Color(1.6, 1.2, 1.1), 0.6)
		if flip:
			A.draw_flipped(self, frame[i], Vector2.ZERO, c)
		else:
			A.draw(self, frame[i], Vector2.ZERO, c)
	if weapon_layer > 0 and frame[4 + weapon_layer] >= 0:
		if flip:
			A.draw_flipped(self, frame[4 + weapon_layer], Vector2.ZERO)
		else:
			A.draw(self, frame[4 + weapon_layer], Vector2.ZERO)
