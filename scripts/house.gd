extends Node2D
## LAST LIGHT V3.6 — single-house vertical slice. Art is original, procedural placeholder geometry.
## Gameplay, interaction targets and visual mesh share the same door/wall positions.
const TX := 40.0
const TY := 20.0
const WALL_HEIGHT := 63.0
const PLAYER_RADIUS := 0.19
const HOME := Rect2(0.0, 0.0, 9.0, 8.0)
const HouseArt := preload("res://scripts/house_art.gd")
var art := HouseArt.new()
const MobileHUD := preload("res://scripts/mobile_hud.gd")
var hud := MobileHUD.new()
var control_rects: Dictionary = {}
var stamina := 100.0
var hunger := 0.0
var thirst := 0.0
var inventory_open := false
var inventory_page := 0
var sprint_held := false
var keyboard_sprint := false
var sprinting := false
var sneaking := false
var joystick_dead_zone := .14
var selected_target: Dictionary = {}
var drops: Array[Dictionary] = []
const SurvivalState := preload("res://scripts/survival_state.gd")
var survival := SurvivalState.new()
const HUNGER_RATE := .025
const THIRST_RATE := .045
const CONTAINER_LOOT := {
 "house.kitchen.counter": {"ll_food_bean_tin":2,"ll_food_water_bottle":2},
 "house.bedroom.bed": {"ll_medical_sterile_bandage":1,"ll_household_flashlight":1},
 "house.living.sofa": {"ll_tools_claw_hammer":1,"ll_food_bean_tin":1},
 "house.bathroom.medicine": {"ll_medical_sterile_bandage":3,"ll_medical_first_aid_case":1}
}
var shove_cooldown := 0.0
var recovery_delay := 0.0
const WALK_SPEED := 2.2
const SPRINT_SPEED := 3.6
const SNEAK_SPEED := .95
const STAMINA_DRAIN := 18.0
const STAMINA_REGEN := 12.0
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
var panel_touches := {}
const MOUSE_POINTER := -2
const SAVE_PATH := "user://last_light_v04.json"
var paused := false
var autosave_time := 0.0
var stick_center := Vector2.ZERO
var stick_radius := 62.0
var attack_cooldown := 0.0
var asset_showcase: Array[Dictionary] = []
var asset_textures: Dictionary = {}
var asset_preview_visible := true

func _ready() -> void:
 art.setup(self)
 _make_house()
 _layout_controls()
 _load_game()
 get_viewport().size_changed.connect(_on_viewport_resized)
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
 items = art.furniture()

func _segment_distance(p: Vector2, a: Vector2, b: Vector2) -> float:
 var line := b - a
 var t: float = clampf((p - a).dot(line) / maxf(line.length_squared(), .00001), 0, 1)
 return p.distance_to(a + line * t)

func _blocked_static(p: Vector2, radius: float = PLAYER_RADIUS) -> bool:
 for wall in walls:
  if _segment_distance(p,wall.a,wall.b)<radius+.09: return true
 for item in items:
  if item.get("solid",true) and Rect2(item.pos,item.size).grow(radius).has_point(p): return true
 return false

func _blocked(p: Vector2, radius: float = PLAYER_RADIUS) -> bool:
 if _blocked_static(p,radius): return true
 for door in doors:
  if not door.open and _segment_distance(p,door.a,door.b)<radius+.09: return true
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
 if health<=0 or paused: return
 var target:=_resolve_target()
 if target.is_empty():
  _announce("Move closer to a door, cabinet or dropped item")
  return
 if target.kind=="door":
  _toggle_door(target.index)
 elif target.kind=="container":
  var item: Dictionary=items[target.index]
  var loot: Dictionary=CONTAINER_LOOT.get(item.id,{})
  var previous:=survival.snapshot()
  for id in loot:
   if not survival.add(id,loot[id]):
    survival.restore(previous)
    _announce("Make room in your pack before searching")
    return
  item.searched=true
  supplies+=1
  _announce("Collected supplies from "+String(item.name).capitalize())
 elif target.kind=="drop":
  var drop: Dictionary=drops[target.index]
  if not survival.add(drop.id,drop.count):
   _announce("Pack is full")
   return
  _announce("Picked up "+survival.name_for(drop.id))
  drops.remove_at(target.index)
 selected_target={}
 _save_game()

