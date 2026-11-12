extends Node2D
## LAST LIGHT V3.6 — single-house vertical slice. Art is original, procedural placeholder geometry.
## Gameplay, interaction targets and visual mesh share the same door/wall positions.
const TX := 40.0
const TY := 20.0
const WALL_HEIGHT := 63.0
const PLAYER_RADIUS := 0.19
const HOME := Rect2(0.0, 0.0, 9.0, 8.0)
var player := Vector2(4.9, 9.35)
var health := 100.0
var god_mode := false
var supplies := 0
var infected := [Vector2(-1.9, 7.9), Vector2(11.6, 7.2)]
var zombie_health := [3, 3]
var zombies_hit_time := [0.0, 0.0]
var walls: Array[Dictionary] = []
var doors: Array[Dictionary] = []
var items: Array[Dictionary] = []
var elapsed := 0.0
var motion_phase := 0.0
var facing := Vector2(0, 1)
var message := "Find the front door and press INTERACT"
var message_time := 5.0
var joystick_touch := -1
var joystick_vector := Vector2.ZERO
var movement_keys := Vector2.ZERO
var panel_touches := {}
var stick_center := Vector2.ZERO
var stick_radius := 62.0
var attack_cooldown := 0.0

func _ready() -> void:
 _make_house()
 set_process(true)
 queue_redraw()

func _wall(a: Vector2, b: Vector2, exterior: bool = false) -> void:
 walls.append({"a": a, "b": b, "exterior": exterior})

func _door(a: Vector2, b: Vector2, label: String, open: bool = false) -> void:
 doors.append({"a": a, "b": b, "label": label, "open": open, "health": 45.0})

func _wall_with_door(a: Vector2, b: Vector2, center: Vector2, width: float, label: String, initially_open: bool = false) -> void:
 var direction := (b - a).normalized()
 var u := center - direction * width * 0.5
 var v := center + direction * width * 0.5
 _wall(a, u, label == "FRONT")
 _door(u, v, label, initially_open)
 _wall(v, b, label == "FRONT")

func _make_house() -> void:
 walls.clear()
 doors.clear()
 items.clear()
 _wall(Vector2(0, 0), Vector2(9, 0), true)
 _wall(Vector2(0, 0), Vector2(0, 8), true)
 _wall(Vector2(9, 0), Vector2(9, 8), true)
 _wall_with_door(Vector2(0, 8), Vector2(9, 8), Vector2(5.4, 8), 1.65, "FRONT")
 _wall_with_door(Vector2(4.5, 0), Vector2(4.5, 4), Vector2(4.5, 2), 1.6, "KITCHEN")
 _wall_with_door(Vector2(4.5, 4), Vector2(4.5, 8), Vector2(4.5, 6), 1.6, "BEDROOM")
 _wall_with_door(Vector2(0, 4), Vector2(4.5, 4), Vector2(2.1, 4), 1.6, "LIVING")
 _wall_with_door(Vector2(4.5, 4), Vector2(9, 4), Vector2(6.9, 4), 1.6, "BATHROOM")
 items = [
  {"pos": Vector2(1.2, 1.0), "size": Vector2(1.5, .7), "name": "KITCHEN COUNTER", "searched": false, "tint": Color("777164")},
  {"pos": Vector2(6.5, 1.0), "size": Vector2(1.25, .9), "name": "BED", "searched": false, "tint": Color("566a75")},
  {"pos": Vector2(1.1, 6.5), "size": Vector2(1.6, .75), "name": "SOFA", "searched": false, "tint": Color("796557")},
  {"pos": Vector2(7.25, 6.6), "size": Vector2(.75, .75), "name": "MEDICINE CABINET", "searched": false, "tint": Color("b3b7a5")}
 ]

func _segment_distance(p: Vector2, a: Vector2, b: Vector2) -> float:
 var line := b - a
 var t: float = clampf((p - a).dot(line) / maxf(line.length_squared(), .00001), 0, 1)
 return p.distance_to(a + line * t)

func _blocked(p: Vector2, radius: float = PLAYER_RADIUS) -> bool:
 for wall in walls:
  if _segment_distance(p, wall.a, wall.b) < radius + .09:
   return true
 for door in doors:
  if not door.open and _segment_distance(p, door.a, door.b) < radius + .09:
   return true
 for item in items:
  var r := Rect2(item.pos, item.size).grow(radius)
  if r.has_point(p):
   return true
 return false

