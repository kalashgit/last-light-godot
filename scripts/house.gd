extends Node2D
## LAST LIGHT house survival candidate — original fixed-isometric 2D, schema-1 compatible.
## Gameplay, interaction targets and visual mesh share the same door/wall positions.
const TX := 40.0
const TY := 20.0
const WALL_HEIGHT := 63.0
const PLAYER_RADIUS := 0.19
const HOME := Rect2(0.0, 0.0, 9.0, 8.0)
const HouseArt := preload("res://scripts/house_art.gd")
var art := HouseArt.new()
var world_art_debug := false
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
const INDOOR_ZOOM := 2.20
const OUTDOOR_ZOOM := 1.0
const MIN_ZOOM := 0.75
const MAX_ZOOM := 3.25
const ZOOM_STEP := 0.25
var camera_zoom := 1.0
var zoom_adjust := 0.0
var factory_icon_textures: Dictionary = {}
var held_sprites: Dictionary = {}
var selected_target: Dictionary = {}
var drops: Array[Dictionary] = []
const LootBuilder := preload("res://scripts/loot_builder.gd")
var loot_builder: CanvasLayer
var builder_open := false
var pending_spawn_id := ""
var golden_textures: Dictionary = {}
const SurvivalState := preload("res://scripts/survival_state.gd")
var survival := SurvivalState.new()
const HouseNavigation := preload("res://scripts/house_navigation.gd")
var navigation := HouseNavigation.new()
var save_blocked := false
var recovery_available := false
var exhausted := false
var last_save_error: Error = OK
const SAVE_VERSION := 2
const HUNGER_RATE := .025
const THIRST_RATE := .045
const CONTAINER_LOOT := {
 "house.kitchen.counter": {"ll_food_bean_tin":2,"ll_food_water_bottle":2},
 "house.bedroom.bed": {"ll_medical_sterile_bandage":1,"ll_household_flashlight":1},
 "house.living.sofa": {"ll_tools_claw_hammer":1,"ll_food_bean_tin":1},
 "house.bathroom.medicine": {"ll_medical_sterile_bandage":3,"ll_medical_first_aid_case":1},
 "house.bedroom.chest": {"ll_tools_hatchet":1,"ll_crafting_pine_plank":2}
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
const SAVE_PATH := "user://last_light_survival_v2.json"
const LEGACY_SAVE_PATH := "user://last_light_v04.json"
var paused := false
var autosave_time := 0.0
var stick_center := Vector2.ZERO
var stick_radius := 62.0
var attack_cooldown := 0.0

func _ready() -> void:
 texture_filter=CanvasItem.TEXTURE_FILTER_NEAREST
 art.setup(self)
 _load_controls()
 _make_house()
 _layout_controls()
 var load_status:=_load_game()
 if load_status==ERR_FILE_NOT_FOUND and FileAccess.file_exists(LEGACY_SAVE_PATH):
  load_status=_load_game(LEGACY_SAVE_PATH)
  if load_status==OK and not FileAccess.file_exists(SAVE_PATH+".schema1.bak"):
   if DirAccess.copy_absolute(LEGACY_SAVE_PATH,SAVE_PATH+".schema1.bak")!=OK:
    _announce("Legacy file retained; could not create extra migration backup")
 if load_status not in [OK,ERR_FILE_NOT_FOUND]:
  var backup_status:=_load_game(SAVE_PATH+".bak")
  save_blocked=true
  recovery_available=backup_status==OK
  _announce("Original save retained; backup loaded" if backup_status==OK else "Save could not load — original file retained")
  paused=true
 get_viewport().size_changed.connect(_on_viewport_resized)
 camera_zoom = _zoom_target()
 loot_builder = LootBuilder.new()
 add_child(loot_builder)
 loot_builder.setup(self)
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
 navigation.rebuild(self)

func _segment_distance(p: Vector2, a: Vector2, b: Vector2) -> float:
 var line := b - a
 var t: float = clampf((p - a).dot(line) / maxf(line.length_squared(), .00001), 0, 1)
 return p.distance_to(a + line * t)

func _blocked_static(p: Vector2, radius: float = PLAYER_RADIUS) -> bool:
 if not Rect2(-7,-7,24,24).grow(-radius).has_point(p): return true
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
 if paused or health<=0: return
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
 # The HUD stays at native size while the world eases into indoor/outdoor zoom.
 camera_zoom = move_toward(camera_zoom, _zoom_target(), 3.0 * clampf(delta,0.0,0.25))
 if paused or inventory_open or builder_open or health<=0:
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
 if stamina<=.01: exhausted=true
 if stamina>=20: exhausted=false
 sprinting=not exhausted and (sprint_held or keyboard_sprint) and not sneaking and direction.length()>.01 and stamina>0
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
  var chase: Vector2=navigation.direction(i,infected[i],player,dt)
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

func _camera_pivot() -> Vector2:
 return get_viewport_rect().size * Vector2(.50, .58 if HOME.has_point(player) else .70)

func _zoom_target() -> float:
 return clampf((INDOOR_ZOOM if HOME.has_point(player) else OUTDOOR_ZOOM) + zoom_adjust, MIN_ZOOM, MAX_ZOOM)

func _adjust_zoom(delta: float) -> void:
 if health<=0 or paused or inventory_open or builder_open: return
 zoom_adjust = clampf(zoom_adjust + delta, MIN_ZOOM-INDOOR_ZOOM, MAX_ZOOM-INDOOR_ZOOM)
 camera_zoom = _zoom_target()
 _save_controls()
 _announce("ZOOM %d%%" % roundi(camera_zoom * 100.0))
 queue_redraw()

func _world_to_view(p: Vector2, height: float = 0.0) -> Vector2:
 var anchor := _camera_pivot()
 return anchor + (_screen(p,height)-anchor)*camera_zoom

func _view_to_world(point: Vector2) -> Vector2:
 var anchor := _camera_pivot()
 var raw := anchor + (point-anchor)/maxf(camera_zoom,0.001)
 var projected := raw-anchor+_iso(player)
 return Vector2((projected.x/TX+projected.y/TY)*.5,(projected.y/TY-projected.x/TX)*.5)

func _poly(points: PackedVector2Array, color: Color) -> void:
 draw_colored_polygon(points, color)

func _quad(a: Vector2, b: Vector2, c: Vector2, d: Vector2, color: Color) -> void:
 _poly(PackedVector2Array([a, b, c, d]), color)

func _text(label: String, point: Vector2, size: int = 16, color: Color = Color("eadcb8")) -> void:
 draw_string(ThemeDB.fallback_font, point, label, HORIZONTAL_ALIGNMENT_LEFT, -1, size, color)

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
  if not survival.equipped.is_empty():
   var direction:=posmod(roundi(facing.angle()/TAU*8),8)
   var held:=_held_frame(survival.equipped,direction)
   if not held.is_empty():
    var grip:=shoulder+side*10+Vector2(0,18)+forward*(18 if attack_cooldown>.25 else 3)
    draw_texture(held.texture,grip-held.anchor)

func draw_ellipse_approx(center: Vector2, radii: Vector2, color: Color) -> void:
 var vertices := PackedVector2Array()
 for i in range(16):
  var a := float(i) / 16 * TAU
  vertices.append(center + Vector2(cos(a) * radii.x, sin(a) * radii.y))
 _poly(vertices, color)

func _draw_ui() -> void:
 hud.draw(self)

func _alive_zombies() -> int:
 var alive := 0
 for hp in zombie_health:
  if hp > 0:
   alive += 1
 return alive

func _draw() -> void:
 var anchor := _camera_pivot()
 draw_set_transform(anchor*(1.0-camera_zoom),0.0,Vector2.ONE*camera_zoom)
 art.draw_world(self)
 if world_art_debug: art.draw_inspector(self)
 draw_set_transform(Vector2.ZERO,0.0,Vector2.ONE)
 _draw_ui()

func _tap(point: Vector2) -> void:
 _layout_controls()
 if health <= 0:
  if control_rects.dead_restart.has_point(point): _restart_game()
  return
 if control_rects.inventory.has_point(point):
  if save_blocked: return
  _set_inventory(not inventory_open)
  return
 if inventory_open:
  _inventory_tap(point)
  return
 if control_rects.pause.has_point(point):
  _set_paused(not paused)
  return
 if paused:
  if control_rects.resume.has_point(point):
   if save_blocked:
    if recovery_available: _recover_backup()
    else: _restart_game()
   else: _set_paused(false)
  elif save_blocked and control_rects.recovery_reset.has_point(point): _restart_game()
  elif not save_blocked:
   if control_rects.deadzone_down.has_point(point): _set_dead_zone(joystick_dead_zone-.02)
   elif control_rects.deadzone_up.has_point(point): _set_dead_zone(joystick_dead_zone+.02)
  return
 for action in ["zoom_in","zoom_out","attack","interact","shove","sneak","quick0","quick1","quick2","quick3"]:
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
 if loot_builder != null and loot_builder.over_launcher(point): return
 if panel_touches.has(pointer) or joystick_touch == pointer: return
 if not pending_spawn_id.is_empty():
  var chosen := pending_spawn_id
  if _place_builder_item(chosen, point):
   pending_spawn_id = ""
   _announce("Placed " + survival.name_for(chosen))
  else:
   _announce("Blocked placement: tap clear ground")
  return
 _layout_controls()
 if health <= 0 or paused or inventory_open:
  panel_touches[pointer] = "modal"
  _tap(point)
  return
 for action in ["inventory","pause","zoom_in","zoom_out","attack","interact","shove","sprint","sneak","quick0","quick1","quick2","quick3"]:
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
 if OS.is_debug_build() and event is InputEventKey and event.pressed and not event.echo and event.keycode==KEY_F8:
  world_art_debug=not world_art_debug
  queue_redraw()
  return
 if builder_open: return
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
  if event.pressed and not event.echo and event.keycode==KEY_B and health>0 and not paused and not inventory_open:
   loot_builder.set_open(not builder_open)
   return
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
    KEY_EQUAL: _adjust_zoom(ZOOM_STEP)
    KEY_MINUS: _adjust_zoom(-ZOOM_STEP)

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
 if save_blocked and not value: return
 paused = value
 _clear_pointers()
 if paused:
  _save_game()
 queue_redraw()

func _restart_game() -> void:
 if save_blocked and FileAccess.file_exists(SAVE_PATH):
  if DirAccess.copy_absolute(SAVE_PATH,SAVE_PATH+".rejected.bak")!=OK:
   _announce("Could not preserve old save; restart cancelled")
   return
  if DirAccess.remove_absolute(SAVE_PATH)!=OK: return
 save_blocked=false
 recovery_available=false
 exhausted=false
 _make_house()
 pending_spawn_id = ""
 if loot_builder != null: loot_builder.set_open(false)
 survival.restore({"inventory":{},"equipped":""})
 stamina=100; hunger=0; thirst=0
 inventory_open=false; sneaking=false
 selected_target={}; drops.clear()
 shove_cooldown=0; recovery_delay=0
 facing=Vector2(0,1)
 inventory_page=0
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
 if save_blocked and path==SAVE_PATH:
  last_save_error=ERR_INVALID_DATA
  return last_save_error
 var door_states: Array=[]
 for door in doors: door_states.append({"open":door.open,"health":door.health})
 var searched: Array=[]
 var containers: Dictionary={}
 for i in range(items.size()):
  if i<4: searched.append(items[i].searched)
  if items[i].get("container",false): containers[items[i].id]=items[i].searched
 var enemies: Array=[]
 for i in range(infected.size()): enemies.append({"x":infected[i].x,"y":infected[i].y,"health":zombie_health[i]})
 var ground: Array=[]
 for drop in drops: ground.append({"id":drop.id,"count":drop.count,"x":drop.pos.x,"y":drop.pos.y})
 var data: Dictionary={"version":SAVE_VERSION,"player":[player.x,player.y],"health":health,"supplies":supplies,"doors":door_states,"searched":searched,"enemies":enemies,"stamina":stamina,"hunger":hunger,"thirst":thirst,"survival":survival.snapshot(),"containers":containers,"drops":ground}
 # Never overwrite unknown/corrupt prior data, including a future schema.
 if FileAccess.file_exists(path):
  if _load_game(path,true)!=OK:
   _announce("Save protected — current file retained")
   last_save_error=ERR_INVALID_DATA
   return last_save_error
  var old: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(path))
  var archived: String=path+".schema1.bak" if old.version==1 else path+".bak"
  if old.version!=1 or not FileAccess.file_exists(archived):
   var backup_error:=DirAccess.copy_absolute(path,archived)
   if backup_error!=OK:
    last_save_error=backup_error
    return backup_error
 var file:=FileAccess.open(path+".tmp",FileAccess.WRITE)
 if file==null:
  last_save_error=FileAccess.get_open_error()
  return last_save_error
 file.store_string(JSON.stringify(data))
 file.flush()
 var error:=file.get_error()
 file.close()
 if error==OK: error=DirAccess.rename_absolute(path+".tmp",path)
 last_save_error=error
 if error!=OK: _announce("Could not save progress; prior save retained")
 return error

