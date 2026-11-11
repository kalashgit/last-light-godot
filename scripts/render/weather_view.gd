class_name WeatherView
extends Node2D
## Rain streaks drawn in screen space.

var intensity := 0.0
var _t := 0.0

func _process(dt: float) -> void:
	_t += dt
	if intensity > 0.02:
		queue_redraw()
	elif visible and intensity <= 0.02:
		queue_redraw()

func _draw() -> void:
	if intensity <= 0.02:
		return
	var size: Vector2 = get_viewport_rect().size
	var n: int = int(intensity * 160.0)
	var col := Color(0.72, 0.8, 0.9, 0.34)
	for i in range(n):
		var sp: float = 900.0 + float(i % 7) * 60.0
		var x: float = fposmod(float(Rng.h(i * 7919) % 4096) / 4096.0 * (size.x + 200.0) - _t * 140.0, size.x + 200.0) - 100.0
		var y: float = fposmod(float(Rng.h(i * 104729 + 13) % 4096) / 4096.0 * size.y + _t * sp, size.y + 40.0) - 20.0
		draw_line(Vector2(x, y), Vector2(x - 5.0, y + 22.0), col, 1.0)
