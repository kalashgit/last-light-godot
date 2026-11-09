extends RefCounted

# F01 candidate interaction-state contract only. W05/W07 own production gameplay.
# No inventory is granted here: an authorized game handler must resolve contents.

const STATE_VERSION := 1

var door_open := false
var drawer_open := false
var freezer_open := false


func toggle_door() -> bool:
	door_open = not door_open
	# The drawer and freezer flap cannot remain extended through a closed door.
	if not door_open:
		drawer_open = false
		freezer_open = false
	return door_open


func toggle_drawer() -> bool:
	if not door_open:
		return false
	drawer_open = not drawer_open
	return drawer_open


func toggle_freezer() -> bool:
	if not door_open:
		return false
	freezer_open = not freezer_open
	return freezer_open


func can_access(region: String) -> bool:
	match region:
		"shelves":
			return door_open
		"crisper":
			return door_open and drawer_open
		"freezer":
			return door_open and freezer_open
		_:
			return false


func snapshot() -> Dictionary:
	return {
		"version": STATE_VERSION,
		"door_open": door_open,
		"drawer_open": drawer_open,
		"freezer_open": freezer_open,
	}


func restore(data: Dictionary) -> bool:
	if data.get("version") != STATE_VERSION:
		return false
	for key in ["door_open", "drawer_open", "freezer_open"]:
		if not data.has(key) or not data[key] is bool:
			return false
	if not data["door_open"] and (data["drawer_open"] or data["freezer_open"]):
		return false
	door_open = data["door_open"]
	drawer_open = data["drawer_open"]
	freezer_open = data["freezer_open"]
	return true
