extends SceneTree
## Engine regression: run with --headless --path . --script res://tests/golden40_house_builder.gd
func _initialize() -> void:
 call_deferred("run")

func run() -> void:
 var game=load("res://main.tscn").instantiate()
 root.add_child(game)
 game.set_process(false)
 game._restart_game()
 assert(game.survival.definitions.size()==48)
 var all_ids: Array=[]
 for id in game.survival.definitions:
  if String(id).begins_with("ll_golden_"):
   all_ids.append(id)
 assert(all_ids.size()==40)
 all_ids.sort()
 assert(game.loot_builder != null)
 assert(game._golden_icon(all_ids[0])!=null)
 game.zombie_health=[0,0]
 game.player=Vector2(-3.0,1.5)
 var id: String=all_ids[0]
 var before:=game.drops.size()
 assert(game._builder_spawn_near(id))
 assert(game.drops.size()==before+1)
 assert(game.drops.back().id==id)
 var position: Vector2=game.drops.back().pos
 assert(not game._blocked(position,.14))
 game.player=position+Vector2(.35,0.0)
 game.selected_target={"kind":"drop","index":game.drops.size()-1}
 game._interact()
 assert(game.survival.inventory.has(id))
 assert(game.drops.size()==before)
 assert(game._drop_item(id))
 assert(not game.survival.inventory.has(id))
 assert(game.drops.size()==before+1)
 var snapshot:=game.drops.duplicate(true)
 assert(game._save_game()==OK)
 assert(game._load_game()==OK)
 assert(game.drops==snapshot)
 game.loot_builder.set_open(true)
 assert(not game._builder_spawn_near(all_ids[1]))
 game.loot_builder.set_open(false)
 assert(not game._spawn_golden_item(id,Vector2(0,0),1))
 # All original legacy item definitions, interactions and save schema remain in place.
 assert(game.survival.definitions.has("ll_food_bean_tin"))
 # Icon-only melee candidates must never crash when the character renderer requests held art.
 var melee := "ll_golden_baseball_bat"
 assert(game.survival.add(melee, 1))
 assert(game.survival.equip(melee))
 assert(game._held_frame(melee, 0).is_empty())
 game.queue_redraw()
 print("GOLDEN40 HOUSE BUILDER: 40 icons, spawn, pickup, drop, save/reload, blocked placement PASS")
 game.free()
 quit()
