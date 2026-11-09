extends "res://scripts/house_navigation.gd"
## Same 0.4-unit A* grid and breach semantics as the single-house game, sized to
## the generated world bounds instead of the fixed house region.

var build_msec := 0

func rebuild(game) -> void:
 var started := Time.get_ticks_msec()
 var r: Rect2 = game.world_rect
 var x0 := floori(r.position.x / STEP)
 var y0 := floori(r.position.y / STEP)
 var x1 := ceili(r.end.x / STEP)
 var y1 := ceili(r.end.y / STEP)
 grid.region = Rect2i(x0, y0, x1 - x0 + 1, y1 - y0 + 1)
 grid.cell_size = Vector2.ONE * STEP
 grid.diagonal_mode = AStarGrid2D.DIAGONAL_MODE_NEVER
 grid.update()
 for y in range(y0, y1 + 1):
  for x in range(x0, x1 + 1):
   grid.set_point_solid(Vector2i(x, y), game._blocked_static(Vector2(x, y) * STEP, .21))
 paths.clear(); timers.clear()
 build_msec = Time.get_ticks_msec() - started

func cell_of(point: Vector2) -> Vector2i:
 return _free_cell(point)

func path_between(a: Vector2, b: Vector2) -> Array:
 var ca := _free_cell(a)
 var cb := _free_cell(b)
 if not grid.is_in_boundsv(ca) or not grid.is_in_boundsv(cb): return []
 var out: Array = []
 for p in grid.get_id_path(ca, cb): out.append(Vector2(p) * STEP)
 return out
