class_name WeatherView
extends Node2D
## Rain streaks drawn in screen space.

var intensity := 0.0
var flyover := false
var _t := 0.0

func _process(dt: float) -> void:
	_t += dt
	queue_redraw()

func _draw() -> void:
	var size: Vector2 = get_viewport_rect().size
	if flyover:
		# the shadow of the circling aircraft sweeps across the ground
		var ph: float = fposmod(_t * 0.11, 1.0)
		var cx: float = lerpf(-200.0, size.x + 200.0, ph)
		var cy: float = size.y * (0.35 + 0.25 * sin(_t * 0.23))
		var pts := PackedVector2Array()
		for k in range(20):
			var a: float = k / 20.0 * TAU
			pts.append(Vector2(cx + cos(a) * 70.0, cy + sin(a) * 18.0))
		draw_colored_polygon(pts, Color(0, 0, 0, 0.3))
		var rot: float = _t * 21.0
		draw_line(Vector2(cx, cy) + Vector2(cos(rot), sin(rot) * 0.3) * 120.0, Vector2(cx, cy) - Vector2(cos(rot), sin(rot) * 0.3) * 120.0, Color(0, 0, 0, 0.22), 5.0)
		draw_line(Vector2(cx + 60, cy), Vector2(cx + 150, cy - 6), Color(0, 0, 0, 0.3), 9.0)
	if intensity <= 0.02:
		return
	var n: int = int(intensity * 160.0)
	var col := Color(0.72, 0.8, 0.9, 0.34)
	for i in range(n):
		var sp: float = 900.0 + float(i % 7) * 60.0
		var x: float = fposmod(float(Rng.h(i * 7919) % 4096) / 4096.0 * (size.x + 200.0) - _t * 140.0, size.x + 200.0) - 100.0
		var y: float = fposmod(float(Rng.h(i * 104729 + 13) % 4096) / 4096.0 * size.y + _t * sp, size.y + 40.0) - 20.0
		draw_line(Vector2(x, y), Vector2(x - 5.0, y + 22.0), col, 1.0)
