extends Node2D
## Material Kit V1 — reusable house/garage visual acceptance scene.
## Separate from playable main scene and current Codex HUD work.
const MaterialArt := preload("res://scripts/building_material_renderer.gd")
const TX := 40.0
const TY := 20.0
const MOVE_SPEED := 2.5
const PLAYER_R := .20
var player := Vector2(4.7,10.0)
var last_face := Vector2(0,-1)
var structures: Array[Dictionary] = []
var segments: Array[Dictionary] = []
var doorways: Array[Dictionary] = []
var stick_touch := -1
var stick := Vector2.ZERO
var stick_center := Vector2.ZERO
var show_roofs := true
var show_grime := true
var material_choice := 0
var paused := false
var info := "Walk into a building. INTERACT opens doors."
var info_timer := 5.0
const MOUSE_ID := -1000

func _ready() -> void:
 _init_buildings()
 _controls_resize()
 get_viewport().size_changed.connect(_controls_resize)
 set_process(true)
 queue_redraw()

func _init_buildings() -> void:
 structures.clear()
 segments.clear()
 doorways.clear()
 _add_structure("RESIDENTIAL HOUSE",Vector2(0,0),Vector2(9,8),"plaster_cream","shingle_asphalt")
 _add_structure("GARAGE / WORKSHOP",Vector2(14,0),Vector2(9,8),"concrete_block","shingle_asphalt")
 # Additional interior partitions for the house demonstrate material swaps.
 _wall(Vector2(4,0),Vector2(4,3),"plaster_cream",false)
 _wall(Vector2(0,4),Vector2(2,4),"plaster_cream",false)
 _wall(Vector2(3.3,4),Vector2(4,4),"plaster_cream",false)
 _door(Vector2(2,4),Vector2(3.3,4),"LIVING / KITCHEN",false)
 _wall(Vector2(4,4),Vector2(9,4),"plaster_cream",false)
 # Garage: partial partition separating tool storage from main bay.
 _wall(Vector2(14,3),Vector2(17,3),"concrete_block",false)
 _wall(Vector2(18.5,3),Vector2(20,3),"concrete_block",false)
 _door(Vector2(17,3),Vector2(18.5,3),"STORAGE",false)

func _add_structure(name: String, origin: Vector2, footprint: Vector2, material: String, roof_type: String) -> void:
 structures.append({"name":name,"bounds":Rect2(origin,footprint),"wall":material,"roof":roof_type})
 var x:=origin.x
 var y:=origin.y
 var w:=footprint.x
 var h:=footprint.y
 # Per-cell wall segments permit windows, door holes and material detail.
 for i in range(int(w)):
  _wall(Vector2(x+i,y),Vector2(x+i+1,y),material,true, i==2 or i==int(w)-3)
 for j in range(int(h)):
  _wall(Vector2(x,y+j),Vector2(x,y+j+1),material,true, j==3)
  _wall(Vector2(x+w,y+j),Vector2(x+w,y+j+1),material,true, j==2)
 var gap_start:=x+floorf(w*.5)-1.0
 var gap_end:=gap_start+2.0
 for i in range(int(w)):
  var ax:=x+i
  if ax>=gap_start and ax<gap_end:
   continue
  var shopfront := (name=="SMALL SHOP" or name=="GAS STATION") and (i==1 or i==int(w)-2)
  _wall(Vector2(ax,y+h),Vector2(ax+1,y+h),material,true,shopfront)
 _door(Vector2(gap_start,y+h),Vector2(gap_end,y+h),name,name.begins_with("GARAGE"))

func _wall(a: Vector2,b: Vector2,mat: String,exterior: bool,window: bool=false) -> void:
 segments.append({"a":a,"b":b,"material":mat,"exterior":exterior,"window":window})

func _door(a: Vector2,b: Vector2,name: String,garage: bool) -> void:
 doorways.append({"a":a,"b":b,"name":name,"garage":garage,"open":false})

func _screen(p: Vector2,h: float=0.0) -> Vector2:
 return Vector2((p.x-p.y)*TX,(p.x+p.y)*TY-h)-Vector2((player.x-player.y)*TX,(player.x+player.y)*TY)+get_viewport_rect().size*Vector2(.5,.55)

