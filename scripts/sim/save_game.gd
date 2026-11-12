class_name SaveGame
extends RefCounted
## Save files live in user://saves/<slot>/ :
##   meta.sav            player, clock, settings, explored map   (schema versioned)
##   r_<x>_<y>.sav       chunk records grouped into 32x32-chunk regions
## Only chunks that differ from the deterministic generator output are stored.

const SCHEMA := 3
const REGION_SHIFT := 5

static var _cache: Dictionary = {}      # region key -> Dictionary of chunk records
static var _cache_slot := ""
static var recovered := 0               # files restored from backup this session

static func dir_for(slot: String) -> String:
	return "user://saves/%s" % slot

static func exists(slot: String) -> bool:
	return FileAccess.file_exists(dir_for(slot) + "/meta.sav") or FileAccess.file_exists(dir_for(slot) + "/meta.sav.bak")

static func _region_path(slot: String, rk: Vector2i) -> String:
	return "%s/r_%d_%d.sav" % [dir_for(slot), rk.x, rk.y]

static func _read(path: String) -> Variant:
	if not FileAccess.file_exists(path):
		return null
	var f: FileAccess = FileAccess.open_compressed(path, FileAccess.READ, FileAccess.COMPRESSION_ZSTD)
	if f == null:
		return null
	var v: Variant = f.get_var()
	f.close()
	return v

## read with corruption detection: a file that will not decode falls back to its backup copy
static func _read_safe(path: String) -> Variant:
	var v: Variant = _read(path)
	if v is Dictionary:
		return v
	var b: Variant = _read(path + ".bak")
	if b is Dictionary:
		recovered += 1
		push_warning("LAST LIGHT: %s was unreadable, restored from backup" % path)
		return b
	return v

static func _write(path: String, v: Variant) -> bool:
	var tmp: String = path + ".tmp"
	var f: FileAccess = FileAccess.open_compressed(tmp, FileAccess.WRITE, FileAccess.COMPRESSION_ZSTD)
	if f == null:
		return false
	f.store_var(v)
	f.close()
	var da: DirAccess = DirAccess.open(path.get_base_dir())
	if da == null:
		return false
	# never leave the player without a readable file: verify the new one, keep the old one as .bak
	if not (_read(tmp) is Dictionary):
		da.remove(tmp.get_file())
		return false
	if da.file_exists(path.get_file()):
		if da.file_exists(path.get_file() + ".bak"):
			da.remove(path.get_file() + ".bak")
		da.rename(path.get_file(), path.get_file() + ".bak")
	return da.rename(tmp.get_file(), path.get_file()) == OK

static func _region(slot: String, rk: Vector2i) -> Dictionary:
	if _cache_slot != slot:
		_cache.clear()
		_cache_slot = slot
	if _cache.has(rk):
		return _cache[rk]
	var v: Variant = _read_safe(_region_path(slot, rk))
	var d: Dictionary = v if v is Dictionary else {}
	if _cache.size() > 12:
		_cache.clear()
	_cache[rk] = d
	return d

## chunk record lookup used by World when a chunk streams in
static func loader(slot: String) -> Callable:
	return func(k: Vector2i) -> Dictionary:
		var rk := Vector2i(k.x >> REGION_SHIFT, k.y >> REGION_SHIFT)
		var reg: Dictionary = _region(slot, rk)
		return reg.get(k, {})

static func save(sim: Sim, slot: String) -> bool:
	DirAccess.make_dir_recursive_absolute(dir_for(slot))
	var w: World = sim.world
	# gather chunk records: unloaded-but-touched + currently loaded
	var by_region: Dictionary = {}
	for k in w.store.keys():
		var rk := Vector2i(k.x >> REGION_SHIFT, k.y >> REGION_SHIFT)
		if not by_region.has(rk):
			by_region[rk] = {}
		by_region[rk][k] = w.store[k]
	for k in w.chunks.keys():
		var c: Chunk = w.chunks[k]
		var zs: Array = sim.zombies.serialized_in_chunk(c.cx, c.cy)
		if not (c.touched or c.modified or c.spawned or zs.size() > 0 or sim.npcs.serialized_in_chunk(c.cx, c.cy).size() > 0):
			continue
		var data: Dictionary = c.save_data()
		data["z"] = zs
		data["npc"] = sim.npcs.serialized_in_chunk(c.cx, c.cy)
		data["lh"] = sim.hour
		var rk2 := Vector2i(k.x >> REGION_SHIFT, k.y >> REGION_SHIFT)
		if not by_region.has(rk2):
			by_region[rk2] = {}
		by_region[rk2][k] = data
	var ok := true
	for rk in by_region.keys():
		var reg: Dictionary = _region(slot, rk)
		var add: Dictionary = by_region[rk]
		for k in add.keys():
			reg[k] = add[k]
		if not _write(_region_path(slot, rk), reg):
			ok = false
	if ok:
		w.store.clear()
	if not _write(dir_for(slot) + "/meta.sav", sim.save_meta()):
		ok = false
	return ok

static func load_game(slot: String) -> Sim:
	var v: Variant = _read_safe(dir_for(slot) + "/meta.sav")
	if not (v is Dictionary):
		return null
	var meta: Dictionary = migrate(v)
	if meta.is_empty():
		return null
	_cache.clear()
	_cache_slot = slot
	var sim := Sim.new(int(meta["seed"]))
	sim.world.store_loader = loader(slot)
	sim.load_meta(meta)
	sim.world.stream(sim.player.pos, 2, 999)
	sim._process_world_events()
	return sim

## upgrade older save metadata to the current schema. returns {} if unreadable.
static func migrate(meta: Dictionary) -> Dictionary:
	var v: int = int(meta.get("v", 0))
	if v <= 0 or not meta.has("seed") or not meta.has("player"):
		return {}
	if v == 1:
		# v1 (pre-release) had no persistent alarm list or rng state
		meta["alarms_done"] = meta.get("alarms_done", {})
		meta["v"] = 2
	if int(meta["v"]) == 2:
		# v3 adds traits, body weight, mood, sandbox options, flyover schedule and tutorial state.
		# Every new field has a default on load; old saves simply start without traits or events.
		var st: Dictionary = meta.get("settings", {})
		st["guide"] = false
		st["flyover"] = 0
		meta["settings"] = st
		meta["v"] = 3
	if int(meta["v"]) > SCHEMA:
		return {}
	return meta

static func delete(slot: String) -> void:
	var path: String = dir_for(slot)
	var da: DirAccess = DirAccess.open(path)
	if da == null:
		return
	for f in da.get_files():
		da.remove(f)
	_cache.clear()

static func summary(slot: String) -> String:
	var v: Variant = _read(dir_for(slot) + "/meta.sav")
	if not (v is Dictionary):
		return ""
	var h: float = v.get("hour", 0.0)
	var p: Dictionary = v.get("player", {})
	return "Day %d, %02d:00 — %d kills%s" % [int(h / 24.0) + 1, int(fposmod(h, 24.0)), int(p.get("kills", 0)), " (dead)" if v.get("dead", false) else ""]