func _try_move(current: Vector2, delta_pos: Vector2, radius: float) -> Vector2:
 var result := current
 var steps := maxi(1, ceili(delta_pos.length() / .10))
 for i in range(steps):
  var d := delta_pos / steps
  if not _blocked(result + Vector2(d.x, 0), radius):
   result.x += d.x
  if not _blocked(result + Vector2(0, d.y), radius):
   result.y += d.y
 return result

func _nearest_door() -> int:
 var closest := -1
 var score := 1.45
 for i in range(doors.size()):
  var door := doors[i]
  var d: float = _segment_distance(player, door.a, door.b)
  if d < score:
   score = d
   closest = i
 return closest

func _announce(text: String) -> void:
 message = text
 message_time = 2.8

func _interact() -> void:
 var i := _nearest_door()
 if i >= 0:
  _toggle_door(i)
  return
 for item in items:
  var center: Vector2 = item.pos + item.size / 2.0
  if player.distance_to(center) < 1.9:
   if item.searched:
    _announce("Already searched " + item.name)
   else:
    item.searched = true
    supplies += 1
    _announce("Found supplies in " + item.name)
   return
 _announce("Move closer to a door or cabinet")

func _toggle_door(i: int) -> void:
 if i < 0 or i >= doors.size():
  return
 var door := doors[i]
 if door.open and _segment_distance(player, door.a, door.b) < .31:
  _announce("Step out of the doorway to close it")
  return
 door.open = not door.open
 _announce(door.label + (" door OPEN" if door.open else " door CLOSED"))

func _attack() -> void:
 if attack_cooldown > 0:
  return
 attack_cooldown = .45
 var hit := false
 for i in range(infected.size()):
  if zombie_health[i] <= 0:
   continue
  if infected[i].distance_to(player) < 1.25:
   zombie_health[i] -= 1
   zombies_hit_time[i] = .22
   hit = true
 if hit:
  _announce("Zombie struck")
 else:
  _announce("Nothing in melee reach")

func _process(delta: float) -> void:
 var dt: float = minf(delta, .05)
 elapsed += dt
 message_time = maxf(0, message_time - dt)
 attack_cooldown = maxf(0, attack_cooldown - dt)
 var key_direction := Input.get_vector("ui_left", "ui_right", "ui_up", "ui_down")
 var input_direction := joystick_vector if joystick_touch >= 0 else key_direction
 if input_direction.length() > .12:
  # Screen-space analog movement converted to isometric grid axes.
  var world_direction := Vector2(input_direction.x + input_direction.y, input_direction.y - input_direction.x).normalized()
  facing = world_direction
  player = _try_move(player, world_direction * 2.2 * dt * minf(1, input_direction.length()), PLAYER_RADIUS)
  motion_phase += dt * 11
 for i in range(infected.size()):
  if zombie_health[i] <= 0:
   continue
  zombies_hit_time[i] = maxf(0, zombies_hit_time[i] - dt)
  if infected[i].distance_to(player) > 6.8:
   continue
  var chase: Vector2 = (player - (infected[i] as Vector2)).normalized()
  var old: Vector2 = infected[i] as Vector2
  infected[i] = _try_move(old, chase * .72 * dt, .17)
  if infected[i].distance_to(old) < .008:
   for door in doors:
    if not door.open and _segment_distance(infected[i], door.a, door.b) < .55:
     door.health -= dt * 12
     if door.health <= 0:
      door.open = true
      _announce("BREACH! An infected broke a door")
  if infected[i].distance_to(player) < .62 and not god_mode:
   health = maxf(0, health - dt * 9)
 if health <= 0:
  _announce("You did not survive — toggle GOD for testing")
 queue_redraw()

func _iso(p: Vector2, height: float = 0) -> Vector2:
 return Vector2((p.x - p.y) * TX, (p.x + p.y) * TY - height)

func _screen(p: Vector2, height: float = 0) -> Vector2:
 var size := get_viewport_rect().size
 return _iso(p, height) - _iso(player) + size * Vector2(.50, .53)

func _poly(points: PackedVector2Array, color: Color) -> void:
 draw_colored_polygon(points, color)

func _quad(a: Vector2, b: Vector2, c: Vector2, d: Vector2, color: Color) -> void:
 _poly(PackedVector2Array([a, b, c, d]), color)

func _text(label: String, point: Vector2, size: int = 16, color: Color = Color("eadcb8")) -> void:
 draw_string(ThemeDB.fallback_font, point, label, HORIZONTAL_ALIGNMENT_LEFT, -1, size, color)

