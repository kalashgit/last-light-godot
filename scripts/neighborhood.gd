extends RefCounted
## LAST LIGHT deterministic lab neighborhood generator (LAB V1 subset).
## Pure data: same seed + VERSION + catalog => identical plan. No rendering, no scene changes.
## Coordinates are gameplay metres on the shared 2:1 grid (80x40 px per metre tile).
## The original furnished house (LAB-H01, 0..9 x 0..8) is NOT generated here; it stays hand-authored.
const VERSION := "ll.lab-neighborhood.v1"
const ROAD := Rect2(-18.0, 13.6, 49.0, 4.2)
const BOUNDS := Rect2(-17.0, -6.0, 47.0, 35.0)
const H01 := Rect2(0.0, 0.0, 9.0, 8.0)
const WALL_INSET := 0.14
const DOOR_CLEARANCE := 1.0

# Supported survival item IDs only (survival_state.gd). Ranges are inclusive [min, max].
const LOOT_PROFILES := {
	"kitchen": {"ll_food_bean_tin": [1, 3], "ll_food_water_bottle": [1, 2]},
	"pantry": {"ll_food_bean_tin": [1, 2], "ll_food_water_bottle": [0, 1]},
	"medical": {"ll_medical_sterile_bandage": [1, 3], "ll_medical_first_aid_case": [0, 1]},
	"bedroom": {"ll_household_flashlight": [0, 1], "ll_medical_sterile_bandage": [1, 1]},
	"living": {"ll_crafting_pine_plank": [1, 2], "ll_food_bean_tin": [0, 1]},
	"tools": {"ll_tools_hatchet": [0, 1], "ll_tools_claw_hammer": [0, 1], "ll_crafting_pine_plank": [1, 2]},
	"grocery": {"ll_food_bean_tin": [1, 2], "ll_food_water_bottle": [1, 2]},
	"cashier": {"ll_medical_first_aid_case": [1, 1], "ll_household_flashlight": [0, 1]},
}

# Room recipes: [asset_id, placement, loot_profile or ""]. Placement: wall | center.
const ROOM_RECIPES := {
	"kitchen": [["ll_furniture_kitchen_counter", "wall", "kitchen"], ["ll_furniture_refrigerator", "wall", ""], ["ll_furniture_cooking_stove", "wall", ""], ["ll_furniture_kitchen_cupboard", "wall", "pantry"], ["ll_furniture_kitchen_table", "center", ""]],
	"bathroom": [["ll_furniture_medicine_cabinet", "wall", "medical"], ["ll_furniture_toilet", "wall", ""], ["ll_furniture_bathroom_vanity", "wall", ""], ["ll_furniture_bathtub", "wall", ""]],
	"bedroom": [["ll_furniture_double_bed", "wall", "bedroom"], ["ll_furniture_wardrobe", "wall", ""], ["ll_furniture_nightstand", "wall", ""], ["ll_furniture_storage_chest", "wall", "tools"]],
	"living": [["ll_furniture_two_seat_sofa", "wall", "living"], ["ll_furniture_bookcase", "wall", ""], ["ll_furniture_tv_stand", "wall", ""], ["ll_furniture_armchair", "wall", ""], ["ll_furniture_coffee_table", "center", ""]],
	"kitchen_living": [["ll_furniture_kitchen_counter", "wall", "kitchen"], ["ll_furniture_refrigerator", "wall", ""], ["ll_furniture_cooking_stove", "wall", ""], ["ll_furniture_two_seat_sofa", "wall", "living"], ["ll_furniture_bookcase", "wall", ""], ["ll_furniture_kitchen_table", "center", ""]],
	"stockroom": [["ll_furniture_storage_shelf", "wall", "pantry"], ["ll_furniture_locker", "wall", "tools"], ["ll_furniture_workbench", "wall", ""], ["ll_furniture_storage_shelf", "wall", ""]],
}
const ROOM_TINTS := {"kitchen": "777164", "bathroom": "b3b7a5", "bedroom": "566a75", "living": "796557", "kitchen_living": "777164", "shop": "8a8a7a", "stockroom": "6f6a5c"}

var catalog: Dictionary = {}
var rng := RandomNumberGenerator.new()


