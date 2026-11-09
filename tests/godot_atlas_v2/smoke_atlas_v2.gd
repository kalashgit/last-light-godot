extends SceneTree
## Headless smoke test for the generic LL_ATLAS_OUTPUTS_V2 loader.
## godot --headless --path . --script res://tests/godot_atlas_v2/smoke_atlas_v2.gd -- \
##     --dir=res://tests/godot_atlas_v2/generated --directions=8
## Never touches main.tscn, saves or gameplay. Calibration data only.

const Loader := preload("res://tests/godot_atlas_v2/atlas_v2_loader.gd")


func _initialize() -> void:
	call_deferred("_run")


func _fail(msg: String) -> void:
	push_error("W06_ATLAS_V2_GODOT_FAIL: " + msg)
	quit(1)


func _run() -> void:
	var dir := "res://tests/godot_atlas_v2/generated"
	var want_dirs := -1
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--dir="):
			dir = arg.trim_prefix("--dir=")
		elif arg.begins_with("--directions="):
			want_dirs = int(arg.trim_prefix("--directions="))
	var loaded: Dictionary = Loader.load_outputs(dir)
	if loaded.has("error"):
		_fail(loaded["error"])
		return
	var summary: Dictionary = loaded["summary"]
	if want_dirs > 0 and int(summary["directions"]) != want_dirs:
		_fail("direction count %d != %d" % [summary["directions"], want_dirs])
		return
	var frames: SpriteFrames = loaded["frames"]
	var root2d := Node2D.new()
	root.add_child(root2d)
	var placed := 0
	for anim in frames.get_animation_names():
		var s: AnimatedSprite2D = Loader.make_sprite(loaded, anim)
		# Place each heading on its own 80x40 tile centre along the iso X axis.
		s.position = Vector2(40 * placed, 20 * placed)
		root2d.add_child(s)
		var tex: Texture2D = frames.get_frame_texture(anim, 0)
		if tex == null or tex.get_width() <= 0:
			_fail("empty texture in " + anim)
			return
		if s.centered or s.offset == Vector2.ZERO:
			_fail("sprite not anchored to ground pivot in " + anim)
			return
		placed += 1
	if placed != int(summary["animations"]):
		_fail("animation count mismatch")
		return
	summary["status"] = "GODOT_ATLAS_V2_IMPORTED_CALIBRATION_ONLY"
	summary["approval"] = "NOT_GOLDEN_NOT_PRODUCTION"
	summary["godot"] = Engine.get_version_info()["string"]
	print("W06_ATLAS_V2_GODOT_PASS " + JSON.stringify(summary))
	quit(0)
