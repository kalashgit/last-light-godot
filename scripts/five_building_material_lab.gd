extends "res://scripts/material_kit_lab.gd"
## Isolated five-building district driven by reusable construction recipes.
const Art := preload("res://scripts/building_material_renderer.gd")
const LabSurvival := preload("res://scripts/lab_survival_state.gd")
const RECIPES := "res://assets/buildings/five_building_lab_v2.json"
var recipes: Dictionary = {}
var fixtures: Array[Dictionary] = []
var exterior_props: Array[Dictionary] = []
var fences: Array[Dictionary] = []
var gameplay = LabSurvival.new()
var selected_item := ""
var inventory_open := false
var sprint_mode := false

func _ready() -> void:
 super._ready()
 var restored: Vector2 = gameplay.load(doorways)
 if restored.x!=INF and restored.y!=INF and restored.x>=-4 and restored.x<=45 and restored.y>=-4 and restored.y<=33 and not _is_blocked(restored):
  player=restored
  _notice("Laboratory save restored")
 queue_redraw()

func _vec(value: Array) -> Vector2:
 return Vector2(float(value[0]),float(value[1]))

func _init_buildings() -> void:
 var payload: Variant = JSON.parse_string(FileAccess.get_file_as_string(RECIPES))
 if not payload is Dictionary or not payload.has("buildings"):
  push_error("Five-building recipes unavailable; loading known material-kit layout")
  super._init_buildings()
  return
 structures.clear()
 segments.clear()
 doorways.clear()
 fixtures.clear()
 exterior_props.clear()
 fences.clear()
 recipes.clear()
 gameplay.examined.clear()
 for recipe in payload.buildings:
  if not recipe is Dictionary:
   continue
  var origin := _vec(recipe.origin)
  var label := String(recipe.id)
  recipes[label]=recipe
  _add_structure(label,origin,_vec(recipe.size),String(recipe.wall),String(recipe.roof))
  for part in recipe.get("partitions",[]):
   var a := origin+_vec(part.a)
   var b := origin+_vec(part.b)
   if String(part.get("kind","wall"))=="door":
    _door(a,b,String(part.get("label","INTERIOR")),false)
   else:
    _wall(a,b,String(part.get("material",recipe.wall)),false)
  for item in recipe.get("fixtures",[]):
   var copy: Dictionary = item.duplicate(true)
   copy["position"]=origin+_vec(item.pos)
   copy["size_world"]=_vec(item.size)
   copy["id"]=label+"/"+String(item.id)
   fixtures.append(copy)
 for item in payload.get("exterior_props",[]):
  var copy: Dictionary = item.duplicate(true)
  copy["position"]=_vec(item.pos)
  copy["size_world"]=_vec(item.size)
  copy["exterior"]=true
  exterior_props.append(copy)
 for segment in payload.get("fences",[]):
  var a := _vec(segment.a)
  var b := _vec(segment.b)
  if String(segment.get("kind","fence"))=="gate":
   _door(a,b,String(segment.get("label","GATE")),true)
  else:
   fences.append({"a":a,"b":b})

func _floor_material(b: Dictionary,x: int,y: int) -> String:
 var recipe: Dictionary = recipes.get(String(b.name),{})
 if recipe.is_empty():
  return super._floor_material(b,x,y)
 var local := Vector2(x,y)-(b.bounds as Rect2).position
 for region in recipe.get("floor_zones",[]):
  if Rect2(_vec(region.pos),_vec(region.size)).has_point(local):
   return String(region.material)
 return String(recipe.get("floor","concrete_stained"))

