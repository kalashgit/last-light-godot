extends SceneTree
func _initialize()->void:
 call_deferred("run")
func run()->void:
 var game=load("res://main.tscn").instantiate()
 root.add_child(game)
 game.set_process(false)
 var data:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://tests/fixtures/house_v1.json"))
 data.stamina=999
 data.hunger=true
 data.thirst="invalid legacy extension"
 data.enemies[0]={"x":1.5,"y":1.4,"health":3}
 var path:="user://migration-edge.json"
 var file:=FileAccess.open(path,FileAccess.WRITE)
 file.store_string(JSON.stringify(data));file.close()
 assert(game._load_game(path)==OK)
 assert(game.stamina==100 and game.hunger==0 and game.thirst==0)
 assert(not game._blocked_static(game.infected[0],.17) and game.zombie_health[0]==3)
 assert(game.supplies==2 and game.survival.inventory.ll_food_bean_tin==2 and game.survival.inventory.ll_food_water_bottle==2 and game.survival.inventory.ll_medical_sterile_bandage==2)
 DirAccess.remove_absolute(ProjectSettings.globalize_path(path))
 print("MIGRATION EDGES: legacy extras ignored, obstructed actor relocated, caches converted without losing counters PASS")
 game.free()
 quit()
