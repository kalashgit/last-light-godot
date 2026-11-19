class_name Art
extends RefCounted
## Registry of all procedurally generated sprites. Everything visible in the game is
## painted here from code (item icons come from the reference sprite sheets). The first launch
## paints it all and keeps the result in user://art_cache; later launches load that in a moment,
## and paint afresh whenever the game's code or art files change.

const VERSION := 8

static var ready := false
static var world: Atlas          # ground, walls, objects
static var chars: Atlas          # character layers
static var icons: Atlas          # item icons, moodles, ui glyphs

## ground[g] -> Array[int] handles (variants)
static var ground: Array = []
## wall sprite handles: wall_spr[tex][orient 0=N 1=W][variant]
static var wall_spr: Array = []
## object sprites keyed by cell value (id | rot<<10 | part<<12)
static var obj_spr: Dictionary = {}
## named overlays (N/W arrays)
static var ov: Dictionary = {}
## item icon handles by item id
static var item_icon: Dictionary = {}
## the icon a perishable shows once it has rotted, by item id (only where the sheets draw one)
static var item_icon_rot: Dictionary = {}
static var misc: Dictionary = {}
## character frames: see ArtChars
static var char_frames: Dictionary = {}

const WV_SOLID := 0
const WV_WINDOW := 1
const WV_DOOR := 2
const WV_CUT := 3
const WV_CUT_DOOR := 4
const WV_POST := 5
const WV_CUT_POST := 6

static var _jobs: Array[Callable] = []
static var _job_i := 0
static var use_cache := true      # tests switch it off to paint from scratch
static var from_cache := false    # whether the art now loaded came from the cache
const CACHE_DIR := "user://art_cache/"

static func begin() -> void:
	ready = false
	world = Atlas.new()
	chars = Atlas.new()
	icons = Atlas.new()
	icons.width = 512
	ground.clear()
	wall_spr.clear()
	obj_spr.clear()
	ov.clear()
	item_icon.clear()
	item_icon_rot.clear()
	misc.clear()
	char_frames.clear()
	ArtIcons.sheet_icons.clear()
	_jobs.clear()
	_job_i = 0
	from_cache = false
	if use_cache and load_cache():
		from_cache = true
		ready = true
		return
	ArtWorld.queue_jobs(_jobs)
	ArtChars.queue_jobs(_jobs)
	ArtIcons.queue_jobs(_jobs)
	_jobs.append(func():
		world.pack()
		chars.pack()
		icons.pack()
		ready = true
		if use_cache:
			save_cache())

## run generation jobs for up to budget_ms. returns progress 0..1
static func step(budget_ms: float) -> float:
	var t0: int = Time.get_ticks_usec()
	while _job_i < _jobs.size():
		_jobs[_job_i].call()
		_job_i += 1
		if (Time.get_ticks_usec() - t0) / 1000.0 > budget_ms:
			break
	return float(_job_i) / float(maxi(_jobs.size(), 1))

# ------------------------------------------------------------------ cache
## what the art was painted from: the game's scripts and data, the reference sheets, the engine
static func cache_key() -> String:
	var ctx := HashingContext.new()
	ctx.start(HashingContext.HASH_MD5)
	ctx.update(("%d|%s" % [VERSION, str(Engine.get_version_info().get("string", ""))]).to_utf8_buffer())
	var files: Array = []
	for d in ["res://scripts", "res://data", "res://assets/art"]:
		_list_files(d, files)
	files.sort()
	for f in files:
		ctx.update((String(f) + "=" + FileAccess.get_md5(String(f))).to_utf8_buffer())
	return ctx.finish().hex_encode()

static func _list_files(dir: String, out: Array) -> void:
	var da := DirAccess.open(dir)
	if da == null:
		return
	for f in da.get_files():
		if f.ends_with(".gd") or f.ends_with(".json") or f.ends_with(".png"):
			out.append(dir + "/" + f)
	for sd in da.get_directories():
		if not sd.begins_with("."):
			_list_files(dir + "/" + sd, out)

static func _atlases() -> Dictionary:
	return {"world": world, "chars": chars, "icons": icons}

## keep the painted art. The index is written last, so a half-written cache is never used.
static func save_cache() -> bool:
	DirAccess.make_dir_recursive_absolute(CACHE_DIR)
	var meta := {"key": cache_key(), "atlas": {}, "ground": ground, "wall_spr": wall_spr, "obj_spr": obj_spr, "ov": ov,
		"item_icon": item_icon, "item_icon_rot": item_icon_rot, "misc": misc, "char_frames": char_frames, "sheet_icons": ArtIcons.sheet_icons}
	var at: Dictionary = _atlases()
	for nm in at.keys():
		var a: Atlas = at[nm]
		if a.image == null or a.image.save_png(CACHE_DIR + nm + ".png") != OK:
			return false
		meta["atlas"][nm] = {"rects": Array(a.rects), "offs": Array(a.offs), "names": a.names, "width": a.width, "height": a.height}
	var tmp := CACHE_DIR + "index.tmp"
	var f := FileAccess.open(tmp, FileAccess.WRITE)
	if f == null:
		return false
	f.store_var(meta)
	f.close()
	return DirAccess.rename_absolute(tmp, CACHE_DIR + "index.bin") == OK

## load the kept art if it was painted from exactly this game; false means paint it afresh
static func load_cache() -> bool:
	if not FileAccess.file_exists(CACHE_DIR + "index.bin"):
		return false
	var f := FileAccess.open(CACHE_DIR + "index.bin", FileAccess.READ)
	if f == null:
		return false
	var meta = f.get_var()
	f.close()
	if not (meta is Dictionary) or String(meta.get("key", "")) != cache_key():
		return false
	var at: Dictionary = _atlases()
	var loaded := {}
	for nm in at.keys():
		var am = meta.get("atlas", {}).get(nm, null)
		var img := Image.load_from_file(CACHE_DIR + nm + ".png")
		if not (am is Dictionary) or img == null or img.is_empty():
			return false
		img.convert(Image.FORMAT_RGBA8)
		loaded[nm] = [am, img]
	for nm in loaded.keys():
		var a: Atlas = at[nm]
		var am2: Dictionary = loaded[nm][0]
		a.images.clear()
		a.rects.assign(am2["rects"])
		a.offs.assign(am2["offs"])
		a.names = am2["names"]
		a.width = int(am2["width"])
		a.height = int(am2["height"])
		a.image = loaded[nm][1]
		a.texture = ImageTexture.create_from_image(a.image)
	ground = meta["ground"]
	wall_spr = meta["wall_spr"]
	obj_spr = meta["obj_spr"]
	ov = meta["ov"]
	item_icon = meta["item_icon"]
	item_icon_rot = meta.get("item_icon_rot", {})
	misc = meta["misc"]
	char_frames = meta["char_frames"]
	ArtIcons.sheet_icons = meta["sheet_icons"]
	return true

## the icon to draw for this item now: the rotten sprite once a perishable has turned
static func icon_of(it: Dictionary, hour: float) -> int:
	var id: String = String(it.get("id", ""))
	if item_icon_rot.has(id) and Items.fresh_state(it, hour) == 2:
		return int(item_icon_rot[id])
	return int(item_icon.get(id, -1))

static func clear_cache() -> void:
	for fn in ["index.bin", "index.tmp", "world.png", "chars.png", "icons.png"]:
		if FileAccess.file_exists(CACHE_DIR + fn):
			DirAccess.remove_absolute(CACHE_DIR + fn)

static func build_all() -> void:
	begin()
	while not ready:
		step(1000.0)
