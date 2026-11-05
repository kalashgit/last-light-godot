extends SceneTree
func _initialize()->void:
 call_deferred("run")
func run()->void:
 var game=load("res://main.tscn").instantiate()
 root.add_child(game)
 game.set_process(false)
 game._restart_game()
 game.zombie_health=[0,0]
 for door in game.doors: door.open=true
 var visits:Dictionary={"house.kitchen.counter":Vector2(1.5,2.2),"house.bedroom.bed":Vector2(6.7,2.4),"house.living.sofa":Vector2(1.8,5.95),"house.bathroom.medicine":Vector2(6.7,6.7),"house.bedroom.chest":Vector2(5.5,2.5)}
 for id in visits:
  var index:=-1
  for i in range(game.items.size()):
   if game.items[i].id==id:index=i
  assert(index>=0)
  game.player=visits[id]
  assert(not game._blocked(game.player))
  game.selected_target={"kind":"container","index":index}
  assert(game._resolve_target()==game.selected_target)
  game._interact()
  assert(game.items[index].searched)
 assert(game.survival.inventory.size()==8)
 var snapshot:Dictionary=game.survival.snapshot()
 game.selected_target={"kind":"container","index":0}
 game._interact()
 assert(game.survival.snapshot()==snapshot)
 print("LOOT LOOP: five reachable containers yield all eight supported IDs; repeat search cannot duplicate PASS")
 game.free()
 quit()
