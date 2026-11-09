extends SceneTree
## Capture the ACTUAL Godot 4.3 prototype; not concept art or final sprites.
func _initialize() -> void:
    call_deferred("_begin")

func _begin() -> void:
    var scene: PackedScene = load("res://scenes/neighborhood_60_showcase.tscn")
    if scene == null:
        push_error("NEIGHBORHOOD_CAPTURE_FAIL missing scene")
        quit(1)
        return
    root.size = Vector2i(720, 1152)
    var world: Node2D = scene.instantiate()
    world.set("test_mode", true)
    root.add_child(world)
    if str(world.get("validation_error")) != "":
        push_error("NEIGHBORHOOD_CAPTURE_FAIL invalid layout")
        quit(1)
        return
    world.set("player", Vector2(39, 18))
    world.set("overview", true)
    world.set("zoom", 0.27)
    world.set("message_timer", 0.0)
    world.queue_redraw()
    await process_frame
    await RenderingServer.frame_post_draw
    var screenshot: Image = root.get_texture().get_image()
    if screenshot.is_empty():
        push_error("NEIGHBORHOOD_CAPTURE_FAIL viewport blank")
        quit(1)
        return
    var directory := "res://preview/neighborhood_60"
    DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(directory))
    var target := directory + "/three_house_street_godot.png"
    var status: Error = screenshot.save_png(target)
    if status != OK:
        push_error("NEIGHBORHOOD_CAPTURE_FAIL unable to save screenshot")
        quit(1)
        return
    print("NEIGHBORHOOD_GODOT_CAPTURE_PASS " + target + " " +
        str(screenshot.get_width()) + "x" + str(screenshot.get_height()))
    quit(0)
