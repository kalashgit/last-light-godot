extends RefCounted
## One-call construction of the world simulation stack for scenes, adapters and tests.

const WorldDefs := preload("res://game/world_simulation/world_defs.gd")
const WorldState := preload("res://game/world_simulation/world_state.gd")
const WorldSave := preload("res://game/world_simulation/world_save.gd")
const InteractionSystem := preload("res://game/world_interactions/interaction_system.gd")

const LAB_LAYOUT := "res://data/world_objects/lab_layout_v1.json"

static var _shared_defs = null


## Definitions are immutable, so they are loaded once and shared.
static func shared_defs():
	if _shared_defs == null:
		var d = WorldDefs.new()
		if not d.load_default():
			push_error("World object definitions invalid: " + "; ".join(d.errors))
		_shared_defs = d
	return _shared_defs


## Returns {defs, world, interactions, saver} or {} on failure.
static func create(layout: Variant = LAB_LAYOUT, seed_value: int = 1) -> Dictionary:
	var defs = shared_defs()
	if not defs.errors.is_empty():
		return {}
	var data = layout
	if layout is String:
		data = JSON.parse_string(FileAccess.get_file_as_string(layout))
	if not data is Dictionary:
		push_error("World layout unreadable")
		return {}
	var world = WorldState.new(defs, seed_value)
	if not world.load_layout(data):
		return {}
	return {"defs": defs, "world": world, "interactions": InteractionSystem.new(world), "saver": WorldSave.new()}


static func dispose(stack: Dictionary) -> void:
	if stack.has("interactions") and stack["interactions"] != null:
		stack["interactions"].world = null
	if stack.has("world") and stack["world"] != null:
		stack["world"].dispose()
	stack.clear()


static func release_shared() -> void:
	_shared_defs = null