func _draw_ground() -> void:
 var sz := get_viewport_rect().size
 draw_rect(Rect2(Vector2.ZERO,sz),Color("253b32"))
 for y in range(-5,34):
  for x in range(-5,47):
   var p := Vector2(x,y)
   var origin := _screen(p)
   # Rectangular culling avoids overdraw on the narrow iPhone viewport.
   if origin.x < -110 or origin.x > sz.x+110 or origin.y < -90 or origin.y > sz.y+90:
    continue
   var material := "grass_sparse"
   if y>=9 and y<=13 and x<29:
    material="asphalt_worn"
   elif y>=24 and y<=29 and x<26:
    material="asphalt_worn"
   elif x>=27 and x<=43 and y>=1 and y<=18:
    material="concrete_stained"
   elif x%9==0 or y%9==0:
    material="paver_gray"
   var v := [_screen(p),_screen(p+Vector2(1,0)),_screen(p+Vector2(1,1)),_screen(p+Vector2(0,1))]
   Art.floor_tile(self,v[0],v[1],v[2],v[3],material,x,y)

func _fixture_bounds(fixture: Dictionary) -> Rect2:
 return Rect2(fixture.position,fixture.size_world)

func _fixture_distance(fixture: Dictionary) -> float:
 var bounds := _fixture_bounds(fixture)
 var nearest := Vector2(clampf(player.x,bounds.position.x,bounds.end.x),clampf(player.y,bounds.position.y,bounds.end.y))
 return player.distance_to(nearest)

func _cross(a: Vector2,b: Vector2) -> float:
 return a.x*b.y-a.y*b.x

func _obstructed_to(target: Vector2) -> bool:
 var ray := target-player
 if ray.length_squared()<.001:
  return false
 for segment in segments:
  var edge: Vector2=segment.b-segment.a
  var det:=_cross(ray,edge)
  if absf(det)<.00001:
   continue
  var diff: Vector2=segment.a-player
  var t:=_cross(diff,edge)/det
  var u:=_cross(diff,ray)/det
  if t>.01 and t<.99 and u>=0.0 and u<=1.0:
   return true
 for door in doorways:
  if door.open:
   continue
  var edge: Vector2=door.b-door.a
  var det:=_cross(ray,edge)
  if absf(det)<.00001:
   continue
  var diff: Vector2=door.a-player
  var t:=_cross(diff,edge)/det
  var u:=_cross(diff,ray)/det
  if t>.01 and t<.99 and u>=0.0 and u<=1.0:
   return true
 for fence in fences:
  var edge: Vector2=fence.b-fence.a
  var det:=_cross(ray,edge)
  if absf(det)<.00001:
   continue
  var diff: Vector2=fence.a-player
  var t:=_cross(diff,edge)/det
  var u:=_cross(diff,ray)/det
  if t>.01 and t<.99 and u>=0.0 and u<=1.0:
   return true
 return false

func _fixture_accessible(fixture: Dictionary) -> bool:
 if _fixture_distance(fixture)>1.15:
  return false
 if not fixture.get("exterior",false):
  var inside_owner:=false
  for building in structures:
   if (building.bounds as Rect2).has_point(fixture.position):
    inside_owner=_is_inside(building.bounds)
    break
  if not inside_owner:
   return false
 var bounds := _fixture_bounds(fixture)
 var target := Vector2(clampf(player.x,bounds.position.x,bounds.end.x),clampf(player.y,bounds.position.y,bounds.end.y))
 return not _obstructed_to(target)

func _nearby_fixture() -> Dictionary:
 var choice: Dictionary = {}
 var best := 1.15
 for fixture in fixtures+exterior_props:
  if not _fixture_accessible(fixture):
   continue
  var dist := _fixture_distance(fixture)
  if dist < best:
   best=dist
   choice=fixture
 return choice

func _interact() -> void:
 var door_index := -1
 var door_dist := 1.55
 for i in range(doorways.size()):
  var d: float = _segment_distance(player,doorways[i].a,doorways[i].b)
  if d < door_dist:
   door_dist=d
   door_index=i
 var nearby := _nearby_fixture()
 if door_index>=0 and (nearby.is_empty() or door_dist<=_fixture_distance(nearby)+.25):
  super._interact()
  _save_progress(false)
  return
 if nearby.is_empty():
  _notice("Move closer to a door or object.")
  return
 var object_id := String(nearby.id)
 var kind := String(nearby.get("kind","storage"))
 var label := String(nearby.get("label","OBJECT"))
 if kind=="pump":
  _notice(label+": inactive. Fuel mechanics not yet implemented.")
 elif kind=="bed":
  _notice(label+": rest/sleep system not yet implemented.")
 elif gameplay.examined.get(object_id,false):
  _notice(label+": already searched")
 else:
  var item_id := String(nearby.get("loot",""))
  if item_id!="" and not gameplay.add_item(item_id):
   _notice("Backpack full or invalid loot")
   return
  gameplay.examined[object_id]=true
  if item_id!="":
   selected_item=item_id
   _notice("Found "+String(LabSurvival.ITEM_NAMES[item_id])+" in "+label)
  else:
   _notice(label+" was empty")
  _save_progress(false)
 queue_redraw()