func _toggle_door(i: int) -> void:
 if i < 0 or i >= doors.size():
  return
 var door := doors[i]
 if door.open and _segment_distance(player, door.a, door.b) < .31:
  _announce("Step out of the doorway to close it")
  return
 if door.open:
  for enemy_index in range(infected.size()):
   if zombie_health[enemy_index] > 0 and _segment_distance(infected[enemy_index], door.a, door.b) < .31:
    _announce("The doorway is occupied")
    return
 door.open = not door.open
 _announce(door.label + (" door OPEN" if door.open else " door CLOSED"))

func _weapon_stats() -> Dictionary:
 if survival.equipped.is_empty(): return {"damage":1,"reach":1.25,"stamina":8.0}
 return survival.definitions[survival.equipped]

func _attack() -> void:
 if health<=0 or paused or attack_cooldown>0: return
 var stats:=_weapon_stats()
 if stamina<float(stats.stamina):
  _announce("Too exhausted to strike")
  return
 stamina-=float(stats.stamina)
 recovery_delay=.85
 attack_cooldown=.5
 var hit:=false
 for i in range(infected.size()):
  var offset: Vector2=infected[i]-player
  if zombie_health[i]>0 and offset.length()<float(stats.reach) and facing.dot(offset.normalized())>=.25 and not _line_blocked(player,infected[i]):
   zombie_health[i]=maxi(0,int(zombie_health[i])-int(stats.damage))
   zombies_hit_time[i]=.32
   infected[i]=_try_move(infected[i],offset.normalized()*.12,.17)
   hit=true
 _announce("Strike landed" if hit else "Miss — face the infected and move closer")

func _shove() -> void:
 if health<=0 or paused or shove_cooldown>0: return
 if stamina<12:
  _announce("Too exhausted to shove")
  return
 stamina-=12
 recovery_delay=.85
 shove_cooldown=.8
 var hit:=false
 for i in range(infected.size()):
  var offset: Vector2=infected[i]-player
  if zombie_health[i]>0 and offset.length()<1.15 and facing.dot(offset.normalized())>=.15 and not _line_blocked(player,infected[i]):
   infected[i]=_try_move(infected[i],offset.normalized()*.65,.17)
   zombies_hit_time[i]=.7
   hit=true
 _announce("Pushed back — make space" if hit else "Shove missed")

func _process(delta: float) -> void:
 if paused or inventory_open or health<=0:
  queue_redraw()
  return
 var total:=clampf(delta,0,.25)
 var steps:=maxi(1,ceili(total/(1.0/60.0)))
 for step in range(steps):
  _step(total/steps)
  if health<=0: break
 queue_redraw()

func _step(dt: float) -> void:
 autosave_time+=dt
 if autosave_time>=15:
  autosave_time=0
  _save_game()
 hunger=minf(100,hunger+HUNGER_RATE*dt)
 thirst=minf(100,thirst+THIRST_RATE*dt)
 elapsed+=dt
 message_time=maxf(0,message_time-dt)
 attack_cooldown=maxf(0,attack_cooldown-dt)
 shove_cooldown=maxf(0,shove_cooldown-dt)
 recovery_delay=maxf(0,recovery_delay-dt)
 var keyboard:=Input.get_vector("ui_left","ui_right","ui_up","ui_down")
 if keyboard==Vector2.ZERO:
  keyboard=Vector2(float(Input.is_physical_key_pressed(KEY_D))-float(Input.is_physical_key_pressed(KEY_A)),float(Input.is_physical_key_pressed(KEY_S))-float(Input.is_physical_key_pressed(KEY_W))).limit_length(1)
 var direction:=joystick_vector if joystick_touch!=-1 else keyboard
 sprinting=(sprint_held or keyboard_sprint) and not sneaking and direction.length()>.01 and stamina>0
 var speed:=SPRINT_SPEED if sprinting else SNEAK_SPEED if sneaking else WALK_SPEED
 if sprinting:
  stamina=maxf(0,stamina-STAMINA_DRAIN*dt)
  recovery_delay=.5
 elif recovery_delay<=0:
  stamina=minf(100,stamina+STAMINA_REGEN*dt)
 if direction.length()>.01:
  facing=_screen_direction_to_world(direction)
  player=_try_move(player,facing*speed*dt*minf(1,direction.length()),PLAYER_RADIUS)
  motion_phase+=dt*(15 if sprinting else 7 if sneaking else 10)
 for i in range(infected.size()):
  if zombie_health[i]<=0: continue
  zombies_hit_time[i]=maxf(0,zombies_hit_time[i]-dt)
  if zombies_hit_time[i]>0 or infected[i].distance_to(player)>6.8: continue
  var chase: Vector2=(player-infected[i]).normalized()
  var old: Vector2=infected[i]
  infected[i]=_try_move(old,chase*.72*dt,.17)
  if infected[i].distance_to(old)<.008:
   for door in doors:
    if not door.open and _segment_distance(infected[i],door.a,door.b)<.55:
     door.health=maxf(0,door.health-dt*12)
     if door.health<=0:
      door.open=true
      _announce("BREACH! An infected broke a door")
  if infected[i].distance_to(player)<.62 and not god_mode and not _line_blocked(infected[i],player):
   health=maxf(0,health-dt*9)
 if health<=0:
  _clear_pointers()
  _announce("You did not survive — begin again")
  _save_game()

