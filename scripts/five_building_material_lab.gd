extends "res://scripts/material_kit_lab.gd"
## Isolated five-building district driven by reusable construction recipes.
const Art := preload("res://scripts/building_material_renderer.gd")
const PropArt := preload("res://scripts/lab_prop_renderer.gd")
const AmbientArt := preload("res://scripts/lab_ambient_renderer.gd")
const SurvivorArt := preload("res://scripts/lab_survivor_renderer.gd")
const LabSurvival := preload("res://scripts/lab_survival_state.gd")
const RECIPES := "res://assets/buildings/five_building_lab_v2.json"
var recipes: Dictionary = {}
var fixtures: Array[Dictionary] = []
var exterior_props: Array[Dictionary] = []
var ground_marks: Array[Dictionary] = []
var fences: Array[Dictionary] = []
var gameplay = LabSurvival.new()
var selected_item := ""
var inventory_open := false
var sprint_mode := false
## Temporary screenshot-friendly inspection mode; normal survival remains available.
var inspection_mode := true
const INSPECT_ZOOM := 0.60
const INSPECT_SPEED_MULTIPLIER := 5.0
var ambient_mode := 0
var walk_cycle := 0.0
var walking := false
var previous_web_fps_limit := 0

func _ready() -> void:
 super._ready()
 # A stable 30 Hz render budget keeps procedural geometry affordable on phones.
 # This lab-only setting is restored when leaving the scene.
 if OS.has_feature("web"):
  previous_web_fps_limit=Engine.max_fps
  Engine.max_fps=30
 var restored: Vector2 = gameplay.load(doorways)
 if restored.x!=INF and restored.y!=INF and restored.x>=-4 and restored.x<=45 and restored.y>=-4 and restored.y<=33 and not _is_blocked(restored):
  player=restored
  _notice("Laboratory save restored")
 queue_redraw()

func _exit_tree() -> void:
 if OS.has_feature("web"):
  Engine.max_fps=previous_web_fps_limit

func _vec(value: Array) -> Vector2:
 return Vector2(float(value[0]),float(value[1]))

func _screen(p: Vector2,h: float=0.0) -> Vector2:
 var normal: Vector2=super._screen(p,h)
 if not inspection_mode:
  return normal
 var center:=get_viewport_rect().size*Vector2(.5,.55)
 return center+(normal-center)*INSPECT_ZOOM

func _toggle_inspection() -> void:
 inspection_mode=not inspection_mode
 _notice("SCOUT: fast + wide view" if inspection_mode else "NORMAL: gameplay view")

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
 ground_marks.clear()
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
 for mark in payload.get("ground_marks",[]):
  ground_marks.append(mark.duplicate(true))
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
 for mark in ground_marks:
  Art.ground_mark(self,_screen(_vec(mark.a)),_screen(_vec(mark.b)),String(mark.kind))

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
 elif kind=="bed" or kind=="sofa":
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
   _notice("Found "+gameplay.item_name(item_id)+" in "+label)
  else:
   _notice(label+" was empty")
  _save_progress(false)
 queue_redraw()

func _movement_speed() -> float:
 if inspection_mode:
  return MOVE_SPEED*INSPECT_SPEED_MULTIPLIER
 return MOVE_SPEED*1.52 if sprint_mode and gameplay.stamina>2 else MOVE_SPEED

func _process(delta: float) -> void:
 super._process(delta)
 if paused:
  return
 var direction := stick if stick_touch!=-1 else Input.get_vector("ui_left","ui_right","ui_up","ui_down")
 gameplay.tick(minf(delta,.1),direction.length()>.14,sprint_mode and not inspection_mode)
 walking=direction.length()>.14
 if walking:
  walk_cycle=fmod(walk_cycle+delta*(15.0 if sprint_mode else 10.0),TAU)

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

