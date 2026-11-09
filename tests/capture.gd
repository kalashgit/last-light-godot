extends SceneTree
func _initialize() -> void:
 call_deferred("capture")
func capture() -> void:
 var game = load("res://main.tscn").instantiate()
 root.add_child(game)
 game.set_process(false)
 game._restart_game()
 for view in ["exterior", "interior"]:
  if view == "interior":
   game.player = Vector2(3, 5)
   game.doors[0].open = true
  game.queue_redraw()
  await process_frame
  await RenderingServer.frame_post_draw
  var error := root.get_texture().get_image().save_png("res://docs/checkpoints/" + view + ".png")
  if error != OK:
   quit(1)
   return
 game.free()
 quit()
