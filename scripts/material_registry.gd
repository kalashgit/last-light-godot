extends RefCounted
## Offline, cached visual definitions. IDs never encode door/loot/save state.
const PATH := "res://assets/materials/runtime_materials_v1.json"
static var _entries: Dictionary = {}
static var _assets: Dictionary = {}
static var _colors: Dictionary = {}
static var _regions: Dictionary = {}
static var _loaded := false

static func validate(payload: Variant) -> PackedStringArray:
 var errors := PackedStringArray()
 if not payload is Dictionary:
  errors.append("registry must be a dictionary")
  return errors
 if payload.get("schema_version") != 1:
  errors.append("unsupported material schema")
 if not payload.get("materials") is Array or not payload.get("assets") is Dictionary:
  errors.append("materials/assets collections missing")
  return errors
 var ids: Dictionary = {}
 for entry in payload.materials:
  if not entry is Dictionary:
   errors.append("invalid material entry")
   continue
  var id := String(entry.get("id",""))
  if id.is_empty() or ids.has(id): errors.append("empty or duplicate material ID: "+id)
  ids[id]=true
  if not entry.get("surfaces") is Array or entry.get("surfaces",[]).is_empty():
   errors.append("missing surfaces: "+id)
  if not entry.get("palette") is Dictionary or not Color.html_is_valid(String(entry.get("palette",{}).get("base",""))):
   errors.append("invalid palette: "+id)
  if entry.get("surfaces") is Array:
   for surface in entry.surfaces:
    if not surface in ["floor","wall","roof"]: errors.append("invalid surface: "+id)
  if entry.get("tile_px")!=[80.0,40.0] or entry.get("world_cell_m")!=1:
   errors.append("invalid scale: "+id)
  var asset: Variant=entry.get("asset_id")
  if asset!=null and not payload.assets.has(asset): errors.append("missing asset: "+id)
 for asset in payload.assets.values():
  if not asset is Dictionary or not ResourceLoader.exists(String(asset.get("path",""))):
   errors.append("missing packaged resource")
 return errors

static func _ensure_loaded() -> void:
 if _loaded: return
 _loaded=true
 var payload: Variant=JSON.parse_string(FileAccess.get_file_as_string(PATH))
 var errors:=validate(payload)
 if not errors.is_empty():
  push_error("Material registry rejected: "+str(errors))
  return
 _assets=payload.assets
 for entry in payload.materials:
  var id:=String(entry.id)
  _entries[id]=entry
  _colors[id]=Color(String(entry.palette.base))
  var region: Variant=entry.get("atlas_region_px")
  if region is Array and region.size()==4:
   _regions[id]=Rect2(region[0],region[1],region[2],region[3])

static func color(id: String, surface: String) -> Color:
 _ensure_loaded()
 if not _entries.has(id) or not surface in _entries[id].surfaces:
  push_error("Unknown/incompatible material: "+id+" / "+surface)
  return Color.MAGENTA
 return _colors[id]

static func atlas_region(id: String) -> Rect2:
 _ensure_loaded()
 return _regions.get(id,Rect2())

static func definition(id: String) -> Dictionary:
 _ensure_loaded()
 # Callers may edit a candidate visual without mutating shared definitions.
 return _entries.get(id,{}).duplicate(true)