func _cycle_ambient() -> void:
 ambient_mode=posmod(ambient_mode+1,AmbientArt.MODES.size())
 _notice("Lighting preview: "+AmbientArt.name_for(ambient_mode))

func _toggle_inventory() -> void:
 inventory_open=not inventory_open
 stick_touch=-1
 stick=Vector2.ZERO
 queue_redraw()

func _inventory_panel() -> Rect2:
 var size:=get_viewport_rect().size
 var width:=minf(508.0,size.x-24.0)
 var height:=minf(432.0,size.y-24.0)
 return Rect2(Vector2((size.x-width)*.5,(size.y-height)*.48),Vector2(width,height))

func _inventory_row(index: int) -> Rect2:
 var panel:=_inventory_panel()
 return Rect2(panel.position+Vector2(16,86+index*43),Vector2(panel.size.x-32,39))

func _inventory_close() -> Rect2:
 var panel:=_inventory_panel()
 return Rect2(panel.position+Vector2(panel.size.x-50,12),Vector2(36,36))

func _inventory_use() -> Rect2:
 var panel:=_inventory_panel()
 return Rect2(panel.position+Vector2(panel.size.x-176,panel.size.y-56),Vector2(160,42))

func _inventory_touch(pos: Vector2) -> void:
 var panel:=_inventory_panel()
 if _inventory_close().has_point(pos) or not panel.has_point(pos):
  _toggle_inventory()
  return
 if _inventory_use().has_point(pos):
  _use_selected()
  queue_redraw()
  return
 var items: Array[String]=gameplay.get_items()
 for i in range(items.size()):
  if _inventory_row(i).has_point(pos):
   selected_item=items[i]
   queue_redraw()
   return

func _on_touch(id: int,pos: Vector2) -> void:
 if inventory_open:
  _inventory_touch(pos)
  return
 var size := get_viewport_rect().size
 if Rect2(Vector2(size.x-231,12),Vector2(111,34)).has_point(pos):
  _save_progress()
  return
 if Rect2(Vector2(size.x-231,54),Vector2(111,34)).has_point(pos):
  _cycle_ambient()
  return
 if not paused:
  if pos.distance_to(Vector2(size.x-175,size.y-260))<36:
   _toggle_inspection()
   return
  if pos.distance_to(Vector2(size.x-176,size.y-80))<38:
   _toggle_inventory()
   return
  if pos.distance_to(Vector2(size.x-175,size.y-170))<37:
   sprint_mode=not sprint_mode
   _notice("Sprint on" if sprint_mode else "Sprint off")
   return
  if pos.distance_to(Vector2(size.x-80,size.y-207))<38:
   _use_selected()
   return
 super._on_touch(id,pos)

func _input(event: InputEvent) -> void:
 if event is InputEventKey and not event.echo and event.pressed:
  match event.keycode:
   KEY_I:
    _toggle_inventory()
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
   KEY_L:
    _cycle_ambient()
    return
   KEY_Z:
    _toggle_inspection()
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
  _draw_facade_style(b)
  if show_roofs:
   _draw_roof_style(b)
  return
 for fixture in fixtures:
  if (b.bounds as Rect2).has_point(fixture.position):
   _draw_fixture(fixture)

func _style(b: Dictionary) -> Dictionary:
 return recipes.get(String(b.name),{}).get("visual_style",{})

