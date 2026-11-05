extends SceneTree
func _initialize()->void:
 call_deferred("run")
func run()->void:
 var game=load("res://main.tscn").instantiate()
 root.add_child(game)
 game.set_process(false)
 game._set_paused(true)
 var previous:float=game.joystick_dead_zone
 game._tap(game.control_rects.deadzone_up.get_center())
 assert(game.paused and game.joystick_dead_zone>previous and game.joystick_touch==-1)
 var expected:float=game.joystick_dead_zone
 game.joystick_dead_zone=.05
 game._load_controls()
 assert(is_equal_approx(game.joystick_dead_zone,expected))
 game._set_dead_zone(4)
 assert(game.joystick_dead_zone==.35)
 game._set_dead_zone(-1)
 assert(game.joystick_dead_zone==.05)
 print("CONTROL SETTINGS: visible paused action, persistence and bounds PASS")
 game.free()
 quit()
