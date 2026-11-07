extends SceneTree
## Isolated animation importer QA; never alters the playable startup scene or saves.
func _initialize() -> void:
    call_deferred("_check")

func _check() -> void:
    var scene: PackedScene = load("res://scenes/animation_lab.tscn")
    if scene == null:
        push_error("Animation lab scene could not load")
        quit(1)
        return
    var demo: Node2D = scene.instantiate()
    root.add_child(demo)
    await process_frame
    var sprites: Array[AnimatedSprite2D] = []
    for child in demo.get_children():
        if child is AnimatedSprite2D:
            sprites.append(child)
    if sprites.size() != 2:
        push_error("Expected 2 V1 animation pilot actors, got " + str(sprites.size()))
        quit(1)
        return
    for actor in sprites:
        var frames := actor.sprite_frames
        if not frames.has_animation("open") or not frames.has_animation("close"):
            push_error("Missing paired open/close animation")
            quit(1)
            return
        if frames.get_frame_count("open") != 9 or frames.get_frame_count("close") != 9:
            push_error("Wrong animation frame count")
            quit(1)
            return
        actor.play("open")
    await create_timer(1.25).timeout
    for actor in sprites:
        if actor.frame != 8:
            push_error("Open action did not reach frame 8")
            quit(1)
            return
        actor.play("close")
    await create_timer(1.25).timeout
    for actor in sprites:
        if actor.frame != 8 or actor.is_playing():
            push_error("Close action did not finish")
            quit(1)
            return
    print("LAST_LIGHT_ANIMATION_LAB_PASS 2 sprites x 9 frames x 2 directions")
    quit(0)
