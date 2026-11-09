extends SceneTree
## Rendered capture of the isolated V2 calibration fixture (needs a display).
func _initialize() -> void:
 call_deferred("run")
func run() -> void:
 var out := "/tmp/last-light-worldgen-captures"
 for a: String in OS.get_cmdline_user_args():
  if a.begins_with("--output-dir="): out = a.trim_prefix("--output-dir=")
 var game = load("res://scripts/worldgen/worldgen_game.gd").new()
 game.world_dir = "res://tests/worldgen/generated_v2/world"
 root.add_child(game)
 game.set_process(false)
 root.size = Vector2i(1280, 800)
 for item in game.items:
  if item.kind == "fridge":
   game.player = item.pos + Vector2(1.2, 1.2)
   if game._blocked(game.player): game.player = game._clear_saved_position(game.player)
   break
 game.current_building = game.building_at(game.player)
 game.camera_zoom = game.INDOOR_ZOOM if game.current_building >= 0 else 1.0
 for d in game.doors: d.open = true
 game.queue_redraw()
 await process_frame
 await RenderingServer.frame_post_draw
 root.get_texture().get_image().save_png(out + "/v2-calibration-fixture-fridge.png")
 game.player = game.spawn_point
 game.current_building = -1
 game.camera_zoom = 1.0
 game.queue_redraw()
 await process_frame
 await RenderingServer.frame_post_draw
 root.get_texture().get_image().save_png(out + "/v2-calibration-fixture-street.png")
 print("CAPTURE V2 done")
 quit(0)
