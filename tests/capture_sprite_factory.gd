extends SceneTree
func _initialize() -> void:
 call_deferred("run")
func run() -> void:
 var scene = load("res://scenes/sprite_factory_review.tscn").instantiate()
 root.add_child(scene)
 await process_frame
 await RenderingServer.frame_post_draw
 var error := root.get_texture().get_image().save_png("res://production/sprite_factory/evidence/godot_review.png")
 assert(error == OK)
 scene.free()
 quit()
