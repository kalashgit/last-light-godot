extends RefCounted
## Generic LL_ATLAS_OUTPUTS_V2 -> Godot 4 SpriteFrames adapter (W06 proposal for W01 review).
## Isolated test code: not referenced by main.tscn, project.godot, saves or gameplay.
## Reads any F12 atlas package through outputs_v2.json; no subject names are hardcoded.
## Node origin = ground pivot: place the AnimatedSprite2D at the world ground point.

const SCHEMA := "LL_ATLAS_OUTPUTS_V2"


## Returns {"frames": SpriteFrames, "offsets": {anim: Vector2}, "summary": {...}} or {"error": String}.
static func load_outputs(dir: String) -> Dictionary:
	var path: String = dir.path_join("outputs_v2.json")
	if not FileAccess.file_exists(path):
		return {"error": "outputs_v2.json missing in " + dir}
	var doc: Variant = JSON.parse_string(FileAccess.get_file_as_string(path))
	if not doc is Dictionary:
		return {"error": "outputs_v2.json invalid JSON"}
	if doc.get("schema", "") != SCHEMA or int(doc.get("schema_version", 0)) != 1:
		return {"error": "unsupported outputs schema"}
	if not doc.get("status", "") in ["CALIBRATION_ONLY", "CANDIDATE_NOT_APPROVED"]:
		return {"error": "unexpected status; loader never treats outputs as approved"}
	var tile: Array = doc.get("logical_tile_px", [])
	if tile.size() != 2 or int(tile[0]) != 80 or int(tile[1]) != 40:
		return {"error": "logical tile mismatch"}

	var textures: Array[ImageTexture] = []
	var images: Array[Image] = []
	for page in doc.get("pages", []):
		var image := Image.new()
		if image.load(dir.path_join(str(page["file"]))) != OK:
			return {"error": "Image.load failed: " + str(page["file"])}
		if image.get_width() != int(page["size"][0]) or image.get_height() != int(page["size"][1]):
			return {"error": "page size mismatch: " + str(page["file"])}
		images.append(image)
		textures.append(ImageTexture.create_from_image(image))
	if textures.is_empty():
		return {"error": "no atlas pages"}

	var clips: Dictionary = doc.get("clips", {})
	var frames := SpriteFrames.new()
	if frames.has_animation("default"):
		frames.remove_animation("default")
	var offsets := {}
	var bbox_checks := 0
	# Sort by clip, direction, frame_index so playback order never depends on JSON order.
	var entries: Array = doc.get("frames", []).duplicate()
	entries.sort_custom(func(a, b):
		if a["clip"] != b["clip"]:
			return str(a["clip"]) < str(b["clip"])
		if int(a["direction"]) != int(b["direction"]):
			return int(a["direction"]) < int(b["direction"])
		return int(a["frame_index"]) < int(b["frame_index"]))
	for e in entries:
		var clip: String = str(e["clip"])
		if not clips.has(clip):
			return {"error": "undeclared clip " + clip}
		var anim: String = "%s_d%02d" % [clip, int(e["direction"])]
		var fps: float = float(clips[clip]["fps"])
		if not frames.has_animation(anim):
			frames.add_animation(anim)
			frames.set_animation_speed(anim, fps)
			frames.set_animation_loop(anim, bool(clips[clip]["loop"]))
		var page: int = int(e["page"])
		if page < 0 or page >= textures.size():
			return {"error": "bad page index " + str(e["key"])}
		var rc: Array = e["rect"]
		var r := Rect2i(int(rc[0]), int(rc[1]), int(rc[2]), int(rc[3]))
		if r.position.x < 0 or r.position.y < 0 or r.end.x > images[page].get_width() or r.end.y > images[page].get_height():
			return {"error": "region outside atlas " + str(e["key"])}
		# Cross-engine pixel check: Godot's decoded alpha bbox must equal Python's.
		var used: Rect2i = images[page].get_region(r).get_used_rect()
		var bb: Array = e["alpha_bbox"]
		if used != Rect2i(int(bb[0]), int(bb[1]), int(bb[2]) - int(bb[0]), int(bb[3]) - int(bb[1])):
			return {"error": "Godot alpha bbox %s != manifest %s for %s" % [used, bb, e["key"]]}
		bbox_checks += 1
		var tex := AtlasTexture.new()
		tex.atlas = textures[page]
		tex.region = Rect2(r)
		# Godot duration is relative to 1/fps.
		frames.add_frame(anim, tex, float(e["duration_ms"]) * fps / 1000.0)
		var trim: Array = e["trim_offset_px"]
		var pivot: Array = e["ground_pivot_px"]
		var off := Vector2(float(trim[0]) - float(pivot[0]), float(trim[1]) - float(pivot[1]))
		if offsets.has(anim) and offsets[anim].distance_to(off) > 0.5:
			return {"error": "pivot wanders inside animation " + anim}
		offsets[anim] = off
	return {"frames": frames, "offsets": offsets,
			"summary": {"animations": frames.get_animation_names().size(),
						"frames": entries.size(), "directions": int(doc.get("directions", 0)),
						"pages": textures.size(), "godot_bbox_checks": bbox_checks}}


## Builds an AnimatedSprite2D whose position is the ground contact point.
static func make_sprite(loaded: Dictionary, anim: String) -> AnimatedSprite2D:
	var s := AnimatedSprite2D.new()
	s.sprite_frames = loaded["frames"]
	s.animation = anim
	s.centered = false
	s.offset = loaded["offsets"][anim]
	s.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	return s
