extends "res://scripts/house.gd"
## Worker 04 integration adapter: plays a generated world through the existing
## survival game (movement, doors, combat, zombies, loot, HUD, inventory, saves).
## Shared gameplay code is NOT modified; this subclass only replaces world
## construction, bounds, spatial lookup, camera framing, container loot and the
## save location/identity. Upper floors are generated and validated offline but
## are not traversable in this single-plane runtime yet (stairs render as solid).

const WorldBlueprint := preload("res://scripts/worldgen/world_blueprint.gd")
const WorldgenArt := preload("res://scripts/worldgen/worldgen_art.gd")
const WorldgenNavigation := preload("res://scripts/worldgen/worldgen_navigation.gd")
const F12AtlasResolver := preload("res://scripts/worldgen/f12_atlas_resolver.gd")
const BUCKET := 4.0
const MAX_INFECTED := 6

@export_dir var world_dir := "res://data/worldgen/generated/w04_demo_suburb"
@export var infected_count := 6

var blueprint := WorldBlueprint.new()
var v2_sprites := F12AtlasResolver.new()
var world_rect := Rect2()
var spawn_point := Vector2.ZERO
var rooms: Array[Dictionary] = []        # ground-floor rooms: id, type, rect, building
var room_lookup: Dictionary = {}         # Vector2i -> rooms index
var building_meta: Array[Dictionary] = []
var current_building := -1
var wall_buckets: Dictionary = {}
var item_buckets: Dictionary = {}
var door_buckets: Dictionary = {}
var world_save_path := ""
var identity_path := ""
var load_error := ""
var suppress_save := false

func _ready() -> void:
 if not blueprint.load_world(world_dir):
  load_error = blueprint.error
  push_error("WORLDGEN: " + load_error)
 world_rect = Rect2(blueprint.bounds)
 var base := "user://worldgen/" + blueprint.world_slug() + "/"
 DirAccess.make_dir_recursive_absolute(base)
 world_save_path = base + "save_v2.json"
 identity_path = base + "identity.json"
 art = WorldgenArt.new()
 navigation = WorldgenNavigation.new()
 v2_sprites.load_intake(blueprint.manifest.get("asset_intake", {}))
 for e in v2_sprites.errors: push_warning("WORLDGEN V2: " + e)
 super._ready()
 if blueprint.newer_blueprint_available:
  _announce("Your saved neighborhood is kept; a newer generated layout was not applied")
 elif not load_error.is_empty():
  _announce("World data could not load — see log")

# ------------------------------------------------------------------ world build
func _vec(a: Array) -> Vector2:
 return Vector2(float(a[0]), float(a[1]))

func _label_for(door: Dictionary, room_types: Dictionary) -> String:
 var kind := String(door.kind)
 if kind == "garage": return "GARAGE"
 var other := ""
 for rid in door.connects:
  if rid != "exterior" and room_types.get(rid, "hall") not in ["hall", "corridor", "landing", "front"]:
   other = String(room_types[rid]).to_upper()
 if "exterior" in door.connects:
  return "FRONT" if String(door.get("world_side", "")) == String(door.get("_front", "")) else "SIDE"
 return other if not other.is_empty() else "HALL"

