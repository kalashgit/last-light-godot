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
	var busy: bool = parts.size() > 0 or texts.size() > 0 or flashes.size() > 0 or hl_on
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
