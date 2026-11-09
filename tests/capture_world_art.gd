extends SceneTree
## Matched actual Godot views. No source artwork is generated or transformed here.
var output_dir := "/tmp/last-light-world-art"
func _initialize() -> void:
 for arg in OS.get_cmdline_user_args():
  if arg.begins_with("--output-dir="): output_dir=arg.trim_prefix("--output-dir=")
 call_deferred("capture")
func capture() -> void:
 if DisplayServer.get_name()=="headless":
  printerr("Graphical display required");quit(1);return
 DirAccess.make_dir_recursive_absolute(output_dir)
 root.size=Vector2i(1280,800)
 root.content_scale_size=root.size
 var g=load("res://main.tscn").instantiate()
 root.add_child(g)
 g.set_process(false)
 g._restart_game()
 g.god_mode=true
 g.zombie_health=[0,0]
 for door in g.doors: door.open=true
 var ids=["ll_golden_acorn","ll_golden_aerosol_canister","ll_golden_aluminum_scrap","ll_golden_ammunition_case"]
 # Only exact existing definitions; probes are explicitly synthetic QA placements.
 var valid:Array=[]
 for id in ids:
  if g.survival.definitions.has(id):valid.append(id)
 var views=[{"name":"kitchen","p":Vector2(2.4,2.5)}, {"name":"bedroom","p":Vector2(6.2,2.5)}, {"name":"living","p":Vector2(3,5)}, {"name":"bathroom","p":Vector2(6.2,5.7)}, {"name":"outdoor","p":Vector2(4.9,9.35)}]
 for view in views:
  g.player=view.p
  g.drops.clear()
  for n in range(valid.size()):g.drops.append({"id":valid[n],"count":1,"pos":view.p+Vector2(-.7+n*.45,.65)})
  for zoom in [1.0,2.2,3.25]:
   g.camera_zoom=zoom
   g.message_time=0
   g._layout_controls()
   g.queue_redraw()
   await process_frame
   await RenderingServer.frame_post_draw
   var path="%s/%s-%d.png"%[output_dir,view.name,roundi(zoom*100)]
   assert(root.get_texture().get_image().save_png(path)==OK)
   print("CAPTURE ",path)
 # Whole Golden set: each must remain a tiny marker; original icons still live in HUD.
 g.player=Vector2(12,12)
 g.camera_zoom=2.2
 g.drops.clear()
 var all_ids:Array=[]
 for id in g.survival.definitions:
  if id.begins_with("ll_golden_"):all_ids.append(id)
 all_ids.sort()
 for i in range(all_ids.size()):g.drops.append({"id":all_ids[i],"count":1,"pos":Vector2(10.5+(i%8)*.4,11+(i/8)*.4)})
 g.message_time=0
 g._layout_controls()
 g.queue_redraw()
 await process_frame
 await RenderingServer.frame_post_draw
 assert(root.get_texture().get_image().save_png(output_dir+"/all40-ground-markers-220.png")==OK)
 g.world_art_debug=true
 g.player=Vector2(2.4,2.5)
 g.queue_redraw()
 await process_frame
 await RenderingServer.frame_post_draw
 assert(root.get_texture().get_image().save_png(output_dir+"/inspector-kitchen-220.png")==OK)
 g.free()
 quit()
