extends Node2D
## Isolated LAST LIGHT V2 real-asset import fixture; not part of main.tscn.
## The source material is calibration-only. Actual Golden approval is separate.

const FIXTURE_DIR := "res://tests/godot_fixture/generated/"
const EXPECTED := {"cube": 1, "vehicle": 16, "cow": 16, "fridge": 7}
var validation_summary: Dictionary = {}
var validation_error: String = ""

func _ready() -> void:
    var path: String = FIXTURE_DIR + "fixture_manifest.json"
    if not FileAccess.file_exists(path):
        validation_error = "fixture manifest missing"
        return
    var data: Variant = JSON.parse_string(FileAccess.get_file_as_string(path))
    if not data is Dictionary:
        validation_error = "manifest invalid JSON"
        return
    if data.get("approval_status", "") != "CALIBRATION_ONLY":
        validation_error = "fixture cannot import or claim approval"
        return
    if data.get("logical_tile_px", []) != [80, 40]:
        validation_error = "logical tile mismatch"
        return
    var cases: Dictionary = data.get("cases", {})
    if cases.size() != EXPECTED.size():
        validation_error = "missing cases"
        return

    var count_total: int = 0
    for name in EXPECTED.keys():
        if not cases.has(name):
            validation_error = "missing case: " + name
            return
        var info: Dictionary = cases[name]
        var image: Image = Image.new()
        var error: Error = image.load(FIXTURE_DIR + str(info.get("atlas", "")))
        if error != OK:
            validation_error = "Godot Image.load failed for " + name
            return
        if image.get_width() != int(info["size"][0]) or image.get_height() != int(info["size"][1]):
            validation_error = "atlas dimension mismatch for " + name
            return
        var full_texture: ImageTexture = ImageTexture.create_from_image(image)
        if full_texture == null:
            validation_error = "ImageTexture conversion failed for " + name
            return
        var regions: Array = info.get("frames", [])
        if regions.size() != EXPECTED[name]:
            validation_error = "frame count mismatch for " + name
            return

        var frames: SpriteFrames = SpriteFrames.new()
        if frames.has_animation("default"):
            frames.remove_animation("default")
        var direction_seen := {}
        for entry in regions:
            var heading: int = int(entry["heading"])
            var animation_name: String = "heading_%02d" % heading
            if name == "fridge":
                animation_name = "freezer_open"
            elif name == "cube":
                animation_name = "cube_static"
            if not frames.has_animation(animation_name):
                frames.add_animation(animation_name)
                frames.set_animation_speed(animation_name, 10)
                frames.set_animation_loop(animation_name, false)
            var rect: Array = entry["rect"]
            var r: Rect2 = Rect2(float(rect[0]), float(rect[1]), float(rect[2]), float(rect[3]))
            if r.position.x < 0 or r.position.y < 0 or r.end.x > image.get_width() or r.end.y > image.get_height():
                validation_error = "region outside atlas " + name
                return
            var region: AtlasTexture = AtlasTexture.new()
            region.atlas = full_texture
            region.region = r
            frames.add_frame(animation_name, region, float(entry.get("duration_ms", 100)) / 100.0)
            if not direction_seen.has(heading):
                direction_seen[heading] = 0
            direction_seen[heading] += 1
        var needed_headings: int = 16 if name == "vehicle" else 8 if name == "cow" else 1
        if direction_seen.size() != needed_headings:
            validation_error = "missing directional animations: " + name
            return

        var actor: AnimatedSprite2D = AnimatedSprite2D.new()
        actor.name = name
        actor.sprite_frames = frames
        var first_animation: String = frames.get_animation_names()[0]
        actor.animation = first_animation
        actor.centered = true
        var first_origin: Array = regions[0]["ground_pivot_px"]
        actor.offset = Vector2(192, 192) - Vector2(float(first_origin[0]), float(first_origin[1]))
        actor.position = Vector2(200 + count_total * 3, 220)
        add_child(actor)
        if frames.get_frame_count(first_animation) < 1 or actor.texture_filter == CanvasItem.TEXTURE_FILTER_MAX:
            validation_error = "SpriteFrames not created for " + name
            return
        if name == "fridge" and frames.get_frame_count("freezer_open") != 7:
            validation_error = "hollow-fridge animation lost a frame"
            return
        count_total += regions.size()
    validation_summary = {"status": "GODOT_IMPORTED_CALIBRATION_ONLY",
                          "subjects": EXPECTED.size(),
                          "frames": count_total,
                          "tile": [80, 40],
                          "approval": "NOT_GOLDEN_OR_PRODUCTION"}