func _draw_wall(a: Vector2, b: Vector2, height: float, tint: Color) -> void:
 var A := _screen(a)
 var B := _screen(b)
 _quad(A, B, _screen(b, height), _screen(a, height), tint)
 draw_line(_screen(a, height), _screen(b, height), Color("344b42"), 2)

# Render-only helpers: visual geometry follows the same tile positions as collisions.
# These methods never alter item, door, wall, or inventory state.
func _block_iso(a: Vector2, b: Vector2, height: float, top: Color, right: Color, left: Color) -> void:
 var east := Vector2(b.x, a.y)
 var west := Vector2(a.x, b.y)
 _quad(_screen(east), _screen(b), _screen(b, height), _screen(east, height), right)
 _quad(_screen(west), _screen(b), _screen(b, height), _screen(west, height), left)
 _quad(_screen(a, height), _screen(east, height), _screen(b, height), _screen(west, height), top)

func _draw_object(item: Dictionary) -> void:
 var a: Vector2 = item.pos
 var b: Vector2 = a + item.size
 var center: Vector2 = a + item.size * 0.5
 var name: String = str(item.name)
 var floor_center := _screen(center)
 draw_ellipse_approx(floor_center + Vector2(0, 6), Vector2(maxf(14, item.size.x * TX * 0.68), maxf(7, item.size.y * TY * .86)), Color(0, .04, .03, .26))
 if name == "BED":
  _block_iso(a, b, 12, Color("675348"), Color("574439"), Color("4c4037"))
  _block_iso(a + Vector2(.11, .10), b - Vector2(.11, .10), 15, Color("c3c3b1"), Color("928c81"), Color("a49d8e"))
  _quad(_screen(a + Vector2(.09, .34), 17), _screen(Vector2(b.x-.09, a.y+.34), 17), _screen(Vector2(b.x-.09, b.y-.07), 17), _screen(Vector2(a.x+.09,b.y-.07), 17), Color("637d86"))
  _block_iso(a + Vector2(.16, .07), a + Vector2(.61,.30), 19, Color("e1dace"), Color("beb4a7"), Color("b0aaa0"))
  draw_line(_screen(a + Vector2(.14,.42), 17), _screen(b - Vector2(.13,.15), 17), Color("9caeb0"), 1.8)
 elif name == "SOFA":
  _block_iso(a,b,14,Color("786f5b"),Color("554f44"),Color("5e5346"))
  _block_iso(a,Vector2(b.x,a.y+.18),28,Color("81735e"),Color("655646"),Color("584d41"))
  _block_iso(a,Vector2(a.x+.13,b.y),22,Color("887866"),Color("655548"),Color("59483e"))
  _block_iso(Vector2(b.x-.13,a.y),b,22,Color("887866"),Color("5e4d41"),Color("634c40"))
  _block_iso(a + Vector2(.14,.24), b - Vector2(.14,.10), 17, Color("9c8a70"), Color("665545"),Color("5e5247"))
  draw_line(_screen(a + Vector2(.7,.23), 18),_screen(a + Vector2(.7,b.y-a.y-.12),18),Color("5d5449"),1.6)
 elif name == "KITCHEN COUNTER":
  _block_iso(a,b,32,Color("908271"),Color("5e594e"),Color("656054"))
  _block_iso(a + Vector2(-.05,-.03),b + Vector2(.04,.05),35,Color("bdb5a3"),Color("817b6f"),Color("817569"))
  var basin := _screen(center + Vector2(.17,0),36)
  draw_ellipse_approx(basin,Vector2(11,5),Color("465b5a"))
  draw_ellipse_approx(basin,Vector2(7,3),Color("9ea8a3"))
  draw_line(basin + Vector2(-2,-7), basin + Vector2(2,-11), Color("d1d0c2"),2)
  draw_line(_screen(b + Vector2(-.09,0),15),_screen(b+Vector2(-.09,0),25),Color("b9a48a"),2)
 elif name == "MEDICINE CABINET":
  _block_iso(a,b,51,Color("c0c6b9"),Color("667b77"),Color("86918a"))
  var door_center := _screen(center,32)
  draw_rect(Rect2(door_center + Vector2(-14,-23), Vector2(24,38)),Color("c0c7bb"))
  draw_rect(Rect2(door_center + Vector2(-11,-20), Vector2(18,32)),Color("778e8b"))
  draw_line(door_center+Vector2(-2,-15), door_center+Vector2(-2,5), Color("e0dcc9"),2)
  draw_line(door_center+Vector2(-9,-5), door_center+Vector2(5,-5),Color("e0dcc9"),2)
  draw_circle(door_center+Vector2(10,2),2.1,Color("f6dca2"))
 else:
  _block_iso(a,b,20,item.tint,item.tint.darkened(.26),item.tint.darkened(.4))
 if not item.searched:
  var glint := _screen(center,32 if name!="MEDICINE CABINET" else 59)
  draw_circle(glint + Vector2(9,-5),2,Color("e9cd91"))

