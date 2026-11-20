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
var held_id := ""             # the item in hand, drawn from its sheet sprite when there is one
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

func set_frame(anim: String, t: float, d8: int, progress: float, wl: int, fl: float, held: String = "") -> void:
	var r: Array = pick(anim, t, d8, progress)
	var key: int = hash(anim) * 31 + int(r[2]) * 97 + d8 * 7 + wl + (1000 if fl > 0.0 else 0) + hash(held) * 13
	if key != _key:
		_key = key
		frame = r[0]
		flip = r[1]
		weapon_layer = wl
		flash = fl
		held_id = held
		queue_redraw()

## where the held sprite goes in this frame: [hand position, angle], or [] when the pose puts it away
func held_pose() -> Array:
	var base: int = 5 + ArtChars.WEAPON_KINDS
	if frame.size() < base + 3 or frame[base] == -99999:
		return []
	var hand := Vector2(frame[base] / 16.0 - ArtChars.CX, frame[base + 1] / 16.0 - ArtChars.CY)
	var ang: float = frame[base + 2] / 1000.0
	if flip:
		hand.x = -hand.x
		ang = PI - ang
	return [hand, ang]

## the length a held thing is drawn at, from how far it reaches
static func held_length(id: String) -> float:
	var reach: float = float(Items.def(id).get("wpn", {}).get("range", 1.0))
	return clampf(reach * 16.0 - 6.0, 9.0, 22.0)

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
			"prisoner":
				cols[1] = Color("d8702a")
				cols[2] = Color("c8662a")
			"hazmat":
				cols[1] = Color("d8c83a")
				cols[2] = Color("d8c83a")
				cols[3] = Color("2a2a2a")
		cols[1] = (cols[1] as Color).lerp(Color(0.45, 0.45, 0.38), 0.45)
		cols[2] = (cols[2] as Color).lerp(Color(0.35, 0.34, 0.3), 0.4)
	# the house outline: a dark rim around the whole figure, like the sprite sheets
	if not ghost:
		var ink := Color(0.09, 0.06, 0.045, 0.95)
		for off in [Vector2(-1, 0), Vector2(1, 0), Vector2(0, -1), Vector2(0, 1)]:
			for li in range(4):
				if frame[li] < 0: continue
				if flip:
					A.draw_flipped(self, frame[li], off, ink)
				else:
					A.draw(self, frame[li], off, ink)
	for i in range(5):
		var c: Color = cols[i]
		if flash > 0.0:
			c = c.lerp(Color(1.6, 1.2, 1.1), 0.6)
		if flip:
			A.draw_flipped(self, frame[i], Vector2.ZERO, c)
		else:
			A.draw(self, frame[i], Vector2.ZERO, c)
	var hm: int = int((Art.models.get(held_id, {}) as Dictionary).get("h", -1)) if held_id != "" else -1
	var hpose: Array = held_pose() if hm >= 0 else []
	var hp: Array = held_pose() if hm < 0 and held_id != "" and Art.held.has(held_id) and Art.item_icon.has(held_id) else []
	if not hpose.is_empty():
		# the rendered side view, at true length, gripped at the hand and turned with the arm;
		# facing the other way it is mirrored rather than turned upside down
		var base: int = 5 + ArtChars.WEAPON_KINDS
		var raw: float = frame[base + 2] / 1000.0
		var hk: float = 1.0 / ArtModels.ITEM_K
		if flip:
			draw_set_transform(hpose[0], -raw, Vector2(-hk, hk))
		else:
			draw_set_transform(hpose[0], raw, Vector2(hk, hk))
		var hr: Rect2 = Art.world.rects[hm]
		draw_texture_rect_region(Art.world.texture, Rect2(Art.world.offs[hm], hr.size), hr, Color(1.6, 1.2, 1.1) if flash > 0.0 else Color.WHITE)
		draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)
	elif not hp.is_empty():
		var g: Array = Art.held[held_id]
		var sc: float = held_length(held_id) / maxf(float(g[3]), 1.0)
		draw_set_transform(hp[0], float(hp[1]) - float(g[2]), Vector2(sc, sc))
		var rr: Rect2 = Art.icons.rects[int(Art.item_icon[held_id])]
		draw_texture_rect_region(Art.icons.texture, Rect2(-Vector2(float(g[0]), float(g[1])), rr.size), rr, Color(1.6, 1.2, 1.1) if flash > 0.0 else Color.WHITE)
		draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)
	elif weapon_layer > 0 and frame[4 + weapon_layer] >= 0:
		if flip:
			A.draw_flipped(self, frame[4 + weapon_layer], Vector2.ZERO)
		else:
			A.draw(self, frame[4 + weapon_layer], Vector2.ZERO)