## catalog: factory manifest objects keyed by id (needs dimensions_m). Returns a plan Dictionary.
func generate(world_seed: int, factory_catalog: Dictionary) -> Dictionary:
	catalog = factory_catalog
	var plan := {"version": VERSION, "seed": world_seed, "bounds": BOUNDS, "road": ROAD, "buildings": [], "infected": [], "paths": []}
	# Lots: west house, east house (north of road, facing south) and a shop south of the road facing north.
	var lots := [
		{"id": "lab.h03", "archetype": "house", "x_min": -15.5, "x_max": -3.5, "front_y": 8.0},
		{"id": "lab.h02", "archetype": "house", "x_min": 12.5, "x_max": 27.5, "front_y": 8.0},
		{"id": "lab.s01", "archetype": "shop", "x_min": 1.0, "x_max": 15.0, "front_y": 20.0},
	]
	for lot in lots:
		_seed_for(world_seed, lot.id)
		var building: Dictionary = _house(lot) if lot.archetype == "house" else _shop(lot)
		plan.buildings.append(building)
		plan.paths.append(building.path)
	_seed_for(world_seed, "lab.infected")
	var h02: Rect2 = plan.buildings[1].rect
	var h03: Rect2 = plan.buildings[0].rect
	var stock: Rect2 = plan.buildings[2].rooms[1].rect
	plan.infected = [
		Vector2(h02.end.x + 1.2, h02.position.y + rng.randf_range(1.0, 3.0)),
		Vector2(h03.position.x + rng.randf_range(1.0, 3.0), h03.position.y - 1.6),
		stock.get_center(),
		Vector2(rng.randf_range(19.0, 24.0), 15.7),
	]
	return plan


func _seed_for(world_seed: int, key: String) -> void:
	rng.seed = ("%s|%d|%s" % [VERSION, world_seed, key]).hash()


func _snap(v: float, step: float = 0.5) -> float:
	return roundf(v / step) * step


func _pick(options: Array) -> Variant:
	return options[rng.randi_range(0, options.size() - 1)]


func _house(lot: Dictionary) -> Dictionary:
	var w: float = _pick([8.0, 8.5, 9.0, 9.5, 10.0])
	var d: float = _pick([7.0, 7.5, 8.0])
	var x0: float = _snap(rng.randf_range(lot.x_min, lot.x_max - w))
	var y1: float = lot.front_y
	var y0: float = y1 - d
	var rect := Rect2(x0, y0, w, d)
	var sx: float = x0 + _snap(w * rng.randf_range(0.42, 0.58))
	var sy: float = y0 + _snap(d * rng.randf_range(0.45, 0.55))
	var living_left: bool = rng.randf() < 0.5
	var open_plan: bool = rng.randf() < 0.35
	var other_front: String = _pick(["bathroom", "bedroom"])
	var other_back: String = "bedroom" if other_front == "bathroom" else "bathroom"
	var left_x := Vector2(x0, sx)
	var right_x := Vector2(sx, x0 + w)
	var live_span: Vector2 = left_x if living_left else right_x
	var other_span: Vector2 = right_x if living_left else left_x
	var rooms: Array = []
	if open_plan:
		rooms.append({"id": lot.id + ".kitchen_living", "type": "kitchen_living", "rect": Rect2(live_span.x, y0, live_span.y - live_span.x, d)})
	else:
		rooms.append({"id": lot.id + ".living", "type": "living", "rect": Rect2(live_span.x, sy, live_span.y - live_span.x, y1 - sy)})
		rooms.append({"id": lot.id + ".kitchen", "type": "kitchen", "rect": Rect2(live_span.x, y0, live_span.y - live_span.x, sy - y0)})
	rooms.append({"id": lot.id + "." + other_front, "type": other_front, "rect": Rect2(other_span.x, sy, other_span.y - other_span.x, y1 - sy)})
	rooms.append({"id": lot.id + "." + other_back, "type": other_back, "rect": Rect2(other_span.x, y0, other_span.y - other_span.x, sy - y0)})
	var b := {"id": lot.id, "archetype": "house", "rect": rect, "front": "south", "open_plan": open_plan, "rooms": rooms, "walls": [], "doors": [], "furniture": []}
	# Front door inside the living span; interior doors form a spanning tree over all rooms.
	var front_x: float = clampf(_snap((live_span.x + live_span.y) * 0.5 + rng.randf_range(-0.5, 0.5), 0.25), live_span.x + 1.2, live_span.y - 1.2)
	_wall_line(b, Vector2(x0, y1), Vector2(x0 + w, y1), true, [{"t": front_x, "w": 1.6, "label": "FRONT"}])
	_wall_line(b, Vector2(x0, y0), Vector2(x0 + w, y0), true, [])
	_wall_line(b, Vector2(x0, y0), Vector2(x0, y1), true, [])
	_wall_line(b, Vector2(x0 + w, y0), Vector2(x0 + w, y1), true, [])
	_wall_line(b, Vector2(sx, y0), Vector2(sx, y1), false, [{"t": _snap((sy + y1) * 0.5, 0.25), "w": 1.2, "label": other_front.to_upper()}])
	if not open_plan:
		_wall_line(b, Vector2(live_span.x, sy), Vector2(live_span.y, sy), false, [{"t": _snap((live_span.x + live_span.y) * 0.5, 0.25), "w": 1.2, "label": "KITCHEN"}])
	_wall_line(b, Vector2(other_span.x, sy), Vector2(other_span.y, sy), false, [{"t": _snap((other_span.x + other_span.y) * 0.5, 0.25), "w": 1.2, "label": other_back.to_upper()}])
	for room in rooms:
		_furnish(b, room)
	b.path = {"from": Vector2(front_x, y1), "to": Vector2(front_x, ROAD.position.y)}
	return b