func _make_house() -> void:
 walls.clear(); doors.clear(); items.clear()
 rooms.clear(); room_lookup.clear(); building_meta.clear()
 var containers: Array[Dictionary] = []
 var fixtures: Array[Dictionary] = []
 for bi in range(blueprint.buildings.size()):
  var b: Dictionary = blueprint.buildings[bi]
  var f0: Dictionary = b.floors[0]
  var footprint: Array[Rect2] = []
  for r in b.footprint: footprint.append(Rect2(r[0], r[1], r[2], r[3]))
  var room_types := {}
  for room in f0.rooms:
   room_types[room.id] = room.type
   var rect := Rect2(room.rect[0], room.rect[1], room.rect[2], room.rect[3])
   rooms.append({"id": room.id, "type": room.type, "rect": rect, "building": bi, "floor_material": room.get("floor_material", "wood_oak")})
   for y in range(int(rect.position.y), int(rect.end.y)):
    for x in range(int(rect.position.x), int(rect.end.x)):
     room_lookup[Vector2i(x, y)] = rooms.size() - 1
  for w in f0.walls:
   var a := _vec(w.a); var c := _vec(w.b)
   walls.append({"a": a, "b": c, "exterior": w.exterior, "building": bi, "near": _near_side(a, c, footprint), "kind": "wall"})
  var front := String(b.get("frame", {}).get("front", "south"))
  for d in f0.doors:
   if d.kind == "opening": continue
   var dd: Dictionary = d.duplicate()
   dd["_front"] = front
   doors.append({"a": _vec(d.a), "b": _vec(d.b), "label": _label_for(dd, room_types), "open": false,
    "health": 45.0, "id": d.id, "kind": d.kind, "building": bi})
  for item in f0.furniture:
   var entry := _item(item, bi)
   (containers if entry.container else fixtures).append(entry)
  var stairs: Array[Rect2] = []
  for s in b.get("stairs", []):
   var sr := Rect2(s.rect[0], s.rect[1], s.rect[2], s.rect[3])
   stairs.append(sr)
   fixtures.append({"id": s.id, "name": "STAIRS (upper floor not yet traversable)", "pos": sr.position + Vector2(.05, .05),
    "size": sr.size - Vector2(.1, .1), "container": false, "searched": true, "asset_id": "", "kind": "stairs", "building": bi})
  building_meta.append({"id": b.id, "footprint": footprint, "roof": b.roof, "materials": b.materials, "condition": b.condition,
   "windows": f0.windows, "stairs": stairs, "program": b.program, "template": b.template,
   "floors": b.floors.size(), "name": b.get("name", String(b.program).replace("_", " ").to_upper())})
 for prop in blueprint.district.get("props", []):
  var entry := _item(prop, -1)
  (containers if entry.container else fixtures).append(entry)
 for f in blueprint.district.get("fences", []):
  walls.append({"a": _vec(f.a), "b": _vec(f.b), "exterior": true, "building": -1, "near": false, "kind": "fence"})
 # Saves index the first four items as legacy flags; keep containers first and stable.
 containers.sort_custom(func(a, b): return String(a.id) < String(b.id))
 items.assign(containers + fixtures)
 _index()
 spawn_point = _vec(blueprint.district.get("spawn", [world_rect.size.x * .5, world_rect.size.y * .5]))
 player = spawn_point
 _spawn_infected()
 navigation.rebuild(self)

func _item(src: Dictionary, building: int) -> Dictionary:
 var s: Array = src.solid_rect
 var entry := {"id": src.id, "name": String(src.label), "pos": Vector2(s[0], s[1]), "size": Vector2(s[2], s[3]),
  "container": bool(src.container), "searched": not bool(src.container), "asset_id": src.asset_id if src.asset_id != null else "",
  "kind": src.type, "art": src.get("art", "factory_sprite"), "height_m": float(src.get("height_m", 1.0)),
  "loot": src.get("initial_contents", {}), "building": building, "tint": Color("777164")}
 if not String(entry.asset_id).is_empty(): art._cache(entry.asset_id)
 return entry

func _near_side(a: Vector2, b: Vector2, footprint: Array[Rect2]) -> bool:
 # Camera looks from +x/+y: walls whose outside faces +x or +y hide the interior.
 var mid := (a + b) * .5
 var probe := mid + (Vector2(-.5, 0) if absf(a.x - b.x) < .01 else Vector2(0, -.5))
 for r in footprint:
  if r.has_point(probe): return true
 return false

func _spawn_infected() -> void:
 infected.clear(); zombie_health.clear(); zombies_hit_time.clear()
 var points: Array = blueprint.district.get("spawn_points", [])
 for i in range(mini(mini(infected_count, MAX_INFECTED), points.size())):
  infected.append(_vec(points[i].pos))
  zombie_health.append(3)
  zombies_hit_time.append(0.0)

func _bucket_keys(r: Rect2) -> Array[Vector2i]:
 var out: Array[Vector2i] = []
 for y in range(floori(r.position.y / BUCKET), floori(r.end.y / BUCKET) + 1):
  for x in range(floori(r.position.x / BUCKET), floori(r.end.x / BUCKET) + 1):
   out.append(Vector2i(x, y))
 return out

func _seg_rect(a: Vector2, b: Vector2) -> Rect2:
 return Rect2(a, Vector2.ZERO).expand(b).grow(.6)

