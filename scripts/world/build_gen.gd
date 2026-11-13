class_name BuildGen
extends RefCounted
## Procedural buildings: floor plans, doors, windows, furniture and yards for every lot type.

const SHOP_KINDS := ["grocery", "pharmacy", "hardware", "clothing", "bookstore", "diner", "bar", "gas", "police",
	"clinic", "gunstore", "office", "warehouse", "school", "firestation"]

static func gen(kind: String, w: int, h: int, facing: int, seed_v: int, bld_id: int) -> LotBuilder.LotPlan:
	var rng: RandomNumberGenerator = Rng.make(seed_v)
	var swap: bool = facing == 1 or facing == 3
	var b := LotBuilder.new(h if swap else w, w if swap else h, rng)
	match kind:
		"house": _house_lot(b)
		"park": _park(b)
		"parking": _parking(b)
		"farm": _farm(b)
		"cabin": _cabin(b)
		"camp": _camp(b)
		"checkpoint": _checkpoint(b)
		"quarantine": _quarantine(b)
		"woods": _woods(b)
		_: _shop(b, kind)
	return b.finalize(facing, bld_id)

static func _bsp(r: Rect2i, rng: RandomNumberGenerator, min_side: int, max_area: int, out: Array) -> void:
	var can_x: bool = r.size.x >= min_side * 2
	var can_y: bool = r.size.y >= min_side * 2
	if r.size.x * r.size.y <= max_area or (not can_x and not can_y):
		out.append(r)
		return
	var split_x: bool = can_x and (not can_y or r.size.x > r.size.y or (r.size.x == r.size.y and rng.randf() < 0.5))
	if split_x:
		var c: int = rng.randi_range(min_side, r.size.x - min_side)
		_bsp(Rect2i(r.position.x, r.position.y, c, r.size.y), rng, min_side, max_area, out)
		_bsp(Rect2i(r.position.x + c, r.position.y, r.size.x - c, r.size.y), rng, min_side, max_area, out)
	else:
		var c2: int = rng.randi_range(min_side, r.size.y - min_side)
		_bsp(Rect2i(r.position.x, r.position.y, r.size.x, c2), rng, min_side, max_area, out)
		_bsp(Rect2i(r.position.x, r.position.y + c2, r.size.x, r.size.y - c2), rng, min_side, max_area, out)

static func _pick(rng: RandomNumberGenerator, arr: Array) -> Variant:
	return arr[rng.randi() % arr.size()]

# ------------------------------------------------------------------ houses
## builds a house inside rect; returns the outside cell of the front door
static func _house_at(b: LotBuilder, rect: Rect2i, lock_chance: float = 0.3) -> Vector2i:
	var rng: RandomNumberGenerator = b.rng
	var rects: Array = []
	_bsp(rect, rng, 3, rng.randi_range(22, 30), rects)
	# front rooms touch the bottom edge
	var living := -1
	var best := -1
	for i in range(rects.size()):
		var r: Rect2i = rects[i]
		if r.end.y == rect.end.y and r.size.x * r.size.y > best:
			best = r.size.x * r.size.y
			living = i
	var order: Array = [living]
	var rest: Array = []
	for i in range(rects.size()):
		if i != living:
			rest.append(i)
	rest.sort_custom(func(a2, b2): return rects[a2].size.x * rects[a2].size.y > rects[b2].size.x * rects[b2].size.y)
	var types: Array = ["living"]
	for k in range(rest.size()):
		order.append(rest[k])
		if k == 0: types.append("kitchen")
		elif k == rest.size() - 1: types.append("bathroom")
		elif k == 3: types.append(_pick(rng, ["study", "storage", "bedroom"]))
		else: types.append("bedroom")
	if rest.size() == 1:
		types[1] = "bedroom"
	var plaster: Array = [Defs.WM_PLASTER_CREAM, Defs.WM_PLASTER_BLUE, Defs.WM_PLASTER_GREEN, Defs.WM_PLASTER_ROSE, Defs.WM_PLASTER_TAN, Defs.WM_PLASTER_GREY]
	var base_room: int = b.rooms.size()
	for k in range(order.size()):
		var t: String = types[k]
		var fl: int = Defs.G_WOOD
		var wm: int = _pick(rng, plaster)
		match t:
			"living": fl = _pick(rng, [Defs.G_WOOD, Defs.G_WOOD_DARK, Defs.G_CARPET_BEIGE])
			"kitchen": fl = Defs.G_TILE
			"bathroom":
				fl = Defs.G_TILE_BLUE
				wm = Defs.WM_TILE_WHITE
			"bedroom": fl = _pick(rng, [Defs.G_CARPET_RED, Defs.G_CARPET_BLUE, Defs.G_CARPET_BEIGE, Defs.G_WOOD])
			"study": fl = Defs.G_WOOD_DARK
			"storage": fl = Defs.G_CONCRETE
		b.add_room(rects[order[k]], t, fl, wm)
	b.build_walls()
	# connect only this building's rooms
	var seen: Array = [base_room]
	var queue: Array = [base_room]
	while queue.size() > 0:
		var a: int = queue.pop_front()
		for bb in range(base_room, b.rooms.size()):
			if seen.has(bb):
				continue
			var kind: int = LotBuilder.E_DOOR
			if b.rooms[a]["type"] == "living" and b.rooms[bb]["type"] == "kitchen" and rng.randf() < 0.5:
				kind = LotBuilder.E_ARCH
			if b.door_between(a, bb, kind):
				seen.append(bb)
				queue.append(bb)
	var front: Vector2i = b.exterior_door(base_room, 2, rng.randf() < lock_chance)
	if b.rooms.size() - base_room > 1:
		var back_room: int = base_room + 1
		for side in [0, 1, 3]:
			if b.exterior_door(back_room, side, rng.randf() < 0.5).x >= 0:
				break
	b.windows(3, rng.randi() % 3)
	for ri in range(base_room, b.rooms.size()):
		_furnish_home(b, ri)
	_house_story(b, base_room)
	return front