func _movement_speed() -> float:
 return MOVE_SPEED*1.52 if sprint_mode and gameplay.stamina>2 else MOVE_SPEED

func _process(delta: float) -> void:
 super._process(delta)
 if paused:
  return
 var direction := stick if stick_touch!=-1 else Input.get_vector("ui_left","ui_right","ui_up","ui_down")
 gameplay.tick(minf(delta,.1),direction.length()>.14,sprint_mode)

func _save_progress(show_message: bool=true) -> void:
 var success: bool = gameplay.save(player,doorways)
 if show_message:
  _notice("Lab saved" if success else "Save failed - check storage")

func _use_selected() -> void:
 if selected_item=="":
  _notice("Select an item in the backpack")
  return
 _notice(gameplay.use_item(selected_item))
 if not gameplay.inventory.has(selected_item):
  selected_item=""
 _save_progress(false)

func _on_touch(id: int,pos: Vector2) -> void:
 var size := get_viewport_rect().size
 if Rect2(Vector2(size.x-231,12),Vector2(111,34)).has_point(pos):
  _save_progress()
  return
 if not paused:
  if pos.distance_to(Vector2(size.x-176,size.y-80))<38:
   inventory_open=not inventory_open
   return
  if pos.distance_to(Vector2(size.x-175,size.y-170))<37:
   sprint_mode=not sprint_mode
   _notice("Sprint on" if sprint_mode else "Sprint off")
   return
  if pos.distance_to(Vector2(size.x-80,size.y-207))<38:
   _use_selected()
   return
  if inventory_open:
   var list: Array[String] = gameplay.get_items()
   var panel := Rect2(Vector2(size.x*.5-160,113),Vector2(320,35+list.size()*27))
   if panel.has_point(pos):
    var index := int((pos.y-panel.position.y-28)/27.0)
    if index>=0 and index<list.size():
     selected_item=list[index]
    return
 super._on_touch(id,pos)

func _input(event: InputEvent) -> void:
 if event is InputEventKey and not event.echo and event.pressed:
  match event.keycode:
   KEY_I:
    inventory_open=not inventory_open
    return
   KEY_F:
    _use_selected()
    return
   KEY_F5:
    _save_progress()
    return
   KEY_SHIFT:
    sprint_mode=not sprint_mode
    return
 super._input(event)

func _is_blocked(p: Vector2) -> bool:
 if super._is_blocked(p):
  return true
 for fence in fences:
  if _segment_distance(p,fence.a,fence.b)<PLAYER_R+.07:
   return true
 for fixture in fixtures:
  if fixture.get("solid",false) and _fixture_bounds(fixture).grow(PLAYER_R).has_point(p):
   return true
 for fixture in exterior_props:
  if fixture.get("solid",false) and _fixture_bounds(fixture).grow(PLAYER_R).has_point(p):
   return true
 return false

func _draw_building(b: Dictionary) -> void:
 super._draw_building(b)
 if not _is_inside(b.bounds):
  return
 for fixture in fixtures:
  if (b.bounds as Rect2).has_point(fixture.position):
   _draw_fixture(fixture)

func _draw_default_furniture(_building: Dictionary) -> void:
 pass

