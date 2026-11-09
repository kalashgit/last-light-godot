extends SceneTree

const FridgeInteraction = preload("res://fridge_interaction.gd")

# Standalone Godot 4 gameplay-contract fixture, NOT production gameplay code.
# Requires model.glb beside project.godot. Tests independent visual interactions.

func _fail(message: String, code: int) -> void:
	push_error(message)
	quit(code)


func _find_clip(player: AnimationPlayer, keyword: String) -> StringName:
	for animation_name in player.get_animation_list():
		if str(animation_name).to_lower().contains(keyword):
			return animation_name
	return &""


func _play_until_near_end(player: AnimationPlayer, clip_name: StringName) -> void:
	var clip := player.get_animation(clip_name)
	player.play(clip_name)
	player.advance(0.0)
	player.advance(clip.length * 0.95)

func _initialize() -> void:
	var model_path := "res://model.glb"
	var packed := ResourceLoader.load(model_path)
	if packed == null or not packed is PackedScene:
		_fail("F01_IMPORT_FAIL: GLB PackedScene unavailable", 2)
		return
	var instance := (packed as PackedScene).instantiate()
	root.add_child(instance)
	var players := instance.find_children("*", "AnimationPlayer", true, false)
	var mesh_nodes := instance.find_children("*", "MeshInstance3D", true, false)
	# Godot 4 sanitizes Blender/glTF node dots to underscores on scene import.
	var door := instance.find_child("hinge_local_main_door", true, false) as Node3D
	var crisper := instance.find_child("slide_local_crisper_drawer", true, false) as Node3D
	var freezer := instance.find_child("hinge_local_freezer_flap", true, false) as Node3D
	var imported_pivots: Array[String] = []
	for node in instance.find_children("*", "Node3D", true, false):
		var found_name := str(node.name)
		if found_name.contains("hinge") or found_name.contains("slide") or found_name.contains("freezer"):
			imported_pivots.append(found_name)
	print("F01_IMPORT_DIAGNOSTIC meshes=", mesh_nodes.size(), " players=", players.size(),
		" door=", door != null, " crisper=", crisper != null, " freezer=", freezer != null,
		" pivot_names=", imported_pivots)
	if players.is_empty() or mesh_nodes.size() < 70 or door == null or crisper == null or freezer == null:
		_fail("F01_IMPORT_FAIL: missing mesh, hinge or drawer hierarchy", 3)
		return
	var player := players[0] as AnimationPlayer
	var door_clip := _find_clip(player, "door")
	var crisper_clip := _find_clip(player, "crisper")
	if door_clip == &"" or crisper_clip == &"":
		_fail("F01_IMPORT_FAIL: independent door/crisper clips missing", 4)
		return
	var door_rest := door.quaternion
	var drawer_rest := crisper.position
	_play_until_near_end(player, door_clip)
	var door_angle := door_rest.angle_to(door.quaternion)
	var drawer_move_during_door := drawer_rest.distance_to(crisper.position)
	if door_angle < 0.7 or drawer_move_during_door > 0.002:
		_fail("F01_INTERACTION_FAIL: door clip motion missing or drawer wrongly coupled", 5)
		return
	var fridge := FridgeInteraction.new()
	if fridge.toggle_drawer() or fridge.toggle_freezer() or fridge.can_access("crisper"):
		_fail("F01_INTERACTION_FAIL: closed appliance allowed inner access", 6)
		return
	# On a fresh scene, the drawer clip should move only the drawer pivot.
	var fresh := (packed as PackedScene).instantiate()
	root.add_child(fresh)
	var fresh_player := fresh.find_children("*", "AnimationPlayer", true, false)[0] as AnimationPlayer
	var fresh_door := fresh.find_child("hinge_local_main_door", true, false) as Node3D
	var fresh_drawer := fresh.find_child("slide_local_crisper_drawer", true, false) as Node3D
	var fresh_door_rest := fresh_door.quaternion
	var fresh_drawer_rest := fresh_drawer.position
	_play_until_near_end(fresh_player, crisper_clip)
	var drawer_travel := fresh_drawer_rest.distance_to(fresh_drawer.position)
	var door_move_during_drawer := fresh_door_rest.angle_to(fresh_door.quaternion)
	if drawer_travel < 0.08 or door_move_during_drawer > 0.002:
		_fail("F01_INTERACTION_FAIL: drawer clip motion missing or door wrongly coupled", 7)
		return
	# Verify access states and deterministic persistence without touching game saves.
	if not fridge.toggle_door() or not fridge.can_access("shelves") or fridge.can_access("crisper"):
		_fail("F01_INTERACTION_FAIL: main door access contract", 8)
		return
	if not fridge.toggle_drawer() or not fridge.can_access("crisper"):
		_fail("F01_INTERACTION_FAIL: drawer access contract", 9)
		return
	if not fridge.toggle_freezer() or not fridge.can_access("freezer"):
		_fail("F01_INTERACTION_FAIL: freezer access contract", 10)
		return
	var saved := fridge.snapshot()
	var restored := FridgeInteraction.new()
	if not restored.restore(saved) or restored.snapshot() != saved:
		_fail("F01_INTERACTION_FAIL: candidate state round-trip", 11)
		return
	if restored.restore({"version": 1, "door_open": false, "drawer_open": true, "freezer_open": false}):
		_fail("F01_INTERACTION_FAIL: invalid persisted state accepted", 12)
		return
	if restored.restore({"version": 99, "door_open": true, "drawer_open": false, "freezer_open": false}):
		_fail("F01_INTERACTION_FAIL: future version accepted", 13)
		return
	if restored.toggle_door() or restored.drawer_open or restored.freezer_open or restored.can_access("freezer"):
		_fail("F01_INTERACTION_FAIL: closing door left contents accessible", 14)
		return
	print("F01_GODOT_GLTF_IMPORT_PASS meshes=", mesh_nodes.size(), " door_rad=", door_angle, " drawer_m=", drawer_travel)
	print("F01_GODOT_INTERACTION_PASS isolated_contract=true state_round_trip=true access_gate=true")
	quit(0)
