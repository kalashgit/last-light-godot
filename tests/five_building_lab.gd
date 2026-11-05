extends SceneTree
## Headless integration smoke for the opt-in five-building graphics laboratory.
## Run with an isolated XDG_DATA_HOME to protect any real user:// save.
const LabState := preload("res://scripts/lab_survival_state.gd")
const AmbientArt := preload("res://scripts/lab_ambient_renderer.gd")
var failures := 0

func check(condition: bool, message: String) -> void:
 if not condition:
  push_error("LAB CHECK: "+message)
  failures+=1

func _initialize() -> void:
 call_deferred("run")

func run() -> void:
 var scene: PackedScene = load("res://scenes/five_building_material_lab.tscn")
 check(scene!=null,"isolated scene loads")
 if scene==null:
  quit(1)
  return
 var lab=scene.instantiate()
 root.add_child(lab)
 lab.set_process(false)
 check(lab.structures.size()==5,"five building recipes instantiate")
 check(lab.fixtures.size()==17 and lab.exterior_props.size()==3,"all twenty fixture IDs instantiate")
 check(lab.fences.size()==5,"outpost fence segments survive")
 check(lab.ground_marks.size()==6,"six data-driven surface marks load")
 var material_texture: Texture2D=load("res://assets/materials/asphalt_grain_v1.png")
 check(material_texture!=null and material_texture.get_width()==128,"optimized original asphalt texture imports")
 var wall_atlas: Texture2D=load("res://assets/materials/wall_kit_atlas_v1.png")
 check(wall_atlas!=null and wall_atlas.get_width()==512 and wall_atlas.get_height()==512,"original four-material wall atlas imports at mobile size")
 var visual_profiles: Dictionary={}
 for recipe in lab.recipes.values():
  var style: Dictionary=recipe.get("visual_style",{})
  check(style.has("profile") and style.has("accent") and style.has("trim"),"building archetype has reusable facade style")
  visual_profiles[String(style.get("profile",""))]=true
 check(visual_profiles.size()==5,"all five buildings have distinctive visual profiles")
 var kinds: Dictionary={}
 for fixture in lab.fixtures+lab.exterior_props:
  kinds[String(fixture.kind)]=true
 for kind in ["counter","bed","sofa","shelf","crate","storage","pump"]:
  check(kinds.has(kind),"distinct art archetype "+kind)

 var viewport_size: Vector2=lab.get_viewport_rect().size
 check(lab.inspection_mode,"wide-view SCOUT mode starts enabled for screenshot review")
 check(lab._movement_speed()>=12.0,"SCOUT traversal is at least five times normal walking speed")
 var projected_scout: Vector2=lab._screen(lab.player+Vector2(5,0))
 lab._on_touch(9,Vector2(viewport_size.x-175,viewport_size.y-260))
 check(not lab.inspection_mode,"SCOUT button returns to normal gameplay")
 check(is_equal_approx(lab._movement_speed(),2.5),"normal mode restores original walking speed")
 var projected_normal: Vector2=lab._screen(lab.player+Vector2(5,0))
 check(projected_scout.distance_to(lab._screen(lab.player))<projected_normal.distance_to(lab._screen(lab.player)),"SCOUT mode has a wider projected view")
 lab._on_touch(9,Vector2(viewport_size.x-175,viewport_size.y-260))
 check(lab.inspection_mode,"SCOUT button toggles back on")
 lab._on_touch(9,Vector2(viewport_size.x-176,viewport_size.y-80))
 check(lab.inventory_open,"PACK touch opens the backpack")
 check(lab._inventory_panel().size.y>=400,"empty backpack is a full-size panel instead of a thin strip")
 check(lab._inventory_panel().encloses(lab._inventory_row(5)),"all six empty slots fit inside the panel")
 lab._on_touch(9,lab._inventory_close().get_center())
 check(not lab.inventory_open,"backpack close button works")

 var entrance: Dictionary=lab.doorways[0]
 lab.player=entrance.a.lerp(entrance.b,.5)+Vector2(0,-.72)
 lab._interact()
 check(bool(lab.doorways[0].open),"entrance still responds to INTERACT")

 lab.player=Vector2(1.5,1.6)
 lab._interact()
 check(int(lab.gameplay.inventory.get("canned_food",0))==1,"counter search gives existing loot")
 check(bool(lab.gameplay.examined.get("RESIDENTIAL HOUSE/kitchen_counter",false)),"search ownership persists by stable ID")
 lab.gameplay.hunger=40.0
 lab.selected_item=""
 lab._on_touch(9,Vector2(viewport_size.x-176,viewport_size.y-80))
 lab._on_touch(9,lab._inventory_row(0).get_center())
 check(lab.selected_item=="canned_food","tapping a backpack slot selects the item")
 lab._on_touch(9,lab._inventory_use().get_center())
 check(lab.gameplay.hunger>40.0,"USE SELECTED consumes food and changes hunger")
 check(not lab.gameplay.inventory.has("canned_food"),"use consumes existing item")
 check(lab.inventory_open,"using an item keeps the backpack open")
 lab._on_touch(9,Vector2(10,viewport_size.y*.5))
 check(not lab.inventory_open,"tapping outside closes the backpack")

 lab.player=Vector2(1.8,5.3)
 lab._interact()
 check(lab.info.contains("sleep system not yet implemented"),"sofa is correctly described as non-implemented rest, not loot")
 check(lab._save_progress!=null,"save action remains bound")
 lab._save_progress(false)
 var restored=LabState.new()
 var restored_pos: Vector2=restored.load(lab.doorways)
 check(restored_pos.distance_to(lab.player)<.01,"position survives laboratory save")
 check(bool(restored.examined.get("RESIDENTIAL HOUSE/kitchen_counter",false)),"examined cabinet survives save")
 check(restored.hunger>40.0,"hunger effect survives save")
 lab.player=Vector2(4.5,10.0)
 check(not lab._roof_occludes_player(lab.structures[0]),"a player south of a house remains visible in front of its roof")
 lab.player=Vector2(4.5,-1.0)
 check(lab._roof_occludes_player(lab.structures[0]),"a player north of a house is correctly behind its roof")
 lab.player=Vector2(3.0,3.0)
 check(not lab._roof_occludes_player(lab.structures[0]),"indoor cutaway stays visible")
 lab.player=Vector2(18.0,26.0)
 check(lab._under_canopy(),"forecourt canopy cuts away over the player")
 lab._on_touch(1,lab.stick_center+Vector2(25,0))
 check(lab.stick_touch==1,"left movement stick captures first touch")
 var before_mode: int=lab.ambient_mode
 lab._on_touch(3,Vector2(lab.get_viewport_rect().size.x-180,71))
 check(lab.ambient_mode==posmod(before_mode+1,AmbientArt.MODES.size()),"mobile TIME control cycles ambient grading")
 check(lab.stick_touch==1,"TIME action does not steal movement finger")
 lab.stick_touch=-1
 lab.stick=Vector2.ZERO
 check(AmbientArt.overlay_for(2).a>AmbientArt.overlay_for(0).a,"night grade is darker than daytime")
 var path:=ProjectSettings.globalize_path(LabState.SAVE_PATH)
 if FileAccess.file_exists(LabState.SAVE_PATH):
  DirAccess.remove_absolute(path)
 print("FIVE-BUILDING LAB: %d failures" % failures)
 lab.free()
 quit(1 if failures else 0)