## cellars and the small tragedies people left behind
static func _house_story(b: LotBuilder, base_room: int) -> void:
	var rng: RandomNumberGenerator = b.rng
	var n: int = b.rooms.size()
	# a hatch down to a cellar in about a third of homes
	if b.hatch_c.x < 0 and rng.randf() < 0.36:
		var order: Array = range(base_room, n)
		order.reverse()
		for ri in order:
			var t: String = b.rooms[ri]["type"]
			if t == "bathroom":
				continue
			var hc: Vector2i = b.place_free(ri, Defs.O_HATCH, 0, 0, 12)
			if hc.x >= 0:
				b.hatch_c = hc
				break
	# a second storey on the bigger homes
	if n - base_room >= 3 and rng.randf() < 0.45:
		var sc: Vector2i = b.place_free(base_room, Defs.O_STAIRS, 0, 0, 12)
		if sc.x >= 0:
			b.stairs_c = sc
	elif rng.randf() < 0.35:
		# no second storey, but a pull-down ladder to the attic
		var ac: Vector2i = b.place_free(base_room, Defs.O_ATTIC_LADDER, 0, 0, 12)
		if ac.x >= 0:
			b.stairs_c = ac
			b.attic = true
	var r: float = rng.randf()
	if r > 0.93:
		# somebody is still living here
		var nc: Vector2i = b.free_cell(base_room)
		if nc.x >= 0:
			b.npc_c.append([nc, false])
	if r < 0.06:
		# someone fortified this place and never left
		b.btype = "stash"
		b.flag_openings(base_room, LotBuilder.F_PLANK)
		b.place_wall(base_room, Defs.O_CRATE)
		var c: Vector2i = b.free_cell(base_room + (1 if n - base_room > 1 else 0))
		if c.x >= 0:
			b.corpse_c.append([c, "corpse_survivor"])
		if rng.randf() < 0.5:
			var z: Vector2i = b.free_cell(base_room)
			if z.x >= 0: b.zspawn_c.append(z)
		elif rng.randf() < 0.5:
			# ...or is still here, and does not want company
			var hc2: Vector2i = b.free_cell(base_room)
			if hc2.x >= 0: b.npc_c.append([hc2, true])
	elif r < 0.10:
		# a last stand in the living room
		for k in range(rng.randi_range(3, 5)):
			var c2: Vector2i = b.free_cell(base_room)
			if c2.x >= 0:
				b.corpse_c.append([c2, "corpse"])
				b.blood_c.append(c2)
		var c3: Vector2i = b.free_cell(base_room)
		if c3.x >= 0:
			b.corpse_c.append([c3, "corpse_armed"])
	elif r < 0.14:
		# looted: the door was forced
		b.flag_openings(base_room, LotBuilder.F_BROKEN, -1, true)
		var c4: Vector2i = b.free_cell(base_room)
		if c4.x >= 0:
			b.corpse_c.append([c4, "corpse_burglar"])
			b.blood_c.append(c4)
	elif r < 0.18 and n - base_room >= 3:
		# a room boarded shut from the outside, and what is still inside it
		var ri2: int = n - 1
		b.flag_openings(base_room, LotBuilder.F_PLANK, ri2, true)
		for k in range(rng.randi_range(1, 3)):
			var z2: Vector2i = b.free_cell(ri2)
			if z2.x >= 0: b.zspawn_c.append(z2)