func _index() -> void:
 wall_buckets.clear(); item_buckets.clear(); door_buckets.clear()
 for i in range(walls.size()):
  for k in _bucket_keys(_seg_rect(walls[i].a, walls[i].b)): wall_buckets.get_or_add(k, []).append(i)
 for i in range(items.size()):
  for k in _bucket_keys(Rect2(items[i].pos, items[i].size).grow(.6)): item_buckets.get_or_add(k, []).append(i)
 for i in range(doors.size()):
  for k in _bucket_keys(_seg_rect(doors[i].a, doors[i].b)): door_buckets.get_or_add(k, []).append(i)

func _near(buckets: Dictionary, r: Rect2) -> Array:
 var seen := {}
 for k in _bucket_keys(r):
  for i in buckets.get(k, []): seen[i] = true
 return seen.keys()

# ------------------------------------------------------------------ collision
func _blocked_static(p: Vector2, radius: float = PLAYER_RADIUS) -> bool:
 if not world_rect.grow(-radius).has_point(p): return true
 var probe := Rect2(p, Vector2.ZERO).grow(radius + .1)
 for i in _near(wall_buckets, probe):
  if _segment_distance(p, walls[i].a, walls[i].b) < radius + .09: return true
 for i in _near(item_buckets, probe):
  if items[i].get("solid", true) and Rect2(items[i].pos, items[i].size).grow(radius).has_point(p): return true
 return false

func _blocked(p: Vector2, radius: float = PLAYER_RADIUS) -> bool:
 if _blocked_static(p, radius): return true
 for i in _near(door_buckets, Rect2(p, Vector2.ZERO).grow(radius + .1)):
  if not doors[i].open and _segment_distance(p, doors[i].a, doors[i].b) < radius + .09: return true
 return false

func _line_blocked(a: Vector2, b: Vector2, furniture: bool = true) -> bool:
 var r := _seg_rect(a, b)
 for i in _near(wall_buckets, r):
  if Geometry2D.segment_intersects_segment(a, b, walls[i].a, walls[i].b) != null: return true
 for i in _near(door_buckets, r):
  if not doors[i].open and Geometry2D.segment_intersects_segment(a, b, doors[i].a, doors[i].b) != null: return true
 if furniture:
  for i in _near(item_buckets, r):
   var rect := Rect2(items[i].pos, items[i].size)
   if rect.has_point(a) or rect.has_point(b): return true
   var c: Array[Vector2] = [rect.position, Vector2(rect.end.x, rect.position.y), rect.end, Vector2(rect.position.x, rect.end.y)]
   for k in range(4):
    if Geometry2D.segment_intersects_segment(a, b, c[k], c[(k + 1) % 4]) != null: return true
 return false

func _clear_saved_position(position: Vector2) -> Vector2:
 var center := position.clamp(world_rect.position + Vector2.ONE, world_rect.end - Vector2.ONE)
 for radius in range(15):
  for y in range(-radius, radius + 1):
   for x in range(-radius, radius + 1):
    var candidate := center + Vector2(x, y) * .25
    if not _blocked(candidate): return candidate
 return spawn_point

# ------------------------------------------------------------------ camera
func building_at(p: Vector2) -> int:
 var index: int = room_lookup.get(Vector2i(floori(p.x), floori(p.y)), -1)
 return -1 if index < 0 else int(rooms[index].building)

func room_at(p: Vector2) -> Dictionary:
 var index: int = room_lookup.get(Vector2i(floori(p.x), floori(p.y)), -1)
 return {} if index < 0 else rooms[index]

func _process(delta: float) -> void:
 current_building = building_at(player)
 var desired_zoom := INDOOR_ZOOM if current_building >= 0 else 1.0
 camera_zoom = lerpf(camera_zoom, desired_zoom, 1.0 - exp(-CAMERA_RESPONSE * clampf(delta, 0.0, 0.25)))
 if paused or inventory_open or health <= 0:
  queue_redraw()
  return
 var total := clampf(delta, 0, .25)
 var steps := maxi(1, ceili(total / (1.0 / 60.0)))
 for step in range(steps):
  _step(total / steps)
  if health <= 0: break
 queue_redraw()

func _camera_center() -> Vector2:
 return get_viewport_rect().size * Vector2(.50, .58 if current_building >= 0 else .62)

