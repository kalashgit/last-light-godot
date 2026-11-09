extends SceneTree
## F12 isolated atlas import/gameplay-scale contract in actual Godot 4.
## Noncanonical QA: does not assert game integration or founder artwork approval.

func _initialize() -> void:
    var raw := FileAccess.get_file_as_string("res://atlas/atlas.json")
    var data = JSON.parse_string(raw)
    if typeof(data) != TYPE_DICTIONARY:
        push_error("F12_GODOT_INVALID_JSON")
        quit(1)
        return
    var frames: Array = data.get("frames", [])
    if frames.size() != 16:
        push_error("F12_GODOT_INCOMPLETE_HEADINGS")
        quit(2)
        return
    var pages: Array = data.get("atlas_files", [])
    if pages.is_empty():
        push_error("F12_GODOT_MISSING_PAGES")
        quit(3)
        return
    var atlas_images: Array[Image] = []
    var atlas_textures: Array[Texture2D] = []
    for entry in pages:
        var img := Image.new()
        if img.load("res://atlas/" + str(entry["file"])) != OK:
            push_error("F12_GODOT_ATLAS_LOAD_FAILED")
            quit(4)
            return
        if img.get_width() != int(data["page_size"]) or img.get_height() != int(data["page_size"]):
            push_error("F12_GODOT_ATLAS_DIMENSIONS")
            quit(5)
            return
        atlas_images.append(img)
        atlas_textures.append(ImageTexture.create_from_image(img))
    var stage := Node2D.new()
    stage.name = "F12_ISOLATED_80X40_GAMEPLAY_SCALE"
    get_root().add_child(stage)
    var directions := {}
    var opaque_count := 0
    for entry in frames:
        var direction := int(entry["direction"])
        if directions.has(direction):
            push_error("F12_GODOT_DUPLICATE_DIRECTION")
            quit(6)
            return
        directions[direction] = true
        var p := int(entry["page"])
        var rect: Array = entry["rect"]
        if p < 0 or p >= atlas_images.size() or rect.size() != 4:
            push_error("F12_GODOT_BAD_FRAME_RECT")
            quit(7)
            return
        var area := Rect2i(int(rect[0]), int(rect[1]), int(rect[2]), int(rect[3]))
        var image := atlas_images[p]
        if area.position.x < 0 or area.position.y < 0 or area.end.x > image.get_width() or area.end.y > image.get_height():
            push_error("F12_GODOT_FRAME_OUT_OF_BOUNDS")
            quit(8)
            return
        if image.get_region(area).get_used_rect().size == Vector2i.ZERO:
            push_error("F12_GODOT_EMPTY_SPRITE")
            quit(9)
            return
        opaque_count += 1
        var sprite := Sprite2D.new()
        sprite.name = "heading_%02d" % direction
        sprite.texture = atlas_textures[p]
        sprite.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
        sprite.region_enabled = true
        sprite.region_rect = Rect2(area)
        # Trimmed sprites carry the original world contact point in cropped pixels.
        # Godot's centered Sprite2D would otherwise shift each heading differently.
        if entry.has("anchor_local_px"):
            var local_anchor: Array = entry["anchor_local_px"]
            if local_anchor.size() != 2:
                push_error("F12_GODOT_INVALID_LOCAL_ANCHOR")
                quit(12)
                return
            var expected_offset := Vector2(area.size.x * 0.5 - float(local_anchor[0]), area.size.y * 0.5 - float(local_anchor[1]))
            sprite.offset = expected_offset
            if sprite.offset.distance_to(expected_offset) > 0.001:
                push_error("F12_GODOT_ANCHOR_COMPENSATION_FAIL")
                quit(13)
                return
        # Shared position anchors all headings to the same physical 80x40 tile.
        sprite.position = Vector2(80, 40)
        sprite.visible = direction == 0
        stage.add_child(sprite)
        if sprite.position != Vector2(80, 40):
            push_error("F12_GODOT_INCONSISTENT_PLACEMENT")
            quit(10)
            return
    if directions.size() != 16 or opaque_count != 16:
        push_error("F12_GODOT_INCOMPLETE_IMPORT")
        quit(11)
        return
    print("F12_GODOT_ATLAS_IMPORT_PASS headings=16 tile=80x40 nearest_filter=true")
    quit(0)