func _valid_number(value: Variant, low: float, high: float) -> bool:
 return (value is float or value is int) and is_finite(float(value)) and float(value) >= low and float(value) <= high

func _integer(value: Variant, low: int, high: int) -> bool:
 return _valid_number(value,low,high) and floorf(float(value))==float(value)

func _load_game(path: String = SAVE_PATH, validate_only: bool = false) -> Error:
 if not FileAccess.file_exists(path): return ERR_FILE_NOT_FOUND
 var file:=FileAccess.open(path,FileAccess.READ)
 if file==null: return FileAccess.get_open_error()
 if file.get_length()>262144: return ERR_INVALID_DATA
 var parser:=JSON.new()
 if parser.parse(file.get_as_text())!=OK: return ERR_INVALID_DATA
 var data: Variant=parser.data
 if not data is Dictionary or not _integer(data.get("version"),1,2): return ERR_INVALID_DATA
 var position: Variant=data.get("player")
 if not position is Array or position.size()!=2 or not _valid_number(position[0],-100,100) or not _valid_number(position[1],-100,100): return ERR_INVALID_DATA
 if not _valid_number(data.get("health"),0,100) or not _integer(data.get("supplies"),0,100000): return ERR_INVALID_DATA
 var door_states: Variant=data.get("doors")
 var searched: Variant=data.get("searched")
 var enemies: Variant=data.get("enemies")
 if not door_states is Array or door_states.size()!=doors.size() or not searched is Array or searched.size()!=4 or not enemies is Array or enemies.size()!=infected.size(): return ERR_INVALID_DATA
 for state in door_states:
  if not state is Dictionary or not state.get("open") is bool or not _valid_number(state.get("health"),0,45): return ERR_INVALID_DATA
 for flag in searched:
  if not flag is bool: return ERR_INVALID_DATA
 for enemy in enemies:
  if not enemy is Dictionary or not _valid_number(enemy.get("x"),-100,100) or not _valid_number(enemy.get("y"),-100,100) or not _integer(enemy.get("health"),0,3): return ERR_INVALID_DATA
 var inventory_state: Dictionary={"inventory":{},"equipped":""}
 if data.version==1:
  if not _integer(data.supplies,0,4): return ERR_INVALID_DATA
  if data.supplies>0:
   var count:=int(data.supplies)
   inventory_state={"inventory":{"ll_food_bean_tin":count,"ll_food_water_bottle":count,"ll_medical_sterile_bandage":count},"equipped":""}
  if not survival.validate(inventory_state): return ERR_INVALID_DATA
 var ground: Array[Dictionary]=[]
 var flags: Dictionary={}
 if data.version==2:
  for key in ["stamina","hunger","thirst"]:
   if not _valid_number(data.get(key),0,100): return ERR_INVALID_DATA
  if not survival.validate(data.get("survival")): return ERR_INVALID_DATA
  inventory_state=data.survival
  var containers: Variant=data.get("containers")
  var expected: Array=[]
  for item in items:
   if item.get("container",false): expected.append(item.id)
  if not containers is Dictionary or containers.size()!=expected.size(): return ERR_INVALID_DATA
  for id in expected:
   if not containers.get(id) is bool: return ERR_INVALID_DATA
  flags=containers
  for i in range(4):
   if flags[items[i].id]!=searched[i]: return ERR_INVALID_DATA
  var raw_drops: Variant=data.get("drops")
  if not raw_drops is Array or raw_drops.size()>128: return ERR_INVALID_DATA
  for drop in raw_drops:
   if not drop is Dictionary or not drop.get("id") is String or not survival.definitions.has(drop.id): return ERR_INVALID_DATA
   if not _integer(drop.get("count"),1,int(survival.definitions[drop.id].stack_max)) or not _valid_number(drop.get("x"),-100,100) or not _valid_number(drop.get("y"),-100,100): return ERR_INVALID_DATA
   ground.append({"id":drop.id,"count":int(drop.count),"pos":Vector2(drop.x,drop.y)})
 if validate_only: return OK
 # Apply only after every legacy and extended value has passed validation.
 survival.restore(inventory_state)
 player=Vector2(position[0],position[1])
 if _blocked_static(player):
  player=_clear_saved_position(player)
  _announce("Saved location obstructed — moved to nearby clear ground")
 health=float(data.health)
 supplies=int(data.supplies)
 stamina=float(data.stamina) if data.version==2 else 100.0
 hunger=float(data.hunger) if data.version==2 else 0.0
 thirst=float(data.thirst) if data.version==2 else 0.0
 for i in range(doors.size()):
  doors[i].open=door_states[i].open
  doors[i].health=float(door_states[i].health)
 for i in range(items.size()):
  items[i].searched=searched[i] if i<4 else not items[i].get("container",false)
  if flags.has(items[i].id): items[i].searched=flags[items[i].id]
 for i in range(infected.size()):
  infected[i]=Vector2(enemies[i].x,enemies[i].y)
  zombie_health[i]=int(enemies[i].health)
  if zombie_health[i]>0 and _blocked_static(infected[i],.17): infected[i]=_clear_saved_position(infected[i])
  zombies_hit_time[i]=0.0
 drops=ground
 for drop in drops:
  if not String(drop.id).begins_with("ll_golden_"):
   art._cache(survival.definitions[drop.id].art_id)
 selected_target={}
 attack_cooldown=0; shove_cooldown=0; recovery_delay=0
 navigation.paths.clear(); navigation.timers.clear()
 _clear_pointers()
 if data.version==1: _announce("Legacy progress loaded; caches supplied food, water and bandages")
 return OK