func _draw_facade_style(b: Dictionary) -> void:
 var style:=_style(b)
 if style.is_empty():
  return
 var bounds: Rect2=b.bounds
 var y:=bounds.end.y
 var left:=bounds.position.x
 var right:=bounds.end.x
 var center:=(left+right)*.5
 var accent:=Color(String(style.get("accent","647875")))
 var trim:=Color(String(style.get("trim","c5c7b5")))
 var profile:=String(style.get("profile",""))
 # A foundation, fascia, and corner language shared by every kit; only
 # appearance changes, never the structural collision or door segments.
 draw_line(_screen(Vector2(left,y),7),_screen(Vector2(right,y),7),accent.darkened(.38),3)
 draw_line(_screen(Vector2(left,y),58),_screen(Vector2(right,y),58),trim.darkened(.12),2)
 for x in [left,right]:
  draw_line(_screen(Vector2(x,y),4),_screen(Vector2(x,y),58),trim,2)
 if profile=="home":
  # Timber porch header and compact step identify the residence at roof-off.
  draw_line(_screen(Vector2(center-1.4,y),48),_screen(Vector2(center+1.4,y),48),accent,5)
  for x in [center-1.4,center+1.4]:
   draw_line(_screen(Vector2(x,y),0),_screen(Vector2(x,y),48),accent.lightened(.12),2)
  var step_a:=_screen(Vector2(center-1.3,y+.35))
  var step_b:=_screen(Vector2(center+1.3,y+.35))
  draw_line(step_a,step_b,Color("9a9481"),6)
 elif profile=="workshop":
  # Framed industrial bay, hazard threshold and workshop sign.
  for x in [center-1.2,center+1.2]:
   draw_line(_screen(Vector2(x,y),5),_screen(Vector2(x,y),55),accent,3)
  draw_line(_screen(Vector2(center-1.2,y),12),_screen(Vector2(center+1.2,y),12),Color("bb9e60"),3)
 elif profile=="market":
  # Deep shop awning distinct from the raised house roof.
  var awning_left:=_screen(Vector2(left+1.0,y),51)
  var awning_right:=_screen(Vector2(right-1.0,y),51)
  draw_line(awning_left,awning_right,accent,8)
  draw_line(awning_left+Vector2(0,5),awning_right+Vector2(0,5),trim,2)
 elif profile=="fuel":
  draw_line(_screen(Vector2(left,y),43),_screen(Vector2(right,y),43),accent,8)
  draw_line(_screen(Vector2(left,y),36),_screen(Vector2(right,y),36),trim,2)
 elif profile=="outpost":
  draw_line(_screen(Vector2(left,y),17),_screen(Vector2(right,y),17),Color("b09b64"),4)
  for i in range(7):
   var x:=lerpf(left+1,right-1,float(i)/6)
   var p:=_screen(Vector2(x,y),17)
   draw_line(p+Vector2(-3,-3),p+Vector2(3,3),Color("39443e"),1.3)
 var sign:=String(style.get("sign",""))
 if not sign.is_empty():
  var a:=_screen(Vector2(center-2.15,y),59)
  var c:=_screen(Vector2(center+2.15,y),59)
  var btm_c:=_screen(Vector2(center+2.15,y),43)
  var btm_a:=_screen(Vector2(center-2.15,y),43)
  draw_colored_polygon(PackedVector2Array([a,c,btm_c,btm_a]),accent.darkened(.19))
  draw_line(a,c,trim,2)
  _text(sign,_screen(Vector2(center-1.95,y),49),11,Color("efe6c7"))