func _is_inside(rect: Rect2) -> bool:
 return rect.grow(-.12).has_point(player)

func _segment_distance(p: Vector2,a: Vector2,b: Vector2) -> float:
 var line:=b-a
 var t:=clampf((p-a).dot(line)/maxf(.00001,line.length_squared()),0.0,1.0)
 return p.distance_to(a+line*t)

func _is_blocked(p: Vector2) -> bool:
 for segment in segments:
  if _segment_distance(p,segment.a,segment.b)<PLAYER_R+.07:
   return true
 for door in doorways:
  if not door.open and _segment_distance(p,door.a,door.b)<PLAYER_R+.07:
   return true
 return false

func _walk(delta_position: Vector2) -> void:
 var count:=maxi(1,ceili(delta_position.length()/.10))
 for i in range(count):
  var d:=delta_position/float(count)
  if not _is_blocked(player+Vector2(d.x,0)):
   player.x+=d.x
  if not _is_blocked(player+Vector2(0,d.y)):
   player.y+=d.y

func _interact() -> void:
 var closest:=-1
 var best:=1.55
 for i in range(doorways.size()):
  var door:=doorways[i]
  var d:=_segment_distance(player,door.a,door.b)
  if d<best:
   closest=i
   best=d
 if closest==-1:
  _notice("Move closer to a doorway.")
  return
 var door:=doorways[closest]
 if door.open and _segment_distance(player,door.a,door.b)<.35:
  _notice("Step away from the doorway to close.")
  return
 door.open=not door.open
 _notice(String(door.name)+(" OPEN" if door.open else " CLOSED"))

func _notice(text: String) -> void:
 info=text
 info_timer=3.0
 queue_redraw()

func _process(delta: float) -> void:
 if paused:
  return
 var key_dir:=Input.get_vector("ui_left","ui_right","ui_up","ui_down")
 var direction:=stick if stick_touch!=-1 else key_dir
 if direction.length()>.14:
  var motion:=Vector2(direction.x/TX+direction.y/TY,direction.y/TY-direction.x/TX).normalized()
  last_face=motion
  _walk(motion*_movement_speed()*minf(delta,.05)*minf(direction.length(),1))
 info_timer=maxf(0.0,info_timer-delta)
 queue_redraw()

func _movement_speed() -> float:
 return MOVE_SPEED

func _draw_ground() -> void:
 var sz:=get_viewport_rect().size
 draw_rect(Rect2(Vector2.ZERO,sz),Color("253c32"))
 for y in range(-3,17):
  for x in range(-4,28):
   var p:=Vector2(x,y)
   if _screen(p).distance_to(sz*.5)>maxf(sz.x,sz.y)*1.25:
    continue
   var corners:=[_screen(p),_screen(p+Vector2(1,0)),_screen(p+Vector2(1,1)),_screen(p+Vector2(0,1))]
   MaterialArt.floor_tile(self,corners[0],corners[1],corners[2],corners[3],"concrete_stained" if y>=9 and y<=11 else "wood_oak" if (x+y)%7==0 else "concrete_stained",x,y)

func _floor_material(b: Dictionary, x: int, y: int) -> String:
 if b.name=="RESIDENTIAL HOUSE":
  return "tile_ceramic" if x<4 and y<4 else "wood_oak"
 return "concrete_stained"

