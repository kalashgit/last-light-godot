extends SceneTree
const Registry := preload("res://scripts/sprite_production_registry.gd")
const Survival := preload("res://scripts/survival_state.gd")
func _initialize() -> void:
 call_deferred("run")
func run() -> void:
 var registry := Registry.new()
 assert(registry.candidates.size() == 20)
 assert(registry.approved.is_empty())
 var existing := 0
 var survival_bound := 0
 var state := Survival.new()
 for id in registry.candidates:
  var icon: Texture2D = registry.review_icon_for(id)
  assert(icon != null and icon.get_size() == Vector2(64,64))
  var normal := registry.icon_for(id)
  if registry.definitions.has(id):
   existing += 1
   assert(normal != null and normal != icon)
  else:
   assert(normal == null)
  if state.definitions.has(id):
   survival_bound += 1
   assert(state.definitions[id].art_id == id)
 assert(existing == 17)
 assert(survival_bound == 6)
 assert(registry.icon_for("unknown_id") == null)
 var scene = load("res://scenes/sprite_factory_review.tscn").instantiate()
 root.add_child(scene)
 await process_frame
 assert(scene.grid.get_child_count() == 20)
 for px in [32,48,64]:
  scene.set_icon_size(px)
  assert(scene.icon_size == px and scene.grid.get_child_count() == 20)
 scene.toggle_background()
 scene.size = Vector2(390,844)
 scene._resize()
 assert(scene.grid.columns == 2)
 scene.free()
 print("SPRITE FACTORY GODOT PASS: 20 candidate imports, 17 existing IDs, 6 survival IDs; candidate isolation, fallback and 32/48/64 review controls")
 quit()
