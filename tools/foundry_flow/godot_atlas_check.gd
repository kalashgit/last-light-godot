extends SceneTree

# Godot 4 headless runtime contract: actually load the exported PNG pages,
# instantiate AtlasTexture regions, and attach directional Sprite2D nodes.
# This cannot certify iPhone FPS, depth sorting or a finished gameplay scene.

func _fail(message: String) -> void:
	printerr("FOUNDRY_GODOT_ATLAS_FAIL: " + message)
	quit(2)


func _initialize() -> void:
	call_deferred("_execute")


func _execute() -> void:
	var args: PackedStringArray = OS.get_cmdline_user_args()
	if args.size() != 4 or args[0] != "--manifest" or args[2] != "--report":
		_fail("Expected --manifest path --report path")
		return
	var manifest_path: String = args[1]
	var report_path: String = args[3]
	var json_text := FileAccess.get_file_as_string(manifest_path)
	if json_text.is_empty():
		_fail("Missing sprite sheet manifest")
		return
	var doc = JSON.parse_string(json_text)
	if typeof(doc) != TYPE_DICTIONARY or doc.get("golden_approved", true) != false:
		_fail("Manifest is invalid or already Golden-promoted")
		return
	if doc.get("status") != "TECHNICAL_SPRITE_SHEET_CANDIDATE":
		_fail("Unexpected production state")
		return
	var base_dir: String = manifest_path.get_base_dir()
	var textures: Array[Texture2D] = []
	for page in doc.get("pages", []):
		var filename: String = page.get("file", "")
		if not filename.begins_with("sheet_") or not filename.ends_with(".png") or filename.get_file() != filename:
			_fail("Unsafe page filename")
			return
		var png_path: String = base_dir.path_join(filename)
		var image := Image.load_from_file(png_path)
		if image == null or image.is_empty() or image.get_width() != page.get("width") or image.get_height() != page.get("height"):
			_fail("Godot failed PNG decode or dimensions")
			return
		var texture := ImageTexture.create_from_image(image)
		if texture == null:
			_fail("Godot failed runtime texture construction")
			return
		textures.append(texture)
	var frames: Array = doc.get("frames", [])
	if frames.is_empty() or frames.size() % 16 != 0:
		_fail("Incomplete heading groups")
		return
	var actor := Node2D.new()
	root.add_child(actor)
	var keys := {}
	for frame in frames:
		var page_index: int = frame.get("page", -1)
		var heading: int = frame.get("heading", -1)
		var region: Array = frame.get("region", [])
		var asset: String = frame.get("asset_id", "")
		if page_index < 0 or page_index >= textures.size() or heading < 0 or heading >= 16 or region.size() != 4:
			_fail("Invalid atlas frame metadata")
			return
		var key := asset + "/" + str(heading)
		if keys.has(key):
			_fail("Duplicate directional frame")
			return
		keys[key] = true
		var rect := Rect2(region[0], region[1], region[2], region[3])
		var source: Texture2D = textures[page_index]
		if rect.position.x < 0 or rect.position.y < 0 or rect.end.x > source.get_width() or rect.end.y > source.get_height():
			_fail("Frame out of bounds")
			return
		var atlas := AtlasTexture.new()
		atlas.atlas = source
		atlas.region = rect
		atlas.filter_clip = true
		if atlas.get_width() != region[2] or atlas.get_height() != region[3]:
			_fail("AtlasTexture region import failed")
			return
		var sprite := Sprite2D.new()
		sprite.texture = atlas
		sprite.centered = false
		actor.add_child(sprite)
	var result := {"result": "GODOT_ATLAS_IMPORT_PASS", "frame_count": frames.size(),
		"pages": textures.size(), "instantiated_sprites": actor.get_child_count(),
		"actual_gameplay_test": false, "iphone_verified": false, "golden_approved": false}
	var dest := FileAccess.open(report_path, FileAccess.WRITE)
	if dest == null:
		_fail("Unable to write Godot evidence")
		return
	dest.store_string(JSON.stringify(result, "  ") + "\n")
	dest.close()
	print("FOUNDRY_GODOT_ATLAS_PASS frames=" + str(frames.size()))
	quit(0)
