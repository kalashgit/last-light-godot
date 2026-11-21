class_name FxView
extends Node2D
## Transient world-space effects: blood spray, debris, muzzle flashes, floating notes,
## plus the interaction / build highlight.

var parts: Array = []        # [pos, vel, life, max_life, color, size, gravity]
var texts: Array = []        # [pos, text, life, color]
var flashes: Array = []      # [from, to, life]
var hl_tile := Vector2i(-99999, 0)
var hl_edge := -1            # -1 tile, 0 north edge, 1 west edge
var hl_ok := true
var hl_on := false
var flames: Array = []       # Vector2i tiles currently on fire
var arcs: Array = []         # [screen pos, angle, kind, life, max life]
## the shape a swing leaves in the air: sweep (radians), reach (px), thickness, colour alpha
const ARC := {"blunt": [2.3, 30.0, 4.0, 0.55], "blade": [1.5, 28.0, 2.0, 0.75], "axe": [1.9, 32.0, 6.0, 0.6], "spear": [0.0, 40.0, 3.0, 0.7], "shove": [1.2, 18.0, 5.0, 0.35]}

func swing_arc(p: Vector2, screen_dir: Vector2, kind: String, life: float) -> void:
	arcs.append([p, screen_dir.angle(), kind if ARC.has(kind) else "blunt", life, life])

func burst(p: Vector2, n: int, color: Color, speed: float, life: float, size: float = 2.0, up: float = 30.0) -> void:
	for i in range(n):
		var a: float = randf() * TAU
		var v := Vector2(cos(a), sin(a) * 0.5) * randf_range(speed * 0.3, speed) + Vector2(0, -up * randf())
		parts.append([p + Vector2(randf_range(-3, 3), randf_range(-3, 3)), v, life * randf_range(0.6, 1.0), life, color, size, 120.0])
	if parts.size() > 400:
		parts = parts.slice(parts.size() - 400)

func note(p: Vector2, text: String, color: Color) -> void:
	texts.append([p, text, 1.2, color])

func flash_line(a: Vector2, b: Vector2) -> void:
	flashes.append([a, b, 0.07])

func _process(dt: float) -> void:
	for a in arcs.duplicate():
		a[3] = float(a[3]) - dt
		if float(a[3]) <= 0.0:
			arcs.erase(a)
	var busy: bool = parts.size() > 0 or texts.size() > 0 or flashes.size() > 0 or hl_on or flames.size() > 0
	var i: int = parts.size() - 1
	while i >= 0:
		var p: Array = parts[i]
		p[2] = float(p[2]) - dt
		if float(p[2]) <= 0.0:
			parts.remove_at(i)
		else:
			var v: Vector2 = p[1]
			v.y += float(p[6]) * dt
			p[1] = v
			p[0] = (p[0] as Vector2) + v * dt
		i -= 1
	i = texts.size() - 1
	while i >= 0:
		texts[i][2] = float(texts[i][2]) - dt
		texts[i][0] = (texts[i][0] as Vector2) + Vector2(0, -22.0 * dt)
		if float(texts[i][2]) <= 0.0:
			texts.remove_at(i)
		i -= 1
	i = flashes.size() - 1
	while i >= 0:
		flashes[i][2] = float(flashes[i][2]) - dt
		if float(flashes[i][2]) <= 0.0:
			flashes.remove_at(i)
		i -= 1
	if busy:
		queue_redraw()

func _draw() -> void:
	for a in arcs:
		var spec: Array = ARC[a[2]]
		var t: float = 1.0 - float(a[3]) / maxf(float(a[4]), 0.01)
		var col := Color(1, 1, 1, float(spec[3]) * (1.0 - t))
		if float(spec[0]) <= 0.0:
			# a thrust: a straight jab along the facing
			var tip: Vector2 = Vector2(a[0]) + Vector2.from_angle(float(a[1])) * float(spec[1]) * (0.4 + t * 0.6)
			draw_line(Vector2(a[0]), tip, col, float(spec[2]))
		else:
			var half: float = float(spec[0]) * 0.5
			var from: float = float(a[1]) - half
			draw_arc(Vector2(a[0]), float(spec[1]), from, from + float(spec[0]) * (0.25 + t * 0.75), 12, col, float(spec[2]))
	if hl_on:
		var tp: Vector2 = Iso.to_screen(hl_tile.x, hl_tile.y)
		var col := Color(0.6, 1.0, 0.6, 0.9) if hl_ok else Color(1.0, 0.45, 0.4, 0.9)
		if hl_edge < 0:
			Art.world.draw(self, Art.misc["select"], tp, col)
		else:
			var b: Vector2 = tp + (Vector2(32, 16) if hl_edge == 0 else Vector2(-32, 16))
			for k in range(3):
				draw_line(tp + Vector2(0, -k * 20.0), b + Vector2(0, -k * 20.0), col, 2.0)
			draw_line(tp, tp + Vector2(0, -40.0), col, 2.0)
			draw_line(b, b + Vector2(0, -40.0), col, 2.0)
	if flames.size() > 0:
		var ft: float = Time.get_ticks_msec() / 1000.0
		for fk in flames:
			var base: Vector2 = Iso.to_screen(fk.x + 0.5, fk.y + 0.5)
			for j in range(3):
				var ph: float = ft * (7.0 + j * 2.3) + fk.x * 1.7 + fk.y * 2.9 + j * 2.1
				var hgt: float = 26.0 + sin(ph) * 7.0 - j * 6.0
				var wdt: float = 13.0 - j * 3.0
				var ox: float = (j - 1) * 9.0 + sin(ph * 0.7) * 2.0
				var col2: Color = [Color(0.95, 0.32, 0.08, 0.85), Color(1.0, 0.6, 0.12, 0.9), Color(1.0, 0.9, 0.45, 0.9)][j]
				draw_colored_polygon(PackedVector2Array([base + Vector2(ox - wdt, 2), base + Vector2(ox + sin(ph * 1.3) * 4.0, -hgt), base + Vector2(ox + wdt, 2)]), col2)
	for p in parts:
		var a: float = clampf(float(p[2]) / float(p[3]) * 2.0, 0.0, 1.0)
		var c: Color = p[4]
		var s: float = p[5]
		draw_rect(Rect2((p[0] as Vector2) - Vector2(s, s) * 0.5, Vector2(s, s)), Color(c.r, c.g, c.b, c.a * a))
	for f in flashes:
		draw_line(f[0], f[1], Color(1.0, 0.95, 0.7, 0.9), 1.5)
	var font: Font = ThemeDB.fallback_font
	for t in texts:
		var c2: Color = t[3]
		c2.a = clampf(float(t[2]) * 1.5, 0.0, 1.0)
		draw_string(font, (t[0] as Vector2) + Vector2(-40, 0), t[1], HORIZONTAL_ALIGNMENT_CENTER, 80, 11, c2)
