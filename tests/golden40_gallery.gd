extends SceneTree

func _initialize() -> void:
 call_deferred("run")

func run() -> void:
 var gallery = load("res://scenes/golden40_gallery.tscn").instantiate()
 root.add_child(gallery)
 await process_frame
 assert(gallery.objects.size() == 40)
 assert(gallery.grid.get_child_count() == 20)
 assert(gallery.page == 0)
 var first_card = gallery.grid.get_child(0)
 var first_texture = first_card.get_child(0).get_child(0)
 assert(first_texture.texture != null)
 gallery._turn(1)
 assert(gallery.page == 1 and gallery.grid.get_child_count() == 20)
 gallery._turn(1)
 assert(gallery.page == 0)
 gallery._turn(-1)
 assert(gallery.page == 1)
 gallery.size = Vector2(390, 844)
 gallery._on_resized()
 assert(gallery.grid.columns == 2)
 gallery.size = Vector2(1170, 800)
 gallery._on_resized()
 assert(gallery.grid.columns == 5)
 gallery.free()
 print("GOLDEN40 GODOT: 40 icons, two pages, textures, responsive grid PASS")
 quit()