func _iso(p: Vector2, height: float = 0) -> Vector2:
 return Vector2((p.x - p.y) * TX, (p.x + p.y) * TY - height)

func _screen(p: Vector2, height: float = 0) -> Vector2:
 var size := get_viewport_rect().size
 return _iso(p, height) - _iso(player) + size * Vector2(.50, .58 if HOME.has_point(player) else .70)

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

func _draw_object(item: Dictionary) -> void:
 var a: Vector2 = item.pos
 var b: Vector2 = a + item.size
 var h := 21.0
 var tint: Color = item.tint
 _quad(_screen(Vector2(b.x, a.y)), _screen(b), _screen(b, h), _screen(Vector2(b.x, a.y), h), tint.darkened(.26))
 _quad(_screen(Vector2(a.x, b.y)), _screen(b), _screen(b, h), _screen(Vector2(a.x, b.y), h), tint.darkened(.4))
 _quad(_screen(a, h), _screen(Vector2(b.x, a.y), h), _screen(b, h), _screen(Vector2(a.x, b.y), h), tint)
 if not item.searched:
  _text("+", _screen(a + item.size / 2, 33), 17, Color("edd18d"))

func _draw_character(location: Vector2, is_player: bool, phase: float, hurt: bool = false) -> void:
 var p:=_screen(location)
 var forward: Vector2=_iso(facing if is_player else (player-location).normalized()).normalized()
 var side:=Vector2(-forward.y,forward.x)
 var cloth:=Color("687b70") if is_player else Color("756e57")
 if hurt: cloth=Color("caa18d")
 var skin:=Color("b9ac90") if is_player else Color("89947b")
 var walk:=sin(phase)*3
 var crouch:=9.0 if is_player and sneaking else 0.0
 draw_ellipse_approx(p+Vector2(3,2),Vector2(16,6),Color(0,0,0,.3))
 for sign in [-1,1]:
  var foot: Vector2=p+side*sign*5+forward*walk*sign
  draw_line(p+Vector2(sign*4,-30+crouch),foot,Color("333f3a"),7,true)
  draw_line(foot,foot+forward*5,Color("252e2a"),5,true)
 var hip:=p+Vector2(0,-31+crouch)
 var shoulder:=p+Vector2(0,-52+crouch)
 draw_line(hip,shoulder,cloth,17,true)
 draw_line(hip+Vector2(-7,0),hip+Vector2(7,0),Color("4b5140"),3,true)
 for sign in [-1,1]:
  var hand: Vector2=shoulder+side*sign*10+Vector2(0,18)+forward*(3 if sign>0 else -3)
  if is_player and attack_cooldown>.25: hand+=forward*15
  draw_line(shoulder+side*sign*7,hand,cloth.darkened(.12),6,true)
  draw_circle(hand,3,skin)
 draw_circle(p+Vector2(0,-62+crouch),8,skin)
 draw_arc(p+Vector2(0,-64+crouch),7,PI,TAU,12,Color("514f3e"),4,true)
 draw_circle(p+Vector2(0,-62+crouch)+forward*6,2,skin.lightened(.12))
 if is_player:
  draw_arc(p+Vector2(0,1),19,forward.angle()-.45,forward.angle()+.45,12,Color("b4c6ab"),2,true)

