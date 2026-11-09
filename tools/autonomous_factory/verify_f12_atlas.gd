extends SceneTree

# Isolated technical import fixture for the pinned F12 RGBA atlas.
# No game scene, canonical assets or production configuration are modified.
func _initialize() -> void:
	var atlas: Texture2D = load("res://m02_f12_cal01_atlas.png") as Texture2D
	if atlas == null:
		push_error("M02 F12 atlas could not be loaded by Godot")
		quit(1)
		return
	if atlas.get_width() != 1024 or atlas.get_height() != 1024:
		push_error("M02 F12 atlas imported at unexpected dimensions")
		quit(1)
		return
	print("M02_F12_GODOT_ATLAS_IMPORT_PASS")
	quit(0)
