extends SceneTree
## Smoke-test the F10 atlas in the repository's actual main.tscn hierarchy.
## No game files or player saves are modified; this is not a rendered screenshot.

func frames_have_local_anchor(manifest: Dictionary) -> bool:
    var frames: Array = manifest["frames"]
    return frames.size() > 0 and frames[0].has("anchor_local_px")

func _initialize() -> void:
    var packed := ResourceLoader.load("res://main.tscn") as PackedScene
    if packed == null:
        push_error("F12_GAME_SCENE_MISSING")
        quit(2)
        return
    var game := packed.instantiate()
    if not game is Node2D:
        push_error("F12_GAME_SCENE_NOT_2D")
        quit(3)
        return
    get_root().add_child(game)
    var raw := FileAccess.get_file_as_string("res://build/f12-f10/atlas/atlas.json")
    var manifest = JSON.parse_string(raw)
    if typeof(manifest) != TYPE_DICTIONARY or manifest.get("frames", []).size() != 16:
        push_error("F12_GAME_ATLAS_METADATA_INVALID")
        quit(4)
        return
    var image := Image.new()
    var filename := str(manifest["atlas_files"][0]["file"])
    if image.load("res://build/f12-f10/atlas/" + filename) != OK:
        push_error("F12_GAME_ATLAS_TEXTURE_LOAD_FAILED")
        quit(5)
        return
    var texture := ImageTexture.create_from_image(image)
    var roots := Node2D.new()
    roots.name = "F12_QA_ONLY_CAR_TILE_ANCHOR"
    roots.position = Vector2(80, 40)
    game.add_child(roots)
    var count := 0
    for entry in manifest["frames"]:
        var sprite := Sprite2D.new()
        sprite.name = "F12_CAR_HEADING_%02d" % int(entry["direction"])
        var r: Array = entry["rect"]
        sprite.texture = texture
        sprite.region_enabled = true
        sprite.region_rect = Rect2(float(r[0]), float(r[1]), float(r[2]), float(r[3]))
        if entry.has("anchor_local_px"):
            var local_anchor: Array = entry["anchor_local_px"]
            var original_pivot: Array = entry.get("world_ground_pivot_px", [])
            var crop_rect: Array = entry.get("source_crop_rect", [])
            if local_anchor.size() != 2 or original_pivot.size() != 2 or crop_rect.size() != 4:
                push_error("F12_GAME_TRIMMED_ANCHOR_METADATA_MISSING")
                quit(7)
                return
            var expected_local := Vector2(float(original_pivot[0])-float(crop_rect[0]), float(original_pivot[1])-float(crop_rect[1]))
            var verified_local := Vector2(float(local_anchor[0]),float(local_anchor[1]))
            if expected_local.distance_to(verified_local) > 0.002:
                push_error("F12_GAME_TRIMMED_ANCHOR_DRIFT")
                quit(8)
                return
            sprite.offset = Vector2(float(r[2])*0.5-verified_local.x, float(r[3])*0.5-verified_local.y)
        sprite.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
        sprite.visible = int(entry["direction"]) == 0
        roots.add_child(sprite)
        count += 1
    if count != 16 or roots.position != Vector2(80,40):
        push_error("F12_GAME_HEADING_PLACEMENT_FAIL")
        quit(6)
        return
    print("F12_REAL_MAIN_TSCN_ATLAS_PROBE_PASS nodes=16 anchor=80x40 trimmed=",frames_have_local_anchor(manifest))
    quit(0)
