extends RefCounted
## Versioned world-delta persistence.
##
## The immutable layout is never saved. A save holds only:
##   - instances whose state differs from the layout baseline (`objects`, full mutable record),
##   - runtime-spawned instances (spill piles, ...),
##   - ids of baseline instances that no longer exist (`removed`),
##   - the world clock and globals.
## Records are cached per object and only re-serialized when dirty (incremental writes).
## Files are written to <path>.tmp and renamed over the old file, keeping <path>.bak.

const SCHEMA := "last-light.world-delta"
const VERSION := 1

var _cache: Dictionary = {}
var last_reserialized: int = 0


func build(world) -> Dictionary:
	world.settle_for_save()
	last_reserialized = 0
	for id in world.dirty:
		var obj = world.objects.get(id)
		if obj != null and world.modified.has(id):
			_cache[id] = obj.to_record()
			last_reserialized += 1
		else:
			_cache.erase(id)
	world.dirty.clear()
	var removed: Array = world.removed_ids.keys()
	removed.sort()
	return {
		"schema": SCHEMA,
		"version": VERSION,
		"layout_id": world.layout_id,
		"world_seed": world.world_seed,
		"time_s": world.time_s,
		"saved_unix": Time.get_unix_time_from_system(),
		"globals": world.globals.duplicate(true),
		"objects": _cache.duplicate(true),
		"removed": removed,
	}


func save(world, path: String) -> Error:
	var data := build(world)
	var text := JSON.stringify(data)
	var tmp := path + ".tmp"
	var f := FileAccess.open(tmp, FileAccess.WRITE)
	if f == null:
		return FileAccess.get_open_error()
	f.store_string(text)
	f.close()
	var abs_path := ProjectSettings.globalize_path(path)
	if FileAccess.file_exists(path):
		DirAccess.remove_absolute(abs_path + ".bak")
		DirAccess.rename_absolute(abs_path, abs_path + ".bak")
	return DirAccess.rename_absolute(ProjectSettings.globalize_path(tmp), abs_path)


static func read(path: String) -> Variant:
	if not FileAccess.file_exists(path):
		return null
	return JSON.parse_string(FileAccess.get_file_as_string(path))


## Upgrade older payloads in place. Version 1 is current; future versions add steps here.
static func migrate(data: Dictionary) -> Dictionary:
	return data


## Validate everything first, then apply to a world freshly built from the same layout.
## Returns "" on success or a failure reason (world untouched on failure).
func apply(world, data) -> String:
	if not data is Dictionary or data.get("schema") != SCHEMA:
		return "not_a_world_delta"
	data = migrate(data)
	if int(data.get("version", 0)) != VERSION:
		return "unsupported_version"
	if data.get("layout_id") != world.layout_id:
		return "layout_mismatch"
	if not data.get("objects") is Dictionary or not data.get("removed") is Array:
		return "malformed"
	for id in data["objects"]:
		var rec = data["objects"][id]
		if not rec is Dictionary or world.defs.get_def(str(rec.get("def", ""))).is_empty():
			return "unknown_definition:" + str(id)
		if not rec.get("state") is Dictionary or not rec.get("pos") is Array:
			return "malformed_record:" + str(id)
		if not rec.get("spawned", false) and not world.objects.has(id):
			return "unknown_instance:" + str(id)
		if not rec.get("spawned", false) and world.objects[id].definition_id != rec["def"]:
			return "definition_changed:" + str(id)
	world.time_s = float(data.get("time_s", 0.0))
	world.world_seed = int(data.get("world_seed", world.world_seed))
	for k in data.get("globals", {}):
		world.globals[k] = data["globals"][k]
	for id in data["removed"]:
		var obj = world.objects.get(id)
		if obj != null:
			world._unindex(obj)
			world.objects.erase(id)
			world.order.erase(id)
			world.dynamic_ids.erase(id)
		world.removed_ids[id] = true
	for id in data["objects"]:
		var rec: Dictionary = data["objects"][id]
		var p: Array = rec["pos"]
		var s: Array = rec.get("size", [0, 0])
		var obj = world.objects.get(id)
		if obj == null:
			obj = world.add_object(id, rec["def"], Vector2(p[0], p[1]), Vector2(s[0], s[1]), int(rec.get("rot", 0)), str(rec.get("room", "")), {}, true)
		else:
			world._unindex(obj)
			obj.pos = Vector2(p[0], p[1])
			obj.size = Vector2(s[0], s[1])
			obj.rotation = int(rec.get("rot", 0))
			obj.room = str(rec.get("room", obj.room))
			world._index(obj)
		for k in rec["state"]:
			obj.state[k] = _normalize(rec["state"][k])
		world.modified[id] = true
		_cache[id] = rec.duplicate(true)
	world.dirty.clear()
	world.power.mark_topology_dirty()
	world.power.recompute_all()
	world.nav_revision += 1
	world.emit({"type": "world_loaded", "objects": data["objects"].size(), "removed": data["removed"].size()})
	return ""


## JSON numbers come back as floats; item counts inside contents must be ints again.
func _normalize(v):
	if v is Dictionary:
		var out := {}
		for k in v:
			out[k] = _normalize(v[k])
		return out
	if v is Array:
		var arr := []
		for x in v:
			arr.append(_normalize(x))
		return arr
	return v
