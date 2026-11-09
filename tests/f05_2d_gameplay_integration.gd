extends SceneTree
## Real LAST LIGHT 2.5D scene integration of an F05 Blender output.
## Temporary test-only Sprite2D; it never replaces a canonical player asset.
const PREVIEW := "res://tests/fixtures/f05_calibration.png"

func _initialize() -> void:
    call_deferred("_test")

func _test() -> void:
    var failures: Array[String] = []
    var packed := ResourceLoader.load("res://main.tscn") as PackedScene
    if packed == null:
        push_error("F05_2D_GAMEPLAY_FAIL cannot load main.tscn")
        quit(2)
        return
    var game = packed.instantiate()
    get_root().add_child(game)
    game.set_process(false)
    game._restart_game()
    var image := Image.new()
    var err := image.load(ProjectSettings.globalize_path(PREVIEW))
    if err != OK or image.get_width() < 64 or image.get_height() < 64:
        failures.append("Blender PNG could not load into the game's real world")
    var sprite := Sprite2D.new()
    sprite.name = "F05_Noncanonical_Player_Calibration"
    if failures.is_empty():
        sprite.texture = ImageTexture.create_from_image(image)
    sprite.scale = Vector2(0.15, 0.15)
    sprite.centered = true
    sprite.z_index = 5
    game.add_child(sprite)
    var starting_world: Vector2 = game.player + Vector2(0.25, 0.25)
    sprite.position = game._screen(starting_world, 0.0)
    var pos_before: Vector2 = sprite.position
    sprite.position = game._screen(starting_world + Vector2(0.4, 0.0), 0.0)
    var world_step_px := sprite.position.distance_to(pos_before)
    if world_step_px < 5.0 or world_step_px > 30.0:
        failures.append("F05 Sprite2D failed 2.5D movement projection")
    if sprite.texture == null or not sprite.visible:
        failures.append("Imported calibration PNG is not a visible Sprite2D")
    if game.doors.size() < 5:
        failures.append("Main game door graph not initialized")
    else:
        var blocked: Vector2 = game._try_move(Vector2(5.4, 8.5), Vector2(0,-1), 0.19)
        game.doors[0].open = true
        var opened: Vector2 = game._try_move(Vector2(5.4,8.5), Vector2(0,-1), 0.19)
        if blocked.y <= 8.2 or opened.y >= 8.0:
            failures.append("Main game collision/door traversal regression")
    var report := {
        "status": "PASS" if failures.is_empty() else "FAIL",
        "scope": "real main.tscn 2.5D Sprite2D texture, screen projection, door traversal",
        "render_px": [image.get_width(), image.get_height()],
        "world_step_screen_px": snappedf(world_step_px, 0.01),
        "image_scale": 0.15,
        "temporary_gameplay_overlay": true,
        "canonical_approved": false,
        "visual_approved": false,
        "defects": failures
    }
    print("F05_2D_GAMEPLAY_QA_" + str(report["status"]), " ", JSON.stringify(report))
    quit(0 if failures.is_empty() else 2)
