extends SceneTree
## Integration regression: PR #18 portrait joystick + inventory thumbnails on the #26 HUD.
## Synthetic viewport sizes only; this is not iPhone/Xogot verification.
var failures := 0
func check(ok: bool, label: String) -> void:
 if not ok:
  failures += 1
  printerr("INTEGRATION HUD FAIL: ", label)
func _initialize() -> void:
 call_deferred("run")
func run() -> void:
 var game = load("res://main.tscn").instantiate()
 root.add_child(game)
 game.set_process(false)
 game._restart_game()
 # Portrait phone-class logical sizes (project default plus two iPhone aspect ratios).
 for size in [Vector2i(720, 1152), Vector2i(720, 1560), Vector2i(720, 1280)]:
  root.size = size
  root.content_scale_size = size
  game._layout_controls()
  var rects: Dictionary = game.control_rects
  var stick: Rect2 = rects.joystick_rect
  var safe: Rect2 = rects.safeRect
  check(safe.encloses(stick), "joystick inside safe area at %s" % [size])
  for name in ["attack","interact","shove","sprint","sneak","inventory","pause","zoom_in","zoom_out","quick0","quick1","quick2","quick3"]:
   check(not stick.intersects(rects[name]), "joystick clear of %s at %s" % [name, size])
  var prompt_y: float = safe.end.y - 470.0
  check(prompt_y + 38.0 <= stick.position.y, "context prompt above joystick at %s" % [size])
  check(is_equal_approx(game.stick_center.x, safe.position.x + 215.0), "founder portrait stick x at %s" % [size])
 # Every base survival item and every Golden 40 item resolves a thumbnail.
 var missing: Array = []
 for id in game.survival.definitions:
  if game._item_icon(id) == null: missing.append(id)
 check(missing.is_empty(), "inventory thumbnails missing: %s" % [missing])
 print("INTEGRATION HUD: %d definitions with thumbnails, %d failures" % [game.survival.definitions.size() - missing.size(), failures])
 quit(1 if failures > 0 else 0)
