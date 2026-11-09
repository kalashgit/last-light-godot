extends RefCounted
## LAST LIGHT — fail-closed, OFFLINE verified paperdoll package loader.
## No dynamic code, web access, Golden promotion, or automatic gameplay replacement.
const CATALOG_SCHEMA := "last-light.paperdoll.catalog.v1"
const STATUS := "TECHNICAL_CANDIDATE_NOT_GOLDEN"
const ALLOWED_SLOTS := ["body", "pants", "shirt", "backpack", "effects"]


static func _safe_relative_path(rel: String) -> bool:
	if not rel.begins_with("atlases/") or not rel.ends_with(".png"):
		return false
	if rel.contains("..") or rel.contains("\\") or rel.contains("//") or rel.contains(":"):
		return false
	for part in rel.split("/"):
		if part.is_empty() or part == ".":
			return false
	return true


static func _integral_number(value: Variant) -> bool:
	# Godot JSON parses integral numerals as float; reject non-integral values.
	if typeof(value) != TYPE_INT and typeof(value) != TYPE_FLOAT:
		return false
	var n: float = float(value)
	return is_finite(n) and n == floorf(n) and n >= 0.0 and n <= 65536.0


static func _normalized_runtime(raw_spec: Dictionary) -> Dictionary:
	var spec: Dictionary = raw_spec.duplicate(true)
	if not _integral_number(spec.get("directions", null)):
		return {}
	spec["directions"] = int(spec["directions"])
	for field in ["frame_size", "pivot"]:
		if not spec.get(field) is Array or spec[field].size() != 2:
			return {}
		for i in range(2):
			if not _integral_number(spec[field][i]):
				return {}
			spec[field][i] = int(spec[field][i])
	if not spec.get("animations") is Dictionary:
		return {}
	for clip in spec["animations"]:
		var animation = spec["animations"][clip]
		if not animation is Dictionary or not _integral_number(animation.get("frames", null)):
			return {}
		animation["frames"] = int(animation["frames"])
		spec["animations"][clip] = animation
	return spec


static func install_package(actor: Node2D, folder: String, initial_items: Dictionary) -> bool:
	## The folder must be a pre-imported res:// path; no file system escape.
	if not actor.has_method("configure") or not actor.has_method("register_sheet") or not actor.has_method("equip"):
		return false
	if not folder.begins_with("res://") or folder.contains("..") or folder.contains("\\"):
		return false
	var catalog_path := folder.path_join("catalog.json")
	if not FileAccess.file_exists(catalog_path):
		return false
	var decoded = JSON.parse_string(FileAccess.get_file_as_string(catalog_path))
	if not (decoded is Dictionary):
		return false
	if decoded.get("schema", "") != CATALOG_SCHEMA or decoded.get("status", "") != STATUS:
		return false
	if not decoded.get("runtime") is Dictionary or not decoded.get("sheets") is Array:
		return false
	var runtime: Dictionary = _normalized_runtime(decoded["runtime"])
	if runtime.is_empty() or runtime.get("schema", "") != "last-light.paperdoll.v1":
		return false
	if not runtime.get("animations") is Dictionary or not runtime.get("slots") is Array:
		return false
	if not initial_items.has("body") or str(initial_items["body"]).is_empty():
		return false
	if decoded.get("generated_sheet_count", -1) != decoded["sheets"].size():
		return false
	if decoded["sheets"].size() < 1 or decoded["sheets"].size() > 512:
		return false

	var staged: Array[Dictionary] = []
	var inventory: Dictionary = {}
	for sheet in decoded["sheets"]:
		if not sheet is Dictionary:
			return false
		var slot: String = str(sheet.get("slot", ""))
		var item_id: String = str(sheet.get("item_id", ""))
		var clip: String = str(sheet.get("animation", ""))
		var rel: String = str(sheet.get("file", ""))
		var expected_hash: String = str(sheet.get("sha256", ""))
		if not ALLOWED_SLOTS.has(slot) or not runtime["slots"].has(slot):
			return false
		if item_id.is_empty() or clip.is_empty() or not runtime["animations"].has(clip):
			return false
		if not _safe_relative_path(rel) or expected_hash.length() != 64:
			return false
		var path := folder.path_join(rel)
		if not FileAccess.file_exists(path) or FileAccess.get_sha256(path) != expected_hash:
			return false
		var key := JSON.stringify([slot, item_id, clip])
		if inventory.has(key):
			return false
		var texture := load(path) as Texture2D
		if texture == null:
			return false
		var size: Array = runtime.get("frame_size", [])
		if size.size() != 2:
			return false
		var expected := Vector2i(int(size[0]) * int(runtime["animations"][clip]["frames"]),
		                         int(size[1]) * int(runtime["directions"]))
		if Vector2i(texture.get_size()) != expected:
			return false
		inventory[key] = true
		staged.append({"slot": slot, "item": item_id, "clip": clip, "texture": texture})

	# A selected item must contain ALL animations; never silently disappear during combat.
	for slot in initial_items:
		if not ALLOWED_SLOTS.has(slot) or not runtime["slots"].has(slot):
			return false
		var item_id: String = str(initial_items[slot])
		if item_id.is_empty():
			if slot == "body":
				return false
			continue
		for clip in runtime["animations"]:
			if not inventory.has(JSON.stringify([slot, item_id, clip])):
				return false
	if not actor.call("configure", runtime):
		return false
	for record in staged:
		if not actor.call("register_sheet", record["slot"], record["item"], record["clip"], record["texture"]):
			return false
	for slot in initial_items:
		if not actor.call("equip", slot, str(initial_items[slot])):
			return false
	return true
