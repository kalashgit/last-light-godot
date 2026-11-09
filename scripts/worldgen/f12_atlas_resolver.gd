extends RefCounted
## Consumes F12 atlas packages bound by tools/worldgen/asset_intake_v2.py and
## exposes per-placement-type frames for the worldgen renderer.
## Input format = W01's tests/godot_fixture/prepare_fixture.py fixture_manifest.json
## (cases -> atlas, size, frames[heading, rect, ground_pivot_px]). Never renders,
## edits or approves assets. Calibration packages load ONLY in worlds flagged
## isolated_calibration_fixture; production worlds need ledger-gated packages.

var by_type: Dictionary = {}   # placement_type -> {texture, frames: Array[{region, pivot, heading}], package_id, stage}
var errors: PackedStringArray = []
var calibration_loaded := false

func load_intake(intake: Dictionary) -> void:
 by_type.clear(); errors.clear()
 var isolated := bool(intake.get("isolated_calibration_fixture", false))
 for pkg in intake.get("packages", []):
  if pkg.stage == "CALIBRATION" and not isolated:
   errors.append("refused calibration package outside isolated fixture: " + String(pkg.package_id))
   continue
  if FileAccess.get_sha256(pkg.atlas_uri) != pkg.atlas_sha256:
   errors.append("atlas hash mismatch: " + String(pkg.package_id))
   continue
  var meta: Variant = JSON.parse_string(FileAccess.get_file_as_string(pkg.metadata_uri))
  if not meta is Dictionary or not meta.get("cases", {}).has(pkg.subject):
   errors.append("metadata missing subject " + String(pkg.subject))
   continue
  var tile: Array = meta.get("logical_tile_px", [])
  if tile.size() != 2 or int(tile[0]) != 80 or int(tile[1]) != 40:
   errors.append("logical tile is not 80x40 for " + String(pkg.package_id))
   continue
  var case_info: Dictionary = meta.cases[pkg.subject]
  var image := Image.new()
  if image.load(pkg.atlas_uri) != OK or image.get_width() != int(case_info.size[0]) or image.get_height() != int(case_info.size[1]):
   errors.append("atlas load/size failed for " + String(pkg.package_id))
   continue
  var texture := ImageTexture.create_from_image(image)
  var frames: Array = []
  for entry in case_info.frames:
   var r: Array = entry.rect
   var region := Rect2(r[0], r[1], r[2], r[3])
   if region.end.x > image.get_width() or region.end.y > image.get_height():
    errors.append("region outside atlas for " + String(pkg.package_id))
    frames.clear()
    break
   frames.append({"region": region, "pivot": Vector2(entry.ground_pivot_px[0], entry.ground_pivot_px[1]),
    "heading": int(entry.heading), "source_frame": int(entry.get("source_frame", 1))})
  if frames.is_empty(): continue
  for t in pkg.placement_types:
   by_type[t] = {"texture": texture, "frames": frames, "package_id": pkg.package_id, "stage": pkg.stage}
  if pkg.stage == "CALIBRATION": calibration_loaded = true

func has_type(placement_type: String) -> bool:
 return by_type.has(placement_type)

## First frame for a heading (F12 heading semantics are owned by F12; worldgen
## passes 0 until the F12 production manifest publishes the heading convention).
func frame(placement_type: String, heading: int = 0) -> Dictionary:
 var entry: Dictionary = by_type[placement_type]
 for f in entry.frames:
  if f.heading == heading: return f
 return entry.frames[0]