static func _furnish_home(b: LotBuilder, ri: int) -> void:
	var rng: RandomNumberGenerator = b.rng
	var t: String = b.rooms[ri]["type"]
	var D := Defs
	match t:
		"living":
			b.place_wall(ri, D.O_SOFA)
			b.place_wall(ri, D.O_TV)
			if rng.randf() < 0.7: b.place_wall(ri, D.O_BOOKSHELF)
			if rng.randf() < 0.6: b.place_wall(ri, D.O_ARMCHAIR)
			if rng.randf() < 0.5: b.place_wall(ri, D.O_LAMP)
			if rng.randf() < 0.5: b.place_wall(ri, D.O_PLANT)
			var tb: Vector2i = b.place_free(ri, D.O_TABLE, 1)
			if tb.x >= 0:
				b.place_at(ri, D.O_CHAIR, tb.x + 1, tb.y, 1)
				b.place_at(ri, D.O_CHAIR, tb.x - 1, tb.y, 3)
		"kitchen":
			b.place_wall(ri, D.O_FRIDGE)
			b.place_wall(ri, D.O_STOVE)
			b.place_wall(ri, D.O_SINK_COUNTER)
			b.place_wall(ri, D.O_COUNTER)
			if rng.randf() < 0.7: b.place_wall(ri, D.O_COUNTER)
			var tb2: Vector2i = b.place_free(ri, D.O_TABLE, 1)
			if tb2.x >= 0:
				b.place_at(ri, D.O_CHAIR, tb2.x, tb2.y + 1, 0)
				b.place_at(ri, D.O_CHAIR, tb2.x, tb2.y - 1, 2)
			if rng.randf() < 0.3: b.place_wall(ri, D.O_TRASH_CAN)
		"bedroom":
			b.place_wall(ri, D.O_BED)
			b.place_wall(ri, D.O_WARDROBE)
			if rng.randf() < 0.8: b.place_wall(ri, D.O_NIGHTSTAND)
			if rng.randf() < 0.6: b.place_wall(ri, D.O_DRESSER)
			if rng.randf() < 0.35: b.place_wall(ri, D.O_DESK)
			if rng.randf() < 0.3: b.place_wall(ri, D.O_BOOKSHELF)
		"bathroom":
			b.place_wall(ri, D.O_TOILET)
			b.place_wall(ri, D.O_BATH_SINK)
			b.place_wall(ri, D.O_BATHTUB)
			if rng.randf() < 0.4: b.place_wall(ri, D.O_WASHER)
		"study":
			b.place_wall(ri, D.O_DESK)
			b.place_wall(ri, D.O_BOOKSHELF)
			b.place_wall(ri, D.O_BOOKSHELF)
			b.place_wall(ri, D.O_FILING)
			b.place_wall(ri, D.O_ARMCHAIR)
		"storage":
			b.place_wall(ri, D.O_CRATE)
			b.place_wall(ri, D.O_TOOL_SHELF)
			b.place_wall(ri, D.O_WORKBENCH)
			b.place_wall(ri, D.O_BOXES)
			b.place_wall(ri, D.O_WASHER)

static func _house_lot(b: LotBuilder) -> void:
	var rng: RandomNumberGenerator = b.rng
	b.btype = "house"
	b.ext_mat = _pick(rng, [Defs.WM_SIDING_WHITE, Defs.WM_SIDING_BLUE, Defs.WM_SIDING_TAN, Defs.WM_SIDING_GREEN, Defs.WM_SIDING_GREY,
		Defs.WM_SIDING_YELLOW, Defs.WM_BRICK_RED, Defs.WM_BRICK_BROWN])
	var front: int = rng.randi_range(3, 4)
	var drive: bool = b.cw >= 13 and rng.randf() < 0.75
	var left: int = 4 if drive else rng.randi_range(1, 2)
	var right: int = rng.randi_range(1, 2)
	var bw: int = clampi(b.cw - left - right, 6, 13)
	var bd: int = clampi(b.ch - front - rng.randi_range(4, 6), 6, 11)
	var x0: int = left + (b.cw - left - right - bw) / 2
	var y1: int = b.ch - front
	var y0: int = y1 - bd
	var door_out: Vector2i = _house_at(b, Rect2i(x0, y0, bw, bd))
	# path to the street
	if door_out.x >= 0:
		b.set_floor(Rect2i(door_out.x, door_out.y, 1, b.ch - door_out.y), Defs.G_CONCRETE)
		for v in range(door_out.y, b.ch):
			b.occ[v * b.cw + door_out.x] = 2
		b.put_yard(Defs.O_MAILBOX, door_out.x + (1 if door_out.x + 1 < b.cw - 1 else -1), b.ch - 1, 0)
	if drive:
		b.set_floor(Rect2i(1, y1 - 5, 3, b.ch - (y1 - 5)), Defs.G_CONCRETE)
		if rng.randf() < 0.6:
			var dr: float = rng.randf()
			b.put_yard(Defs.O_CAR_WRECK if dr < 0.15 else (Defs.O_PICKUP if dr < 0.32 else (Defs.O_VAN if dr < 0.42 else Defs.O_CAR)), 1, y1 - 4, 0 if rng.randf() < 0.5 else 2)
		elif rng.randf() < 0.5:
			b.put_yard(Defs.O_BICYCLE if rng.randf() < 0.65 else Defs.O_MOTORBIKE, 2, y1 - 3, 0 if rng.randf() < 0.5 else 2)
	# backyard fence
	var fr: float = rng.randf()
	if fr < 0.7:
		var kind: int = LotBuilder.E_PICKET
		var gate: int = LotBuilder.E_PICKET_GATE
		if fr < 0.1:
			kind = LotBuilder.E_CHAIN
			gate = LotBuilder.E_CHAIN_GATE
		elif fr < 0.22:
			kind = LotBuilder.E_HEDGE
			gate = LotBuilder.E_NONE
		var yard := Rect2i(1, 1, b.cw - 2, y1 - 6 if drive else y1 - 1)
		yard.size.y = maxi(yard.size.y, y0)
		var gates: Array = [Vector2i(b.cw - 2, yard.end.y - 1), Vector2i(b.cw - 2, yard.end.y), Vector2i(x0 - 1, yard.end.y), Vector2i(x0 - 1, yard.end.y - 1)]
		b.fence_rect(yard, kind, gate, gates)
	# garden clutter
	for k in range(rng.randi_range(1, 4)):
		var u: int = rng.randi_range(1, b.cw - 2)
		var v: int = rng.randi_range(1, maxi(y0 - 2, 1))
		b.put_yard(_pick(rng, [Defs.O_TREE_OAK, Defs.O_TREE_BIRCH, Defs.O_BUSH, Defs.O_BUSH, Defs.O_FLOWERS, Defs.O_PICNIC_TABLE, Defs.O_TREE_PINE]), u, v, 0)
	if rng.randf() < 0.35:
		b.put_yard(Defs.O_TRASH_CAN, x0 + bw, y1 - 1, 0)
	if rng.randf() < 0.3:
		b.put_yard(_pick(rng, [Defs.O_BUSH, Defs.O_FLOWERS]), rng.randi_range(x0, x0 + bw - 1), y1 + 1, 0)
	if rng.randf() < 0.12:
		# survivor vegetable patch
		var gx: int = rng.randi_range(2, maxi(b.cw - 5, 2))
		for j in range(2):
			for i in range(3):
				if b.inb(gx + i, 2 + j) and b.room_at(gx + i, 2 + j) < 0 and b.occ[(2 + j) * b.cw + gx + i] == 0:
					b.floor_g[(2 + j) * b.cw + gx + i] = Defs.G_SOIL
					b.placements.append([_pick(rng, [Defs.O_CROP_POTATO, Defs.O_CROP_CABBAGE, Defs.O_CROP_CARROT, Defs.O_CROP_TOMATO, Defs.O_CROP_CORN, Defs.O_CROP_WHEAT, Defs.O_CROP_PUMPKIN, Defs.O_CROP_ONION, Defs.O_CROP_BEANS]) | 0x10000, gx + i, 2 + j, 0])
					b.occ[(2 + j) * b.cw + gx + i] = 1

