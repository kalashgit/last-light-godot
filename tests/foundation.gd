extends SceneTree
var failures := 0
func check(ok: bool, label: String) -> void:
 if not ok:
  push_error(label)
  failures += 1
func touch(game: Node, id: int, point: Vector2, pressed: bool) -> void:
 var e := InputEventScreenTouch.new()
 e.index = id
 e.position = point
 e.pressed = pressed
 game._input(e)
func _initialize() -> void:
 call_deferred("run")
func run() -> void:
 var game = load("res://main.tscn").instantiate()
 root.add_child(game)
 game.set_process(false)
 game._restart_game()
 check(game.doors.size() == 5, "Five functional doorways")
 var closed: Vector2 = game._try_move(Vector2(5.4, 8.5), Vector2(0, -1), .19)
 check(closed.y > 8.2, "Closed door blocks movement")
 game.doors[0].open = true
 var opened: Vector2 = game._try_move(Vector2(5.4, 8.5), Vector2(0, -1), .19)
 check(opened.y < 8, "Open door permits entry")
 game.player = Vector2(5.4, 8)
 game._toggle_door(0)
 check(game.doors[0].open, "Door cannot close on player")
 for direction in [Vector2.RIGHT, Vector2.DOWN, Vector2(1,1).normalized()]:
  var world: Vector2 = game._screen_direction_to_world(direction)
  var projected: Vector2 = game._iso(world)
  check(projected.normalized().dot(direction) > .999, "Movement follows screen direction")
 touch(game, 0, game.stick_center + Vector2(40,0), true)
 check(game.joystick_touch == 0 and game.joystick_vector.x > 0, "Joystick captures finger")
 touch(game, 1, game.control_rects.attack.get_center(), true)
 check(game.joystick_touch == 0 and game.attack_cooldown > 0, "Attack works while movement finger remains captured")
 var mouse := InputEventMouseButton.new()
 mouse.button_index = MOUSE_BUTTON_LEFT
 mouse.pressed = true
 mouse.device = InputEvent.DEVICE_ID_EMULATION
 mouse.position = game.stick_center
 game._input(mouse)
 check(game.joystick_touch == 0, "Emulated mouse cannot steal touch")
 touch(game, 1, Vector2.ZERO, false)
 check(game.joystick_touch == 0, "Unrelated release preserves movement")
 touch(game, 0, Vector2.ZERO, false)
 check(game.joystick_touch == -1 and game.joystick_vector == Vector2.ZERO, "Release clears stick")
 game.player = Vector2(2, 3.7)
 game.infected[0] = Vector2(2, 4.3)
 game.attack_cooldown = 0
 game._attack()
 check(game.zombie_health[0] == 3, "Wall blocks melee")
 game.player = Vector2(2, 4.7)
 game.attack_cooldown = 0
 game._attack()
 check(game.zombie_health[0] == 2, "Reachable zombie takes melee damage")
 game.health = 73
 game.supplies = 2
 game.items[0].searched = true
 game.zombie_health[0] = 0
 var path := "user://foundation-test.json"
 check(game._save_game(path) == OK, "Save succeeds")
 game.health = 10
 game.doors[0].open = false
 check(game._load_game(path) == OK, "Load succeeds")
 check(game.health == 73 and game.supplies == 2 and game.items[0].searched and game.zombie_health[0] == 0 and game.doors[0].open, "World and player round trip")
 var file := FileAccess.open(path, FileAccess.WRITE)
 file.store_string('{"version": 999}')
 file.close()
 check(game._load_game(path) != OK and game.health == 73, "Invalid save rejected without changing state")
 game._set_paused(true)
 var before: Vector2 = game.player
 game._process(.05)
 check(game.player == before, "Pause freezes simulation")
 game.health = 0
 game._set_paused(false)
 game._process(.05)
 check(game.player == before, "Death freezes simulation")
 game._restart_game()
 check(game.health == 100 and game.supplies == 0 and game.zombie_health[0] == 3, "Restart restores fresh world")
 DirAccess.remove_absolute(ProjectSettings.globalize_path(path))
 print("FOUNDATION: %d failures" % failures)
 game.free()
 quit(1 if failures else 0)
