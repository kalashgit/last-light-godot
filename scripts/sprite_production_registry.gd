extends RefCounted
## Opt-in inventory resolver. Stable IDs come from the existing factory catalog.
## Candidates are accessible only via the explicit review method.
const FACTORY := "res://assets/generated/factory/"
const APPROVED := "res://production/sprite_factory/approved_registry.json"
const REVIEW := "res://production/sprite_factory/batches/LL-ICON-B0003/active.json"
var definitions: Dictionary = {}
var approved: Dictionary = {}
var candidates: Dictionary = {}

func _init() -> void:
 var source: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(FACTORY + "manifest.json"))
 for entry in source.objects:
  definitions[entry.id] = entry
 var registry: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(APPROVED))
 for entry in registry.items:
  if entry.get("status") != "approved_inventory_export" or not entry.has("founder_approval"):
   continue
  if approved.has(entry.logical_item_id):
   # Ambiguous revisions must be selected by an integrator, never last-write-wins.
   approved[entry.logical_item_id] = {}
  else:
   approved[entry.logical_item_id] = entry
 var review: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(REVIEW))
 for entry in review.items:
  candidates[entry.logical_item_id] = entry

func icon_for(id: String) -> Texture2D:
 var entry: Dictionary = approved.get(id, {})
 if not entry.is_empty() and _valid_approved(entry):
  return load("res://" + String(entry.export_path)) as Texture2D
 # Preserve the existing generated placeholder for known catalog objects.
 for frame in definitions.get(id, {}).get("frames", []):
  if frame.mode == "icon":
   return load(FACTORY + String(frame.file)) as Texture2D
 return null

func _valid_approved(entry: Dictionary) -> bool:
 var path := "res://" + String(entry.get("export_path", ""))
 if not path.begins_with("res://assets/last_light/approved/") or not FileAccess.file_exists(path):
  return false
 var visual: Dictionary = entry.get("visual_qa", {})
 if visual.get("result") != "PASS" or not visual.get("critical_defects", []).is_empty():
  return false
 var scores: Dictionary = visual.get("scores", {})
 if scores.size() != 6:
  return false
 for score in scores.values():
  if score < 4:
   return false
 return FileAccess.get_sha256(path) == entry.get("content_sha256", "")

func review_icon_for(id: String) -> Texture2D:
 var entry: Dictionary = candidates.get(id, {})
 if entry.is_empty():
  return null
 var path := "res://" + String(entry.export_path)
 if FileAccess.get_sha256(path) != entry.content_sha256:
  return null
 return load(path) as Texture2D