# ------------------------------------------------------------------ shops & civic
static func _rows(b: LotBuilder, ri: int, id: int, alt: int = -1) -> void:
	var R: Rect2i = b.rooms[ri]["r"]
	var mid: int = R.position.x + R.size.x / 2
	var v: int = R.position.y + 1
	while v < R.end.y - 2:
		for u in range(R.position.x + 1, R.end.x - 1):
			if u == mid:
				continue
			var oid: int = id
			if alt >= 0 and b.rng.randf() < 0.25:
				oid = alt
			b.place_at(ri, oid, u, v, 0)
		v += 2

static func _many(b: LotBuilder, ri: int, id: int, n: int) -> void:
	for k in range(n):
		b.place_wall(ri, id)

static func _tables(b: LotBuilder, ri: int, n: int) -> void:
	for k in range(n):
		var tb: Vector2i = b.place_free(ri, Defs.O_TABLE, 1)
		if tb.x >= 0:
			b.place_at(ri, Defs.O_CHAIR, tb.x + 1, tb.y, 1)
			b.place_at(ri, Defs.O_CHAIR, tb.x - 1, tb.y, 3)

static func _shop(b: LotBuilder, kind: String) -> void:
	var rng: RandomNumberGenerator = b.rng
	var D := Defs
	b.btype = kind
	b.flat_roof = true
	b.ext_mat = _pick(rng, [D.WM_BRICK_RED, D.WM_BRICK_BROWN, D.WM_CONCRETE, D.WM_BRICK_GREY, D.WM_SIDING_GREY])
	var apron: int = 2
	if kind == "gas":
		apron = 7
	if kind == "warehouse" or kind == "firestation":
		b.ext_mat = D.WM_METAL if kind == "warehouse" else D.WM_BRICK_RED
		apron = 3
	var x0 := 1
	var x1: int = b.cw - 1
	var y1: int = b.ch - apron
	var depth: int = clampi(y1 - 2, 6, 18)
	if kind == "gas":
		depth = mini(depth, 7)
		x0 = maxi(1, b.cw / 2 - 5)
		x1 = mini(b.cw - 1, x0 + 10)
	var y0: int = y1 - depth
	var back_d: int = 0
	if depth >= 9 and kind != "warehouse":
		back_d = clampi(depth / 3, 3, 5)
	var main_floor: int = D.G_LINO
	match kind:
		"hardware", "warehouse", "firestation", "gunstore": main_floor = D.G_CONCRETE
		"bar", "bookstore", "diner": main_floor = D.G_WOOD_DARK
		"clothing", "office": main_floor = D.G_CARPET_BLUE
		"clinic", "pharmacy": main_floor = D.G_TILE
	var wm: int = _pick(rng, [D.WM_PLASTER_CREAM, D.WM_PLASTER_GREY, D.WM_PLASTER_TAN])
	if kind == "warehouse":
		wm = D.WM_METAL
	b.add_room(Rect2i(x0, y0 + back_d, x1 - x0, depth - back_d), "main", main_floor, wm)
	var back_types: Array = ["storage"]
	match kind:
		"police": back_types = ["armory", "office", "storage"]
		"clinic": back_types = ["ward", "office", "storage"]
		"diner", "bar": back_types = ["kitchen", "storage"]
		"school": back_types = ["class", "class", "office"]
		"office": back_types = ["office", "office", "bathroom"]
		"grocery", "hardware": back_types = ["storage", "office"]
		"firestation": back_types = ["bunk", "storage"]
	if back_d > 0:
		var nb: int = mini(back_types.size(), maxi(1, (x1 - x0) / 4))
		var bx: int = x0
		for k in range(nb):
			var bw: int = (x1 - x0) / nb if k < nb - 1 else x1 - bx
			var fl: int = D.G_CONCRETE
			var t: String = back_types[k]
			if t == "office" or t == "bunk": fl = D.G_CARPET_BEIGE
			elif t == "kitchen" or t == "ward" or t == "bathroom": fl = D.G_TILE
			elif t == "class": fl = D.G_LINO
			b.add_room(Rect2i(bx, y0, bw, back_d), t, fl, wm if t != "bathroom" else D.WM_TILE_WHITE)
			bx += bw
	b.build_walls()
	b.connect_rooms(0)
	var front_lock: float = 0.3
	if kind == "police" or kind == "gunstore":
		front_lock = 0.7
	var door_out: Vector2i = b.exterior_door(0, 2, rng.randf() < front_lock)
	if kind == "warehouse" or kind == "firestation" or kind == "grocery":
		b.exterior_door(0, 2, rng.randf() < 0.5)
	if b.rooms.size() > 1:
		b.exterior_door(b.rooms.size() - 1, 0, rng.randf() < 0.6)
	else:
		b.exterior_door(0, 0, rng.randf() < 0.6)
	b.windows(2 if kind != "warehouse" and kind != "gunstore" and kind != "police" else 5, rng.randi() % 2)
	b.set_floor(Rect2i(0, y1, b.cw, apron), D.G_CONCRETE)
	# ---- main room
	match kind:
		"grocery":
			_many(b, 0, D.O_FREEZER, 4)
			_many(b, 0, D.O_STORE_COUNTER, 2)
			_rows(b, 0, D.O_STORE_SHELF)
			b.put_yard(D.O_VENDING, x0 + 1, y1, 0)
		"pharmacy":
			_many(b, 0, D.O_MED_CABINET, 5)
			_many(b, 0, D.O_STORE_COUNTER, 1)
			_rows(b, 0, D.O_STORE_SHELF)
		"hardware":
			_many(b, 0, D.O_TOOL_SHELF, 5)
			_many(b, 0, D.O_STORE_COUNTER, 1)
			_many(b, 0, D.O_WORKBENCH, 1)
			_rows(b, 0, D.O_TOOL_SHELF, D.O_CRATE)
		"clothing":
			_many(b, 0, D.O_STORE_COUNTER, 1)
			_many(b, 0, D.O_WARDROBE, 2)
			_rows(b, 0, D.O_CLOTHES_RACK)
		"bookstore":
			_many(b, 0, D.O_BOOKSHELF, 8)
			_many(b, 0, D.O_STORE_COUNTER, 1)
			_many(b, 0, D.O_ARMCHAIR, 2)
			_rows(b, 0, D.O_BOOKSHELF)
		"diner":
			_many(b, 0, D.O_BAR_COUNTER, 3)
			_many(b, 0, D.O_VENDING, 1)
			_tables(b, 0, 8)
		"bar":
			_many(b, 0, D.O_BAR_COUNTER, 5)
			_tables(b, 0, 5)
			for k in range(5):
				b.place_free(0, D.O_STOOL, 1)
		"gas":
			_many(b, 0, D.O_STORE_COUNTER, 1)
			_many(b, 0, D.O_FREEZER, 2)
			_many(b, 0, D.O_STORE_SHELF, 4)
			_many(b, 0, D.O_VENDING, 1)
			for k in range(2):
				b.put_yard(D.O_GAS_PUMP, b.cw / 2 - 3 + k * 5, y1 + 3, 0)
			b.set_floor(Rect2i(0, y1, b.cw, apron), D.G_ASPHALT)
		"police":
			_many(b, 0, D.O_DESK, 4)
			_many(b, 0, D.O_FILING, 3)
			_many(b, 0, D.O_LOCKER, 3)
			_many(b, 0, D.O_VENDING, 1)
			_many(b, 0, D.O_CHAIR, 3)
		"clinic":
			_many(b, 0, D.O_STORE_COUNTER, 1)
			_many(b, 0, D.O_CHAIR, 5)
			_many(b, 0, D.O_MED_CABINET, 2)
			_many(b, 0, D.O_HOSPITAL_BED, 2)
			_many(b, 0, D.O_PLANT, 2)
		"gunstore":
			_many(b, 0, D.O_GUN_LOCKER, 4)
			_many(b, 0, D.O_STORE_COUNTER, 2)
			_many(b, 0, D.O_LOCKER, 2)
			_many(b, 0, D.O_CRATE, 2)
		"office":
			_many(b, 0, D.O_DESK, 8)
			_many(b, 0, D.O_FILING, 4)
			_many(b, 0, D.O_PLANT, 2)
			_many(b, 0, D.O_VENDING, 1)
		"warehouse":
			_many(b, 0, D.O_METAL_SHELF, 10)
			_rows(b, 0, D.O_METAL_SHELF, D.O_CRATE)
			for k in range(6):
				b.place_free(0, _pick(rng, [D.O_PALLET, D.O_BARREL, D.O_BOXES, D.O_CRATE]), 1)
		"school":
			_many(b, 0, D.O_LOCKER, 8)
			_many(b, 0, D.O_BOOKSHELF, 2)
			var R: Rect2i = b.rooms[0]["r"]
			var v: int = R.position.y + 2
			while v < R.end.y - 1:
				var u: int = R.position.x + 2
				while u < R.end.x - 2:
					b.place_at(0, D.O_SCHOOL_DESK, u, v, 0)
					u += 2
				v += 2
		"firestation":
			_many(b, 0, D.O_LOCKER, 6)
			_many(b, 0, D.O_TOOL_SHELF, 3)
			_many(b, 0, D.O_CRATE, 2)
			_many(b, 0, D.O_WORKBENCH, 1)
	# ---- back rooms
	for ri in range(1, b.rooms.size()):
		match b.rooms[ri]["type"]:
			"storage":
				_many(b, ri, D.O_METAL_SHELF, 2)
				_many(b, ri, D.O_CRATE, 2)
				_many(b, ri, D.O_BOXES, 2)
			"office":
				_many(b, ri, D.O_DESK, 1)
				_many(b, ri, D.O_FILING, 2)
				_many(b, ri, D.O_BOOKSHELF, 1)
			"armory":
				_many(b, ri, D.O_GUN_LOCKER, 3)
				_many(b, ri, D.O_LOCKER, 2)
			"ward":
				_many(b, ri, D.O_HOSPITAL_BED, 3)
				_many(b, ri, D.O_MED_CABINET, 3)
			"kitchen":
				_many(b, ri, D.O_STOVE, 2)
				_many(b, ri, D.O_FRIDGE, 2)
				_many(b, ri, D.O_SINK_COUNTER, 1)
				_many(b, ri, D.O_COUNTER, 2)
			"class":
				_many(b, ri, D.O_BOOKSHELF, 1)
				_many(b, ri, D.O_DESK, 1)
				b.place_free(ri, D.O_SCHOOL_DESK, 1, 0)
				b.place_free(ri, D.O_SCHOOL_DESK, 1, 0)
			"bathroom":
				_many(b, ri, D.O_TOILET, 2)
				_many(b, ri, D.O_BATH_SINK, 1)
			"bunk":
				_many(b, ri, D.O_BED, 3)
				_many(b, ri, D.O_WARDROBE, 1)
	# ---- outside
	b.put_yard(D.O_DUMPSTER, x0 + 1, maxi(y0 - 1, 0), 0)
	if rng.randf() < 0.5:
		b.put_yard(D.O_TRASH_CAN, x1 - 1, y1, 0)
	if rng.randf() < 0.4 and kind != "gas":
		b.put_yard(D.O_BENCH, x1 - 3, y1, 2)
	if door_out.x >= 0 and rng.randf() < 0.3:
		b.put_yard(D.O_STREET_LAMP, clampi(door_out.x + 2, 0, b.cw - 1), b.ch - 1, 0)