func _shop(lot: Dictionary) -> Dictionary:
	var w: float = _pick([11.0, 12.0, 13.0])
	var d: float = _pick([7.0, 7.5])
	var x0: float = _snap(rng.randf_range(lot.x_min, lot.x_max - w))
	var y0: float = lot.front_y
	var y1: float = y0 + d
	var split: float = y0 + _snap(d * 0.62)
	var rect := Rect2(x0, y0, w, d)
	var hall := Rect2(x0, y0, w, split - y0)
	var stock := Rect2(x0, split, w, y1 - split)
	var b := {"id": lot.id, "archetype": "shop", "rect": rect, "front": "north", "open_plan": false,
		"rooms": [{"id": lot.id + ".hall", "type": "shop", "rect": hall}, {"id": lot.id + ".stockroom", "type": "stockroom", "rect": stock}],
		"walls": [], "doors": [], "furniture": []}
	var door_x: float = _snap(x0 + w * rng.randf_range(0.35, 0.65), 0.25)
	var stock_door_x: float = _snap(x0 + w - rng.randf_range(1.6, 2.6), 0.25)
	_wall_line(b, Vector2(x0, y0), Vector2(x0 + w, y0), true, [{"t": door_x, "w": 2.0, "label": "SHOP"}])
	_wall_line(b, Vector2(x0, y1), Vector2(x0 + w, y1), true, [])
	_wall_line(b, Vector2(x0, y0), Vector2(x0, y1), true, [])
	_wall_line(b, Vector2(x0 + w, y0), Vector2(x0 + w, y1), true, [])
	_wall_line(b, Vector2(x0, split), Vector2(x0 + w, split), false, [{"t": stock_door_x, "w": 1.2, "label": "STOCKROOM"}])
	# Grocery aisle: one row of shelves with walk-around gaps; cashier counter by the entrance.
	var shelf_y: float = y0 + _snap((split - y0) * 0.55, 0.25)
	var n := 0
	var x: float = x0 + 1.2
	while x + 0.85 < x0 + w - 1.2:
		if absf(x + 0.425 - door_x) > 1.4 and absf(x + 0.425 - stock_door_x) > 1.4 and rng.randf() < 0.85:
			_place(b, b.rooms[0], "ll_furniture_storage_shelf", Vector2(x, shelf_y), "grocery" if n % 2 == 0 else "")
			n += 1
		x += 1.5
	var counter_x: float = door_x + 1.9 if door_x + 3.1 < x0 + w else door_x - 2.95
	_place(b, b.rooms[0], "ll_furniture_kitchen_counter", Vector2(counter_x, y0 + 1.15), "cashier")
	_place_against_walls(b, b.rooms[0], "ll_furniture_freezer", "")
	_furnish(b, b.rooms[1])
	b.path = {"from": Vector2(door_x, y0), "to": Vector2(door_x, ROAD.end.y)}
	return b


## Split one wall line into wall segments and door gaps. `t` is the door centre along the
## varying axis (x for horizontal walls, y for vertical walls).
func _wall_line(b: Dictionary, a: Vector2, c: Vector2, exterior: bool, gaps: Array) -> void:
	var horizontal: bool = absf(a.y - c.y) < 0.01
	var cursor := a
	gaps.sort_custom(func(p, q): return p.t < q.t)
	for gap in gaps:
		var u := Vector2(gap.t - gap.w * 0.5, a.y) if horizontal else Vector2(a.x, gap.t - gap.w * 0.5)
		var v := Vector2(gap.t + gap.w * 0.5, a.y) if horizontal else Vector2(a.x, gap.t + gap.w * 0.5)
		_segment(b, cursor, u, exterior)
		b.doors.append({"a": u, "b": v, "label": gap.label})
		cursor = v
	_segment(b, cursor, c, exterior)


func _segment(b: Dictionary, a: Vector2, c: Vector2, exterior: bool) -> void:
	if a.distance_to(c) < 0.05:
		return
	var windows: Array = []
	if exterior and a.distance_to(c) >= 2.4:
		var mid := (a + c) * 0.5
		var dir := (c - a).normalized()
		var half: float = minf(0.9, a.distance_to(c) * 0.5 - 0.6)
		windows.append([mid - dir * half, mid + dir * half])
	b.walls.append({"a": a, "b": c, "exterior": exterior, "windows": windows})


