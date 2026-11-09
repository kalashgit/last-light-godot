extends SceneTree
func _initialize()->void:
 call_deferred("run")
func run()->void:
 var source:=FileAccess.get_file_as_string("res://tests/fixtures/house_v1.json")
 var file:=FileAccess.open("user://last_light_v04.json",FileAccess.WRITE)
 file.store_string(source);file.close()
 DirAccess.remove_absolute(ProjectSettings.globalize_path("user://last_light_survival_v2.json"))
 var game=load("res://main.tscn").instantiate()
 root.add_child(game)
 game.set_process(false)
 assert(game.health==73 and game.supplies==2)
 game._set_paused(true)
 assert(FileAccess.get_file_as_string("user://last_light_v04.json")==source)
 assert(JSON.parse_string(FileAccess.get_file_as_string(game.SAVE_PATH)).version==3)
 assert(FileAccess.get_file_as_string(game.SAVE_PATH+".schema1.bak")==source)
 print("SAVE ISOLATION: candidate imports legacy progress, writes separate v2-path file at schema 3, legacy bytes unchanged PASS")
 game.free()
 quit()
