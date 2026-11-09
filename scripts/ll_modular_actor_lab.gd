extends Node2D
## Preview-only scene showing LAST LIGHT paperdoll layering and real Y-sort grouping.
## All colored rectangles are procedural TEST ART, never Golden production assets.

const ACTOR_SCRIPT = preload("res://scripts/ll_modular_actor_2d.gd")
const CELL := Vector2i(64, 80)
const HEADINGS = ["front", "right", "back", "left"]
@onready var depth_root: Node2D = $DepthSorted
var actors: Array = []
var walking := true


func _ready() -> void:
	var sheets: Dictionary = {}
	for layer in ["base", "legs", "torso_outer", "back", "blood"]:
		for clip in ["idle", "walk"]:
			var frame_count: int = 4 if clip == "walk" else 1
			sheets[layer + "_" + clip] = _make_atlas(layer, frame_count)
	var manifest := _make_manifest()
	for position_y in [260.0, 365.0]:
		var actor := ACTOR_SCRIPT.new()
		actor.position = Vector2(270.0, position_y)
		depth_root.add_child(actor)
		if actor.configure(manifest, sheets):
			actor.set_motion("walk", "front")
			actors.append(actor)
	var blocker := Sprite2D.new()
	blocker.name = "WallOccluder_AtGroundPoint"
	blocker.position = Vector2(310, 318)
	var blocker_img := Image.create(90, 130, false, Image.FORMAT_RGBA8)
	blocker_img.fill(Color(0.22, 0.29, 0.28, 1))
	blocker.texture = ImageTexture.create_from_image(blocker_img)
	blocker.centered = false
	blocker.offset = Vector2(-45, -128)
	depth_root.add_child(blocker)
	queue_redraw()


func _make_manifest() -> Dictionary:
	var items: Array = []
	for slot in ["base", "legs", "torso_outer", "back", "blood"]:
		items.append({
			"slot": slot,
			"cell_px": [CELL.x, CELL.y],
			"anchor_px": [32, 76],
			"atlases": {"idle": slot + "_idle", "walk": slot + "_walk"}
		})
	return {
		"schema_version": 1,
		"rig": "ll_biped_v1",
		"tile_px": [80, 40],
		"approval_status": "TECHNICAL_CANDIDATE_NOT_GOLDEN",
		"directions": HEADINGS.duplicate(),
		"clips": {
			"idle": {"frames": 1, "fps": 8.0, "loop": true},
			"walk": {"frames": 4, "fps": 8.0, "loop": true}
		},
		"layers": items
	}


func _make_atlas(slot: String, count: int) -> Texture2D:
	var img := Image.create(CELL.x * count, CELL.y * HEADINGS.size(), false, Image.FORMAT_RGBA8)
	img.fill(Color.TRANSPARENT)
	var color := Color(0.56, 0.67, 0.6, 1)
	match slot:
		"base": color = Color(0.62, 0.52, 0.42, 1)
		"legs": color = Color(0.24, 0.36, 0.41, 1)
		"torso_outer": color = Color(0.29, 0.52, 0.37, 1)
		"back": color = Color(0.34, 0.26, 0.19, 1)
		"blood": color = Color(0.54, 0.15, 0.11, 0.8)
	for row in range(HEADINGS.size()):
		for frame in range(count):
			var left := frame * CELL.x
			match slot:
				"base":
					img.fill_rect(Rect2i(left + 26, row * CELL.y + 9, 12, 54), color)
				"legs":
					img.fill_rect(Rect2i(left + 26, row * CELL.y + 51, 12, 21), color)
				"torso_outer":
					img.fill_rect(Rect2i(left + 22, row * CELL.y + 28, 20, 23), color)
				"back":
					img.fill_rect(Rect2i(left + 38, row * CELL.y + 27, 13, 25), color)
				"blood":
					img.fill_rect(Rect2i(left + 30, row * CELL.y + 33, 4, 6), color)
	return ImageTexture.create_from_image(img)


func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo:
		if event.keycode == KEY_SPACE:
			walking = not walking
			for actor in actors:
				actor.set_motion("walk" if walking else "idle", "front")
		elif event.keycode == KEY_D:
			for actor in actors:
				actor.set_motion("walk" if walking else "idle", "right")


func _draw() -> void:
	for x in range(0, 8):
		for y in range(0, 8):
			var origin := Vector2(200 + (x - y) * 40, 245 + (x + y) * 20)
			draw_colored_polygon(PackedVector2Array([
				origin, origin + Vector2(40, 20),
				origin + Vector2(0, 40), origin + Vector2(-40, 20)
			]), Color(0.28, 0.32, 0.29, 1))