func draw_ellipse_approx(center: Vector2, radii: Vector2, color: Color) -> void:
 var vertices := PackedVector2Array()
 for i in range(16):
  var a := float(i) / 16 * TAU
  vertices.append(center + Vector2(cos(a) * radii.x, sin(a) * radii.y))
 _poly(vertices, color)

func _draw_house() -> void:
 var inside := HOME.has_point(player)
 for y in range(8):
  for x in range(9):
   var tile := Vector2(x, y)
   var tint := Color("7b7264") if x < 4 else Color("8b8273")
   if y >= 4:
    tint = Color("6d766b") if x < 4 else Color("6a7e80")
   _quad(_screen(tile), _screen(tile + Vector2(1, 0)), _screen(tile + Vector2(1, 1)), _screen(tile + Vector2(0, 1)), tint)
 if inside:
  for item in items:
   _draw_object(item)
  for wall in walls:
   var a: Vector2 = wall.a
   var b: Vector2 = wall.b
   # Remove only camera-facing exterior walls; far walls stay solid.
   if wall.exterior and (absf(a.y - 8) < .001 and absf(b.y - 8) < .001 or absf(a.x - 9) < .001 and absf(b.x - 9) < .001):
    continue
   _draw_wall(a, b, WALL_HEIGHT if wall.exterior else 45, Color("5d7168") if wall.exterior else Color("56645a"))
  for door in doors:
   var c: Vector2 = (door.a + door.b) / 2
   if not door.open:
    _draw_wall(door.a, door.b, 38, Color("875d43"))
   else:
    draw_circle(_screen(c), 6, Color("b0deb2"))
   _text("OPEN" if door.open else "DOOR", _screen(c, 49), 12, Color("bce2c1") if door.open else Color("ebcea0"))
 else:
  # Full opaque roof and walls. Geometry remains unchanged for collision.
  for wall in walls:
   _draw_wall(wall.a, wall.b, WALL_HEIGHT, Color("6c8077") if wall.exterior else Color("697970"))
  var a := _screen(Vector2(0, 0), 70)
  var b := _screen(Vector2(9, 0), 70)
  var c := _screen(Vector2(9, 8), 70)
  var d := _screen(Vector2(0, 8), 70)
  var ridge_a := _screen(Vector2(4.5, 0), 110)
  var ridge_b := _screen(Vector2(4.5, 8), 110)
  _quad(a, ridge_a, ridge_b, d, Color("586669"))
  _quad(ridge_a, b, c, ridge_b, Color("394c51"))
  _text("LAST LIGHT / SAFEHOUSE", _screen(Vector2(3.0, 3), 132), 13)
  var front: Dictionary = doors[0]
  var center: Vector2 = (front.a + front.b) / 2
  _text("OPEN" if front.open else "DOOR", _screen(center, 80), 14)

func _draw_ui() -> void:
 hud.draw(self)

func _alive_zombies() -> int:
 var alive := 0
 for hp in zombie_health:
  if hp > 0:
   alive += 1
 return alive

func _draw() -> void:
 art.draw_world(self)
 _draw_ui()

func _tap(point: Vector2) -> void:
 _layout_controls()
 if health <= 0:
  if control_rects.dead_restart.has_point(point): _restart_game()
  return
 if control_rects.inventory.has_point(point):
  _set_inventory(not inventory_open)
  return
 if inventory_open:
  _inventory_tap(point)
  return
 if control_rects.pause.has_point(point):
  _set_paused(not paused)
  return
 if paused:
  if control_rects.resume.has_point(point): _set_paused(false)
  return
 for action in ["attack","interact","shove","sneak","quick0","quick1","quick2","quick3"]:
  if control_rects[action].has_point(point):
   _activate_action(action)
   return
 _select_world_target(point)

