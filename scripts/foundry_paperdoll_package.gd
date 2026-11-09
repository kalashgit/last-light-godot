extends RefCounted
## LAST LIGHT — fail-closed, OFFLINE verified paperdoll package loader.
## No dynamic code, web access, Golden promotion, or automatic gameplay replacement.
const CATALOG_SCHEMA := "last-light.paperdoll.catalog.v1"
const STATUS := "TECHNICAL_CANDIDATE_NOT_GOLDEN"
const ALLOWED_SLOTS := ["body", "pants", "shirt", "backpack", "effects"]


static func _safe_relative_path(rel: String) -> bool:
	if not rel.begins_with("atlases/") or not rel.ends_with(".png"):
		print("LL_PAPERDOLL_PACKAGE_REJECT step=1")
		return false
	if rel.contains("..") or rel.contains("\\") or rel.contains("//") or rel.contains(":"):
		print("LL_PAPERDOLL_PACKAGE_REJECT step=2")
		return false
	for part in rel.split("/"):
		if part.is_empty() or part == ".":
			print("LL_PAPERDOLL_PACKAGE_REJECT step=3")
			return false
	return true


static func install_package(actor: Node2D, folder: String, initial_items: Dictionary) -> bool:
	## The folder must be a pre-imported res:// path; no file system escape.
	if not actor.has_method("configure") or not actor.has_method("register_sheet") or not actor.has_method("equip"):
		print("LL_PAPERDOLL_PACKAGE_REJECT step=4")
		return false
	if not folder.begins_with("res://") or folder.contains("..") or folder.contains("\\"):
		print("LL_PAPERDOLL_PACKAGE_REJECT step=5")
		return false
	var catalog_path := folder.path_join("catalog.json")
	if not FileAccess.file_exists(catalog_path):
		print("LL_PAPERDOLL_PACKAGE_REJECT step=6")
		return false
	var decoded = JSON.parse_string(FileAccess.get_file_as_string(catalog_path))
	if not (decoded is Dictionary):
		print("LL_PAPERDOLL_PACKAGE_REJECT step=7")
		return false
	if decoded.get("schema", "") != CATALOG_SCHEMA or decoded.get("status", "") != STATUS:
		print("LL_PAPERDOLL_PACKAGE_REJECT step=8")
		return false
	if not decoded.get("runtime") is Dictionary or not decoded.get("sheets") is Array:
		print("LL_PAPERDOLL_PACKAGE_REJECT step=9")
		return false
	var runtime: Dictionary = decoded["runtime"]
	if runtime.get("schema", "") != "last-light.paperdoll.v1":
		print("LL_PAPERDOLL_PACKAGE_REJECT step=10")
		return false
	if not runtime.get("animations") is Dictionary or not runtime.get("slots") is Array:
		print("LL_PAPERDOLL_PACKAGE_REJECT step=11")
		return false
	if not initial_items.has("body") or str(initial_items["body"]).is_empty():
		print("LL_PAPERDOLL_PACKAGE_REJECT step=12")
		return false
	if decoded.get("generated_sheet_count", -1) != decoded["sheets"].size():
		print("LL_PAPERDOLL_PACKAGE_REJECT step=13")
		return false
	if decoded["sheets"].size() < 1 or decoded["sheets"].size() > 512:
		print("LL_PAPERDOLL_PACKAGE_REJECT step=14")
		return false

	var staged: Array[Dictionary] = []
	var inventory: Dictionary = {}
	for sheet in decoded["sheets"]:
		if not sheet is Dictionary:
			print("LL_PAPERDOLL_PACKAGE_REJECT step=15")
			return false
		var slot: String = str(sheet.get("slot", ""))
		var item_id: String = str(sheet.get("item_id", ""))
		var clip: String = str(sheet.get("animation", ""))
		var rel: String = str(sheet.get("file", ""))
		var expected_hash: String = str(sheet.get("sha256", ""))
		if not ALLOWED_SLOTS.has(slot) or not runtime["slots"].has(slot):
			print("LL_PAPERDOLL_PACKAGE_REJECT step=16")
			return false
		if item_id.is_empty() or clip.is_empty() or not runtime["animations"].has(clip):
			print("LL_PAPERDOLL_PACKAGE_REJECT step=17")
			return false
		if not _safe_relative_path(rel) or expected_hash.length() != 64:
			print("LL_PAPERDOLL_PACKAGE_REJECT step=18")
			return false
		var path := folder.path_join(rel)
		if not FileAccess.file_exists(path) or FileAccess.get_sha256(path) != expected_hash:
			print("LL_PAPERDOLL_PACKAGE_REJECT step=19")
			return false
		var key := JSON.stringify([slot, item_id, clip])
		if inventory.has(key):
			print("LL_PAPERDOLL_PACKAGE_REJECT step=20")
			return false
		var texture := load(path) as Texture2D
		if texture == null:
			print("LL_PAPERDOLL_PACKAGE_REJECT step=21")
			return false
		var size: Array = runtime.get("frame_size", [])
		if size.size() != 2:
			print("LL_PAPERDOLL_PACKAGE_REJECT step=22")
			return false
		var expected := Vector2i(int(size[0]) * int(runtime["animations"][clip]["frames"]),
		                         int(size[1]) * int(runtime["directions"]))
		if Vector2i(texture.get_size()) != expected:
			print("LL_PAPERDOLL_PACKAGE_REJECT step=23")
			return false
		inventory[key] = true
		staged.append({"slot": slot, "item": item_id, "clip": clip, "texture": texture})

	# A selected item must contain ALL animations; never silently disappear during combat.
	for slot in initial_items:
		if not ALLOWED_SLOTS.has(slot) or not runtime["slots"].has(slot):
			print("LL_PAPERDOLL_PACKAGE_REJECT step=24")
			return false
		var item_id: String = str(initial_items[slot])
		if item_id.is_empty():
			if slot == "body":
				print("LL_PAPERDOLL_PACKAGE_REJECT step=25")
				return false
			continue
		for clip in runtime["animations"]:
			if not inventory.has(JSON.stringify([slot, item_id, clip])):
				print("LL_PAPERDOLL_PACKAGE_REJECT step=26")
				return false
	if not actor.call("configure", runtime):
		print("LL_PAPERDOLL_PACKAGE_REJECT step=27")
		return false
	for record in staged:
		if not actor.call("register_sheet", record["slot"], record["item"], record["clip"], record["texture"]):
			print("LL_PAPERDOLL_PACKAGE_REJECT step=28")
			return false
	for slot in initial_items:
		if not actor.call("equip", slot, str(initial_items[slot])):
			print("LL_PAPERDOLL_PACKAGE_REJECT step=29")
			return false
	return true
