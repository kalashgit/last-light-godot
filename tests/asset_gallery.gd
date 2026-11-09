extends SceneTree
func _initialize() -> void:
 call_deferred("run")
func run() -> void:
 var scene = load("res://scenes/asset_gallery.tscn").instantiate()
 root.add_child(scene)
 if scene.objects.size() != 300:
  push_error("Expected 300 factory objects")
  quit(1)
  return
 var frames := 0
 for item in scene.objects:
  for frame in item.frames:
   var texture = load("res://assets/generated/factory/"+frame.file)
   if not texture is Texture2D or texture.get_width()!=frame.size_px[0] or texture.get_height()!=frame.size_px[1]:
    push_error("Missing or incorrectly sized factory texture: "+frame.file)
    quit(1)
    return
   frames+=1
 for mode in ["icon","ground","held"]:
  scene.mode=mode
  for page in range(15):
   scene.page=page
   scene._refresh()
   if scene.grid.get_child_count()!=20:
    push_error("Incomplete gallery page")
    quit(1)
    return
   await process_frame
 print("GALLERY PASS: 300 objects, %d textures, 45 page/mode combinations" % frames)
 scene.free()
 quit()