func _update_stick(point: Vector2) -> void:
 var raw := (point-stick_center).limit_length(stick_radius)/stick_radius
 var magnitude := raw.length()
 joystick_vector=Vector2.ZERO if magnitude<=joystick_dead_zone else raw.normalized()*((magnitude-joystick_dead_zone)/(1.0-joystick_dead_zone))

func _layout_controls() -> void:
 control_rects = hud.layout(self)

func _on_viewport_resized() -> void:
 _clear_pointers()
 _layout_controls()

func _clear_pointers() -> void:
 joystick_touch = -1
 joystick_vector = Vector2.ZERO
 sprint_held = false
 keyboard_sprint = false
 sprinting = false
 panel_touches.clear()

func _notification(what: int) -> void:
 if what == NOTIFICATION_APPLICATION_FOCUS_OUT or what == NOTIFICATION_APPLICATION_PAUSED:
  _set_paused(true)
 elif what == NOTIFICATION_WM_CLOSE_REQUEST:
  _save_game()

func _screen_direction_to_world(direction: Vector2) -> Vector2:
 # Inverse of _iso: screen axes have unequal scale in a 2:1 projection.
 return Vector2(direction.x / TX + direction.y / TY, direction.y / TY - direction.x / TX).normalized()

func _pointer_down(pointer: int, point: Vector2) -> void:
 if panel_touches.has(pointer) or joystick_touch == pointer: return
 _layout_controls()
 if health <= 0 or paused or inventory_open:
  panel_touches[pointer] = "modal"
  _tap(point)
  return
 for action in ["inventory","pause","attack","interact","shove","sprint","sneak","quick0","quick1","quick2","quick3"]:
  if control_rects[action].has_point(point):
   panel_touches[pointer] = action
   if action=="sprint": sprint_held=true
   else: _tap(point)
   return
 if control_rects.joystick_rect.has_point(point):
  if joystick_touch == -1:
   joystick_touch=pointer
   _update_stick(point)
  return
 panel_touches[pointer]="world"
 _select_world_target(point)

func _pointer_up(pointer: int) -> void:
 var was_sprint: bool = panel_touches.get(pointer, "")=="sprint"
 panel_touches.erase(pointer)
 if was_sprint:
  sprint_held=panel_touches.values().has("sprint")
  if not sprint_held: sprinting=false
 if joystick_touch==pointer:
  joystick_touch=-1
  joystick_vector=Vector2.ZERO

func _input(event: InputEvent) -> void:
 if event is InputEventScreenTouch:
  if event.pressed and not event.canceled: _pointer_down(event.index,event.position)
  else: _pointer_up(event.index)
 elif event is InputEventScreenDrag:
  if not get_viewport_rect().has_point(event.position):
   _pointer_up(event.index)
  elif event.index==joystick_touch:
   _update_stick(event.position)
  elif panel_touches.get(event.index, "")=="sprint" and not control_rects.sprint.has_point(event.position):
   _pointer_up(event.index)
 elif event is InputEventMouseButton and event.device!=InputEvent.DEVICE_ID_EMULATION and event.button_index==MOUSE_BUTTON_LEFT:
  if event.pressed: _pointer_down(MOUSE_POINTER,event.position)
  else: _pointer_up(MOUSE_POINTER)
 elif event is InputEventMouseMotion and event.device!=InputEvent.DEVICE_ID_EMULATION and joystick_touch==MOUSE_POINTER:
  if get_viewport_rect().has_point(event.position): _update_stick(event.position)
  else: _pointer_up(MOUSE_POINTER)
 elif event is InputEventKey:
  if event.keycode==KEY_SHIFT:
   keyboard_sprint=event.pressed and not paused
  if not event.pressed or event.echo: return
  if event.keycode in [KEY_ESCAPE,KEY_P]:
   if inventory_open: _set_inventory(false)
   else: _set_paused(not paused)
  elif event.keycode==KEY_I and health>0: _set_inventory(not inventory_open)
  elif event.keycode==KEY_R and health<=0: _restart_game()
  elif not paused and health>0:
   match event.keycode:
    KEY_E: _interact()
    KEY_SPACE: _attack()
    KEY_Q: _activate_action("shove")
    KEY_C: _activate_action("sneak")
    KEY_1: _activate_action("quick0")
    KEY_2: _activate_action("quick1")
    KEY_3: _activate_action("quick2")
    KEY_4: _activate_action("quick3")

