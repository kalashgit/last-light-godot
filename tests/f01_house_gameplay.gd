extends SceneTree
## Exercises the real playable house, SurvivalState, targeting and save I/O.
## Synthetic input only; not a claim of physical iPhone/Xogot verification.

const FRIDGE := "house.kitchen.fridge"
const SAVE_TEST := "user://f01_refrigerator_gameplay_test.json"
var failures: Array[String] = []
var checks := 0


func _initialize() -> void:
 call_deferred("run")


func check(condition: bool, label: String) -> void:
 checks += 1
 if not condition:
  failures.append(label)
  printerr("F01_HOUSE_FAIL: ",label)


func run() -> void:
 var game: Variant = load("res://main.tscn").instantiate()
 root.add_child(game)
 game.set_process(false)
 game._restart_game()
 for i in range(game.zombie_health.size()): game.zombie_health[i] = 0
 var fridge_index: int = game._fridge_index()
 check(fridge_index >= 4 and game.items[fridge_index].id == FRIDGE, "furnished enterable house retains kitchen refrigerator and legacy container slots")
 check(not game.refrigerator.door_open and not game.refrigerator.drawer_open, "refrigerator initially closed")
 game.player = Vector2(0.7,1.4)
 var target := {"kind":"refrigerator","index":fridge_index}
 check(game._target_valid(target), "interactable refrigerator reachable from inside kitchen")
 check(not game._blocked(game.player), "player can stand beside refrigerator")
 game.selected_target = target
 check(game._context_prompt() == "Open Refrigerator", "real HUD prompt shows refrigerator action")
 var initial_inventory: Dictionary = game.survival.snapshot()
 game._interact()
 check(game.refrigerator.door_open and not game.refrigerator.drawer_open, "main door opens independently")
 check(game._context_prompt() == "Open Crisper", "second action prompts drawer opening")
 game._interact()
 check(game.refrigerator.door_open and game.refrigerator.drawer_open, "crisper opens without closing main door")
 check(game._context_prompt() == "Collect Crisper Contents", "contents exposed only after drawer opens")
 game._interact()
 check(game.refrigerator.contents_claimed and game.survival.inventory.get("ll_food_bean_tin",0)==1 and game.survival.inventory.get("ll_food_water_bottle",0)==1, "real inventory receives one of each item")
 check(game._context_prompt() == "Close Crisper", "searched contents cannot be collected again")
 var collected_inventory: Dictionary = game.survival.snapshot()
 game._interact()
 check(not game.refrigerator.drawer_open and game.refrigerator.door_open, "drawer closes independently")
 game._interact()
 check(not game.refrigerator.door_open, "main door closes after drawer")
 game._interact()
 game._interact()
 check(game.refrigerator.drawer_open and game.survival.snapshot() == collected_inventory, "reopening empty crisper never duplicates real loot")
 check(game._save_game(SAVE_TEST)==OK, "refrigerator state saved using real game serializer")
 var saved: Dictionary = game.refrigerator.snapshot()
 game.refrigerator.reset()
 game.survival.restore(initial_inventory)
 check(game._load_game(SAVE_TEST)==OK and game.refrigerator.snapshot()==saved and game.survival.snapshot()==collected_inventory, "full gameplay save/load restores door, crisper, looted flag and inventory")
 var legacy_v2: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(SAVE_TEST))
 legacy_v2.erase("appliances")
 var old := FileAccess.open(SAVE_TEST+".old",FileAccess.WRITE)
 old.store_string(JSON.stringify(legacy_v2))
 old.close()
 check(game._load_game(SAVE_TEST+".old")==OK and not game.refrigerator.door_open and not game.refrigerator.contents_claimed, "older schema-2 saves without appliance field load safely")
 var invalid: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(SAVE_TEST))
 invalid.appliances[FRIDGE].door_open = false
 invalid.appliances[FRIDGE].drawer_open = true
 var corrupted := FileAccess.open(SAVE_TEST+".invalid",FileAccess.WRITE)
 corrupted.store_string(JSON.stringify(invalid))
 corrupted.close()
 var stable: Dictionary = game.refrigerator.snapshot()
 check(game._load_game(SAVE_TEST+".invalid")==ERR_INVALID_DATA and game.refrigerator.snapshot()==stable, "invalid appliance state rejected without mutating world")
 game.player=Vector2(8.0,7.0)
 check(not game._target_valid(target), "distant player cannot operate refrigerator remotely")
 for suffix in ["", ".old", ".invalid", ".bak"]:
  var filename: String = SAVE_TEST+suffix
  if FileAccess.file_exists(filename): DirAccess.remove_absolute(ProjectSettings.globalize_path(filename))
 game.free()
 print("F01_HOUSE_GAMEPLAY: %d checks, %d failures (actual main.tscn state/save/loot; iPhone hardware unverified)" % [checks,failures.size()])
 quit(0 if failures.is_empty() else 1)