# ------------------------------------------------------------------ loot
func _interact() -> void:
 if health <= 0 or paused: return
 var target := _resolve_target()
 if target.is_empty() or target.kind != "container":
  super._interact()
  return
 var item: Dictionary = items[target.index]
 var previous := survival.snapshot()
 for id in item.loot:
  if not survival.definitions.has(id): continue
  if not survival.add(id, int(item.loot[id])):
   survival.restore(previous)
   _announce("Make room in your pack before searching")
   return
 item.searched = true
 supplies += 1
 _announce(("Searched " if item.loot.is_empty() else "Collected supplies from ") + String(item.name).capitalize() + ("" if not item.loot.is_empty() else " — empty"))
 selected_target = {}
 _save_game()

# ------------------------------------------------------------------ saves
func _restart_game() -> void:
 # The base restart moves SAVE_PATH aside when blocked; do that for the world save
 # instead so the single-house game's save is never touched from here.
 if save_blocked and FileAccess.file_exists(world_save_path):
  if DirAccess.copy_absolute(world_save_path, world_save_path + ".rejected.bak") != OK:
   _announce("Could not preserve old save; restart cancelled")
   return
  if DirAccess.remove_absolute(world_save_path) != OK: return
 save_blocked = false
 # The base restart saves its own two hard-coded infected; that intermediate save
 # would make every later save fail the enemy-count protection, so skip it.
 suppress_save = true
 super._restart_game()
 suppress_save = false
 player = spawn_point
 _spawn_infected()
 _save_game()

func _recover_backup() -> bool:
 var bak := world_save_path + ".bak"
 if not recovery_available or _load_game(bak, true) != OK: return false
 if FileAccess.file_exists(world_save_path) and DirAccess.copy_absolute(world_save_path, world_save_path + ".rejected.bak") != OK: return false
 if DirAccess.copy_absolute(bak, world_save_path) != OK: return false
 if _load_game() != OK: return false
 save_blocked = false
 recovery_available = false
 _set_paused(false)
 _announce("Backup restored; original retained as rejected backup")
 return true

func _save_game(path: String = SAVE_PATH) -> Error:
 if suppress_save: return OK
 var target := _map_path(path)
 if target.is_empty(): return ERR_FILE_NOT_FOUND
 if save_blocked and target == world_save_path:
  last_save_error = ERR_INVALID_DATA
  return last_save_error
 var result: Error = super._save_game(target)
 if result == OK and target == world_save_path: _write_identity()
 return result

func _load_game(path: String = SAVE_PATH, validate_only: bool = false) -> Error:
 var target := _map_path(path)
 if target.is_empty(): return ERR_FILE_NOT_FOUND
 if target == world_save_path and FileAccess.file_exists(target) and not _identity_matches():
  return ERR_INVALID_DATA
 return super._load_game(target, validate_only)

func _map_path(path: String) -> String:
 # Never read or write the single-house game's saves from the generated world.
 if path == LEGACY_SAVE_PATH: return ""
 if path.begins_with(SAVE_PATH): return world_save_path + path.trim_prefix(SAVE_PATH)
 return path

func _identity() -> Dictionary:
 var door_ids: Array = []
 var door_delta := {}
 for d in doors:
  door_ids.append(d.id)
  door_delta[d.id] = {"open": d.open, "health": d.health}
 var container_delta := {}
 for item in items:
  if item.container: container_delta[item.id] = item.searched
 return {"schema": "last_light.worldgen.save_identity.v1", "world_id": blueprint.manifest.get("world_id", ""),
  "generator_version": blueprint.manifest.get("generator_version", ""), "world_seed": blueprint.manifest.get("world_seed", 0),
  "blueprint_sha256": blueprint.manifest.get("blueprint_sha256", ""), "door_ids": door_ids,
  "delta": {"doors": door_delta, "containers": container_delta}}

func _write_identity() -> void:
 var f := FileAccess.open(identity_path + ".tmp", FileAccess.WRITE)
 if f == null: return
 f.store_string(JSON.stringify(_identity()))
 f.close()
 DirAccess.rename_absolute(identity_path + ".tmp", identity_path)

func _identity_matches() -> bool:
 if not FileAccess.file_exists(identity_path): return true
 var saved: Variant = JSON.parse_string(FileAccess.get_file_as_string(identity_path))
 if not saved is Dictionary: return false
 var now := _identity()
 return saved.get("world_id") == now.world_id and saved.get("blueprint_sha256") == now.blueprint_sha256 and saved.get("door_ids") == now.door_ids
