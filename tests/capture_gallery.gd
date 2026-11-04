extends SceneTree
func _initialize() -> void:
 call_deferred("run")
func run() -> void:
 var gallery = load("res://scenes/asset_gallery.tscn").instantiate()
 root.add_child(gallery)
 for mode in ["icon","ground","held"]:
  gallery.mode=mode
  gallery.page=14 if mode=="ground" else 5 if mode=="held" else 0
  gallery._refresh()
  await process_frame
  await RenderingServer.frame_post_draw
  if root.get_texture().get_image().save_png("res://docs/asset-factory/gallery_"+mode+".png")!=OK:
   quit(1)
   return
 gallery.free()
 quit()
