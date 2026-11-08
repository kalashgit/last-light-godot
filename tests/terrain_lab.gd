extends SceneTree
## Smoke-test that the actual Godot runtime can import and display all 12 PNGs.

func _initialize() -> void:
 call_deferred("_run")

func _run() -> void:
 var scene: PackedScene = load("res://scenes/terrain_tile_lab.tscn")
 if scene == null:
  push_error("Terrain lab scene missing")
  quit(1)
  return
 var lab = scene.instantiate()
 root.add_child(lab)
 if lab.tile_count != 12 or not lab.tiles.has("ll_tile_grass_sparse_to_asphalt_worn_c04"):
  push_error("Incorrect terrain candidate count or transition import")
  quit(1)
  return
 print("LL_TERRAIN_GODOT_PREVIEW_PASS", lab.tile_count)
 lab.free()
 quit(0)