# ------------------------------------------------------------------ open lots
static func _park(b: LotBuilder) -> void:
	var rng: RandomNumberGenerator = b.rng
	b.btype = "park"
	b.set_floor(Rect2i(0, b.ch / 2, b.cw, 1), Defs.G_GRAVEL)
	b.set_floor(Rect2i(b.cw / 2, 0, 1, b.ch), Defs.G_GRAVEL)
	for u in range(b.cw):
		b.occ[(b.ch / 2) * b.cw + u] = 2
	for v in range(b.ch):
		b.occ[v * b.cw + b.cw / 2] = 2
	var n: int = b.cw * b.ch / 14
	for k in range(n):
		var id: int = _pick(rng, [Defs.O_TREE_OAK, Defs.O_TREE_OAK, Defs.O_TREE_BIRCH, Defs.O_BUSH, Defs.O_FLOWERS, Defs.O_FLOWERS, Defs.O_BENCH, Defs.O_PICNIC_TABLE, Defs.O_TRASH_CAN, Defs.O_TREE_PINE])
		b.put_yard(id, rng.randi_range(0, b.cw - 1), rng.randi_range(0, b.ch - 1), rng.randi() % 4)

static func _parking(b: LotBuilder) -> void:
	var rng: RandomNumberGenerator = b.rng
	b.btype = "parking"
	b.set_floor(Rect2i(0, 0, b.cw, b.ch), Defs.G_ASPHALT)
	var v := 1
	while v + 4 <= b.ch - 1:
		b.set_floor(Rect2i(1, v, b.cw - 2, 4), Defs.G_PARKING)
		var u := 1
		while u + 2 <= b.cw - 1:
			if rng.randf() < 0.3:
				var pr: float = rng.randf()
				var lot_k: String = b.btype
				var pick_id: int = Defs.O_CAR_WRECK if pr < 0.25 else (Defs.O_VAN if pr < 0.4 else (Defs.O_PICKUP if pr < 0.5 else Defs.O_CAR))
				if lot_k == "police" and pr > 0.4: pick_id = Defs.O_POLICE_CAR
				elif (lot_k == "clinic" or lot_k == "hospital") and pr > 0.4: pick_id = Defs.O_AMBULANCE
				elif (lot_k == "warehouse" or lot_k == "hardware" or lot_k == "grocery") and pr > 0.55: pick_id = Defs.O_TRUCK
				elif lot_k == "school" and pr > 0.6: pick_id = Defs.O_BUS
				b.put_yard(pick_id, u, v, 0 if rng.randf() < 0.5 else 2)
			u += 3
		v += 7