func _set_inventory(value: bool) -> void:
 if save_blocked: return
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
   var score: float=_interaction_distance(target)
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
 var page: Array=rows.slice(inventory_page*6,inventory_page*6+6)
 for row in page:
  var definition: Dictionary=survival.definitions[row.id]
  row.detail="%s · %.2f kg%s" % [definition.category,float(definition.weight_kg)*int(row.count)," · equipped" if survival.equipped==row.id else ""]
 return page

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
  _announce(("Ate " if kind=="food" else "Drank " if kind=="drink" else "Applied ")+survival.name_for(id))
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
 if not id.begins_with("ll_golden_"):
  art._cache(survival.definitions[id].art_id)
 selected_target={}
 _announce("Dropped "+survival.name_for(id))
 _save_game()
 return true

func _draw_drop(index: int) -> void:
 var drop: Dictionary=drops[index]
 var id: String=survival.definitions[drop.id].art_id
 if art.world_art.is_world_ready(id):
  var meta: Dictionary=art.world_art.lookup(id)
  var footprint:=Vector2(meta.ground_footprint_m[0],meta.ground_footprint_m[1])
  art.world_art.contact_shadow(self,drop.pos,footprint)
  art._sprite(self,id,drop.pos)
 else:
  art.world_art.draw_marker(self,drop.pos)
 if player.distance_to(drop.pos)<1.5:
  draw_arc(_screen(drop.pos),3,0,TAU,12,Color("c2b98e"),1,false)

