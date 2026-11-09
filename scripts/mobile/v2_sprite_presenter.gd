extends RefCounted
## W08 mobile presentation adapter for F12 V2 render output (Production Integration V2).
##
## Consumes the F12 -> Godot fixture manifest shape tested in PR #53
## (cases{subject:{atlas,size,frames[{heading,source_frame,rect,ground_pivot_px,duration_ms}]}}).
## It does NOT render, re-author or approve assets. It only decides how approved
## frames are presented on a phone:
##   * approval gate, fail closed: CALIBRATION_ONLY output is accepted only in an
##     isolated fixture context, never in gameplay;
##   * stable trim: one alpha bounding box per subject (union over all frames),
##     so ground pivots, feet and wheels cannot jump between frames (F12 spec 16);
##   * compact repack: trimmed frames are packed into a smaller atlas to cut
##     texture memory, nearest filtering, no mipmaps (crisp pixels);
##   * heading lookup only when F12 publishes its heading convention. The current
##     fixture does not, so lookup returns -1 rather than guessing.

const CONTEXT_FIXTURE := "fixture"
const CONTEXT_GAME := "game"
## The only approval status the game context accepts. No package carries it today;
## W01 + founder approval through the protected V2 ledger must produce it.
const GAME_APPROVAL_STATUS := "GODOT_INTEGRATION_APPROVED"
const FIXTURE_STATUS := "CALIBRATION_ONLY"
const LOGICAL_TILE := Vector2i(80, 40)
const PADDING := 2


## Returns "" when `manifest` may be presented in `context`, otherwise the reason.
static func gate(manifest: Dictionary, context: String) -> String:
	var status := str(manifest.get("approval_status", ""))
	var tile: Array = manifest.get("logical_tile_px", [])
	if tile.size() != 2 or int(tile[0]) != LOGICAL_TILE.x or int(tile[1]) != LOGICAL_TILE.y:
		return "BLOCKED_PROJECTION: logical tile is not 80x40"
	if context == CONTEXT_FIXTURE:
		if status == FIXTURE_STATUS or status == GAME_APPROVAL_STATUS:
			return ""
		return "BLOCKED_STATUS: unknown approval status '%s'" % status
	if context == CONTEXT_GAME:
		if status != GAME_APPROVAL_STATUS:
			return "BLOCKED_NOT_APPROVED: '%s' cannot enter gameplay" % status
		var receipt: Dictionary = manifest.get("integration_receipt", {})
		for key in ["package_id", "package_sha256", "ledger_commit", "w09_evidence", "founder_evidence"]:
			if str(receipt.get(key, "")).is_empty():
				return "BLOCKED_RECEIPT: integration receipt missing " + key
		return ""
	return "BLOCKED_CONTEXT: " + context


static func load_manifest(path: String) -> Dictionary:
	if not FileAccess.file_exists(path):
		return {}
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(path))
	return parsed if parsed is Dictionary else {}


## Union of the alpha bounds of every frame of one subject, in frame-local pixels.
static func stable_trim(atlas: Image, frames: Array) -> Rect2i:
	var union := Rect2i()
	for entry in frames:
		var r: Array = entry["rect"]
		var region := Rect2i(int(r[0]), int(r[1]), int(r[2]), int(r[3]))
		var used := atlas.get_region(region).get_used_rect()
		if not used.has_area():
			continue
		union = used if not union.has_area() else union.merge(used)
	return union


## Builds presentation data for one subject. Returns {} and sets result.error on failure.
static func build_subject(atlas: Image, info: Dictionary) -> Dictionary:
	var frames: Array = info.get("frames", [])
	if frames.is_empty():
		return {"error": "no frames"}
	var trim := stable_trim(atlas, frames)
	if not trim.has_area():
		return {"error": "all frames are transparent"}
	var cell := trim.size + Vector2i.ONE * PADDING * 2
	var columns := maxi(1, int(ceil(sqrt(float(frames.size())))))
	var rows := int(ceil(float(frames.size()) / columns))
	var packed := Image.create(cell.x * columns, cell.y * rows, false, Image.FORMAT_RGBA8)
	packed.fill(Color(0, 0, 0, 0))
	var regions: Array[Rect2i] = []
	var pivots: Array[Vector2] = []
	for index in range(frames.size()):
		var entry: Dictionary = frames[index]
		var r: Array = entry["rect"]
		var source := Rect2i(int(r[0]) + trim.position.x, int(r[1]) + trim.position.y, trim.size.x, trim.size.y)
		var destination := Vector2i(index % columns * cell.x + PADDING, index / columns * cell.y + PADDING)
		packed.blit_rect(atlas, source, destination)
		regions.append(Rect2i(destination, trim.size))
		var pivot: Array = entry.get("ground_pivot_px", [r[2] * .5, r[3]])
		pivots.append(Vector2(float(pivot[0]), float(pivot[1])) - Vector2(trim.position))
	var texture := ImageTexture.create_from_image(packed)
	var sprite_frames := SpriteFrames.new()
	if sprite_frames.has_animation("default"):
		sprite_frames.remove_animation("default")
	for index in range(frames.size()):
		var entry: Dictionary = frames[index]
		var animation := "heading_%02d" % int(entry.get("heading", 0))
		if not sprite_frames.has_animation(animation):
			sprite_frames.add_animation(animation)
			sprite_frames.set_animation_speed(animation, 10.0)
			sprite_frames.set_animation_loop(animation, false)
		var region := AtlasTexture.new()
		region.atlas = texture
		region.region = Rect2(regions[index])
		sprite_frames.add_frame(animation, region, float(entry.get("duration_ms", 100)) / 100.0)
	return {
		"sprite_frames": sprite_frames,
		"texture": texture,
		"trim": trim,
		"regions": regions,
		## Ground pivot inside the trimmed frame. Identical for every frame of a
		## turntable/clip when F12 keeps a stable pivot, so offsets never jump.
		"pivots": pivots,
		"source_bytes": atlas.get_width() * atlas.get_height() * 4,
		"packed_bytes": packed.get_width() * packed.get_height() * 4,
		"packed_size": packed.get_size(),
	}


## Places a sprite so its ground pivot lands on `ground_screen` (feet on the tile).
static func configure_sprite(sprite: AnimatedSprite2D, subject: Dictionary, frame_index: int = 0) -> void:
	sprite.sprite_frames = subject.sprite_frames
	sprite.centered = false
	sprite.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	sprite.offset = -subject.pivots[frame_index]


## Maps a world facing to an F12 heading index. Requires F12 to publish
## heading_zero_world_deg and clockwise; returns -1 when it has not (fail closed).
static func heading_for(world_direction: Vector2, count: int, convention: Dictionary) -> int:
	if count < 1 or not convention.has("heading_zero_world_deg") or not convention.has("clockwise"):
		return -1
	if count == 1:
		return 0
	var degrees := rad_to_deg(world_direction.angle()) - float(convention.heading_zero_world_deg)
	if not bool(convention.clockwise):
		degrees = -degrees
	var step := 360.0 / count
	return posmod(roundi(degrees / step), count)
