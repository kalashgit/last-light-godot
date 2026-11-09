extends SceneTree
## Worker 04 Godot evidence: generated worlds load, collide, navigate, can be
## entered and looted, and persist by stable IDs. Synthetic engine input only;
## actual iPhone/Xogot input and performance remain UNVERIFIED.

var failures := 0
var checks := 0

func check(ok: bool, label: String) -> void:
 checks += 1
 if not ok:
  failures += 1
  push_error("WORLDGEN CHECK FAILED: " + label)

func _initialize() -> void:
 call_deferred("run")

func load_game(scene: String) -> Node:
 var game = load(scene).instantiate()
 root.add_child(game)
 game.set_process(false)
 return game

func count_manifest(dir: String) -> Dictionary:
 var m: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(dir + "/world_manifest.json"))
 var doors := 0
 var furniture := 0
 var rooms := 0
 for entry in m.buildings:
  var b: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(dir + "/" + entry.file))
  for d in b.floors[0].doors:
   if d.kind != "opening": doors += 1
  furniture += b.floors[0].furniture.size() + b.get("stairs", []).size()
  rooms += b.floors[0].rooms.size()
 var district: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(dir + "/" + m.district.file))
 return {"doors": doors, "items": furniture + district.props.size(), "rooms": rooms, "fences": district.fences.size(), "manifest": m}

## A standing point that the game's own _target_valid accepts and the nav grid reaches.
func interaction_point(game, index: int) -> Variant:
 var item: Dictionary = game.items[index]
 var rect := Rect2(item.pos, item.size)
 var saved: Vector2 = game.player
 var result: Variant = null
 for ring in [.45, .7, 1.0]:
  for k in range(16):
   var dir := Vector2.RIGHT.rotated(TAU * k / 16.0)
   var p: Vector2 = rect.get_center() + Vector2(dir.x * (rect.size.x * .5 + ring), dir.y * (rect.size.y * .5 + ring))
   if game._blocked_static(p, .19) or game.navigation.path_between(game.spawn_point, p).is_empty(): continue
   game.player = p
   if game._target_valid({"kind": "container", "index": index}):
    result = p
    break
  if result != null: break
 game.player = saved
 return result

func walk_to(game, target: Vector2, max_steps := 4000) -> bool:
 var path: Array = game.navigation.path_between(game.player, target)
 if path.is_empty(): return false
 path.append(target)
 var steps := 0
 for waypoint in path:
  while game.player.distance_to(waypoint) > .12 and steps < max_steps:
   steps += 1
   var before: Vector2 = game.player
   game.player = game._try_move(game.player, (waypoint - game.player).limit_length(.1), game.PLAYER_RADIUS)
   if game.player.distance_to(before) < .001:
    var d: int = game._nearest_door()
    if d >= 0 and not game.doors[d].open:
     game.doors[d].open = true
    else:
     break
 return game.player.distance_to(target) < .3

