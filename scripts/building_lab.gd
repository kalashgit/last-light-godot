extends Node2D
## LAST LIGHT / Building Prototype District V1.
## Independent test scene. Does not replace main.tscn or the active house.
## Five original procedural building shells, interactable entrances, camera follow.
const TX := 40.0
const TY := 20.0
const WALL_H := 57.0
const SPEED := 2.8
const RADIUS := 0.20
const SAVELESS := true
var player := Vector2(6.0, 16.5)
var look := Vector2(0, -1)
var buildings: Array[Dictionary] = []
var walls: Array[Dictionary] = []
var doors: Array[Dictionary] = []
var props: Array[Dictionary] = []
var prop_textures: Dictionary = {}
var selected_name := "PROTOTYPE DISTRICT"
var status := "Explore five building prototypes. INTERACT opens nearby doors."
var status_time := 8.0
var stick_owner := -1
var stick := Vector2.ZERO
var stick_center := Vector2.ZERO
var pause_game := false
const MOUSE_ID := -999

func _ready() -> void:
 _build_district()
 _load_prop_textures()
 _position_controls()
 get_viewport().size_changed.connect(_position_controls)
 set_process(true)
 queue_redraw()

func _add_building(label: String, origin: Vector2, footprint: Vector2, palette: Color, layout: String) -> void:
 var b := {"name": label, "rect": Rect2(origin, footprint), "tint": palette, "kind": layout}
 buildings.append(b)
 var x := origin.x
 var y := origin.y
 var w := footprint.x
 var h := footprint.y
 # Camera-facing south wall has a central entrance; all other faces solid.
 _wall(Vector2(x,y), Vector2(x+w,y))
 _wall(Vector2(x,y), Vector2(x,y+h))
 _wall(Vector2(x+w,y), Vector2(x+w,y+h))
 var mid := Vector2(x+w*0.5,y+h)
 _wall(Vector2(x,y+h),mid+Vector2(-0.83,0))
 _door(mid+Vector2(-0.83,0),mid+Vector2(0.83,0),label)
 _wall(mid+Vector2(0.83,0),Vector2(x+w,y+h))
 _populate(b)

func _wall(a: Vector2,b: Vector2) -> void:
 walls.append({"a":a,"b":b})

func _door(a: Vector2,b: Vector2,label: String) -> void:
 doors.append({"a":a,"b":b,"label":label,"open":false})

func _prop(pos: Vector2, name: String, id: String, width: float=0.65, height: float=0.55) -> void:
 props.append({"pos":pos,"name":name,"id":id,"size":Vector2(width,height)})

func _populate(b: Dictionary) -> void:
 var r: Rect2 = b.rect
 var p := r.position
 match String(b.kind):
  "house":
   _prop(p+Vector2(1.1,1.2),"Chair","ll_furniture_dining_chair")
   _prop(p+Vector2(2.8,1.6),"Table","ll_furniture_kitchen_table",1.1,0.8)
   _prop(p+Vector2(5.7,2.0),"Storage","ll_household_storage_box")
   _prop(p+Vector2(2.1,4.5),"Book","ll_household_paperback_book",0.3,0.3)
  "garage":
   _prop(p+Vector2(1.3,1.5),"Tools","ll_tools_claw_hammer")
   _prop(p+Vector2(3.3,2.1),"Storage","ll_household_storage_box")
   _prop(p+Vector2(6.4,3.2),"Planks","ll_crafting_pine_plank",1.1,0.45)
   _prop(p+Vector2(2.5,5.4),"Pipe","ll_crafting_copper_pipe",0.7,0.3)
  "shop":
   for k in range(3):
    _prop(p+Vector2(2.0+k*2.2,2.0),"Display","ll_household_storage_box",0.85,1.2)
   _prop(p+Vector2(2.0,5.7),"Food","ll_food_bean_tin",0.3,0.3)
   _prop(p+Vector2(6.7,5.7),"Water","ll_food_water_bottle",0.3,0.3)
  "station":
   _prop(p+Vector2(2.0,2.0),"Counter","ll_furniture_kitchen_table",1.2,0.7)
   _prop(p+Vector2(5.0,2.0),"Fuel supply","ll_household_storage_box")
   _prop(p+Vector2(3.2,5.6),"Oil","ll_food_cooking_oil",0.3,0.3)
  "outpost":
   _prop(p+Vector2(2.2,2.0),"Supplies","ll_household_storage_box")
   _prop(p+Vector2(6.0,2.0),"First aid","ll_medical_first_aid_case")
   _prop(p+Vector2(4.2,5.0),"Tools","ll_tools_shovel")
   _prop(p+Vector2(9.0,6.0),"Equipment","ll_household_storage_box")