func _draw_roof_style(b: Dictionary) -> void:
 var style:=_style(b)
 var profile:=String(style.get("profile",""))
 var box: Rect2=b.bounds
 var mid:=box.position+box.size*.5
 var accent:=Color(String(style.get("accent","66756a")))
 match profile:
  "home":
   # Short brick chimney emerging above the shingled roof.
   var p:=_screen(box.position+Vector2(2,2),103)
   draw_rect(Rect2(p-Vector2(8,12),Vector2(16,24)),Color("84675c"))
   draw_line(p-Vector2(10,12),p+Vector2(10,-12),Color("b39b87"),4)
  "workshop":
   # Raised metal seams are inherited; roof vents give service identity.
   for dx in [-1.8,1.8]:
    var p:=_screen(mid+Vector2(dx,0),81)
    draw_rect(Rect2(p-Vector2(14,5),Vector2(28,10)),accent.darkened(.22))
    draw_line(p-Vector2(10,2),p+Vector2(10,-2),Color("a3b3b1"),2)
  "market":
   var p:=_screen(mid+Vector2(1,-1),69)
   draw_rect(Rect2(p-Vector2(18,11),Vector2(36,22)),Color("48514d"))
   for x in [-9.0,0.0,9.0]:
    draw_line(p+Vector2(x,-6),p+Vector2(x,7),Color("8d9991"),1.2)
  "fuel":
   var p:=_screen(mid,69)
   draw_line(p-Vector2(32,8),p+Vector2(32,8),accent.lightened(.25),4)
   draw_circle(p,5,Color("b4b9a4"))
  "outpost":
   var p:=_screen(mid+Vector2(-1,-1),84)
   draw_line(p,p-Vector2(0,43),Color("a5b2ab"),2)
   draw_line(p-Vector2(14,36),p+Vector2(14,-36),Color("9daaa1"),2)
   draw_circle(p-Vector2(0,43),3,Color("c4b074"))

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
 var nearby := _fixture_accessible(fixture)
 var searched: bool = bool(gameplay.examined.get(String(fixture.id),false))
 PropArt.draw_prop(self,a,b,d,e,kind,tint,name,height,nearby,searched)
 # The formerly permanent 20 labels obscured small phones; show a readable
 # contextual cue only when the survivor can actually interact with this prop.
 if nearby:
  _text("INTERACT / "+name,_screen(p+dim*.5,height+29),11,Color("f2e7cf"))

func _draw_player() -> void:
 SurvivorArt.draw_survivor(self,_screen(player),last_face,walking,walk_cycle)
 _text("YOU",_screen(player)+Vector2(-11,-50),11,Color("f0df9f"))

func _roof_occludes_player(b: Dictionary) -> bool:
 var box: Rect2=b.bounds
 # In a 2:1 isometric view, south/east (+x/+y) are the visible foreground.
 # Outside the footprint on the north/west sides, the roof must be above the survivor.
 return show_roofs and not _is_inside(box) and player.x<box.end.x and player.y<box.end.y

func _draw_foreground_occlusion() -> void:
 for building in structures:
  var box: Rect2=building.bounds
  if _roof_occludes_player(building):
   var roof_height:=68.0
   Art.roof(self,_screen(box.position,roof_height),_screen(Vector2(box.end.x,box.position.y),roof_height),_screen(box.end,roof_height),_screen(Vector2(box.position.x,box.end.y),roof_height),String(building.roof))
   _draw_roof_style(building)
  elif not show_roofs and not _is_inside(box):
   # Transparent-roof mode still needs the nearest external wall to mask
   # survivors standing behind it; the walkable interior remains unchanged.
   for wall in segments:
    if not bool(wall.exterior):
     continue
    var a: Vector2=wall.a
    var b: Vector2=wall.b
    if not box.grow(.05).has_point(a.lerp(b,.5)):
     continue
    var south:=is_equal_approx(a.y,box.end.y) and is_equal_approx(b.y,box.end.y)
    var east:=is_equal_approx(a.x,box.end.x) and is_equal_approx(b.x,box.end.x)
    if (south or east) and player.x<box.end.x and player.y<box.end.y:
     if bool(wall.window):
      Art.window(self,_screen(a),_screen(b),60.0,String(wall.material))
     else:
      Art.wall_segment(self,_screen(a),_screen(b),60.0,String(wall.material))

func _under_canopy() -> bool:
 return Rect2(Vector2(15.5,24.5),Vector2(8,4)).has_point(player)

