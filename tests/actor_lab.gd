extends SceneTree
## Headless isolated 2.5D actor importer QA. Uses generated test preview atlases.
## Does not change main game scene, live inventory, zombie AI, or save data.
func _initialize() -> void:
    call_deferred("_check")

func _check() -> void:
    var packed: PackedScene = load("res://scenes/actor_lab.tscn")
    if packed == null:
        push_error("Actor Lab scene failed to load")
        quit(1)
        return
    var demo: Node2D = packed.instantiate()
    root.add_child(demo)
    await process_frame
    var actors: Array[AnimatedSprite2D] = []
    for child in demo.get_children():
        if child is AnimatedSprite2D:
            actors.append(child)
    if actors.size() != 5:
        push_error("Expected five Blender actor pilot sprites, got " + str(actors.size()))
        quit(1)
        return
    var walk_count := 0
    var shamble_count := 0
    for sprite in actors:
        var f: SpriteFrames = sprite.sprite_frames
        for dir in ["front","right","back","left"]:
            var animation: String = "idle_"+dir
            if not f.has_animation(animation) or f.get_frame_count(animation) != 1:
                push_error("Missing stable idle actor direction: " + dir)
                quit(1)
                return
            var image: Texture2D = f.get_frame_texture(animation,0)
            if image == null or image.get_width() <= 0:
                push_error("Broken imported actor frame texture")
                quit(1)
                return
        if f.has_animation("walk_front"):
            walk_count += 1
            if f.get_frame_count("walk_front") != 4:
                push_error("Walk animation should have 4 benchmark frames")
                quit(1)
                return
        if f.has_animation("shamble_front"):
            shamble_count += 1
            if f.get_frame_count("shamble_front") != 4:
                push_error("Zombie shamble should have 4 benchmark frames")
                quit(1)
                return
    if walk_count != 1 or shamble_count != 1:
        push_error("Need 1 clothed walking human and 1 shambling medical zombie")
        quit(1)
        return
    var event := InputEventMouseButton.new()
    event.button_index = MOUSE_BUTTON_LEFT
    event.pressed = true
    demo._unhandled_input(event)
    for sprite in actors:
        if not sprite.animation.ends_with("_right"):
            push_error("Actor direction switch failed")
            quit(1)
            return
    await create_timer(.3).timeout
    var worker_seen := false
    for sprite in actors:
        if sprite.sprite_frames.has_animation("walk_right"):
            worker_seen = true
            if sprite.sprite_frames.get_frame_count("walk_right") != 4:
                push_error("Worker animation missing after directional input")
                quit(1)
                return
    if not worker_seen:
        push_error("No walking human pilot visible")
        quit(1)
        return
    print("LAST_LIGHT_ACTOR_LAB_PASS five actors four directions walk and zombie shamble")
    quit(0)
