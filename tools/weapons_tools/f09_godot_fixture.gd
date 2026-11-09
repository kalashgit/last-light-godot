extends SceneTree
## LAST LIGHT F09 -- isolated candidate gameplay layout smoke test.
## Loads provisional fixed-scale 16-direction tool sprites into real Sprite2D
## nodes; does not touch main.tscn or the master inventory runtime.

const ROOT := "res://sprites"
const IDS := [
    "ll_tools_adjustable_wrench",
    "ll_tools_socket_handle",
    "ll_tools_hand_saw"
]

func _initialize() -> void:
    call_deferred("_run")

func _run() -> void:
    var stage := Node2D.new()
    stage.name = "F09CandidateWorldScene"
    get_root().add_child(stage)
    var checked := 0
    var bounds := Rect2(Vector2.ZERO, Vector2(1152, 720))
    for row in range(3):
        for heading in range(16):
            var path: String = "%s/%s/h%02d.png" % [ROOT, IDS[row], heading]
            var img := Image.new()
            if img.load(ProjectSettings.globalize_path(path)) != OK:
                push_error("F09_MISSING_WORLD_SPRITE: " + path)
                quit(21)
                return
            if img.get_width() != 96 or img.get_height() != 96:
                push_error("F09_INCORRECT_WORLD_RESOLUTION " + path)
                quit(22)
                return
            var sprite := Sprite2D.new()
            sprite.name = "Heading_%02d" % heading
            sprite.texture = ImageTexture.create_from_image(img)
            sprite.centered = true
            sprite.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
            sprite.position = Vector2(94.0 + heading * 64.0, 180.0 + row * 160.0)
            stage.add_child(sprite)
            if not bounds.has_point(sprite.position):
                push_error("F09_SPRITE_OFF_STAGE " + str(sprite.position))
                quit(23)
                return
            if sprite.texture == null:
                push_error("F09_SPRITE_TEXTURE_NULL")
                quit(24)
                return
            checked += 1
    var imported_models := 0
    for ident in IDS:
        var glb: String = "res://models/%s.glb" % ident
        var packed := ResourceLoader.load(glb)
        if not (packed is PackedScene):
            push_error("F09_GLB_IMPORT_FAILED " + glb)
            quit(26)
            return
        # Headless uses the dummy RenderingServer. Validate imported
        # PackedScene nodes without creating live MeshInstance3D resources;
        # doing so produced a spurious dummy-storage mesh-null error on exit.
        var state := packed.get_state()
        if state == null or state.get_node_count() < 1:
            push_error("F09_GLB_EMPTY_PACKED_SCENE " + glb)
            quit(27)
            return
        imported_models += 1
    if imported_models != 3:
        quit(28)
        return
    if checked != 48 or stage.get_child_count() != 48:
        quit(25)
        return
    print("F09_GODOT_SCENE_SMOKE_PASS baked_models=",imported_models," sprites=", checked,
          " stage=",stage.name," headings=16 tools=3")
    quit(0)