func _draw_character(location: Vector2, is_player: bool, phase: float, hurt: bool = false) -> void:
 var p: Vector2 = _screen(location)
 var color: Color = Color("447f9b") if is_player else Color("85514d")
 if hurt:
  color = Color("d98972")
 draw_ellipse_approx(p + Vector2(0, 2), Vector2(12, 5), Color(0, 0, 0, .45))
 var bob := sin(phase) * 2.5
 draw_rect(Rect2(p + Vector2(-6, -29 + bob), Vector2(12, 22)), color)
 draw_circle(p + Vector2(0, -33 + bob), 6, Color("d3b69a") if is_player else Color("9eae96"))
 _text("YOU" if is_player else "!", p + Vector2(-14, -48 + bob), 14, Color("f5d98b") if is_player else Color("fa9a86"))

func draw_ellipse_approx(center: Vector2, radii: Vector2, color: Color) -> void:
 var vertices := PackedVector2Array()
 for i in range(16):
  var a := float(i) / 16 * TAU
  vertices.append(center + Vector2(cos(a) * radii.x, sin(a) * radii.y))
 _poly(vertices, color)

func _interior_visual_state() -> String:
 # Only a player INSIDE the physical building removes roof/occluding walls.
 # A player touching the door, exterior wall, or porch never triggers cutaway.
 if Rect2(.35,.35,8.30,7.30).has_point(player):
  return "INSIDE"
 if HOME.grow(.95).has_point(player):
  return "EDGE"
 return "OUTSIDE"

func _draw_room_floor(tile: Vector2) -> void:
 var is_top := tile.y < 4.0
 var is_left := tile.x < 4.5
 var kitchen := is_top and is_left
 var bedroom := is_top and not is_left
 var living := not is_top and is_left
 var main_col := Color("89948d") if kitchen else Color("917d6b") if bedroom else Color("806c5e") if living else Color("9caaa6")
 var contrast := Color("adbaad") if kitchen else Color("c0a688") if bedroom else Color("a78f78") if living else Color("c6cfbf")
 var east := tile + Vector2(1,0)
 var south := tile + Vector2(1,1)
 var west := tile + Vector2(0,1)
 _quad(_screen(tile),_screen(east),_screen(south),_screen(west),main_col if int(tile.x+tile.y)%3!=0 else contrast)
 if kitchen or (not kitchen and not bedroom and not living):
  draw_line(_screen(tile + Vector2(.5,0)),_screen(tile + Vector2(.5,1)),Color("e7e3d1",.28),1)
 else:
  for j in range(2):
   var phase := float(j+1)/3.0
   draw_line(_screen(tile + Vector2(0,phase)),_screen(tile + Vector2(1,phase)),Color("dbc9a6",.23),1.0)
  draw_line(_screen(tile+Vector2(.58,0)),_screen(tile+Vector2(.58,.5)),Color("473e35",.20),1)

