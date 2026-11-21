class_name ArtModels
extends RefCounted
## The 2.5D models built from the founder's mesh recipes (tools/art/model_specs.py builds the part
## lists; tools/godot/render_models.gd renders them with the game's own camera). Every item has a
## model lying on the ground, weapons and tools a side view to hold, and some world props are
## models too, all at one true scale.

const DIR := "res://assets/art/models/"
## the world's scale: 30.37 px per metre in the camera plane, 26.3 px per metre of height
## (a 1.75 m person is 46 px, a 2.7 m storey 72 px, a tile about 1.49 m across)
const PX_PER_M := 30.37
const VERT_PX_PER_M := 26.3
const TILE_M := 1.49
## item models are stored at twice the world scale and drawn at half size
const ITEM_K := 2.0
## the smallest an item on the ground is drawn (px), so a ring or a pill bottle can still be seen
const MIN_GROUND_PX := 6.0

## world props that are models: prop name -> object
const PROPS := {"barrel": Defs.O_BARREL, "cardboard_boxes": Defs.O_BOXES, "ammo_crate": Defs.O_MIL_CRATE, "tyre_pile": Defs.O_TYRES,
	"traffic_cone": Defs.O_CONE, "cooler": Defs.O_COOLER, "coffin": Defs.O_COFFIN}

static func queue_jobs(jobs: Array[Callable]) -> void:
	if not FileAccess.file_exists(DIR + "manifest.json"):
		return
	var man: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(DIR + "manifest.json"))
	var ids: Array = (man.get("items", {}) as Dictionary).keys()
	var i := 0
	while i < ids.size():
		var chunk: Array = ids.slice(i, i + 24)
		jobs.append(func():
			for id in chunk:
				var e: Dictionary = man["items"][id]
				var m := {"dims": e.get("dims", [])}
				if e.has("g"):
					var hg: int = _add(e["g"])
					if hg >= 0: m["g"] = hg
				if e.has("h"):
					var hh: int = _add(e["h"])
					if hh >= 0: m["h"] = hh
				Art.models[String(id)] = m)
		i += 24
	queue_vehicle_jobs(jobs)
	jobs.append(func():
		for name in (man.get("props", {}) as Dictionary).keys():
			if not PROPS.has(name):
				continue
			var e2: Dictionary = man["props"][name]
			var img: Image = _img(String(e2["f"]))
			if img == null:
				continue
			var a: Array = e2["a"]
			# the model stands on the tile's centre, 16 px below the tile's top corner (the draw anchor)
			var hnd: int = Art.world.add(img, float(a[0]), float(a[1]) - 16.0, "", false)
			for r in range(4):
				Art.obj_spr[Defs.ocell(int(PROPS[name]), r, 0)] = hnd)

## vehicles rendered as 3D models (tools/godot/render_vehicles.gd): every heading, one piece per
## footprint tile and layer; the paint goes in obj_spr (drawn tinted), the rest in obj_fix
const VDIR := "res://assets/art/vehicles/"

static func vehicle_manifest() -> Dictionary:
	if not FileAccess.file_exists(VDIR + "manifest.json"):
		return {}
	var m = JSON.parse_string(FileAccess.get_file_as_string(VDIR + "manifest.json"))
	return m.get("vehicles", {}) if m is Dictionary else {}

## the objects drawn from the rendered vehicles (the box models of these are not painted)
static func rendered_vehicles() -> Dictionary:
	var out := {}
	var vm: Dictionary = vehicle_manifest()
	for name in vm.keys():
		out[int(vm[name]["oid"])] = true
	return out

static func queue_vehicle_jobs(jobs: Array[Callable]) -> void:
	var vm: Dictionary = vehicle_manifest()
	for name in vm.keys():
		var v: Dictionary = vm[name]
		jobs.append(func():
			var oid: int = int(v["oid"])
			var blank := -1
			for r in range(4):
				var e: Dictionary = v["rots"][r]
				if e.is_empty():
					continue
				var path: String = VDIR + String(e["f"])
				if not ResourceLoader.exists(path):
					continue
				var strip: Image = (load(path) as Texture2D).get_image()
				strip.convert(Image.FORMAT_RGBA8)
				var parts: Array = e["parts"]
				for p in range(parts.size()):
					var cell: int = Defs.ocell(oid, r, p)
					var layers: Array = parts[p]
					for layer in range(2):
						var q: Array = layers[layer]
						if q.is_empty():
							continue
						var hnd: int = Art.world.add(strip.get_region(Rect2i(int(q[0]), int(q[1]), int(q[2]), int(q[3]))), float(q[4]), float(q[5]), "", false)
						if layer == 0:
							Art.obj_spr[cell] = hnd
						else:
							Art.obj_fix[cell] = hnd
					if not Art.obj_spr.has(cell):
						# a piece with no paint showing still needs a sprite to stand for it
						if blank < 0:
							var im := Image.create(1, 1, false, Image.FORMAT_RGBA8)
							blank = Art.world.add(im, 0, 0, "", false)
						Art.obj_spr[cell] = blank)

static func _img(file: String) -> Image:
	var path: String = DIR + file
	if not ResourceLoader.exists(path):
		return null
	var im: Image = (load(path) as Texture2D).get_image()
	im.convert(Image.FORMAT_RGBA8)
	return im

static func _add(e: Dictionary) -> int:
	var im: Image = _img(String(e["f"]))
	if im == null:
		return -1
	var a: Array = e["a"]
	return Art.world.add(im, float(a[0]), float(a[1]), "", false)

## how much an item's ground model is scaled when drawn: half (it is stored at twice the world
## scale), or more for something so small it would vanish
static func ground_scale(hnd: int) -> float:
	var sz: Vector2 = Art.world.rects[hnd].size
	var k: float = 1.0 / ITEM_K
	var biggest: float = maxf(sz.x, sz.y) * k
	if biggest < MIN_GROUND_PX:
		k = MIN_GROUND_PX / maxf(maxf(sz.x, sz.y), 1.0)
	return k

## true size of an item model in metres (length, width, height)
static func dims(id: String) -> Array:
	return (Art.models.get(id, {}) as Dictionary).get("dims", [])
