extends SceneTree
## Headless Godot 4 runtime contract for LAST LIGHT's noncanonical modular pilot.
const ACTOR_SCRIPT = preload("res://scripts/ll_modular_actor_2d.gd")
const CELL := Vector2i(32, 32)
const HEADINGS := ["front", "right", "back", "left"]
var failures: Array[String] = []


func _initialize() -> void:
	call_deferred("_run_tests")


func _check(value: bool, detail: String) -> void:
	if not value:
		failures.append(detail)


func _texture(frames: int, shade: Color) -> Texture2D:
	var img := Image.create(CELL.x * frames, CELL.y * HEADINGS.size(), false, Image.FORMAT_RGBA8)
	img.fill(Color.TRANSPARENT)
	for row in range(HEADINGS.size()):
		for frame in range(frames):
			img.fill_rect(Rect2i(frame * CELL.x + 4, row * CELL.y + 3, 24, 24), shade)
	return ImageTexture.create_from_image(img)


func _manifest() -> Dictionary:
	return {
		"schema_version": 1,
		"rig": "ll_biped_v1",
		"tile_px": [80, 40],
		"approval_status": "TECHNICAL_CANDIDATE_NOT_GOLDEN",
		"directions": HEADINGS.duplicate(),
		"clips": {
			"idle": {"frames": 1, "fps": 8.0, "loop": true},
			"walk": {"frames": 3, "fps": 8.0, "loop": true}
		},
		"layers": [
			{
				"slot": "torso_outer",
				"cell_px": [32, 32],
				"anchor_px": [16, 28],
				"atlases": {"idle": "coat_idle", "walk": "coat_walk"}
			},
			{
				"slot": "base",
				"cell_px": [32, 32],
				"anchor_px": [16, 28],
				"atlases": {"idle": "base_idle", "walk": "base_walk"}
			}
		]
	}


func _run_tests() -> void:
	var world := Node2D.new()
	world.name = "LastLight2D_TestWorld"
	get_root().add_child(world)
	var depth_root := Node2D.new()
	depth_root.name = "DepthSorted"
	depth_root.y_sort_enabled = true
	world.add_child(depth_root)

	var sheet: Dictionary = {
		"base_idle": _texture(1, Color(0.3, 0.7, 0.65, 1)),
		"base_walk": _texture(3, Color(0.3, 0.7, 0.65, 1)),
		"coat_idle": _texture(1, Color(0.65, 0.3, 0.2, 1)),
		"coat_walk": _texture(3, Color(0.65, 0.3, 0.2, 1))
	}
	var actor := ACTOR_SCRIPT.new()
	actor.position = Vector2(100, 150)
	depth_root.add_child(actor)
	_check(actor.configure(_manifest(), sheet), "valid 2-layer rig was rejected")
	actor.set_process(false)
	_check(actor.get_layer_sprite("base") != null, "missing body layer")
	_check(actor.get_layer_sprite("torso_outer") != null, "missing outfit layer")
	_check(actor.get_child(0).name == "Layer_base", "slot order is unstable")
	_check(actor.get_child(1).name == "Layer_torso_outer", "outfit should render above body")
	_check(actor.get_layer_sprite("base").offset == Vector2(-16, -28), "ground pivot incorrect")
	_check(not actor.y_sort_enabled and depth_root.y_sort_enabled, "depth sorting hierarchy invalid")
	_check(actor.get_layer_sprite("base").z_index == 0, "layer Z offset overrides Y sort")

	var second := ACTOR_SCRIPT.new()
	second.position = Vector2(100, 180)
	depth_root.add_child(second)
	_check(second.configure(_manifest(), sheet), "second actor configuration failed")
	second.set_process(false)
	_check(second.position.y > actor.position.y, "second actor ground-contact depth not distinct")
	_check(actor.set_motion("walk", "back"), "walk/back rejected")
	actor.advance_animation(0.26)
	_check(actor.current_frame() == 2, "shared clock did not advance two frames")
	_check(actor.get_layer_sprite("base").region_rect == Rect2(64, 64, 32, 32), "base sprite wrong atlas cell")
	_check(actor.get_layer_sprite("torso_outer").region_rect == Rect2(64, 64, 32, 32), "coat drifted out of phase")
	actor.advance_animation(0.13)
	_check(actor.current_frame() == 0, "walk animation did not loop")
	_check(actor.set_motion("walk", "left"), "left heading rejected")
	_check(actor.get_layer_sprite("base").region_rect.position.y == 96, "heading did not select row")
	_check(actor.set_slot_visible("torso_outer", false), "equipment toggle failed")
	_check(not actor.get_layer_sprite("torso_outer").visible, "clothing not hidden")
	_check(not actor.set_motion("attack", "front"), "unknown clip accepted")
	_check(not actor.set_motion("idle", "northwest"), "unknown heading accepted")

	var bad := _manifest()
	bad["layers"][0]["anchor_px"] = [15, 28]
	_check(not actor.configure(bad, sheet), "misaligned cloth pivot accepted")
	_check(actor.current_heading() == "left", "bad reconfiguration damaged live actor")
	bad = _manifest()
	bad["directions"] = ["front", "front", "back", "left"]
	_check(not actor.configure(bad, sheet), "duplicate heading accepted")
	bad = _manifest()
	bad["layers"][0]["atlases"]["walk"] = "missing_asset"
	_check(not actor.configure(bad, sheet), "missing atlas accepted")

	var main_scene := load("res://main.tscn")
	_check(main_scene is PackedScene, "existing playable main scene is not intact")
	world.queue_free()
	if failures.is_empty():
		print("LL_MODULAR_ACTOR_GODOT_PASS: 2 layered actors, synchronized heading/state, ground-pivot Y sort, invalid-input rejection")
		quit(0)
	else:
		for failure in failures:
			print("LL_MODULAR_ACTOR_GODOT_FAIL: ", failure)
		quit(2)