func _draw_fixture(fixture: Dictionary) -> void:
 var p: Vector2 = fixture.position
 var dim: Vector2 = fixture.size_world
 var name := String(fixture.get("label","PROP"))
 var kind := String(fixture.get("kind","storage"))
 var height := float(fixture.get("height_px",18))
 var tint := Color(String(fixture.get("color","887c6a")))
 var a := _screen(p)
 var b := _screen(p+Vector2(dim.x,0))
 var d := _screen(p+dim)
 var e := _screen(p+Vector2(0,dim.y))
 var lift := Vector2(0,height)
 draw_colored_polygon(PackedVector2Array([e,d,d-lift,e-lift]),tint.darkened(.33))
 draw_colored_polygon(PackedVector2Array([b,d,d-lift,b-lift]),tint.darkened(.16))
 draw_colored_polygon(PackedVector2Array([a-lift,b-lift,d-lift,e-lift]),tint.lightened(.11))
 if _fixture_accessible(fixture) and _fixture_distance(fixture)<1.15:
  var highlight:=Color("c1daa4")
  draw_line(a-lift,b-lift,highlight,2)
  draw_line(b-lift,d-lift,highlight,2)
  draw_line(d-lift,e-lift,highlight,2)
  draw_line(e-lift,a-lift,highlight,2)
 if gameplay.examined.get(String(fixture.id),false):
  draw_circle(a.lerp(d,.5)-lift,3,Color("a6d3bd"))
 match kind:
  "shelf":
   for k in range(1,4):
    var z := lift*float(k)/4.0
    draw_line(e-z,d-z,Color("c1ab7b"),2.2)
    draw_line(a-z,e-z,Color("514e47"),1.5)
  "bed":
   draw_colored_polygon(PackedVector2Array([a-lift*.70,b-lift*.70,d-lift*.70,e-lift*.70]),Color("87948f"))
   draw_line(a.lerp(e,.20)-lift*.73,b.lerp(d,.20)-lift*.73,Color("ded7c2"),6)
  "pump":
   draw_rect(Rect2(_screen(p+dim*.5)-Vector2(5,height+18),Vector2(10,18)),Color("d5c9ad"))
   draw_line(_screen(p+dim*.5)-Vector2(6,height+6),_screen(p+dim*.5)+Vector2(10,-height+1),Color("303d3d"),2)
   draw_circle(_screen(p+dim*.5)-Vector2(0,height+13),2.5,Color("53686d"))
  "crate":
   draw_line(e-lift,b-lift,Color("554e40"),1.5)
   draw_line(a-lift,d-lift,Color("554e40"),1.5)
  "counter":
   draw_line(a-lift,e-lift,tint.lightened(.33),3)
   draw_line(e-lift,d-lift,tint.lightened(.23),2)
 _text(name,_screen(p+dim*.5,height+7),10,Color("f2e7cf"))

func _draw() -> void:
 _draw_ground()
 # Forecourt canopy is a distinct architectural assembly, not a sixth building.
 var canopy_start:=Vector2(15.5,24.5)
 var canopy_end:=Vector2(23.5,28.5)
 for world_p in [Vector2(15.5,24.5),Vector2(23.5,24.5),Vector2(15.5,28.5),Vector2(23.5,28.5)]:
  draw_line(_screen(world_p),_screen(world_p,59),Color("8b9591"),4)
 Art.roof(self,_screen(canopy_start,59),_screen(Vector2(canopy_end.x,canopy_start.y),59),_screen(canopy_end,59),_screen(Vector2(canopy_start.x,canopy_end.y),59),"flat_membrane")
 for fixture in exterior_props:
  _draw_fixture(fixture)
 for b in structures:
  _draw_building(b)
 for fence in fences:
  Art.fence_segment(self,_screen(fence.a),_screen(fence.b))
 for gate in doorways:
  if String(gate.name)=="OUTPOST GATE":
   Art.door(self,_screen(gate.a),_screen(gate.b),gate.open,true)
   _text("GATE OPEN" if gate.open else "GATE / INTERACT",_screen((gate.a+gate.b)*.5,55),11)
 _draw_player()
 _draw_hud()

func _hud_title() -> String:
 return "LAST LIGHT / FIVE-BUILDING LAB V2"