static func _woods(b: LotBuilder) -> void:
	var rng: RandomNumberGenerator = b.rng
	b.btype = "woods"
	for k in range(b.cw * b.ch / 9):
		b.put_yard(_pick(rng, [Defs.O_TREE_OAK, Defs.O_TREE_PINE, Defs.O_TREE_BIRCH, Defs.O_BUSH, Defs.O_TALL_GRASS]), rng.randi_range(0, b.cw - 1), rng.randi_range(0, b.ch - 1), 0)

static func _farm(b: LotBuilder) -> void:
	var rng: RandomNumberGenerator = b.rng
	b.btype = "farm"
	b.ext_mat = _pick(rng, [Defs.WM_SIDING_WHITE, Defs.WM_SIDING_TAN, Defs.WM_SIDING_YELLOW])
	var hw: int = clampi(b.cw / 3, 8, 11)
	var door_out: Vector2i = _house_at(b, Rect2i(2, b.ch - 4 - 8, hw, 8), 0.2)
	if door_out.x >= 0:
		b.set_floor(Rect2i(door_out.x, door_out.y, 1, b.ch - door_out.y), Defs.G_DIRT)
	# barn
	var bw: int = clampi(b.cw / 4, 7, 9)
	var bx: int = b.cw - bw - 3
	var barn := Rect2i(bx, b.ch - 5 - 11, bw, 11)
	var ri: int = b.add_room(barn, "barn", Defs.G_PLANK, Defs.WM_BUILT_PLANK)
	b.build_walls()
	b.exterior_door(ri, 2, false, LotBuilder.E_ARCH)
	b.exterior_door(ri, 2, false, LotBuilder.E_ARCH)
	_many(b, ri, Defs.O_HAY, 6)
	_many(b, ri, Defs.O_CRATE, 3)
	_many(b, ri, Defs.O_TOOL_SHELF, 2)
	_many(b, ri, Defs.O_BARREL, 2)
	_many(b, ri, Defs.O_WORKBENCH, 1)
	b.set_floor(Rect2i(bx, barn.end.y, bw, b.ch - barn.end.y), Defs.G_DIRT)
	b.set_floor(Rect2i(2, b.ch - 3, b.cw - 4, 2), Defs.G_DIRT)
	# fields
	var field := Rect2i(2, 2, b.cw - 4, b.ch - 22)
	if field.size.y >= 4:
		var crops: Array = [Defs.O_CROP_POTATO, Defs.O_CROP_CABBAGE, Defs.O_CROP_CARROT, Defs.O_CROP_TOMATO, Defs.O_CROP_CORN, Defs.O_CROP_WHEAT, Defs.O_CROP_PUMPKIN, Defs.O_CROP_ONION, Defs.O_CROP_BEANS]
		for v in range(field.position.y, field.end.y):
			for u in range(field.position.x, field.end.x):
				if b.room_at(u, v) >= 0:
					continue
				b.floor_g[v * b.cw + u] = Defs.G_SOIL
				if (v - field.position.y) % 2 == 0 and rng.randf() < 0.55:
					var crop: int = crops[((u - field.position.x) / 6) % 4]
					b.placements.append([crop | 0x10000, u, v, 0])
					b.occ[v * b.cw + u] = 1
		b.fence_rect(field.grow(1), LotBuilder.E_PICKET, LotBuilder.E_PICKET_GATE, [Vector2i(field.position.x + 3, field.end.y), Vector2i(field.position.x + 3, field.end.y + 1), Vector2i(field.end.x - 4, field.end.y), Vector2i(field.end.x - 4, field.end.y + 1)])
	for k in range(5):
		b.put_yard(_pick(rng, [Defs.O_TREE_OAK, Defs.O_HAY, Defs.O_BARREL, Defs.O_BUSH]), rng.randi_range(1, b.cw - 2), rng.randi_range(b.ch - 20, b.ch - 2), 0)
	b.put_yard(Defs.O_PICKUP if rng.randf() < 0.7 else Defs.O_CAR_WRECK, hw + 4, b.ch - 9, 0)
	b.put_yard(Defs.O_COOP, hw + 8, b.ch - 5, 2)
	b.put_yard(Defs.O_WELL, hw + 7, b.ch - 9, 0)

