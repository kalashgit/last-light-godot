extends SceneTree
## Smoke-test that the actual Godot runtime can import and display all 12 PNGs.

func _initialize() -> void:
 call_deferred("_run")

func _run() -> void:
 var scene: PackedScene = load("res://scenes/terrain_tile_lab.tscn")
 assert(scene != null, "Terrain lab scene missing")
 var lab = scene.instantiate()
 root.add_child(lab)
 await process_frame
 assert(lab.tile_count == 12, "Incorrect imported candidate count")
 assert(lab.tiles.has("ll_tile_grass_sparse_to_asphalt_worn_c04"), "Transition missing")
 print("LL_TERRAIN_GODOT_PREVIEW_PASS", lab.tile_count)
 quit(0)