func _draw() -> void:
 _draw_ground()
 # Forecourt canopy is a distinct architectural assembly, not a sixth building.
 var canopy_start:=Vector2(15.5,24.5)
 var canopy_end:=Vector2(23.5,28.5)
 for world_p in [Vector2(15.5,24.5),Vector2(23.5,24.5),Vector2(15.5,28.5),Vector2(23.5,28.5)]:
  draw_line(_screen(world_p),_screen(world_p,59),Color("8b9591"),4)
 if not _under_canopy():
  Art.roof(self,_screen(canopy_start,59),_screen(Vector2(canopy_end.x,canopy_start.y),59),_screen(canopy_end,59),_screen(Vector2(canopy_start.x,canopy_end.y),59),"flat_membrane")
  var fuel_accent:=Color(String(recipes.get("GAS STATION",{}).get("visual_style",{}).get("accent","527e7b")))
  draw_line(_screen(Vector2(canopy_start.x,canopy_end.y),58),_screen(canopy_end,58),fuel_accent,5)
  draw_line(_screen(Vector2(canopy_end.x,canopy_start.y),58),_screen(canopy_end,58),Color("d2b57b"),3)
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
 _draw_foreground_occlusion()
 AmbientArt.draw_world(self,get_viewport_rect().size,ambient_mode)
 _draw_hud()

func _hud_title() -> String:
 return "LAST LIGHT / FIVE-BUILDING LAB V7"

func _hud_subtitle() -> String:
 return "5 STRUCTURES  •  MODULAR MATERIALS  •  INTERACTIVE DOORS"

func _hud_bar(label: String,x: float,y: float,width: float,value: float,color: Color) -> void:
 _text(label,Vector2(x,y-7),10,Color("c1d0c2"))
 draw_rect(Rect2(Vector2(x,y),Vector2(width,8)),Color("35423d"))
 draw_rect(Rect2(Vector2(x,y),Vector2(width*clampf(value/100,0,1),8)),color)
 _text("%d" % int(value),Vector2(x+width-22,y-7),10,Color("e7e4d7"))

func _hud_button(center: Vector2,radius: float,label: String,fill: Color) -> void:
 draw_circle(center,radius,fill)
 draw_arc(center,radius,0,TAU,32,Color("d4d7c7",.7),1.4)
 _text(label,center-Vector2(float(label.length())*3.3,-4),11,Color("172620"))

func _draw_hud() -> void:
 var size := get_viewport_rect().size
 var compact:=size.x<620.0
 var columns:=2 if compact else 4
 var header_height:=142.0 if compact else 106.0
 draw_rect(Rect2(Vector2.ZERO,Vector2(size.x,header_height)),Color("11221e",.95))
 _text("LAST LIGHT / LAB V7" if compact else _hud_title(),Vector2(12,22),14 if compact else 17,Color("e9e9dc"))
 var bar_width:=minf(99.0,maxf(52.0,(size.x-247.0-9.0*float(columns-1))/float(columns)))
 var labels: Array[String]=["HP","STAMINA","HUNGER","THIRST"]
 var values: Array[float]=[gameplay.health,gameplay.stamina,gameplay.hunger,gameplay.thirst]
 var colors: Array[Color]=[Color("c98177"),Color("a9b980"),Color("c6ae79"),Color("7aafb9")]
 for i in range(4):
  _hud_bar(labels[i],12.0+float(i%columns)*(bar_width+9.0),52.0+float(int(i/columns))*35.0,bar_width,values[i],colors[i])
 if info_timer>0:
  _text(info,Vector2(12,header_height-15),12,Color("e9dbba"))
 # Left virtual stick. Movement finger remains captured independently.
 draw_circle(stick_center,57,Color("294a40",.86))
 draw_arc(stick_center,57,0,TAU,32,Color("b4c7b3"),2)
 draw_circle(stick_center+stick*33,24,Color("d4c1a0"))
 _hud_button(Vector2(size.x-80,size.y-99),51,"INTERACT",Color("c4aa7a"))
 _hud_button(Vector2(size.x-80,size.y-207),35,"USE",Color("93b2a6"))
 _hud_button(Vector2(size.x-175,size.y-170),35,"RUN ON" if sprint_mode else "RUN",Color("b2c38a"))
 _hud_button(Vector2(size.x-175,size.y-260),34,"SCOUT" if inspection_mode else "NORMAL",Color("b9cdb5" if inspection_mode else "87978d"))
 _hud_button(Vector2(size.x-176,size.y-80),35,"PACK",Color("b7b6a4"))
 draw_rect(Rect2(Vector2(size.x-112,12),Vector2(103,34)),Color("40584a"))
 _text("RESUME" if paused else "PAUSE",Vector2(size.x-100,35),13)
 draw_rect(Rect2(Vector2(size.x-112,54),Vector2(103,34)),Color("40584a"))
 _text("ROOF ON" if show_roofs else "ROOF OFF",Vector2(size.x-104,77),11)
 draw_rect(Rect2(Vector2(size.x-231,12),Vector2(111,34)),Color("4d6559"))
 _text("SAVE",Vector2(size.x-211,35),13)
 draw_rect(Rect2(Vector2(size.x-231,54),Vector2(111,34)),Color("4d6559"))
 _text(AmbientArt.name_for(ambient_mode),Vector2(size.x-208,77),12)
 if selected_item!="":
  _text("SELECTED: "+gameplay.item_name(selected_item),Vector2(175,size.y-22),11,Color("f1e2c0"))
 if inventory_open:
  _draw_inventory()

