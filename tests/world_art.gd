extends SceneTree
var checks:=0
var game
func check(condition:bool,label:String)->void:
 checks+=1
 assert(condition,label)
func _initialize()->void:call_deferred("run")
func run()->void:
 game=load("res://main.tscn").instantiate()
 root.add_child(game)
 game.set_process(false)
 game._restart_game()
 var art=game.art.world_art
 var count:=0
 for id in game.survival.definitions:
  if id.begins_with("ll_golden_"):
   count+=1
   check(not art.is_world_ready(id),"Golden icon must not become ground art")
   check(game._golden_icon(id)!=null,"Inventory icon preserved")
   check(art.lookup(id).marker_radius_px<=3,"Marker remains tiny in world pixels")
 check(count==40,"All forty icons retained")
 check(not art.is_world_ready("unmapped_id"),"Unknown mapping fails closed")
 check(art.is_world_ready("ll_food_bean_tin"),"Native original world representation retained")
 check(game.texture_filter==CanvasItem.TEXTURE_FILTER_NEAREST,"Nearest world sampling")
 for item in game.items:
  check(art.furniture_scale(item)>0,"Positive isotropic furniture scale")
 for prop in game.art.decorations:
  var support:Dictionary=game.art._support_item(prop)
  if not support.is_empty() and prop.support.get("surface_height_m")!=null:
   var expected:float=float(prop.support.surface_height_m)*art.VERTICAL_PX_PER_M*art.furniture_scale(support)
   check(is_equal_approx(game.art._decoration_height(prop),expected),"Support elevation scales once")
 # Pure camera math at all required zooms. HUD rectangles cannot inherit world zoom.
 game.player=Vector2(2.4,2.5)
 game._layout_controls()
 var hud:Rect2=game.control_rects.inventory
 for zoom in [1.0,2.2,3.25]:
  game.camera_zoom=zoom
  game._layout_controls()
  check(game.control_rects.inventory==hud,"HUD remains fixed")
  var p:=Vector2(3.2,2.8)
  check(game._view_to_world(game._world_to_view(p)).distance_to(p)<.00001,"Zoom-aware tap inverse")
  check(is_equal_approx(game._world_to_view(p).distance_to(game._world_to_view(game.player)),game._screen(p).distance_to(game._screen(game.player))*zoom),"Exactly one world zoom")
 var event:=InputEventKey.new()
 event.keycode=KEY_F8;event.pressed=true
 game._input(event)
 check(game.world_art_debug,"Debug overlay toggle")
 # Actual save/load keeps stable gameplay IDs despite artwork role changes.
 game.zombie_health=[0,0];game.player=Vector2(-3,1.5)
 check(game._spawn_golden_item("ll_golden_acorn",Vector2(-2,1.5)),"Spawn icon-only item using marker")
 var ids:Array=game.drops.duplicate(true)
 check(game._save_game()==OK and game._load_game()==OK,"Save/reload succeeds")
 check(ids==game.drops,"Drop identities and positions preserved")
 print("WORLD ART: ",checks," checks PASS; no visual or device approval inferred")
 game.free();quit()
