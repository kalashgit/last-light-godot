extends RefCounted
## Presentation-only draw-call batcher for flat-colored world geometry (W08).
##
## House walls, doors and the roof are made of many small quads and antialiased
## lines. Godot's GL Compatibility renderer starts a new batch every time the
## command type switches (polygon -> line -> polygon ...), so one wall segment cost
## several draw calls. This object duck-types the drawing calls house_art.gd uses,
## appends everything as vertex-colored triangles in painter's order and submits
## one triangle array per flush. Callers flush before any texture or actor is
## drawn, so depth/Y-sort order is exactly preserved.
##
## Gameplay coordinates, projection and collision are untouched: _screen() is
## forwarded to the owning game node.

## Width of the alpha fade on antialiased lines, in canvas units. Matches the
## ~1 px feather Godot adds for draw_line(..., antialiased = true).
const FEATHER := 1.0
const TRANSPARENT := Color(0, 0, 0, 0)

var game: CanvasItem
var points := PackedVector2Array()
var colors := PackedColorArray()
var indices := PackedInt32Array()
## Statistics for the profiler and tests.
var flushes := 0
var triangles_submitted := 0


## Read-only forward used by house_art._furniture for the search-marker distance.
var player: Vector2:
	get:
		return game.player


func _init(owner: CanvasItem) -> void:
	game = owner


func _screen(p: Vector2, height: float = 0.0) -> Vector2:
	return game._screen(p, height)


func get_viewport_rect() -> Rect2:
	return game.get_viewport_rect()


func pending_triangles() -> int:
	return indices.size() / 3


func _vertex(p: Vector2, color: Color) -> int:
	points.append(p)
	colors.append(color)
	return points.size() - 1


func _triangle_indices(a: int, b: int, c: int) -> void:
	indices.append(a)
	indices.append(b)
	indices.append(c)


func _quad_colored(a: Vector2, b: Vector2, c: Vector2, d: Vector2, ca: Color, cb: Color, cc: Color, cd: Color) -> void:
	var ia := _vertex(a, ca)
	var ib := _vertex(b, cb)
	var ic := _vertex(c, cc)
	var id := _vertex(d, cd)
	_triangle_indices(ia, ib, ic)
	_triangle_indices(ia, ic, id)


func _quad(a: Vector2, b: Vector2, c: Vector2, d: Vector2, color: Color) -> void:
	_quad_colored(a, b, c, d, color, color, color, color)


func _poly(polygon: PackedVector2Array, color: Color) -> void:
	draw_colored_polygon(polygon, color)


func draw_colored_polygon(polygon: PackedVector2Array, color: Color) -> void:
	if polygon.size() < 3:
		return
	var local := Geometry2D.triangulate_polygon(polygon)
	if local.is_empty():
		return
	var base := points.size()
	for p in polygon:
		_vertex(p, color)
	for index in local:
		indices.append(base + index)


func draw_line(a: Vector2, b: Vector2, color: Color, width: float = 1.0, antialiased: bool = false) -> void:
	var direction := b - a
	if direction.length_squared() < 0.000001:
		return
	var normal := direction.orthogonal().normalized()
	var half := normal * maxf(width, 0.5) * 0.5
	_quad(a + half, b + half, b - half, a - half, color)
	if antialiased:
		var edge := Color(color, 0.0)
		var feather := normal * FEATHER
		_quad_colored(a + half, b + half, b + half + feather, a + half + feather, color, color, edge, edge)
		_quad_colored(a - half, b - half, b - half - feather, a - half - feather, color, color, edge, edge)


func draw_circle(center: Vector2, radius: float, color: Color, _filled: bool = true, _width: float = -1.0, _antialiased: bool = false) -> void:
	var segments := clampi(int(radius * 2.0) + 8, 8, 24)
	var c := _vertex(center, color)
	var first := points.size()
	for i in range(segments):
		var angle := TAU * float(i) / float(segments)
		_vertex(center + Vector2(cos(angle), sin(angle)) * radius, color)
	for i in range(segments):
		_triangle_indices(c, first + i, first + (i + 1) % segments)


# Texture and mesh commands cannot join a vertex-colored batch. Flush first so the
# painter's order is kept, then forward to the real canvas item.
func draw_texture_rect(texture: Texture2D, rect: Rect2, tile: bool, modulate: Color = Color.WHITE, transpose: bool = false) -> void:
	flush()
	game.draw_texture_rect(texture, rect, tile, modulate, transpose)


func draw_texture(texture: Texture2D, position: Vector2, modulate: Color = Color.WHITE) -> void:
	flush()
	game.draw_texture(texture, position, modulate)


func draw_mesh(mesh: Mesh, texture: Texture2D, transform: Transform2D = Transform2D(), modulate: Color = Color.WHITE) -> void:
	flush()
	game.draw_mesh(mesh, texture, transform, modulate)


func draw_rect(rect: Rect2, color: Color, filled: bool = true, width: float = -1.0, antialiased: bool = false) -> void:
	if filled:
		_quad(rect.position, Vector2(rect.end.x, rect.position.y), rect.end, Vector2(rect.position.x, rect.end.y), color)
	else:
		flush()
		game.draw_rect(rect, color, false, width, antialiased)


## Submit pending geometry to the owner's canvas item. Must be called from inside
## the owner's _draw(), so the active draw_set_transform (camera zoom) applies.
func flush() -> void:
	if indices.is_empty():
		return
	RenderingServer.canvas_item_add_triangle_array(game.get_canvas_item(), indices, points, colors)
	flushes += 1
	triangles_submitted += indices.size() / 3
	points = PackedVector2Array()
	colors = PackedColorArray()
	indices = PackedInt32Array()


func reset_stats() -> void:
	flushes = 0
	triangles_submitted = 0
