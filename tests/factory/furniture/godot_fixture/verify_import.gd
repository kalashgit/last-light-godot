extends SceneTree

# Standalone, headless Godot 4 importer smoke test. Requires model.glb copied
# beside project.godot. Does not mutate the LAST LIGHT playable project.

func _initialize() -> void:
	var model_path := "res://model.glb"
	var packed := ResourceLoader.load(model_path)
	if packed == null or not packed is PackedScene:
		push_error("F01_IMPORT_FAIL: GLB PackedScene unavailable")
		quit(2)
		return
	var instance := (packed as PackedScene).instantiate()
	root.add_child(instance)
	var players := instance.find_children("*", "AnimationPlayer", true, false)
	var mesh_nodes := instance.find_children("*", "MeshInstance3D", true, false)
	if players.is_empty() or mesh_nodes.size() < 20:
		push_error("F01_IMPORT_FAIL: missing animation or mesh hierarchy")
		quit(3)
		return
	var playable := false
	for player_node in players:
		var player := player_node as AnimationPlayer
		for animation_name in player.get_animation_list():
			var clip := player.get_animation(animation_name)
			if clip != null and clip.length > 0.0 and clip.get_track_count() > 0:
				player.play(animation_name)
				player.advance(clip.length)
				playable = true
	if not playable:
		push_error("F01_IMPORT_FAIL: no playable hinge animation")
		quit(4)
		return
	print("F01_GODOT_GLTF_IMPORT_PASS meshes=", mesh_nodes.size(), " players=", players.size())
	quit(0)
