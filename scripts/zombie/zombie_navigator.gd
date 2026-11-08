extends RefCounted
## Zombie path following on the shared map grid (Worker 03).
## Uses the host world's AStarGrid2D and coordinate system unchanged (house.gd: 0.4 m cells,
## world metres, closed doors are passable route candidates so blocked zombies can breach).
## Paths are cached per agent and only recomputed when the goal moves to another cell
## (rate-limited), when a path is exhausted, or when the agent is stuck.

const REPLAN_MIN := .35     # s between goal-change replans
const REPLAN_MAX := 2.5     # s before a cached path is refreshed anyway
const WAYPOINT_REACHED := .23
const DIRECT_RANGE := 1.1   # straight-line steering below this distance

var world
var paths_computed := 0
var direct_checks := 0


func setup(host_world) -> void:
	world = host_world


func _grid() -> AStarGrid2D:
	return world.zw_nav_grid()


func _step() -> float:
	return world.zw_nav_step()


func _cell(p: Vector2) -> Vector2i:
	var s := _step()
	return Vector2i(roundi(p.x / s), roundi(p.y / s))


func _free_cell(p: Vector2) -> Vector2i:
	var grid := _grid()
	var cell := _cell(p)
	for radius in range(5):
		for y in range(-radius, radius + 1):
			for x in range(-radius, radius + 1):
				var c := cell + Vector2i(x, y)
				if grid.is_in_boundsv(c) and not grid.is_point_solid(c):
					return c
	return Vector2i(-99999, -99999)


func reachable(p: Vector2) -> bool:
	var grid := _grid()
	var c := _cell(p)
	return grid.is_in_boundsv(c) and not grid.is_point_solid(c)


func _straight_clear(a: Vector2, b: Vector2, radius: float) -> bool:
	direct_checks += 1
	var d := a.distance_to(b)
	var n := maxi(1, ceili(d / .25))
	for i in range(1, n + 1):
		if world.zw_blocked_static(a.lerp(b, float(i) / n), radius):
			return false
	return true


func clear(nav: Dictionary) -> void:
	nav.path = []
	nav.goal_cell = Vector2i(-99999, -99999)
	nav.timer = 0.0
	nav.direct = false


## nav is the agent's transient navigation record (never saved).
func direction(nav: Dictionary, from: Vector2, goal: Vector2, radius: float, dt: float, force: bool = false) -> Vector2:
	nav.timer = float(nav.get("timer", 0.0)) - dt
	var goal_cell := _cell(goal)
	var path: Array = nav.get("path", [])
	var changed: bool = goal_cell != nav.get("goal_cell", Vector2i(-99999, -99999))
	var need := force or not nav.has("path") or float(nav.timer) <= -REPLAN_MAX + REPLAN_MIN
	if changed and float(nav.timer) <= 0.0:
		need = true
	if path.is_empty() and not bool(nav.get("direct", false)) and float(nav.timer) <= 0.0:
		need = true
	if need:
		nav.goal_cell = goal_cell
		nav.timer = REPLAN_MIN
		if from.distance_to(goal) < DIRECT_RANGE or _straight_clear(from, goal, radius):
			nav.direct = true
			nav.path = []
		else:
			nav.direct = false
			var grid := _grid()
			var a := _free_cell(from)
			var b := _free_cell(goal)
			paths_computed += 1
			if grid.is_in_boundsv(a) and grid.is_in_boundsv(b):
				nav.path = Array(grid.get_id_path(a, b))
			else:
				nav.path = []
		path = nav.path
	if bool(nav.get("direct", false)) or path.is_empty():
		return (goal - from).normalized() if from.distance_to(goal) > .001 else Vector2.ZERO
	var s := _step()
	while not path.is_empty() and from.distance_to(Vector2(path[0]) * s) < WAYPOINT_REACHED:
		path.remove_at(0)
	if path.is_empty():
		return (goal - from).normalized() if from.distance_to(goal) > .001 else Vector2.ZERO
	return (Vector2(path[0]) * s - from).normalized()
