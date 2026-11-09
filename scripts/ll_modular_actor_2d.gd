extends Node2D
## LAST LIGHT — original 2.5D modular actor runtime (TECHNICAL CANDIDATE).
## All art layers share one rig, atlas cell, animation clock and ground-contact pivot.
## This is a reusable component, not a replacement for the current main scene.

const SLOT_ORDER: Array[String] = [
	"back", "base", "underwear", "legs", "feet",
	"torso_inner", "torso_outer", "head", "equipment", "blood"
]

var _clips: Dictionary = {}
var _directions: Array = []
var _layers: Dictionary = {}
var _sprites: Dictionary = {}
var _active_clip: String = ""
var _direction: String = ""
var _frame: int = 0
var _elapsed: float = 0.0
var _configured: bool = false


func configure(manifest: Dictionary, textures: Dictionary) -> bool:
	## Metadata-only input plus already-loaded Texture2D objects. No network or AI.
	## Validate everything before replacing any current visible character.
	if manifest.get("schema_version", 0) != 1:
		return false
	if manifest.get("rig", "") != "ll_biped_v1":
		return false
	if manifest.get("tile_px", []) != [80, 40]:
		return false
	var headings = manifest.get("directions", [])
	if not (headings is Array) or headings.size() < 4 or headings.size() > 16:
		return false
	var unique_headings: Dictionary = {}
	for h in headings:
		if not (h is String) or h.is_empty() or unique_headings.has(h):
			return false
		unique_headings[h] = true
	var clip_specs = manifest.get("clips", {})
	if not (clip_specs is Dictionary) or clip_specs.is_empty() or not clip_specs.has("idle"):
		return false
	for clip_name in clip_specs:
		if not (clip_name is String) or clip_name.is_empty():
			return false
		var clip = clip_specs[clip_name]
		if not (clip is Dictionary):
			return false
		if int(clip.get("frames", 0)) < 1 or int(clip.get("frames", 0)) > 256:
			return false
		if float(clip.get("fps", 0.0)) <= 0.0 or float(clip.get("fps", 0.0)) > 60.0:
			return false
		if not (clip.get("loop", null) is bool):
			return false

	var raw_layers = manifest.get("layers", [])
	if not (raw_layers is Array) or raw_layers.is_empty():
		return false
	var validated: Dictionary = {}
	var shared_cell: Array = []
	var shared_anchor: Array = []
	for entry in raw_layers:
		if not (entry is Dictionary):
			return false
		var slot: String = str(entry.get("slot", ""))
		if not SLOT_ORDER.has(slot) or validated.has(slot):
			return false
		var cell = entry.get("cell_px", [])
		var anchor = entry.get("anchor_px", [])
		if not (cell is Array) or cell.size() != 2 or not (anchor is Array) or anchor.size() != 2:
			return false
		if int(cell[0]) <= 0 or int(cell[1]) <= 0 or int(cell[0]) > 1024 or int(cell[1]) > 1024:
			return false
		if float(anchor[0]) < 0 or float(anchor[1]) < 0 or float(anchor[0]) > float(cell[0]) or float(anchor[1]) > float(cell[1]):
			return false
		if shared_cell.is_empty():
			shared_cell = cell
			shared_anchor = anchor
		elif cell != shared_cell or anchor != shared_anchor:
			# A cropped overlay MUST already be restored to the common rig canvas.
			return false
		var refs = entry.get("atlases", {})
		if not (refs is Dictionary):
			return false
		var resolved: Dictionary = {}
		for clip_name in clip_specs:
			var ref = refs.get(clip_name, "")
			if not (ref is String) or ref.is_empty() or not textures.has(ref):
				return false
			var texture = textures[ref]
			if not (texture is Texture2D):
				return false
			if texture.get_width() != int(cell[0]) * int(clip_specs[clip_name]["frames"]):
				return false
			if texture.get_height() != int(cell[1]) * headings.size():
				return false
			resolved[clip_name] = texture
		validated[slot] = {"cell": cell, "anchor": anchor, "textures": resolved}
	if not validated.has("base"):
		return false

	for child in get_children():
		if child is Sprite2D and child.is_in_group("ll_modular_generated_layer"):
			remove_child(child)
			child.queue_free()
	_sprites.clear()
	_layers = validated
	_clips = clip_specs.duplicate(true)
	_directions = headings.duplicate()
	for slot in SLOT_ORDER:
		if not validated.has(slot):
			continue
		var layer := Sprite2D.new()
		layer.name = "Layer_" + slot
		layer.add_to_group("ll_modular_generated_layer")
		layer.centered = false
		layer.offset = -Vector2(float(shared_anchor[0]), float(shared_anchor[1]))
		layer.region_enabled = true
		layer.z_index = 0  # Never override Y sorting of other ACTOR roots.
		add_child(layer)
		_sprites[slot] = layer
	_active_clip = "idle"
	_direction = str(headings[0])
	_frame = 0
	_elapsed = 0.0
	_configured = true
	y_sort_enabled = false
	_draw_frame()
	set_process(true)
	return true


func set_motion(clip_name: String, heading: String) -> bool:
	if not _configured or not _clips.has(clip_name) or not _directions.has(heading):
		return false
	if _active_clip != clip_name:
		_frame = 0
		_elapsed = 0.0
	_active_clip = clip_name
	_direction = heading
	_draw_frame()
	return true


func set_slot_visible(slot: String, shown: bool) -> bool:
	if not _sprites.has(slot):
		return false
	(_sprites[slot] as Sprite2D).visible = shown
	return true


func get_layer_sprite(slot: String) -> Sprite2D:
	return _sprites.get(slot, null) as Sprite2D


func current_frame() -> int:
	return _frame


func current_heading() -> String:
	return _direction


func advance_animation(delta: float) -> void:
	if not _configured or delta <= 0.0:
		return
	var clip: Dictionary = _clips[_active_clip]
	var fps: float = float(clip["fps"])
	var duration: float = 1.0 / fps
	_elapsed += minf(delta, 10.0)
	var steps: int = int(floor(_elapsed / duration))
	if steps == 0:
		return
	_elapsed = fmod(_elapsed, duration)
	var total: int = int(clip["frames"])
	if bool(clip["loop"]):
		_frame = (_frame + steps) % total
	else:
		_frame = mini(total - 1, _frame + steps)
	_draw_frame()


func _process(delta: float) -> void:
	advance_animation(delta)


func _draw_frame() -> void:
	if not _configured:
		return
	var row: int = _directions.find(_direction)
	if row < 0:
		return
	for slot in _sprites:
		var sprite: Sprite2D = _sprites[slot]
		var desc: Dictionary = _layers[slot]
		var cell: Array = desc["cell"]
		sprite.texture = desc["textures"][_active_clip]
		sprite.region_rect = Rect2(
			float(_frame * int(cell[0])),
			float(row * int(cell[1])),
			float(cell[0]), float(cell[1])
		)
