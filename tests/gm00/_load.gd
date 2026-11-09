extends SceneTree
func _initialize(): call_deferred("_r")
func _r():
    var s = load("res://scenes/gm00_world_sandbox.tscn").instantiate()
    root.add_child(s)
    for i in 5: await process_frame
    print("err='", s.validation_error, "' buildings=", s.world_buildings.size(), " problems=", s.layout_problems, " player=", s.player, " msg=", s.message)
    print(s.perf_stats())
    quit()
