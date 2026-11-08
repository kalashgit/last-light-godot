extends RefCounted
## State-dependent collision, line of sight and navigation blockers for world objects.
## Pure queries: no state is stored here except the back-reference to the world.
## Worker 03 (zombie AI/nav) consumes: point_blocked, segment_blocked, blocked_nav_cells,
## and the world's `navigation_changed` events / nav_revision counter for cache invalidation.

const EDGE_THICKNESS := 0.09

var world


func _init(w) -> void:
	world = w


func bounds_of(obj) -> Rect2:
	if obj.is_edge:
		var e: Array = obj.edge_points()
		var r := Rect2(e[0], Vector2.ZERO).expand(e[1])
		return r.grow(EDGE_THICKNESS)
	return obj.rect()


func barricade_layers(obj) -> int:
	var b = obj.state.get("barricade", [])
	return b.size() if b is Array else 0


## True when the object physically stops a walking actor in its current state.
func blocks_movement(obj) -> bool:
	if obj.removed:
		return false
	var d: Dictionary = world.def_of(obj)
	if barricade_layers(obj) > 0:
		return true
	match d.get("family", ""):
		"door":
			return not obj.state.get("open", false) and not obj.state.get("broken", false)
		"window":
			# Closed intact glass blocks; open or broken windows can be climbed through.
			return not obj.state.get("open", false) and not obj.state.get("broken", false)
	return not d.get("passable", false)


## 0 = transparent, 0.5 = partial, 1 = opaque.
func sight_block(obj) -> float:
	if obj.removed:
		return 0.0
	var d: Dictionary = world.def_of(obj)
	var layers := barricade_layers(obj)
	var family: String = d.get("family", "")
	if family == "door":
		if obj.state.get("open", false) or obj.state.get("broken", false):
			return minf(1.0, 0.25 * layers)
		return 1.0
	if family == "window":
		return minf(1.0, 0.25 * layers)
	match d.get("sight", "opaque"):
		"transparent": return 0.0
		"partial": return 0.5
	return 1.0


## Movement test for a circle at `p` against static walls and blocking objects.
func point_blocked(p: Vector2, radius: float, ignore_id: String = "") -> bool:
	for w in world.static_walls:
		if Geometry2D.get_closest_point_to_segment(p, w[0], w[1]).distance_to(p) < radius + EDGE_THICKNESS:
			return true
	for id in world.query_rect(Rect2(p - Vector2(radius, radius), Vector2(radius, radius) * 2.0).grow(EDGE_THICKNESS)):
		if id == ignore_id:
			continue
		var obj = world.objects[id]
		if not blocks_movement(obj):
			continue
		if obj.is_edge:
			var e: Array = obj.edge_points()
			if Geometry2D.get_closest_point_to_segment(p, e[0], e[1]).distance_to(p) < radius + EDGE_THICKNESS:
				return true
		elif obj.rect().grow(radius).has_point(p):
			return true
	return false


## Accumulated opacity along a sight line (static walls are fully opaque).
func segment_sight(a: Vector2, b: Vector2) -> float:
	for w in world.static_walls:
		if Geometry2D.segment_intersects_segment(a, b, w[0], w[1]) != null:
			return 1.0
	var total := 0.0
	for id in world.query_rect(Rect2(a, Vector2.ZERO).expand(b).grow(0.1)):
		var obj = world.objects[id]
		var s := sight_block(obj)
		if s <= 0.0:
			continue
		if _segment_hits(obj, a, b):
			total += s
			if total >= 1.0:
				return 1.0
	return total


func segment_blocked_for_sight(a: Vector2, b: Vector2) -> bool:
	return segment_sight(a, b) >= 1.0


func _segment_hits(obj, a: Vector2, b: Vector2) -> bool:
	if obj.is_edge:
		var e: Array = obj.edge_points()
		return Geometry2D.segment_intersects_segment(a, b, e[0], e[1]) != null
	var r: Rect2 = obj.rect()
	if r.has_point(a) or r.has_point(b):
		return true
	var corners := [r.position, Vector2(r.end.x, r.position.y), r.end, Vector2(r.position.x, r.end.y)]
	for i in 4:
		if Geometry2D.segment_intersects_segment(a, b, corners[i], corners[(i + 1) % 4]) != null:
			return true
	return false


## First blocking thing inside `r` (static wall, object footprint or edge), or "" when free.
## Used to validate furniture placement.
func rect_blocker(r: Rect2, ignore_id: String) -> String:
	if not world.bounds.encloses(r):
		return "out_of_bounds"
	var inner := r.grow(-0.01)
	var corners := [inner.position, Vector2(inner.end.x, inner.position.y), inner.end, Vector2(inner.position.x, inner.end.y)]
	for w in world.static_walls:
		if inner.has_point(w[0]) or inner.has_point(w[1]):
			return "wall"
		for i in 4:
			if Geometry2D.segment_intersects_segment(w[0], w[1], corners[i], corners[(i + 1) % 4]) != null:
				return "wall"
	for id in world.query_rect(r):
		if id == ignore_id:
			continue
		var obj = world.objects[id]
		if world.def_of(obj).get("passable", false):
			continue
		if obj.is_edge:
			# Furniture may not sit inside a doorway or window opening, open or closed.
			var e: Array = obj.edge_points()
			if inner.has_point(e[0]) or inner.has_point(e[1]) or inner.has_point((e[0] + e[1]) * 0.5):
				return id
			for i in 4:
				if Geometry2D.segment_intersects_segment(e[0], e[1], corners[i], corners[(i + 1) % 4]) != null:
					return id
		elif obj.rect().intersects(inner):
			return id
	return ""


## Navigation grid helper for Worker 03: cells (of size `cell`) inside `area` that a
## `radius` agent cannot stand in. Rebuild when world.nav_revision changes.
func blocked_nav_cells(area: Rect2, cell: float = 0.5, radius: float = 0.18) -> Array:
	var out := []
	var nx := int(ceil(area.size.x / cell))
	var ny := int(ceil(area.size.y / cell))
	for y in ny:
		for x in nx:
			var p := area.position + Vector2((x + 0.5) * cell, (y + 0.5) * cell)
			if point_blocked(p, radius):
				out.append(Vector2i(x, y))
	return out