static func _cabin(b: LotBuilder) -> void:
	var rng: RandomNumberGenerator = b.rng
	b.btype = "cabin"
	b.ext_mat = Defs.WM_LOG
	var w: int = clampi(b.cw - 6, 5, 8)
	var d: int = clampi(b.ch - 7, 5, 7)
	var x0: int = (b.cw - w) / 2
	var y1: int = b.ch - 3
	var rects: Array = []
	if w >= 7 and rng.randf() < 0.6:
		rects = [Rect2i(x0, y1 - d, w - 3, d), Rect2i(x0 + w - 3, y1 - d, 3, d)]
	else:
		rects = [Rect2i(x0, y1 - d, w, d)]
	b.add_room(rects[0], "cabin", Defs.G_PLANK, Defs.WM_LOG)
	if rects.size() > 1:
		b.add_room(rects[1], "bedroom", Defs.G_PLANK, Defs.WM_LOG)
	b.build_walls()
	b.connect_rooms(0)
	var door_out: Vector2i = b.exterior_door(0, 2, rng.randf() < 0.25)
	b.windows(3, rng.randi() % 3)
	b.place_wall(0, Defs.O_STOVE)
	b.place_wall(0, Defs.O_COUNTER)
	b.place_wall(0, Defs.O_CRATE)
	b.place_wall(0, Defs.O_BOOKSHELF)
	b.place_wall(0, Defs.O_ARMCHAIR)
	var last: int = b.rooms.size() - 1
	b.place_wall(last, Defs.O_BED)
	b.place_wall(last, Defs.O_WARDROBE)
	b.place_free(0, Defs.O_TABLE, 1)
	if rng.randf() < 0.45:
		var hc: Vector2i = b.place_free(0, Defs.O_HATCH, 0, 0, 12)
		if hc.x >= 0:
			b.hatch_c = hc
	if door_out.x >= 0:
		b.set_floor(Rect2i(door_out.x, door_out.y, 1, b.ch - door_out.y), Defs.G_DIRT)
	b.put_yard(Defs.O_STUMP, x0 - 2, y1 - 2, 0)
	b.put_yard(Defs.O_BARREL, x0 + w, y1 - 1, 0)
	b.put_yard(Defs.O_CAMPFIRE, clampi(x0 + w / 2 + 2, 0, b.cw - 1), b.ch - 1, 0)
	for k in range(4):
		b.put_yard(_pick(rng, [Defs.O_TREE_PINE, Defs.O_TREE_OAK, Defs.O_ROCK, Defs.O_BUSH]), rng.randi_range(0, b.cw - 1), rng.randi_range(0, 2), 0)

