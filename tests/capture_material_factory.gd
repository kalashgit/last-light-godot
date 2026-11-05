extends SceneTree
## Real renderer capture, isolated user directory supplied by the caller.
func _initialize() -> void:
 call_deferred("capture")
func capture() -> void:
 var viewport:=SubViewport.new()
 viewport.size=Vector2i(1920,1080)
 viewport.render_target_update_mode=SubViewport.UPDATE_ALWAYS
 root.add_child(viewport)
 var lab=load("res://scenes/five_building_material_lab.tscn").instantiate()
 viewport.add_child(lab)
 lab.set_process(false)
 lab.player=Vector2(20,14)
 var prefix:=OS.get_environment("LL_CAPTURE_PREFIX")
 if prefix.is_empty(): prefix="res://docs/checkpoints/modular-factory/current"
 for roofs in [true,false]:
  lab.show_roofs=roofs
  lab.queue_redraw()
  await process_frame
  await RenderingServer.frame_post_draw
  var suffix:="-roofs-on.png" if roofs else "-roofs-off.png"
  if viewport.get_texture().get_image().save_png(prefix+suffix)!=OK:
   quit(1)
   return
 lab.free()
 var gallery=load("res://scenes/material_registry_gallery.tscn").instantiate()
 viewport.add_child(gallery)
 await process_frame
 await RenderingServer.frame_post_draw
 if viewport.get_texture().get_image().save_png(prefix+"-materials.png")!=OK:
  quit(1)
  return
 gallery.free()
 quit()
