extends RefCounted
## LL-103: atomic schema-1 catalog loading; no autoload, gameplay or save coupling.
const Instance := preload("res://src/content/content_instance.gd")
const CONTRACT_PATH := "res://data/catalog/contracts_v1.json"
const CATALOG_PATH := "res://data/catalog/starter_v1.json"
const VISUALS_PATH := "res://data/catalog/visuals_v1.json"
var errors: Array[String] = []
var _definitions: Dictionary = {}
var _assets: Dictionary = {}
var _sections: Dictionary = {}
var _overrides: Dictionary = {}
var _rules: Dictionary = {}

func _json(path: String) -> Variant:
 if not FileAccess.file_exists(path):
  errors.append("Missing JSON: " + path)
  return null
 var file := FileAccess.open(path, FileAccess.READ)
 if file == null or file.get_length() > 2097152:
  errors.append("Unreadable/oversized JSON: " + path)
  return null
 var parser := JSON.new()
 if parser.parse(file.get_as_text()) != OK:
  errors.append("Malformed JSON: " + path)
  return null
 return parser.data
func load_catalog(path: String = CATALOG_PATH, visuals_path: String = VISUALS_PATH) -> bool:
 errors.clear()
 var data: Variant = _json(path)
 var visuals: Variant = _json(visuals_path)
 var contract: Variant = _json(CONTRACT_PATH)
 if not errors.is_empty():
  return false
 return load_data(data, visuals, contract)
func _text(value: Variant) -> bool:
 return value is String and not value.strip_edges().is_empty()
func _number(value: Variant) -> bool:
 return (value is int or value is float) and is_finite(float(value))
func _strings(value: Variant) -> bool:
 if not value is Array:
  return false
 var seen := {}
 for entry in value:
  if not _text(entry) or seen.has(entry):
   return false
  seen[entry] = true
 return true
func _schema(value: Variant) -> bool:
 # JSON numbers are floats in Godot; booleans are deliberately not accepted.
 return value is Dictionary and _number(value.get("schema")) and value.schema == 1
func load_data(data: Variant, visuals: Variant, contract: Variant = null) -> bool:
 errors.clear()
 if contract == null:
  contract = _json(CONTRACT_PATH)
 if not _schema(contract) or not contract.get("sections") is Dictionary or not contract.get("capabilities") is Dictionary:
  errors.append("Invalid frozen content contract")
  return false
 if not _schema(visuals) or not visuals.get("assets") is Dictionary:
  errors.append("Invalid visual manifest")
  return false
 var assets: Dictionary = visuals.assets
 var asset_pattern := RegEx.create_from_string("^asset[.][a-z][a-z0-9_]*(?:[.][a-z][a-z0-9_]*)*$")
 for id in assets:
  var asset: Variant = assets[id]
  if not id is String or asset_pattern.search(id) == null or not asset is Dictionary:
   errors.append("Invalid asset record")
   continue
  var path: Variant = asset.get("path")
  if not _text(path) or not path.begins_with("res://") or ".." in path.split("/") or not ResourceLoader.exists(path, "Texture2D"):
   errors.append("Missing asset file: " + str(id))
  var size: Variant = asset.get("size_px")
  var anchor: Variant = asset.get("anchor_px")
  if not size is Array or size.size() != 2 or not _number(size[0]) or not _number(size[1]) or size[0] < 1 or size[1] < 1 or size[0] > 2048 or size[1] > 2048 or floorf(size[0]) != size[0] or floorf(size[1]) != size[1]:
   errors.append("Invalid asset dimensions: " + str(id))
  if not anchor is Array or anchor.size() != 2 or not _number(anchor[0]) or not _number(anchor[1]):
   errors.append("Invalid anchor: " + str(id))
  if not _text(asset.get("source")) or not _text(asset.get("license")):
   errors.append("Asset provenance missing: " + str(id))
 if not _schema(data):
  errors.append("Catalog schema must equal 1")
  return false
 var vocabulary: Variant = data.get("capability_vocabulary")
 if not _strings(vocabulary) or vocabulary.size() != contract.capabilities.size():
  errors.append("Invalid capability vocabulary")
 elif vocabulary.any(func(c: String) -> bool: return not contract.capabilities.has(c)):
  errors.append("Unknown vocabulary capability")
 var definitions := {}
 var sections := {}
 var pattern := RegEx.create_from_string("^(item|prop|building|vehicle|entity|loot)[.][a-z][a-z0-9_]*(?:[.][a-z][a-z0-9_]*)*$")
 for section in contract.sections:
  var records: Variant = data.get(section)
  if not records is Array:
   errors.append(section + ": expected array")
   continue
  for record in records:
   if not record is Dictionary:
    errors.append(section + ": expected object")
    continue
   var id: Variant = record.get("id")
   if not _text(id) or pattern.search(id) == null or not id.begins_with(contract.sections[section]):
    errors.append(section + ": bad id")
    continue
   if definitions.has(id):
    errors.append("Duplicate id: " + id)
   definitions[id] = record
   sections[id] = section
   if section != "loot_profiles" and not _text(record.get("name")):
    errors.append(id + ": name required")
   if section in ["items", "props", "vehicles"]:
    var caps: Variant = record.get("capabilities")
    if not _strings(caps):
     errors.append(id + ": invalid capabilities")
    else:
     for capability in caps:
      if not contract.capabilities.has(capability):
       errors.append(id + ": unknown capability")
   var refs: Array = []
   if section == "items":
    if not _text(record.get("category")):
     errors.append(id + ": category required")
    if not _number(record.get("weight_kg")) or record.weight_kg < 0:
     errors.append(id + ": invalid weight")
    if not _number(record.get("stack_max")) or record.stack_max < 1 or floorf(record.stack_max) != record.stack_max:
     errors.append(id + ": invalid stack limit")
    var visual: Variant = record.get("visual")
    if not visual is Dictionary:
     errors.append(id + ": icon/ground refs required")
    else:
     refs = [visual.get("icon"), visual.get("ground")]
   elif section in ["props", "vehicles", "enemies"]:
    refs = [record.get("visual")]
   for ref in refs:
    if not _text(ref) or not assets.has(ref):
     errors.append(id + ": unknown visual asset")
   if section == "enemies" and not _text(record.get("behavior")):
    errors.append(id + ": behavior required")
 for id in definitions:
  var record: Dictionary = definitions[id]
  if sections[id] == "buildings":
   var profile: Variant = record.get("loot_profile")
   if not _text(profile) or sections.get(profile) != "loot_profiles":
    errors.append(id + ": unknown loot_profile")
   if not _strings(record.get("rooms")) or record.rooms.is_empty():
    errors.append(id + ": rooms missing")
   _references(record.get("starter_props"), "props", sections, id)
  elif sections[id] == "loot_profiles":
   _references(record.get("entries"), "items", sections, id)
 if not errors.is_empty():
  return false
 # Commit together; rejected loads preserve the last known-good catalog/overrides.
 _definitions = definitions.duplicate(true)
 _sections = sections.duplicate(true)
 _assets = assets.duplicate(true)
 _rules = contract.capabilities.duplicate(true)
 _overrides.clear()
 return true
