extends SceneTree
var failures:=0
func check(value:bool,label:String)->void:
 if not value:
  failures+=1
  push_error(label)
func _initialize()->void:
 call_deferred("run")
func run()->void:
 var game=load("res://main.tscn").instantiate()
 root.add_child(game)
 game.set_process(false)
 var distances:Array=[]
 for fps in [30,60,120]:
  game._restart_game()
  game.player=Vector2(-5,-5)
  game.zombie_health=[0,0]
  game.joystick_touch=1
  game.joystick_vector=Vector2.RIGHT
  var start:Vector2=game.player
  for i in range(fps*2): game._process(1.0/fps)
  distances.append(game.player.distance_to(start))
 check(absf(distances[0]-distances[2])<.01,"frame independent walking")
 game._clear_pointers()
 game.player=Vector2(-5,-5)
 game.facing=Vector2.RIGHT
 game.infected=[Vector2(-4.2,-5),Vector2(-5.8,-5)]
 game.zombie_health=[3,3]
 game.stamina=100
 game._attack()
 check(game.zombie_health[0]==2 and game.zombie_health[1]==3,"directional melee")
 var energy:float=game.stamina
 game._attack()
 check(game.stamina==energy,"cooldown prevents repeat")
 var before:Vector2=game.infected[0]
 game._shove()
 check(game.infected[0].distance_to(before)>.4 and game.zombie_health[0]==2,"shove creates space without damage")
 game.stamina=0
 game.attack_cooldown=0
 game._attack()
 check(game.zombie_health[0]==2,"exhausted attack rejected")
 game._set_inventory(true)
 var position:Vector2=game.player
 game._process(.2)
 check(game.paused and game.player==position,"inventory is modal")
 print("PLAYER MECHANICS: %d failures, distances %s"%[failures,str(distances)])
 game.free()
 quit(1 if failures else 0)