## an army roadblock that did not hold: sandbags, a tent, crates, and the soldiers who stayed
static func _checkpoint(b: LotBuilder) -> void:
	var rng: RandomNumberGenerator = b.rng
	b.btype = "checkpoint"
	b.set_floor(Rect2i(1, 1, b.cw - 2, b.ch - 2), Defs.G_GRAVEL)
	for u in range(2, b.cw - 2):
		if u < b.cw / 2 - 1 or u > b.cw / 2 + 1:
			b.put_yard(Defs.O_SANDBAG, u, b.ch - 2, 0)
	for v in range(3, b.ch - 2):
		b.put_yard(Defs.O_SANDBAG, 2, v, 0)
		b.put_yard(Defs.O_SANDBAG, b.cw - 3, v, 0)
	b.put_yard(Defs.O_TENT, 4, 2, 0)
	b.put_yard(Defs.O_MIL_CRATE, 7, 3, 0)
	b.put_yard(Defs.O_MIL_CRATE, 8, 3, 1)
	b.put_yard(Defs.O_MIL_CRATE, b.cw - 6, 3, 0)
	b.put_yard(Defs.O_STREET_LAMP, b.cw / 2, 2, 0)
	b.put_yard(Defs.O_TRUCK if rng.randf() < 0.6 else Defs.O_CAR_WRECK, b.cw - 6, 5, 0)
	for k in range(rng.randi_range(2, 4)):
		var c: Vector2i = Vector2i(rng.randi_range(4, b.cw - 5), rng.randi_range(5, b.ch - 4))
		b.corpse_c.append([c, "corpse_armed"])
		b.blood_c.append(c)
	for k2 in range(rng.randi_range(4, 7)):
		b.zspawn_c.append(Vector2i(rng.randi_range(3, b.cw - 4), rng.randi_range(3, b.ch - 3)))

## a fenced field camp for the sick, overrun from the inside
static func _quarantine(b: LotBuilder) -> void:
	var rng: RandomNumberGenerator = b.rng
	b.btype = "quarantine"
	b.set_floor(Rect2i(1, 1, b.cw - 2, b.ch - 2), Defs.G_DIRT)
	b.fence_rect(Rect2i(1, 1, b.cw - 2, b.ch - 2), LotBuilder.E_CHAIN, LotBuilder.E_PICKET_GATE, [Vector2i(b.cw / 2, b.ch - 1)])
	for row in range(3):
		for col in range(3):
			b.put_yard(Defs.O_TENT, 3 + col * 8, 3 + row * 7, 0)
			b.put_yard(Defs.O_HOSPITAL_BED, 6 + col * 8, 3 + row * 7, 0)
	b.put_yard(Defs.O_MED_CABINET, b.cw - 4, 3, 0)
	b.put_yard(Defs.O_MED_CABINET, b.cw - 4, 4, 0)
	b.put_yard(Defs.O_MIL_CRATE, b.cw - 5, b.ch - 5, 0)
	b.put_yard(Defs.O_AMBULANCE if rng.randf() < 0.7 else Defs.O_CAR_WRECK, 2, b.ch - 7, 0)
	for k in range(rng.randi_range(5, 9)):
		var c: Vector2i = Vector2i(rng.randi_range(3, b.cw - 4), rng.randi_range(3, b.ch - 4))
		b.corpse_c.append([c, "corpse"])
		b.blood_c.append(c)
	for k2 in range(rng.randi_range(9, 14)):
		b.zspawn_c.append(Vector2i(rng.randi_range(3, b.cw - 4), rng.randi_range(3, b.ch - 4)))

static func _camp(b: LotBuilder) -> void:
	var rng: RandomNumberGenerator = b.rng
	b.btype = "camp"
	var cx: int = b.cw / 2
	var cy: int = b.ch / 2
	b.set_floor(Rect2i(cx - 2, cy - 2, 5, 5), Defs.G_DIRT)
	b.put_yard(Defs.O_CAMPFIRE, cx, cy, 0)
	b.put_yard(Defs.O_BEDROLL, cx - 2, cy, 0)
	b.put_yard(Defs.O_BEDROLL, cx + 2, cy - 1, 0)
	b.put_yard(Defs.O_CRATE, cx, cy - 2, 0)
	b.put_yard(Defs.O_BOXES, cx + 1, cy + 2, 0)
	b.put_yard(Defs.O_STUMP, cx - 1, cy + 2, 0)
	if rng.randf() < 0.5:
		b.corpse_c.append([Vector2i(cx - 2, cy + 1), "corpse_survivor"])
		b.blood_c.append(Vector2i(cx - 2, cy + 1))
	for k in range(6):
		b.put_yard(_pick(rng, [Defs.O_TREE_PINE, Defs.O_TREE_OAK, Defs.O_BUSH, Defs.O_ROCK]), rng.randi_range(0, b.cw - 1), rng.randi_range(0, b.ch - 1), 0)
