extends SceneTree
func _initialize() -> void:
 var manifest: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://production/sprite_factory/batches/LL-ICON-B0004/active.json"))
 assert(manifest.items.size() == 6)
 for entry in manifest.items:
  var path := "res://" + String(entry.export_path)
  var texture := load(path) as Texture2D
  assert(texture != null and texture.get_size() == Vector2(64,64))
  assert(FileAccess.get_sha256(path) == entry.content_sha256)
 print("B0004 PASS: six candidate textures loaded and hash-verified; no production approval implied")
 quit()
