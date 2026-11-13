class_name Inv
extends RefCounted
## Inventory helpers. An inventory is just an Array of item Dictionaries.

static func add(arr: Array, it: Dictionary) -> void:
	if int(it.get("n", 1)) <= 0:
		return
	for o in arr:
		if Items.can_stack(o, it):
			o["n"] = int(o["n"]) + int(it["n"])
			if it.has("t") and float(it["t"]) < float(o["t"]):
				o["t"] = it["t"]
			return
	arr.append(it)

static func add_new(arr: Array, id: String, n: int = 1, hour: float = 0.0) -> void:
	var d: Dictionary = Items.def(id)
	if d.is_empty():
		return
	if Items.is_unique(d):
		for i in range(n):
			arr.append(Items.make(id, 1, hour))
	else:
		add(arr, Items.make(id, n, hour))

static func count(arr: Array, id: String) -> int:
	var n := 0
	for o in arr:
		if o["id"] == id:
			n += int(o["n"])
	return n

## remove n units of id. returns true if all were removed
static func take(arr: Array, id: String, n: int) -> bool:
	if count(arr, id) < n:
		return false
	var left: int = n
	var i: int = arr.size() - 1
	while i >= 0 and left > 0:
		var o: Dictionary = arr[i]
		if o["id"] == id:
			var k: int = mini(left, int(o["n"]))
			o["n"] = int(o["n"]) - k
			left -= k
			if int(o["n"]) <= 0:
				arr.remove_at(i)
		i -= 1
	return true

## split one unit (or n units) off a stack and return it as a new item
static func split(arr: Array, it: Dictionary, n: int = 1) -> Dictionary:
	var have: int = int(it.get("n", 1))
	if n >= have:
		arr.erase(it)
		return it
	it["n"] = have - n
	var o: Dictionary = it.duplicate(true)
	o["n"] = n
	return o

static func weight(arr: Array) -> float:
	var w := 0.0
	for o in arr:
		w += Items.weight(o)
	return w

static func find(arr: Array, id: String) -> Dictionary:
	for o in arr:
		if o["id"] == id:
			return o
	return {}

static func volume(arr: Array) -> float:
	var v := 0.0
	for o in arr:
		v += Items.vol(o)
	return v

static func find_tag(arr: Array, tag: String) -> Dictionary:
	for o in arr:
		if tag == "fire" and float(o.get("wet", 0.0)) > 0.0: continue     # damp matches will not strike
		if Items.has_tag(o, tag):
			return o
	return {}

static func has_tag(arr: Array, tag: String) -> bool:
	return not find_tag(arr, tag).is_empty()

## consume one use from a multi-use item; removes it (or swaps to its empty form) at zero
static func use_charge(arr: Array, it: Dictionary) -> void:
	var d: Dictionary = Items.def(it["id"])
	if not it.has("u"):
		var one: Dictionary = split(arr, it, 1)
		return
	it["u"] = int(it["u"]) - 1
	if int(it["u"]) <= 0 and not d.has("maxuses") and not d.has("gun"):
		arr.erase(it)
		if d.has("empty"):
			add(arr, Items.make(d["empty"], 1))
