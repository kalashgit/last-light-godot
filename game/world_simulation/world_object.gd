extends RefCounted
## One placed world-object instance: stable identity, placement and mutable state.
## The archetype (what it *is*) lives in WorldDefs; this is what the instance is *doing*.
##
## Coordinates are tile units (same space as scripts/house.gd: 1.0 = one iso tile).
## - cells objects: `pos` is the top-left corner, `size` the footprint (swapped when rotation is odd).
## - edge objects (doors/windows): `pos` is the midpoint, `size.x` the length, rotation 0 = along +x, 1 = along +y.

var instance_id: String = ""
var definition_id: String = ""
var pos: Vector2 = Vector2.ZERO
var size: Vector2 = Vector2.ONE
var rotation: int = 0
## Optional room tag for room-climate and building metadata (Worker 04 supplies it).
var room: String = ""
## Mutable JSON-safe state. Only bool/float/String/Array/Dictionary values.
var state: Dictionary = {}
## True when created at runtime (not present in the immutable layout).
var spawned: bool = false
var removed: bool = false
var revision: int = 0
## Derived from the definition footprint at creation; not saved.
var is_edge: bool = false


func edge_points() -> Array:
	var half := size.x * 0.5
	var dir := Vector2.RIGHT if rotation % 2 == 0 else Vector2.DOWN
	return [pos - dir * half, pos + dir * half]


func rect() -> Rect2:
	var s := size if rotation % 2 == 0 else Vector2(size.y, size.x)
	return Rect2(pos, s)


func center() -> Vector2:
	return pos if is_edge else rect().get_center()


## Closest point on the footprint to `p`. Used for reach checks.
func closest_point(p: Vector2) -> Vector2:
	if is_edge:
		var e := edge_points()
		return Geometry2D.get_closest_point_to_segment(p, e[0], e[1])
	var r := rect()
	return Vector2(clampf(p.x, r.position.x, r.end.x), clampf(p.y, r.position.y, r.end.y))


## Which side of an edge object a point is on: +1 or -1 (0 when exactly on the line).
func edge_side(p: Vector2) -> int:
	var e := edge_points()
	var d: Vector2 = e[1] - e[0]
	var c := d.cross(p - e[0])
	return 1 if c > 0.0001 else (-1 if c < -0.0001 else 0)


func to_record() -> Dictionary:
	return {
		"def": definition_id,
		"pos": [pos.x, pos.y],
		"size": [size.x, size.y],
		"rot": rotation,
		"room": room,
		"spawned": spawned,
		"state": state.duplicate(true),
	}