func _dims(asset_id: String) -> Vector2:
	assert(catalog.has(asset_id), "Neighborhood references unknown factory asset " + asset_id)
	var d: Array = catalog[asset_id].dimensions_m
	return Vector2(snappedf(float(d[0]), 0.01), snappedf(float(d[1]), 0.01))


func _furnish(b: Dictionary, room: Dictionary) -> void:
	for entry in ROOM_RECIPES.get(room.type, []):
		if entry[1] == "center":
			var size := _dims(entry[0])
			var r: Rect2 = room.rect
			if minf(r.size.x, r.size.y) < 3.4:
				continue
			_place(b, room, entry[0], r.get_center() - size * 0.5 + Vector2(rng.randf_range(-0.3, 0.3), rng.randf_range(-0.2, 0.2)), entry[2])
		else:
			_place_against_walls(b, room, entry[0], entry[2])


## Try wall-hugging positions in seeded order; the first legal one wins. Illegal rooms skip the piece.
func _place_against_walls(b: Dictionary, room: Dictionary, asset_id: String, loot: String) -> bool:
	var size := _dims(asset_id)
	var r: Rect2 = Rect2(room.rect).grow(-WALL_INSET)
	var candidates: Array = []
	var x: float = r.position.x
	while x + size.x <= r.end.x:
		candidates.append(Vector2(x, r.position.y))
		candidates.append(Vector2(x, r.end.y - size.y))
		x += 0.25
	var y: float = r.position.y
	while y + size.y <= r.end.y:
		candidates.append(Vector2(r.position.x, y))
		candidates.append(Vector2(r.end.x - size.x, y))
		y += 0.25
	# Fisher-Yates with the seeded generator keeps placement deterministic.
	for i in range(candidates.size() - 1, 0, -1):
		var j := rng.randi_range(0, i)
		var tmp: Vector2 = candidates[i]
		candidates[i] = candidates[j]
		candidates[j] = tmp
	for p in candidates:
		if _place(b, room, asset_id, p, loot):
			return true
	return false


func _place(b: Dictionary, room: Dictionary, asset_id: String, pos: Vector2, loot: String) -> bool:
	var size := _dims(asset_id)
	var rect := Rect2(pos, size)
	if not Rect2(room.rect).grow(-WALL_INSET + 0.001).encloses(rect):
		return false
	for door in b.doors:
		var mid: Vector2 = (door.a + door.b) * 0.5
		var near := mid.clamp(rect.position, rect.end)
		if near.distance_to(mid) < DOOR_CLEARANCE + door.a.distance_to(door.b) * 0.5:
			return false
	for other in b.furniture:
		if Rect2(other.pos, other.size).grow(0.55).intersects(rect):
			return false
	var count := 0
	for other in b.furniture:
		if other.asset_id == asset_id:
			count += 1
	var item := {
		"id": "%s.%s.%s%s" % [b.id, room.type, String(asset_id).trim_prefix("ll_furniture_"), "" if count == 0 else "_%d" % count],
		"asset_id": asset_id, "name": String(catalog[asset_id].get("name", asset_id)).to_upper(),
		"pos": pos, "size": size, "tint": ROOM_TINTS.get(room.type, "777164"),
		"container": not loot.is_empty(), "room": room.id, "loot": {},
	}
	if not loot.is_empty():
		item.loot = _roll_loot(loot)
	b.furniture.append(item)
	return true


func _roll_loot(profile: String) -> Dictionary:
	var result := {}
	var table: Dictionary = LOOT_PROFILES[profile]
	var ids: Array = table.keys()
	ids.sort()
	for id in ids:
		var count := rng.randi_range(int(table[id][0]), int(table[id][1]))
		if count > 0:
			result[id] = count
	if result.is_empty():
		result[ids[0]] = 1
	return result


## Stable digest for reproducibility tests and save compatibility checks.
static func digest(plan: Dictionary) -> String:
	return JSON.stringify(_plain(plan)).sha256_text()


static func _plain(value: Variant) -> Variant:
	if value is Vector2:
		return [snappedf(value.x, 0.001), snappedf(value.y, 0.001)]
	if value is Rect2:
		return [snappedf(value.position.x, 0.001), snappedf(value.position.y, 0.001), snappedf(value.size.x, 0.001), snappedf(value.size.y, 0.001)]
	if value is Array:
		var out: Array = []
		for v in value:
			out.append(_plain(v))
		return out
	if value is Dictionary:
		var keys: Array = value.keys()
		keys.sort()
		var out := {}
		for k in keys:
			out[str(k)] = _plain(value[k])
		return out
	return value