func _build_district() -> void:
 buildings.clear()
 walls.clear()
 doors.clear()
 props.clear()
 # Connected pedestrian paths, with buildings spaced to allow navigation.
 _add_building("HOUSE",Vector2(0,0),Vector2(9,8),Color("657F72"),"house")
 _add_building("GAS STATION",Vector2(13,0),Vector2(10,8),Color("8F8167"),"station")
 _add_building("GARAGE",Vector2(0,20),Vector2(9,8),Color("787F82"),"garage")
 _add_building("SMALL SHOP",Vector2(13,20),Vector2(10,8),Color("789181"),"shop")
 _add_building("MILITARY OUTPOST",Vector2(29,5),Vector2(14,11),Color("6C7966"),"outpost")
 # Outdoor sample props: indicative of future gas station pumps and military yard.
 _prop(Vector2(15.0,10.1),"PUMP (placeholder)","ll_household_storage_box")
 _prop(Vector2(20.0,10.1),"PUMP (placeholder)","ll_household_storage_box")
 _prop(Vector2(33.0,19.0),"Crate","ll_household_storage_box")

func _load_prop_textures() -> void:
 var path := "res://assets/generated/factory/manifest.json"
 if not FileAccess.file_exists(path):
  push_warning("Generated prop manifest unavailable; using placeholders")
  return
 var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(path))
 if not parsed is Dictionary or not parsed.has("objects"):
  return
 var wanted := {}
 for obj in props:
  wanted[String(obj.id)] = true
 for item in parsed.objects:
  if not item is Dictionary or not wanted.has(String(item.get("id",""))):
   continue
  for frame in item.get("frames",[]):
   if frame.get("mode","") == "ground":
    var tex: Texture2D = load("res://assets/generated/factory/" + String(frame.get("file",""))) as Texture2D
    if tex != null:
     prop_textures[String(item.id)] = {"texture":tex,"anchor":Vector2(float(frame.anchor_px[0]),float(frame.anchor_px[1]))}
    break

func _segment_distance(p: Vector2,a: Vector2,b: Vector2) -> float:
 var ab := b-a
 return p.distance_to(a+ab*clampf((p-a).dot(ab)/maxf(ab.length_squared(),0.0001),0.0,1.0))

func _blocked(p: Vector2) -> bool:
 for wall in walls:
  if _segment_distance(p,wall.a,wall.b) < RADIUS+0.08:
   return true
 for door in doors:
  if not door.open and _segment_distance(p,door.a,door.b) < RADIUS+0.08:
   return true
 # The building laboratory uses non-blocking demonstration props until
 # full furniture collision is integrated in the ongoing house task.
 return false

func _move(delta_pos: Vector2) -> void:
 var steps := maxi(1,ceili(delta_pos.length()/0.09))
 for i in range(steps):
  var step := delta_pos/float(steps)
  if not _blocked(player+Vector2(step.x,0)):
   player.x += step.x
  if not _blocked(player+Vector2(0,step.y)):
   player.y += step.y

func _nearby_door() -> int:
 var best := -1
 var distance := 1.55
 for i in range(doors.size()):
  var d: float = _segment_distance(player,doors[i].a,doors[i].b)
  if d < distance:
   best=i
   distance=d
 return best

func _interact() -> void:
 var i := _nearby_door()
 if i < 0:
  status = "Stand closer to a doorway"
 else:
  if doors[i].open and _segment_distance(player,doors[i].a,doors[i].b) < 0.38:
   status = "Step clear of the doorway"
  else:
   doors[i].open = not doors[i].open
   status = "%s entrance %s" % [doors[i].label,"OPEN" if doors[i].open else "CLOSED"]
 status_time = 2.8
 queue_redraw()

func _process(delta: float) -> void:
 if pause_game:
  queue_redraw()
  return
 var direction := stick if stick_owner != -1 else Input.get_vector("ui_left","ui_right","ui_up","ui_down")
 if direction.length() > 0.14:
  var world := Vector2(direction.x/TX+direction.y/TY,direction.y/TY-direction.x/TX).normalized()
  look = world
  _move(world*SPEED*minf(delta,0.05)*minf(1.0,direction.length()))
 status_time = maxf(0.0,status_time-delta)
 queue_redraw()

