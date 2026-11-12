class_name ArtIcons
extends RefCounted
## Item icons, status (moodle) icons and HUD glyphs — all painted procedurally.

const S := 24

static func queue_jobs(jobs: Array[Callable]) -> void:
	var ids: Array = Items.DB.keys()
	var i := 0
	while i < ids.size():
		var chunk: Array = ids.slice(i, i + 16)
		jobs.append(func():
			for id in chunk:
				var d: Dictionary = Items.DB[id]
				var ic: Array = d["icon"]
				var p: Painter = _icon(ic[0], Color(ic[1]), Color(ic[2]))
				p.outline(Color(0.05, 0.05, 0.05, 0.85))
				Art.item_icon[id] = Art.icons.add(p.img, 0, 0, "", false))
		i += 16
	jobs.append(_gen_moodles)

static func _icon(shape: String, a: Color, b: Color) -> Painter:
	var p := Painter.new(S, S)
	var da: Color = a.darkened(0.25)
	match shape:
		"can":
			p.rect(7, 5, 10, 15, a)
			p.rect(7, 10, 10, 5, b)
			p.rect(7, 5, 10, 1, Color(0.8, 0.8, 0.8))
			p.rect(7, 19, 10, 1, Color(0.6, 0.6, 0.6))
			p.rect(15, 6, 2, 13, da)
		"bottle":
			p.rect(10, 3, 4, 4, b)
			p.rect(8, 7, 8, 14, a)
			p.rect(8, 12, 8, 4, b)
			p.rect(14, 8, 2, 12, da)
		"box":
			p.rect(6, 5, 12, 16, a)
			p.rect(8, 8, 8, 6, b)
			p.rect(16, 5, 2, 16, da)
		"bag":
			p.rect(7, 6, 10, 15, a)
			p.rect(7, 4, 10, 2, da)
			p.rect(9, 10, 6, 6, b)
		"jar":
			p.rect(8, 4, 8, 3, b)
			p.rect(7, 7, 10, 14, a)
			p.rect(15, 8, 2, 12, da)
		"fruit":
			p.ball(12, 13, 7, 7, a, 3, 0.05)
			p.rect(12, 4, 1, 3, Color(0.3, 0.2, 0.1))
			p.rect(13, 4, 3, 2, b)
		"veg":
			p.ball(12, 13, 8, 7, a, 4, 0.1)
			p.ball(10, 11, 4, 3, b, 5, 0.05)
		"carrot":
			p.poly(PackedVector2Array([Vector2(7, 8), Vector2(13, 6), Vector2(19, 21)]), a)
			p.line(8, 7, 5, 3, b)
			p.line(10, 6, 9, 2, b)
			p.line(11, 6, 13, 2, b)
		"berries":
			p.ball(9, 14, 4, 4, a, 6, 0.05)
			p.ball(15, 15, 4, 4, a, 7, 0.05)
			p.ball(12, 9, 4, 4, a, 8, 0.05)
			p.rect(12, 3, 2, 3, b)
		"mushroom":
			p.rect(10, 12, 4, 8, a)
			p.poly(PackedVector2Array([Vector2(4, 13), Vector2(12, 4), Vector2(20, 13)]), b)
		"egg":
			p.ball(12, 13, 6, 8, a, 9, 0.03)
			p.ball(12, 14, 3, 3, b, 10, 0.03)
		"meat":
			p.ball(12, 12, 9, 6, a, 11, 0.1)
			p.ball(9, 11, 3, 2, b, 12, 0.05)
			p.rect(18, 13, 4, 2, Color(0.92, 0.9, 0.85))
		"fish":
			p.ball(11, 12, 8, 4, a, 13, 0.1)
			p.poly(PackedVector2Array([Vector2(17, 12), Vector2(22, 7), Vector2(22, 17)]), b)
			p.put(6, 11, Color.BLACK)
		"bread":
			p.ball(12, 12, 9, 6, a, 14, 0.08)
			p.line(8, 9, 10, 13, b)
			p.line(12, 8, 14, 12, b)
			p.line(16, 9, 17, 12, b)
		"bar":
			p.rect(4, 9, 16, 7, a)
			p.rect(4, 9, 6, 7, b)
			p.rect(4, 15, 16, 1, da)
		"pot":
			p.rect(5, 9, 14, 10, a)
			p.rect(5, 8, 14, 2, b)
			p.rect(2, 11, 3, 2, a)
			p.rect(19, 11, 3, 2, a)
		"pills":
			p.rect(8, 8, 8, 12, a)
			p.rect(7, 5, 10, 3, b)
			p.rect(8, 12, 8, 4, b)
		"bandage":
			p.ball(12, 12, 7, 7, a, 15, 0.03)
			p.ball(12, 12, 3, 3, b, 16, 0.02)
			p.rect(17, 12, 4, 7, a)
		"rag":
			p.poly(PackedVector2Array([Vector2(4, 7), Vector2(19, 5), Vector2(21, 17), Vector2(13, 19), Vector2(6, 16)]), a)
			p.line(7, 9, 17, 14, b)
		"kit":
			p.rect(4, 7, 16, 12, a)
			p.rect(9, 5, 6, 2, da)
			p.rect(11, 9, 2, 8, b)
			p.rect(8, 12, 8, 2, b)
		"needle":
			p.line(5, 19, 19, 5, a)
			p.line(19, 5, 15, 12, b)
			p.line(15, 12, 9, 10, b)
		"knife":
			p.poly(PackedVector2Array([Vector2(10, 3), Vector2(14, 5), Vector2(13, 14), Vector2(10, 14)]), a)
			p.rect(10, 14, 4, 7, b)
		"machete":
			p.poly(PackedVector2Array([Vector2(9, 1), Vector2(15, 3), Vector2(14, 16), Vector2(10, 16)]), a)
			p.rect(10, 16, 4, 6, b)
		"bat":
			p.line(5, 20, 17, 6, a, 3)
			p.line(15, 8, 19, 4, b, 4)
		"crowbar":
			p.line(6, 20, 16, 5, a, 2)
			p.line(16, 5, 20, 7, b, 2)
		"pipe":
			p.line(5, 20, 18, 5, a, 3)
			p.line(17, 6, 19, 4, b, 3)
		"pan":
			p.ball(14, 9, 7, 6, a, 17, 0.04)
			p.ball(14, 9, 4, 3, b, 18, 0.03)
			p.line(9, 14, 4, 20, a, 2)
		"hammer":
			p.line(7, 20, 14, 8, a, 2)
			p.rect(10, 4, 10, 5, b)
		"axe":
			p.line(7, 21, 15, 5, a, 2)
			p.poly(PackedVector2Array([Vector2(13, 3), Vector2(21, 5), Vector2(20, 12), Vector2(15, 9)]), b)
		"shovel":
			p.line(6, 21, 15, 9, a, 2)
			p.poly(PackedVector2Array([Vector2(13, 6), Vector2(18, 2), Vector2(21, 7), Vector2(17, 11)]), b)
		"spear":
			p.line(4, 21, 18, 5, a, 2)
			p.poly(PackedVector2Array([Vector2(16, 5), Vector2(22, 1), Vector2(19, 8)]), b)
		"screwdriver":
			p.line(6, 19, 11, 13, a, 3)
			p.line(12, 12, 19, 5, b)
		"wrench":
			p.line(6, 19, 16, 8, a, 2)
			p.rect(14, 4, 6, 6, b)
			p.rect(16, 4, 2, 3, Color(0, 0, 0, 0))
		"pistol":
			p.rect(4, 8, 15, 4, a)
			p.rect(13, 12, 4, 8, b)
			p.rect(4, 7, 2, 1, b)
		"shotgun":
			p.line(2, 14, 21, 8, a, 2)
			p.line(2, 15, 9, 13, b, 3)
		"rifle":
			p.line(1, 15, 22, 7, b, 2)
			p.line(1, 16, 8, 14, a, 3)
		"ammo":
			for k in range(3):
				p.rect(6 + k * 5, 8, 3, 11, a)
				p.rect(6 + k * 5, 5, 3, 3, b)
		"saw":
			p.poly(PackedVector2Array([Vector2(3, 8), Vector2(17, 8), Vector2(17, 15), Vector2(3, 11)]), a)
			p.rect(16, 6, 6, 11, b)
		"opener":
			p.line(5, 18, 14, 8, a, 2)
			p.ball(16, 7, 4, 4, b, 19, 0.03)
		"lighter":
			p.rect(9, 9, 6, 11, a)
			p.rect(9, 6, 6, 3, b)
			p.rect(11, 3, 2, 3, Color(1.0, 0.7, 0.2))
		"flashlight":
			p.rect(4, 10, 11, 5, b)
			p.poly(PackedVector2Array([Vector2(15, 9), Vector2(20, 6), Vector2(20, 19), Vector2(15, 16)]), a)
		"battery":
			p.rect(8, 7, 8, 13, a)
			p.rect(8, 7, 8, 4, b)
			p.rect(10, 5, 4, 2, Color(0.7, 0.7, 0.7))
		"candle":
			p.rect(10, 9, 4, 12, a)
			p.ball(12, 6, 2, 3, b, 20, 0.02)
		"trowel":
			p.line(6, 20, 11, 13, a, 2)
			p.poly(PackedVector2Array([Vector2(10, 12), Vector2(15, 4), Vector2(19, 6), Vector2(14, 14)]), b)
		"wcan":
			p.rect(7, 9, 10, 11, a)
			p.line(17, 13, 22, 7, b, 2)
			p.line(7, 11, 3, 14, b)
			p.line(3, 14, 7, 17, b)
		"rod":
			p.line(3, 21, 20, 3, a)
			p.line(20, 3, 20, 14, b)
			p.rect(7, 15, 3, 3, b)
		"gascan":
			p.rect(6, 7, 13, 14, a)
			p.rect(14, 4, 4, 3, b)
			p.line(8, 10, 16, 18, b)
			p.line(16, 10, 8, 18, b)
		"scissors":
			p.line(6, 4, 14, 14, a)
			p.line(17, 4, 9, 14, a)
			p.ball(8, 17, 3, 3, b, 21, 0.02)
			p.ball(15, 17, 3, 3, b, 22, 0.02)
		"radio":
			p.rect(4, 8, 16, 11, a)
			p.ball(9, 14, 3, 3, b, 23, 0.02)
			p.line(17, 8, 20, 2, b)
			p.rect(13, 11, 5, 2, b)
		"generator":
			p.rect(4, 8, 16, 11, a)
			p.rect(6, 10, 6, 5, b)
			p.rect(5, 19, 3, 2, b)
			p.rect(16, 19, 3, 2, b)
		"nails":
			for k in range(4):
				p.line(6 + k * 4, 6 + (k % 2) * 2, 5 + k * 4, 19, a)
				p.rect(5 + k * 4, 5 + (k % 2) * 2, 3, 1, b)
		"plank":
			p.poly(PackedVector2Array([Vector2(3, 16), Vector2(18, 4), Vector2(21, 8), Vector2(6, 20)]), a)
			p.line(5, 17, 19, 6, b)
		"log":
			p.poly(PackedVector2Array([Vector2(3, 14), Vector2(16, 5), Vector2(20, 11), Vector2(7, 20)]), a)
			p.ball(18, 8, 3, 4, b, 24, 0.03)
		"stick":
			p.line(4, 20, 20, 5, a, 2)
			p.line(12, 12, 16, 14, b)
		"stone":
			p.ball(12, 13, 8, 6, a, 25, 0.1)
			p.ball(9, 11, 3, 2, a.lightened(0.15), 26, 0.05)
		"metal":
			p.poly(PackedVector2Array([Vector2(4, 8), Vector2(18, 5), Vector2(21, 15), Vector2(9, 19)]), a)
			p.line(6, 10, 18, 14, b)
		"wire":
			p.ball(12, 12, 8, 8, a, 27, 0.04)
			p.ball(12, 12, 5, 5, Color(0, 0, 0, 0), 0, 0)
			p.ellipse(12, 12, 4.5, 4.5, b)
			p.ellipse(12, 12, 2.5, 2.5, a)
		"tape":
			p.ball(12, 12, 8, 8, a, 28, 0.03)
			p.ellipse(12, 12, 3.5, 3.5, b)
		"rope":
			p.ball(12, 13, 8, 6, a, 29, 0.14)
			p.ellipse(12, 13, 3, 2, b)
			p.line(18, 9, 21, 4, a, 2)
		"sheet":
			p.rect(4, 7, 16, 11, a)
			p.rect(4, 11, 16, 1, b)
			p.rect(4, 15, 16, 1, b)
			p.rect(18, 7, 2, 11, b)
		"paper":
			p.rect(6, 4, 12, 16, a)
			for k in range(5):
				p.rect(8, 7 + k * 2, 8, 1, b)
		"pack":
			p.rect(6, 7, 12, 14, a)
			p.rect(8, 12, 8, 6, b)
			p.rect(9, 4, 6, 3, b)
			p.rect(16, 8, 2, 12, a.darkened(0.3))
		"jacket":
			p.poly(PackedVector2Array([Vector2(8, 4), Vector2(16, 4), Vector2(22, 9), Vector2(19, 13), Vector2(17, 11), Vector2(17, 21), Vector2(7, 21), Vector2(7, 11), Vector2(5, 13), Vector2(2, 9)]), a)
			p.rect(12, 5, 1, 16, b)
		"seeds":
			p.rect(7, 5, 10, 15, b)
			p.ball(12, 12, 3, 4, a, 30, 0.05)
			p.rect(7, 5, 10, 2, a)
		"book":
			p.rect(6, 4, 12, 16, a)
			p.rect(6, 4, 2, 16, a.darkened(0.3))
			p.rect(10, 7, 6, 3, b)
		"toy":
			p.ball(12, 14, 6, 6, a, 31, 0.05)
			p.ball(12, 7, 4, 4, a, 32, 0.05)
			p.ball(8, 4, 2, 2, a, 33, 0.05)
			p.ball(16, 4, 2, 2, a, 34, 0.05)
			p.ball(12, 15, 3, 3, b, 35, 0.03)
		_:
			p.rect(6, 6, 12, 12, a)
	return p

