extends SceneTree
func _initialize() -> void:
 var root_path := "res://production/sprite_factory_v4/hybrid24/"
 var file := FileAccess.open(root_path+"manifest.jsonl",FileAccess.READ)
 assert(file != null)
 var count := 0
 var seen: Dictionary = {}
 while not file.eof_reached():
  var line := file.get_line()
  if line.is_empty():
   continue
  var row: Dictionary = JSON.parse_string(line)
  assert(not seen.has(row.logical_item_id))
  seen[row.logical_item_id] = true
  var path: String = root_path + row.relative_path
  var texture := load(path) as Texture2D
  assert(texture != null and texture.get_size() == Vector2(64,64))
  assert(FileAccess.get_sha256(path) == row.sha256)
  assert(row.founder_approved == false)
  assert(row.view == "inventory_icon")
  count += 1
 file.close()
 assert(count == 24)
 var project_text := FileAccess.get_file_as_string("res://project.godot")
 assert(project_text.contains('run/main_scene="res://main.tscn"'))
 print("V4 GODOT PASS: 24 original draft textures, dimensions, paths, identities and hashes; no approval or world/held view implied")
 quit()