func _iso(p: Vector2,h: float=0.0) -> Vector2:
 return Vector2((p.x-p.y)*TX,(p.x+p.y)*TY-h)

func _screen(p: Vector2,h: float=0.0) -> Vector2:
 var size := get_viewport_rect().size
 return _iso(p,h)-_iso(player)+size*Vector2(0.5,0.53)

func _quad(a: Vector2,b: Vector2,c: Vector2,d: Vector2,tint: Color) -> void:
 draw_colored_polygon(PackedVector2Array([a,b,c,d]),tint)

func _label(value: String,p: Vector2,font_size: int=13,tint: Color=Color("F4E9CE")) -> void:
 draw_string(ThemeDB.fallback_font,p,value,HORIZONTAL_ALIGNMENT_LEFT,-1,font_size,tint)

func _inside(b: Dictionary) -> bool:
 return (b.rect as Rect2).grow(-0.15).has_point(player)

func _draw_tile(cell: Vector2,tint: Color) -> void:
 _quad(_screen(cell),_screen(cell+Vector2(1,0)),_screen(cell+Vector2(1,1)),_screen(cell+Vector2(0,1)),tint)

func _draw_building(b: Dictionary) -> void:
 var rect: Rect2 = b.rect
 var start := rect.position
 var end := rect.end
 var inside := _inside(b)
 var tint: Color = b.tint
 for y in range(int(start.y),int(end.y)):
  for x in range(int(start.x),int(end.x)):
   _draw_tile(Vector2(x,y),tint.lightened(0.10) if (x+y)%2==0 else tint)
 if inside:
  for prop in props:
   if rect.has_point(prop.pos):
    _draw_prop(prop)
  # Omit camera-facing front/right faces while the player is inside.
  _wall_face(Vector2(start.x,start.y),Vector2(end.x,start.y),WALL_H,tint.darkened(0.26))
  _wall_face(Vector2(start.x,start.y),Vector2(start.x,end.y),WALL_H,tint.darkened(0.18))
 else:
  _wall_face(Vector2(start.x,start.y),Vector2(end.x,start.y),WALL_H,tint.darkened(0.2))
  _wall_face(Vector2(start.x,start.y),Vector2(start.x,end.y),WALL_H,tint.darkened(0.16))
  _wall_face(Vector2(end.x,start.y),end,WALL_H,tint.darkened(0.34))
  _wall_face(Vector2(start.x,end.y),end,WALL_H,tint.darkened(0.27))
  var corners := [
   _screen(start,WALL_H+7),_screen(Vector2(end.x,start.y),WALL_H+7),
   _screen(end,WALL_H+7),_screen(Vector2(start.x,end.y),WALL_H+7)
  ]
  _quad(corners[0],corners[1],corners[2],corners[3],tint.darkened(0.32))
  _label(String(b.name),_screen(start+rect.size*Vector2(0.33,0.35),WALL_H+18),12)
 for door in doors:
  if door.label != b.name:
   continue
  var midpoint: Vector2 = (door.a+door.b)*0.5
  if door.open:
   draw_circle(_screen(midpoint),6,Color("A5E6AD"))
  else:
   _wall_face(door.a,door.b,37,Color("805940"))
  _label("OPEN" if door.open else "DOOR",_screen(midpoint,43),10,Color("EAD7A4"))

func _wall_face(a: Vector2,b: Vector2,height: float,tint: Color) -> void:
 _quad(_screen(a),_screen(b),_screen(b,height),_screen(a,height),tint)
 draw_line(_screen(a,height),_screen(b,height),tint.lightened(0.3),1.3)

func _draw_prop(prop: Dictionary) -> void:
 var p: Vector2 = prop.pos
 var id: String = prop.id
 var point := _screen(p)
 if prop_textures.has(id):
  var data: Dictionary = prop_textures[id]
  draw_texture(data.texture,point-(data.anchor as Vector2))
 else:
  draw_circle(point,8,Color("C6B58D"))
 _label(String(prop.name),point+Vector2(-18,14),9)