func _line_blocked(a: Vector2, b: Vector2, furniture: bool = true) -> bool:
 for wall in walls:
  if Geometry2D.segment_intersects_segment(a,b,wall.a,wall.b)!=null: return true
 for door in doors:
  if not door.open and Geometry2D.segment_intersects_segment(a,b,door.a,door.b)!=null: return true
 if furniture:
  for item in items:
   var r:=Rect2(item.pos,item.size)
   if r.has_point(a) or r.has_point(b): return true
   var corners: Array[Vector2]=[r.position,Vector2(r.end.x,r.position.y),r.end,Vector2(r.position.x,r.end.y)]
   for i in range(4):
    if Geometry2D.segment_intersects_segment(a,b,corners[i],corners[(i+1)%4])!=null: return true
 return false

func _set_paused(value: bool) -> void:
 paused = value
 _clear_pointers()
 if paused:
  _save_game()
 queue_redraw()

func _restart_game() -> void:
 _make_house()
 survival.restore({"inventory":{},"equipped":""})
 stamina=100; hunger=0; thirst=0
 inventory_open=false; sneaking=false
 selected_target={}; drops.clear()
 shove_cooldown=0; recovery_delay=0
 facing=Vector2(0,1)
 player = Vector2(4.9, 9.35)
 health = 100.0
 supplies = 0
 god_mode = false
 infected = [Vector2(-1.9, 7.9), Vector2(11.6, 7.2)]
 zombie_health = [3, 3]
 zombies_hit_time = [0.0, 0.0]
 elapsed = 0.0
 motion_phase = 0.0
 attack_cooldown = 0.0
 autosave_time = 0.0
 paused = false
 _clear_pointers()
 _announce("Find the front door and press INTERACT")
 _save_game()

func _save_game(path: String = SAVE_PATH) -> Error:
 var door_states: Array = []
 for door in doors:
  door_states.append({"open": door.open, "health": door.health})
 var searched: Array = []
 for item in items.slice(0,4):
  searched.append(item.searched)
 var enemies: Array = []
 for i in range(infected.size()):
  enemies.append({"x": infected[i].x, "y": infected[i].y, "health": zombie_health[i]})
 var data := {"version": 1, "player": [player.x, player.y], "health": health,
  "supplies": supplies, "doors": door_states, "searched": searched, "enemies": enemies}
 # Write and flush a temporary file before replacing the last known save.
 var file := FileAccess.open(path + ".tmp", FileAccess.WRITE)
 if file == null:
  return FileAccess.get_open_error()
 file.store_string(JSON.stringify(data))
 file.flush()
 var write_error := file.get_error()
 file.close()
 if write_error != OK:
  return write_error
 return DirAccess.rename_absolute(path + ".tmp", path)

func _valid_number(value: Variant, low: float, high: float) -> bool:
 return (value is float or value is int) and is_finite(float(value)) and float(value) >= low and float(value) <= high