## moodle pictograms (white glyph, tinted by severity colour in HUD)
static func _gen_moodles() -> void:
	var w := Color.WHITE
	var names := ["hungry", "thirsty", "tired", "panic", "pain", "bleeding", "sick", "cold", "hot", "wet", "heavy", "injured", "infected", "exhausted", "stuffed", "bored", "sad", "stress", "drunk"]
	for nm in names:
		var p := Painter.new(S, S)
		match nm:
			"hungry":
				p.rect(6, 4, 1, 8, w); p.rect(8, 4, 1, 8, w); p.rect(10, 4, 1, 8, w); p.rect(7, 11, 3, 2, w); p.rect(8, 12, 1, 9, w)
				p.ellipse(16, 8, 2.5, 4.5, w); p.rect(16, 11, 1, 10, w)
			"thirsty":
				p.poly(PackedVector2Array([Vector2(12, 3), Vector2(18, 14), Vector2(6, 14)]), w)
				p.ellipse(12, 15, 6, 5.5, w)
			"tired":
				p.line(5, 6, 11, 6, w); p.line(11, 6, 5, 12, w); p.line(5, 12, 11, 12, w)
				p.line(13, 12, 19, 12, w); p.line(19, 12, 13, 19, w); p.line(13, 19, 19, 19, w)
			"panic":
				p.rect(10, 3, 4, 12, w); p.rect(10, 17, 4, 4, w)
			"pain":
				p.poly(PackedVector2Array([Vector2(13, 2), Vector2(6, 13), Vector2(11, 13), Vector2(9, 22), Vector2(18, 10), Vector2(13, 10), Vector2(16, 2)]), w)
			"bleeding":
				p.poly(PackedVector2Array([Vector2(8, 3), Vector2(12, 10), Vector2(4, 10)]), w); p.ellipse(8, 11, 4, 3.5, w)
				p.poly(PackedVector2Array([Vector2(16, 10), Vector2(20, 17), Vector2(12, 17)]), w); p.ellipse(16, 18, 4, 3.5, w)
			"sick":
				p.ellipse(12, 12, 9, 9, w); p.ellipse(12, 12, 7, 7, Color(1, 1, 1, 0.25))
				p.rect(8, 9, 2, 2, w); p.rect(14, 9, 2, 2, w); p.line(8, 17, 10, 15, w); p.line(10, 15, 12, 17, w); p.line(12, 17, 14, 15, w); p.line(14, 15, 16, 17, w)
			"cold":
				p.line(12, 3, 12, 21, w); p.line(4, 7, 20, 17, w); p.line(4, 17, 20, 7, w)
				p.line(10, 5, 12, 7, w); p.line(14, 5, 12, 7, w); p.line(10, 19, 12, 17, w); p.line(14, 19, 12, 17, w)
			"hot":
				p.ellipse(12, 12, 5, 5, w)
				for k in range(8):
					var a: float = k / 8.0 * TAU
					p.line(12 + cos(a) * 7.0, 12 + sin(a) * 7.0, 12 + cos(a) * 10.0, 12 + sin(a) * 10.0, w)
			"wet":
				for k in range(3):
					p.line(6 + k * 6, 4 + k * 2, 4 + k * 6, 10 + k * 2, w, 2)
					p.line(8 + k * 5, 13, 6 + k * 5, 19, w, 2)
			"heavy":
				p.poly(PackedVector2Array([Vector2(7, 9), Vector2(17, 9), Vector2(21, 21), Vector2(3, 21)]), w)
				p.ellipse(12, 6, 3, 3, w)
			"injured":
				p.rect(9, 3, 6, 18, w); p.rect(3, 9, 18, 6, w)
			"infected":
				p.ellipse(12, 8, 4, 4, w); p.ellipse(7, 16, 4, 4, w); p.ellipse(17, 16, 4, 4, w); p.ellipse(12, 13, 2.5, 2.5, w)
			"exhausted":
				p.ellipse(8, 9, 5, 6, w); p.ellipse(16, 9, 5, 6, w)
				p.poly(PackedVector2Array([Vector2(3, 10), Vector2(21, 10), Vector2(12, 22)]), w)
				p.line(12, 6, 10, 11, Color(1, 1, 1, 0.2), 2); p.line(10, 11, 14, 13, Color(1, 1, 1, 0.2), 2); p.line(14, 13, 12, 18, Color(1, 1, 1, 0.2), 2)
			"stuffed":
				p.ellipse(12, 13, 8, 7, w); p.rect(11, 3, 2, 4, w)
			"sad":
				p.ellipse(12, 12, 9, 9, w)
				p.rect(7, 8, 3, 3, Color(1, 1, 1, 0.2)); p.rect(14, 8, 3, 3, Color(1, 1, 1, 0.2))
				p.line(8, 18, 12, 15, Color(1, 1, 1, 0.2), 2); p.line(12, 15, 16, 18, Color(1, 1, 1, 0.2), 2)
			"stress":
				p.line(4, 6, 9, 11, w, 2); p.line(9, 11, 5, 15, w, 2); p.line(5, 15, 10, 20, w, 2)
				p.line(13, 4, 18, 9, w, 2); p.line(18, 9, 14, 13, w, 2); p.line(14, 13, 19, 18, w, 2)
			"drunk":
				p.rect(9, 3, 4, 5, w); p.rect(7, 8, 8, 13, w); p.rect(15, 11, 4, 2, w); p.rect(18, 11, 2, 7, w); p.rect(15, 16, 4, 2, w)
			"bored":
				p.ellipse(12, 12, 9, 9, w); p.rect(7, 9, 3, 1, Color(1, 1, 1, 0.2)); p.rect(14, 9, 3, 1, Color(1, 1, 1, 0.2)); p.rect(8, 16, 8, 1, Color(1, 1, 1, 0.2))
		Art.misc["m_" + nm] = Art.icons.add(p.img, 0, 0, "", false)
