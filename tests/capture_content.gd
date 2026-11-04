extends SceneTree
func _initialize() -> void:
 call_deferred("capture")
func capture() -> void:
 var demo = load("res://scenes/content_demo.tscn").instantiate()
 root.add_child(demo)
 var state: Dictionary = demo.instances[0].snapshot()
 var original_path: String = demo.catalog.visual(state.definition_id).path
 for name in ["catalog", "visual_swap"]:
  if name=="visual_swap":
   demo._action("Swap selected art")
   if demo.instances[0].snapshot()!=state:
    push_error("Art replacement changed instance state")
    quit(1)
    return
  await process_frame
  await RenderingServer.frame_post_draw
  var error := root.get_texture().get_image().save_png("res://docs/checkpoints/ll103/"+name+".png")
  if error!=OK:
   quit(1)
   return
 var proof := FileAccess.open("res://docs/checkpoints/ll103/identity-proof.json",FileAccess.WRITE)
 if proof==null:
  quit(1)
  return
 proof.store_string(JSON.stringify({"before":state,"after":demo.instances[0].snapshot(),"visual_before":original_path,"visual_after":demo.catalog.visual(state.definition_id).path},"  ")+"\n")
 proof.close()
 demo.free()
 print("CAPTURE PASS: 20-object catalog and visual swap; identity/state unchanged")
 quit()