func _golden_icon(id: String) -> Texture2D:
 if not survival.definitions.has(id): return null
 if not id.begins_with("ll_golden_"): return null
 if not golden_textures.has(id):
  var path: String = str(survival.definitions[id].get("icon_path", ""))
  golden_textures[id] = load("res://" + path) if not path.is_empty() else null
 return golden_textures[id]

## Inventory thumbnail adapter: Golden 40 icon first, then the original factory
## "icon" frame for legacy survival items (ported from PR #18). Cached; null is safe.
func _item_icon(id: String) -> Texture2D:
 var golden := _golden_icon(id)
 if golden != null: return golden
 if factory_icon_textures.has(id): return factory_icon_textures[id]
 var icon: Texture2D = null
 var definition: Dictionary = survival.definitions.get(id, {})
 var art_id := str(definition.get("art_id", id))
 if art.catalog.has(art_id):
  for frame in art.catalog[art_id].get("frames", []):
   if str(frame.get("mode", "")) == "icon":
    var path := "res://assets/generated/factory/" + str(frame.get("file", ""))
    if ResourceLoader.exists(path): icon = load(path) as Texture2D
    break
 factory_icon_textures[id] = icon
 return icon

func _spawn_golden_item(id: String, position: Vector2, count: int = 1) -> bool:
 if builder_open or paused or inventory_open or save_blocked or health<=0: return false
 if not id.begins_with("ll_golden_") or not survival.definitions.has(id): return false
 if count<1 or count>int(survival.definitions[id].stack_max) or drops.size()>=128: return false
 if not Rect2(-6.5,-6.5,23,23).has_point(position) or _blocked(position, 0.14): return false
 if _golden_icon(id)==null: return false
 drops.append({"id":id,"count":count,"pos":position})
 selected_target={}
 if _save_game()!=OK:
  drops.pop_back()
  return false
 _announce("Spawned " + survival.name_for(id))
 queue_redraw()
 return true

