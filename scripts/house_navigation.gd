extends RefCounted
## Small-house 0.4m navigation grid. Closed doors remain route candidates for breaching.
const STEP := .4
var grid := AStarGrid2D.new()
var paths: Dictionary = {}
var timers: Dictionary = {}
var replans := 0
func rebuild(game) -> void:
 grid.region=Rect2i(-20,-20,66,66)
 grid.cell_size=Vector2.ONE*STEP
 grid.diagonal_mode=AStarGrid2D.DIAGONAL_MODE_NEVER
 grid.update()
 for y in range(-20,46):
  for x in range(-20,46):
   var world := Vector2(x,y)*STEP
   grid.set_point_solid(Vector2i(x,y),game._blocked_static(world,.21))
 paths.clear(); timers.clear()
func _cell(point: Vector2) -> Vector2i:
 return Vector2i(roundi(point.x/STEP),roundi(point.y/STEP))
func _free_cell(point: Vector2) -> Vector2i:
 var cell := _cell(point)
 for radius in range(5):
  for y in range(-radius,radius+1):
   for x in range(-radius,radius+1):
    var candidate := cell+Vector2i(x,y)
    if grid.is_in_boundsv(candidate) and not grid.is_point_solid(candidate):
     return candidate
 return Vector2i(-999,-999)
func direction(index: int, from: Vector2, target: Vector2, dt: float) -> Vector2:
 timers[index]=float(timers.get(index,0))-dt
 if timers[index]<=0 or not paths.has(index):
  var a := _free_cell(from)
  var b := _free_cell(target)
  paths[index]=grid.get_id_path(a,b) if grid.is_in_boundsv(a) and grid.is_in_boundsv(b) else []
  timers[index]=.7+index*.11
  replans+=1
 var path: Variant = paths[index]
 while not path.is_empty() and from.distance_to(Vector2(path[0])*STEP)<.23:
  path.remove_at(0)
 if not path.is_empty():
  return (Vector2(path[0])*STEP-from).normalized()
 return (target-from).normalized()