func _load_game(path: String = SAVE_PATH) -> Error:
 if not FileAccess.file_exists(path):
  return ERR_FILE_NOT_FOUND
 var file := FileAccess.open(path, FileAccess.READ)
 if file == null:
  return FileAccess.get_open_error()
 if file.get_length() > 65536:
  return ERR_INVALID_DATA
 var data: Variant = JSON.parse_string(file.get_as_text())
 if not data is Dictionary or data.get("version") != 1:
  return ERR_INVALID_DATA
 var pos: Variant = data.get("player")
 if not pos is Array or pos.size() != 2:
  return ERR_INVALID_DATA
 if not _valid_number(pos[0], -100, 100) or not _valid_number(pos[1], -100, 100):
  return ERR_INVALID_DATA
 if not _valid_number(data.get("health"), 0, 100) or not _valid_number(data.get("supplies"), 0, items.size()):
  return ERR_INVALID_DATA
 var door_states: Variant = data.get("doors")
 var searched: Variant = data.get("searched")
 var enemies: Variant = data.get("enemies")
 if not door_states is Array or door_states.size() != doors.size():
  return ERR_INVALID_DATA
 if not searched is Array or searched.size() != 4:
  return ERR_INVALID_DATA
 if not enemies is Array or enemies.size() != infected.size():
  return ERR_INVALID_DATA
 for state in door_states:
  if not state is Dictionary or not state.get("open") is bool or not _valid_number(state.get("health"), 0, 45):
   return ERR_INVALID_DATA
 for state in searched:
  if not state is bool:
   return ERR_INVALID_DATA
 for enemy in enemies:
  if not enemy is Dictionary or not _valid_number(enemy.get("x"), -100, 100) or not _valid_number(enemy.get("y"), -100, 100) or not _valid_number(enemy.get("health"), 0, 3):
   return ERR_INVALID_DATA
 # No mutation before the entire schema has passed validation.
 player = Vector2(pos[0], pos[1])
 health = data.health
 supplies = int(data.supplies)
 for i in range(doors.size()):
  doors[i].open = door_states[i].open
  doors[i].health = door_states[i].health
 for i in range(4):
  items[i].searched = searched[i]
 for i in range(infected.size()):
  infected[i] = Vector2(enemies[i].x, enemies[i].y)
  zombie_health[i] = int(enemies[i].health)
 _clear_pointers()
 return OK


func _set_inventory(value: bool) -> void:
 inventory_open=value
 inventory_page=0
 _set_paused(value)

func _target_valid(target: Dictionary) -> bool:
 if target.is_empty() or not target.has("kind") or not target.get("index") is int: return false
 var index: int=target.index
 var point := Vector2.ZERO
 if target.kind=="door":
  if index<0 or index>=doors.size(): return false
  var door: Dictionary=doors[index]
  point=(door.a+door.b)*.5
  if _segment_distance(player,door.a,door.b)>1.5: return false
  point=point.move_toward(player,.32)
 elif target.kind=="container":
  if index<0 or index>=items.size() or not items[index].get("container",false) or items[index].searched: return false
  var rect := Rect2(items[index].pos,items[index].size)
  point=player.clamp(rect.position,rect.end)
  if player.distance_to(point)>1.6: return false
  point=point.move_toward(player,.05)
 elif target.kind=="drop":
  if index<0 or index>=drops.size(): return false
  point=drops[index].pos
  if player.distance_to(point)>1.5: return false
 else: return false
 return not _line_blocked(player,point,false)

func _target_point(target: Dictionary) -> Vector2:
 if target.kind=="door": return (doors[target.index].a+doors[target.index].b)*.5
 if target.kind=="container": return items[target.index].pos+items[target.index].size*.5
 return drops[target.index].pos

func _resolve_target() -> Dictionary:
 if _target_valid(selected_target): return selected_target.duplicate()
 selected_target={}
 var best: Dictionary={}
 var distance:=INF
 for kind in ["door","container","drop"]:
  var count: int=doors.size() if kind=="door" else items.size() if kind=="container" else drops.size()
  for index in range(count):
   var target: Dictionary={"kind":kind,"index":index}
   if not _target_valid(target): continue
   var score: float=player.distance_to(_target_point(target))
   if score<distance:
    distance=score
    best=target
 return best

func _context_prompt() -> String:
 var target:=_resolve_target()
 if target.is_empty(): return "No usable target nearby"
 if target.kind=="door": return "Close Door" if doors[target.index].open else "Open Door"
 if target.kind=="drop": return "Pick Up Item"
 return "Search "+String(items[target.index].name).capitalize()

func _inventory_rows() -> Array:
 var rows:=survival.rows()
 inventory_page=clampi(inventory_page,0,maxi(0,ceili(rows.size()/6.0)-1))
 return rows.slice(inventory_page*6,inventory_page*6+6)

func _first_item(kind: String) -> String:
 var ids: Array=survival.inventory.keys()
 ids.sort()
 for id in ids:
  if survival.definitions[id].kind==kind: return id
 return ""

func _quick_slots() -> Array:
 var medical:=_first_item("heal")
 var supply:=_first_item("drink") if thirst>0 else _first_item("food")
 if supply.is_empty(): supply=_first_item("food") if _first_item("drink").is_empty() else _first_item("drink")
 return ["Hands" if survival.equipped.is_empty() else "Tool", "Med" if not medical.is_empty() else "—", "—", "Drink" if survival.definitions.get(supply,{}).get("kind")=="drink" else "Food" if not supply.is_empty() else "—"]