func _builder_spawn_near(id: String) -> bool:
 for distance in [0.65, 0.95, 1.35, 1.8]:
  for direction in [Vector2(0,1),Vector2(1,0),Vector2(-1,0),Vector2(0,-1)]:
   var p: Vector2=player + direction*distance
   if not _blocked(p,0.14) and _spawn_golden_item(id,p):
    return true
 _announce("No clear placement nearby")
 return false

func _place_builder_item(id: String, point: Vector2) -> bool:
 return _spawn_golden_item(id,_view_to_world(point),1)


func _select_world_target(point: Vector2) -> void:
 var best: Dictionary={}
 var distance:=60.0
 for kind in ["door","container","drop"]:
  var count: int=doors.size() if kind=="door" else items.size() if kind=="container" else drops.size()
  for index in range(count):
   var target: Dictionary={"kind":kind,"index":index}
   if not _target_valid(target): continue
   var screen:=_world_to_view(_target_point(target),30 if kind!="drop" else 0)
   var score:=point.distance_to(screen)
   if score<distance:
    distance=score
    best=target
 selected_target=best
 if not best.is_empty(): _announce(_context_prompt())

func _activate_action(action: String) -> void:
 match action:
  "zoom_in": _adjust_zoom(ZOOM_STEP)
  "zoom_out": _adjust_zoom(-ZOOM_STEP)
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