func _references(values: Variant, target: String, sections: Dictionary, id: String) -> void:
 if not _strings(values):
  errors.append(id + ": invalid reference array")
  return
 for value in values:
  if sections.get(value) != target:
   errors.append(id + ": missing/wrong-kind reference " + value)
func ids() -> Array:
 return _definitions.keys()
func definition(id: String) -> Dictionary:
 return _definitions.get(id, {}).duplicate(true)
func category(id: String) -> String:
 var record := definition(id)
 return record.get("category", id.get_slice(".", 1)) if not record.is_empty() else ""
func interaction_verbs(id: String) -> Array[String]:
 var verbs: Array[String] = []
 if not _definitions.has(id):
  return verbs
 verbs.append("inspect")
 for capability in _definitions[id].get("capabilities", []):
  for verb in _rules[capability]:
   if not verbs.has(verb):
    verbs.append(verb)
 return verbs
func visual(id: String, view: String = "icon") -> Dictionary:
 if not _definitions.has(id) or view not in ["icon", "ground"]:
  return {}
 var raw: Variant = _definitions[id].get("visual")
 var ref: String = raw.get(view, "") if raw is Dictionary else str(raw)
 ref = _overrides.get(id + "/" + view, ref)
 return _assets.get(ref, {}).duplicate(true)
func replace_visual(id: String, view: String, asset_id: String) -> bool:
 if visual(id, view).is_empty() or not _assets.has(asset_id):
  return false
 _overrides[id + "/" + view] = asset_id
 return true
func create_instance(id: String, instance_id: String, count: Variant = 1):
 return restore_instance({"definition_id": id, "instance_id": instance_id, "count": count, "condition": 1.0, "flags": _default_flags(id)})
func _default_flags(id: String) -> Dictionary:
 var flags := {}
 var caps: Array = _definitions.get(id, {}).get("capabilities", [])
 if "openable" in caps:
  flags.open = false
 if "power_consumer" in caps or "power_source" in caps:
  flags.powered = false
 if "light_source" in caps:
  flags.lit = false
 if "sound_source" in caps:
  flags.active = false
 return flags
func restore_instance(state: Variant):
 if not state is Dictionary or not _text(state.get("definition_id")):
  return null
 var id: String = state.definition_id
 if _sections.get(id) not in ["items", "props", "vehicles", "enemies"] or not _text(state.get("instance_id")):
  return null
 if not _number(state.get("count")) or state.count < 1 or floorf(state.count) != state.count or state.count > _definitions[id].get("stack_max", 1):
  return null
 if not _number(state.get("condition")) or state.condition < 0 or state.condition > 1:
  return null
 if not state.get("flags") is Dictionary:
  return null
 var defaults := _default_flags(id)
 for key in state.flags:
  if not defaults.has(key) or not state.flags[key] is bool:
   return null
 if state.keys().any(func(key: Variant) -> bool: return key not in ["instance_id", "definition_id", "count", "condition", "flags"]):
  return null
 defaults.merge(state.flags, true)
 return Instance.new(_definitions[id], {"definition_id": id, "instance_id": state.instance_id, "count": int(state.count), "condition": float(state.condition), "flags": defaults})