func _draw_inventory() -> void:
 var size:=get_viewport_rect().size
 var panel:=_inventory_panel()
 var items: Array[String]=gameplay.get_items()
 draw_rect(Rect2(Vector2.ZERO,size),Color(0.035,0.07,0.06,.64))
 draw_rect(panel.grow(4),Color("0c1915",.95))
 draw_rect(panel,Color("20382f"))
 draw_rect(panel,Color("a9bda9",.8),false,2)
 _text("BACKPACK",panel.position+Vector2(18,35),23,Color("f2e8cb"))
 _text("%d / %d SLOTS   •   TAP AN ITEM TO SELECT" % [items.size(),LabSurvival.CAPACITY],panel.position+Vector2(19,65),12,Color("c8d5c5"))
 var close_rect:=_inventory_close()
 draw_rect(close_rect,Color("496253"))
 _text("X",close_rect.position+Vector2(12,24),18,Color("f7e8d2"))
 for i in range(LabSurvival.CAPACITY):
  var row:=_inventory_row(i)
  var populated:=i<items.size()
  var item_id:=items[i] if populated else ""
  var active:=populated and item_id==selected_item
  draw_rect(row,Color("5d7054") if active else Color("304a3e") if i%2==0 else Color("2b4238"))
  if active:
   draw_rect(row,Color("e4d19b"),false,2)
  _text("%02d" % [i+1],row.position+Vector2(12,25),13,Color("a8bdad"))
  if populated:
   _text(gameplay.item_name(item_id),row.position+Vector2(47,25),15,Color("f5e5c4"))
   _text("×%d" % int(gameplay.inventory[item_id]),row.position+Vector2(row.size.x-46,25),14,Color("f5e5c4"))
  else:
   _text("EMPTY SLOT",row.position+Vector2(47,25),13,Color("829c8c"))
 if items.is_empty():
  _text("Search cabinets, shelves, and crates to find supplies.",panel.position+Vector2(18,panel.size.y-68),12,Color("e6d9ad"))
 var use_rect:=_inventory_use()
 draw_rect(use_rect,Color("b7ad81") if selected_item!="" and gameplay.inventory.has(selected_item) else Color("5a6b60"))
 _text("USE SELECTED" if selected_item!="" and gameplay.inventory.has(selected_item) else "NO ITEM SELECTED",use_rect.position+Vector2(12,27),12,Color("172720"))
 _text("TAP OUTSIDE TO CLOSE",panel.position+Vector2(18,panel.size.y-27),11,Color("c4d0c0"))
