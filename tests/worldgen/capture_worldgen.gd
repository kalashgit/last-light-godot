extends SceneTree
## Real rendered captures of generated worlds (needs a display, e.g. xvfb-run).
## Desktop viewport emulation only; never iPhone/Xogot verification.

var output_dir := "/tmp/last-light-worldgen-captures"

func _initialize() -> void:
 for argument: String in OS.get_cmdline_user_args():
  if argument.begins_with("--output-dir="):
   output_dir = argument.trim_prefix("--output-dir=")
 call_deferred("capture")

func room_point(game, building: int, types: Array) -> Vector2:
 for room in game.rooms:
  if room.building == building and room.type in types:
   for dy in range(int(room.rect.size.y)):
    for dx in range(int(room.rect.size.x)):
     var p: Vector2 = room.rect.position + Vector2(dx + .5, dy + .5)
     if not game._blocked_static(p, .25): return p
 return game.spawn_point

func capture() -> void:
 if DisplayServer.get_name() == "headless":
  printerr("CAPTURE: requires a graphical display")
  quit(1)
  return
 DirAccess.make_dir_recursive_absolute(output_dir)
 var shots := [
  {"scene": "neighborhood_playable", "name": "suburb-street-spawn", "at": "spawn"},
  {"scene": "neighborhood_playable", "name": "suburb-starter-house-kitchen", "at": ["building", 4, ["kitchen", "living"]]},
  {"scene": "neighborhood_playable", "name": "suburb-two-storey-ground", "at": ["building", 1, ["living", "kitchen"]]},
  {"scene": "neighborhood_playable", "name": "suburb-corner-store", "at": ["building", 2, ["sales"]]},
  {"scene": "neighborhood_playable", "name": "suburb-behind-house-roof-ghost", "at": "behind"},
  {"scene": "lab_a_street", "name": "lab-a-street-overview", "at": "spawn"},
  {"scene": "lab_a_street", "name": "lab-a-h03-birch-garage", "at": ["building", 0, ["garage"]]},
  {"scene": "lab_a_street", "name": "lab-a-s01-corner-supply", "at": ["building", 1, ["sales"]]},
 ]
 var game = null
 var loaded := ""
 for shot in shots:
  if loaded != shot.scene:
   if game: game.queue_free()
   await process_frame
   game = load("res://scenes/worldgen/%s.tscn" % shot.scene).instantiate()
   root.add_child(game)
   game.set_process(false)
   game._restart_game()
   game.god_mode = true
   for door in game.doors: door.open = true
   loaded = shot.scene
  root.size = Vector2i(1280, 800)
  root.content_scale_size = Vector2i(1280, 800)
  await process_frame
  if shot.at is String and shot.at == "spawn":
   game.player = game.spawn_point
  elif shot.at is String and shot.at == "behind":
   var fp: Rect2 = game.building_meta[0].footprint[0]
   game.player = Vector2(fp.get_center().x, fp.position.y - 1.2)
   if game._blocked(game.player): game.player = game._clear_saved_position(game.player)
  else:
   game.player = room_point(game, shot.at[1], shot.at[2])
  game.current_building = game.building_at(game.player)
  game.camera_zoom = game.INDOOR_ZOOM if game.current_building >= 0 else 1.0
  game.message_time = 0
  game._layout_controls()
  game.queue_redraw()
  await process_frame
  await RenderingServer.frame_post_draw
  var image := root.get_texture().get_image()
  var path := "%s/%s.png" % [output_dir, shot.name]
  if image.save_png(path) != OK:
   printerr("CAPTURE: failed " + path)
   quit(1)
   return
  print("CAPTURE: %s building=%d player=%s" % [path, game.current_building, game.player])
 quit(0)
