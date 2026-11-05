extends SceneTree
## Headless integration smoke for the opt-in five-building graphics laboratory.
## Run with an isolated XDG_DATA_HOME to protect any real user:// save.
const LabState := preload("res://scripts/lab_survival_state.gd")
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
 var kinds: Dictionary={}
 for fixture in lab.fixtures+lab.exterior_props:
  kinds[String(fixture.kind)]=true
 for kind in ["counter","bed","sofa","shelf","crate","storage","pump"]:
  check(kinds.has(kind),"distinct art archetype "+kind)

 var entrance: Dictionary=lab.doorways[0]
 lab.player=entrance.a.lerp(entrance.b,.5)+Vector2(0,-.72)
 lab._interact()
 check(bool(lab.doorways[0].open),"entrance still responds to INTERACT")

 lab.player=Vector2(1.5,1.6)
 lab._interact()
 check(int(lab.gameplay.inventory.get("canned_food",0))==1,"counter search gives existing loot")
 check(bool(lab.gameplay.examined.get("RESIDENTIAL HOUSE/kitchen_counter",false)),"search ownership persists by stable ID")
 lab.gameplay.hunger=40.0
 lab._use_selected()
 check(lab.gameplay.hunger>40.0,"food still changes hunger")
 check(not lab.gameplay.inventory.has("canned_food"),"use consumes existing item")

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
 var path:=ProjectSettings.globalize_path(LabState.SAVE_PATH)
 if FileAccess.file_exists(LabState.SAVE_PATH):
  DirAccess.remove_absolute(path)
 print("FIVE-BUILDING LAB: %d failures" % failures)
 lab.free()
 quit(1 if failures else 0)