func _draw_house() -> void:
 var state := _interior_visual_state()
 var inside := state == "INSIDE"
 for y in range(8):
  for x in range(9):
   _draw_room_floor(Vector2(x,y))
 if inside:
  # Render the far walls, retain every floor and item. Only foreground wall
  # faces occluding the camera are cut away after *actual interior entry*.
  for wall in walls:
   var a: Vector2 = wall.a
   var b: Vector2 = wall.b
   if wall.exterior and (is_equal_approx(a.y,8.0) and is_equal_approx(b.y,8.0) or is_equal_approx(a.x,9.0) and is_equal_approx(b.x,9.0)):
    continue
   var height := WALL_HEIGHT if wall.exterior else 41.0
   _draw_wall(a,b,height,Color("c0ac92") if wall.exterior else Color("9e9884"))
   draw_line(_screen(a,9),_screen(b,9),Color("e9d5b7",.8),2.0)
   draw_line(_screen(a,height-5),_screen(b,height-5),Color("e4d7bf",.42),1.0)
   if wall.exterior:
    for k in range(1,9):
     var pt: Vector2 = a.lerp(b,float(k)/9.0)
     draw_line(_screen(pt,14),_screen(pt,height-8),Color("725a48",.12),1.0)
  for item in items:
   _draw_object(item)
  for door in doors:
   if not door.open:
    _draw_wall(door.a,door.b,35,Color("80624b"))
    draw_line(_screen(door.a,36),_screen(door.b,36),Color("d5b997"),2)
   else:
    var mid: Vector2 = (door.a + door.b)*.5
    draw_circle(_screen(mid),4,Color("b1d7b0"))
 else:
  # OUTSIDE and EDGE ALWAYS render full structure regardless of proximity.
  for wall in walls:
   if wall.exterior:
    _draw_wall(wall.a,wall.b,WALL_HEIGHT,Color("aeaa93"))
   else:
    _draw_wall(wall.a,wall.b,WALL_HEIGHT,Color("7b806b"))
  for k in range(1,11):
   var t := float(k)/11.0
   var front_pt := Vector2(t*9,8)
   var rear_pt := Vector2(t*9,0)
   draw_line(_screen(front_pt,12),_screen(front_pt,WALL_HEIGHT-10),Color("f2e7cd",.19),1)
   draw_line(_screen(rear_pt,12),_screen(rear_pt,WALL_HEIGHT-10),Color("e1d4bc",.14),1)
  # Window glass, frames and sill on the real front facade.
  for wx in [2.1,7.25]:
   var left := Vector2(wx-.48,8)
   var right := Vector2(wx+.48,8)
   _quad(_screen(left,29),_screen(right,29),_screen(right,53),_screen(left,53),Color("3f666d"))
   draw_line(_screen(left,54),_screen(right,54),Color("e9d6b9"),2.5)
   draw_line(_screen(left,28),_screen(right,28),Color("dfcab0"),2.5)
   draw_line(_screen(Vector2(wx,8),29),_screen(Vector2(wx,8),53),Color("e9d6b9"),1.8)
   draw_line(_screen(left,41),_screen(right,41),Color("e0ccb3"),1.6)
  # Two pitched roof planes and repeated original shingles on a 2:1 iso grid.
  var a := _screen(Vector2(0,0),71)
  var b := _screen(Vector2(9,0),71)
  var c := _screen(Vector2(9,8),71)
  var d := _screen(Vector2(0,8),71)
  var ridge_a := _screen(Vector2(4.5,0),116)
  var ridge_b := _screen(Vector2(4.5,8),116)
  _quad(a,ridge_a,ridge_b,d,Color("606a60"))
  _quad(ridge_a,b,c,ridge_b,Color("414d4b"))
  draw_line(ridge_a,ridge_b,Color("a6a99a"),3)
  for j in range(1,9):
   var t := float(j)/9.0
   draw_line(a.lerp(ridge_a,t),d.lerp(ridge_b,t),Color("ccd0b8",.21),1)
   draw_line(ridge_a.lerp(b,t),ridge_b.lerp(c,t),Color("172a2b",.36),1)
  for j in range(1,7):
   var t := float(j)/7.0
   draw_line(a.lerp(d,t),ridge_a.lerp(ridge_b,t),Color("d4cbb9",.14),1)
   draw_line(ridge_a.lerp(ridge_b,t),b.lerp(c,t),Color("dfddd1",.14),1)
  # Chimney and skylight are dedicated geometry, not placeholder blocks.
  _block_iso(Vector2(2.6,2.0),Vector2(3.15,2.50),130,Color("9e8b7b"),Color("766759"),Color("66564b"))
  draw_line(_screen(Vector2(2.54,2.10),130),_screen(Vector2(3.2,2.10),130),Color("d3c4b0"),3)