func run() -> void:
 var started := Time.get_ticks_msec()
 for case in [["res://scenes/worldgen/neighborhood_playable.tscn", "res://data/worldgen/generated/w04_demo_suburb"],
   ["res://scenes/worldgen/lab_a_street.tscn", "res://data/worldgen/generated/lab_a_street"]]:
  var scene: String = case[0]
  var expected := count_manifest(case[1])
  var t0 := Time.get_ticks_msec()
  var game = load_game(scene)
  var load_ms := Time.get_ticks_msec() - t0
  game._restart_game()
  check(game.load_error.is_empty(), scene + " blueprint loaded: " + game.load_error)
  check(game.doors.size() == expected.doors, "door count matches blueprint %d/%d" % [game.doors.size(), expected.doors])
  check(game.items.size() == expected.items, "item count matches blueprint %d/%d" % [game.items.size(), expected.items])
  check(game.rooms.size() == expected.rooms, "ground rooms match blueprint")
  check(game.infected.size() > 0 and game.infected.size() <= 6, "infected spawned from generated spawn points")
  check(not game._blocked(game.player), "spawn is clear")
  check(game.current_building == -1 or game.building_at(game.player) == -1, "spawn is outdoors")
  for i in range(4): check(game.items[i].container, "first four items are containers (save contract)")
  # Every ground room and container is reachable through the engine's own collision grid.
  var unreachable_rooms := []
  for room in game.rooms:
   var target: Vector2 = room.rect.get_center()
   var ok := false
   for dy in range(int(room.rect.size.y)):
    for dx in range(int(room.rect.size.x)):
     var p: Vector2 = room.rect.position + Vector2(dx + .5, dy + .5)
     if not game._blocked_static(p, .21) and not game.navigation.path_between(game.spawn_point, p).is_empty():
      ok = true
      break
    if ok: break
   if not ok: unreachable_rooms.append(room.id)
  check(unreachable_rooms.is_empty(), "all ground rooms reachable in engine nav: " + str(unreachable_rooms))
  var unreachable_items := []
  for item in game.items:
   if not item.container: continue
   if not interaction_point(game, game.items.find(item)): unreachable_items.append(item.id)
  check(unreachable_items.size() == 0, "all containers have a reachable interaction point: " + str(unreachable_items.slice(0, 5)))
  # Walk into the first building's kitchen (or largest room) with real collision and door toggling.
  var target_room: Dictionary = {}
  for room in game.rooms:
   if room.building == 0 and room.type in ["kitchen", "sales", "bay"]:
    target_room = room
    break
  if target_room.is_empty(): target_room = game.rooms[0]
  var goal: Vector2 = Vector2.ZERO
  for dy in range(int(target_room.rect.size.y)):
   for dx in range(int(target_room.rect.size.x)):
    var p: Vector2 = target_room.rect.position + Vector2(dx + .5, dy + .5)
    if goal == Vector2.ZERO and not game._blocked_static(p, .25): goal = p
  game.god_mode = true
  check(walk_to(game, goal), "player walked from street into " + target_room.id)
  game._process(.016)
  check(game.current_building == 0, "indoor detection switches to the entered building")
  # Loot one container in that building through the real interact path.
  var looted := -1
  for i in range(game.items.size()):
   var item: Dictionary = game.items[i]
   if item.container and item.building == 0 and not item.loot.is_empty():
    var spot: Variant = interaction_point(game, i)
    for p in ([spot] if spot != null else []):
     if walk_to(game, p):
      game.selected_target = {"kind": "container", "index": i}
      if game._target_valid(game.selected_target):
       var before: int = game.survival.inventory.size()
       game._interact()
       if item.searched: looted = i
       check(game.survival.inventory.size() >= before, "inventory received generated loot")
       break
    if looted >= 0: break
  check(looted >= 0, "a generated container in building 0 was searched")
  var door_index := 0
  game.doors[door_index].open = true
  check(game._save_game() == OK, "world save written")
  var looted_id: String = game.items[looted].id if looted >= 0 else ""
  var door_id: String = game.doors[door_index].id
  var player_pos: Vector2 = game.player
  game.queue_free()
  await process_frame
  # Fresh instance: frozen blueprint + save delta restore identical identities.
  var again = load_game(scene)
  check(again.load_error.is_empty(), "reload uses frozen blueprint")
  check(again.player.distance_to(player_pos) < .05, "player position restored")
  var restored := false
  for item in again.items:
   if item.id == looted_id: restored = item.searched
  check(restored, "searched container restored by stable ID " + looted_id)
  check(again.doors[door_index].id == door_id and again.doors[door_index].open, "door state restored by stable ID")
  var identity: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(again.identity_path))
  check(identity.blueprint_sha256 == expected.manifest.blueprint_sha256, "save identity bound to blueprint hash")
  check(identity.delta.containers.get(looted_id, false), "ID-keyed save delta records the search")
  check(not FileAccess.file_exists("user://last_light_survival_v2.json"), "single-house game save untouched")
  # A save from a different blueprint must be refused, not silently applied.
  identity.blueprint_sha256 = "0".repeat(64)
  var f := FileAccess.open(again.identity_path, FileAccess.WRITE)
  f.store_string(JSON.stringify(identity))
  f.close()
  check(again._load_game() == ERR_INVALID_DATA, "mismatched blueprint identity refused")
  # Logic budget: 600 simulated 60 Hz steps with infected active (desktop, not iPhone).
  again._restart_game()
  again.god_mode = true
  var t1 := Time.get_ticks_usec()
  for i in range(600): again._step(1.0 / 60.0)
  var step_ms := float(Time.get_ticks_usec() - t1) / 600000.0
  print("WORLDGEN METRICS %s load_ms=%d nav_build_ms=%d walls=%d doors=%d items=%d mean_step_ms=%.3f" % [
   scene.get_file(), load_ms, again.navigation.build_msec, again.walls.size(), again.doors.size(), again.items.size(), step_ms])
  again.queue_free()
  await process_frame
 print("WORLDGEN GODOT: %d checks, %d failures (%d ms; synthetic input, iPhone/Xogot UNVERIFIED)" % [checks, failures, Time.get_ticks_msec() - started])
 quit(1 if failures else 0)