func _draw_building(b: Dictionary) -> void:
 var box: Rect2=b.bounds
 var inside:=_is_inside(box)
 # House: kitchen ceramic, living/bedroom wood. Garage concrete.
 for y in range(int(box.position.y),int(box.end.y)):
  for x in range(int(box.position.x),int(box.end.x)):
   var p:=Vector2(x,y)
   var floor_id:=_floor_material(b,x,y)
   var v:=[_screen(p),_screen(p+Vector2(1,0)),_screen(p+Vector2(1,1)),_screen(p+Vector2(0,1))]
   MaterialArt.floor_tile(self,v[0],v[1],v[2],v[3],floor_id,x,y)
   if b.name=="RESIDENTIAL HOUSE" and x==4 and y<4:
    MaterialArt.transition(self,v[0],v[1],v[2],v[3])
 if inside:
  _draw_default_furniture(b)
 # Structural walls belong to their owning house, not to visual materials.
 for s in segments:
  var a: Vector2=s.a
  var c: Vector2=s.b
  if not box.grow(.05).has_point(a.lerp(c,.5)):
   continue
  var south:=absf(a.y-box.end.y)<.01 and absf(c.y-box.end.y)<.01
  var east:=absf(a.x-box.end.x)<.01 and absf(c.x-box.end.x)<.01
  if inside and s.exterior and (south or east):
   continue
  if s.window:
   MaterialArt.window(self,_screen(a),_screen(c),60 if s.exterior else 48,String(s.material))
  else:
   MaterialArt.wall_segment(self,_screen(a),_screen(c),60 if s.exterior else 46,String(s.material))
  if show_grime and int(a.x+a.y)%5==0:
   MaterialArt.damaged_overlay(self,_screen(a.lerp(c,.48),14),.8)
 for door in doorways:
  var a: Vector2=door.a
  var c: Vector2=door.b
  if not box.grow(.05).has_point(a.lerp(c,.5)):
   continue
  MaterialArt.door(self,_screen(a),_screen(c),door.open,door.garage)
  var label_point:=_screen(a.lerp(c,.5),63)
  _text("OPEN" if door.open else "INTERACT",label_point,11)
 # Exterior-only roof: live cutaway when the survivor enters.
 if not inside and show_roofs:
  var z:=68.0
  MaterialArt.roof(self,_screen(box.position,z),_screen(Vector2(box.end.x,box.position.y),z),_screen(box.end,z),_screen(Vector2(box.position.x,box.end.y),z),String(b.roof))
  _text(String(b.name),_screen(box.position+box.size*Vector2(.30,.37),78),12)
 if inside:
  _text("INSIDE: "+String(b.name),_screen(box.position+box.size*Vector2(.23,.12),74),12)

func _draw_default_furniture(b: Dictionary) -> void:
 # Material Kit V1's historical shape previews; V2 replaces these with recipes.
 if b.name=="RESIDENTIAL HOUSE":
  _furniture(Vector2(1.6,1.5),Vector2(1.6,.7),"COUNTER",Color("877e71"))
  _furniture(Vector2(6.3,2.0),Vector2(1.5,1),"BED",Color("657c8a"))
  _furniture(Vector2(1.2,6.3),Vector2(2.0,.7),"SOFA",Color("937766"))
 else:
  _furniture(Vector2(15.4,1.5),Vector2(2.4,.7),"BENCH",Color("8f8c7c"))
  _furniture(Vector2(20,4.5),Vector2(1.3,.8),"STORAGE",Color("9a937f"))

func _furniture(p: Vector2,dim: Vector2,name: String,tint: Color) -> void:
 var a:=_screen(p)
 var b:=_screen(p+Vector2(dim.x,0))
 var c:=_screen(p+dim)
 var d:=_screen(p+Vector2(0,dim.y))
 var h:=19.0
 draw_colored_polygon(PackedVector2Array([a,b,c,d]),tint.darkened(.27))
 draw_colored_polygon(PackedVector2Array([a-Vector2(0,h),b-Vector2(0,h),c-Vector2(0,h),d-Vector2(0,h)]),tint)
 draw_colored_polygon(PackedVector2Array([d,c,c-Vector2(0,h),d-Vector2(0,h)]),tint.darkened(.19))
 _text(name,_screen(p+dim*.5,h+6),10)

func _text(value: String,position: Vector2,font_size: int=13,color: Color=Color("f2e7c9")) -> void:
 draw_string(ThemeDB.fallback_font,position,value,HORIZONTAL_ALIGNMENT_LEFT,-1,font_size,color)

