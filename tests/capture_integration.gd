extends SceneTree
## Portrait render evidence for the integration branch. Desktop/Xvfb capture, not iPhone proof.
## Usage: xvfb-run -a godot --path . --rendering-driver opengl3 --script tests/capture_integration.gd -- --output-dir=DIR [--scene=res://lab.tscn]
var output_dir := "/tmp/last-light-integration"
var scene := "res://main.tscn"
func _initialize() -> void:
 for arg in OS.get_cmdline_user_args():
  if arg.begins_with("--output-dir="): output_dir = arg.trim_prefix("--output-dir=")
  if arg.begins_with("--scene="): scene = arg.trim_prefix("--scene=")
 call_deferred("capture")
func shot(name: String) -> void:
 await process_frame
 await RenderingServer.frame_post_draw
 var path := "%s/%s.png" % [output_dir, name]
 assert(root.get_texture().get_image().save_png(path) == OK)
 print("CAPTURE ", path)
func capture() -> void:
 if DisplayServer.get_name() == "headless":
  printerr("Graphical display required"); quit(1); return
 DirAccess.make_dir_recursive_absolute(output_dir)
 root.size = Vector2i(720, 1152)
 root.content_scale_size = root.size
 var g = load(scene).instantiate()
 root.add_child(g)
 g.set_process(false)
 g._restart_game()
 g.god_mode = true
 var tag: String = scene.get_file().get_basename()
 var views: Array = g.capture_views() if g.has_method("capture_views") else []
 if views.is_empty():
  views = [{"name":"outdoor","p":Vector2(4.9, 9.35)}, {"name":"kitchen","p":Vector2(2.4, 2.5)}]
 for view in views:
  g.player = view.p
  g.camera_zoom = g._zoom_target()
  g.message_time = 0
  g._layout_controls()
  g.queue_redraw()
  await shot("%s-portrait-%s" % [tag, view.name])
 for id in ["ll_food_bean_tin", "ll_food_water_bottle", "ll_medical_sterile_bandage", "ll_tools_claw_hammer", "ll_golden_acorn"]:
  if g.survival.definitions.has(id): g.survival.add(id, 1)
 g._set_inventory(true)
 g.queue_redraw()
 await shot("%s-portrait-inventory" % tag)
 quit()
