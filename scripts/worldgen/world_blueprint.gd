extends RefCounted
## Loads an exported LAST LIGHT world (tools/llworld.py) for the runtime.
## The first load copies the blueprint into user:// and every later load reads
## that frozen copy, so a visited world is never regenerated or rerolled even
## if the generator or the res:// export changes. Every file is SHA-256 checked.

const MANIFEST_SCHEMA := "last_light.worldgen.world_manifest.v1"
const FROZEN_ROOT := "user://worldgen/"

var source_dir := ""
var frozen_dir := ""
var manifest: Dictionary = {}
var district: Dictionary = {}
var buildings: Array = []
var terrain := PackedByteArray()  # one ASCII terrain code per cell, row-major
var terrain_codes: Dictionary = {}
var bounds := Rect2i()
var error := ""
var newer_blueprint_available := false

func world_slug() -> String:
 return String(manifest.get("world_id", "unknown")).replace(".", "_")

func load_world(dir: String) -> bool:
 source_dir = dir.trim_suffix("/") + "/"
 var source_manifest := _read_json(source_dir + "world_manifest.json")
 if source_manifest.is_empty() or source_manifest.get("schema") != MANIFEST_SCHEMA:
  error = "Missing or invalid world manifest at " + source_dir
  return false
 frozen_dir = FROZEN_ROOT + String(source_manifest.world_id).replace(".", "_") + "/blueprint/"
 var frozen_manifest := _read_json(frozen_dir + "world_manifest.json")
 if frozen_manifest.is_empty():
  if not _freeze(source_manifest):
   return false
  frozen_manifest = _read_json(frozen_dir + "world_manifest.json")
 elif frozen_manifest.get("blueprint_sha256") != source_manifest.get("blueprint_sha256"):
  # Keep the world the player already visited. A different export is reported, never applied.
  newer_blueprint_available = true
 manifest = frozen_manifest
 return _load_from(frozen_dir)

func _files(m: Dictionary) -> Array:
 var out: Array = [m.district.file, m.region.file]
 for entry in m.chunks: out.append(entry.file)
 for entry in m.buildings: out.append(entry.file)
 return out

func _freeze(m: Dictionary) -> bool:
 for rel in _files(m):
  var target: String = frozen_dir + rel
  DirAccess.make_dir_recursive_absolute(target.get_base_dir())
  if DirAccess.copy_absolute(source_dir + rel, target) != OK:
   error = "Could not freeze blueprint file " + rel
   return false
 # Manifest last: a partially copied blueprint is never treated as complete.
 if DirAccess.copy_absolute(source_dir + "world_manifest.json", frozen_dir + "world_manifest.json") != OK:
  error = "Could not freeze world manifest"
  return false
 return true

func _verify(dir: String, rel: String, expected: String) -> bool:
 var actual := FileAccess.get_sha256(dir + rel)
 if actual != expected:
  error = "Blueprint file failed integrity check: " + rel
  return false
 return true

func _load_from(dir: String) -> bool:
 if not _verify(dir, manifest.district.file, manifest.district.sha256): return false
 district = _read_json(dir + manifest.district.file)
 var b: Array = manifest.bounds
 bounds = Rect2i(int(b[0]), int(b[1]), int(b[2]), int(b[3]))
 terrain.resize(bounds.size.x * bounds.size.y)
 terrain.fill(103) # 'g'
 for entry in manifest.chunks:
  if not _verify(dir, entry.file, entry.sha256): return false
  var chunk := _read_json(dir + entry.file)
  terrain_codes = chunk.terrain_codes
  var r: Array = chunk.rect
  for dy in range(chunk.terrain_rows.size()):
   var row: String = chunk.terrain_rows[dy]
   for dx in range(row.length()):
    terrain[(int(r[1]) + dy) * bounds.size.x + int(r[0]) + dx] = row.unicode_at(dx)
 buildings.clear()
 for entry in manifest.buildings:
  if not _verify(dir, entry.file, entry.sha256): return false
  buildings.append(_read_json(dir + entry.file))
 return true

func terrain_at(x: int, y: int) -> String:
 if x < 0 or y < 0 or x >= bounds.size.x or y >= bounds.size.y: return "grass"
 return String(terrain_codes.get(char(terrain[y * bounds.size.x + x]), "grass"))

static func _read_json(path: String) -> Dictionary:
 if not FileAccess.file_exists(path): return {}
 var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(path))
 return parsed if parsed is Dictionary else {}