func _hud_subtitle() -> String:
 return "5 STRUCTURES  •  MODULAR MATERIALS  •  INTERACTIVE DOORS"

func _hud_bar(label: String,x: float,value: float,color: Color) -> void:
 _text(label,Vector2(x,45),10,Color("c1d0c2"))
 draw_rect(Rect2(Vector2(x,52),Vector2(99,8)),Color("35423d"))
 draw_rect(Rect2(Vector2(x,52),Vector2(99*clampf(value/100,0,1),8)),color)
 _text("%d" % int(value),Vector2(x+77,45),10,Color("e7e4d7"))

func _hud_button(center: Vector2,radius: float,label: String,fill: Color) -> void:
 draw_circle(center,radius,fill)
 draw_arc(center,radius,0,TAU,32,Color("d4d7c7",.7),1.4)
 _text(label,center-Vector2(float(label.length())*3.3,-4),11,Color("172620"))

func _draw_hud() -> void:
 var size := get_viewport_rect().size
 draw_rect(Rect2(Vector2.ZERO,Vector2(size.x,106)),Color("11221e",.95))
 _text(_hud_title(),Vector2(12,22),17,Color("e9e9dc"))
 _hud_bar("HP",12,gameplay.health,Color("c98177"))
 _hud_bar("STAMINA",121,gameplay.stamina,Color("a9b980"))
 _hud_bar("HUNGER",230,gameplay.hunger,Color("c6ae79"))
 _hud_bar("THIRST",339,gameplay.thirst,Color("7aafb9"))
 if info_timer>0:
  _text(info,Vector2(12,90),12,Color("e9dbba"))
 # Left virtual stick. Movement finger remains captured independently.
 draw_circle(stick_center,57,Color("294a40",.86))
 draw_arc(stick_center,57,0,TAU,32,Color("b4c7b3"),2)
 draw_circle(stick_center+stick*33,24,Color("d4c1a0"))
 _hud_button(Vector2(size.x-80,size.y-99),51,"INTERACT",Color("c4aa7a"))
 _hud_button(Vector2(size.x-80,size.y-207),35,"USE",Color("93b2a6"))
 _hud_button(Vector2(size.x-175,size.y-170),35,"RUN ON" if sprint_mode else "RUN",Color("b2c38a"))
 _hud_button(Vector2(size.x-176,size.y-80),35,"PACK",Color("b7b6a4"))
 draw_rect(Rect2(Vector2(size.x-112,12),Vector2(103,34)),Color("40584a"))
 _text("RESUME" if paused else "PAUSE",Vector2(size.x-100,35),13)
 draw_rect(Rect2(Vector2(size.x-112,54),Vector2(103,34)),Color("40584a"))
 _text("ROOF ON" if show_roofs else "ROOF OFF",Vector2(size.x-104,77),11)
 draw_rect(Rect2(Vector2(size.x-231,12),Vector2(111,34)),Color("4d6559"))
 _text("SAVE",Vector2(size.x-211,35),13)
 var items: Array[String] = gameplay.get_items()
 if selected_item!="":
  _text("EQUIPPED: "+String(LabSurvival.ITEM_NAMES.get(selected_item,selected_item)),Vector2(175,size.y-22),11,Color("f1e2c0"))
 if inventory_open:
  var panel := Rect2(Vector2(size.x*.5-160,113),Vector2(320,35+items.size()*27))
  draw_rect(panel,Color("1b302b",.96))
  draw_rect(Rect2(panel.position,panel.size),Color("b3c6aa",.55),false,1)
  _text("BACKPACK / TAP ITEM TO SELECT",panel.position+Vector2(12,22),12)
  for i in range(items.size()):
   var item_id:=items[i]
   var line:=String(LabSurvival.ITEM_NAMES[item_id])+"  ×"+str(gameplay.inventory[item_id])
   _text(line,panel.position+Vector2(16,47+i*27),12,Color("f1dc99") if item_id==selected_item else Color("e2e6d8"))
  if items.is_empty():
   _text("Empty. Search a container.",panel.position+Vector2(16,47),12)