func _clear_saved_position(position: Vector2) -> Vector2:
 var center:=position.clamp(Vector2(-6.5,-6.5),Vector2(16.5,16.5))
 for radius in range(15):
  for y in range(-radius,radius+1):
   for x in range(-radius,radius+1):
    var candidate:=center+Vector2(x,y)*.25
    if not _blocked(candidate): return candidate
 return Vector2(4.9,9.35)

func _recover_backup() -> bool:
 if not recovery_available or _load_game(SAVE_PATH+".bak",true)!=OK: return false
 if FileAccess.file_exists(SAVE_PATH) and DirAccess.copy_absolute(SAVE_PATH,SAVE_PATH+".rejected.bak")!=OK: return false
 if DirAccess.copy_absolute(SAVE_PATH+".bak",SAVE_PATH)!=OK: return false
 if _load_game()!=OK: return false
 save_blocked=false
 recovery_available=false
 _set_paused(false)
 _announce("Backup restored; original retained as rejected backup")
 return true

func _held_frame(id: String, direction: int) -> Dictionary:
 # Golden 40 artwork is an inventory icon, not an authored held animation.
 if not art.catalog.has(id): return {}
 var key:=id+"/%d"%direction
 if not held_sprites.has(key):
  for frame in art.catalog[id].frames:
   if frame.mode=="held" and int(frame.angle_degrees)==direction*45:
    held_sprites[key]={"texture":load("res://assets/generated/factory/"+frame.file),"anchor":Vector2(frame.anchor_px[0],frame.anchor_px[1])}
    break
 return held_sprites.get(key,{})

func _load_controls() -> void:
 var config:=ConfigFile.new()
 if config.load("user://last_light_controls.cfg")==OK:
  var value: Variant=config.get_value("touch","dead_zone",.14)
  if _valid_number(value,.05,.35): joystick_dead_zone=float(value)
  var desired: Variant=config.get_value("camera","zoom_offset",0.0)
  if _valid_number(desired,-1.45,1.05): zoom_adjust=float(desired)

func _save_controls() -> void:
 var config := ConfigFile.new()
 config.set_value("touch","dead_zone",joystick_dead_zone)
 config.set_value("camera","zoom_offset",zoom_adjust)
 if config.save("user://last_light_controls.cfg")!=OK: _announce("Could not save controls")

func _set_dead_zone(value: float) -> void:
 joystick_dead_zone=clampf(value,.05,.35)
 _clear_pointers()
 _save_controls()
 queue_redraw()

func _interaction_distance(target: Dictionary) -> float:
 if target.kind=="door": return _segment_distance(player,doors[target.index].a,doors[target.index].b)
 if target.kind=="container":
  var r:=Rect2(items[target.index].pos,items[target.index].size)
  return player.distance_to(player.clamp(r.position,r.end))
 return player.distance_to(drops[target.index].pos)