func _draw_controls() -> void:
 var size := get_viewport_rect().size
 draw_rect(Rect2(Vector2.ZERO,Vector2(size.x,104)),Color("111E1B",0.9))
 _label("LAST LIGHT / BUILDING LAB",Vector2(14,26),19)
 _label("5 STRUCTURES | WALK + INTERACT | SEPARATE TEST SCENE",Vector2(14,47),11,Color("B6C4B2"))
 if status_time>0:
  _label(status,Vector2(14,75),12)
 draw_circle(stick_center,57,Color("29483C",0.86))
 draw_arc(stick_center,57,0.0,TAU,32,Color("B7C4A4"),2)
 draw_circle(stick_center+stick*33,24,Color("C8BA8F"))
 var action := Vector2(size.x-86,size.y-107)
 draw_circle(action,52,Color("C7AD7B"))
 _label("INTERACT",action-Vector2(38,0),13,Color("17251B"))
 var pause_rect := Rect2(Vector2(size.x-115,12),Vector2(101,35))
 draw_rect(pause_rect,Color("405C4B"))
 _label("RESUME" if pause_game else "PAUSE",Vector2(size.x-104,35),14)

func _draw() -> void:
 var v := get_viewport_rect().size
 draw_rect(Rect2(Vector2.ZERO,v),Color("17271E"))
 for y in range(-8,40):
  for x in range(-8,52):
   var tile := Vector2(x,y)
   _draw_tile(tile,Color("3A5441") if (x+y)%2==0 else Color("3D5845"))
 # Simple roads between the buildings; world positions are decorative only.
 for x in range(-2,48):
  for y in range(12,16):
   _draw_tile(Vector2(x,y),Color("646C68"))
 for x in range(10,13):
  for y in range(-2,31):
   _draw_tile(Vector2(x,y),Color("646C68"))
 for b in buildings:
  _draw_building(b)
 for prop in props:
  if not _is_prop_indoor(prop):
   _draw_prop(prop)
 var actor := _screen(player)
 draw_ellipse(actor+Vector2(0,2),Vector2(9,4),Color(0,0,0,0.48))
 draw_rect(Rect2(actor+Vector2(-6,-26),Vector2(12,20)),Color("478FAA"))
 draw_circle(actor+Vector2(0,-30),6,Color("DFBE9F"))
 _label("YOU",actor+Vector2(-14,-43),12,Color("F0DF9A"))
 _draw_controls()

func _is_prop_indoor(prop: Dictionary) -> bool:
 for b in buildings:
  if (b.rect as Rect2).has_point(prop.pos):
   return true
 return false

func _position_controls() -> void:
 var size := get_viewport_rect().size
 stick_center=Vector2(89,size.y-103)

func _pointer_down(id: int,pos: Vector2) -> void:
 if pos.distance_to(stick_center)<89 and stick_owner==-1 and not pause_game:
  stick_owner=id
  _set_stick(pos)
  return
 var size := get_viewport_rect().size
 if Rect2(Vector2(size.x-115,12),Vector2(101,35)).has_point(pos):
  pause_game=not pause_game
  stick_owner=-1
  stick=Vector2.ZERO
 elif not pause_game and pos.distance_to(Vector2(size.x-86,size.y-107))<57:
  _interact()

func _set_stick(pos: Vector2) -> void:
 stick=(pos-stick_center).limit_length(57)/57
 if stick.length()<0.14:
  stick=Vector2.ZERO

func _input(event: InputEvent) -> void:
 if event is InputEventScreenTouch:
  if event.pressed and not event.canceled:
   _pointer_down(event.index,event.position)
  elif event.index==stick_owner:
   stick_owner=-1
   stick=Vector2.ZERO
 elif event is InputEventScreenDrag:
  if event.index==stick_owner:
   _set_stick(event.position)
 elif event is InputEventMouseButton and event.device!=InputEvent.DEVICE_ID_EMULATION:
  if event.button_index==MOUSE_BUTTON_LEFT:
   if event.pressed:
    _pointer_down(MOUSE_ID,event.position)
   elif stick_owner==MOUSE_ID:
    stick_owner=-1
    stick=Vector2.ZERO
 elif event is InputEventMouseMotion and event.device!=InputEvent.DEVICE_ID_EMULATION and stick_owner==MOUSE_ID:
  _set_stick(event.position)
 elif event is InputEventKey and event.pressed and not event.echo:
  if event.keycode==KEY_E:
   _interact()
  elif event.keycode==KEY_ESCAPE or event.keycode==KEY_P:
   pause_game=not pause_game