func _inventory_tap(point: Vector2) -> void:
 var rows:=_inventory_rows()
 for i in range(rows.size()):
  if control_rects["modal_use_%d"%i].has_point(point):
   _use_item(rows[i].id)
   return
  if control_rects["modal_drop_%d"%i].has_point(point):
   _drop_item(rows[i].id)
   return
 if control_rects.inv_prev.has_point(point): inventory_page=maxi(0,inventory_page-1)
 if control_rects.inv_next.has_point(point): inventory_page+=1
 _inventory_rows()

func _use_item(id: String) -> bool:
 if health<=0 or (paused and not inventory_open) or not survival.inventory.has(id): return false
 var definition: Dictionary=survival.definitions[id]
 var kind: String=definition.kind
 if kind=="weapon":
  survival.equip("" if survival.equipped==id else id)
  _announce("Hands ready" if survival.equipped.is_empty() else "Equipped "+survival.name_for(id))
 elif kind in ["food","drink","heal"]:
  if (kind=="food" and hunger<=0) or (kind=="drink" and thirst<=0) or (kind=="heal" and health>=100):
   _announce("No need to use this yet")
   return false
  var effect:=survival.consume(id)
  if effect.is_empty(): return false
  if kind=="food": hunger=maxf(0,hunger-effect.amount)
  elif kind=="drink": thirst=maxf(0,thirst-effect.amount)
  else: health=minf(100,health+effect.amount)
  _announce(survival.action(id) if survival.inventory.has(id) else "Used "+survival.name_for(id))
 else:
  _announce(survival.name_for(id)+" — carry or drop")
  return true
 _save_game()
 queue_redraw()
 return true

func _drop_item(id: String) -> bool:
 if health<=0 or (paused and not inventory_open) or not survival.inventory.has(id) or drops.size()>=128: return false
 var position:=player
 var found:=false
 for offset in [facing*.55,Vector2(.5,0),Vector2(0,.5),Vector2(-.5,0),Vector2(0,-.5),Vector2.ZERO]:
  var candidate: Vector2=player+offset
  if not _blocked(candidate,.1) and not _line_blocked(player,candidate,false):
   position=candidate
   found=true
   break
 if not found:
  _announce("No clear ground for this item")
  return false
 if not survival.remove(id): return false
 drops.append({"id":id,"count":1,"pos":position})
 art._cache(survival.definitions[id].art_id)
 selected_target={}
 _announce("Dropped "+survival.name_for(id))
 _save_game()
 return true

func _draw_drop(index: int) -> void:
 var drop: Dictionary=drops[index]
 var id: String=survival.definitions[drop.id].art_id
 art._sprite(self,id,drop.pos)
 if player.distance_to(drop.pos)<1.5: draw_circle(_screen(drop.pos,12),2,Color("d5c899"))

func _select_world_target(point: Vector2) -> void:
 var best: Dictionary={}
 var distance:=60.0
 for kind in ["door","container","drop"]:
  var count: int=doors.size() if kind=="door" else items.size() if kind=="container" else drops.size()
  for index in range(count):
   var target: Dictionary={"kind":kind,"index":index}
   if not _target_valid(target): continue
   var screen:=_screen(_target_point(target),30 if kind!="drop" else 0)
   var score:=point.distance_to(screen)
   if score<distance:
    distance=score
    best=target
 selected_target=best
 if not best.is_empty(): _announce(_context_prompt())

func _activate_action(action: String) -> void:
 match action:
  "attack": _attack()
  "interact": _interact()
  "shove": _shove()
  "sneak": sneaking=not sneaking
  "quick0":
   if not survival.equipped.is_empty(): survival.equip("")
   else: survival.equip(_first_item("weapon"))
  "quick1":
   var id:=_first_item("heal")
   if not id.is_empty(): _use_item(id)
  "quick3":
   var id:=_first_item("drink") if thirst>0 else _first_item("food")
   if not id.is_empty(): _use_item(id)
  "quick2": pass