func _draw_ui() -> void:
 var size := get_viewport_rect().size
 var dark := Color("0b1c19")
 draw_rect(Rect2(Vector2.ZERO, Vector2(size.x, 139)), dark)
 _text("L A S T   L I G H T", Vector2(18, 30), 22, Color("f0e0b6"))
 _text("V3.6 / HOUSE VERTICAL SLICE", Vector2(18, 51), 12, Color("b1c6b8"))
 _text("HP %d   SUPPLIES %d   ZOMBIES %d" % [int(health), supplies, _alive_zombies()], Vector2(18, 80), 15)
 _text("GOD MODE ON" if god_mode else "GOD MODE OFF", Vector2(18, 105), 14, Color("f4d69a") if god_mode else Color("b5bdb0"))
 if message_time > 0:
  _text(message, Vector2(18, 131), 13)
 stick_center = Vector2(100, size.y - 108)
 draw_circle(stick_center, stick_radius, Color(.12, .24, .21, .85))
 draw_arc(stick_center, stick_radius, 0, TAU, 32, Color("9daf9c"), 2)
 draw_circle(stick_center + joystick_vector * 36, 30, Color("cab782"))
 _text("MOVE", stick_center + Vector2(-22, 77), 12)
 var interact_center := Vector2(size.x - 92, size.y - 111)
 var attack_center := Vector2(size.x - 205, size.y - 92)
 draw_circle(interact_center, 53, Color("d6bd88"))
 draw_circle(attack_center, 43, Color("b98273"))
 _text("INTERACT", interact_center - Vector2(40, 0), 14, Color("17231d"))
 _text("ATTACK", attack_center - Vector2(31, 0), 14, Color("17231d"))
 draw_rect(Rect2(Vector2(size.x - 128, 12), Vector2(111, 34)), Color("33483b"))
 _text("GOD ON" if god_mode else "GOD OFF", Vector2(size.x - 112, 35), 14)

func _alive_zombies() -> int:
 var alive := 0
 for hp in zombie_health:
  if hp > 0:
   alive += 1
 return alive

func _draw() -> void:
 var v := get_viewport_rect().size
 draw_rect(Rect2(Vector2.ZERO, v), Color("101e19"))
 for y in range(-6, 17):
  for x in range(-7, 18):
   var cell := Vector2(x, y)
   var col := Color("425d47") if (x + y) % 2 == 0 else Color("3c5542")
   _quad(_screen(cell), _screen(cell + Vector2(1, 0)), _screen(cell + Vector2(1, 1)), _screen(cell + Vector2(0, 1)), col)
 _draw_house()
 for i in range(infected.size()):
  if zombie_health[i] > 0:
   _draw_character(infected[i], false, elapsed * 4 + i, zombies_hit_time[i] > 0)
 _draw_character(player, true, motion_phase)
 _draw_ui()

func _tap(point: Vector2) -> void:
 var size := get_viewport_rect().size
 if point.y < 48 and point.x > size.x - 140:
  god_mode = not god_mode
  health = 100 if god_mode else health
  _announce("GOD MODE ON" if god_mode else "GOD MODE OFF")
  return
 if point.distance_to(Vector2(size.x - 92, size.y - 111)) < 58:
  _interact()
  return
 if point.distance_to(Vector2(size.x - 205, size.y - 92)) < 48:
  _attack()
  return
 for i in range(doors.size()):
  var d := doors[i]
  var c: Vector2 = (d.a + d.b) / 2
  if point.distance_to(_screen(c, 49)) < 28 and player.distance_to(c) < 1.85:
   _toggle_door(i)
   return
 for item in items:
  if point.distance_to(_screen(item.pos + item.size / 2, 23)) < 38:
   _interact()
   return

func _update_stick(point: Vector2) -> void:
 joystick_vector = (point - stick_center).limit_length(stick_radius) / stick_radius
 if joystick_vector.length() < .14:
  joystick_vector = Vector2.ZERO

func _input(event: InputEvent) -> void:
 if event is InputEventScreenTouch:
  if event.pressed:
   if event.position.distance_to(stick_center) < stick_radius + 42 and joystick_touch < 0:
    joystick_touch = event.index
    _update_stick(event.position)
   else:
    _tap(event.position)
  elif joystick_touch == event.index:
   joystick_touch = -1
   joystick_vector = Vector2.ZERO
 elif event is InputEventScreenDrag and event.index == joystick_touch:
  _update_stick(event.position)
 elif event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT and event.pressed:
  if event.position.distance_to(stick_center) < stick_radius + 42:
   joystick_touch = 999
   _update_stick(event.position)
  else:
   _tap(event.position)
 elif event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT and not event.pressed and joystick_touch == 999:
  joystick_touch = -1
  joystick_vector = Vector2.ZERO
 elif event is InputEventMouseMotion and joystick_touch == 999:
  _update_stick(event.position)
 elif event is InputEventKey and event.pressed and not event.echo:
  if event.keycode == KEY_E:
   _interact()
  elif event.keycode == KEY_SPACE:
   _attack()
  elif event.keycode == KEY_G:
   god_mode = not god_mode