func _draw_player() -> void:
 var p:=_screen(player)
 draw_circle(p,7,Color("172820",.7))
 draw_rect(Rect2(p+Vector2(-6,-25),Vector2(12,19)),Color("508da9"))
 draw_circle(p+Vector2(0,-31),6,Color("cbb599"))
 _text("YOU",p+Vector2(-12,-46),11,Color("f2df9f"))

func _hud_title() -> String:
 return "LAST LIGHT / MATERIAL KIT V1"

func _hud_subtitle() -> String:
 return "WOOD  /  CERAMIC  /  CONCRETE  •  PLASTER  /  BLOCK  •  SHINGLE"

func _draw_hud() -> void:
 var size:=get_viewport_rect().size
 draw_rect(Rect2(Vector2.ZERO,Vector2(size.x,100)),Color("101c19",.92))
 _text(_hud_title(),Vector2(12,26),19)
 _text(_hud_subtitle(),Vector2(12,46),11,Color("bac7b7"))
 if info_timer>0:
  _text(info,Vector2(12,76),12)
 draw_circle(stick_center,57,Color("2b493b",.85))
 draw_arc(stick_center,57,0,TAU,36,Color("bac4a6"),2)
 draw_circle(stick_center+stick*33,25,Color("c9ba95"))
 var interact:=Vector2(size.x-80,size.y-99)
 draw_circle(interact,51,Color("c7a879"))
 _text("INTERACT",interact+Vector2(-38,3),12,Color("19241c"))
 draw_rect(Rect2(Vector2(size.x-112,12),Vector2(103,34)),Color("3c5548"))
 _text("RESUME" if paused else "PAUSE",Vector2(size.x-101,35),13)
 draw_rect(Rect2(Vector2(size.x-112,54),Vector2(103,34)),Color("43554b"))
 _text("ROOF: ON" if show_roofs else "ROOF: OFF",Vector2(size.x-105,77),11)

func _draw() -> void:
 _draw_ground()
 for b in structures:
  _draw_building(b)
 _draw_player()
 _draw_hud()

func _controls_resize() -> void:
 stick_center=Vector2(90,get_viewport_rect().size.y-105)
 stick_touch=-1
 stick=Vector2.ZERO

func _on_touch(id: int,pos: Vector2) -> void:
 if pos.distance_to(stick_center)<92 and stick_touch==-1 and not paused:
  stick_touch=id
  _drag_stick(pos)
  return
 var size:=get_viewport_rect().size
 if Rect2(Vector2(size.x-112,12),Vector2(103,34)).has_point(pos):
  paused=not paused
  stick_touch=-1
  stick=Vector2.ZERO
 elif Rect2(Vector2(size.x-112,54),Vector2(103,34)).has_point(pos):
  show_roofs=not show_roofs
  queue_redraw()
 elif not paused and pos.distance_to(Vector2(size.x-80,size.y-99))<55:
  _interact()

func _drag_stick(pos: Vector2) -> void:
 stick=(pos-stick_center).limit_length(57)/57
 if stick.length()<.14:
  stick=Vector2.ZERO

func _input(event: InputEvent) -> void:
 if event is InputEventScreenTouch:
  if event.pressed and not event.canceled:
   _on_touch(event.index,event.position)
  elif event.index==stick_touch:
   stick_touch=-1
   stick=Vector2.ZERO
 elif event is InputEventScreenDrag and event.index==stick_touch:
  _drag_stick(event.position)
 elif event is InputEventMouseButton and event.device!=InputEvent.DEVICE_ID_EMULATION:
  if event.button_index==MOUSE_BUTTON_LEFT:
   if event.pressed:
    _on_touch(MOUSE_ID,event.position)
   elif stick_touch==MOUSE_ID:
    stick_touch=-1
    stick=Vector2.ZERO
 elif event is InputEventMouseMotion and event.device!=InputEvent.DEVICE_ID_EMULATION and stick_touch==MOUSE_ID:
  _drag_stick(event.position)
 elif event is InputEventKey and event.pressed and not event.echo:
  if event.keycode==KEY_E:
   _interact()
  elif event.keycode==KEY_P or event.keycode==KEY_ESCAPE:
   paused=not paused
  elif event.keycode==KEY_R:
   show_roofs=not show_roofs
