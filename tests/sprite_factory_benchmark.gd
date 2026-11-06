extends SceneTree
## Synthetic static-icon rendering, not world simulation or phone performance.
func _initialize() -> void:
 call_deferred("run")
func run() -> void:
 Engine.max_fps = 0
 DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_DISABLED)
 var registry = load("res://scripts/sprite_production_registry.gd").new()
 var textures: Array[Texture2D] = []
 for id in registry.candidates:
  textures.append(registry.review_icon_for(id))
 var results: Array = []
 for count in [100,300,750,1500]:
  var container := Node2D.new()
  root.add_child(container)
  var started := Time.get_ticks_usec()
  for i in range(count):
   var sprite := Sprite2D.new()
   sprite.texture = textures[i % textures.size()]
   sprite.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
   sprite.position = Vector2(18 + (i % 50)*23,18 + int(i/50)*24)
   sprite.scale = Vector2(0.35,0.35)
   container.add_child(sprite)
  var setup_ms := (Time.get_ticks_usec() - started)/1000.0
  for i in range(10):
   await process_frame
   await RenderingServer.frame_post_draw
  var timings: Array[float] = []
  var last := Time.get_ticks_usec()
  for i in range(60):
   await process_frame
   await RenderingServer.frame_post_draw
   var now := Time.get_ticks_usec()
   timings.append((now-last)/1000.0)
   last = now
  timings.sort()
  results.append({"objects":count,"setup_ms":setup_ms,"frame_median_ms":timings[30],"frame_p95_ms":timings[57],"draw_calls":RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_DRAW_CALLS_IN_FRAME),"texture_memory_bytes":RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TEXTURE_MEM_USED)})
  container.free()
  await process_frame
 var report := {"engine":Engine.get_version_info().string,"scope":"Synthetic static candidate inventory Sprite2D stress; software desktop rendering; no AI, collision, world anchors or iPhone measurement","samples_per_count":60,"counts":results}
 var file := FileAccess.open("res://production/sprite_factory/evidence/benchmark.json",FileAccess.WRITE)
 file.store_string(JSON.stringify(report,"  "))
 file.close()
 print(JSON.stringify(report))
 quit()
